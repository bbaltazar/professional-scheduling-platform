# Advanced Search Feature Documentation

## Overview
A comprehensive Yelp-style search system that allows customers to find professionals and businesses by service, location, and type. This feature enables discovery through a powerful unified search interface.

## Key Features

### 1. **Unified Search Interface**
- Single search box for all queries (service names, professional names, business names)
- Dropdown to toggle between "Professional" and "Business" search modes
- Location input with "Use Current Location" button
- Enter key support for quick searches
- URL parameter preservation for shareable search results

### 2. **Professional Search**
Find professionals by:
- **Service name**: "haircut", "massage", "facial"
- **Professional name**: Search by specialist name
- **Bio keywords**: Search professional bios/descriptions
- **Location**: Filter by city, state, or address

Results show:
- Professional name and avatar
- Bio/description
- Phone number
- All workplaces where they work (with locations)
- Services offered with prices
- Direct link to booking

### 3. **Business Search**
Find businesses by:
- **Business name**: Search by workplace name
- **Description**: Search business descriptions
- **Location**: Filter by city, state, or address

Results show:
- Business name and verification badge
- Full address and contact info
- Number of professionals
- All services available with prices
- Direct link to view business professionals

## API Endpoint

### `GET /search`

**Query Parameters:**
```
query       (string, optional)  - Search term (service, name, etc.)
search_type (string, required)  - "professional" or "business"
location    (string, optional)  - Free-text location search
city        (string, optional)  - Specific city filter
state       (string, optional)  - Specific state filter
limit       (int, default: 20)  - Maximum results to return
```

**Response Format:**
```json
{
  "results": [
    {
      "type": "professional",
      "id": 1,
      "name": "Jane Smith",
      "bio": "Expert stylist with 10 years experience",
      "phone": "555-1234",
      "services": [
        {
          "id": 1,
          "name": "Haircut",
          "price": 50.0,
          "duration": 60
        }
      ],
      "workplaces": [
        {
          "id": 1,
          "name": "Elite Salon",
          "address": "123 Main St",
          "city": "San Francisco",
          "state": "CA",
          "is_verified": true
        }
      ]
    }
  ],
  "count": 1
}
```

## Search Logic

### Professional Search Algorithm:
1. **Direct Match**: Search specialist name and bio
2. **Service Match**: Find services matching query, then get their specialists
3. **Location Filter**: 
   - If `city` specified: Exact match on workplace city
   - If `state` specified: Exact match on workplace state
   - If `location` specified: Fuzzy match on city, state, or address
4. **Workplace Aggregation**: Include all workplaces for each professional
5. **Location Filtering**: Exclude professionals with no workplaces matching location criteria

### Business Search Algorithm:
1. **Direct Match**: Search business name and description
2. **Location Filter**: Same as professional search
3. **Service Aggregation**: Collect all services from all specialists at the business
4. **Specialist Count**: Count active specialists at each workplace

## UI Components

### Search Header (Sticky)
```html
┌─────────────────────────────────────────────────────────────┐
│ 🌟 Élite Services                                           │
├─────────────────────────────────────────────────────────────┤
│ 🔍 [haircut, massage...] │ [Professional▾] │ [SF, CA 📍] │ Search │
└─────────────────────────────────────────────────────────────┘
```

Features:
- **Search input**: Service/name search with icon
- **Type dropdown**: Professional/Business toggle
- **Location input**: Free-text location with GPS button
- **Search button**: Submits search (or press Enter)

### Results Display

**Professional Card:**
```
┌────────────────────────────────────────────────────┐
│ [JS] Jane Smith  👤 Professional                   │
│ Expert stylist with 10 years experience            │
│ 📞 555-1234                                        │
│ 📍 Elite Salon - San Francisco, CA ✓              │
│ [Haircut $50] [Color $120] [Styling $40]         │
│                                     [View Profile] │
└────────────────────────────────────────────────────┘
```

**Business Card:**
```
┌────────────────────────────────────────────────────┐
│ [✓] Elite Salon  🏢 Business  ✓ Verified          │
│ Full-service salon offering premium treatments     │
│ 📍 123 Main St, San Francisco, CA 94102           │
│ 📞 555-1234  🌐 elitesalon.com                    │
│ 👥 5 professionals                                 │
│ [Haircut $50] [Massage $80] [Facial $60]         │
│                                  [View Business]   │
└────────────────────────────────────────────────────┘
```

### Empty States

**Initial State:**
```
        🔍
   Start your search
Enter a service, professional name,
or business name to find what you need
```

**No Results:**
```
        😔
    No results found
Try different search terms or
   broaden your location
```

**Loading State:**
```
       ⟳
    Searching...
```

## User Flows

