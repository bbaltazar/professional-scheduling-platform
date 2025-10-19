# Workplace Management Feature

## Overview

This feature adds comprehensive workplace management to the professional scheduling platform, allowing professionals to associate themselves with multiple workplaces (e.g., barbershops, salons, offices) and maintain clean separation between their different work locations. The feature includes Yelp API integration to validate and populate workplace information.

## Key Features

### 1. **Workplace Management**
- Create, read, update, and delete workplaces
- Store comprehensive workplace information including:
  - Name, address, city, state, zip code, country
  - Phone number and website
  - Description
  - Yelp business verification
  - Verification status

### 2. **Many-to-Many Relationships**
- Professionals can be associated with multiple workplaces
- Each association includes:
  - Role (owner, employee, contractor, etc.)
  - Start and end dates
  - Active status for tracking employment history
- Maintains audit trail by marking associations as inactive rather than deleting them

### 3. **Yelp API Integration**
- Search for businesses using Yelp's comprehensive database
- Validate business information
- Auto-populate workplace data from Yelp business details
- Verify workplaces through Yelp's rating and review system

## Database Schema

### Workplaces Table
```sql
CREATE TABLE workplaces (
    id INTEGER PRIMARY KEY,
    name VARCHAR NOT NULL,
    address VARCHAR NOT NULL,
    city VARCHAR NOT NULL,
    state VARCHAR,
    zip_code VARCHAR,
    country VARCHAR DEFAULT 'US',
    phone VARCHAR,
    website VARCHAR,
    description TEXT,
    yelp_business_id VARCHAR UNIQUE,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at DATETIME,
    updated_at DATETIME
);
```

### Specialist-Workplace Association Table
```sql
CREATE TABLE specialist_workplace (
    specialist_id INTEGER REFERENCES specialists(id),
    workplace_id INTEGER REFERENCES workplaces(id),
    role VARCHAR,
    start_date DATE,
    end_date DATE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME,
    updated_at DATETIME,
    PRIMARY KEY (specialist_id, workplace_id)
);
```

## API Endpoints

### Workplace CRUD Operations

#### Create Workplace
```http
POST /workplaces/
Content-Type: application/json

{
  "name": "The Modern Barbershop",
  "address": "123 Main St",
  "city": "San Francisco",
  "state": "CA",
  "zip_code": "94102",
  "country": "US",
  "phone": "+1-555-123-4567",
  "website": "https://modernbarber.com",
  "description": "A modern barbershop with traditional techniques",
  "yelp_business_id": "modern-barbershop-sf",
  "is_verified": false
}
```

#### Get All Workplaces
```http
GET /workplaces/?city=San Francisco&state=CA&is_verified=true
```

#### Get Workplace by ID
```http
GET /workplaces/{workplace_id}
```

#### Update Workplace
```http
PUT /workplaces/{workplace_id}
Content-Type: application/json

{
  "phone": "+1-555-987-6543",
  "is_verified": true
}
```

#### Delete Workplace
```http
DELETE /workplaces/{workplace_id}
```

### Specialist-Workplace Associations

#### Associate Specialist with Workplace
```http
POST /specialists/{specialist_id}/workplaces/{workplace_id}
Content-Type: application/json

{
  "role": "owner",
  "start_date": "2025-01-01",
  "is_active": true
}
```

#### Remove Specialist-Workplace Association
```http
DELETE /specialists/{specialist_id}/workplaces/{workplace_id}
```

#### Get Specialist's Workplaces
```http
GET /specialists/{specialist_id}/workplaces
```

### Yelp Integration

#### Search Yelp Businesses
```http
GET /yelp/search?term=barbershop&location=San Francisco, CA&limit=10
```

Response:
```json
[
  {
    "id": "modern-barbershop-sf",
    "name": "The Modern Barbershop",
    "url": "https://www.yelp.com/biz/modern-barbershop-sf",
    "phone": "+15551234567",
    "display_phone": "(555) 123-4567",
    "address": "123 Main St",
    "city": "San Francisco",
    "state": "CA",
    "zip_code": "94102",
    "country": "US",
    "rating": 4.5,
    "review_count": 142,
    "categories": ["Barbershops", "Men's Hair Salons"],
    "image_url": "https://...",
    "is_closed": false,
    "distance": 1234.56
  }
]
```

