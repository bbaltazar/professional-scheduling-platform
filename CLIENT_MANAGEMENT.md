# Client Management System Documentation

## Overview

The Client Management System allows professionals to track, manage, and maintain relationships with their clients. The system features intelligent client consolidation that merges bookings from the same person even when they use different contact information.

## Key Features

### 🎯 Smart Client Consolidation
- **Email OR Phone Matching**: Clients are identified uniquely by matching either email OR phone number
- **Unified History**: If a client books with email A + phone 1, then later books with email A + phone 2, all bookings are consolidated under one client record
- **Backward Compatible**: Works with legacy bookings that don't have consumer_id records

### 📊 Client Dashboard
- **Client Statistics**: Total clients, average rating, upcoming appointments
- **Search & Filter**: Filter clients by name, email, phone, or rating
- **Rating System**: Rate clients 1-10 for internal reference
- **Booking Stats**: See total visits, last appointment, next appointment

### 📋 Client Profiles
- **Private Notes**: Add biographical information about each client
- **Appointment Notes**: Track dated notes for each appointment
- **Rating Score**: Internal 1-10 rating system
- **Booking History**: View all past and future appointments

## Database Schema

### ClientProfile Table
```sql
CREATE TABLE client_profiles (
    id INTEGER PRIMARY KEY,
    specialist_id INTEGER NOT NULL,  -- FK to specialists
    consumer_id INTEGER NOT NULL,    -- FK to consumers
    bio TEXT,                         -- Professional's notes about client
    score INTEGER,                    -- Rating 1-10
    notes TEXT,                       -- JSON array of appointment notes
    created_at DATETIME,
    updated_at DATETIME,
    UNIQUE (specialist_id, consumer_id)  -- One profile per specialist-client pair
);
```

### Notes Structure
```json
[
    {
        "date": "2025-10-19T14:30:00Z",
        "note": "Client prefers morning appointments",
        "booking_id": 123
    },
    {
        "date": "2025-10-20T10:00:00Z",
        "note": "Requested specific stylist next time"
    }
]
```

## API Endpoints

### Get All Clients
```http
GET /professional/clients?specialist_id={id}
```

**Response:**
```json
[
    {
        "consumer_id": 1,
        "name": "John Doe",
        "email": "john@example.com",
        "phone": "+1 (555) 123-4567",
        "total_bookings": 5,
        "last_booking_date": "2025-10-15T14:00:00Z",
        "next_booking_date": "2025-10-25T10:00:00Z",
        "score": 9,
        "has_profile": true
    }
]
```

**Features:**
- Consolidates clients by email OR phone matching
- Includes booking statistics
- Shows profile status
- Sorted by last booking date (most recent first)

### Get Client Detail
```http
GET /professional/clients/{consumer_id}?specialist_id={id}
```

**Response:**
```json
{
    "consumer": {
        "id": 1,
        "name": "John Doe",
        "email": "john@example.com",
        "phone": "+1 (555) 123-4567",
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-10-19T00:00:00Z"
    },
    "profile": {
        "id": 1,
        "specialist_id": 1,
        "consumer_id": 1,
        "bio": "Regular client, prefers morning appointments",
        "score": 9,
        "notes": [
            {
                "date": "2025-10-15T14:30:00Z",
                "note": "Requested shorter haircut style"
            }
        ],
        "created_at": "2025-01-05T00:00:00Z",
        "updated_at": "2025-10-19T14:30:00Z"
    },
    "bookings_past": [
        {
            "id": 123,
            "date": "2025-10-15",
            "start_time": "14:00:00",
            "end_time": "14:30:00",
            "service_name": "Haircut",
            "service_price": 50.00,
            "status": "completed",
            "notes": "Client was satisfied"
        }
    ],
    "bookings_future": [
        {
            "id": 124,
            "date": "2025-10-25",
            "start_time": "10:00:00",
            "end_time": "10:30:00",
            "service_name": "Haircut",
            "service_price": 50.00,
            "status": "confirmed",
            "notes": null
        }
    ],
    "total_revenue": 250.00,
    "first_booking_date": "2025-01-10"
}
```

**Features:**
- Consolidated booking history from all matching consumer records
- Separate past and future appointments
- Total revenue calculation (completed bookings only)
- Client since date (first booking)

