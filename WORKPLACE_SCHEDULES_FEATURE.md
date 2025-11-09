# Workplace-Linked Recurring Schedules Feature

## Overview
This feature allows professionals to associate their recurring schedules with specific workplaces, enabling:
- Schedule management across multiple locations (up to 2 workplaces + "Personal")
- Storefront view for workplaces to see all employee schedules aggregated
- Better organization and context for professional availability

## Implementation Summary

### 1. Database Changes ✅

**File: `src/calendar_app/database.py`**
- Added `workplace_id` column to `CalendarEvent` model (nullable foreign key to `workplaces` table)
- Added relationship: `workplace = relationship("Workplace")`
- Migration created: `4976b5d06d1e_add_workplace_id_to_calendar_events.py`

**Migration Applied:**
```bash
poetry run alembic upgrade head
```

### 2. Backend API Updates ✅

**File: `src/calendar_app/main.py`**

#### Updated `RecurringScheduleCreate` model:
```python
workplace_id: Optional[int] = None  # None = "Personal", or ID of workplace
```

#### Updated `POST /specialist/{specialist_id}/recurring-schedule`:
- Validates that `workplace_id` belongs to the specialist's associated workplaces
- Includes workplace name in schedule title and description
- Returns `workplace_id` and `workplace_label` in response

#### Updated `GET /specialist/{specialist_id}/recurring-schedules`:
- Includes full workplace information in response:
  ```json
  {
    "workplace_id": 123,
    "workplace": {
      "id": 123,
      "name": "Downtown Salon",
      "address": "123 Main St",
      "city": "San Francisco"
    }
  }
  ```

#### New Endpoint - `GET /workplaces/{workplace_id}/schedules`:
**Purpose:** Storefront view - aggregates all employee schedules for a workplace

**Query Parameters:**
- `start_date` (optional): Filter from date (YYYY-MM-DD)
- `end_date` (optional): Filter to date (YYYY-MM-DD)

**Response:**
```json
{
  "workplace_id": 123,
  "workplace_name": "Downtown Salon",
  "workplace_address": "123 Main St, San Francisco",
  "total_specialists": 5,
  "specialists_with_schedules": 3,
  "schedules": [
    {
      "specialist_id": 1,
      "specialist_name": "Jane Doe",
      "specialist_email": "jane@example.com",
      "schedules": [
        {
          "id": 456,
          "title": "Weekly Availability at Downtown Salon",
          "recurrence_type": "weekly",
          "days_of_week": [0, 1, 2, 3, 4],
          "start_time": "09:00",
          "end_time": "17:00",
          "start_date": "2025-01-01",
          "end_date": "2025-12-31"
        }
      ]
    }
  ]
}
```

### 3. Frontend Updates ✅

**File: `src/calendar_app/templates/professional.html`**
- Added workplace dropdown selector before date inputs:
  ```html
  <select id="recurringWorkplaceId">
    <option value="">Personal</option>
    <!-- Dynamically populated with workplaces -->
  </select>
  ```

**File: `src/calendar_app/static/js/schedule.js`**

#### New Function - `loadWorkplacesForSchedule()`:
```javascript
// Loads specialist's workplaces into dropdown
// Automatically called when switching to schedule tab
```

#### Updated `saveWeeklySchedule()`:
```javascript
// Now includes workplace_id in schedule data:
workplace_id: workplaceId ? parseInt(workplaceId) : null
```

#### Updated `displayRecurringSchedules()`:
```javascript
// Shows workplace badge with icon:
// 📍 Downtown Salon - San Francisco
// 🏠 Personal
```

**File: `src/calendar_app/static/js/navigation.js`**
- Calls `loadWorkplacesForSchedule()` when schedule tab is opened

**File: `src/calendar_app/static/js/main.js`**
- Exposed `window.loadWorkplacesForSchedule` for tab switching

## Usage Guide

### For Professionals