### Flow 1: Search by Service
1. User enters "haircut" in search box
2. Selects "Professional" from dropdown
3. Enters "San Francisco" in location
4. Clicks Search
5. Sees all professionals offering haircuts in SF
6. Clicks on a professional
7. Views services and books

### Flow 2: Search by Business
1. User enters "salon" in search box
2. Selects "Business" from dropdown
3. Enters "CA" in location
4. Clicks Search
5. Sees all salons in California
6. Clicks on a business
7. Views professionals at that business
8. Books with a professional (referral tracked to business)

### Flow 3: Location-First Search
1. User leaves search box empty
2. Clicks GPS button (📍)
3. Browser requests location permission
4. Location auto-populated
5. Clicks Search
6. Sees all professionals/businesses near them

## Integration with Referral Tracking

When a user books through the search flow:

**Professional Search → Booking:**
- Referral attributed to **professional** (direct booking)
- `referred_by_specialist_id` is set

**Business Search → Professional → Booking:**
- User journey: Search → Business → Professional → Service → Book
- `workplace_id` parameter flows through: `/consumer/business/123`
- Referral attributed to **business**
- `referred_by_workplace_id` is set

## URL Patterns

### Search Results Page:
```
/search?q=haircut&type=professional&location=San%20Francisco
/search?q=salon&type=business&location=CA
/search?type=professional&location=94102
```

Parameters are:
- **Shareable**: Copy URL to share search results
- **Bookmarkable**: Save searches for later
- **SEO-friendly**: Clean parameter structure

## Mobile Responsive

The search interface adapts for mobile:
- Search box stacks vertically
- Cards display in single column
- Touch-friendly buttons
- Location button easily accessible
- Smooth scrolling results

## Performance Considerations

### Query Optimization:
1. **Limit Results**: Default 20, max configurable
2. **Indexed Fields**: Search on indexed columns (name, city, state)
3. **Lazy Loading**: Could add pagination for 100+ results
4. **Caching**: Consider caching popular searches

### Database Queries:
- Professional search: 3-4 queries (specialists, services, workplaces, associations)
- Business search: 3-4 queries (workplaces, associations, specialists, services)
- All queries use proper indexes and JOIN optimization

## Future Enhancements

1. **Autocomplete**: Suggest services/names as user types
2. **Filters**: Price range, ratings, availability
3. **Sort Options**: Distance, price, rating, availability
4. **Map View**: Show results on interactive map
5. **Save Searches**: Let users save favorite searches
6. **Search History**: Remember recent searches
7. **Radius Search**: Search within X miles of location
8. **Featured Results**: Promoted listings at top
9. **Reviews Integration**: Show ratings in results
10. **Calendar Integration**: Show next available appointment

## Testing

### Test Scenarios:

**Professional Search:**
```bash
# Search by service
GET /search?query=haircut&search_type=professional

# Search by location
GET /search?search_type=professional&location=San%20Francisco

# Search by service and location
GET /search?query=massage&search_type=professional&city=SF&state=CA
```

**Business Search:**
```bash
# Search by business name
GET /search?query=salon&search_type=business

# Search by location
GET /search?search_type=business&location=California

# Search by service (finds businesses offering it)
GET /search?query=haircut&search_type=business&city=SF
```

### Manual Testing:
1. Visit `/search`
2. Try each search type
3. Test location autocomplete
4. Test GPS location button
5. Verify results display correctly
6. Click through to professional/business pages
7. Complete a booking to verify referral tracking

## Analytics Opportunities

Track search metrics:
- Most searched services
- Popular locations
- Professional vs Business search ratio
- Click-through rates
- Conversion from search to booking
- Average time from search to booking

## Files Modified/Created

### New Files:
- `templates/search.html` - Search interface

### Modified Files:
- `main.py` - Added `/search` endpoint and route
- `index.html` - Added search links
- `consumer.html` - Added "Advanced Search" button

## Dependencies

- No new dependencies required
- Uses existing database models
- Leverages existing workplace associations
- Compatible with referral tracking system

## Launch Checklist

- [x] Search endpoint implemented
- [x] Professional search working
- [x] Business search working
- [x] Location filtering functional
- [x] Search UI created
- [x] Mobile responsive
- [x] URL parameters working
- [x] Integration with booking flow
- [x] Referral tracking compatible
- [x] Empty states handled
- [x] Loading states implemented
- [ ] Add tests
- [ ] Monitor performance
- [ ] Gather user feedback

## Ready to Use!

The advanced search feature is fully implemented and ready for testing. Visit:
- **Homepage**: http://localhost:8000/ (see search button)
- **Search Page**: http://localhost:8000/search
- **Consumer Page**: http://localhost:8000/consumer (see advanced search button)

Try searching for services, professionals, or businesses by location!
