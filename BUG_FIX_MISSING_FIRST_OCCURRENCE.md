# Bug Fix: New Availability Blocks Not Appearing

## Issue
After successfully creating a new availability block, the success toast appears but the block doesn't show up on the calendar UI.

## Root Cause
The backend's `generate_recurring_event_instances()` function was **skipping the first occurrence** with this code:

```python
for occurrence_start in occurrences[1:]:  # Skip first occurrence
```

This was based on the assumption that the base event (with `is_recurring=True`) would serve as the first occurrence. However, the frontend's `/calendar-instances` endpoint filters specifically for instances:

```python
CalendarEvent.is_recurring == False,  # Only instances, not base templates
```

**Result:** The first occurrence was never created as an instance, so it never appeared in the UI.

## Example
When creating a Saturday availability on Dec 23, 2025:
- Base event created: Dec 23 (start_date), is_recurring=True
- rrule generates occurrences: [Dec 27, Jan 3, Jan 10, ...]
- Old code: Created instances starting from Jan 3 (skipped Dec 27)
- Dec 27 instance never existed → Block didn't appear

## Solution
Changed the instance generation to create ALL occurrences, including the first one:

```python
# Before
for occurrence_start in occurrences[1:]:  # Skip first occurrence

# After  
for occurrence_start in occurrences:  # Create instances for ALL occurrences
```

**Rationale:**
- The base event is purely a **template** with metadata (recurrence rules, settings)
- The base event itself should NOT be displayed on the calendar
- ALL visible occurrences should be instances with `is_recurring=False`
- This keeps the data model clean and consistent

## Additional Improvements

### 1. Enhanced Logging - Backend
Added logging to track instance creation:

```python
print(f"[get_calendar_instances] Found {len(events)} instances for specialist {specialist_id}")
print(f"[get_calendar_instances] Date range: {start_dt} to {end_dt}")
```

### 2. Enhanced Logging - Frontend
Added detailed logging to diagnose availability loading:

```javascript
console.log('[loadRecurringAvailability] First 3 instances:', instances.slice(0, 3));
console.log('[loadRecurringAvailability] Blocks for current week:', 
    unifiedCalendarData.availability.filter(/* ... */).length);
```

This helps identify:
- How many instances were returned from backend
- Which instances are in the current week view
- Date-to-column conversion issues

## Testing Instructions

1. **Restart the server:**
   ```bash
   python scripts/start_server.py
   ```

2. **Open browser console** (F12 → Console tab)

3. **Create a new availability block:**
   - Drag to select a time slot on any day
   - Choose workplace
   - Click "Create"
   - Watch console for logs

4. **Expected behavior:**
   - Success toast: "✅ Availability blocks created successfully!"
   - Block immediately appears on the calendar
   - No need to refresh the page

5. **Console logs to verify:**
   ```
   [createAvailabilityFromModal] Success for day X: {message: "...", event_id: 123}
   [loadRecurringAvailability] Loaded N calendar instances
   [loadRecurringAvailability] First 3 instances: [{instance_id: 123, date: "2025-12-27", ...}, ...]
   [loadRecurringAvailability] Created N availability blocks
   [loadRecurringAvailability] Blocks for current week: M
   [renderAvailabilityBlocks] Instance date: 2025-12-27 Week start: 2025-12-22 Column: 5
   [renderAvailabilityBlocks] Block added for 2025-12-27 in column 5
   ```

6. **Server logs to verify:**
   ```
   [get_calendar_instances] Found N instances for specialist X
   [get_calendar_instances] Date range: 2025-12-23 00:00:00 to 2027-12-23 23:59:59
   ```

## Impact

### Affected Functionality
- ✅ Creating new recurring schedules
- ✅ Drag-to-create availability blocks  
- ✅ Modal-based schedule creation

### Not Affected
- Existing schedules (already had instances)
- Deleting instances
- Deleting series
- Editing schedules

### Database Impact
**None** - This was purely a logic bug. No schema changes or migrations needed.

However, **existing schedules created before this fix** may be missing their first occurrence. To fix existing data, you could run a one-time script to regenerate instances for all recurring events.

## Data Consistency Check

After the fix, the data model should be:

**Base Template Event:**
```python
{
    "id": 456,
    "is_recurring": True,
    "recurring_event_id": "123_1703345678.123",
    "start_datetime": "2025-12-23 09:00:00",
    # ... other metadata
}
```

**Instance Events (visible on calendar):**
```python
[
    {
        "id": 789,  # instance_id
        "is_recurring": False,
        "recurring_event_id": "123_1703345678.123",
        "start_datetime": "2025-12-27 09:00:00",  # First Saturday
    },
    {
        "id": 790,
        "is_recurring": False,
        "recurring_event_id": "123_1703345678.123",
        "start_datetime": "2026-01-03 09:00:00",  # Second Saturday
    },
    # ... more instances
]
```

**Key Point:** Every visible block has its own `instance_id` and `is_recurring=False`.

## Related Issues Fixed

This fix also resolves:
- Schedules appearing to not save
- "Empty calendar" after creating first schedule
- Inconsistent behavior between days of week

## Files Modified

### Backend
- `src/calendar_app/main.py` (line 357)
  - `generate_recurring_event_instances()`: Removed `[1:]` slice to include first occurrence
  - `get_calendar_instances()`: Added debug logging

### Frontend  
- `src/calendar_app/static/js/unified-calendar.js` (line 220-260)
  - `loadRecurringAvailability()`: Added detailed console logging

## Summary

The "missing first occurrence" bug was caused by an off-by-one error in the instance generation logic. The base template event was intended to be the first occurrence, but the UI only displays instance events, creating a gap. By generating all occurrences as instances, the calendar now displays correctly from the very first occurrence.

This is a critical fix that restores the core functionality of creating new availability schedules.
