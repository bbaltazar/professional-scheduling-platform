"""
poetry run uvicorn main:app --reload
"""

from __future__ import annotations
from typing import Union, List, Optional
from datetime import date, time, datetime, timedelta
import secrets
from fastapi import FastAPI, Depends, HTTPException, Request, Cookie, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
import jwt

try:
    from .database import (
        get_db,
        Specialist,
        ServiceDB,
        AvailabilitySlot,
        Booking,
        database,
        VerificationCode,
    )
    from .verification_service import verification_service
except ImportError:
    from database import (
        get_db,
        Specialist,
        ServiceDB,
        AvailabilitySlot,
        Booking,
        database,
        VerificationCode,
    )
    from verification_service import verification_service

app = FastAPI(
    title="Élite Scheduling Platform",
    description="A luxury scheduling platform for professionals and clients",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# JWT Configuration
JWT_SECRET_KEY = secrets.token_urlsafe(32)
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer(auto_error=False)

import os
from pathlib import Path

# Get the directory where this file is located
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


# Authentication Helper Functions
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)

    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None


def get_current_specialist(
    request: Request, db: Session = Depends(get_db)
) -> Optional[Specialist]:
    """Get current authenticated specialist from session with their services and availability"""
    # Try to get token from cookie first
    token = request.cookies.get("access_token")
    if not token:
        return None

    payload = verify_token(token)
    if not payload:
        return None

    specialist_id = payload.get("specialist_id")
    if not specialist_id:
        return None

    # Fetch specialist with services eagerly loaded
    specialist = db.query(Specialist).filter(Specialist.id == specialist_id).first()
    return specialist


def require_authentication(
    request: Request, db: Session = Depends(get_db)
) -> Specialist:
    """Dependency to require authentication"""
    specialist = get_current_specialist(request, db)
    if not specialist:
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Please sign in to access professional features.",
        )
    return specialist


@app.on_event("startup")
async def startup():
    """Initialize database connection on startup."""
    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    """Close database connection on shutdown."""
    await database.disconnect()


# Health Check
@app.get("/health")
def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
    }


# Authentication Endpoints
@app.post("/auth/logout")
async def logout(response: Response):
    """Logout user by clearing authentication cookie"""
    response.delete_cookie(key="access_token")
    return {"success": True, "message": "Successfully logged out"}


@app.get("/auth/me")
async def get_current_user(request: Request, db: Session = Depends(get_db)):
    """Get current authenticated user info with services and availability"""
    specialist = get_current_specialist(request, db)
    if not specialist:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Get services for this specialist
    services = (
        db.query(ServiceDB).filter(ServiceDB.specialist_id == specialist.id).all()
    )

    # Get recent availability slots for this specialist
    from datetime import date, timedelta

    today = date.today()
    recent_availability = (
        db.query(AvailabilitySlot)
        .filter(
            AvailabilitySlot.specialist_id == specialist.id,
            AvailabilitySlot.date >= today,
        )
        .all()
    )

    specialist_response = SpecialistResponse(
        id=specialist.id,
        name=specialist.name,
        email=specialist.email,
        bio=specialist.bio,
        phone=specialist.phone,
        services=services,
    )

    return {
        "specialist": specialist_response,
        "services": services,
        "availability": [
            {
                "id": slot.id,
                "date": slot.date.isoformat(),
                "start_time": slot.start_time.strftime("%H:%M:%S"),
                "end_time": slot.end_time.strftime("%H:%M:%S"),
                "is_available": slot.is_available,
            }
            for slot in recent_availability
        ],
    }


# HTML Routes for Web Interface
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/professional", response_class=HTMLResponse)
async def professional_dashboard(request: Request, db: Session = Depends(get_db)):
    """Professional dashboard - shows verification form if not authenticated, dashboard if authenticated"""
    specialist = get_current_specialist(request, db)

    # Pass authentication state to template
    return templates.TemplateResponse(
        "professional.html",
        {
            "request": request,
            "authenticated": specialist is not None,
            "specialist": specialist,
        },
    )


@app.get("/consumer", response_class=HTMLResponse)
async def consumer_portal(request: Request):
    return templates.TemplateResponse("consumer.html", {"request": request})


"""
Desired features

We want to build a simple API that allows us to:

1. Takes a specialist's services and their prices. 
2. Allows a user to choose a time slot for a service.
"""


# Pydantic models for API
class Service(BaseModel):
    name: str
    price: float
    duration: int


class ServiceResponse(Service):
    id: int
    specialist_id: int

    class Config:
        from_attributes = True


class SpecialistCreate(BaseModel):
    name: str
    email: str
    bio: Optional[str] = None
    phone: Optional[str] = None


