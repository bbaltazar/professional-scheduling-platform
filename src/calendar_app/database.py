"""
Database configuration and models for the calendar app
"""

import databases
import sqlalchemy
from sqlalchemy import (
    create_engine,
    MetaData,
    Table,
    Column,
    Integer,
    String,
    Float,
    ForeignKey,
    DateTime,
    Boolean,
    Date,
    Time,
    Text,
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from typing import List

# Database URL - using SQLite for development
DATABASE_URL = "sqlite:///./calendar_app.db"

# SQLAlchemy setup
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database instance for async operations
database = databases.Database(DATABASE_URL)


# SQLAlchemy Models
class Specialist(Base):
    __tablename__ = "specialists"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    bio = Column(String)  # Professional bio/description
    phone = Column(String)

    # Relationships
    services = relationship("ServiceDB", back_populates="specialist")
    availability_slots = relationship("AvailabilitySlot", back_populates="specialist")
    bookings = relationship("Booking", back_populates="specialist")
    calendar_events = relationship("CalendarEvent", back_populates="specialist")
    working_hours = relationship("WorkingHours", back_populates="specialist")
    scheduling_preferences = relationship("SchedulingPreferences", back_populates="specialist")


class ServiceDB(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    price = Column(Float)
    duration = Column(Integer)  # duration in minutes
    specialist_id = Column(Integer, ForeignKey("specialists.id"))

    # Relationships
    specialist = relationship("Specialist", back_populates="services")
    bookings = relationship("Booking", back_populates="service")


class AvailabilitySlot(Base):
    __tablename__ = "availability_slots"

    id = Column(Integer, primary_key=True, index=True)
    specialist_id = Column(Integer, ForeignKey("specialists.id"))
    date = Column(Date)  # Which date
    start_time = Column(Time)  # Start time (e.g., 09:00)
    end_time = Column(Time)  # End time (e.g., 17:00)
    is_available = Column(Boolean, default=True)

    # Relationships
    specialist = relationship("Specialist", back_populates="availability_slots")


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    specialist_id = Column(Integer, ForeignKey("specialists.id"))
    service_id = Column(Integer, ForeignKey("services.id"))
    client_name = Column(String)
    client_email = Column(String)
    client_phone = Column(String)
    date = Column(Date)
    start_time = Column(Time)
    end_time = Column(Time)
    status = Column(String, default="confirmed")  # confirmed, cancelled, completed
    notes = Column(String)

    # Relationships
    specialist = relationship("Specialist", back_populates="bookings")
    service = relationship("ServiceDB", back_populates="bookings")


class CalendarEvent(Base):
    __tablename__ = "calendar_events"

    id = Column(Integer, primary_key=True, index=True)
    specialist_id = Column(Integer, ForeignKey("specialists.id"))
    
    # Event basics
    title = Column(String)
    description = Column(Text, nullable=True)
    location = Column(String, nullable=True)
    
    # Date and time (supports both timed and all-day events)
    start_datetime = Column(DateTime)  # Full datetime for timed events
    end_datetime = Column(DateTime)    # Full datetime for timed events
    is_all_day = Column(Boolean, default=False)
    timezone = Column(String, default="UTC")
    
    # Event properties
    event_type = Column(String, default="availability")  # 'availability', 'block', 'appointment', 'break'
    category = Column(String, nullable=True)  # 'work', 'personal', 'vacation', 'meeting', etc.
    priority = Column(String, default="normal")  # 'low', 'normal', 'high', 'urgent'
    color = Column(String, nullable=True)  # Hex color for visual organization
    
    # Availability settings (for availability events)
    is_bookable = Column(Boolean, default=True)
    max_bookings = Column(Integer, nullable=True)  # Null = unlimited
    buffer_before = Column(Integer, default=0)  # Minutes of buffer before
    buffer_after = Column(Integer, default=0)   # Minutes of buffer after
    
    # Recurrence settings (RRULE-like flexibility)
    is_recurring = Column(Boolean, default=False)
    recurrence_rule = Column(Text, nullable=True)  # JSON with full recurrence config
    recurrence_end_date = Column(Date, nullable=True)
    recurrence_count = Column(Integer, nullable=True)  # Max occurrences
    
    # Event status and metadata
    status = Column(String, default="confirmed")  # 'tentative', 'confirmed', 'cancelled'
    visibility = Column(String, default="public")  # 'public', 'private'
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    
    # For recurring event management
    recurring_event_id = Column(String, nullable=True)  # Groups recurring instances
    original_start = Column(DateTime, nullable=True)    # For modified instances
    
    # Relationships
    specialist = relationship("Specialist", back_populates="calendar_events")
    event_exceptions = relationship("EventException", back_populates="event")


class EventException(Base):
    __tablename__ = "event_exceptions"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("calendar_events.id"))
    exception_date = Column(Date)  # Date this exception applies to
    exception_type = Column(String)  # 'cancelled', 'modified', 'moved'
    
    # For modified exceptions - override original event data
    new_start_datetime = Column(DateTime, nullable=True)
    new_end_datetime = Column(DateTime, nullable=True)
    new_title = Column(String, nullable=True)
    new_description = Column(Text, nullable=True)
    
    created_at = Column(DateTime)
    
    # Relationships
    event = relationship("CalendarEvent", back_populates="event_exceptions")


class WorkingHours(Base):
    __tablename__ = "working_hours"

    id = Column(Integer, primary_key=True, index=True)
    specialist_id = Column(Integer, ForeignKey("specialists.id"))
    
    # Day of week (0 = Monday, 6 = Sunday)
    day_of_week = Column(Integer)
    
    # Time ranges (supports multiple ranges per day)
    time_ranges = Column(Text)  # JSON array of {start_time, end_time} objects
    
    # Working hours settings
    is_working_day = Column(Boolean, default=True)
    break_duration = Column(Integer, default=0)  # Minutes of break time
    break_start_time = Column(Time, nullable=True)
    
    # Timezone
    timezone = Column(String, default="UTC")
    
    # Status
    is_active = Column(Boolean, default=True)
    effective_date = Column(Date)  # When these hours take effect
    
    # Relationships
    specialist = relationship("Specialist", back_populates="working_hours")


class SchedulingPreferences(Base):
    __tablename__ = "scheduling_preferences"

    id = Column(Integer, primary_key=True, index=True)
    specialist_id = Column(Integer, ForeignKey("specialists.id"))
    
    # Buffer times (in minutes)
    default_buffer_before = Column(Integer, default=15)
    default_buffer_after = Column(Integer, default=15)
    
    # Booking windows
    advance_booking_days = Column(Integer, default=365)  # How far in advance bookings allowed
    min_booking_notice = Column(Integer, default=60)     # Minimum notice in minutes
    
    # Scheduling preferences
    auto_accept_bookings = Column(Boolean, default=True)
    max_daily_bookings = Column(Integer, nullable=True)
    max_weekly_bookings = Column(Integer, nullable=True)
    
    # Time slot preferences
    minimum_slot_duration = Column(Integer, default=15)  # Minutes
    slot_increment = Column(Integer, default=15)         # Minutes
    
    # Break and travel preferences
    lunch_break_start = Column(Time, nullable=True)
    lunch_break_duration = Column(Integer, default=60)   # Minutes
    travel_time_between_appointments = Column(Integer, default=0)  # Minutes
    
    # Timezone and locale
    timezone = Column(String, default="UTC")
    date_format = Column(String, default="YYYY-MM-DD")
    time_format = Column(String, default="24h")  # '12h' or '24h'
    
    # Notifications
    email_reminders = Column(Boolean, default=True)
    sms_reminders = Column(Boolean, default=False)
    reminder_advance_time = Column(Integer, default=1440)  # Minutes (24 hours)
    
    # Status
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    
    # Relationships
    specialist = relationship("Specialist", back_populates="scheduling_preferences")


class VerificationCode(Base):
    __tablename__ = "verification_codes"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, index=True)
    phone = Column(String, index=True)
    code = Column(String, index=True)  # 6-digit verification code
    verification_type = Column(String)  # 'email', 'sms', 'login', 'registration'
    is_used = Column(Boolean, default=False)
    created_at = Column(DateTime)
    expires_at = Column(DateTime)


# Create all tables
Base.metadata.create_all(bind=engine)


# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