### Update Client Profile
```http
PUT /professional/clients/{consumer_id}/profile?specialist_id={id}
Content-Type: application/json

{
    "bio": "Preferred client, always on time",
    "score": 9,
    "notes": "[{\"date\":\"2025-10-19T14:30:00Z\",\"note\":\"Great communication\"}]"
}
```

**Response:**
```json
{
    "id": 1,
    "specialist_id": 1,
    "consumer_id": 1,
    "bio": "Preferred client, always on time",
    "score": 9,
    "notes": [
        {
            "date": "2025-10-19T14:30:00Z",
            "note": "Great communication"
        }
    ],
    "created_at": "2025-01-05T00:00:00Z",
    "updated_at": "2025-10-19T14:30:00Z"
}
```

**Features:**
- Creates profile if doesn't exist
- Updates existing profile fields
- Validates score (1-10 range)
- Notes are stored as JSON string, returned as parsed array

## UI Components

### Clients Tab (Professional Dashboard)
- **Location**: Professional dashboard → Clients tab
- **Features**:
  - Client grid with cards showing summary info
  - Search bar (filters by name, email, phone)
  - Rating filter dropdown (9-10 stars, 7-8 stars, etc.)
  - Statistics cards (total clients, average rating, upcoming appointments)
  - Click any client card to open detail modal

### Client Detail Modal
- **Triggered by**: Clicking a client card
- **Sections**:
  1. **Header**: Email, phone, client since date, total revenue
  2. **Client Profile**: Editable bio, rating slider (1-10), save button
  3. **Appointment Notes**: Add new notes with dates, view history
  4. **Booking History**: Separate tabs for upcoming and past appointments

### Client Card (List View)
```
┌─────────────────────────────────┐
│ John Doe              ⭐ 9/10   │
│ 📋 Has Profile                  │
│                                 │
│ 📧 john@example.com             │
│ 📱 +1 (555) 123-4567            │
│                                 │
│  5          📅                  │
│  Total Visits   Upcoming        │
│                                 │
│ Last visit: Oct 15, 2025        │
└─────────────────────────────────┘
```

## Client Consolidation Logic

### How It Works

1. **Booking Created**: Client books appointment with email X and phone Y
2. **Consumer Lookup**: System checks if consumer exists with email X OR phone Y
3. **Consolidation**: If multiple consumer records match, all are linked
4. **History Display**: Professional sees unified booking history

### Example Scenarios

#### Scenario 1: Email Match
```
Booking 1: email=john@email.com, phone=555-0001
Booking 2: email=john@email.com, phone=555-0002
Result: Both bookings shown under same client (matched by email)
```

#### Scenario 2: Phone Match
```
Booking 1: email=john@email.com, phone=555-0001
Booking 2: email=john.doe@email.com, phone=555-0001
Result: Both bookings shown under same client (matched by phone)
```

#### Scenario 3: Multiple Matches
```
Consumer A: email=john@email.com, phone=555-0001
Consumer B: email=john@email.com, phone=555-0002
Consumer C: email=john.doe@email.com, phone=555-0001

When searching for email=john@email.com OR phone=555-0001:
- Matches: A (email match), B (email match), C (phone match)
- Result: All three consumer records' bookings are consolidated
```

### Implementation Details

**find_matching_consumers()**
```python
def find_matching_consumers(db: Session, email: str = None, phone: str = None) -> List[Consumer]:
    """Find all consumers matching email OR phone"""
    conditions = []
    if email:
        conditions.append(Consumer.email == email)
    if phone:
        conditions.append(Consumer.phone == phone)
    
    return db.query(Consumer).filter(or_(*conditions)).all()
```

**consolidate_consumer_bookings()**
```python
def consolidate_consumer_bookings(db: Session, consumers: List[Consumer]) -> List[Booking]:
    """Get all bookings from multiple consumer records"""
    consumer_ids = [c.id for c in consumers]
    
    # Get bookings with consumer_id FK
    bookings = db.query(Booking).filter(Booking.consumer_id.in_(consumer_ids)).all()
    
    # Also get legacy bookings without consumer_id but matching email/phone
    for consumer in consumers:
        if consumer.email:
            legacy_by_email = db.query(Booking).filter(
                Booking.consumer_id.is_(None),
                Booking.client_email == consumer.email
            ).all()
            bookings.extend(legacy_by_email)
        
        if consumer.phone:
            legacy_by_phone = db.query(Booking).filter(
                Booking.consumer_id.is_(None),
                Booking.client_phone == consumer.phone
            ).all()
            bookings.extend(legacy_by_phone)
    
    return list(set(bookings))  # Deduplicate
```

