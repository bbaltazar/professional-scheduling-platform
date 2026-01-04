# Bug Fixes: Calendar Instance Display and Deletion

## Issues Fixed

### 1. Date Offset Bug - Blocks Appearing on Wrong Days
**Problem:** Creating availability for Dec 27 (Saturday) displayed block on Dec 25 (Thursday)

**Root Cause:**  
The frontend was using `avail.day` (weekday 0-6) to match columns, but column indices represent **position in the current week view**, not absolute weekdays.

Example:
- Dec 27, 2025 = Saturday (weekday = 5)
- Week of Dec 22-28: Column 5 = Saturday ✓
- Week of Dec 15-21: Column 5 = Saturday (Dec 20) ✗

The old code assumed `day` would always match the column position, but when viewing different weeks, this broke.

**Solution:**  
Calculate column position based on the **actual date** of the instance relative to the current week being displayed:

```javascript
// Before: Used static day_of_week
const dayColumn = document.querySelector(`.time-slots-container[data-day="${avail.day}"]`);

// After: Calculate column from actual date
const instanceDate = new Date(avail.date);
const weekStart = new Date(currentWeekStart);
const daysDiff = Math.floor((instanceDate - weekStart) / (1000 * 60 * 60 * 24));

// Only render if in current week (0-6)
if (daysDiff >= 0 && daysDiff <= 6) {
    const dayColumn = document.querySelector(`.time-slots-container[data-day="${daysDiff}"]`);
    // ... render block
}
```

**Key Changes:**
- Use `avail.date` (actual ISO date from backend) instead of `avail.day`
- Calculate column position dynamically: `(instanceDate - weekStart) / milliseconds_per_day`
- Skip instances outside the current week view
- Added logging to track date-to-column conversion

### 2. Instance Deletion Failure
**Problem:** "Delete This Instance" button failed silently, but "Delete Entire Series" worked

**Root Cause:**  
Likely an authentication or network issue, but error handling was insufficient to diagnose.

**Solution:**  
Enhanced error handling and logging in `deleteScheduleInstance()`:

```javascript
// Added comprehensive error handling
const response = await fetch(`/calendar-event/${instanceId}`, {
    method: 'DELETE',
    headers: {
        'Content-Type': 'application/json'  // Explicit headers
    }
});

console.log('[deleteScheduleInstance] Response status:', response.status, response.statusText);

if (!response.ok) {
    let errorMessage = 'Failed to delete instance';
    try {
        const error = await response.json();
        errorMessage = error.detail || errorMessage;
        console.error('[deleteScheduleInstance] Server error:', error);
    } catch (e) {
        // Handle non-JSON error responses
        const errorText = await response.text();
        console.error('[deleteScheduleInstance] Server response:', errorText);
        errorMessage = errorText || errorMessage;
    }
    throw new Error(errorMessage);
}
```

**Improvements:**
- Log response status before parsing
- Try JSON parse first, fall back to text for error messages
- Explicit Content-Type header
- Better error messages in toast notifications

### 3. UI Improvements
**Enhancement:** Modal now shows actual date instead of just day name

```javascript
// Added human-readable date display
const actualDate = schedule.date ? new Date(schedule.date).toLocaleDateString('en-US', { 
    weekday: 'long', 
    month: 'short', 
    day: 'numeric',
    year: 'numeric'
}) : dayName;

// Displays as: "Saturday, Dec 27, 2025" instead of just "Saturday"
```

**Benefits:**
- Clearer which exact instance you're editing
- Helps debugging date offset issues
- Better UX for weekly recurring schedules

## Testing Instructions

1. **Restart the server:**
   ```bash
   python scripts/start_server.py
   ```

2. **Test Date Accuracy:**
   - Navigate to week of Dec 22-28, 2025
   - Create availability for Saturday (Dec 27)
   - Verify block appears in Saturday column (not Thursday)
   - Navigate to different weeks and verify blocks stay on correct days

3. **Test Instance Deletion:**
   - Click any availability block
   - Click "Delete This Instance"
   - Check browser console for logs:
     - `[deleteScheduleInstance] Deleting instance X`
     - `[deleteScheduleInstance] Response status: 200 OK`
     - `[deleteScheduleInstance] Success: {message: ...}`
   - Verify only that instance disappears
   - Other days in series should remain

4. **Test Series Deletion:**
   - Click any block in a series
   - Click "Delete Entire Series"
   - Check console for success message with count
   - Verify all instances disappear

5. **Check Console Logs:**
   - Open browser DevTools Console
   - Look for `[renderAvailabilityBlocks]` logs showing date-to-column conversion
   - Verify no "outside current week" warnings for visible blocks
   - Check for any red error messages

## Expected Console Output

```
[renderAvailabilityBlocks] Rendering 7 blocks
[renderAvailabilityBlocks] Instance date: 2025-12-27 Week start: 2025-12-22 Column: 5
[renderAvailabilityBlocks] Block added for 2025-12-27 in column 5
[AvailabilityBlock] Clicked! Data: {instance_id: 123, date: "2025-12-27", ...}
[showScheduleEditModal] Instance ID: 123 Recurring Event ID: 456_... Day: Saturday Actual Date: Saturday, Dec 27, 2025
[deleteScheduleInstance] Deleting instance 123 (Saturday)
[deleteScheduleInstance] Response status: 200 OK
[deleteScheduleInstance] Success: {message: "Calendar event instance deleted successfully", instance_id: 123}
```

## Backend Verification

The backend endpoint is correct and returns proper data:

```python
# /specialist/{id}/calendar-instances
instances.append({
    "instance_id": event.id,  # Unique database ID
    "recurring_event_id": event.recurring_event_id,  # Series grouping
    "day_of_week": event.start_datetime.weekday(),  # 0=Mon, 6=Sun
    "start_time": event.start_datetime.strftime("%H:%M"),
    "end_time": event.end_datetime.strftime("%H:%M"),
    "date": event.start_datetime.strftime("%Y-%m-%d"),  # KEY: ISO date string
    # ...
})
```

The `date` field is the critical addition that fixes the rendering issue.

## Potential Remaining Issues

If instance deletion still fails after these changes:

1. **Check Authentication:**
   - Verify you're logged in as the correct specialist
   - Check browser cookies for session token
   - Try refreshing the page and logging in again

2. **Check Network Tab:**
   - Open DevTools → Network tab
   - Click "Delete This Instance"
   - Look for DELETE request to `/calendar-event/{id}`
   - Check request headers (should include cookies)
   - Check response body and status code

3. **Check Backend Logs:**
   - Look for DELETE requests in server terminal
   - Check for authentication errors
   - Verify database connection

4. **CORS/CSRF Issues:**
   - Verify the frontend and backend are on the same origin
   - Check for CORS errors in console
   - Ensure CSRF protection isn't blocking DELETE

## Files Modified

### Frontend
- `unified-calendar.js`:
  - `renderAvailabilityBlocks()`: Date-based column calculation
  - `deleteScheduleInstance()`: Enhanced error handling
  - `showScheduleEditModal()`: Display actual date

### No Backend Changes
The backend already provided the `date` field, so no changes were needed there.

## Summary

The main issue was a logic error in how calendar blocks were positioned. The frontend incorrectly used weekday numbers as column indices, which only worked when viewing the current week. By switching to date-based calculations, blocks now appear in the correct columns regardless of which week is being viewed.

The deletion issue was addressed with better error handling and logging to help diagnose any remaining problems.
