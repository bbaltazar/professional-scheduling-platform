# Instance-Based Calendar Architecture

## Overview
Implemented a new instance-aware architecture for calendar event management that allows direct manipulation of individual calendar instances using their database IDs, eliminating the need for complex day_of_week calculations.

## Architecture Changes

### Previous System
- Frontend stored only `schedule_id` (base template ID)
- Deletion required both `event_id` AND `day_of_week` parameter
- Complex logic to remove days from recurrence rules
- No direct access to individual occurrences

### New System
- Each calendar block stores its own `instance_id` (unique database ID)
- Direct deletion: `DELETE /calendar-event/{instance_id}`
- Series deletion: `DELETE /calendar-event/series/{recurring_event_id}`
- Simplified frontend logic with explicit instance tracking

## Database Schema

### Existing Structure (No Changes Needed!)
```python
class CalendarEvent:
    id = Column(Integer, primary_key=True)  # Instance ID
    recurring_event_id = Column(String)     # Series ID (groups related instances)
    is_recurring = Column(Boolean)          # True = template, False = instance
    # ... other fields
```

**Key Points:**
- `id`: Unique identifier for EACH occurrence (instance_id)
- `recurring_event_id`: Groups all instances of a recurring series (series_id)
- Base template has `is_recurring=True`
- Individual instances have `is_recurring=False`

## Backend Changes

### New Endpoints

#### 1. GET /specialist/{specialist_id}/calendar-instances
Returns individual calendar instances (not just base templates).

**Response Format:**
```json
[
  {
    "instance_id": 123,           // Unique ID for this specific occurrence
    "recurring_event_id": "456_1234567890.123",  // Series ID
    "base_event_id": 456,         // ID of the template event
    "day_of_week": 1,             // 0=Monday, 6=Sunday
    "start_time": "09:00",
    "end_time": "17:00",
    "date": "2025-12-24",         // Actual date of this instance
    "workplace_id": 789,
    "workplace": { "id": 789, "name": "Main Office" },
    "recurrence_type": "weekly"
  }
]
```

**Key Features:**
- Returns actual instances from database (not generated on-the-fly)
- Each instance has its own unique `instance_id`
- Includes both series ID and base template ID
- Date range defaults to 2 years from start date

#### 2. DELETE /calendar-event/{instance_id}
Deletes a specific calendar instance by its database ID.

**Usage:**
```javascript
DELETE /calendar-event/123
```

**Response:**
```json
{
  "message": "Calendar event instance deleted successfully",
  "instance_id": 123,
  "recurring_event_id": "456_1234567890.123"
}
```

**Behavior:**
- Soft deletes (sets `is_active=False`)
- Only affects the specific instance
- Other instances in the series remain active

#### 3. DELETE /calendar-event/series/{recurring_event_id}
Deletes ALL events in a recurring series.

**Usage:**
```javascript
DELETE /calendar-event/series/456_1234567890.123
```

**Response:**
```json
{
  "message": "Deleted 42 events in the recurring series",
  "recurring_event_id": "456_1234567890.123",
  "deleted_count": 42
}
```

**Behavior:**
- Soft deletes all instances AND the base template
- Includes count of deleted events
- Verifies user ownership before deletion

## Frontend Changes

### Data Structure Update

**Old Structure:**
```javascript
{
  day: 1,
  start_time: "09:00",
  end_time: "17:00",
  schedule_id: 456,  // Only base template ID
  recurrence_type: "weekly"
}
```

**New Structure:**
```javascript
{
  day: 1,
  start_time: "09:00",
  end_time: "17:00",
  instance_id: 123,                        // NEW: Unique instance ID
  recurring_event_id: "456_1234567890.123", // NEW: Series ID
  base_event_id: 456,                       // NEW: Template ID
  date: "2025-12-24",                       // NEW: Actual date
  workplace_id: 789,
  workplace_name: "Main Office",
  recurrence_type: "weekly"
}
```

### Updated Functions

#### loadRecurringAvailability()
```javascript
// OLD: Called /specialist/{id}/recurring-schedules (returns templates)
// NEW: Calls /specialist/{id}/calendar-instances (returns instances)

async function loadRecurringAvailability() {
    const response = await fetch(`/specialist/${window.currentSpecialistId}/calendar-instances`);
    const instances = await response.json();
    
    // Each instance now has its own ID
    unifiedCalendarData.availability = instances.map(instance => ({
        instance_id: instance.instance_id,  // Direct database ID
        recurring_event_id: instance.recurring_event_id,
        // ... other fields
    }));
}
```

#### deleteScheduleInstance()
```javascript
// Simplified - just needs the instance ID
async function deleteScheduleInstance(instanceId, dayName) {
    const response = await fetch(`/calendar-event/${instanceId}`, {
        method: 'DELETE'
    });
    // No need to calculate or send day_of_week!
}
```