## Testing Guide

### Test Case 1: Basic Client Management
1. Log in as professional
2. Go to Clients tab
3. Verify existing clients are displayed
4. Click a client to open detail modal
5. Add bio and rating, click Save
6. Verify profile saved message appears

### Test Case 2: Appointment Notes
1. Open client detail modal
2. Enter a note in the appointment notes section
3. Click "Add Note"
4. Verify note appears with timestamp
5. Close and reopen modal
6. Verify note persists

### Test Case 3: Client Consolidation (Email Match)
1. Create booking with email=test@example.com, phone=111-1111
2. Create booking with email=test@example.com, phone=222-2222
3. Check professional's client list
4. Should see ONE client with 2 bookings
5. Click client, verify both appointments shown

### Test Case 4: Client Consolidation (Phone Match)
1. Create booking with email=john@email.com, phone=555-0001
2. Create booking with email=jane@email.com, phone=555-0001
3. Check professional's client list
4. Should see ONE client with 2 bookings
5. Verify consolidation by phone number

### Test Case 5: Search and Filter
1. Go to Clients tab
2. Enter client name in search box
3. Verify filtered results
4. Select rating filter "9-10 stars"
5. Verify only highly-rated clients shown
6. Clear filters, verify all clients return

### Test Case 6: Statistics
1. Go to Clients tab
2. Verify "Total Clients" count is accurate
3. Verify "Average Rating" reflects rated clients
4. Verify "Upcoming" count matches clients with future appointments

## Performance Considerations

### Optimization Strategies
1. **Indexing**: Email and phone columns indexed for fast lookups
2. **Caching**: Client list cached in frontend (`allClients` variable)
3. **Lazy Loading**: Client details loaded only when modal opened
4. **Batch Queries**: Consolidation logic minimizes database hits

### Scaling Recommendations
- For large client bases (1000+ clients), implement pagination
- Consider adding full-text search for notes
- Add caching layer (Redis) for frequently accessed client profiles
- Implement background job for booking consolidation

## Migration

### Running the Migration
```bash
cd /Users/brianabaltazar/SoftwareEngineering/apps/calendar_app
python scripts/migrate_add_client_profiles.py
```

### Rollback (if needed)
```sql
DROP TABLE client_profiles;
```

### Backward Compatibility
- System works with existing bookings (with or without consumer_id)
- Legacy bookings matched by email/phone in consolidation logic
- No data loss during migration

## Security Considerations

### Access Control
- Professionals can only see their own clients
- Client profiles are private to each professional
- Separate specialist can have different profile for same client

### Data Privacy
- Client scores and notes are NEVER visible to clients
- Profiles are professional's private workspace
- Email/phone data respects existing privacy policies

### Validation
- Score range validated (1-10)
- Email format validated on consumer creation
- Phone format flexible to support international numbers

## Future Enhancements

### Potential Features
1. **Client Tags**: Categorize clients (VIP, Regular, New)
2. **Automated Notes**: Generate notes from booking data
3. **Client Communication**: Send SMS/email directly from client profile
4. **Revenue Analytics**: Track client lifetime value
5. **Referral Tracking**: See which clients refer others
6. **Appointment Preferences**: Store preferred times, services
7. **Photo Upload**: Add client photos for recognition
8. **Export**: Download client list as CSV/Excel

### Technical Improvements
1. Add GraphQL API for more flexible querying
2. Implement real-time updates with WebSockets
3. Add audit trail for profile changes
4. Implement soft delete for client profiles
5. Add multi-language support for notes

## Troubleshooting

### Issue: Clients not appearing
**Solution**: Ensure client has at least one booking with the professional

### Issue: Duplicate clients showing
**Solution**: This shouldn't happen due to consolidation logic. Check if email/phone exactly match (spaces, formatting).

### Issue: Profile not saving
**Solution**: Check browser console for errors. Verify specialist_id is set. Confirm score is 1-10.

### Issue: Booking history incomplete
**Solution**: Verify all bookings have consumer_id set. Legacy bookings are matched by email/phone in consolidation logic.

### Issue: Search not working
**Solution**: Search is case-insensitive and searches name, email, phone. Clear any rating filters.

## Support

For issues or feature requests related to client management:
1. Check this documentation first
2. Review browser console for JavaScript errors
3. Check server logs for backend errors
4. Verify database schema matches expected structure
