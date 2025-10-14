from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_professional = Column(Boolean, default=False)
    profession = Column(String, nullable=True)
    hourly_rate = Column(Float, nullable=True)
    
    appointments_as_professional = relationship("Appointment", back_populates="professional", foreign_keys="Appointment.professional_id")
    appointments_as_client = relationship("Appointment", back_populates="client", foreign_keys="Appointment.client_id")
    availabilities = relationship("Availability", back_populates="user")

class Availability(Base):
    __tablename__ = "availabilities"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    day_of_week = Column(Integer)  # 0=Monday, 6=Sunday
    start_time = Column(String)  # Format: "HH:MM"
    end_time = Column(String)    # Format: "HH:MM"
    
    user = relationship("User", back_populates="availabilities")

class Appointment(Base):
    __tablename__ = "appointments"
    
    id = Column(Integer, primary_key=True, index=True)
    professional_id = Column(Integer, ForeignKey("users.id"))
    client_id = Column(Integer, ForeignKey("users.id"))
    date = Column(DateTime)
    start_time = Column(String)
    end_time = Column(String)
    status = Column(String)  # "pending", "confirmed", "cancelled"
    created_at = Column(DateTime, default=datetime.now)
    
    professional = relationship("User", foreign_keys=[professional_id], back_populates="appointments_as_professional")
    client = relationship("User", foreign_keys=[client_id], back_populates="appointments_as_client")

