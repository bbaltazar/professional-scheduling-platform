# Quick Start: Appointment Duration Tracking

## ✅ Completed
- Database table created
- API endpoints implemented
- Models and schemas defined
- Migration successful

## 🎯 How to Use

### Step 1: Start Tracking an Appointment

When a professional starts an appointment, call:

```javascript
POST /specialist/{specialist_id}/appointment-session/start

Body: {
  "booking_id": 123
}
```

This records the actual start time.

### Step 2: Complete the Appointment

When finished, call:

```javascript
PATCH /specialist/{specialist_id}/appointment-session/{session_id}/complete

Body: {}  // or include notes
```

This records the end time and calculates duration.

### Step 3: Get Smart Recommendations

Before creating a new booking, fetch the recommendation:

```javascript
GET /specialist/{specialist_id}/duration-recommendation?consumer_id=45&service_id=12
```

Response shows recommended duration based on history.

## 📊 What You Get

### For Each Client:
- Average appointment duration
- How consistent their appointments are
- Typical overtime amount
- Historical range (min-max)

### Smart Recommendations:
```
"John Smith typically takes 72 minutes
(based on 8 previous appointments)"

Confidence: HIGH
Use this duration? [Yes] [No, use 60 min default]
```

## 🔧 Next: Add to UI

### Add Start/Complete Buttons

In `professional.html`, in the bookings list:

```javascript
// When appointment is upcoming or in-progress
async function startAppointment(bookingId) {
    const response = await fetch(
        `/specialist/${currentSpecialistId}/appointment-session/start`,
        {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ booking_id: bookingId })
        }
    );
    
    if (response.ok) {
        alert('Appointment started! Timer is running.');
        // Update UI - hide "Start", show "Complete"
        loadBookings();  // Refresh the list
    }
}

async function completeAppointment(sessionId) {
    const response = await fetch(
        `/specialist/${currentSpecialistId}/appointment-session/${sessionId}/complete`,
        {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({})
        }
    );
    
    if (response.ok) {
        const session = await response.json();
        alert(`Appointment completed! Actual duration: ${session.actual_duration_minutes} minutes`);
        loadBookings();  // Refresh
    }
}
```

### Show Recommendations When Booking

Before submitting a new booking:

```javascript
async function showDurationRecommendation(consumerId, serviceId) {
    try {
        const response = await fetch(
            `/specialist/${currentSpecialistId}/duration-recommendation?consumer_id=${consumerId}&service_id=${serviceId}`,
            { credentials: 'include' }
        );
        
        if (response.ok) {
            const rec = await response.json();
            
            // Show recommendation to user
            const html = `
                <div class="duration-recommendation" style="
                    background: rgba(255, 215, 0, 0.1);
                    padding: 15px;
                    border-radius: 8px;
                    border-left: 3px solid #FFD700;
                    margin: 15px 0;
                ">
                    <h4 style="color: #FFD700; margin-bottom: 8px;">
                        💡 Recommended Duration: ${rec.recommended_duration_minutes} minutes
                    </h4>
                    <p style="color: rgba(255,255,255,0.8); font-size: 0.9rem; margin-bottom: 10px;">
                        ${rec.based_on}
                    </p>
                    ${rec.client_history ? `
                        <p style="color: rgba(255,255,255,0.6); font-size: 0.85rem;">
                            Client average: ${rec.client_history.average_duration_minutes} min 
                            (${rec.client_history.total_sessions} sessions, 
                            ${Math.round(rec.client_history.consistency_score * 100)}% consistent)
                        </p>
                    ` : ''}
                    <button 
                        onclick="useDuration(${rec.recommended_duration_minutes})"
                        class="btn btn-small"
                        style="margin-top: 10px;"
                    >
                        Use This Duration
                    </button>
                </div>
            `;
            
            document.getElementById('recommendationContainer').innerHTML = html;
        }
    } catch (error) {
        console.log('No recommendation available yet');
    }
}

function useDuration(minutes) {
    // Update the duration field in your booking form
    document.getElementById('durationMinutes').value = minutes;
    // Or however you handle service duration in your form
}
```

