# AI Agent Instructions for Professional Scheduling Platform

## Architecture Overview

**Monolithic FastAPI app** with SQLAlchemy ORM, JWT auth, and vanilla JS frontend. All backend logic lives in `src/calendar_app/main.py` (~5600 lines). Frontend is modular ES6 JavaScript in `static/js/`.

### Core Data Model
- **CalendarEvent**: Recurring availability patterns (daily/weekly/monthly) with `rrule` library
- **AvailabilitySlot**: Legacy table - **deprecated**, do not query or reference
- **Booking**: Consumer appointments linked to CalendarEvent instances
- **Specialist**: Professional users with JWT auth
- **ServiceDB**: Services offered (name, price, duration, workplace_id)
- **Workplace**: Physical locations with Yelp API integration
- **ClientProfile**: Consumer contact info with favorite tracking

### Key Architectural Decisions
1. **No AvailabilitySlot**: Removed in favor of CalendarEvent. All availability queries filter `event_type="availability"` and `is_active=True`
2. **Date handling**: Backend uses `datetime.strptime()` (local timezone). Frontend uses `parseDateLocal()` to avoid UTC conversion bugs from `new Date("YYYY-MM-DD")`
3. **Specialist-Workplace**: Many-to-many relationship via `specialist_workplace_association` table with role tracking
4. **AI Assistant**: Google Gemini integration for drafting client messages (requires `GEMINI_API_KEY` in `.env`)

## Development Workflow

### Starting the Server
```bash
./start.sh                          # Recommended
# OR
python scripts/start_server.py     # Direct invocation
# Runs on http://localhost:8002
```

### Running Tests
```bash
pytest tests/                       # All tests
pytest tests/test_api.py           # Specific file
pytest --cov=src.calendar_app      # With coverage
```

### Database Operations
- **Migrations**: Uses Alembic (see `ALEMBIC_GUIDE.md`)
- **Schema**: SQLite dev, PostgreSQL production
- **Seeding**: `python scripts/populate_db.py`
- **Reset**: `rm calendar_app.db test.db` (server recreates on restart)

## Project-Specific Conventions

### Date/Time Handling (CRITICAL)
- **Backend**: `date.isoformat()` returns YYYY-MM-DD (no timezone)
- **Frontend**: Always use `parseDateLocal(dateStr)` instead of `new Date(dateStr)` to parse YYYY-MM-DD dates
- **Why**: `new Date("2024-02-28")` interprets as UTC midnight → wrong day in local timezone
- **Functions**: `formatDateLocal(date)`, `parseDateLocal(dateStr)` in `unified-calendar.js`

### Authentication Pattern
```python
# Endpoint protection
@app.post("/specialist/{specialist_id}/endpoint")
async def endpoint(
    specialist_id: int,
    db: Session = Depends(get_db),
    current_specialist: Specialist = Depends(require_authentication_dep)
):
    # Verify access
    if current_specialist.id != specialist_id:
        raise HTTPException(status_code=403, detail="Access denied")
```

### Calendar Event Queries
```python
# ✅ Correct: Query active availability
events = db.query(CalendarEvent).filter(
    CalendarEvent.specialist_id == specialist_id,
    CalendarEvent.event_type == "availability",
    CalendarEvent.is_active == True
).all()

# ❌ Wrong: Do NOT query AvailabilitySlot
# This table is deprecated and will be removed
```

### Frontend Module Pattern
- **Initialization**: `professional-init.js` creates placeholder functions for SSR
- **Modules**: Each feature has dedicated file (`bookings.js`, `clients.js`, etc.)
- **Main**: `main.js` imports and wires modules together
- **Example**: `window.loadBookings = placeholderFn('loadBookings')` → replaced by actual export

