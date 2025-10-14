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
