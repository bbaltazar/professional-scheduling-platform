# Folder Structure Reorganization

## What Changed

The project has been reorganized from a flat structure to a proper Python project layout:

### Before
```
src/calendar_app/
├── main.py
├── database.py
├── models.py
├── auth.py
├── config.py
├── verification_service.py
├── templates/
├── static/
├── test_*.py (6 files)        # ❌ Tests mixed with source
├── populate_db.py             # ❌ Utilities mixed with source
├── start_server.py            # ❌ Utilities mixed with source
└── *.db (3 files)             # ❌ Databases in source directory
```

### After
```
calendar_app/                   # Project root
├── src/
│   └── calendar_app/          # ✅ Clean application code
│       ├── main.py
│       ├── database.py
│       ├── models.py
│       ├── auth.py
│       ├── config.py
│       ├── verification_service.py
│       ├── templates/
│       └── static/
├── tests/                     # ✅ All tests organized
│   ├── test_api.py
│   ├── test_booking_integration.py
│   ├── test_consumer.py
│   ├── test_frontend_integration.py
│   ├── test_persistence.py
│   └── test_services_management.py
├── scripts/                   # ✅ Utility scripts separated
│   ├── populate_db.py
│   └── start_server.py
└── *.db (3 files)            # ✅ Databases at project root
```

## Import Changes

All test files and scripts have been updated to use the new package structure:

### Before
```python
from main import app, get_db
from database import Base, Specialist
```

### After
```python
from src.calendar_app.main import app, get_db
from src.calendar_app.database import Base, Specialist
```

## Running the Application

### Start the server
```bash
# From project root
poetry run uvicorn src.calendar_app.main:app --reload --host 0.0.0.0 --port 8000

# Or use the helper script
poetry run python scripts/start_server.py
```

### Run tests
```bash
# Run all tests
poetry run pytest tests/

# Run specific test file
poetry run pytest tests/test_booking_integration.py

# Run with coverage
poetry run pytest tests/ --cov=src.calendar_app
```

### Populate database with test data
```bash
poetry run python scripts/populate_db.py
```

## Test Results

After reorganization:
- ✅ **11 tests passed** - All TestClient-based tests work perfectly
- ⚠️ **2 tests require server** - `test_api.py` and `test_consumer.py` need a running server at port 8001
- ✅ **Import paths updated** - All tests properly import from `src.calendar_app`
- ✅ **No breaking changes** - Application functionality unchanged

## Benefits

1. **Cleaner Structure**: Source code separated from tests and utilities
2. **Standard Layout**: Follows Python best practices for project organization
3. **Easier Navigation**: Clear separation of concerns
4. **Better Testing**: Tests isolated in their own directory
5. **Professional**: Standard structure recognized by IDEs and tools

## Notes

- Database files (`*.db`) are kept at project root for easy access
- The `__pycache__` directories are gitignored
- All import paths have been automatically updated
- No code functionality was changed, only file locations

## Migration Steps Taken

1. ✅ Moved all `test_*.py` files to `tests/` directory
2. ✅ Created `scripts/` directory for utility scripts
3. ✅ Moved `populate_db.py` and `start_server.py` to `scripts/`
4. ✅ Moved database files to project root
5. ✅ Updated all import statements in test files
6. ✅ Updated imports in `start_server.py`
7. ✅ Ran full test suite to verify (11/13 tests passing, 2 need server)
8. ✅ Created comprehensive README.md
9. ✅ Created this migration guide

## Verification

To verify everything works:

```bash
# 1. Check structure
ls -la src/calendar_app/
ls -la tests/
ls -la scripts/

# 2. Run tests
poetry run pytest tests/ -v

# 3. Start server
poetry run uvicorn src.calendar_app.main:app --reload --port 8000

# 4. Visit http://localhost:8000/professional
```
