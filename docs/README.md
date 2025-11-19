# Calendar Booking Application

A FastAPI-based appointment booking system with recurring schedule support, JWT authentication, and a responsive luxury-themed UI.

## Project Structure

```
calendar_app/
├── src/
│   └── calendar_app/          # Main application package
│       ├── main.py            # FastAPI app with all endpoints
│       ├── database.py        # SQLAlchemy models and DB setup
│       ├── models.py          # Pydantic request/response models
│       ├── auth.py            # JWT authentication logic
│       ├── config.py          # Environment configuration
│       ├── verification_service.py  # Email/SMS verification
│       ├── templates/         # Jinja2 HTML templates
│       └── static/            # CSS, JS, images
├── tests/                     # All test files
│   ├── test_api.py
│   ├── test_booking_integration.py
│   ├── test_consumer.py
│   ├── test_frontend_integration.py
│   ├── test_persistence.py
│   └── test_services_management.py
├── scripts/                   # Utility scripts
│   ├── populate_db.py         # Seed database with test data
│   └── start_server.py        # Server startup helper
├── calendar_app.db            # SQLite database (production)
├── test.db                    # SQLite database (testing)
├── pyproject.toml             # Poetry dependencies
├── poetry.lock                # Locked dependencies
└── .env.example               # Environment variables template
```

## Features

- **Recurring Schedules**: Support for daily, weekly, monthly, and yearly recurring appointments
- **JWT Authentication**: Secure specialist authentication with token-based system
- **Service Management**: Create, update, and delete services with pricing
- **Calendar Integration**: Visual calendar interface for availability management
- **Booking System**: Consumer-facing booking flow with time slot selection
- **Email/SMS Verification**: Two-factor authentication for specialist signup
- **Workplace Management**: ⭐ **NEW** - Professionals can manage multiple workplaces with Yelp API integration
  - Many-to-many specialist-workplace relationships
  - Yelp business search and validation
  - Verified workplace listings
  - Role-based associations (owner, employee, contractor)
- **Responsive UI**: Luxury glassmorphism theme with mobile support

## Tech Stack

- **Backend**: FastAPI 0.104+
- **ORM**: SQLAlchemy 2.0+
- **Database**: SQLite (can be swapped for PostgreSQL)
- **Migrations**: Alembic 1.13+ (database schema versioning)
- **Authentication**: JWT (python-jose)
- **Templates**: Jinja2
- **Testing**: pytest with TestClient
- **CSS**: Custom glassmorphism/luxury gold theme

## Getting Started

### Prerequisites

- Python 3.11+
- Poetry (for dependency management)

### Installation

1. **Clone the repository**
   ```bash
   cd /path/to/calendar_app
   ```

2. **Install dependencies**
   ```bash
   poetry install
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Initialize the database**
   ```bash
   # Apply database migrations
   ./scripts/migrate.sh upgrade
   
   # Optional: add test data
   poetry run python scripts/populate_db.py
   ```
   
   See [ALEMBIC_GUIDE.md](ALEMBIC_GUIDE.md) for detailed migration documentation.

### Running the Application

#### Option 1: Using Poetry directly
```bash
poetry run uvicorn src.calendar_app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Option 2: Using the start script
```bash
poetry run python scripts/start_server.py
```

The application will be available at:
- **Professional Portal**: http://localhost:8000/professional
- **Consumer Portal**: http://localhost:8000/consumer
- **API Docs**: http://localhost:8000/docs

### Running Tests

```bash
# Run all tests
poetry run pytest tests/

# Run specific test file
poetry run pytest tests/test_booking_integration.py

# Run with coverage
poetry run pytest tests/ --cov=src.calendar_app --cov-report=html
```

## API Endpoints

### Authentication
- `POST /signup/request-verification` - Request verification code
- `POST /signup/verify-code` - Verify code and complete signup
- `POST /login` - Login and get JWT token

### Services
- `GET /services` - List all services for a specialist
- `POST /services` - Create new service
- `PUT /services/{id}` - Update service
- `DELETE /services/{id}` - Delete service

### Calendar
- `GET /availability/slots` - Get available time slots
- `POST /availability/slots` - Create availability slot
- `DELETE /availability/slots/{id}` - Delete availability slot
- `POST /recurring-schedules` - Create recurring schedule

### Bookings
- `POST /bookings` - Create new booking
- `GET /bookings` - List bookings for specialist
- `PUT /bookings/{id}` - Update booking
- `DELETE /bookings/{id}` - Cancel booking

### Consumer
- `GET /professionals` - List all professionals
- `GET /professionals/{id}/services` - Get services for a professional
- `GET /professionals/{id}/availability` - Get available time slots
- `POST /bookings/book` - Book an appointment

## Configuration

Environment variables (`.env` file):

```env
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
DATABASE_URL=sqlite:///./calendar_app.db
DEBUG=True
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
```

## Database Schema

### Main Tables
- **specialists**: Professional users with authentication
- **services**: Services offered by specialists
- **availability_slots**: Available time slots for booking
- **calendar_events**: Recurring schedule patterns
- **bookings**: Consumer booking records

## Development

### Code Organization

- **main.py**: FastAPI application, routes, and business logic
- **database.py**: SQLAlchemy ORM models and database session
- **models.py**: Pydantic models for request/response validation
- **auth.py**: JWT token creation and verification
- **config.py**: Environment-based settings
- **verification_service.py**: Email/SMS verification logic

### Adding New Features

1. Add database models to `src/calendar_app/database.py`
2. Add Pydantic models to `src/calendar_app/models.py`
3. Add endpoints to `src/calendar_app/main.py`
4. Add templates to `src/calendar_app/templates/`
5. Add tests to `tests/test_*.py`

## Troubleshooting

### Import Errors
If you get import errors, make sure you're running from the project root:
```bash
cd /path/to/calendar_app
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Database Errors
Reset the database:
```bash
rm calendar_app.db test.db test_auth.db
# Restart the server to recreate tables
```

## Roadmap
[ ] Create a commerce page that conveys the value prop
* feature set:
   - service listings
   - loyal customer platform
   - booking management
   - payment processing
   - reviews and ratings
[ ] Create a relationship between professional and workplace
[ ] Add payment processing integration for bookings
[ ] Add payment processing integration for new signups
[ ] Implement notification system for bookings
[ ] Enhance UI with more luxury-themed components
[ ] Add Video and Photos of Services across application
[ ] Fix dashboard summary counts

## License

MIT License - See LICENSE file for details
