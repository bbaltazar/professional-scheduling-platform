# Project Structure

This document describes the organization of the Professional Scheduling Platform codebase.

## Directory Overview

```
calendar_app/
├── docs/                          # 📚 Documentation
│   ├── README.md                  # Main project documentation
│   ├── MIGRATION.md               # Database migration guide
│   ├── START_SERVER.md            # Server startup instructions
│   └── PROJECT_STRUCTURE.md       # This file
│
├── data/                          # 📊 Data files
│   ├── samples/                   # Sample CSV files for testing
│   │   ├── client_template.csv
│   │   ├── sample_clients.csv
│   │   └── barbers_sanjose_top_expanded_partial.csv
│   └── test/                      # Test databases
│       └── test_auth.db
│
├── frontend/                      # 🎨 Frontend source code
│   └── src/                       # TypeScript source
│       ├── types.ts               # Type definitions
│       ├── utils.ts               # Utility functions
│       ├── navigation.ts          # Navigation & dashboard
│       └── schedule.ts            # Schedule management
│
├── scripts/                       # 🔧 Utility scripts
│   ├── migrations/                # One-off migration scripts
│   │   ├── add_imports.py
│   │   ├── add_is_favorite_column.py
│   │   ├── migrate_appointment_sessions.py
│   │   ├── migrate_add_client_profiles.py
│   │   ├── migrate_add_referrals.py
│   │   └── migrate_legacy_bookings.py
│   ├── populate_db.py             # DB population
│   ├── start_server.py            # Server launcher
│   ├── add_workplaces.py          # Workplace setup
│   └── verify_workplaces.py       # Workplace verification
│
├── src/                           # 🐍 Python backend
│   └── calendar_app/
│       ├── __init__.py
│       ├── auth.py                # Authentication logic
│       ├── config.py              # Configuration
│       ├── database.py            # Database setup
│       ├── main.py                # FastAPI application
│       ├── models.py              # SQLAlchemy models
│       ├── verification_service.py # Phone verification
│       ├── yelp_service.py        # Yelp integration
│       ├── static/
│       │   ├── css/
│       │   │   └── shared.css
│       │   └── js/                # Compiled TypeScript + legacy JS
│       │       ├── types.js       # ← Compiled from frontend/src/types.ts
│       │       ├── utils.js       # ← Compiled from frontend/src/utils.ts
│       │       ├── navigation.js  # ← Compiled from frontend/src/navigation.ts
│       │       ├── schedule.js    # ← Compiled from frontend/src/schedule.ts
│       │       ├── *.js.map       # Source maps
│       │       ├── auth.js        # Legacy JS (not yet converted)
│       │       ├── bookings.js    # Legacy JS (not yet converted)
│       │       ├── clients.js     # Legacy JS (not yet converted)
│       │       └── ...            # Other legacy JS modules
│       └── templates/
│           ├── index.html
│           ├── professional.html
│           ├── consumer.html
│           └── ...
│
├── tests/                         # 🧪 All tests
│   ├── __init__.py
│   ├── test_api.py
│   ├── test_authentication.py
│   ├── test_booking_integration.py
│   ├── test_consumer.py
│   ├── test_csv_upload.py
│   ├── test_frontend_integration.py
│   ├── test_persistence.py
│   ├── test_services_management.py
│   └── test_workplace.py
│
├── alembic/                       # 📦 Database migrations (Alembic)
│   ├── versions/
│   │   └── *.py                   # Migration scripts
│   ├── env.py
│   └── script.py.mako
│
├── .env                           # Environment variables (not in git)
├── .env.example                   # Environment template
├── .gitignore
├── alembic.ini                    # Alembic configuration
├── calendar_app.db                # Main SQLite database
├── package.json                   # Node.js dependencies
├── package-lock.json
├── poetry.lock                    # Python dependencies lock
├── pyproject.toml                 # Python project config
├── README.md                      # Project overview (links to docs/)
├── tsconfig.json                  # TypeScript configuration
├── start.sh                       # Quick start script
└── validate_js.mjs                # JavaScript validation
```

## Key Directories

### `/docs` - Documentation
All project documentation including setup guides, migration instructions, and architecture docs.

### `/data` - Data Files
- `samples/` - CSV templates and sample data for testing
- `test/` - Test databases (not committed to git)

