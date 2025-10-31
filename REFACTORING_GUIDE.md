# Refactoring Implementation Guide

This guide provides **copy-paste ready code** for implementing the refactoring recommendations from the technical debt assessment.

---

## Step 1: Setup Alembic for Database Migrations (30 minutes)

### Install Alembic
```bash
poetry add alembic
```

### Initialize Alembic
```bash
alembic init alembic
```

### Configure Alembic

**File: `alembic/env.py`**
```python
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# Import your models
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from src.calendar_app.database import Base, DATABASE_URL

# this is the Alembic Config object
config = context.config

# Set database URL
config.set_main_option("sqlalchemy.url", DATABASE_URL)

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Add your model's MetaData object here for 'autogenerate' support
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

### Create Initial Migration
```bash
# Generate migration from current models
alembic revision --autogenerate -m "Initial schema"

# Apply migration
alembic upgrade head
```

### Update `database.py`
```python
# Remove this line from production code:
# Base.metadata.create_all(bind=engine)  # ❌ Remove

# Instead, use alembic migrations
# Run: alembic upgrade head
```

---

## Step 2: Extract Configuration (15 minutes)

### Install python-dotenv
```bash
poetry add python-dotenv pydantic-settings
```

### Create `.env` file
```env
# .env
DATABASE_URL=sqlite:///./calendar_app.db
SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
SESSION_EXPIRE_HOURS=24

# Yelp API
YELP_API_KEY=your-yelp-api-key

# Twilio (for SMS)
TWILIO_ACCOUNT_SID=your-account-sid
TWILIO_AUTH_TOKEN=your-auth-token
TWILIO_PHONE_NUMBER=+1234567890

# Environment
ENVIRONMENT=development
DEBUG=true
```

### Update `config.py`
```python
# src/calendar_app/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    """Application settings from environment variables"""
    
    # Database
    database_url: str = "sqlite:///./calendar_app.db"
    
    # Security
    secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    session_expire_hours: int = 24
    
    # External APIs
    yelp_api_key: str
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_phone_number: str = ""
    
    # Application
    environment: str = "development"
    debug: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()

# Usage in code
settings = get_settings()
```

### Update `database.py`
```python
# src/calendar_app/database.py
from src.calendar_app.config import get_settings

settings = get_settings()
DATABASE_URL = settings.database_url

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)
```

---

## Step 3: Add Database Indexes (10 minutes)

### Update `database.py` models with indexes

```python
# src/calendar_app/database.py

class Booking(Base):
    __tablename__ = "bookings"
    
    id = Column(Integer, primary_key=True, index=True)
    specialist_id = Column(Integer, ForeignKey("specialists.id"), nullable=False, index=True)  # ✅ Index
    service_id = Column(Integer, ForeignKey("services.id"), index=True)  # ✅ Index
    
    client_name = Column(String, nullable=False, index=True)  # ✅ Index for search
    client_email = Column(String, nullable=False, index=True)  # ✅ Index for lookup
    client_phone = Column(String, nullable=True)
    
    notes = Column(String, nullable=True)
    date = Column(Date, nullable=False, index=True)  # ✅ Index for date queries
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    status = Column(String, default="pending", index=True)  # ✅ Index for filtering
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)  # ✅ Index for sorting

class AppointmentSession(Base):
    __tablename__ = "appointment_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=False, index=True)  # ✅ Index
    specialist_id = Column(Integer, ForeignKey("specialists.id"), nullable=False, index=True)  # ✅ Index
    consumer_id = Column(Integer, ForeignKey("consumers.id"), nullable=True, index=True)  # ✅ Index
    
    actual_start = Column(DateTime, nullable=True, index=True)  # ✅ Index for date queries
    actual_end = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)  # ✅ Index