class SpecialistResponse(BaseModel):
    id: int
    name: str
    email: str
    bio: Optional[str] = None
    phone: Optional[str] = None
    services: List[ServiceResponse] = []

    class Config:
        from_attributes = True


class AvailabilitySlotCreate(BaseModel):
    date: date
    start_time: time
    end_time: time


class AvailabilitySlotResponse(AvailabilitySlotCreate):
    id: int
    specialist_id: int
    is_available: bool

    class Config:
        from_attributes = True


class BookingCreate(BaseModel):
    specialist_id: int
    service_id: int
    slot_id: int
    client_name: str
    client_email: EmailStr
    client_phone: Optional[str] = None
    notes: Optional[str] = None


class BookingResponse(BookingCreate):
    id: int
    specialist_id: int
    end_time: time
    status: str

    class Config:
        from_attributes = True


class SpecialistCatalogResponse(BaseModel):
    id: int
    name: str
    bio: Optional[str] = None
    services: List[ServiceResponse] = []
    available_dates: List[date] = []

    class Config:
        from_attributes = True


class TimeSlotResponse(BaseModel):
    id: int
    start_time: time
    end_time: time
    duration_minutes: int
    date: date

    class Config:
        from_attributes = True


class ErrorResponse(BaseModel):
    error: str
    detail: str
    timestamp: datetime


# Authentication Models
class LoginRequest(BaseModel):
    email: EmailStr
    name: Optional[str] = None  # For new registrations
    bio: Optional[str] = None
    phone: Optional[str] = None


class AuthResponse(BaseModel):
    success: bool
    message: str
    access_token: Optional[str] = None
    specialist: Optional[SpecialistResponse] = None
    requires_verification: bool = False


