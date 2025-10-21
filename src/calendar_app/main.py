"""
poetry run uvicorn main:app --reload
"""

from __future__ import annotations
from typing import Union, List, Optional
from datetime import date, time, datetime, timedelta
import secrets
import json
from contextlib import asynccontextmanager

# Note: dateutil will need to be installed: pip install python-dateutil
try:
    from dateutil.rrule import rrule, DAILY, WEEKLY
    from dateutil.rrule import MO, TU, WE, TH, FR, SA, SU

    DATEUTIL_AVAILABLE = True
except ImportError:
    DATEUTIL_AVAILABLE = False
from fastapi import (
    FastAPI,
    Depends,
    HTTPException,
    Request,
    Cookie,
    Response,
    Query,
    UploadFile,
    File,
)
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from sqlalchemy import func
import jwt
import csv
import io

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
        Workplace,
        specialist_workplace_association,
        Consumer,
        Referral,
        ClientProfile,
    )
    from .verification_service import verification_service
    from .yelp_service import yelp_service, YelpAPIError
    from .models import (
        # Core service models
        Service,
        ServiceResponse,
        # Workplace models
        WorkplaceCreate,
        WorkplaceResponse,
        WorkplaceUpdate,
        YelpBusinessSearch,
        YelpBusinessResponse,
        SpecialistWorkplaceAssociation,
        SpecialistWorkplaceResponse,
        # Specialist models
        SpecialistCreate,
        SpecialistResponse,
        SpecialistCatalogResponse,
        # Availability models
        AvailabilitySlotCreate,
        AvailabilitySlotResponse,
        TimeSlotResponse,
        TimeRange,
        AvailabilityQuery,
        # Booking models
        BookingCreate,
        BookingResponse,
        BookingWithServiceResponse,
        BookingStatusUpdate,
        # Calendar models
        RecurrenceRule,
        CalendarEventCreate,
        CalendarEventResponse,
        CalendarEventUpdate,
        EventExceptionCreate,
        EventExceptionResponse,
        BulkEventOperation,
        CalendarView,
        # Working hours and preferences
        WorkingHoursCreate,
        WorkingHoursResponse,
        SchedulingPreferencesCreate,
        SchedulingPreferencesResponse,
        # Smart scheduling
        SmartSchedulingSuggestion,
        # Authentication models
        LoginRequest,
        AuthResponse,
        # Verification models
        VerificationRequest,
        VerificationResponse,
        CodeVerificationRequest,
        CodeVerificationResponse,
        # Consumer models
        ConsumerCreate,
        ConsumerResponse,
        # Referral models
        ReferralCreate,
        ReferralResponse,
        # Error models
        ErrorResponse,
    )
    from .auth import (
        JWT_SECRET_KEY,
        JWT_ALGORITHM,
        ACCESS_TOKEN_EXPIRE_HOURS,
        security,
        create_access_token,
        verify_token,
        get_current_specialist,
        require_authentication,
        get_current_specialist_dep,
        require_authentication_dep,
    )
    from .config import settings
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
        Workplace,
        specialist_workplace_association,
        Consumer,
        Referral,
        ClientProfile,
    )
    from verification_service import verification_service
    from models import (
        # Core service models
        Service,
        ServiceResponse,
        # Specialist models
        SpecialistCreate,
        SpecialistResponse,
        SpecialistCatalogResponse,
        # Availability models
        AvailabilitySlotCreate,
        AvailabilitySlotResponse,
        TimeSlotResponse,
        TimeRange,
        AvailabilityQuery,
        # Booking models
        BookingCreate,
        BookingResponse,
        BookingWithServiceResponse,
        BookingStatusUpdate,
        # Calendar models
        RecurrenceRule,
        CalendarEventCreate,
        CalendarEventResponse,
        CalendarEventUpdate,
        EventExceptionCreate,
        EventExceptionResponse,
        BulkEventOperation,
        CalendarView,
        # Working hours and preferences
        WorkingHoursCreate,
        WorkingHoursResponse,
        SchedulingPreferencesCreate,
        SchedulingPreferencesResponse,
        # Smart scheduling
        SmartSchedulingSuggestion,
        # Authentication models
        LoginRequest,
        AuthResponse,
        # Verification models
        VerificationRequest,
        VerificationResponse,
        CodeVerificationRequest,
        CodeVerificationResponse,
        # Error models
        ErrorResponse,
    )
    from auth import (
        JWT_SECRET_KEY,
        JWT_ALGORITHM,
        ACCESS_TOKEN_EXPIRE_HOURS,
        security,
        create_access_token,
        verify_token,
        get_current_specialist,
        require_authentication,
        get_current_specialist_dep,
        require_authentication_dep,
    )
    from config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown events."""
    # Startup: Initialize database connection
    await database.connect()
    yield
    # Shutdown: Close database connection
    await database.disconnect()


app = FastAPI(
    title="Élite Scheduling Platform",
    description="A luxury scheduling platform for professionals and clients",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,  # Use settings instead of hardcoded "*"
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import os
from pathlib import Path

# Get the directory where this file is located
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Mount static files
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


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
    db: Session,
    specialist_id: int,
    start_datetime: datetime,
    end_datetime: datetime,
    exclude_event_id: Optional[int] = None,
) -> bool:
    """
    Check if there are any calendar conflicts for the given time range.
    Considers all types of calendar events and buffer times.
    """
    query = db.query(CalendarEvent).filter(
        CalendarEvent.specialist_id == specialist_id,
        CalendarEvent.is_active == True,
        CalendarEvent.start_datetime < end_datetime,
        CalendarEvent.end_datetime > start_datetime,
    )

    # Exclude specific event if provided (useful for availability events)
    if exclude_event_id:
        query = query.filter(CalendarEvent.id != exclude_event_id)

    conflicting_events = query.all()

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


@app.get("/search", response_class=HTMLResponse)
async def search_page(request: Request):
    """
    Unified search page with Yelp-style interface.
    """
    return templates.TemplateResponse("search.html", {"request": request})


@app.get("/consumer", response_class=HTMLResponse)
async def consumer_portal(request: Request):
    return templates.TemplateResponse("consumer.html", {"request": request})


@app.get("/consumer/business/{business_id}", response_class=HTMLResponse)
async def consumer_business_page(
    request: Request, business_id: int, db: Session = Depends(get_db)
):
    """
    Business detail page showing professionals at that business.
    Used for the business-first booking flow.
    """
    business = db.query(Workplace).filter(Workplace.id == business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    return templates.TemplateResponse(
        "consumer_business.html",
        {
            "request": request,
            "business_name": business.name,
            "business_id": business_id,
        },
    )


@app.get("/consumer/professional/{specialist_id}", response_class=HTMLResponse)
async def consumer_professional_page(
    request: Request, specialist_id: int, db: Session = Depends(get_db)
):
    specialist = db.query(Specialist).filter(Specialist.id == specialist_id).first()
    if not specialist:
        raise HTTPException(status_code=404, detail="Professional not found")

    return templates.TemplateResponse(
        "consumer_professional.html", {"request": request, "specialist": specialist}
    )


@app.get(
    "/consumer/professional/{specialist_id}/service/{service_id}",
    response_class=HTMLResponse,
)
async def consumer_booking_page(
    request: Request, specialist_id: int, service_id: int, db: Session = Depends(get_db)
):
    specialist = db.query(Specialist).filter(Specialist.id == specialist_id).first()
    if not specialist:
        raise HTTPException(status_code=404, detail="Professional not found")

    service = (
        db.query(ServiceDB)
        .filter(ServiceDB.id == service_id, ServiceDB.specialist_id == specialist_id)
        .first()
    )
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    return templates.TemplateResponse(
        "consumer_booking.html",
        {"request": request, "specialist": specialist, "service": service},
    )


"""
Desired features

