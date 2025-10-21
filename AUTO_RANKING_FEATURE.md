# Auto-Ranking Feature for Client Management

## Overview
Clients are now automatically assigned rankings based on when they're added to your client list. This provides a chronological ordering system that reflects the order in which you acquired each client.

## How Auto-Ranking Works

### 1. **First Booking Creates Rank**
When a new client books an appointment for the first time:
- A `ClientProfile` is automatically created
- The client receives the next available rank number
- Example: If you have 5 ranked clients, the new client gets rank #6

### 2. **Manual Profile Creation**
When you view or edit a client's profile for the first time:
- If no rank exists, the next available rank is automatically assigned
- You can change the rank manually at any time

### 3. **CSV Upload Respects Row Order**
When you upload a CSV file with multiple clients:
- Clients are ranked sequentially based on their row order in the CSV
- The ranking continues from your highest existing rank
- Example: If you have clients ranked 1-5, uploading a CSV with 3 clients will rank them 6, 7, 8

## Examples

### Example 1: Starting from Scratch
```
Initial state: No clients

Action: Client "John Smith" books first appointment
Result: John Smith = Rank #1

Action: Client "Jane Doe" books second appointment
Result: Jane Doe = Rank #2

Current rankings:
#1 - John Smith
#2 - Jane Doe
```

### Example 2: CSV Upload
```
Current rankings:
#1 - John Smith
#2 - Jane Doe

Action: Upload CSV with 5 clients:
  Row 1: Michael Johnson
  Row 2: Sarah Williams
  Row 3: David Brown
  Row 4: Emily Davis
  Row 5: Robert Miller

Result:
#1 - John Smith (unchanged)
#2 - Jane Doe (unchanged)
#3 - Michael Johnson (from CSV row 1)
#4 - Sarah Williams (from CSV row 2)
#5 - David Brown (from CSV row 3)
#6 - Emily Davis (from CSV row 4)
#7 - Robert Miller (from CSV row 5)
```

### Example 3: Manual Adjustment
```
Current rankings:
#1 - John Smith
#2 - Jane Doe
#3 - Michael Johnson

Action: Change John Smith's rank from #1 to #10
Result:
#2 - Jane Doe
#3 - Michael Johnson
#10 - John Smith

Action: New client "Bob Jones" books
Result: Bob Jones = Rank #11 (next after highest rank 10)
```

## Technical Details

### Database
- Rankings are stored in the `score` field of `ClientProfile`
- The `score` field is now interpreted as a ranking (1 = top priority)
- Lower numbers = higher priority clients

### Helper Function
```python
def get_next_client_rank(db: Session, specialist_id: int) -> int:
    """
    Get the next available rank for a new client.
    Returns the highest existing rank + 1, or 1 if no clients exist.
    """
    max_rank = (
        db.query(func.max(ClientProfile.score))
        .filter(ClientProfile.specialist_id == specialist_id)
        .scalar()
    )
    return (max_rank or 0) + 1
```

### Auto-Ranking Locations

1. **New Booking** (`create_booking` endpoint)
   ```python
   # Auto-create client profile with next available rank
   next_rank = get_next_client_rank(db, booking.specialist_id)
   client_profile = ClientProfile(
       specialist_id=booking.specialist_id,
       consumer_id=consumer.id,
       score=next_rank,
       ...
   )
   ```

2. **Profile Update** (`update_client_profile` endpoint)
   ```python
   if not profile:
       # Create new profile with auto-ranking if score not provided
       if score is None:
           score = get_next_client_rank(db, specialist_id)
   ```

3. **CSV Upload** (`upload_clients_csv` endpoint)
   ```python
   # Get starting rank for CSV upload
   starting_rank = get_next_client_rank(db, specialist_id)
   current_rank = starting_rank
   
   # For each row:
   profile = ClientProfile(
       score=current_rank,  # Rank based on CSV row order
       ...
   )
   current_rank += 1  # Increment for next client
   ```