class Consumer(Base):
    __tablename__ = "consumers"
    
    id = Column(Integer, primary_key=True, index=True)
    specialist_id = Column(Integer, ForeignKey("specialists.id"), nullable=False, index=True)  # ✅ Index
    
    name = Column(String, nullable=False, index=True)  # ✅ Index for search
    email = Column(String, nullable=True, index=True)  # ✅ Index for lookup
    phone = Column(String, nullable=True, index=True)  # ✅ Index for lookup
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)  # ✅ Index
```

### Generate migration
```bash
alembic revision --autogenerate -m "Add indexes to improve query performance"
alembic upgrade head
```

---

## Step 4: Fix N+1 Query Issues (20 minutes)

### Update `main.py` - `get_specialist_bookings()`

**Before (N+1 queries):**
```python
# ❌ Bad: N+1 queries
bookings = db.query(Booking).filter(...).all()

for booking in bookings:
    session = db.query(AppointmentSession).filter(
        AppointmentSession.booking_id == booking.id
    ).first()  # ❌ One query per booking
```

**After (Single query with JOIN):**
```python
from sqlalchemy.orm import joinedload

@app.get("/bookings/specialist/{specialist_id}")
def get_specialist_bookings(specialist_id: int, db: Session = Depends(get_db)):
    """Get all bookings for a specialist with related data"""
    
    # ✅ Good: Single query with eager loading
    bookings = (
        db.query(Booking)
        .options(
            joinedload(Booking.sessions),  # Eager load sessions
            joinedload(Booking.service)    # Eager load service
        )
        .filter(Booking.specialist_id == specialist_id)
        .all()
    )
    
    booking_responses = []
    for booking in bookings:
        # Now session is already loaded, no additional query
        session = booking.sessions[0] if booking.sessions else None
        
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
            } if booking.service else None,
            "session_id": session.id if session else None,
            "session_started": session.actual_start if session else None,
            "session_ended": session.actual_end if session else None,
            "actual_duration": session.actual_duration_minutes if session else None,
        }
        booking_responses.append(booking_dict)
    
    return booking_responses
```

### Update relationship in `database.py`

```python
class Booking(Base):
    __tablename__ = "bookings"
    # ... existing columns ...
    
    # Add relationship for eager loading
    sessions = relationship("AppointmentSession", back_populates="booking", lazy="select")
    service = relationship("ServiceDB", lazy="select")

class AppointmentSession(Base):
    __tablename__ = "appointment_sessions"
    # ... existing columns ...
    
    # Add back reference
    booking = relationship("Booking", back_populates="sessions")
```

---

## Step 5: Implement Pagination (30 minutes)

### Create pagination helper

**File: `src/calendar_app/core/pagination.py`**
```python
from typing import TypeVar, Generic, List, Optional
from pydantic import BaseModel
from fastapi import Query

T = TypeVar('T')

class PaginationParams:
    """Pagination query parameters"""
    
    def __init__(
        self,
        page: int = Query(1, ge=1, description="Page number (1-indexed)"),
        page_size: int = Query(20, ge=1, le=100, description="Items per page")
    ):
        self.page = page
        self.page_size = page_size
        self.skip = (page - 1) * page_size

class PageResponse(BaseModel, Generic[T]):
    """Paginated response wrapper"""
    
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool
    
    @classmethod
    def create(
        cls,
        items: List[T],
        total: int,
        page: int,
        page_size: int
    ):
        total_pages = (total + page_size - 1) // page_size
        
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1
        )
```

### Use pagination in endpoints

```python
from src.calendar_app.core.pagination import PaginationParams, PageResponse

@app.get("/bookings", response_model=PageResponse[BookingResponse])
def get_bookings(
    specialist_id: Optional[int] = None,
    status: Optional[str] = None,
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db)
):
    """Get paginated bookings"""
    
    # Build query
    query = db.query(Booking)
    
    if specialist_id:
        query = query.filter(Booking.specialist_id == specialist_id)
    if status:
        query = query.filter(Booking.status == status)
    
    # Get total count
    total = query.count()
    
    # Get page of results
    bookings = (
        query
        .order_by(Booking.created_at.desc())
        .offset(pagination.skip)
        .limit(pagination.page_size)
        .all()
    )
    
    # Convert to response models
    items = [BookingResponse.from_orm(b) for b in bookings]
    
    return PageResponse.create(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size
    )
