# Appointment Duration Tracking Feature

## Overview
Track actual appointment durations to provide professionals with data-driven insights on how long appointments really take, helping them schedule more accurately.

## Database Changes

### New Table: `appointment_sessions`
Tracks the actual start and end times of appointments for analytics.

```sql
CREATE TABLE appointment_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    booking_id INTEGER NOT NULL REFERENCES bookings(id),
    specialist_id INTEGER NOT NULL REFERENCES specialists(id),
    consumer_id INTEGER REFERENCES consumers(id),
    service_id INTEGER REFERENCES services(id),
    
    -- Scheduled times
    scheduled_start DATETIME NOT NULL,
    scheduled_end DATETIME NOT NULL,
    scheduled_duration_minutes INTEGER NOT NULL,
    
    -- Actual times
    actual_start DATETIME,
    actual_end DATETIME,
    actual_duration_minutes INTEGER,
    
    -- Analytics flags
    was_early BOOLEAN DEFAULT FALSE,
    was_late BOOLEAN DEFAULT FALSE,
    went_overtime BOOLEAN DEFAULT FALSE,
    
    -- Metadata
    session_notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Migration Required
Run this after updating the code:
```python
# In Python terminal or migration script:
from src.calendar_app.database import database, Base, AppointmentSession
Base.metadata.create_all(bind=database.engine)
```

Or manually:
```bash
# Backup first!
cp calendar_app.db calendar_app.db.backup

# Then run Python to create table
python -c "from src.calendar_app.database import database, Base; Base.metadata.create_all(bind=database.engine)"
```

## API Endpoints

### 1. Start Appointment Session
**POST** `/specialist/{specialist_id}/appointment-session/start`

**Request:**
```json
{
  "booking_id": 123,
  "actual_start": "2025-10-30T14:05:00",  // optional, uses now() if omitted
  "session_notes": "Client arrived 5 min late"
}
```

**Response:** `AppointmentSessionResponse`

### 2. Complete Appointment Session
**PATCH** `/specialist/{specialist_id}/appointment-session/{session_id}/complete`

**Request:**
```json
{
  "actual_end": "2025-10-30T15:20:00",  // optional, uses now() if omitted
  "session_notes": "Needed extra time for additional service"
}
```

**Response:** `AppointmentSessionResponse`

### 3. Get Appointment Sessions
**GET** `/specialist/{specialist_id}/appointment-sessions?consumer_id=45&service_id=12&limit=50`

**Response:** `List[AppointmentSessionResponse]`

### 4. Get Client Duration Insights
**GET** `/specialist/{specialist_id}/client/{consumer_id}/duration-insights`

**Response:**
```json
{
  "consumer_id": 45,
  "client_name": "John Smith",
  "total_sessions": 8,
  "average_duration_minutes": 62.5,
  "median_duration_minutes": 60,
  "min_duration_minutes": 45,
  "max_duration_minutes": 90,
  "typical_overtime_minutes": 12.5,
  "consistency_score": 0.85
}
```

### 5. Get Duration Recommendation
**GET** `/specialist/{specialist_id}/duration-recommendation?consumer_id=45&service_id=12`

**Response:**
```json
{
  "recommended_duration_minutes": 65,
  "confidence": "high",
  "based_on": "Based on 8 previous appointments with this client",
  "client_history": { /* ClientDurationInsight */ },
  "service_history": { /* ServiceDurationInsight */ }
}
```

## Usage Flow

### For Professionals:

1. **When appointment starts:**
   - Click "Start Appointment" button
   - System records actual start time
   - Creates `AppointmentSession` record

2. **When appointment ends:**
   - Click "Complete Appointment" button
   - System records actual end time
   - Calculates actual duration
   - Updates booking status to "completed"

3. **When booking new appointment:**
   - System fetches duration recommendation
   - Shows historical data: "This client typically takes 65 minutes (based on 8 appointments)"
   - Professional can adjust duration or use recommendation

## Analytics Provided

### Client-Level Insights:
- **Average Duration**: How long this client's appointments typically take
- **Consistency Score**: 0-1 score indicating how predictable their duration is
- **Typical Overtime**: How much they usually go over scheduled time
- **Range**: Min/max durations seen

### Service-Level Insights:
- **Average Duration**: How long this service takes across all clients
- **Typical Variance**: Standard deviation of durations
- **Comparison**: Actual vs scheduled duration

### Smart Recommendations:
Priority order:
1. **Client History** (if ≥3 appointments): Use client's average
2. **Service History** (if ≥5 appointments): Use service average  
3. **Service Default**: Fall back to configured duration

Confidence levels:
- **High**: ≥5 client appointments
- **Medium**: 3-4 client appointments or ≥5 service appointments
- **Low**: Insufficient data, using default

## Frontend Integration Points

### 1. Booking List View
Add buttons to each upcoming/in-progress booking:
```html
<button onclick="startAppointment(bookingId)">▶ Start</button>
<button onclick="completeAppointment(sessionId)">✓ Complete</button>
```

### 2. New Booking Flow
When creating a booking, show recommendation:
```html
<div class="duration-recommendation">
  <h4>Recommended Duration: 65 minutes</h4>
  <p>Based on 8 previous appointments with this client</p>
  <p>Client average: 65 min | Service average: 60 min</p>
  <button onclick="useRecommendation(65)">Use Recommendation</button>
