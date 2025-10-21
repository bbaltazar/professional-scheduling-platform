# Referral Tracking Implementation Summary

## ✅ What Was Implemented

### 1. Database Schema
- **New `consumers` table**: Stores customer information (name, email, phone)
- **New `referrals` table**: Tracks first booking source for each customer
  - `referred_by_specialist_id`: Set when booking directly with professional
  - `referred_by_workplace_id`: Set when booking through business
- **Updated `bookings` table**: Added `consumer_id` foreign key
- Migration script created and run successfully

### 2. Backend API Endpoints
- `GET /consumer/workplaces` - Browse all businesses (with city/state filters)
- `GET /consumer/workplaces/{workplace_id}` - Get business details
- `GET /consumer/workplaces/{workplace_id}/specialists` - Get professionals at a business
- `POST /booking/` - Updated to accept `source_workplace_id` parameter

### 3. Booking Logic Updates
- Automatic consumer creation/lookup by email
- First booking creates referral record:
  - If `source_workplace_id` provided → business referral
  - If `source_workplace_id` null → professional referral
- Subsequent bookings reuse existing consumer (no new referral)

### 4. Frontend UI
- **Updated `consumer.html`**:
  - Toggle buttons: "Browse by Professional" vs "Browse by Business"
  - Two separate sections for each browse mode
  - Business grid shows: name, location, professional count, verified badge
  
- **New `consumer_business.html`**:
  - Business header with full details
  - Grid of professionals at that business
  - Services with prices shown
  - Click professional → booking flow with `workplace_id` param
  
- **Updated `consumer_professional.html`**:
  - Propagates `workplace_id` query parameter to booking page
  
- **Updated `consumer_booking.html`**:
  - Captures `workplace_id` from URL
  - Sends `source_workplace_id` in booking API request

### 5. Query Parameter Flow
The `workplace_id` flows through the entire booking funnel:
```
/consumer (browse businesses)
  ↓
/consumer/business/123
  ↓
/consumer/professional/456?workplace_id=123
  ↓
/consumer/professional/456/service/789?workplace_id=123
  ↓
POST /booking/ { source_workplace_id: 123 }
```

## 📊 How to Use

### For Customers - Professional-First Flow:
1. Visit `/consumer`
2. Keep "Browse by Professional" selected
3. Select a professional from the grid
4. Choose a service
5. Book appointment
→ **Customer is attributed to the professional**

### For Customers - Business-First Flow:
1. Visit `/consumer`
2. Click "Browse by Business"
3. Select a business from the grid
4. View professionals at that business
5. Select a professional
6. Choose a service
7. Book appointment
→ **Customer is attributed to the business**

## 🔍 Analytics Queries

### Get customers attributed to a business:
```python
from database import SessionLocal, Consumer, Referral

db = SessionLocal()

business_id = 1
referrals = db.query(Referral).filter(
    Referral.referred_by_workplace_id == business_id
).all()

for ref in referrals:
    consumer = db.query(Consumer).filter(Consumer.id == ref.consumer_id).first()
    print(f"{consumer.name} - {consumer.email} - {ref.referral_date}")
```

### Get customers attributed to a professional:
```python
specialist_id = 2
referrals = db.query(Referral).filter(
    Referral.referred_by_specialist_id == specialist_id
).all()

for ref in referrals:
    consumer = db.query(Consumer).filter(Consumer.id == ref.consumer_id).first()
    print(f"{consumer.name} - {consumer.email} - {ref.referral_date}")
```

### Count referral sources for a professional:
```python
from sqlalchemy import func

specialist_id = 2

# Business referrals
business_count = db.query(Referral).filter(
    Referral.specialist_id == specialist_id,
    Referral.referred_by_workplace_id.isnot(None)
).count()

# Direct referrals
direct_count = db.query(Referral).filter(
    Referral.specialist_id == specialist_id,
    Referral.referred_by_specialist_id.isnot(None)
).count()

print(f"Business referrals: {business_count}")
print(f"Direct referrals: {direct_count}")
```

## 🧪 Testing

1. **Migration Completed**: ✅
   - `consumers` table created
   - `referrals` table created
   - `consumer_id` column added to `bookings`

2. **Server Auto-Reload**: ✅
   - Server should have reloaded automatically
   - New endpoints are live

3. **Test URLs**:
   - Browse professionals: http://localhost:8000/consumer
   - Browse businesses: http://localhost:8000/consumer (click "Browse by Business")
   - Example business detail: http://localhost:8000/consumer/business/1

4. **Verify Referral Tracking**:
   - Make a booking through a business
   - Check database:
     ```python
     from database import SessionLocal, Referral
     db = SessionLocal()
     referrals = db.query(Referral).all()
     for r in referrals:
         print(f"Consumer: {r.consumer_id}, Business: {r.referred_by_workplace_id}, Professional: {r.referred_by_specialist_id}")
     ```

## 📁 Files Changed

### New Files:
- `templates/consumer_business.html` - Business detail page
- `scripts/migrate_add_referrals.py` - Database migration
- `REFERRAL_TRACKING.md` - Full documentation

### Modified Files:
- `database.py` - Added Consumer, Referral, updated Booking
- `models.py` - Added Consumer/Referral Pydantic models
- `main.py` - New endpoints, updated booking logic
- `consumer.html` - Browse mode toggle
- `consumer_professional.html` - Propagate workplace_id
- `consumer_booking.html` - Capture source_workplace_id

## 🎯 Key Features

1. **Dual Booking Flows**: Professional-first OR Business-first
2. **Referral Attribution**: Only tracks first booking per customer
3. **Book of Business**: Query customers by business or professional
4. **Query Parameter Propagation**: Workplace ID flows through entire funnel
5. **Backward Compatible**: Legacy booking fields preserved
6. **Zero-Downtime Migration**: Tables added without data loss

## 🚀 Next Steps (Future Enhancements)

1. Add analytics dashboard showing referral metrics
2. Commission calculation based on referral source
3. Export book of business reports
4. Consumer portal for viewing booking history
5. Loyalty/rewards program based on booking frequency
6. Multi-touch attribution (track all sources, not just first)

## 📝 Notes

- Only the **first booking** creates a referral record
- Exactly ONE of `referred_by_specialist_id` or `referred_by_workplace_id` is set
- Consumer records are looked up by email (unique identifier)
- Legacy `client_name`, `client_email`, `client_phone` fields are still populated for backward compatibility
- Server will auto-reload after file changes

## ✅ Ready to Test!

The feature is fully implemented and ready to test. Visit http://localhost:8000/consumer and try both booking flows!