#### Creating a Schedule:
1. Navigate to **Schedule** tab
2. Use the visual calendar to drag and create time blocks
3. Select location from **📍 Location** dropdown:
   - "Personal" (default) - not linked to any workplace
   - Or select one of your associated workplaces
4. Set effective start date (required)
5. Optionally set end date
6. Click **💾 Save Weekly Schedule**

#### Viewing Schedules:
- All schedules show location badge
- 🏠 Personal schedules
- 📍 Workplace schedules (with workplace name and city)

### For Workplaces

#### Viewing Employee Schedules (Storefront View):
```
GET /workplaces/{workplace_id}/schedules
```

**Example:**
```bash
curl -X GET "http://localhost:8000/workplaces/123/schedules?start_date=2025-01-01&end_date=2025-12-31"
```

This returns all schedules from all professionals associated with workplace ID 123.

## Data Model

```
CalendarEvent
├── id (primary key)
├── specialist_id (foreign key → specialists)
├── workplace_id (foreign key → workplaces) ← NEW
├── title
├── description
├── start_datetime
├── end_datetime
├── is_recurring
├── recurrence_rule (JSON)
└── ... other fields
```

## Validation Rules

1. **Workplace Association**: 
   - `workplace_id` must be `null` (Personal) OR
   - Must belong to a workplace where `specialist_id` is an active member

2. **Professional Limits**:
   - Can have multiple "Personal" schedules
   - Can have schedules at multiple workplaces (no limit enforced at DB level)
   - Recommended: Up to 2 workplaces + Personal

## API Summary

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/specialist/{id}/recurring-schedule` | POST | Create schedule (with optional `workplace_id`) |
| `/specialist/{id}/recurring-schedules` | GET | List specialist's schedules (includes workplace info) |
| `/specialist/{id}/recurring-schedule/{schedule_id}` | DELETE | Delete a schedule |
| `/workplaces/{id}/schedules` | GET | **NEW** - Storefront view of all employee schedules |

## Testing Checklist

- [ ] Create a "Personal" schedule (workplace_id=null)
  - Verify it shows "🏠 Personal" badge
  - Verify it's saved correctly
  
- [ ] Associate professional with a workplace
  - Create schedule with that workplace
  - Verify workplace name appears in dropdown
  - Verify it shows "📍 [Workplace Name]" badge

- [ ] Try to create schedule for unassociated workplace
  - Should return 403 error

- [ ] View storefront schedule
  - GET `/workplaces/{id}/schedules`
  - Verify all employee schedules appear
  - Verify filtering by dates works

- [ ] Update existing personal schedules
  - Verify they still work after migration

## Future Enhancements

1. **Calendar Integration**: Export workplace schedules to iCal/Google Calendar
2. **Conflict Detection**: Warn if scheduling conflicts exist across workplaces
3. **Bulk Operations**: Copy schedule from one workplace to another
4. **Analytics**: Track utilization rates per workplace
5. **Public Storefront**: Consumer-facing view of workplace availability

## Files Modified

### Backend
- `src/calendar_app/database.py` - Added `workplace_id` column and relationship
- `src/calendar_app/main.py` - Updated APIs and added storefront endpoint

### Frontend
- `src/calendar_app/templates/professional.html` - Added workplace dropdown
- `src/calendar_app/static/js/schedule.js` - Load workplaces, save/display logic
- `src/calendar_app/static/js/navigation.js` - Call loadWorkplacesForSchedule on tab switch
- `src/calendar_app/static/js/main.js` - Expose loadWorkplacesForSchedule to window

### Database
- `alembic/versions/4976b5d06d1e_add_workplace_id_to_calendar_events.py` - Migration

## Notes

- SQLite batch mode used for migration (required for foreign key constraints)
- Workplace selection is optional - defaults to "Personal"
- Existing schedules remain unaffected (workplace_id is NULL)
- Workplace dropdown dynamically loads from `/specialists/{id}/workplaces` endpoint

---

**Status**: ✅ Implementation Complete  
**Migration Applied**: ✅ Yes  
**Ready for Testing**: ✅ Yes