We want to build a simple API that allows us to:

1. Takes a specialist's services and their prices. 
2. Allows a user to choose a time slot for a service.
"""


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


@app.post("/verification/verify")
async def verify_code(request: CodeVerificationRequest, db: Session = Depends(get_db)):
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

    # Convert specialist to response format
    specialist_response = SpecialistResponse(
        id=specialist.id,
        name=specialist.name,
        email=specialist.email,
        bio=specialist.bio,
        phone=specialist.phone,
        services=[],
    )

    # Create response with cookie
    response_data = CodeVerificationResponse(
        success=True,
        verified=True,
        message="Verification successful! You are now signed in.",
        access_token=access_token,
        specialist=specialist_response,
    )

    # Create JSON response and set cookie
    json_response = JSONResponse(content=response_data.model_dump())
    json_response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS, False for localhost
        samesite="lax",
        max_age=ACCESS_TOKEN_EXPIRE_HOURS * 3600,
        path="/",  # Ensure cookie is available for all paths
    )

    return json_response


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
    current_specialist: Specialist = Depends(require_authentication_dep),
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
    current_specialist: Specialist = Depends(require_authentication_dep),
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
    current_specialist: Specialist = Depends(require_authentication_dep),
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
    current_specialist: Specialist = Depends(require_authentication_dep),
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
    current_specialist: Specialist = Depends(require_authentication_dep),
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
    current_specialist: Specialist = Depends(require_authentication_dep),
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
    current_specialist: Specialist = Depends(require_authentication_dep),
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
    current_specialist: Specialist = Depends(require_authentication_dep),
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
    current_specialist: Specialist = Depends(require_authentication_dep),
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
    current_specialist: Specialist = Depends(require_authentication_dep),
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
    current_specialist: Specialist = Depends(require_authentication_dep),
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

    # Also get calendar events that represent availability (from recurring schedules)
    calendar_availability = (
        db.query(CalendarEvent)
        .filter(
            CalendarEvent.specialist_id == specialist_id,
            CalendarEvent.event_type == "availability",
            CalendarEvent.status == "confirmed",
            func.date(CalendarEvent.start_datetime) == booking_date,
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

    # Also process calendar availability events (from recurring schedules)
    for cal_event in calendar_availability:
        # Generate time slots within the calendar availability window
        current_time = cal_event.start_datetime
        end_time = cal_event.end_datetime

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
            # Skip the current availability event itself from conflict check
            if not conflict:
                calendar_conflict = has_calendar_conflict(
                    db,
                    specialist_id,
                    current_time,
                    slot_end,
                    exclude_event_id=cal_event.id,  # Exclude the current availability event
                )
                conflict = calendar_conflict

            if not conflict:
                # Check if this slot is already in available_slots to avoid duplicates
                slot_time = current_time.time()
                slot_exists = any(
                    slot["start_time"] == slot_time for slot in available_slots
                )

                if not slot_exists:
                    available_slots.append(
                        {
                            "start_time": slot_time,
                            "end_time": slot_end.time(),
                            "duration_minutes": service_duration,
                        }
                    )

            # Increment by the service duration
            current_time += timedelta(minutes=service_duration)

    # Sort available slots by start time and return
    available_slots.sort(key=lambda slot: slot["start_time"])
    return available_slots


@app.post("/booking/", response_model=BookingResponse)
def create_booking(booking: BookingCreate, db: Session = Depends(get_db)):
    """
    Create a new booking for a consumer with comprehensive validation.
    """
    try:
        print(f"DEBUG: Received booking request: {booking}")

        # Validate specialist exists
        specialist = (
            db.query(Specialist).filter(Specialist.id == booking.specialist_id).first()
        )
        if not specialist:
            print(f"DEBUG: Specialist {booking.specialist_id} not found")
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

        # Also check calendar events that represent availability (from recurring schedules)
        calendar_availability = (
            db.query(CalendarEvent)
            .filter(
                CalendarEvent.specialist_id == booking.specialist_id,
                CalendarEvent.event_type == "availability",
                CalendarEvent.status == "confirmed",
                CalendarEvent.is_active == True,
                func.date(CalendarEvent.start_datetime) == booking.booking_date,
            )
            .all()
        )

        # Check if the requested time falls within any availability slot
        booking_start = datetime.combine(booking.booking_date, booking.start_time)
        booking_end = booking_start + timedelta(minutes=service.duration)

        valid_slot = None

        # Check traditional availability slots
        for slot in availability_slots:
            slot_start = datetime.combine(slot.date, slot.start_time)
            slot_end = datetime.combine(slot.date, slot.end_time)

            # Check if booking fits within this availability slot
            if booking_start >= slot_start and booking_end <= slot_end:
                valid_slot = slot
                break

        # If not found in traditional slots, check calendar availability events
        if not valid_slot:
            for cal_event in calendar_availability:
                # Check if booking fits within this calendar availability
                if (
                    booking_start >= cal_event.start_datetime
                    and booking_end <= cal_event.end_datetime
                ):
                    valid_slot = cal_event  # Use calendar event as valid slot indicator
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

        # Get or create consumer using normalized matching
        matching_consumers = find_matching_consumers(
            db, email=booking.client_email, phone=booking.client_phone
        )

        if matching_consumers:
            # Use first matching consumer (they should all be the same person)
            consumer = matching_consumers[0]
        else:
            # Create new consumer
            consumer = Consumer(
                name=booking.client_name,
                email=booking.client_email,
                phone=booking.client_phone,
            )
            db.add(consumer)
            db.flush()  # Get consumer ID without committing

            # Create referral tracking for first booking
            referral = Referral(
                consumer_id=consumer.id,
                specialist_id=booking.specialist_id,
                referred_by_specialist_id=(
                    None if booking.source_workplace_id else booking.specialist_id
                ),
                referred_by_workplace_id=booking.source_workplace_id,
            )
            db.add(referral)

            # Auto-create client profile with next available rank
            next_rank = get_next_client_rank(db, booking.specialist_id)
            client_profile = ClientProfile(
                specialist_id=booking.specialist_id,
                consumer_id=consumer.id,
                bio=None,
                score=next_rank,
                notes=None,
            )
            db.add(client_profile)

        # Create the booking
        db_booking = Booking(
            specialist_id=booking.specialist_id,
            service_id=booking.service_id,
            consumer_id=consumer.id,
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

        print(f"DEBUG: Successfully created booking with ID: {db_booking.id}")
        return db_booking

    except Exception as e:
        print(f"DEBUG: Error creating booking: {str(e)}")
        print(f"DEBUG: Error type: {type(e)}")
        db.rollback()
        if isinstance(e, HTTPException):
            raise e
        else:
            raise HTTPException(
                status_code=500, detail=f"Internal server error: {str(e)}"
            )


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


# ==================== Workplace Endpoints ====================


@app.post("/workplaces/", response_model=WorkplaceResponse)
async def create_workplace(workplace: WorkplaceCreate, db: Session = Depends(get_db)):
    """
    Create a new workplace.
    """
    # Validate Yelp business if provided
    if workplace.yelp_business_id:
        try:
            is_valid = await yelp_service.validate_business(workplace.yelp_business_id)
            if not is_valid:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid Yelp business ID or business is closed",
                )
        except YelpAPIError as e:
            raise HTTPException(status_code=400, detail=f"Yelp API error: {str(e)}")

    db_workplace = Workplace(
        name=workplace.name,
        address=workplace.address,
        city=workplace.city,
        state=workplace.state,
        zip_code=workplace.zip_code,
        country=workplace.country,
        phone=workplace.phone,
        website=workplace.website,
        description=workplace.description,
        yelp_business_id=workplace.yelp_business_id,
        is_verified=workplace.is_verified,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    db.add(db_workplace)
    db.commit()
    db.refresh(db_workplace)

    # Count specialists
    specialists_count = len(db_workplace.specialists)

    # Convert to response model
    response = WorkplaceResponse(
        id=db_workplace.id,
        name=db_workplace.name,
        address=db_workplace.address,
        city=db_workplace.city,
        state=db_workplace.state,
        zip_code=db_workplace.zip_code,
        country=db_workplace.country,
        phone=db_workplace.phone,
        website=db_workplace.website,
        description=db_workplace.description,
        yelp_business_id=db_workplace.yelp_business_id,
        is_verified=db_workplace.is_verified,
        created_at=db_workplace.created_at,
        updated_at=db_workplace.updated_at,
        specialists_count=specialists_count,
    )

    return response


@app.get("/workplaces/", response_model=List[WorkplaceResponse])
def get_workplaces(
    city: Optional[str] = None,
    state: Optional[str] = None,
    is_verified: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    """
    Get all workplaces with optional filtering.
    """
    query = db.query(Workplace)

    if city:
        query = query.filter(Workplace.city.ilike(f"%{city}%"))
    if state:
        query = query.filter(Workplace.state.ilike(f"%{state}%"))
    if is_verified is not None:
        query = query.filter(Workplace.is_verified == is_verified)

    workplaces = query.all()

    # Convert to response models
    response_workplaces = []
    for workplace in workplaces:
        specialists_count = len(workplace.specialists)
        response = WorkplaceResponse(
            id=workplace.id,
            name=workplace.name,
            address=workplace.address,
            city=workplace.city,
            state=workplace.state,
            zip_code=workplace.zip_code,
            country=workplace.country,
            phone=workplace.phone,
            website=workplace.website,
            description=workplace.description,
            yelp_business_id=workplace.yelp_business_id,
            is_verified=workplace.is_verified,
            created_at=workplace.created_at,
            updated_at=workplace.updated_at,
            specialists_count=specialists_count,
        )
        response_workplaces.append(response)

    return response_workplaces


@app.get("/workplaces/{workplace_id}", response_model=WorkplaceResponse)
def get_workplace(workplace_id: int, db: Session = Depends(get_db)):
    """
    Get a specific workplace by ID.
    """
    workplace = db.query(Workplace).filter(Workplace.id == workplace_id).first()
    if not workplace:
        raise HTTPException(status_code=404, detail="Workplace not found")

    specialists_count = len(workplace.specialists)

    response = WorkplaceResponse(
        id=workplace.id,
        name=workplace.name,
        address=workplace.address,
        city=workplace.city,
        state=workplace.state,
        zip_code=workplace.zip_code,
        country=workplace.country,
        phone=workplace.phone,
        website=workplace.website,
        description=workplace.description,
        yelp_business_id=workplace.yelp_business_id,
        is_verified=workplace.is_verified,
        created_at=workplace.created_at,
        updated_at=workplace.updated_at,
        specialists_count=specialists_count,
    )

    return response


@app.put("/workplaces/{workplace_id}", response_model=WorkplaceResponse)
async def update_workplace(
    workplace_id: int, workplace_update: WorkplaceUpdate, db: Session = Depends(get_db)
):
    """
    Update a workplace.
    """
    workplace = db.query(Workplace).filter(Workplace.id == workplace_id).first()
    if not workplace:
        raise HTTPException(status_code=404, detail="Workplace not found")

    # Validate Yelp business if being updated
    if workplace_update.yelp_business_id is not None:
        try:
            is_valid = await yelp_service.validate_business(
                workplace_update.yelp_business_id
            )
            if not is_valid:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid Yelp business ID or business is closed",
                )
        except YelpAPIError as e:
            raise HTTPException(status_code=400, detail=f"Yelp API error: {str(e)}")

    # Update fields that are provided
    update_data = workplace_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(workplace, field, value)

    workplace.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(workplace)

    specialists_count = len(workplace.specialists)

    response = WorkplaceResponse(
        id=workplace.id,
        name=workplace.name,
        address=workplace.address,
        city=workplace.city,
        state=workplace.state,
        zip_code=workplace.zip_code,
        country=workplace.country,
        phone=workplace.phone,
        website=workplace.website,
        description=workplace.description,
        yelp_business_id=workplace.yelp_business_id,
        is_verified=workplace.is_verified,
        created_at=workplace.created_at,
        updated_at=workplace.updated_at,
        specialists_count=specialists_count,
    )

    return response


@app.delete("/workplaces/{workplace_id}")
def delete_workplace(workplace_id: int, db: Session = Depends(get_db)) -> dict:
    """
    Delete a workplace.
    """
    workplace = db.query(Workplace).filter(Workplace.id == workplace_id).first()
    if not workplace:
        raise HTTPException(status_code=404, detail="Workplace not found")

    # Check if workplace has associated specialists
    if workplace.specialists:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete workplace with associated specialists. Remove associations first.",
        )

    db.delete(workplace)
    db.commit()

    return {"message": "Workplace deleted successfully"}


# ==================== Specialist-Workplace Association Endpoints ====================


@app.post("/specialists/{specialist_id}/workplaces/{workplace_id}")
def associate_specialist_workplace(
    specialist_id: int,
    workplace_id: int,
    association: SpecialistWorkplaceAssociation,
    db: Session = Depends(get_db),
) -> dict:
    """
    Associate a specialist with a workplace.
    """
    # Check if specialist exists
    specialist = db.query(Specialist).filter(Specialist.id == specialist_id).first()
    if not specialist:
        raise HTTPException(status_code=404, detail="Specialist not found")

    # Check if workplace exists
    workplace = db.query(Workplace).filter(Workplace.id == workplace_id).first()
    if not workplace:
        raise HTTPException(status_code=404, detail="Workplace not found")

    # Check if association already exists and is active
    from sqlalchemy import and_

    existing_association = db.execute(
        specialist_workplace_association.select().where(
            and_(
                specialist_workplace_association.c.specialist_id == specialist_id,
                specialist_workplace_association.c.workplace_id == workplace_id,
                specialist_workplace_association.c.is_active == True,
            )
        )
    ).first()

    if existing_association:
        # Return success if already associated (idempotent operation)
        return {
            "message": "Specialist is already associated with this workplace",
            "specialist_id": specialist_id,
            "workplace_id": workplace_id,
            "role": existing_association.role,
            "already_exists": True,
        }

    # Create new association
    association_data = {
        "specialist_id": specialist_id,
        "workplace_id": workplace_id,
        "role": association.role,
        "start_date": association.start_date,
        "end_date": association.end_date,
        "is_active": association.is_active,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }

    db.execute(specialist_workplace_association.insert().values(**association_data))
    db.commit()

    return {
        "message": "Specialist successfully associated with workplace",
        "specialist_id": specialist_id,
        "workplace_id": workplace_id,
        "role": association.role,
        "already_exists": False,
    }


@app.delete("/specialists/{specialist_id}/workplaces/{workplace_id}")
def disassociate_specialist_workplace(
    specialist_id: int, workplace_id: int, db: Session = Depends(get_db)
) -> dict:
    """
    Remove association between a specialist and workplace.
    """
    from sqlalchemy import and_

    # Find the association
    existing_association = db.execute(
        specialist_workplace_association.select().where(
            and_(
                specialist_workplace_association.c.specialist_id == specialist_id,
                specialist_workplace_association.c.workplace_id == workplace_id,
                specialist_workplace_association.c.is_active == True,
            )
        )
    ).first()

    if not existing_association:
        raise HTTPException(
            status_code=404,
            detail="Active association not found between specialist and workplace",
        )

    # Update association to inactive instead of deleting (for audit trail)
    db.execute(
        specialist_workplace_association.update()
        .where(
            and_(
                specialist_workplace_association.c.specialist_id == specialist_id,
                specialist_workplace_association.c.workplace_id == workplace_id,
            )
        )
        .values(is_active=False, end_date=date.today(), updated_at=datetime.utcnow())
    )
    db.commit()

    return {
        "message": "Specialist successfully disassociated from workplace",
        "specialist_id": specialist_id,
        "workplace_id": workplace_id,
    }


@app.get(
    "/specialists/{specialist_id}/workplaces",
    response_model=List[SpecialistWorkplaceResponse],
)
def get_specialist_workplaces(specialist_id: int, db: Session = Depends(get_db)):
    """
    Get all workplaces associated with a specialist with association details.
    """
    specialist = db.query(Specialist).filter(Specialist.id == specialist_id).first()
    if not specialist:
        raise HTTPException(status_code=404, detail="Specialist not found")

    # Get active workplace associations
    from sqlalchemy import and_

    associations = db.execute(
        specialist_workplace_association.select().where(
            and_(
                specialist_workplace_association.c.specialist_id == specialist_id,
                specialist_workplace_association.c.is_active == True,
            )
        )
    ).fetchall()

    # Build response with workplace and association data
    response_list = []
    for assoc in associations:
        workplace = (
            db.query(Workplace).filter(Workplace.id == assoc.workplace_id).first()
        )
        if workplace:
            specialists_count = len(workplace.specialists)
            workplace_response = WorkplaceResponse(
                id=workplace.id,
                name=workplace.name,
                address=workplace.address,
                city=workplace.city,
                state=workplace.state,
                zip_code=workplace.zip_code,
                country=workplace.country,
                phone=workplace.phone,
                website=workplace.website,
                description=workplace.description,
                yelp_business_id=workplace.yelp_business_id,
                is_verified=workplace.is_verified,
                created_at=workplace.created_at,
                updated_at=workplace.updated_at,
                specialists_count=specialists_count,
            )

            response = SpecialistWorkplaceResponse(
                workplace=workplace_response,
                role=assoc.role,
                start_date=assoc.start_date,
                end_date=assoc.end_date,
                is_active=assoc.is_active,
            )
            response_list.append(response)

    return response_list


# ==================== Consumer Business Browsing Endpoints ====================


@app.get("/consumer/workplaces", response_model=List[WorkplaceResponse])
def get_all_workplaces(
    city: Optional[str] = None,
    state: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """
    Get all workplaces/businesses for consumer browsing.
    Optionally filter by location.
    """
    query = db.query(Workplace)

    if city:
        query = query.filter(Workplace.city.ilike(f"%{city}%"))
    if state:
        query = query.filter(Workplace.state.ilike(f"%{state}%"))

    workplaces = query.limit(limit).all()

    # Add specialist count to each workplace
    response = []
    for workplace in workplaces:
        specialists_count = (
            db.query(specialist_workplace_association)
            .filter(
                specialist_workplace_association.c.workplace_id == workplace.id,
                specialist_workplace_association.c.is_active == True,
            )
            .count()
        )

        workplace_dict = {
            "id": workplace.id,
            "name": workplace.name,
            "address": workplace.address,
            "city": workplace.city,
            "state": workplace.state,
            "zip_code": workplace.zip_code,
            "country": workplace.country,
            "phone": workplace.phone,
            "website": workplace.website,
            "description": workplace.description,
            "yelp_business_id": workplace.yelp_business_id,
            "is_verified": workplace.is_verified,
            "created_at": workplace.created_at,
            "updated_at": workplace.updated_at,
            "specialists_count": specialists_count,
        }
        response.append(WorkplaceResponse(**workplace_dict))

    return response


@app.get("/consumer/workplaces/{workplace_id}", response_model=WorkplaceResponse)
def get_workplace_details(workplace_id: int, db: Session = Depends(get_db)):
    """
    Get detailed information about a specific workplace.
    """
    workplace = db.query(Workplace).filter(Workplace.id == workplace_id).first()

    if not workplace:
        raise HTTPException(status_code=404, detail="Workplace not found")

    # Count specialists
    specialists_count = (
        db.query(specialist_workplace_association)
        .filter(
            specialist_workplace_association.c.workplace_id == workplace.id,
            specialist_workplace_association.c.is_active == True,
        )
        .count()
    )

    workplace_dict = {
        "id": workplace.id,
        "name": workplace.name,
        "address": workplace.address,
        "city": workplace.city,
        "state": workplace.state,
        "zip_code": workplace.zip_code,
        "country": workplace.country,
        "phone": workplace.phone,
        "website": workplace.website,
        "description": workplace.description,
        "yelp_business_id": workplace.yelp_business_id,
        "is_verified": workplace.is_verified,
        "created_at": workplace.created_at,
        "updated_at": workplace.updated_at,
        "specialists_count": specialists_count,
    }

    return WorkplaceResponse(**workplace_dict)


@app.get(
    "/consumer/workplaces/{workplace_id}/specialists",
    response_model=List[SpecialistCatalogResponse],
)
def get_workplace_specialists(workplace_id: int, db: Session = Depends(get_db)):
    """
    Get all specialists working at a specific workplace.
    This is for the business-first booking flow.
    """
    # Verify workplace exists
    workplace = db.query(Workplace).filter(Workplace.id == workplace_id).first()
    if not workplace:
        raise HTTPException(status_code=404, detail="Workplace not found")

    # Get active specialists at this workplace
    associations = (
        db.query(specialist_workplace_association)
        .filter(
            specialist_workplace_association.c.workplace_id == workplace_id,
            specialist_workplace_association.c.is_active == True,
        )
        .all()
    )

    specialist_ids = [assoc.specialist_id for assoc in associations]

    if not specialist_ids:
        return []

    # Get specialist details
    specialists = db.query(Specialist).filter(Specialist.id.in_(specialist_ids)).all()

    response = []
    for specialist in specialists:
        # Get services
        services = (
            db.query(ServiceDB).filter(ServiceDB.specialist_id == specialist.id).all()
        )

        services_data = [
            {
                "id": svc.id,
                "name": svc.name,
                "price": svc.price,
                "duration": svc.duration,
                "specialist_id": svc.specialist_id,
            }
            for svc in services
        ]

        specialist_data = {
            "id": specialist.id,
            "name": specialist.name,
            "email": specialist.email,
            "bio": specialist.bio,
            "phone": specialist.phone,
            "services": services_data,
        }
        response.append(SpecialistCatalogResponse(**specialist_data))

    return response


# ==================== Search Endpoints ====================


@app.get("/search")
def unified_search(
    query: str,
    search_type: str = "professional",  # "professional" or "business"
    location: Optional[str] = None,
    city: Optional[str] = None,
    state: Optional[str] = None,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """
    Unified search endpoint for professionals and businesses.

    Search by:
    - query: Service name, professional name, or business name
    - search_type: "professional" or "business"
    - location: Free-text location (city, state)
    - city/state: Specific filters
    """

    if search_type == "professional":
        # Search for professionals by name or service
        specialists_query = db.query(Specialist)

        # Search in specialist name or bio
        if query:
            specialists_query = specialists_query.filter(
                (Specialist.name.ilike(f"%{query}%"))
                | (Specialist.bio.ilike(f"%{query}%"))
            )

        # Also search in services
        service_specialists = []
        if query:
            services = (
                db.query(ServiceDB).filter(ServiceDB.name.ilike(f"%{query}%")).all()
            )
            service_specialists = [svc.specialist_id for svc in services]

        if service_specialists:
            specialists_query = specialists_query.filter(
                Specialist.id.in_(service_specialists)
            )

        specialists = specialists_query.limit(limit).all()

        # Build response with workplace info
        results = []
        for specialist in specialists:
            # Get services
            services = (
                db.query(ServiceDB)
                .filter(ServiceDB.specialist_id == specialist.id)
                .all()
            )

            # Get workplaces
            workplace_assocs = (
                db.query(specialist_workplace_association)
                .filter(
                    specialist_workplace_association.c.specialist_id == specialist.id,
                    specialist_workplace_association.c.is_active == True,
                )
                .all()
            )

            workplaces = []
            for assoc in workplace_assocs:
                workplace = (
                    db.query(Workplace)
                    .filter(Workplace.id == assoc.workplace_id)
                    .first()
                )
                if workplace:
                    # Filter by location if specified
                    if city and workplace.city.lower() != city.lower():
                        continue
                    if state and workplace.state.lower() != state.lower():
                        continue
                    if location:
                        loc_lower = location.lower()
                        if not (
                            loc_lower in workplace.city.lower()
                            or loc_lower in workplace.state.lower()
                            or loc_lower in workplace.address.lower()
                        ):
                            continue

                    workplaces.append(
                        {
                            "id": workplace.id,
                            "name": workplace.name,
                            "address": workplace.address,
                            "city": workplace.city,
                            "state": workplace.state,
                            "is_verified": workplace.is_verified,
                        }
                    )

            # Skip if location filter excludes all workplaces
            if (city or state or location) and not workplaces:
                continue

            results.append(
                {
                    "type": "professional",
                    "id": specialist.id,
                    "name": specialist.name,
                    "bio": specialist.bio,
                    "phone": specialist.phone,
                    "services": [
                        {
                            "id": svc.id,
                            "name": svc.name,
                            "price": svc.price,
                            "duration": svc.duration,
                        }
                        for svc in services
                    ],
                    "workplaces": workplaces,
                }
            )

        return {"results": results, "count": len(results)}

    elif search_type == "business":
        # Search for businesses
        query_obj = db.query(Workplace)

        # Search in business name or description
        if query:
            query_obj = query_obj.filter(
                (Workplace.name.ilike(f"%{query}%"))
                | (Workplace.description.ilike(f"%{query}%"))
            )

        # Location filters
        if city:
            query_obj = query_obj.filter(Workplace.city.ilike(f"%{city}%"))
        if state:
            query_obj = query_obj.filter(Workplace.state.ilike(f"%{state}%"))
        if location:
            loc_lower = f"%{location}%"
            query_obj = query_obj.filter(
                (Workplace.city.ilike(loc_lower))
                | (Workplace.state.ilike(loc_lower))
                | (Workplace.address.ilike(loc_lower))
            )

        workplaces = query_obj.limit(limit).all()

        # Build response with specialist info
        results = []
        for workplace in workplaces:
            # Get specialists at this workplace
            specialist_assocs = (
                db.query(specialist_workplace_association)
                .filter(
                    specialist_workplace_association.c.workplace_id == workplace.id,
                    specialist_workplace_association.c.is_active == True,
                )
                .all()
            )

            specialist_ids = [assoc.specialist_id for assoc in specialist_assocs]
            specialists = (
                db.query(Specialist).filter(Specialist.id.in_(specialist_ids)).all()
                if specialist_ids
                else []
            )

            # Get all services offered at this workplace
            all_services = []
            for spec in specialists:
                services = (
                    db.query(ServiceDB).filter(ServiceDB.specialist_id == spec.id).all()
                )
                all_services.extend(
                    [
                        {
                            "id": svc.id,
                            "name": svc.name,
                            "price": svc.price,
                            "duration": svc.duration,
                            "specialist_name": spec.name,
                        }
                        for svc in services
                    ]
                )

            results.append(
                {
                    "type": "business",
                    "id": workplace.id,
                    "name": workplace.name,
                    "address": workplace.address,
                    "city": workplace.city,
                    "state": workplace.state,
                    "zip_code": workplace.zip_code,
                    "phone": workplace.phone,
                    "website": workplace.website,
                    "description": workplace.description,
                    "is_verified": workplace.is_verified,
                    "specialists_count": len(specialists),
                    "services": all_services,
                }
            )

        return {"results": results, "count": len(results)}

    else:
        raise HTTPException(
            status_code=400,
            detail="Invalid search_type. Must be 'professional' or 'business'",
        )


# ==================== Yelp Integration Endpoints ====================


@app.get("/yelp/search", response_model=List[YelpBusinessResponse])
async def search_yelp_businesses(
    term: str,
    location: str,
    limit: int = 10,
    radius: Optional[int] = None,
    categories: Optional[str] = None,
) -> List[YelpBusinessResponse]:
    """
    Search for businesses using Yelp API.
    """
    search_params = YelpBusinessSearch(
        term=term,
        location=location,
        limit=min(limit, 50),  # Cap at 50 results
        radius=radius,
        categories=categories,
    )

    try:
        businesses = await yelp_service.search_businesses(search_params)
        return businesses
    except YelpAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/yelp/business/{business_id}", response_model=YelpBusinessResponse)
async def get_yelp_business(business_id: str) -> YelpBusinessResponse:
    """
    Get detailed information about a specific Yelp business.
    """
    try:
        business = await yelp_service.get_business_details(business_id)
        if not business:
            raise HTTPException(status_code=404, detail="Business not found")
        return business
    except YelpAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/workplaces/from-yelp/{business_id}", response_model=WorkplaceResponse)
async def create_workplace_from_yelp(business_id: str, db: Session = Depends(get_db)):
    """
    Create a workplace from Yelp business data.
    If workplace already exists, return the existing workplace.
    """
    try:
        # Check if workplace with this Yelp ID already exists
        existing_workplace = (
            db.query(Workplace)
            .filter(Workplace.yelp_business_id == business_id)
            .first()
        )

        if existing_workplace:
            # Return existing workplace instead of error
            specialists_count = len(existing_workplace.specialists)
            return WorkplaceResponse(
                id=existing_workplace.id,
                name=existing_workplace.name,
                address=existing_workplace.address,
                city=existing_workplace.city,
                state=existing_workplace.state,
                zip_code=existing_workplace.zip_code,
                country=existing_workplace.country,
                phone=existing_workplace.phone,
                website=existing_workplace.website,
                description=existing_workplace.description,
                yelp_business_id=existing_workplace.yelp_business_id,
                is_verified=existing_workplace.is_verified,
                specialists_count=specialists_count,
                created_at=existing_workplace.created_at,
                updated_at=existing_workplace.updated_at,
            )

        # Fetch business details from Yelp
        business = await yelp_service.get_business_details(business_id)
        if not business:
            raise HTTPException(status_code=404, detail="Yelp business not found")

        # Create workplace from Yelp data
        db_workplace = Workplace(
            name=business.name,
            address=business.address,
            city=business.city,
            state=business.state,
            zip_code=business.zip_code,
            country=business.country,
            phone=business.phone,
            website=None,  # Yelp doesn't provide website in basic search
            description=f"Business verified through Yelp. Rating: {business.rating}/5 ({business.review_count} reviews)",
            yelp_business_id=business_id,
            is_verified=True,  # Verified through Yelp
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        db.add(db_workplace)
        db.commit()
        db.refresh(db_workplace)

        specialists_count = len(db_workplace.specialists)

        response = WorkplaceResponse(
            id=db_workplace.id,
            name=db_workplace.name,
            address=db_workplace.address,
            city=db_workplace.city,
            state=db_workplace.state,
            zip_code=db_workplace.zip_code,
            country=db_workplace.country,
            phone=db_workplace.phone,
            website=db_workplace.website,
            description=db_workplace.description,
            yelp_business_id=db_workplace.yelp_business_id,
            is_verified=db_workplace.is_verified,
            created_at=db_workplace.created_at,
            updated_at=db_workplace.updated_at,
            specialists_count=specialists_count,
        )

        return response

    except YelpAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== Client Management Endpoints ====================


def normalize_email(email):
    """Normalize email for comparison (lowercase, strip whitespace)"""
    if not email:
        return None
    return email.strip().lower()


def normalize_phone(phone):
    """Normalize phone for comparison (remove all non-digits)"""
    if not phone:
        return None
    # Remove all non-digit characters
    return "".join(c for c in phone if c.isdigit())


def find_matching_consumers(
    db: Session, email: str = None, phone: str = None
) -> List[Consumer]:
    """
    Find all consumers that match the given email OR phone.
    Uses normalized, case-insensitive matching.
    This handles client consolidation - same person using different contact info.
    """
    if not email and not phone:
        return []

    norm_email = normalize_email(email)
    norm_phone = normalize_phone(phone)

    # Get all consumers and check manually (for phone normalization)
    all_consumers = db.query(Consumer).all()
    matching_consumers = []

    for consumer in all_consumers:
        matched = False

        # Check email match (case-insensitive)
        if norm_email and normalize_email(consumer.email) == norm_email:
            matched = True

        # Check phone match (normalized - digits only)
        if norm_phone and normalize_phone(consumer.phone) == norm_phone:
            matched = True

        if matched:
            matching_consumers.append(consumer)

    return matching_consumers

    return matching_consumers


def consolidate_consumer_bookings(
    db: Session, consumers: List[Consumer]
) -> List[Booking]:
    """
    Get all bookings from multiple consumer records.
    Used when the same person has multiple consumer records.
    """
    if not consumers:
        return []

    consumer_ids = [c.id for c in consumers]
    bookings = db.query(Booking).filter(Booking.consumer_id.in_(consumer_ids)).all()

    # Also get legacy bookings without consumer_id but matching email/phone
    legacy_bookings = []
    for consumer in consumers:
        if consumer.email:
            legacy_by_email = (
                db.query(Booking)
                .filter(
                    Booking.consumer_id.is_(None),
                    Booking.client_email == consumer.email,
                )
                .all()
            )
            legacy_bookings.extend(legacy_by_email)

        if consumer.phone:
            legacy_by_phone = (
                db.query(Booking)
                .filter(
                    Booking.consumer_id.is_(None),
                    Booking.client_phone == consumer.phone,
                )
                .all()
            )
            legacy_bookings.extend(legacy_by_phone)

    # Combine and deduplicate
    all_bookings = list(set(bookings + legacy_bookings))
    return all_bookings


def get_next_client_rank(db: Session, specialist_id: int) -> int:
    """
    Get the next available rank for a new client.
    Returns the highest existing rank + 1, or 1 if no clients exist.
    """
    max_rank = (
        db.query(func.max(ClientProfile.score))
        .filter(ClientProfile.specialist_id == specialist_id)
        .scalar()
    )
    return (max_rank or 0) + 1


@app.get("/professional/clients")
async def get_professional_clients(specialist_id: int, db: Session = Depends(get_db)):
    """
    Get all unique clients for this professional.
    Includes both clients with bookings and clients added via CSV (with profiles but no bookings).
    Consolidates clients by email OR phone matching.
    Returns ClientSummary list with booking stats.
    """
    # Get all bookings for this specialist
    all_bookings = (
        db.query(Booking).filter(Booking.specialist_id == specialist_id).all()
    )

    # Build unique client list by consolidating matches
    seen_consumers = set()
    client_summaries = []
    processed_contacts = set()  # Track processed email/phone combinations

    for booking in all_bookings:
        # Determine contact info
        email = booking.consumer.email if booking.consumer else booking.client_email
        phone = booking.consumer.phone if booking.consumer else booking.client_phone

        contact_key = f"{email or 'none'}:{phone or 'none'}"
        if contact_key in processed_contacts:
            continue
        processed_contacts.add(contact_key)

        # Find all matching consumers
        matching_consumers = find_matching_consumers(db, email, phone)

        if not matching_consumers:
            # Legacy booking without consumer record
            matching_consumers = []

        # Get primary consumer (first match or create summary from booking)
        if matching_consumers:
            primary_consumer = matching_consumers[0]
            consumer_id = primary_consumer.id

            # Skip if we've already processed this consumer
            if consumer_id in seen_consumers:
                continue
            seen_consumers.add(consumer_id)
        else:
            # Use booking data for legacy entries
            consumer_id = None

        # Get ALL bookings for this client (consolidated)
        if matching_consumers:
            client_bookings = consolidate_consumer_bookings(db, matching_consumers)
            # Filter to only this specialist's bookings
            client_bookings = [
                b for b in client_bookings if b.specialist_id == specialist_id
            ]
        else:
            # Legacy booking only
            client_bookings = [booking]

        # Calculate stats
        total_bookings = len(client_bookings)
        sorted_bookings = sorted(client_bookings, key=lambda b: b.date)
        last_booking = sorted_bookings[-1] if sorted_bookings else None

        # Separate past and future
        today = date.today()
        future_bookings = [b for b in sorted_bookings if b.date >= today]
        next_booking = future_bookings[0] if future_bookings else None

        # Get profile if exists
        profile = None
        has_profile = False
        score = None
        is_favorite = False
        if consumer_id:
            profile = (
                db.query(ClientProfile)
                .filter(
                    ClientProfile.specialist_id == specialist_id,
                    ClientProfile.consumer_id == consumer_id,
                )
                .first()
            )
            if profile:
                has_profile = True
                score = profile.score
                is_favorite = profile.is_favorite or False

        # Build summary
        client_summary = {
            "consumer_id": consumer_id,
            "name": (
                primary_consumer.name if matching_consumers else booking.client_name
            ),
            "email": (
                primary_consumer.email if matching_consumers else booking.client_email
            ),
            "phone": (
                primary_consumer.phone if matching_consumers else booking.client_phone
            ),
            "total_bookings": total_bookings,
            "last_booking_date": (
                datetime.combine(last_booking.date, last_booking.start_time)
                if last_booking
                else None
            ),
            "next_booking_date": (
                datetime.combine(next_booking.date, next_booking.start_time)
                if next_booking
                else None
            ),
            "score": score,
            "has_profile": has_profile,
            "is_favorite": is_favorite,
        }

        client_summaries.append(client_summary)

    # Also include clients who have profiles but no bookings (e.g., from CSV upload)
    profiles_without_bookings = (
        db.query(ClientProfile)
        .filter(ClientProfile.specialist_id == specialist_id)
        .all()
    )

    for profile in profiles_without_bookings:
        # Skip if we already processed this consumer
        if profile.consumer_id in seen_consumers:
            continue

        consumer = db.query(Consumer).filter(Consumer.id == profile.consumer_id).first()
        if not consumer:
            continue  # Skip if consumer was deleted

        seen_consumers.add(consumer.id)

        # Build summary for client with no bookings
        client_summary = {
            "consumer_id": consumer.id,
            "name": consumer.name,
            "email": consumer.email,
            "phone": consumer.phone,
            "total_bookings": 0,
            "last_booking_date": None,
            "next_booking_date": None,
            "score": profile.score,
            "has_profile": True,
            "is_favorite": profile.is_favorite or False,
        }

        client_summaries.append(client_summary)

    # Sort by rank (score) if available, then by last booking date
    def sort_key(client):
        # Primary: Sort by rank (lower is better)
        rank = client["score"] if client["score"] is not None else 999999

        # Secondary: Sort by last booking date (more recent first)
        last_booking = client["last_booking_date"]
        if last_booking:
            booking_sort = -last_booking.timestamp()
        else:
            booking_sort = 0  # No bookings go last within same rank

        return (rank, booking_sort)

    client_summaries.sort(key=sort_key)

    return client_summaries


@app.get("/professional/clients/{consumer_id}")
async def get_client_detail(
    specialist_id: int, consumer_id: int, db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific client.
    Includes consolidated booking history, profile, and stats.
    """
    # Get consumer
    consumer = db.query(Consumer).filter(Consumer.id == consumer_id).first()
    if not consumer:
        raise HTTPException(status_code=404, detail="Client not found")

    # Find all matching consumers (consolidation)
    matching_consumers = find_matching_consumers(db, consumer.email, consumer.phone)

    # Get all bookings (consolidated)
    all_bookings = consolidate_consumer_bookings(db, matching_consumers)

    # Filter to this specialist's bookings only
    specialist_bookings = [b for b in all_bookings if b.specialist_id == specialist_id]

    # Separate past and future
    today = date.today()
    past_bookings = []
    future_bookings = []

    for booking in specialist_bookings:
        booking_dict = {
            "id": booking.id,
            "date": booking.date.isoformat(),
            "start_time": booking.start_time.isoformat(),
            "end_time": booking.end_time.isoformat(),
            "service_name": booking.service.name if booking.service else "Unknown",
            "service_price": booking.service.price if booking.service else 0,
            "status": booking.status,
            "notes": booking.notes,
        }

        if booking.date < today:
            past_bookings.append(booking_dict)
        else:
            future_bookings.append(booking_dict)

    # Sort bookings
    past_bookings.sort(key=lambda x: x["date"], reverse=True)
    future_bookings.sort(key=lambda x: x["date"])

    # Calculate total revenue
    total_revenue = sum(
        b.service.price
        for b in specialist_bookings
        if b.service and b.status == "completed"
    )

    # Get first booking date
    first_booking_date = (
        min(b.date for b in specialist_bookings) if specialist_bookings else None
    )

    # Get client profile
    profile = (
        db.query(ClientProfile)
        .filter(
            ClientProfile.specialist_id == specialist_id,
            ClientProfile.consumer_id == consumer_id,
        )
        .first()
    )

    # Parse notes JSON if exists
    profile_data = None
    if profile:
        import json

        notes = []
        if profile.notes:
            try:
                notes = json.loads(profile.notes)
            except:
                notes = []

        profile_data = {
            "id": profile.id,
            "specialist_id": profile.specialist_id,
            "consumer_id": profile.consumer_id,
            "bio": profile.bio,
            "score": profile.score,
            "notes": notes,
            "created_at": profile.created_at.isoformat(),
            "updated_at": profile.updated_at.isoformat(),
        }

    # Build response
    response = {
        "consumer": {
            "id": consumer.id,
            "name": consumer.name,
            "email": consumer.email,
            "phone": consumer.phone,
            "created_at": consumer.created_at.isoformat(),
            "updated_at": consumer.updated_at.isoformat(),
        },
        "profile": profile_data,
        "bookings_past": past_bookings,
        "bookings_future": future_bookings,
        "total_revenue": total_revenue,
        "first_booking_date": (
            first_booking_date.isoformat() if first_booking_date else None
        ),
    }

    return response