</div>
```

### 3. Client Profile Page
Show duration insights:
```html
<div class="client-insights">
  <h3>Appointment History</h3>
  <p>Total Sessions: 8</p>
  <p>Average Duration: 62.5 minutes</p>
  <p>Consistency: 85% (Very Predictable)</p>
  <p>Typical Overtime: +12.5 minutes</p>
</div>
```

## Example JavaScript Integration

```javascript
// Start appointment
async function startAppointment(bookingId) {
    const response = await fetch(
        `/specialist/${specialistId}/appointment-session/start`,
        {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ booking_id: bookingId })
        }
    );
    
    if (response.ok) {
        const session = await response.json();
        console.log('Session started:', session);
        // Update UI to show "Complete" button
    }
}

// Complete appointment
async function completeAppointment(sessionId) {
    const response = await fetch(
        `/specialist/${specialistId}/appointment-session/${sessionId}/complete`,
        {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({})
        }
    );
    
    if (response.ok) {
        const session = await response.json();
        console.log('Session completed. Duration:', session.actual_duration_minutes);
        // Show success message with actual duration
    }
}

// Get duration recommendation for booking
async function getDurationRecommendation(consumerId, serviceId) {
    const response = await fetch(
        `/specialist/${specialistId}/duration-recommendation?consumer_id=${consumerId}&service_id=${serviceId}`,
        { credentials: 'include' }
    );
    
    if (response.ok) {
        const recommendation = await response.json();
        displayRecommendation(recommendation);
    }
}

function displayRecommendation(rec) {
    const html = `
        <div class="recommendation">
            <h4>💡 Recommended Duration: ${rec.recommended_duration_minutes} minutes</h4>
            <p class="confidence ${rec.confidence}">${rec.based_on}</p>
            ${rec.client_history ? `
                <p>Client Average: ${rec.client_history.average_duration_minutes} min (${rec.client_history.total_sessions} sessions)</p>
            ` : ''}
            <button onclick="useDuration(${rec.recommended_duration_minutes})">Use This Duration</button>
        </div>
    `;
    document.getElementById('recommendationContainer').innerHTML = html;
}
```

## Benefits

1. **Data-Driven Scheduling**: No more guessing - use actual historical data
2. **Better Client Management**: Identify clients who need more/less time
3. **Improved Accuracy**: Reduce double-bookings and scheduling conflicts
4. **Professional Insights**: Understand which services actually take longer
5. **Client Satisfaction**: More accurate time estimates = happier clients

## Next Steps

1. ✅ Run database migration to create `appointment_sessions` table
2. ✅ Test API endpoints with Postman or curl
3. 🔄 Add UI buttons for Start/Complete appointment
4. 🔄 Integrate duration recommendations into booking flow
5. 🔄 Add analytics dashboard showing duration trends