```

---

## Step 6: Standardize Error Handling (30 minutes)

### Create custom exceptions

**File: `src/calendar_app/core/exceptions.py`**
```python
from fastapi import HTTPException
from typing import Optional, Dict, Any

class AppException(Exception):
    """Base application exception"""
    
    def __init__(
        self,
        message: str,
        code: str,
        status_code: int = 400,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

class ResourceNotFound(AppException):
    """Resource not found exception"""
    
    def __init__(self, resource: str, identifier: Any):
        super().__init__(
            message=f"{resource} not found",
            code="RESOURCE_NOT_FOUND",
            status_code=404,
            details={"resource": resource, "identifier": str(identifier)}
        )

class ResourceAlreadyExists(AppException):
    """Resource already exists exception"""
    
    def __init__(self, resource: str, field: str, value: Any):
        super().__init__(
            message=f"{resource} with {field}='{value}' already exists",
            code="RESOURCE_ALREADY_EXISTS",
            status_code=409,
            details={"resource": resource, "field": field, "value": str(value)}
        )

class ValidationError(AppException):
    """Validation error exception"""
    
    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=422,
            details={"field": field} if field else {}
        )

class AuthenticationError(AppException):
    """Authentication error exception"""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            code="AUTHENTICATION_ERROR",
            status_code=401
        )

class AuthorizationError(AppException):
    """Authorization error exception"""
    
    def __init__(self, message: str = "Not authorized to perform this action"):
        super().__init__(
            message=message,
            code="AUTHORIZATION_ERROR",
            status_code=403
        )
```

### Add error handlers

**File: `src/calendar_app/main.py`**
```python
from datetime import datetime
from fastapi import Request
from fastapi.responses import JSONResponse
from src.calendar_app.core.exceptions import AppException

@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """Handle custom application exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
                "timestamp": datetime.utcnow().isoformat(),
                "path": str(request.url)
            }
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    # Log the full exception
    import traceback
    traceback.print_exc()
    
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
                "timestamp": datetime.utcnow().isoformat(),
                "path": str(request.url)
            }
        }
    )
```

### Use in endpoints

```python
from src.calendar_app.core.exceptions import (
    ResourceNotFound,
    AuthorizationError,
    ValidationError
)

@app.get("/specialists/{specialist_id}")
def get_specialist(specialist_id: int, db: Session = Depends(get_db)):
    """Get specialist by ID"""
    
    specialist = db.query(Specialist).filter(Specialist.id == specialist_id).first()
    
    if not specialist:
        # ✅ Standardized error
        raise ResourceNotFound("Specialist", specialist_id)
    
    return specialist

@app.delete("/specialists/{specialist_id}/workplaces/{workplace_id}")
def remove_workplace(
    specialist_id: int,
    workplace_id: int,
    current_user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove workplace from specialist"""
    
    # Check authorization
    if specialist_id != current_user_id:
        raise AuthorizationError("You can only modify your own workplaces")
    
    # ... rest of logic
```

---

## Step 7: Add Input Validation (20 minutes)

### Create validation models

**File: `src/calendar_app/schemas/booking.py`**
```python
from pydantic import BaseModel, Field, validator
from datetime import date, time, datetime

class CreateBookingRequest(BaseModel):
    """Request model for creating a booking"""
    
    specialist_id: int = Field(..., gt=0, description="Specialist ID")
    service_id: int = Field(..., gt=0, description="Service ID")
    
    client_name: str = Field(..., min_length=1, max_length=100)
    client_email: str = Field(..., regex=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    client_phone: Optional[str] = Field(None, regex=r'^\+?1?\d{9,15}$')
    
    date: date = Field(...)
    start_time: time = Field(...)
    notes: Optional[str] = Field(None, max_length=500)
    
    @validator('date')
    def date_must_be_future(cls, v):
        """Validate date is not in the past"""
        if v < date.today():
            raise ValueError('Booking date must be today or in the future')
        return v
    
    @validator('start_time')
    def time_must_be_business_hours(cls, v):
        """Validate time is during business hours"""
        if v.hour < 6 or v.hour >= 22:
            raise ValueError('Booking must be between 6 AM and 10 PM')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "specialist_id": 1,
                "service_id": 2,
                "client_name": "John Doe",
                "client_email": "john@example.com",
                "client_phone": "+14155551234",
                "date": "2025-11-01",
                "start_time": "10:00:00",
                "notes": "First session"
            }
        }