### CSS Architecture
- **shared.css**: Global components (buttons, forms, cards) - dark theme with gold accents (#D4AF37)
- **professional.css**: Dashboard-specific styles (1873 lines) - uses class-based styling, not inline
- **Pattern**: Paragraphs use `.section-subtitle`, headings use `.section h2`
- **Avoid**: Inline styles except for specific overrides

### API Endpoint Naming
- Specialist operations: `/specialist/{id}/action`
- Consumer operations: `/specialists/` (plural) for catalog
- Calendar: `/specialist/{id}/calendar/instances` for date range queries
- Bookings: `/booking/` (singular) for CRUD operations

## Common Patterns

### Creating Recurring Schedules
```python
# Weekly schedule with multiple days
schedule = CalendarEvent(
    specialist_id=specialist_id,
    event_type="availability",
    start_time=time(9, 0),
    end_time=time(17, 0),
    recurrence_rule="RRULE:FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR",
    is_active=True
)
```

### Generating Calendar Instances
```python
from dateutil.rrule import rrulestr, WEEKLY, MO, TU, WE, TH, FR

# Parse recurrence rule
rrule_obj = rrulestr(event.recurrence_rule, dtstart=start_date)
# Generate dates
dates = list(rrule_obj.between(start_date, end_date, inc=True))
```

### Client Profile Lookups
```python
# Check if client exists before creating booking
client = db.query(ClientProfile).filter(
    ClientProfile.specialist_id == specialist_id,
    ClientProfile.email == booking.client_email
).first()

if not client:
    # Create new client profile
    client = ClientProfile(specialist_id=specialist_id, ...)
```

## Integration Points

### Yelp API (`yelp_service.py`)
- Search businesses: `yelp_service.search_businesses(term, location, categories)`
- Get details: `yelp_service.get_business(business_id)`
- Requires `YELP_API_KEY` in environment

### Google Gemini AI (`ai_assistant.py`)
- Draft messages: `get_assistant().draft_reschedule_message(...)`
- Fallback to templates if API fails
- Requires `GEMINI_API_KEY` in environment
- Free tier: 1500 requests/day

### Email/SMS Verification (`verification_service.py`)
- Codes stored in `VerificationCode` table
- 6-digit codes, 10-minute expiration
- Used for specialist signup flow

## File Organization

```
src/calendar_app/
├── main.py                 # All endpoints (~5600 lines)
├── database.py             # SQLAlchemy models
├── models.py               # Pydantic schemas
├── auth.py                 # JWT token logic
├── config.py               # Environment variables
├── ai_assistant.py         # Gemini integration
├── verification_service.py # Email/SMS codes
├── yelp_service.py         # Yelp API client
├── templates/              # Jinja2 HTML
│   ├── professional.html   # Main dashboard (1549 lines)
│   ├── consumer.html       # Consumer portal
│   └── consumer_booking.html
└── static/
    ├── js/                 # Modular ES6
    │   ├── main.js         # Module wiring
    │   ├── unified-calendar.js  # Calendar UI
    │   ├── bookings.js     # Booking management
    │   ├── clients.js      # Client list/profiles
    │   └── ai-assistant.js # AI modal logic
    └── css/
        ├── shared.css      # Global components
        └── professional.css # Dashboard styles
```

## Testing Patterns

- **Integration tests**: Use `TestClient` from FastAPI
- **Database**: Tests use `test.db` (separate from `calendar_app.db`)
- **Auth**: Create test specialist, generate JWT, include in headers
- **Bookings**: Test full flow (create service → availability → booking)

## Debugging Tips

1. **Import errors**: Run from project root, `export PYTHONPATH=$(pwd)`
2. **Date discrepancies**: Check for `new Date()` vs `parseDateLocal()` usage
3. **Calendar not showing**: Verify `is_active=True` filter on queries
4. **Auth failures**: Check JWT token in localStorage, verify specialist_id matches
5. **AI errors**: Confirm `GEMINI_API_KEY` set, check fallback message behavior

## External Dependencies

- **dateutil**: Recurrence rule parsing (rrule)
- **python-jose**: JWT tokens
- **Twilio**: SMS verification (optional)
- **Yelp Fusion API**: Business search
- **Google Generative AI**: Message drafting

## Current Roadmap Items
- Payment processing integration
- Notification system (email/SMS for bookings)
- Service photos/videos
- Client loyalty platform
- Dashboard summary count fixes
