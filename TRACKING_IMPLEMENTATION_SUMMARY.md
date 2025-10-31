# Appointment Duration Tracking - Implementation Summary

## What Was Built

A comprehensive appointment duration tracking system that records actual appointment times and provides data-driven insights to professionals about how long appointments really take with different clients and services.

## Changes Made

### 1. Database Schema (`database.py`)
**New Table: `AppointmentSession`**
- Tracks scheduled vs actual appointment times
- Records start/end times, duration, and metadata
- Links to bookings, specialists, consumers, and services
- Includes analytics flags (early/late/overtime)

### 2. API Models (`models.py`)
**New Pydantic Models:**
- `AppointmentSessionCreate` - Start tracking a session
- `AppointmentSessionUpdate` - Complete a session
- `AppointmentSessionResponse` - Session data response
- `ClientDurationInsight` - Analytics for specific clients
- `ServiceDurationInsight` - Analytics for services
- `DurationRecommendation` - Smart duration suggestions

### 3. API Endpoints (`main.py`)
**New Endpoints:**

1. **POST** `/specialist/{id}/appointment-session/start`
   - Starts tracking when appointment begins
   - Records actual start time
   - Detects early/late starts

2. **PATCH** `/specialist/{id}/appointment-session/{session_id}/complete`
   - Records when appointment ends
   - Calculates actual duration
   - Updates booking to "completed" status
   - Detects overtime

3. **GET** `/specialist/{id}/appointment-sessions`
   - Lists all completed sessions
   - Filterable by client, service
   - For historical analysis

4. **GET** `/specialist/{id}/client/{consumer_id}/duration-insights`
   - Returns comprehensive client statistics
   - Average, median, min, max durations
   - Consistency score (how predictable)
   - Typical overtime amount

5. **GET** `/specialist/{id}/duration-recommendation`
   - Smart recommendation for booking duration
   - Combines client + service history
   - Provides confidence level
   - Shows basis for recommendation

### 4. Documentation
- `APPOINTMENT_TRACKING.md` - Complete feature documentation
- `migrate_appointment_sessions.py` - Database migration script

## How It Works

### Workflow:

```
1. Professional creates booking (existing flow)
   ↓
2. On appointment day, professional clicks "Start Appointment"
   → Creates AppointmentSession with actual_start time
   ↓
3. Professional performs service
   ↓
4. Professional clicks "Complete Appointment"
   → Records actual_end time
   → Calculates actual_duration
   → Marks booking as completed
   ↓
5. System uses this data for future recommendations
```

### Intelligence:

When professional books next appointment with same client:
```
System checks:
1. Does this client have ≥3 previous appointments?
   YES → Recommend client's average duration (HIGH confidence)
   NO → Continue to step 2

2. Does this service have ≥5 appointments across all clients?
   YES → Recommend service average (MEDIUM confidence)
   NO → Use service default duration (LOW confidence)
```

### Example Scenario:

**Client: John Smith**
- Service: Haircut (default 60 min)
- Previous appointments: 8 sessions
- Average actual duration: 72 minutes
- Consistency: 90% (very predictable)
- Typical overtime: +12 minutes

**When booking John's next haircut:**
```
Recommendation: 72 minutes
Confidence: HIGH
Basis: "Based on 8 previous appointments with this client"

Professional sees:
- "John typically takes 72 minutes"
- "Service average: 65 minutes"
- "Consistency: 90% (Very predictable)"

Professional can:
- Accept recommendation (72 min)
- Adjust manually
- View detailed history
```

## Data Tracked

### Per Session:
- Scheduled start/end times
- Actual start/end times  
- Scheduled vs actual duration
- Was client early/late?
- Did appointment go overtime?
- Session notes

### Analytics Provided:
- **Client Level**: Average, median, range, consistency, typical overtime
- **Service Level**: Average duration, variance from scheduled
- **Recommendations**: Smart suggestions with confidence levels

## Benefits

### For Professionals:
1. **Accurate Scheduling** - Stop guessing, use real data
2. **Better Time Management** - Know which clients need more time
3. **Reduced Conflicts** - Prevent double-booking from underestimating
4. **Client Insights** - Understand each client's needs

### For Clients:
1. **Better Estimates** - More accurate appointment times
2. **Less Waiting** - Professionals schedule more realistically
3. **Consistency** - Reliable service timing