## 📱 UI Suggestions

### Booking List Item:
```html
<div class="booking-card">
    <h3>John Smith - Haircut</h3>
    <p>Today at 2:00 PM (60 min)</p>
    
    <!-- Show based on booking status and time -->
    <div class="booking-actions">
        <!-- If upcoming and within 30 min of start time -->
        <button onclick="startAppointment({{booking.id}})" class="btn btn-primary">
            ▶ Start Appointment
        </button>
        
        <!-- If session started but not completed -->
        <button onclick="completeAppointment({{session.id}})" class="btn btn-success">
            ✓ Complete Appointment
        </button>
        
        <!-- Show timer if in progress -->
        <span class="timer">Running: 45 minutes</span>
    </div>
</div>
```

### Client Profile:
```html
<div class="client-insights-card">
    <h3>📊 Appointment History</h3>
    <div class="stat-grid">
        <div class="stat">
            <span class="stat-label">Total Sessions</span>
            <span class="stat-value">8</span>
        </div>
        <div class="stat">
            <span class="stat-label">Average Duration</span>
            <span class="stat-value">72 min</span>
        </div>
        <div class="stat">
            <span class="stat-label">Consistency</span>
            <span class="stat-value">90%</span>
        </div>
        <div class="stat">
            <span class="stat-label">Typical Overtime</span>
            <span class="stat-value">+12 min</span>
        </div>
    </div>
</div>
```

## 🎨 CSS Suggestions

```css
.duration-recommendation {
    background: rgba(255, 215, 0, 0.1);
    border-left: 3px solid #FFD700;
    padding: 15px;
    border-radius: 8px;
    margin: 15px 0;
}

.confidence-high {
    color: #4CAF50;
    font-weight: 600;
}

.confidence-medium {
    color: #FFA500;
    font-weight: 600;
}

.confidence-low {
    color: #999;
    font-weight: 600;
}

.timer {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    color: #FFD700;
    font-weight: 600;
}

.timer::before {
    content: '⏱️';
}

.stat-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 15px;
}

.stat {
    text-align: center;
    padding: 15px;
    background: rgba(255, 255, 255, 0.03);
    border-radius: 8px;
}

.stat-label {
    display: block;
    font-size: 0.85rem;
    color: rgba(255, 255, 255, 0.6);
    margin-bottom: 5px;
}

.stat-value {
    display: block;
    font-size: 1.5rem;
    font-weight: 700;
    color: #FFD700;
}
```

## 🧪 Testing

### Test the API:
```bash
# 1. Start a session
curl -X POST http://localhost:8000/specialist/1/appointment-session/start \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"booking_id": 1}'

# 2. Complete it (use session_id from response)
curl -X PATCH http://localhost:8000/specialist/1/appointment-session/1/complete \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{}'

# 3. Get recommendation
curl "http://localhost:8000/specialist/1/duration-recommendation?consumer_id=1&service_id=1" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 📈 Analytics Dashboard (Future)

Consider adding a dashboard showing:
- Most time-consuming clients
- Services that typically run over
- Your scheduling accuracy over time
- Weekly/monthly duration trends
- Comparison: scheduled vs actual time

## ✨ Tips

1. **Start simple** - Add Start/Complete buttons first
2. **Show value quickly** - Display recommendations after 2-3 appointments
3. **Make it optional** - Don't force tracking, make it beneficial
4. **Visual feedback** - Show running timer, actual vs scheduled
5. **Celebrate accuracy** - "You're 95% accurate at predicting appointment times!"

## 🐛 Troubleshooting

**Migration failed?**
```bash
python migrate_appointment_sessions.py
```

**Endpoints not found?**
- Check server logs
- Verify imports were added
- Restart server

**No recommendations?**
- Need at least 2-3 completed sessions
- Check that sessions have actual_end recorded
- Verify consumer_id matches

---

**Status**: ✅ Ready to use!
**Documentation**: See `APPOINTMENT_TRACKING.md` for full details