### `/frontend/src` - TypeScript Source
All TypeScript source code lives here. Compiled output goes to `src/calendar_app/static/js/`.

**Build process:**
```bash
frontend/src/utils.ts → (tsc) → src/calendar_app/static/js/utils.js
```

### `/scripts` - Utility Scripts
- Root level: Reusable utilities (populate_db.py, start_server.py)
- `migrations/`: One-off migration scripts (historical, not always needed)

### `/src/calendar_app` - Python Backend
FastAPI application with models, routes, services, and static files.

### `/tests` - Test Suite
All tests in one place. Run with `pytest`.

## TypeScript Migration Strategy

The project is gradually migrating from JavaScript to TypeScript:

**Converted modules (4/15):**
- ✅ `types.ts` - Type definitions
- ✅ `utils.ts` - Utility functions
- ✅ `navigation.ts` - Navigation & dashboard
- ✅ `schedule.ts` - Schedule management (partial)

**Legacy JavaScript modules (11/15):**
- ⏳ `auth.js` - Authentication
- ⏳ `bookings.js` - Booking management
- ⏳ `clients.js` - Client management
- ⏳ `client-detail.js` - Client detail view
- ⏳ `client-bulk-operations.js` - Bulk operations
- ⏳ `csv-upload.js` - CSV upload
- ⏳ `services.js` - Service management
- ⏳ `workplaces.js` - Workplace management
- ⏳ `main.js` - Main application
- ⏳ And others...

**Migration process:**
1. Create TypeScript version in `frontend/src/`
2. Run `npm run build` to compile
3. Update HTML templates to reference compiled `.js` file
4. Test thoroughly
5. Remove old `.js` file from `static/js/`

## Development Workflow

### TypeScript Development
```bash
# Build once
npm run build

# Watch mode (recommended)
npm run watch

# Type check only (no compilation)
npm run type-check
```

### Python Development
```bash
# Install dependencies
poetry install

# Run server
python scripts/start_server.py
# or
./start.sh

# Run tests
pytest

# Populate DB with sample data
python scripts/populate_db.py
```

### Database Migrations
```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## File Naming Conventions

- **Python**: `snake_case.py`
- **TypeScript**: `kebab-case.ts` (compiled to `kebab-case.js`)
- **HTML Templates**: `snake_case.html`
- **CSS**: `kebab-case.css`
- **Tests**: `test_*.py`
- **Migration Scripts**: `migrate_*.py` or descriptive names

## Import Patterns

### TypeScript Imports
```typescript
// Import from types
import type { Specialist, Booking } from './types.js';

// Import utilities
import { validatePhone, formatTime } from './utils.js';
```

### Python Imports
```python
# Relative imports within package
from .models import Specialist, Booking
from .auth import verify_token

# Absolute imports
from calendar_app.database import get_db
```

## Configuration Files

- **tsconfig.json** - TypeScript compiler configuration
  - Source: `frontend/src/`
  - Output: `src/calendar_app/static/js/`
  - Target: ES2020
  - Strict mode enabled

- **pyproject.toml** - Python project configuration
  - Uses Poetry for dependency management
  - pytest configuration
  - Python 3.11+

- **package.json** - Node.js configuration
  - Build scripts for TypeScript
  - Dev dependencies only (no runtime JS)

## Best Practices

1. **Keep root clean** - Only config files and README in root
2. **Documentation in docs/** - All markdown files go here
3. **Data in data/** - Sample files and test data organized
4. **TypeScript in frontend/src/** - Single source of truth for TS
5. **Scripts organized** - Utilities vs. one-off migrations
6. **All tests in tests/** - Easy to run entire test suite
7. **Source maps enabled** - Easy debugging of TypeScript in browser

## Migration from Old Structure

The project was reorganized on November 18, 2025 to improve maintainability:

**Changes made:**
- ✅ Created `frontend/src/` for TypeScript source
- ✅ Moved `typescript/` → `frontend/src/`
- ✅ Created `docs/` for all documentation
- ✅ Created `data/samples/` and `data/test/`
- ✅ Created `scripts/migrations/` for one-off scripts
- ✅ Consolidated tests in `tests/`
- ✅ Removed backup files (`.bak`)
- ✅ Updated `tsconfig.json` paths
- ✅ Cleaned root directory

**Compatibility:**
All existing functionality preserved. TypeScript compilation tested and working.
