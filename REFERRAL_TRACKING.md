# Referral Tracking & Dual Booking Flow Feature

## Overview
This feature implements a **dual booking flow** with **referral tracking** to attribute customers to either businesses or professionals, creating a "book of business" for analytics and commission tracking.

## Two Booking Flows

### 1. Professional-First Flow (Direct Booking)
**Path**: Customer → Browse Professionals → Select Professional → Choose Service → Book

- Customer browses all professionals directly
- Selects a professional and service
- Makes a booking
- **Referral Attribution**: Customer is credited to the **professional**

### 2. Business-First Flow (Workplace Referral)
**Path**: Customer → Browse Businesses → Select Business → View Professionals → Select Professional → Choose Service → Book

- Customer browses businesses/workplaces
- Selects a business to explore
- Views professionals working at that business
- Selects a professional and service
- Makes a booking
- **Referral Attribution**: Customer is credited to the **business**

## Database Schema

### New Tables

#### `consumers`
Tracks customer information across bookings:
```sql
CREATE TABLE consumers (
    id INTEGER PRIMARY KEY,
    name VARCHAR,
    email VARCHAR UNIQUE,
    phone VARCHAR,
    created_at DATETIME,
    updated_at DATETIME
)
```

#### `referrals`
Tracks the source of each customer's **first booking**:
```sql
CREATE TABLE referrals (
    id INTEGER PRIMARY KEY,
    consumer_id INTEGER,           -- Which customer
    specialist_id INTEGER,          -- Which professional they booked with
    referred_by_specialist_id INTEGER NULL,  -- If direct booking
    referred_by_workplace_id INTEGER NULL,   -- If business-first booking
    referral_date DATETIME
)
```

**Important**: Only ONE of `referred_by_specialist_id` or `referred_by_workplace_id` will be populated.

#### Updated `bookings` Table
Added foreign key to link bookings to consumers:
```sql
ALTER TABLE bookings ADD COLUMN consumer_id INTEGER REFERENCES consumers(id)
```

Legacy fields (`client_name`, `client_email`, `client_phone`) are kept for backward compatibility.

## API Endpoints

### Consumer Business Browsing

#### `GET /consumer/workplaces`
Browse all businesses/workplaces.

**Query Parameters**:
- `city` (optional): Filter by city
- `state` (optional): Filter by state
- `limit` (default: 50): Number of results

**Response**:
```json
[
  {
    "id": 1,
    "name": "Elite Salon & Spa",
    "address": "123 Main St",
    "city": "San Francisco",
    "state": "CA",
    "specialists_count": 5,
    "is_verified": true
  }
]
```

#### `GET /consumer/workplaces/{workplace_id}`
Get detailed information about a specific business.

#### `GET /consumer/workplaces/{workplace_id}/specialists`
Get all professionals working at a specific business.

**Response**:
```json
[
  {
    "id": 1,
    "name": "Jane Smith",
    "email": "jane@example.com",
    "bio": "Expert stylist with 10 years experience",
    "phone": "555-1234",
    "services": [
      {
        "id": 1,
        "name": "Haircut",
        "price": 50.0,
        "duration": 60
      }
    ]
  }
]
```

### Booking Endpoint Updates

#### `POST /booking/`
**New Field**: `source_workplace_id` (optional)

**Request Body**:
```json
{
  "specialist_id": 1,
  "service_id": 1,
  "booking_date": "2025-10-25",
  "start_time": "14:00",
  "client_name": "John Doe",
  "client_email": "john@example.com",
  "client_phone": "555-9876",
  "source_workplace_id": 3  // ← NEW: If booking through business
}
```

**Referral Logic**:
1. Check if consumer exists by email
2. If **new consumer**:
   - Create consumer record
   - Create referral record:
     - If `source_workplace_id` is provided → attribute to **business**
     - If `source_workplace_id` is null → attribute to **professional**
3. If **existing consumer**:
   - Use existing consumer record
   - No new referral created (only first booking counts)
4. Create booking linked to consumer

## UI Components