#### deleteScheduleSeries()
```javascript
// Simplified - just needs the series ID
async function deleteScheduleSeries(recurringEventId) {
    const response = await fetch(`/calendar-event/series/${recurringEventId}`, {
        method: 'DELETE'
    });
    // Deletes all instances in one call
}
```

#### showScheduleEditModal()
```javascript
// Updated to use instance_id and recurring_event_id
function showScheduleEditModal(schedule) {
    const instanceId = schedule.instance_id;
    const recurringEventId = schedule.recurring_event_id;
    
    // Buttons now call new functions with IDs
    modal.innerHTML = `
        <button onclick="deleteScheduleInstance(${instanceId}, '${dayName}')">
            Delete This Day
        </button>
        <button onclick="deleteScheduleSeries('${recurringEventId}')">
            Delete Entire Series
        </button>
    `;
}
```

## Benefits

### 1. **Simplicity**
- No more complex day_of_week calculations
- Direct ID-based operations
- Clear intent in API calls

### 2. **Reliability**
- Each block has a unique database ID
- No ambiguity about which instance to delete
- Eliminates race conditions

### 3. **Scalability**
- Easy to add more instance-specific operations
- Can track edits/modifications per instance
- Supports future features (e.g., single-instance time changes)

### 4. **Maintainability**
- Clear separation: instance operations vs. series operations
- Consistent API patterns
- Easier to debug with explicit IDs

## Migration Notes

### Backward Compatibility
Legacy functions are maintained with warnings:
```javascript
// Old function redirects to new implementation
async function deleteSchedule(scheduleId, dayOfWeek, dayName) {
    console.warn('[deleteSchedule] Legacy function called');
    await deleteScheduleInstance(scheduleId, dayName);
}
```

### No Database Changes Required
The existing `CalendarEvent` table already has all necessary fields:
- `id` serves as `instance_id`
- `recurring_event_id` serves as `series_id`
- No migration script needed!

## Testing Checklist

1. **Create Schedule**
   - [ ] Create weekly schedule with multiple days
   - [ ] Verify each day appears as separate block
   - [ ] Check console logs for instance_id values

2. **Delete Single Instance**
   - [ ] Click a schedule block
   - [ ] Click "Delete [Day] Only"
   - [ ] Verify only that instance disappears
   - [ ] Confirm other days remain

3. **Delete Series**
   - [ ] Click any schedule block in a series
   - [ ] Click "Delete Entire Series"
   - [ ] Verify all instances disappear
   - [ ] Check deleted_count in response

4. **Daily Schedules**
   - [ ] Create daily schedule (all 7 days)
   - [ ] Verify "Delete This Day" button NOT shown
   - [ ] Delete series removes all 7 instances

5. **Multiple Workplaces**
   - [ ] Create schedules for different workplaces
   - [ ] Verify each has unique instance_id
   - [ ] Delete from one workplace doesn't affect others

## Future Enhancements

### 1. Instance-Level Updates
Add `PUT /calendar-event/{instance_id}` to update individual occurrences:
```javascript
// Update just this Tuesday's hours
PUT /calendar-event/123
{
  "start_time": "10:00",
  "end_time": "18:00"
}
```

### 2. Exception Tracking
Link to `EventException` table for modified instances:
```python
class EventException:
    event_id = Column(Integer, ForeignKey("calendar_events.id"))
    exception_type = Column(String)  # 'modified', 'cancelled'
    new_start_datetime = Column(DateTime)
```

### 3. Bulk Operations
Add endpoint for bulk instance operations:
```javascript
DELETE /calendar-events/bulk
{
  "instance_ids": [123, 456, 789]
}
```

### 4. Instance History
Track changes to individual instances:
```python
class InstanceHistory:
    instance_id = Column(Integer)
    change_type = Column(String)
    old_value = Column(JSON)
    new_value = Column(JSON)
    changed_at = Column(DateTime)
```

## Code Locations

### Backend Files
- **main.py** (lines 1770-1900): New endpoints
  - `GET /specialist/{id}/calendar-instances`
  - `DELETE /calendar-event/{instance_id}`
  - `DELETE /calendar-event/series/{recurring_event_id}`

### Frontend Files
- **unified-calendar.js** (lines 220-260): `loadRecurringAvailability()`
- **unified-calendar.js** (lines 1909-2010): `showScheduleEditModal()`
- **unified-calendar.js** (lines 2020-2130): New delete/update functions

## Summary

This architecture change provides a cleaner, more maintainable approach to calendar instance management by leveraging the database IDs that already exist. No schema changes required, just smarter use of existing data structures!

**Key Takeaway:** Each visual block on the calendar now maps directly to a database row with a unique ID, making operations explicit and straightforward.
