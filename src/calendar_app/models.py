"""
Pydantic models for API request/response validation and serialization.

This module contains all the data models used throughout the calendar application,
organized by functional areas for better maintainability.
"""

from __future__ import annotations
from typing import Union, List, Optional
from datetime import date, time, datetime
from pydantic import BaseModel, EmailStr, Field


# ==================== Core Service Models ====================


class Service(BaseModel):
    name: str
    price: float
    duration: int


class ServiceResponse(Service):
    id: int
    specialist_id: int

    class Config:
        from_attributes = True


# ==================== Workplace Models ====================


class WorkplaceCreate(BaseModel):
    name: str
    address: str
    city: str
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: str = "US"
    phone: Optional[str] = None
    website: Optional[str] = None
    description: Optional[str] = None
    yelp_business_id: Optional[str] = None
    is_verified: bool = False


class WorkplaceResponse(WorkplaceCreate):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    specialists_count: int = 0

    class Config:
        from_attributes = True


class WorkplaceUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    description: Optional[str] = None
    is_verified: Optional[bool] = None


class YelpBusinessSearch(BaseModel):
    term: str
    location: str
    limit: int = 10
    radius: Optional[int] = None  # in meters
    categories: Optional[str] = None


class YelpBusinessResponse(BaseModel):
    id: str
    name: str
    url: str
    phone: Optional[str] = None
    display_phone: Optional[str] = None
    address: str
    city: str
    state: str
    zip_code: str
    country: str
    rating: Optional[float] = None
    review_count: Optional[int] = None
    categories: List[str] = []
    image_url: Optional[str] = None
    is_closed: bool = False
    distance: Optional[float] = None


class SpecialistWorkplaceAssociation(BaseModel):
    role: Optional[str] = None  # e.g., "owner", "employee", "contractor"
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_active: bool = True


class SpecialistWorkplaceResponse(BaseModel):
    """Response model that includes both workplace and association data"""

    workplace: WorkplaceResponse
    role: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_active: bool = True

    class Config:
        from_attributes = True


# ==================== Specialist Models ====================


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


class SpecialistCatalogResponse(BaseModel):
    id: int
    name: str
    bio: Optional[str] = None
    services: List[ServiceResponse] = []
    available_dates: List[date] = []

    class Config:
        from_attributes = True


# ==================== Availability Models ====================


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


class TimeSlotResponse(BaseModel):
    id: int
    start_time: time
    end_time: time
    duration_minutes: int
    date: date

    class Config:
        from_attributes = True


class TimeRange(BaseModel):
    """Flexible time range supporting both date-times and all-day events"""

    start_time: Optional[time] = None
    end_time: Optional[time] = None
    start_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None
    is_all_day: bool = False
    timezone: str = "UTC"


class AvailabilityQuery(BaseModel):
    start_datetime: datetime
    end_datetime: datetime
    duration_minutes: int
    service_id: Optional[int] = None
    buffer_minutes: int = 0
    preferred_times: Optional[List[TimeRange]] = None
    exclude_weekends: bool = False


# ==================== Booking Models ====================


class BookingCreate(BaseModel):
    specialist_id: int
    service_id: int
    booking_date: date
    start_time: time
    client_name: str
    client_email: EmailStr
    client_phone: Optional[str] = None
    notes: Optional[str] = None
    # Referral tracking - pass workplace_id if booking through business
    source_workplace_id: Optional[int] = None


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


# ==================== Calendar & Scheduling Models ====================


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


# ==================== Working Hours & Preferences ====================


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


# ==================== Smart Scheduling ====================


class SmartSchedulingSuggestion(BaseModel):
    suggested_datetime: datetime
    duration_minutes: int
    confidence_score: float  # 0.0 to 1.0
    reason: str
    alternative_times: List[datetime]
    conflicts: List[str]


# ==================== Authentication Models ====================


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


# ==================== Verification Models ====================


class VerificationRequest(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    verification_type: str = "registration"  # "registration" or "login"
    # Optional registration fields (ignored during verification)
    name: Optional[str] = None
    bio: Optional[str] = None

    class Config:
        extra = "allow"  # Allow additional fields from frontend


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


# ==================== Consumer Models ====================


class ConsumerCreate(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None


class ConsumerResponse(BaseModel):
    id: int
    name: str
    email: str
    phone: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== Referral Models ====================


class ReferralCreate(BaseModel):
    consumer_id: int
    specialist_id: int
    referred_by_specialist_id: Optional[int] = None
    referred_by_workplace_id: Optional[int] = None


class ReferralResponse(BaseModel):
    id: int
    consumer_id: int
    specialist_id: int
    referred_by_specialist_id: Optional[int] = None
    referred_by_workplace_id: Optional[int] = None
    referral_date: datetime

    class Config:
        from_attributes = True


# ==================== Client Profile Models ====================


class AppointmentNote(BaseModel):
    """Individual appointment note"""

    date: datetime
    note: str
    booking_id: Optional[int] = None


class ClientProfileCreate(BaseModel):
    """Create a new client profile"""

    consumer_id: int
    bio: Optional[str] = None
    score: Optional[int] = Field(None, ge=1, le=10, description="Client rating 1-10")
    notes: Optional[List[AppointmentNote]] = []


class ClientProfileUpdate(BaseModel):
    """Update an existing client profile"""

    bio: Optional[str] = None
    score: Optional[int] = Field(None, ge=1, le=10, description="Client rating 1-10")
    notes: Optional[List[AppointmentNote]] = None

    class Config:
        from_attributes = True


class ClientProfileResponse(BaseModel):
    """Client profile response"""

    id: int
    specialist_id: int
    consumer_id: int
    bio: Optional[str] = None
    score: Optional[int] = None
    notes: Optional[List[AppointmentNote]] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ClientSummary(BaseModel):
    """Summary of a client for list view"""

    consumer_id: int
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    total_bookings: int
    last_booking_date: Optional[datetime] = None
    next_booking_date: Optional[datetime] = None
    score: Optional[int] = None
    has_profile: bool = False

    class Config:
        from_attributes = True


class ClientDetail(BaseModel):
    """Detailed client information including booking history"""

    consumer: ConsumerResponse
    profile: Optional[ClientProfileResponse] = None
    bookings_past: List[dict]  # Past bookings
    bookings_future: List[dict]  # Upcoming bookings
    total_revenue: float = 0.0
    first_booking_date: Optional[datetime] = None

    class Config:
        from_attributes = True


# ==================== Error Models ====================


class ErrorResponse(BaseModel):
    error: str
    detail: str
    timestamp: datetime