## CSV Upload Response

The CSV upload now returns ranking information:

```json
{
  "message": "CSV processed successfully",
  "created": 5,
  "skipped": 2,
  "total_rows": 7,
  "starting_rank": 3,
  "ending_rank": 7,
  "errors": []
}
```

### UI Display
```
✅ Upload Successful!
• 5 clients added
• 2 duplicates skipped
• 7 total rows processed
• Ranked 3 to 7
```

## Benefits

### 1. **Chronological Order**
- Automatically tracks the order clients were added
- No manual ranking needed for new clients
- Preserves acquisition timeline

### 2. **CSV Import Intelligence**
- Respects the order you've arranged in your CSV
- Allows you to pre-order clients before import
- Maintains sequence across batches

### 3. **Flexible Adjustment**
- Auto-ranking provides a starting point
- You can manually adjust any rank at any time
- System continues to work correctly after manual changes

### 4. **No Gaps**
- Rankings automatically continue from highest number
- No confusion about what rank to assign next
- Clean sequential numbering

## Use Cases

### Scenario 1: Priority by First Contact
Let the auto-ranking system track who contacted you first. Your longest-standing clients naturally get lower rank numbers.

### Scenario 2: Batch Import with Pre-Ordering
Arrange your CSV clients in order of importance before uploading:
```csv
name,email,phone
VIP Client One,vip1@example.com,555-0001
VIP Client Two,vip2@example.com,555-0002
Regular Client,regular@example.com,555-0003
```
They'll be ranked in that exact order!

### Scenario 3: Historical Records
Import old client lists in chronological order to maintain your historical client acquisition timeline.

## Best Practices

### ✅ DO:
- Let the system auto-rank new clients initially
- Adjust ranks manually only when needed
- Order your CSV files intentionally before upload
- Use ranking to reflect client priority/importance

### ❌ DON'T:
- Worry about gaps in ranking numbers (they're fine)
- Manually assign ranks to every new client
- Delete and re-add clients to change ranks (just edit the rank)

## Migration Notes

**For Existing Clients:**
- Clients without rankings will get auto-ranked when:
  - Their profile is viewed/edited
  - They book a new appointment
  - You manually update their profile

**Backward Compatibility:**
- Existing manually-set rankings are preserved
- System continues from the highest existing rank
- No data migration needed

## Technical Implementation Summary

| Event | Auto-Rank Behavior |
|-------|-------------------|
| New booking (first-time client) | ✅ Auto-ranked (next available) |
| Profile created manually | ✅ Auto-ranked if score not provided |
| Profile updated manually | ⏭️ Skipped (preserves manual setting) |
| CSV upload | ✅ Auto-ranked (sequential from next available) |
| Existing client re-books | ⏭️ Skipped (keeps existing rank) |

## Code Locations

- **Helper Function**: `main.py` line ~3278
- **Booking Creation**: `main.py` line ~2160
- **Profile Update**: `main.py` line ~3570
- **CSV Upload**: `main.py` line ~3700-3800
- **Frontend Display**: `professional.html` line ~4050

## Testing

### Test 1: Fresh Start
1. Start with no clients
2. Create first booking → Check rank = 1
3. Create second booking → Check rank = 2

### Test 2: CSV Upload
1. Start with 2 ranked clients (ranks 1, 2)
2. Upload CSV with 5 clients
3. Verify ranks 3, 4, 5, 6, 7 assigned
4. Check upload response shows "Ranked 3 to 7"

### Test 3: Manual Override
1. Client has auto-rank #5
2. Manually change to #20
3. Add new client
4. Verify new client gets #21 (not #6)

## Summary

The auto-ranking feature provides intelligent, chronological client ordering while maintaining flexibility for manual adjustments. CSV uploads respect row order, making bulk imports intuitive and predictable. The system works seamlessly across all client addition methods.

---

**Key Takeaway:** You never need to think about what rank to assign—the system does it automatically based on order of addition, while always allowing manual adjustment when needed.