@app.put("/professional/clients/{consumer_id}/profile")
async def update_client_profile(
    specialist_id: int,
    consumer_id: int,
    bio: Optional[str] = None,
    score: Optional[int] = None,
    notes: Optional[str] = None,  # JSON string of notes array
    is_favorite: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    """
    Update or create a client profile with professional's notes.
    Score is now used as ranking (1 = top client, higher numbers = lower priority).
    """
    # Validate score (now ranking - allow any positive integer)
    if score is not None and score < 1:
        raise HTTPException(status_code=400, detail="Ranking must be at least 1")

    # Verify consumer exists
    consumer = db.query(Consumer).filter(Consumer.id == consumer_id).first()
    if not consumer:
        raise HTTPException(status_code=404, detail="Client not found")

    # Get or create profile
    profile = (
        db.query(ClientProfile)
        .filter(
            ClientProfile.specialist_id == specialist_id,
            ClientProfile.consumer_id == consumer_id,
        )
        .first()
    )

    if not profile:
        # Create new profile with auto-ranking if score not provided
        if score is None:
            score = get_next_client_rank(db, specialist_id)

        profile = ClientProfile(
            specialist_id=specialist_id,
            consumer_id=consumer_id,
            bio=bio,
            score=score,
            notes=notes,
            is_favorite=is_favorite if is_favorite is not None else False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(profile)
    else:
        # Update existing
        if bio is not None:
            profile.bio = bio
        if score is not None:
            profile.score = score
        if notes is not None:
            profile.notes = notes
        if is_favorite is not None:
            profile.is_favorite = is_favorite
        profile.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(profile)

    # Parse notes for response
    import json

    notes_list = []
    if profile.notes:
        try:
            notes_list = json.loads(profile.notes)
        except:
            notes_list = []

    return {
        "id": profile.id,
        "specialist_id": profile.specialist_id,
        "consumer_id": profile.consumer_id,
        "bio": profile.bio,
        "score": profile.score,
        "notes": notes_list,
        "created_at": profile.created_at.isoformat(),
        "updated_at": profile.updated_at.isoformat(),
    }


@app.delete("/professional/clients/{consumer_id}")
async def delete_client(
    consumer_id: int,
    specialist_id: int = Query(..., description="Specialist ID"),
    db: Session = Depends(get_db),
):
    """
    Delete a client and all associated records for a specific specialist.
    This removes:
    - Client profile (bio, score, notes)
    - All booking records with this specialist
    - Consumer record if no other bookings exist
    """
    # Verify consumer exists
    consumer = db.query(Consumer).filter(Consumer.id == consumer_id).first()
    if not consumer:
        raise HTTPException(status_code=404, detail="Client not found")

    # Delete client profile for this specialist
    db.query(ClientProfile).filter(
        ClientProfile.specialist_id == specialist_id,
        ClientProfile.consumer_id == consumer_id,
    ).delete()

    # Delete all bookings with this specialist
    db.query(Booking).filter(
        Booking.specialist_id == specialist_id, Booking.consumer_id == consumer_id
    ).delete()

    # Check if consumer has any other bookings with other specialists
    remaining_bookings = (
        db.query(Booking).filter(Booking.consumer_id == consumer_id).count()
    )

    # If no other bookings exist, delete the consumer record
    if remaining_bookings == 0:
        db.delete(consumer)

    db.commit()

    return {
        "message": "Client deleted successfully",
        "consumer_id": consumer_id,
        "deleted_consumer_record": remaining_bookings == 0,
    }


@app.post("/professional/clients/upload-csv")
async def upload_clients_csv(
    specialist_id: int = Query(..., description="Specialist ID"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Upload a CSV file to bulk import clients.
    Expected CSV format: name,email,phone
    - Header row is optional (will be auto-detected)
    - Name is required
    - Email OR Phone must be provided (at least one)
    - Duplicates (by email or phone) will be skipped
    - Creates Consumer records and ClientProfile records
    """
    # Validate file type
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a CSV")

    # Verify specialist exists
    specialist = db.query(Specialist).filter(Specialist.id == specialist_id).first()
    if not specialist:
        raise HTTPException(status_code=404, detail="Specialist not found")

    try:
        # Read file content
        content = await file.read()
        decoded_content = content.decode("utf-8")
        csv_reader = csv.reader(io.StringIO(decoded_content))

        # Read all rows
        rows = list(csv_reader)
        if not rows:
            raise HTTPException(status_code=400, detail="CSV file is empty")

        # Detect if first row is header
        first_row = rows[0]
        has_header = False
        if len(first_row) >= 2:
            # Check if first row looks like headers (contains common header words)
            header_keywords = ["name", "email", "phone", "mail", "contact"]
            if any(
                keyword in str(cell).lower()
                for cell in first_row
                for keyword in header_keywords
            ):
                has_header = True
                rows = rows[1:]  # Skip header row

        # Get starting rank for CSV upload (next available rank)
        starting_rank = get_next_client_rank(db, specialist_id)
        current_rank = starting_rank

        # Process rows
        created_count = 0
        skipped_count = 0
        errors = []

        for idx, row in enumerate(rows, start=2 if has_header else 1):
            if not row or len(row) < 1:
                continue  # Skip empty rows

            # Parse row (handle different column counts)
            name = row[0].strip() if len(row) > 0 and row[0].strip() else None
            email = row[1].strip() if len(row) > 1 and row[1].strip() else None
            phone = row[2].strip() if len(row) > 2 and row[2].strip() else None

            # Validate: Name is required
            if not name:
                errors.append(f"Row {idx}: Missing name")
                skipped_count += 1
                continue

            # Validate: Email OR Phone must be provided
            if not email and not phone:
                errors.append(f"Row {idx}: Must provide email OR phone")
                skipped_count += 1
                continue

            # Validate email format if provided
            if email and ("@" not in email or "." not in email):
                errors.append(f"Row {idx}: Invalid email format '{email}'")
                skipped_count += 1
                continue

            # Check if consumer already exists (by email or phone)
            existing_consumer = None
            if email:
                existing_consumer = (
                    db.query(Consumer).filter(Consumer.email == email).first()
                )
            if not existing_consumer and phone:
                existing_consumer = (
                    db.query(Consumer).filter(Consumer.phone == phone).first()
                )

            if existing_consumer:
                consumer = existing_consumer
                # Check if profile already exists for this specialist
                existing_profile = (
                    db.query(ClientProfile)
                    .filter(
                        ClientProfile.specialist_id == specialist_id,
                        ClientProfile.consumer_id == consumer.id,
                    )
                    .first()
                )
                if existing_profile:
                    skipped_count += 1
                    continue  # Already have this client
            else:
                # Create new consumer (name is required at this point)
                consumer = Consumer(name=name, email=email, phone=phone)
                db.add(consumer)
                db.flush()  # Get the consumer.id

            # Create client profile for this specialist with auto-rank
            profile = ClientProfile(
                specialist_id=specialist_id,
                consumer_id=consumer.id,
                bio=None,
                score=current_rank,  # Assign rank based on CSV row order
                notes=None,
            )
            db.add(profile)
            created_count += 1
            current_rank += 1  # Increment rank for next client

        db.commit()

        return {
            "message": f"CSV processed successfully",
            "created": created_count,
            "skipped": skipped_count,
            "errors": errors[:10],  # Return first 10 errors only
            "total_rows": len(rows),
            "starting_rank": starting_rank,
            "ending_rank": current_rank - 1,
        }

    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400, detail="File encoding error. Please use UTF-8 encoding"
        )
    except csv.Error as e:
        raise HTTPException(status_code=400, detail=f"CSV parsing error: {str(e)}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error processing CSV: {str(e)}")
