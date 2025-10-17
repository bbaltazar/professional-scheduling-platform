"""
poetry run uvicorn main:app --reload
"""

from __future__ import annotations
from typing import Union, List, Optional
from datetime import date, time, datetime, timedelta
import secrets
import json

# Note: dateutil will need to be installed: pip install python-dateutil
try:
    from dateutil.rrule import rrule, DAILY, WEEKLY
    from dateutil.rrule import MO, TU, WE, TH, FR, SA, SU

    DATEUTIL_AVAILABLE = True
except ImportError:
    DATEUTIL_AVAILABLE = False
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
        CalendarEvent,
        EventException,
        WorkingHours,
        SchedulingPreferences,
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
        CalendarEvent,
        EventException,
        WorkingHours,
        SchedulingPreferences,
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


# Advanced Calendar Management Helper Functions


def generate_recurring_event_instances(
    db: Session, base_event: CalendarEvent, recurrence_rule: RecurrenceRule
):
    """
    Generate instances of a recurring event based on sophisticated recurrence rules.
    Supports RFC 5545-like RRULE patterns for Google Calendar-level flexibility.
    """
    if not DATEUTIL_AVAILABLE:
        # Fallback to simple recurring logic if dateutil is not available
        return generate_simple_recurring_instances(db, base_event, recurrence_rule)

    # Map frequency strings to dateutil constants
    freq_map = {"DAILY": DAILY, "WEEKLY": WEEKLY}

    # Map weekday integers to dateutil weekday objects
    weekday_map = {0: MO, 1: TU, 2: WE, 3: TH, 4: FR, 5: SA, 6: SU}

    # Build rrule parameters
    rrule_params = {
        "freq": freq_map.get(recurrence_rule.freq, WEEKLY),
        "interval": recurrence_rule.interval,
        "dtstart": base_event.start_datetime,
    }

    # Add end conditions
    if recurrence_rule.until:
        rrule_params["until"] = datetime.combine(recurrence_rule.until, time.max)
    elif recurrence_rule.count:
        rrule_params["count"] = recurrence_rule.count
    else:
        # Default to 2 years if no end specified
        rrule_params["until"] = base_event.start_datetime + timedelta(days=730)

    # Add weekday restrictions
    if recurrence_rule.byweekday:
        rrule_params["byweekday"] = [
            weekday_map[day] for day in recurrence_rule.byweekday
        ]

    # Add month day restrictions
    if recurrence_rule.bymonthday:
        rrule_params["bymonthday"] = recurrence_rule.bymonthday

    # Add month restrictions
    if recurrence_rule.bymonth:
        rrule_params["bymonth"] = recurrence_rule.bymonth

    # Generate occurrence dates
    rule = rrule(**rrule_params)
    occurrences = list(rule)

    # Create event instances (skip the first one as it's the base event)
    duration = base_event.end_datetime - base_event.start_datetime

    for occurrence_start in occurrences[1:]:  # Skip first occurrence
        occurrence_end = occurrence_start + duration

        # Check for conflicts with existing events
        if not has_calendar_conflict(
            db, base_event.specialist_id, occurrence_start, occurrence_end
        ):
            db_instance = CalendarEvent(
                specialist_id=base_event.specialist_id,
                title=base_event.title,
                description=base_event.description,
                location=base_event.location,
                start_datetime=occurrence_start,
                end_datetime=occurrence_end,
                is_all_day=base_event.is_all_day,
                timezone=base_event.timezone,
                event_type=base_event.event_type,
                category=base_event.category,
                priority=base_event.priority,
                color=base_event.color,
                is_bookable=base_event.is_bookable,
                max_bookings=base_event.max_bookings,
                buffer_before=base_event.buffer_before,
                buffer_after=base_event.buffer_after,
                is_recurring=False,  # Individual instances are not recurring
                status=base_event.status,
                visibility=base_event.visibility,
                recurring_event_id=base_event.recurring_event_id,
                original_start=occurrence_start,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(db_instance)

    db.commit()


def generate_simple_recurring_instances(
    db: Session, base_event: CalendarEvent, recurrence_rule: RecurrenceRule
):
    """
    Fallback simple recurring instance generator when dateutil is not available.
    """
    current_date = base_event.start_datetime.date()
    end_date = recurrence_rule.until or (current_date + timedelta(days=365))
    duration = base_event.end_datetime - base_event.start_datetime
    count = 0
    max_count = recurrence_rule.count or 100

    while current_date <= end_date and count < max_count:
        # Simple frequency handling
        if recurrence_rule.freq == "DAILY":
            current_date += timedelta(days=recurrence_rule.interval)
        elif recurrence_rule.freq == "WEEKLY":
            current_date += timedelta(weeks=recurrence_rule.interval)
        else:
            break

        if current_date <= end_date:
            # Create instance
            occurrence_start = datetime.combine(
                current_date, base_event.start_datetime.time()
            )
            occurrence_end = occurrence_start + duration

            if not has_calendar_conflict(
                db, base_event.specialist_id, occurrence_start, occurrence_end
            ):
                db_instance = CalendarEvent(
                    specialist_id=base_event.specialist_id,
                    title=base_event.title,
                    description=base_event.description,
                    location=base_event.location,
                    start_datetime=occurrence_start,
                    end_datetime=occurrence_end,
                    is_all_day=base_event.is_all_day,
                    timezone=base_event.timezone,
                    event_type=base_event.event_type,
                    category=base_event.category,
                    priority=base_event.priority,
                    color=base_event.color,
                    is_bookable=base_event.is_bookable,
                    max_bookings=base_event.max_bookings,
                    buffer_before=base_event.buffer_before,
                    buffer_after=base_event.buffer_after,
                    is_recurring=False,
                    status=base_event.status,
                    visibility=base_event.visibility,
                    recurring_event_id=base_event.recurring_event_id,
                    original_start=occurrence_start,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
                db.add(db_instance)

        count += 1

    db.commit()


def apply_recurring_exceptions(
    db: Session,
    events: List[CalendarEvent],
    start_date: Optional[date],
    end_date: Optional[date],
) -> List[CalendarEvent]:
    """
    Apply exceptions to recurring events (cancellations, modifications).
    Returns the event list with exceptions applied.
    """
    # Get all exceptions for the events in the date range
    event_ids = [event.id for event in events]
    exceptions = (
        db.query(EventException).filter(EventException.event_id.in_(event_ids)).all()
    )

    # Group exceptions by event ID
    exceptions_by_event = {}
    for exception in exceptions:
        if exception.event_id not in exceptions_by_event:
            exceptions_by_event[exception.event_id] = []
        exceptions_by_event[exception.event_id].append(exception)

    # Apply exceptions
    result_events = []
    for event in events:
        event_exceptions = exceptions_by_event.get(event.id, [])

        # Check if this specific occurrence should be modified or cancelled
        event_date = event.start_datetime.date()
        exception_for_date = None

        for exception in event_exceptions:
            if exception.exception_date == event_date:
                exception_for_date = exception
                break

        if exception_for_date:
            if exception_for_date.exception_type == "cancelled":
                # Skip cancelled events
                continue
            elif exception_for_date.exception_type in ["modified", "moved"]:
                # Apply modifications
                if exception_for_date.new_start_datetime:
                    event.start_datetime = exception_for_date.new_start_datetime
                if exception_for_date.new_end_datetime:
                    event.end_datetime = exception_for_date.new_end_datetime
                if exception_for_date.new_title:
                    event.title = exception_for_date.new_title
                if exception_for_date.new_description:
                    event.description = exception_for_date.new_description

        result_events.append(event)

    return result_events


def create_event_exception(
    db: Session, event: CalendarEvent, modifications: CalendarEventUpdate
):
    """
    Create an exception for a specific instance of a recurring event.
    """
    exception_date = event.start_datetime.date()

    db_exception = EventException(
        event_id=event.id,
        exception_date=exception_date,
        exception_type="modified",
        new_start_datetime=modifications.start_datetime,
        new_end_datetime=modifications.end_datetime,
        new_title=modifications.title,
        new_description=modifications.description,
        created_at=datetime.utcnow(),
    )

    db.add(db_exception)
    db.commit()


def has_calendar_conflict(
    db: Session, specialist_id: int, start_datetime: datetime, end_datetime: datetime
) -> bool:
    """
    Check if there are any calendar conflicts for the given time range.
    Considers all types of calendar events and buffer times.
    """
    conflicting_events = (
        db.query(CalendarEvent)
        .filter(
            CalendarEvent.specialist_id == specialist_id,
            CalendarEvent.is_active == True,
            CalendarEvent.start_datetime < end_datetime,
            CalendarEvent.end_datetime > start_datetime,
        )
        .all()
    )

    # Check for buffer time conflicts
    for event in conflicting_events:
        # Add buffer times to the event
        buffered_start = event.start_datetime - timedelta(minutes=event.buffer_before)
        buffered_end = event.end_datetime + timedelta(minutes=event.buffer_after)

        if buffered_start < end_datetime and buffered_end > start_datetime:
            return True

    return False


def generate_smart_availability_suggestions(
    db: Session, specialist_id: int, query: AvailabilityQuery
) -> List[SmartSchedulingSuggestion]:
    """
    Generate intelligent scheduling suggestions based on preferences, working hours, and patterns.
    Uses machine learning-like algorithms to suggest optimal times.
    """
    suggestions = []

    # Get specialist's preferences and working hours
    preferences = (
        db.query(SchedulingPreferences)
        .filter(
            SchedulingPreferences.specialist_id == specialist_id,
            SchedulingPreferences.is_active == True,
        )
        .first()
    )

    working_hours = (
        db.query(WorkingHours)
        .filter(
            WorkingHours.specialist_id == specialist_id, WorkingHours.is_active == True
        )
        .all()
    )

    # Generate time slots based on working hours
    current_datetime = query.start_datetime
    end_datetime = query.end_datetime
    duration = timedelta(minutes=query.duration_minutes)

    while current_datetime + duration <= end_datetime:
        # Check if this time falls within working hours
        if is_within_working_hours(current_datetime, working_hours):
            # Check for conflicts
            if not has_calendar_conflict(
                db, specialist_id, current_datetime, current_datetime + duration
            ):
                # Calculate confidence score based on various factors
                confidence = calculate_confidence_score(
                    db, specialist_id, current_datetime, query, preferences
                )

                suggestion = SmartSchedulingSuggestion(
                    suggested_datetime=current_datetime,
                    duration_minutes=query.duration_minutes,
                    confidence_score=confidence,
                    reason=f"Available slot with {confidence:.1%} confidence",
                    alternative_times=[],
                    conflicts=[],
                )
                suggestions.append(suggestion)

        # Move to next time slot
        increment = preferences.slot_increment if preferences else 30
        current_datetime += timedelta(minutes=increment)

    # Sort by confidence score and return top suggestions
    suggestions.sort(key=lambda x: x.confidence_score, reverse=True)
    return suggestions[:10]  # Return top 10 suggestions


def is_within_working_hours(
    check_datetime: datetime, working_hours: List[WorkingHours]
) -> bool:
    """
    Check if a datetime falls within the specialist's working hours.
    """
    weekday = check_datetime.weekday()  # 0=Monday, 6=Sunday
    check_time = check_datetime.time()

    for wh in working_hours:
        if wh.day_of_week == weekday and wh.is_working_day:
            # Parse time ranges from JSON
            time_ranges = json.loads(wh.time_ranges)
            for tr in time_ranges:
                if tr.get("start_time") and tr.get("end_time"):
                    start_time = time.fromisoformat(tr["start_time"])
                    end_time = time.fromisoformat(tr["end_time"])
                    if start_time <= check_time <= end_time:
                        return True

    return False


def calculate_confidence_score(
    db: Session,
    specialist_id: int,
    suggested_datetime: datetime,
    query: AvailabilityQuery,
    preferences: Optional[SchedulingPreferences],
) -> float:
    """
    Calculate a confidence score for a suggested time slot based on multiple factors.
    """
    score = 1.0

    # Factor 1: Time of day preferences (higher score for mid-morning/afternoon)
    hour = suggested_datetime.hour
    if 9 <= hour <= 11 or 14 <= hour <= 16:
        score *= 1.0  # Peak times
    elif 8 <= hour <= 9 or 11 <= hour <= 14 or 16 <= hour <= 17:
        score *= 0.8  # Good times
    else:
        score *= 0.6  # Off-peak times

    # Factor 2: Day of week preferences (weekdays typically better)
    weekday = suggested_datetime.weekday()
    if 0 <= weekday <= 4:  # Monday to Friday
        score *= 1.0
    else:  # Weekend
        score *= 0.7

    # Factor 3: Advance booking notice
    if preferences:
        notice_hours = (suggested_datetime - datetime.utcnow()).total_seconds() / 3600
        min_notice_hours = preferences.min_booking_notice / 60
        if notice_hours >= min_notice_hours * 2:
            score *= 1.0  # Good advance notice
        elif notice_hours >= min_notice_hours:
            score *= 0.8  # Adequate notice
        else:
            score *= 0.3  # Short notice

    # Factor 4: Buffer around existing appointments
    nearby_events = (
        db.query(CalendarEvent)
        .filter(
            CalendarEvent.specialist_id == specialist_id,
            CalendarEvent.is_active == True,
            CalendarEvent.start_datetime >= suggested_datetime - timedelta(hours=2),
            CalendarEvent.end_datetime <= suggested_datetime + timedelta(hours=2),
        )
        .all()
    )

    if len(nearby_events) == 0:
        score *= 1.0  # No nearby events
    elif len(nearby_events) <= 2:
        score *= 0.9  # Some nearby events
    else:
        score *= 0.7  # Busy period

    return min(score, 1.0)


def execute_bulk_calendar_operation(
    db: Session, specialist_id: int, operation: BulkEventOperation
) -> List[CalendarEventResponse]:
    """
    Execute bulk operations on calendar events for efficiency.
    """
    results = []

    if operation.operation == "create":
        for event_data in operation.events:
            # Convert to CalendarEventCreate if needed
            if isinstance(event_data, CalendarEventUpdate):
                # Skip updates in create operation
                continue

            # Create the event
            db_event = CalendarEvent(
                specialist_id=specialist_id,
                **event_data.dict(),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(db_event)
            results.append(db_event)

    elif operation.operation == "update":
        # Batch update operations
        for event_data in operation.events:
            if hasattr(event_data, "id") and event_data.id:
                db_event = (
                    db.query(CalendarEvent)
                    .filter(
                        CalendarEvent.id == event_data.id,
                        CalendarEvent.specialist_id == specialist_id,
                    )
                    .first()
                )

                if db_event:
                    for field, value in event_data.dict(exclude_unset=True).items():
                        if field != "id":
                            setattr(db_event, field, value)
                    db_event.updated_at = datetime.utcnow()
                    results.append(db_event)

    db.commit()

    # Refresh all results
    for result in results:
        db.refresh(result)

    return results


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
    booking_date: date
    start_time: time
    client_name: str
    client_email: EmailStr
    client_phone: Optional[str] = None
    notes: Optional[str] = None


class BookingResponse(BaseModel):
    id: int
    specialist_id: int
    service_id: int
    client_name: str
    client_email: str
    client_phone: Optional[str] = None
    notes: Optional[str] = None
    date: date
    start_time: time
    end_time: time
    status: str

    class Config:
        from_attributes = True


class BookingWithServiceResponse(BaseModel):
    id: int
    specialist_id: int
    service_id: int
    client_name: str
    client_email: str
    client_phone: Optional[str] = None
    notes: Optional[str] = None
    date: date
    start_time: time
    end_time: time
    status: str
    service: Optional[dict] = None

    class Config:
        from_attributes = True


class BookingStatusUpdate(BaseModel):
    status: str


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


# Advanced Calendar Models - Google Calendar Level Flexibility


class RecurrenceRule(BaseModel):
    """Comprehensive recurrence rule similar to RFC 5545 RRULE"""

    freq: str  # 'DAILY', 'WEEKLY'
    interval: int = 1  # Every N days/weeks
    byweekday: Optional[List[int]] = None  # Days of week (0=Mon, 6=Sun)
    bymonthday: Optional[List[int]] = None  # Days of month (1-31)
    bymonth: Optional[List[int]] = None  # Months (1-12)
    byyearday: Optional[List[int]] = None  # Day of year (1-366)
    bysetpos: Optional[List[int]] = None  # Nth occurrence (1st Monday, last Friday)
    wkst: int = 0  # Week start (0=Monday)
    until: Optional[date] = None  # End date for recurrence
    count: Optional[int] = None  # Maximum occurrences

    # Advanced patterns
    byweekno: Optional[List[int]] = None  # Week numbers
    byhour: Optional[List[int]] = None  # Hours (0-23)
    byminute: Optional[List[int]] = None  # Minutes (0-59)


class TimeRange(BaseModel):
    """Flexible time range supporting both date-times and all-day events"""

    start_time: Optional[time] = None
    end_time: Optional[time] = None
    start_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None
    is_all_day: bool = False
    timezone: str = "UTC"


class CalendarEventCreate(BaseModel):
    title: str
    description: Optional[str] = None
    location: Optional[str] = None

    # Time settings - flexible for both timed and all-day events
    start_datetime: datetime
    end_datetime: datetime
    is_all_day: bool = False
    timezone: str = "UTC"

    # Event classification
    event_type: str = "availability"  # 'availability', 'block', 'appointment', 'break'
    category: Optional[str] = None
    priority: str = "normal"  # 'low', 'normal', 'high', 'urgent'
    color: Optional[str] = None

    # Availability settings
    is_bookable: bool = True
    max_bookings: Optional[int] = None
    buffer_before: int = 0  # Minutes
    buffer_after: int = 0  # Minutes

    # Recurrence
    is_recurring: bool = False
    recurrence_rule: Optional[RecurrenceRule] = None

    # Status
    status: str = "confirmed"  # 'tentative', 'confirmed', 'cancelled'
    visibility: str = "public"  # 'public', 'private'


class CalendarEventResponse(CalendarEventCreate):
    id: int
    specialist_id: int
    recurring_event_id: Optional[str] = None
    original_start: Optional[datetime] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CalendarEventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    start_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None
    is_all_day: Optional[bool] = None
    timezone: Optional[str] = None
    event_type: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = None
    color: Optional[str] = None
    is_bookable: Optional[bool] = None
    max_bookings: Optional[int] = None
    buffer_before: Optional[int] = None
    buffer_after: Optional[int] = None
    status: Optional[str] = None
    visibility: Optional[str] = None
    is_active: Optional[bool] = None


class EventExceptionCreate(BaseModel):
    exception_date: date
    exception_type: str  # 'cancelled', 'modified', 'moved'
    new_start_datetime: Optional[datetime] = None
    new_end_datetime: Optional[datetime] = None
    new_title: Optional[str] = None
    new_description: Optional[str] = None


class EventExceptionResponse(EventExceptionCreate):
    id: int
    event_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class WorkingHoursCreate(BaseModel):
    day_of_week: int  # 0=Monday, 6=Sunday
    time_ranges: List[TimeRange]
    is_working_day: bool = True
    break_duration: int = 0  # Minutes
    break_start_time: Optional[time] = None
    timezone: str = "UTC"
    effective_date: Optional[date] = None


class WorkingHoursResponse(WorkingHoursCreate):
    id: int
    specialist_id: int
    is_active: bool

    class Config:
        from_attributes = True


class SchedulingPreferencesCreate(BaseModel):
    # Buffer times
    default_buffer_before: int = 15
    default_buffer_after: int = 15

    # Booking windows
    advance_booking_days: int = 365
    min_booking_notice: int = 60  # Minutes

    # Limits
    auto_accept_bookings: bool = True
    max_daily_bookings: Optional[int] = None
    max_weekly_bookings: Optional[int] = None

    # Time preferences
    minimum_slot_duration: int = 15
    slot_increment: int = 15

    # Breaks
    lunch_break_start: Optional[time] = None
    lunch_break_duration: int = 60
    travel_time_between_appointments: int = 0

    # Locale
    timezone: str = "UTC"
    date_format: str = "YYYY-MM-DD"
    time_format: str = "24h"

    # Notifications
    email_reminders: bool = True
    sms_reminders: bool = False
    reminder_advance_time: int = 1440  # Minutes


class SchedulingPreferencesResponse(SchedulingPreferencesCreate):
    id: int
    specialist_id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BulkEventOperation(BaseModel):
    operation: str  # 'create', 'update', 'delete', 'move'
    events: List[Union[CalendarEventCreate, CalendarEventUpdate]]
    apply_to_series: bool = False  # For recurring events


class CalendarView(BaseModel):
    start_date: date
    end_date: date
    view_type: str = "week"  # 'day', 'week', 'month', 'year'
    timezone: str = "UTC"
    include_all_day: bool = True
    event_types: Optional[List[str]] = None
    categories: Optional[List[str]] = None


class SmartSchedulingSuggestion(BaseModel):
    suggested_datetime: datetime
    duration_minutes: int
    confidence_score: float  # 0.0 to 1.0
    reason: str
    alternative_times: List[datetime]
    conflicts: List[str]


class AvailabilityQuery(BaseModel):
    start_datetime: datetime
    end_datetime: datetime
    duration_minutes: int
    service_id: Optional[int] = None
    buffer_minutes: int = 0
    preferred_times: Optional[List[TimeRange]] = None
    exclude_weekends: bool = False


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


# Advanced Calendar Event Management - Google Calendar Level Features


@app.post(
    "/specialist/{specialist_id}/calendar/events",
    response_model=CalendarEventResponse,
)
def create_calendar_event(
    specialist_id: int,
    event: CalendarEventCreate,
    db: Session = Depends(get_db),
    current_specialist: Specialist = Depends(require_authentication),
):
    """
    Create a calendar event with advanced recurrence and flexibility options.
    Supports Google Calendar-level features including complex recurrence rules.
    """
    if current_specialist.id != specialist_id:
        raise HTTPException(
            status_code=403, detail="You can only manage your own calendar"
        )

    # Generate recurring event ID for recurring events
    recurring_event_id = None
    if event.is_recurring:
        recurring_event_id = f"{specialist_id}_{datetime.utcnow().timestamp()}"

    # Convert recurrence rule to JSON
    recurrence_json = None
    if event.recurrence_rule:
        recurrence_json = event.recurrence_rule.json()

    db_event = CalendarEvent(
        specialist_id=specialist_id,
        title=event.title,
        description=event.description,
        location=event.location,
        start_datetime=event.start_datetime,
        end_datetime=event.end_datetime,
        is_all_day=event.is_all_day,
        timezone=event.timezone,
        event_type=event.event_type,
        category=event.category,
        priority=event.priority,
        color=event.color,
        is_bookable=event.is_bookable,
        max_bookings=event.max_bookings,
        buffer_before=event.buffer_before,
        buffer_after=event.buffer_after,
        is_recurring=event.is_recurring,
        recurrence_rule=recurrence_json,
        status=event.status,
        visibility=event.visibility,
        recurring_event_id=recurring_event_id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    db.add(db_event)
    db.commit()
    db.refresh(db_event)

    # Generate recurring event instances if needed
    if event.is_recurring and event.recurrence_rule:
        generate_recurring_event_instances(db, db_event, event.recurrence_rule)

    return db_event


@app.get(
    "/specialist/{specialist_id}/calendar/events",
    response_model=List[CalendarEventResponse],
)
def get_calendar_events(
    specialist_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    event_types: Optional[str] = None,  # Comma-separated list
    categories: Optional[str] = None,  # Comma-separated list
    include_recurring: bool = True,
    db: Session = Depends(get_db),
    current_specialist: Optional[Specialist] = Depends(get_current_user),
):
    """
    Get calendar events with advanced filtering options.
    Public availability events are visible to everyone, private events only to owner.
    """
    query = db.query(CalendarEvent).filter(
        CalendarEvent.specialist_id == specialist_id, CalendarEvent.is_active == True
    )

    # Privacy filter - only show public events to non-owners
    if not current_specialist or current_specialist.id != specialist_id:
        query = query.filter(CalendarEvent.visibility == "public")

    # Date filtering
    if start_date:
        query = query.filter(
            CalendarEvent.end_datetime >= datetime.combine(start_date, time.min)
        )
    if end_date:
        query = query.filter(
            CalendarEvent.start_datetime <= datetime.combine(end_date, time.max)
        )

    # Event type filtering
    if event_types:
        type_list = [t.strip() for t in event_types.split(",")]
        query = query.filter(CalendarEvent.event_type.in_(type_list))

    # Category filtering
    if categories:
        category_list = [c.strip() for c in categories.split(",")]
        query = query.filter(CalendarEvent.category.in_(category_list))

    events = query.order_by(CalendarEvent.start_datetime).all()

    # Apply recurring event exceptions
    if include_recurring:
        events = apply_recurring_exceptions(db, events, start_date, end_date)

    return events


@app.put(
    "/specialist/{specialist_id}/calendar/events/{event_id}",
    response_model=CalendarEventResponse,
)
def update_calendar_event(
    specialist_id: int,
    event_id: int,
    event_update: CalendarEventUpdate,
    modify_series: bool = False,  # For recurring events - modify entire series or just this instance
    db: Session = Depends(get_db),
    current_specialist: Specialist = Depends(require_authentication),
):
    """
    Update calendar event with support for modifying recurring series or individual instances.
    """
    if current_specialist.id != specialist_id:
        raise HTTPException(
            status_code=403, detail="You can only manage your own calendar"
        )

    db_event = (
        db.query(CalendarEvent)
        .filter(
            CalendarEvent.id == event_id, CalendarEvent.specialist_id == specialist_id
        )
        .first()
    )

    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")

    # Handle recurring event modifications
    if db_event.is_recurring and not modify_series:
        # Create exception for this specific instance
        create_event_exception(db, db_event, event_update)
    else:
        # Update the event directly
        for field, value in event_update.dict(exclude_unset=True).items():
            setattr(db_event, field, value)

        db_event.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(db_event)

    return db_event


@app.delete("/specialist/{specialist_id}/calendar/events/{event_id}")
def delete_calendar_event(
    specialist_id: int,
    event_id: int,
    delete_series: bool = False,  # For recurring events
    db: Session = Depends(get_db),
    current_specialist: Specialist = Depends(require_authentication),
):
    """
    Delete calendar event with support for recurring event series management.
    """
    if current_specialist.id != specialist_id:
        raise HTTPException(
            status_code=403, detail="You can only manage your own calendar"
        )

    db_event = (
        db.query(CalendarEvent)
        .filter(
            CalendarEvent.id == event_id, CalendarEvent.specialist_id == specialist_id
        )
        .first()
    )

    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")

    if db_event.is_recurring and delete_series:
        # Delete entire recurring series
        db.query(CalendarEvent).filter(
            CalendarEvent.recurring_event_id == db_event.recurring_event_id
        ).update({"is_active": False})
    else:
        # Delete just this event
        db_event.is_active = False

    db.commit()

    return {"message": "Event deleted successfully"}


# Recurring Schedule Management (Simplified Interface)


class RecurringScheduleCreate(BaseModel):
    recurrence_type: str  # 'daily' or 'weekly'
    days_of_week: Optional[List[int]] = None  # For weekly: 0=Monday, 6=Sunday
    start_time: str  # Format: "09:00"
    end_time: str  # Format: "17:00"
    start_date: str  # Format: "2024-01-01"
    end_date: Optional[str] = None  # Format: "2024-12-31"


@app.post("/specialist/{specialist_id}/recurring-schedule")
def create_recurring_schedule(
    specialist_id: int,
    schedule: RecurringScheduleCreate,
    db: Session = Depends(get_db),
    current_specialist: Specialist = Depends(require_authentication),
):
    """
    Create recurring schedule using simplified interface that maps to calendar events.
    """
    if current_specialist.id != specialist_id:
        raise HTTPException(
            status_code=403, detail="You can only manage your own schedule"
        )

    # Build recurrence rule based on simple interface
    if schedule.recurrence_type == "daily":
        freq = "DAILY"
        byweekday = None
    elif schedule.recurrence_type == "weekly":
        if not schedule.days_of_week or len(schedule.days_of_week) == 0:
            raise HTTPException(
                status_code=400, detail="Days of week required for weekly schedule"
            )
        freq = "WEEKLY"
        byweekday = schedule.days_of_week
    else:
        raise HTTPException(
            status_code=400,
            detail="Unsupported recurrence type. Use 'daily' or 'weekly'",
        )

    # Parse dates and times
    try:
        start_date = datetime.strptime(schedule.start_date, "%Y-%m-%d").date()
        start_time_obj = datetime.strptime(schedule.start_time, "%H:%M").time()
        end_time_obj = datetime.strptime(schedule.end_time, "%H:%M").time()

        start_datetime = datetime.combine(start_date, start_time_obj)
        end_datetime = datetime.combine(start_date, end_time_obj)

        end_date = None
        if schedule.end_date:
            end_date = datetime.strptime(schedule.end_date, "%Y-%m-%d").date()
    except ValueError as e:
        raise HTTPException(
            status_code=400, detail=f"Invalid date/time format: {str(e)}"
        )

    # Create recurrence rule
    recurrence_rule = RecurrenceRule(
        freq=freq, interval=1, byweekday=byweekday, until=end_date
    )

    # Generate recurring event ID
    recurring_event_id = f"{specialist_id}_{datetime.utcnow().timestamp()}"

    # Create base calendar event
    db_event = CalendarEvent(
        specialist_id=specialist_id,
        title=f"{schedule.recurrence_type.title()} Availability",
        description=f"Recurring {schedule.recurrence_type} availability from {schedule.start_time} to {schedule.end_time}",
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        is_all_day=False,
        timezone="UTC",
        event_type="availability",
        category="schedule",
        priority="normal",
        color="#4CAF50",
        is_bookable=True,
        max_bookings=1,
        buffer_before=0,
        buffer_after=0,
        is_recurring=True,
        recurrence_rule=recurrence_rule.json(),
        status="confirmed",
        visibility="public",
        recurring_event_id=recurring_event_id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    db.add(db_event)
    db.commit()
    db.refresh(db_event)

    # Generate recurring instances
    generate_recurring_event_instances(db, db_event, recurrence_rule)

    return {
        "message": "Recurring schedule created successfully",
        "event_id": db_event.id,
        "recurring_event_id": recurring_event_id,
        "recurrence_type": schedule.recurrence_type,
    }


@app.get("/specialist/{specialist_id}/recurring-schedules")
def get_recurring_schedules(
    specialist_id: int,
    db: Session = Depends(get_db),
    current_specialist: Specialist = Depends(require_authentication),
):
    """
    Get all recurring schedules for a specialist.
    """
    if current_specialist.id != specialist_id:
        raise HTTPException(
            status_code=403, detail="You can only view your own schedules"
        )

    # Get all recurring calendar events (base events only, not instances)
    recurring_events = (
        db.query(CalendarEvent)
        .filter(
            CalendarEvent.specialist_id == specialist_id,
            CalendarEvent.is_recurring == True,
            CalendarEvent.is_active == True,
            CalendarEvent.recurring_event_id != None,
        )
        .all()
    )

    schedules = []
    for event in recurring_events:
        recurrence_rule = None
        if event.recurrence_rule:
            try:
                import json

                recurrence_data = json.loads(event.recurrence_rule)
                recurrence_rule = RecurrenceRule(**recurrence_data)
            except:
                continue

        schedules.append(
            {
                "id": event.id,
                "title": event.title,
                "recurrence_type": (
                    recurrence_rule.freq.lower() if recurrence_rule else "unknown"
                ),
                "days_of_week": recurrence_rule.byweekday if recurrence_rule else None,
                "start_time": event.start_datetime.strftime("%H:%M"),
                "end_time": event.end_datetime.strftime("%H:%M"),
                "start_date": event.start_datetime.strftime("%Y-%m-%d"),
                "end_date": (
                    recurrence_rule.until.strftime("%Y-%m-%d")
                    if recurrence_rule and recurrence_rule.until
                    else None
                ),
                "created_at": event.created_at.isoformat(),
            }
        )

    return schedules


# Smart Scheduling and Availability


@app.post(
    "/specialist/{specialist_id}/calendar/find-availability",
    response_model=List[SmartSchedulingSuggestion],
)
def find_smart_availability(
    specialist_id: int,
    query: AvailabilityQuery,
    db: Session = Depends(get_db),
):
    """
    Find optimal availability slots using smart scheduling algorithms.
    Considers working hours, existing events, preferences, and travel time.
    """
    return generate_smart_availability_suggestions(db, specialist_id, query)


@app.post(
    "/specialist/{specialist_id}/calendar/bulk-operations",
    response_model=List[CalendarEventResponse],
)
def bulk_calendar_operations(
    specialist_id: int,
    operation: BulkEventOperation,
    db: Session = Depends(get_db),
    current_specialist: Specialist = Depends(require_authentication),
):
    """
    Perform bulk operations on calendar events for efficiency.
    Supports creating multiple events, batch updates, etc.
    """
    if current_specialist.id != specialist_id:
        raise HTTPException(
            status_code=403, detail="You can only manage your own calendar"
        )

    return execute_bulk_calendar_operation(db, specialist_id, operation)


# Working Hours and Preferences Management


@app.post(
    "/specialist/{specialist_id}/working-hours",
    response_model=WorkingHoursResponse,
)
def set_working_hours(
    specialist_id: int,
    working_hours: WorkingHoursCreate,
    db: Session = Depends(get_db),
    current_specialist: Specialist = Depends(require_authentication),
):
    """
    Set working hours with support for multiple time ranges per day and breaks.
    """
    if current_specialist.id != specialist_id:
        raise HTTPException(
            status_code=403, detail="You can only manage your own working hours"
        )

    # Convert time ranges to JSON
    time_ranges_json = json.dumps(
        [
            {
                "start_time": tr.start_time.isoformat() if tr.start_time else None,
                "end_time": tr.end_time.isoformat() if tr.end_time else None,
                "start_datetime": (
                    tr.start_datetime.isoformat() if tr.start_datetime else None
                ),
                "end_datetime": (
                    tr.end_datetime.isoformat() if tr.end_datetime else None
                ),
                "is_all_day": tr.is_all_day,
                "timezone": tr.timezone,
            }
            for tr in working_hours.time_ranges
        ]
    )

    db_working_hours = WorkingHours(
        specialist_id=specialist_id,
        day_of_week=working_hours.day_of_week,
        time_ranges=time_ranges_json,
        is_working_day=working_hours.is_working_day,
        break_duration=working_hours.break_duration,
        break_start_time=working_hours.break_start_time,
        timezone=working_hours.timezone,
        effective_date=working_hours.effective_date or date.today(),
        is_active=True,
    )

    db.add(db_working_hours)
    db.commit()
    db.refresh(db_working_hours)

    return db_working_hours


@app.get(
    "/specialist/{specialist_id}/working-hours",
    response_model=List[WorkingHoursResponse],
)
def get_working_hours(
    specialist_id: int,
    db: Session = Depends(get_db),
):
    """
    Get working hours configuration for a specialist.
    """
    working_hours = (
        db.query(WorkingHours)
        .filter(
            WorkingHours.specialist_id == specialist_id, WorkingHours.is_active == True
        )
        .order_by(WorkingHours.day_of_week)
        .all()
    )

    return working_hours


@app.post(
    "/specialist/{specialist_id}/preferences",
    response_model=SchedulingPreferencesResponse,
)
def set_scheduling_preferences(
    specialist_id: int,
    preferences: SchedulingPreferencesCreate,
    db: Session = Depends(get_db),
    current_specialist: Specialist = Depends(require_authentication),
):
    """
    Set comprehensive scheduling preferences for intelligent calendar management.
    """
    if current_specialist.id != specialist_id:
        raise HTTPException(
            status_code=403, detail="You can only manage your own preferences"
        )

    # Check if preferences already exist
    existing = (
        db.query(SchedulingPreferences)
        .filter(
            SchedulingPreferences.specialist_id == specialist_id,
            SchedulingPreferences.is_active == True,
        )
        .first()
    )

    if existing:
        # Update existing preferences
        for field, value in preferences.dict().items():
            setattr(existing, field, value)
        existing.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        return existing
    else:
        # Create new preferences
        db_preferences = SchedulingPreferences(
            specialist_id=specialist_id,
            **preferences.dict(),
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(db_preferences)
        db.commit()
        db.refresh(db_preferences)
        return db_preferences


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

            # Check if this slot conflicts with calendar events (blocks, PTO, etc.)
            if not conflict:
                calendar_conflict = has_calendar_conflict(
                    db,
                    specialist_id,
                    datetime.combine(booking_date, current_time.time()),
                    datetime.combine(booking_date, slot_end.time()),
                )
                conflict = calendar_conflict

            if not conflict:
                available_slots.append(
                    {
                        "start_time": current_time.time(),
                        "end_time": slot_end.time(),
                        "duration_minutes": service_duration,
                    }
                )

            # Increment by the shortest service duration to allow booking any service
            # This ensures customers can book any service at properly spaced intervals
            current_time += timedelta(minutes=service_duration)

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

    # Validate that there's an availability slot covering this time
    availability_slots = (
        db.query(AvailabilitySlot)
        .filter(
            AvailabilitySlot.specialist_id == booking.specialist_id,
            AvailabilitySlot.date == booking.booking_date,
            AvailabilitySlot.is_available == True,
        )
        .all()
    )

    # Check if the requested time falls within any availability slot
    booking_start = datetime.combine(booking.booking_date, booking.start_time)
    booking_end = booking_start + timedelta(minutes=service.duration)

    valid_slot = None
    for slot in availability_slots:
        slot_start = datetime.combine(slot.date, slot.start_time)
        slot_end = datetime.combine(slot.date, slot.end_time)

        # Check if booking fits within this availability slot
        if booking_start >= slot_start and booking_end <= slot_end:
            valid_slot = slot
            break

    if not valid_slot:
        raise HTTPException(
            status_code=404, detail="No availability slot covers the requested time"
        )

    # Check for conflicts with existing bookings
    existing_booking = (
        db.query(Booking)
        .filter(
            Booking.specialist_id == booking.specialist_id,
            Booking.date == booking.booking_date,
            Booking.status == "confirmed",
        )
        .filter(
            # Check for time overlap
            (Booking.start_time < booking_end.time())
            & (Booking.end_time > booking_start.time())
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
        date=booking.booking_date,
        start_time=booking.start_time,
        end_time=booking_end.time(),
        notes=booking.notes,
        status="confirmed",
    )

    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)

    return db_booking


@app.get(
    "/bookings/specialist/{specialist_id}",
    response_model=List[BookingWithServiceResponse],
)
def get_specialist_bookings(specialist_id: int, db: Session = Depends(get_db)):
    """
    Get all bookings for a specialist with service details.
    """
    bookings = (
        db.query(Booking)
        .filter(Booking.specialist_id == specialist_id)
        .join(ServiceDB)
        .all()
    )

    # Add service details to each booking
    booking_responses = []
    for booking in bookings:
        booking_dict = {
            "id": booking.id,
            "specialist_id": booking.specialist_id,
            "service_id": booking.service_id,
            "client_name": booking.client_name,
            "client_email": booking.client_email,
            "client_phone": booking.client_phone,
            "notes": booking.notes,
            "date": booking.date,
            "start_time": booking.start_time,
            "end_time": booking.end_time,
            "status": booking.status,
            "service": {
                "id": booking.service.id,
                "name": booking.service.name,
                "price": booking.service.price,
                "duration": booking.service.duration,
            },
        }
        booking_responses.append(booking_dict)

    return booking_responses


@app.put("/booking/{booking_id}/status")
def update_booking_status(
    booking_id: int, status_update: BookingStatusUpdate, db: Session = Depends(get_db)
):
    """
    Update the status of a booking (e.g., completed, cancelled).
    """
    # Validate status
    valid_statuses = ["confirmed", "completed", "cancelled"]
    if status_update.status not in valid_statuses:
        raise HTTPException(
            status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}"
        )

    # Find the booking
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    # Update the status
    old_status = booking.status
    booking.status = status_update.status
    db.commit()
    db.refresh(booking)

    return {
        "message": f"Booking status updated from {old_status} to {status_update.status}",
        "booking_id": booking_id,
        "new_status": status_update.status,
    }