## Next Steps to Use

### 1. Run Migration
```bash
cd /Users/brianabaltazar/SoftwareEngineering/apps/calendar_app
python migrate_appointment_sessions.py
```

### 2. Test API (Optional)
```bash
# Start a session
curl -X POST http://localhost:8000/specialist/1/appointment-session/start \
  -H "Content-Type: application/json" \
  -d '{"booking_id": 123}'

# Complete a session
curl -X PATCH http://localhost:8000/specialist/1/appointment-session/1/complete \
  -H "Content-Type: application/json" \
  -d '{}'

# Get recommendations
curl http://localhost:8000/specialist/1/duration-recommendation?consumer_id=45&service_id=12
```

### 3. Add UI Components

**In professional.html, add to bookings list:**
```html
<!-- For upcoming bookings -->
<button onclick="startAppointment(booking.id)">▶ Start</button>

<!-- For in-progress bookings -->
<button onclick="completeAppointment(sessionId)">✓ Complete</button>
```

**In booking creation form:**
```javascript
// Fetch and show recommendation
async function loadDurationRecommendation(consumerId, serviceId) {
    const rec = await fetch(`/specialist/${specialistId}/duration-recommendation?consumer_id=${consumerId}&service_id=${serviceId}`).then(r => r.json());
    
    // Show recommendation to user
    showRecommendation(rec);
}
```

### 4. Add Analytics Dashboard (Future Enhancement)
- Show duration trends over time
- Identify most/least time-intensive clients
- Service performance metrics
- Scheduling accuracy score

## Technical Details

### Database Relationships:
```
AppointmentSession
  ├── booking_id → Booking
  ├── specialist_id → Specialist
  ├── consumer_id → Consumer
  └── service_id → ServiceDB
```

### Calculations:

**Actual Duration:**
```python
actual_duration_minutes = (actual_end - actual_start).total_seconds() / 60
```

**Overtime Status:**
```python
went_overtime = actual_end > scheduled_end
```

**Typical Overtime:**
```python
overtime_per_session = actual_duration - scheduled_duration
typical_overtime = average(all_overtime_values)
```

**Consistency Score:**
```python
std_dev = standard_deviation(durations)
consistency = 1 - (std_dev / average_duration)
# Clamped to [0, 1]
```

### Recommendation Logic:
```python
if client_sessions >= 3:
    recommend = client_average
    confidence = "high" if client_sessions >= 5 else "medium"
elif service_sessions >= 5:
    recommend = service_average
    confidence = "medium"
else:
    recommend = service.duration
    confidence = "low"
```

## Files Modified

1. ✅ `src/calendar_app/database.py` - Added AppointmentSession model
2. ✅ `src/calendar_app/models.py` - Added 6 new Pydantic models
3. ✅ `src/calendar_app/main.py` - Added 5 new endpoints
4. ✅ `APPOINTMENT_TRACKING.md` - Feature documentation
5. ✅ `migrate_appointment_sessions.py` - Migration script

## Files to Modify (Frontend Integration)

1. 🔄 `src/calendar_app/templates/professional.html` - Add Start/Complete buttons
2. 🔄 Add duration recommendation display in booking flow
3. 🔄 Add client insights panel to client profile view

## Security

All endpoints require authentication:
- Uses `require_authentication_dep` dependency
- Verifies specialist_id matches authenticated user
- Prevents cross-specialist data access

## Performance Considerations

- Session queries are indexed by specialist_id
- Limited to 100 sessions by default (configurable)
- Calculations done in-memory (fast for reasonable data volumes)
- Consider caching recommendations for frequently booked clients

## Future Enhancements

1. **Bulk Import** - Import historical appointment data
2. **Export Reports** - CSV/PDF reports of duration analytics
3. **Notifications** - Alert when running over scheduled time
4. **Predictions** - ML model to predict duration based on notes/service type
5. **Comparison Views** - Compare your durations to industry averages
6. **Calendar Integration** - Auto-adjust calendar blocks based on history

## Support

If you encounter issues:
1. Check `APPOINTMENT_TRACKING.md` for detailed documentation
2. Verify migration completed successfully
3. Test endpoints with curl before UI integration
4. Check server logs for error messages

---

**Status**: ✅ Backend Complete | 🔄 Frontend Integration Pending

**Created**: October 30, 2025
**Version**: 1.0
