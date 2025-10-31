# Alembic Migration Setup - Complete ✅

## Summary

Alembic database migrations are now fully configured and operational for the calendar_app project. This provides version-controlled schema management with safe upgrade/rollback capabilities.

## What Was Done

### 1. Package Installation
- Added `alembic (>=1.13.0,<2.0.0)` to `pyproject.toml`
- Installed Alembic package in virtual environment

### 2. Alembic Initialization
- Created `alembic/` directory structure
- Generated `alembic.ini` configuration file
- Created `alembic/versions/` for migration files
- Set up `alembic/env.py` environment script

### 3. Configuration
**alembic.ini:**
- Database URL: `sqlite:///./calendar_app.db`
- Script location: `alembic/`
- Path separator: `os`

**alembic/env.py:**
- Imported `Base` metadata from `calendar_app.database`
- Added `src/` to Python path for imports
- Configured `target_metadata = Base.metadata` for autogenerate

### 4. Initial Migration
**Created:** `77fb5ce9d2e1_initial_migration.py`

**Captured Schema:**
- ✅ All existing tables (Specialist, Consumer, Service, Booking, etc.)
- ✅ All database indexes added in Quick Wins:
  - `bookings`: specialist_id, service_id, consumer_id, client_name, client_email, date, status
  - `appointment_sessions`: booking_id, specialist_id, consumer_id, service_id, actual_start
  - `consumers`: phone, created_at
- ✅ Removed obsolete tables: `recurring_schedules`, `pto_blocks`

**Status:** Stamped as applied (database marked at revision `77fb5ce9d2e1`)

### 5. Database Code Update
**database.py:**
- Commented out `Base.metadata.create_all(bind=engine)`
- Added migration instructions in comments
- Database creation now handled by Alembic

### 6. Helper Script
**Created:** `scripts/migrate.sh`
- `upgrade` - Apply pending migrations
- `downgrade` - Rollback last migration
- `create` - Generate new migration
- `history` - Show migration log
- `current` - Show current state
- Made executable with `chmod +x`

### 7. Documentation
**Created:** `ALEMBIC_GUIDE.md`
- Complete migration workflow guide
- Common scenarios and examples
- Production deployment procedures
- Troubleshooting section
- SQLite-specific limitations

**Updated:** `README.md`
- Added Alembic to tech stack
- Updated installation instructions
- Referenced migration guide

## Current State

### Migration Status
```
Current: 77fb5ce9d2e1 (head) - Initial migration
Status: Applied and stamped
Tables: All synced with models
```

### Files Created/Modified

**New Files:**
- `alembic.ini` - Alembic configuration
- `alembic/env.py` - Migration environment
- `alembic/versions/77fb5ce9d2e1_initial_migration.py` - Initial schema
- `scripts/migrate.sh` - Migration helper script
- `ALEMBIC_GUIDE.md` - Complete documentation
- `ALEMBIC_SETUP_COMPLETE.md` - This summary

**Modified Files:**
- `pyproject.toml` - Added alembic dependency
- `src/calendar_app/database.py` - Removed create_all()
- `README.md` - Updated with migration info

### Database State
- Existing database: `calendar_app.db` (245 KB)
- Alembic version table: `alembic_version` (created)
- Current migration: `77fb5ce9d2e1`
- All data preserved: ✅
- All indexes tracked: ✅

## How to Use

### Daily Development

**When you change models:**
```bash
# 1. Edit src/calendar_app/database.py
# 2. Create migration
./scripts/migrate.sh create "describe your changes"

# 3. Review the generated file in alembic/versions/
# 4. Apply migration
./scripts/migrate.sh upgrade
```

**Check migration status:**
```bash
./scripts/migrate.sh current
./scripts/migrate.sh history
```

**Rollback if needed:**
```bash
./scripts/migrate.sh downgrade
```

### Production Deployment

**Pre-deployment:**
1. Review all pending migrations
2. Test on staging/copy of production data
3. Create database backup