# Verification Models
class VerificationRequest(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    verification_type: str = "registration"  # "registration" or "login"


class VerificationResponse(BaseModel):
    success: bool
    message: str
    method: str  # "email" or "sms"


class CodeVerificationRequest(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    code: str
    verification_type: str = "registration"
    # Add optional registration data
    name: Optional[str] = None
    bio: Optional[str] = None
    specialist_phone: Optional[str] = None


class CodeVerificationResponse(BaseModel):
    success: bool
    message: str
    verified: bool = False
    access_token: Optional[str] = None
    specialist: Optional[SpecialistResponse] = None


# Verification Endpoints
@app.post("/verification/send", response_model=VerificationResponse)
async def send_verification_code(
    request: VerificationRequest, db: Session = Depends(get_db)
):
    """
    Send a 6-digit verification code via email or SMS
    """
    if not request.email and not request.phone:
        raise HTTPException(
            status_code=400, detail="Either email or phone number must be provided"
        )

    # Clean up expired codes first
    verification_service.cleanup_expired_codes(db)

    success = False
    method = ""
    message = ""

    if request.email:
        success = await verification_service.send_email_verification(
            db, request.email, request.verification_type
        )
        method = "email"
        message = f"Verification code sent to {request.email}"
    elif request.phone:
        success = await verification_service.send_sms_verification(
            db, request.phone, request.verification_type
        )
        method = "sms"
        message = f"Verification code sent to {request.phone}"

    if not success:
        raise HTTPException(status_code=500, detail="Failed to send verification code")

    return VerificationResponse(success=success, message=message, method=method)


@app.post("/verification/verify", response_model=CodeVerificationResponse)
async def verify_code(
    request: CodeVerificationRequest, response: Response, db: Session = Depends(get_db)
):
    """
    Verify the 6-digit code provided by the user and authenticate them
    """
    if not request.email and not request.phone:
        raise HTTPException(
            status_code=400, detail="Either email or phone number must be provided"
        )

    if not request.code or len(request.code) != 6:
        raise HTTPException(
            status_code=400, detail="Verification code must be 6 digits"
        )

    # Verify the code
    verified = verification_service.verify_code(
        db=db,
        email=request.email,
        phone=request.phone,
        code=request.code,
        verification_type=request.verification_type,
    )

    if not verified:
        return CodeVerificationResponse(
            success=False,
            verified=False,
            message="Invalid or expired verification code. Please try again.",
        )

    # Code verified successfully, now handle authentication
    contact_email = request.email
    specialist = None

    if contact_email:
        # Check if specialist already exists
        specialist = (
            db.query(Specialist).filter(Specialist.email == contact_email).first()
        )

        if not specialist and request.verification_type == "registration":
            # Create new specialist if this is registration
            if not request.name:
                raise HTTPException(
                    status_code=400, detail="Name is required for registration"
                )

            specialist = Specialist(
                name=request.name,
                email=contact_email,
                bio=request.bio,
                phone=request.specialist_phone,
            )
            db.add(specialist)
            db.commit()
            db.refresh(specialist)

        elif not specialist and request.verification_type == "login":
            raise HTTPException(
                status_code=404,
                detail="No account found with this email. Please register first.",
            )

    if not specialist:
        raise HTTPException(
            status_code=500, detail="Failed to create or find specialist account"
        )

    # Create access token
    access_token = create_access_token(
        data={"specialist_id": specialist.id, "email": specialist.email}
    )

    # Set secure cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS, False for localhost
        samesite="lax",
        max_age=ACCESS_TOKEN_EXPIRE_HOURS * 3600,
    )

    # Convert specialist to response format
    specialist_response = SpecialistResponse(
        id=specialist.id,
        name=specialist.name,
        email=specialist.email,
        bio=specialist.bio,
        phone=specialist.phone,
        services=[],
    )

    return CodeVerificationResponse(
        success=True,
        verified=True,
        message="Verification successful! You are now signed in.",
        access_token=access_token,
        specialist=specialist_response,
    )


@app.get("/auth/my-services", response_model=List[ServiceResponse])
async def get_current_user_services(request: Request, db: Session = Depends(get_db)):
    """Get current authenticated user's services"""
    specialist = get_current_specialist(request, db)
    if not specialist:
        raise HTTPException(status_code=401, detail="Not authenticated")

    services = (
        db.query(ServiceDB).filter(ServiceDB.specialist_id == specialist.id).all()
    )
    return services


@app.post("/specialist/", response_model=SpecialistResponse)
def create_specialist(
    specialist: SpecialistCreate,
    db: Session = Depends(get_db),
    current_specialist: Specialist = Depends(require_authentication),
):
    """
    Create a new specialist with enhanced profile info and validation.
    Note: This endpoint is now protected - specialists should be created through the verification process.
    """
    # Check if specialist with this email already exists
    existing_specialist = (
        db.query(Specialist).filter(Specialist.email == specialist.email).first()
    )
    if existing_specialist:
        raise HTTPException(
            status_code=400, detail="Specialist with this email already exists"
        )

    # Validate name length
    if len(specialist.name.strip()) < 2:
        raise HTTPException(
            status_code=400, detail="Specialist name must be at least 2 characters long"
        )

    db_specialist = Specialist(
        name=specialist.name.strip(),
        email=specialist.email.lower().strip(),
        bio=specialist.bio.strip() if specialist.bio else None,
        phone=specialist.phone.strip() if specialist.phone else None,
    )
    db.add(db_specialist)
    db.commit()
    db.refresh(db_specialist)
    return db_specialist


@app.put("/specialist/{specialist_id}/services")
def update_specialist_services(
    specialist_id: int,
    services: List[Service],
    request: Request,
    db: Session = Depends(get_db),
    current_specialist: Specialist = Depends(require_authentication),
) -> dict:
    """
    Update the services offered by a specialist using a real database.
    """
    # Ensure specialist can only update their own services
    if current_specialist.id != specialist_id:
        raise HTTPException(
            status_code=403, detail="You can only update your own services"
        )

    # Check if specialist exists (redundant but kept for consistency)
    specialist = db.query(Specialist).filter(Specialist.id == specialist_id).first()
    if not specialist:
        raise HTTPException(status_code=404, detail="Specialist not found")

    # Delete existing services for this specialist
    db.query(ServiceDB).filter(ServiceDB.specialist_id == specialist_id).delete()

    # Add new services with validation
    db_services = []
    for service in services:
        # Validate service data
        if len(service.name.strip()) < 2:
            raise HTTPException(
                status_code=400,
                detail=f"Service name '{service.name}' must be at least 2 characters long",
            )
        if service.price <= 0:
            raise HTTPException(
                status_code=400,
                detail=f"Service price must be greater than 0, got {service.price}",
            )
        if service.duration <= 0 or service.duration > 1440:  # Max 24 hours
            raise HTTPException(
                status_code=400,
                detail=f"Service duration must be between 1 and 1440 minutes, got {service.duration}",
            )

        db_service = ServiceDB(
            name=service.name.strip(),
            price=round(service.price, 2),  # Round to 2 decimal places
            duration=service.duration,
            specialist_id=specialist_id,
        )
        db.add(db_service)
        db_services.append(db_service)

    db.commit()

    # Refresh to get the IDs
    for service in db_services:
        db.refresh(service)

    return {
        "specialist_id": specialist_id,
        "services": [
            {
                "id": service.id,
                "name": service.name,
                "price": service.price,
                "duration": service.duration,
                "specialist_id": service.specialist_id,
            }
            for service in db_services
        ],
    }


@app.get("/specialist/{specialist_id}/services", response_model=List[ServiceResponse])
def read_specialist_services(specialist_id: int, db: Session = Depends(get_db)):
    """
    Get the services offered by a specialist from the database.
    """
    specialist = db.query(Specialist).filter(Specialist.id == specialist_id).first()
    if not specialist:
        raise HTTPException(status_code=404, detail="Specialist not found")

    services = (
        db.query(ServiceDB).filter(ServiceDB.specialist_id == specialist_id).all()
    )
    return services


@app.get("/specialist/{specialist_id}", response_model=SpecialistResponse)
def read_specialist(specialist_id: int, db: Session = Depends(get_db)):
    """
    Get a specialist and their services.
    """
    specialist = db.query(Specialist).filter(Specialist.id == specialist_id).first()
    if not specialist:
        raise HTTPException(status_code=404, detail="Specialist not found")

    return specialist


@app.get("/specialists/", response_model=List[SpecialistResponse])
def read_specialists(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Get all specialists.
    """
    specialists = db.query(Specialist).offset(skip).limit(limit).all()
    return specialists


# Professional Side - Availability Management
@app.post(
    "/specialist/{specialist_id}/availability",
    response_model=List[AvailabilitySlotResponse],
)
def add_availability_slots(
    specialist_id: int,
    slots: List[AvailabilitySlotCreate],
    request: Request,
    db: Session = Depends(get_db),
    current_specialist: Specialist = Depends(require_authentication),
):
    """
    Add availability slots for a specialist.
    """
    # Ensure specialist can only update their own availability
    if current_specialist.id != specialist_id:
        raise HTTPException(
            status_code=403, detail="You can only update your own availability"
        )
    specialist = db.query(Specialist).filter(Specialist.id == specialist_id).first()
    if not specialist:
        raise HTTPException(status_code=404, detail="Specialist not found")

    db_slots = []
    for slot in slots:
        db_slot = AvailabilitySlot(
            specialist_id=specialist_id,
            date=slot.date,
            start_time=slot.start_time,
            end_time=slot.end_time,
        )
        db.add(db_slot)
        db_slots.append(db_slot)

    db.commit()

    for slot in db_slots:
        db.refresh(slot)

    return db_slots


@app.get(
    "/specialist/{specialist_id}/availability",
    response_model=List[AvailabilitySlotResponse],
)
def get_specialist_availability(
    specialist_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
):
    """
    Get availability slots for a specialist.
    """
    query = db.query(AvailabilitySlot).filter(
        AvailabilitySlot.specialist_id == specialist_id
    )

    if start_date:
        query = query.filter(AvailabilitySlot.date >= start_date)
    if end_date:
        query = query.filter(AvailabilitySlot.date <= end_date)

    return query.all()


# Consumer Side - Browse and Book
@app.get("/catalog/specialists", response_model=List[SpecialistCatalogResponse])
def get_specialists_catalog(db: Session = Depends(get_db)):
    """
    Get all specialists with their services and availability for consumers to browse.
    """
    specialists = db.query(Specialist).all()
    catalog = []

    for specialist in specialists:
        available_dates = [
            slot.date
            for slot in db.query(AvailabilitySlot)
            .filter(AvailabilitySlot.specialist_id == specialist.id)
            .filter(AvailabilitySlot.is_available == True)
            .filter(AvailabilitySlot.date >= datetime.now().date())
            .distinct(AvailabilitySlot.date)
            .all()
        ]

        catalog.append(
            SpecialistCatalogResponse(
                id=specialist.id,
                name=specialist.name,
                bio=specialist.bio,
                services=specialist.services,
                available_dates=available_dates,
            )
        )

    return catalog


@app.get("/specialist/{specialist_id}/availability/{booking_date}")
def get_available_time_slots(
    specialist_id: int,
    booking_date: date,
    service_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """
    Get available time slots for a specific specialist on a specific date.
    Returns slots that can accommodate the requested service duration.
    """
    # Get service duration - use specific service or minimum duration for this specialist
    if service_id:
        service = db.query(ServiceDB).filter(ServiceDB.id == service_id).first()
        if not service:
            raise HTTPException(status_code=404, detail="Service not found")
        service_duration = service.duration
    else:
        # Find the minimum service duration for this specialist to determine smallest available slots
        min_service = (
            db.query(ServiceDB)
            .filter(ServiceDB.specialist_id == specialist_id)
            .order_by(ServiceDB.duration)
            .first()
        )
        if not min_service:
            # If no services exist, default to 30 minutes
            service_duration = 30
        else:
            service_duration = min_service.duration

    # Get availability slots for the date
    availability_slots = (
        db.query(AvailabilitySlot)
        .filter(
            AvailabilitySlot.specialist_id == specialist_id,
            AvailabilitySlot.date == booking_date,
            AvailabilitySlot.is_available == True,
        )
        .all()
    )

    # Get existing bookings for the date
    existing_bookings = (
        db.query(Booking)
        .filter(
            Booking.specialist_id == specialist_id,
            Booking.date == booking_date,
            Booking.status == "confirmed",
        )
        .all()
    )

    available_slots = []
    for slot in availability_slots:
        # Generate time slots within the availability window
        current_time = datetime.combine(booking_date, slot.start_time)
        end_time = datetime.combine(booking_date, slot.end_time)

        while current_time + timedelta(minutes=service_duration) <= end_time:
            slot_end = current_time + timedelta(minutes=service_duration)

            # Check if this slot conflicts with existing bookings
            conflict = False
            for booking in existing_bookings:
                booking_start = datetime.combine(booking_date, booking.start_time)
                booking_end = datetime.combine(booking_date, booking.end_time)

                if current_time < booking_end and slot_end > booking_start:
                    conflict = True
                    break

            if not conflict:
                available_slots.append(
                    {
                        "start_time": current_time.time(),
                        "end_time": slot_end.time(),
                        "duration_minutes": service_duration,
                    }
                )

            # Use the minimum service duration as the interval, but at least 15 minutes
            interval = max(15, min(30, service_duration))
            current_time += timedelta(minutes=interval)

    return available_slots


@app.post("/booking/", response_model=BookingResponse)
def create_booking(booking: BookingCreate, db: Session = Depends(get_db)):
    """
    Create a new booking for a consumer with comprehensive validation.
    """
    # Validate specialist exists
    specialist = (
        db.query(Specialist).filter(Specialist.id == booking.specialist_id).first()
    )
    if not specialist:
        raise HTTPException(status_code=404, detail="Specialist not found")

    # Validate service exists and belongs to specialist
    service = (
        db.query(ServiceDB)
        .filter(
            ServiceDB.id == booking.service_id,
            ServiceDB.specialist_id == booking.specialist_id,
        )
        .first()
    )
    if not service:
        raise HTTPException(
            status_code=404, detail="Service not found for this specialist"
        )

    # Validate availability slot exists and is available
    availability_slot = (
        db.query(AvailabilitySlot)
        .filter(
            AvailabilitySlot.id == booking.slot_id,
            AvailabilitySlot.specialist_id == booking.specialist_id,
            AvailabilitySlot.is_available == True,
        )
        .first()
    )
    if not availability_slot:
        raise HTTPException(
            status_code=404, detail="Availability slot not found or not available"
        )

    # Calculate booking times
    slot_start = datetime.combine(availability_slot.date, availability_slot.start_time)
    booking_end = slot_start + timedelta(minutes=service.duration)
    slot_end = datetime.combine(availability_slot.date, availability_slot.end_time)

    # Validate service fits within availability slot
    if booking_end > slot_end:
        raise HTTPException(
            status_code=400,
            detail=f"Service duration ({service.duration} min) exceeds available time slot",
        )

    # Check for conflicts with existing bookings
    existing_booking = (
        db.query(Booking)
        .filter(
            Booking.specialist_id == booking.specialist_id,
            Booking.date == availability_slot.date,
            Booking.status == "confirmed",
        )
        .filter(
            # Check for time overlap
            (Booking.start_time < booking_end.time())
            & (Booking.end_time > slot_start.time())
        )
        .first()
    )

    if existing_booking:
        raise HTTPException(
            status_code=400, detail="Time slot conflicts with existing booking"
        )

    # Create the booking
    db_booking = Booking(
        specialist_id=booking.specialist_id,
        service_id=booking.service_id,
        client_name=booking.client_name,
        client_email=booking.client_email,
        client_phone=booking.client_phone,
        date=availability_slot.date,
        start_time=slot_start.time(),
        end_time=booking_end.time(),
        notes=booking.notes,
        status="confirmed",
    )

    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)

    # Update availability slot to unavailable if fully booked
    # (You might want to implement partial slot booking logic here)
    availability_slot.is_available = False
    db.commit()

    return db_booking


@app.get("/bookings/specialist/{specialist_id}", response_model=List[BookingResponse])
def get_specialist_bookings(specialist_id: int, db: Session = Depends(get_db)):
    """
    Get all bookings for a specialist.
    """
    bookings = db.query(Booking).filter(Booking.specialist_id == specialist_id).all()
    return bookings