### Updated `consumer.html`
- **Toggle Buttons**: Switch between "Browse by Professional" and "Browse by Business"
- **Professionals Section**: Existing professional browsing (default)
- **Businesses Section**: New business browsing grid

### New `consumer_business.html`
- Business header with name, address, phone, website
- Verified badge for Yelp-verified businesses
- Grid of professionals at that business
- Service listings with prices

### Updated `consumer_professional.html`
- Propagates `workplace_id` query parameter when navigating to booking

### Updated `consumer_booking.html`
- Captures `workplace_id` from URL query parameters
- Includes `source_workplace_id` in booking API request

## Query Parameter Flow

The `workplace_id` parameter flows through the entire business-first booking flow:

1. **Business List** → **Business Detail**:
   ```
   /consumer/business/{business_id}
   ```

2. **Business Detail** → **Professional Services**:
   ```
   /consumer/professional/{specialist_id}?workplace_id={business_id}
   ```

3. **Professional Services** → **Booking Page**:
   ```
   /consumer/professional/{specialist_id}/service/{service_id}?workplace_id={business_id}
   ```

4. **Booking Page** → **API Request**:
   ```json
   {
     "source_workplace_id": business_id
   }
   ```

## Analytics & Reporting

### Book of Business Queries

**Get customers attributed to a specific business**:
```sql
SELECT c.*, r.referral_date
FROM consumers c
JOIN referrals r ON c.id = r.consumer_id
WHERE r.referred_by_workplace_id = ?
```

**Get customers attributed to a specific professional**:
```sql
SELECT c.*, r.referral_date
FROM consumers c
JOIN referrals r ON c.id = r.consumer_id
WHERE r.referred_by_specialist_id = ?
```

**Get referral source breakdown for a professional**:
```sql
SELECT 
  CASE 
    WHEN r.referred_by_workplace_id IS NOT NULL THEN 'Business'
    ELSE 'Direct'
  END as source,
  COUNT(*) as count
FROM referrals r
WHERE r.specialist_id = ?
GROUP BY source
```

## Testing

### Test Professional-First Flow:
1. Go to `/consumer`
2. Keep "Browse by Professional" selected
3. Select a professional
4. Choose a service and book
5. **Expected**: Referral created with `referred_by_specialist_id` set

### Test Business-First Flow:
1. Go to `/consumer`
2. Click "Browse by Business"
3. Select a business
4. Select a professional at that business
5. Choose a service and book
6. **Expected**: Referral created with `referred_by_workplace_id` set

### Verify Referral Tracking:
```python
from database import SessionLocal, Referral, Consumer

db = SessionLocal()

# Get all referrals
referrals = db.query(Referral).all()

for ref in referrals:
    consumer = db.query(Consumer).filter(Consumer.id == ref.consumer_id).first()
    source = "Business" if ref.referred_by_workplace_id else "Professional"
    print(f"Customer: {consumer.name} | Source: {source} | Date: {ref.referral_date}")
```

## Migration

Run the migration script to add new tables:
```bash
python scripts/migrate_add_referrals.py
```

This script:
- Creates `consumers` table
- Creates `referrals` table
- Adds `consumer_id` column to `bookings` table
- Preserves all existing data

## Future Enhancements

1. **Commission Tracking**: Calculate commissions based on referral attribution
2. **Analytics Dashboard**: Show professional/business performance metrics
3. **Referral Reports**: Export book of business for each entity
4. **Multi-source Attribution**: Track all booking sources, not just first
5. **Consumer Portal**: Let consumers view their booking history
6. **Loyalty Programs**: Reward customers based on booking frequency

## Files Modified

- `database.py`: Added Consumer, Referral tables, updated Booking
- `models.py`: Added ConsumerCreate, ConsumerResponse, ReferralCreate, ReferralResponse
- `main.py`: Updated imports, booking endpoint, added consumer browsing endpoints
- `consumer.html`: Added business browsing toggle
- `consumer_business.html`: NEW - Business detail page
- `consumer_professional.html`: Propagate workplace_id param
- `consumer_booking.html`: Capture and send source_workplace_id
- `scripts/migrate_add_referrals.py`: NEW - Migration script