```

### Use in endpoints

```python
@app.post("/bookings", response_model=BookingResponse)
def create_booking(
    request: CreateBookingRequest,  # ✅ Pydantic validates automatically
    db: Session = Depends(get_db)
):
    """Create a new booking"""
    
    # Pydantic has already validated:
    # - specialist_id > 0
    # - client_email format
    # - client_phone format
    # - date is in future
    # - time is in business hours
    
    booking = Booking(
        specialist_id=request.specialist_id,
        service_id=request.service_id,
        client_name=request.client_name,
        client_email=request.client_email,
        client_phone=request.client_phone,
        date=request.date,
        start_time=request.start_time,
        notes=request.notes
    )
    
    db.add(booking)
    db.commit()
    db.refresh(booking)
    
    return booking
```

---

## Step 8: Add Request Logging (15 minutes)

### Create logging middleware

**File: `src/calendar_app/core/logging_middleware.py`**
```python
import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("api")

class LoggingMiddleware(BaseHTTPMiddleware):
    """Log all API requests and responses"""
    
    async def dispatch(self, request: Request, call_next):
        # Generate request ID
        request_id = str(time.time())
        
        # Log request
        logger.info(
            f"REQUEST {request_id}: {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "client_ip": request.client.host
            }
        )
        
        # Process request
        start_time = time.time()
        response = await call_next(request)
        duration = time.time() - start_time
        
        # Log response
        logger.info(
            f"RESPONSE {request_id}: {response.status_code} in {duration:.2f}s",
            extra={
                "request_id": request_id,
                "status_code": response.status_code,
                "duration_ms": duration * 1000
            }
        )
        
        return response
```

### Add to FastAPI app

```python
# main.py
from src.calendar_app.core.logging_middleware import LoggingMiddleware

app = FastAPI()
app.add_middleware(LoggingMiddleware)
```

---

## Quick Reference: Before vs After

### Query Optimization
```python
# ❌ Before: N+1 queries
bookings = db.query(Booking).all()
for b in bookings:
    session = db.query(Session).filter(Session.booking_id == b.id).first()

# ✅ After: Single query
bookings = db.query(Booking).options(joinedload(Booking.sessions)).all()
```

### Error Handling
```python
# ❌ Before: Inconsistent
raise HTTPException(404, "Not found")
return JSONResponse({"error": "Failed"}, 400)

# ✅ After: Standardized
raise ResourceNotFound("Specialist", specialist_id)
```

### Validation
```python
# ❌ Before: Manual checks
if not specialist_id or specialist_id < 0:
    raise HTTPException(400, "Invalid ID")

# ✅ After: Pydantic
specialist_id: int = Field(..., gt=0)
```

### Configuration
```python
# ❌ Before: Hardcoded
API_KEY = "abc123"

# ✅ After: Environment variables
from src.calendar_app.config import get_settings
settings = get_settings()
API_KEY = settings.api_key
```

---

## Testing the Changes

### Run migration
```bash
alembic upgrade head
```

### Test pagination
```bash
curl "http://localhost:8000/bookings?page=1&page_size=10"
```

### Test error handling
```bash
curl "http://localhost:8000/specialists/99999"
# Should return standardized error:
# {
#   "error": {
#     "code": "RESOURCE_NOT_FOUND",
#     "message": "Specialist not found",
#     ...
#   }
# }
```

### Check logs
```bash
tail -f logs/api.log
```