#### Get Yelp Business Details
```http
GET /yelp/business/{business_id}
```

#### Create Workplace from Yelp Business
```http
POST /workplaces/from-yelp/{business_id}
```

This endpoint automatically creates a verified workplace using data from Yelp, including:
- Name, address, city, state, zip code
- Phone number
- Rating and review information in the description
- Yelp business ID for future reference
- Automatically marked as verified

## Configuration

### Environment Variables

Add the following to your `.env` file:

```bash
# Yelp API Configuration
YELP_API_KEY=your_yelp_api_key_here
```

### Getting a Yelp API Key

1. Go to [https://www.yelp.com/developers](https://www.yelp.com/developers)
2. Create a developer account
3. Create a new app
4. Copy your API key
5. Add it to your environment variables

**Note**: The Yelp Fusion API is free for up to 5,000 API calls per day.

## Use Cases

### 1. Barbershop Owner with Side Hustle
A barber who owns their own shop but also does mobile haircuts on weekends can:
- Add their barbershop as a verified workplace through Yelp
- Add "Mobile Services" as a custom workplace
- Keep their schedules separate for each location
- Track bookings by workplace

### 2. Multi-Location Professional
A stylist working at multiple salons can:
- Associate with each salon
- Mark role (employee, contractor)
- Set start/end dates for each position
- Maintain employment history even after leaving a workplace

### 3. Venue Verification
Clients can:
- See verified workplaces (validated through Yelp)
- View ratings and reviews
- Know the professional works at legitimate, established businesses

## Implementation Details

### Models

**Pydantic Models** (`models.py`):
- `WorkplaceCreate` - For creating new workplaces
- `WorkplaceResponse` - For API responses
- `WorkplaceUpdate` - For updating workplaces
- `YelpBusinessSearch` - For Yelp search parameters
- `YelpBusinessResponse` - For Yelp business data
- `SpecialistWorkplaceAssociation` - For association data

**SQLAlchemy Models** (`database.py`):
- `Workplace` - Workplace database table
- `specialist_workplace_association` - Association table

### Services

**Yelp Service** (`yelp_service.py`):
- `search_businesses()` - Search Yelp for businesses
- `get_business_details()` - Get detailed business info
- `validate_business()` - Validate a Yelp business ID
- Handles API errors gracefully
- Provides detailed error messages

## Testing

Run the test script to verify functionality:

```bash
python test_workplace.py
```

Or test via the API documentation:

```bash
# Start the server
uvicorn src.calendar_app.main:app --reload

# Open browser to:
http://localhost:8000/docs
```

## Future Enhancements

1. **Workplace Photos**: Integrate Yelp business photos
2. **Working Hours**: Link workplace hours with specialist availability
3. **Location-Based Search**: Search specialists by workplace location
4. **Workplace Reviews**: Allow clients to leave reviews for specific workplaces
5. **Service Location Filtering**: Filter services by workplace
6. **Distance Calculation**: Calculate distance from client to workplace
7. **Maps Integration**: Display workplace locations on a map

## Security Considerations

1. **API Key Protection**: Never commit Yelp API key to version control
2. **Rate Limiting**: Respect Yelp's API rate limits (5,000 calls/day)
3. **Authentication**: Future version should re-enable authentication for association management
4. **Data Validation**: All workplace data is validated before database insertion
5. **Audit Trail**: Association changes are tracked with timestamps

## Dependencies

New dependencies added:
- `httpx` - For making async HTTP requests to Yelp API

## Migration Notes

For existing databases, run migrations to:
1. Create the `workplaces` table
2. Create the `specialist_workplace` association table
3. Update any existing specialist records if needed

The application will automatically create tables on startup if they don't exist.

## Support

For issues or questions:
1. Check the API documentation at `/docs`
2. Review error messages in the response
3. Verify Yelp API key is properly configured
4. Check server logs for detailed error information