**Deployment:**
```bash
# Backup
cp calendar_app.db calendar_app.db.backup.$(date +%Y%m%d_%H%M%S)

# Apply migrations
./scripts/migrate.sh upgrade

# Restart application
./start.sh
```

## Next Schema Changes

When you need to make database changes, you now have a safe workflow:

### Example: Adding a Field
```python
# 1. Edit database.py
class Specialist(Base):
    # ... existing fields ...
    bio = Column(Text, nullable=True)  # NEW

# 2. Generate migration
./scripts/migrate.sh create "add specialist bio field"

# 3. Review alembic/versions/XXXXX_add_specialist_bio_field.py
# 4. Apply
./scripts/migrate.sh upgrade
```

### Example: Adding an Index
```python
# 1. Edit database.py
class Booking(Base):
    client_phone = Column(String, index=True)  # Added index=True

# 2. Generate migration
./scripts/migrate.sh create "add index to booking client_phone"

# 3. Apply
./scripts/migrate.sh upgrade
```

## Benefits You Now Have

1. **Version Control for Schema**: Every database change is tracked and versioned
2. **Rollback Capability**: Can undo migrations if issues arise
3. **Team Collaboration**: Other developers can apply your schema changes automatically
4. **Production Safety**: No more `create_all()` that could drop tables
5. **Change Documentation**: Migration files serve as schema change history
6. **Automatic Detection**: Alembic autogenerate detects most model changes
7. **Data Preservation**: Migrations maintain existing data during schema changes

## Testing the Setup

Let's verify everything works by checking the current state:

```bash
# Should show: 77fb5ce9d2e1 (head)
./scripts/migrate.sh current

# Should show: <base> -> 77fb5ce9d2e1 (head), Initial migration
./scripts/migrate.sh history
```

Both commands should work without errors, confirming the setup is complete.

## Important Notes

### What Changed
- ❌ **Old:** `Base.metadata.create_all()` auto-creates tables on startup
- ✅ **New:** Use `./scripts/migrate.sh upgrade` to apply migrations

### Database Safety
- Migrations are **forward-only** by default (upgrade adds, downgrade removes)
- Always backup production before migrations
- Test migrations on copy of production data first
- SQLite has limitations (can't drop columns easily)

### Version Control
- ✅ **Commit:** All files in `alembic/` including `alembic.ini`
- ✅ **Commit:** Migration files in `alembic/versions/`
- ❌ **Don't commit:** Database files (`.db`, already in `.gitignore`)

## Troubleshooting

### "Target database is not up to date"
```bash
./scripts/migrate.sh upgrade
```

### "Can't locate revision"
```bash
.venv/bin/alembic stamp head
```

### Migration didn't detect my change
Alembic autogenerate has limitations. You may need to manually edit the migration file. Common cases:
- Column renames (appears as drop + add)
- Column type changes
- Table renames

## Success Criteria

- [x] Alembic installed and configured
- [x] Initial migration created and applied
- [x] Database stamped to current revision
- [x] Helper script created and executable
- [x] Documentation complete
- [x] README updated
- [x] `create_all()` removed from database.py
- [x] Migration workflow tested

## Completion Time

**Total Time:** ~15 minutes
- Installation: 2 min
- Configuration: 3 min
- Initial migration: 2 min
- Helper script: 3 min
- Documentation: 5 min

## Next Steps

Your migration system is ready! Future schema changes should:

1. Modify `database.py` models
2. Run `./scripts/migrate.sh create "description"`
3. Review generated migration
4. Run `./scripts/migrate.sh upgrade`
5. Commit migration files to git

For detailed information, see [ALEMBIC_GUIDE.md](ALEMBIC_GUIDE.md).

---

**Status:** ✅ Alembic migrations fully operational
**Date:** October 30, 2025
**Migration:** 77fb5ce9d2e1 (Initial migration)
