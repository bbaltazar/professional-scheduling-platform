# CSV Upload Validation Update

## Changes Made

### Updated Requirements
**OLD:**
- Email is required (used to identify unique clients)
- Name is optional (will use email prefix if missing)
- Phone is optional
- Header row is optional (auto-detected)
- Duplicate emails will be skipped

**NEW:**
- Name is required
- Email OR Phone must be filled

## Files Modified

### 1. Frontend (`src/calendar_app/templates/professional.html`)
**Location:** Lines ~1862-1878 (modal instructions)

**Changed:**
```html
<!-- OLD -->
<li><strong>Email</strong> is required (used to identify unique clients)</li>
<li><strong>Name</strong> is optional (will use email prefix if missing)</li>
<li><strong>Phone</strong> is optional</li>
<li>Header row is optional (auto-detected)</li>
<li>Duplicate emails will be skipped</li>

<!-- NEW -->
<li><strong>Name</strong> is required</li>
<li><strong>Email</strong> OR <strong>Phone</strong> must be filled</li>
```

### 2. Backend (`src/calendar_app/main.py`)
**Location:** Lines ~3650-3730

#### Docstring Update
```python
# OLD
"""
Upload a CSV file to bulk import clients.
Expected CSV format: name,email,phone
- Header row is optional (will be auto-detected)
- Email is required, name and phone are optional
- Duplicates (by email) will be skipped
- Creates Consumer records and ClientProfile records
"""

# NEW
"""
Upload a CSV file to bulk import clients.
Expected CSV format: name,email,phone
- Header row is optional (will be auto-detected)
- Name is required
- Email OR Phone must be provided (at least one)
- Duplicates (by email or phone) will be skipped
- Creates Consumer records and ClientProfile records
"""
```

#### Validation Logic Update
```python
# OLD - Email was required
if not email:
    errors.append(f"Row {idx}: Missing email")
    skipped_count += 1
    continue

# NEW - Name is required, Email OR Phone required
# Validate: Name is required
if not name:
    errors.append(f"Row {idx}: Missing name")
    skipped_count += 1
    continue

# Validate: Email OR Phone must be provided
if not email and not phone:
    errors.append(f"Row {idx}: Must provide email OR phone")
    skipped_count += 1
    continue

# Validate email format if provided
if email and ("@" not in email or "." not in email):
    errors.append(f"Row {idx}: Invalid email format '{email}'")
    skipped_count += 1
    continue
```

#### Duplicate Detection Update
```python
# OLD - Only checked by email
existing_consumer = (
    db.query(Consumer).filter(Consumer.email == email).first()
)

# NEW - Checks by email OR phone
existing_consumer = None
if email:
    existing_consumer = (
        db.query(Consumer).filter(Consumer.email == email).first()
    )
if not existing_consumer and phone:
    existing_consumer = (
        db.query(Consumer).filter(Consumer.phone == phone).first()
    )
```

#### Consumer Creation Update
```python
# OLD - Used email prefix as fallback name
consumer_name = name if name else email.split("@")[0]
consumer = Consumer(name=consumer_name, email=email, phone=phone)

# NEW - Name is always provided (validated earlier)
consumer = Consumer(name=name, email=email, phone=phone)
```

### 3. Sample Data (`sample_clients.csv`)

**Updated to demonstrate new flexibility:**
```csv
name,email,phone
John Smith,john.smith@example.com,555-0100    # Both email and phone
Jane Doe,jane.doe@example.com,555-0200        # Both email and phone
Michael Johnson,michael.j@example.com,555-0300 # Both email and phone
Sarah Williams,,555-0400                       # Phone only (no email)
David Brown,david.brown@example.com,555-0500   # Both email and phone
Emily Davis,emily.davis@example.com,           # Email only (no phone)
Robert Miller,,555-0700                        # Phone only (no email)
Jessica Wilson,jessica.wilson@example.com,555-0800 # Both email and phone
```

Shows three valid patterns:
1. Name + Email + Phone (most common)
2. Name + Email only (row 6)
3. Name + Phone only (rows 4, 7)

## Validation Rules Summary

### ✅ Valid Rows:
- `John Smith,john@example.com,555-1234` - All fields
- `Jane Doe,jane@example.com,` - Name + Email only
- `Bob Jones,,555-5678` - Name + Phone only

### ❌ Invalid Rows:
- `,john@example.com,555-1234` - Missing name
- `John Smith,,` - Missing both email and phone
- `Jane Doe,invalid-email,` - Invalid email format (no @ or .)

## Error Messages

**New error messages users will see:**

1. Missing name:
   ```
   Row 5: Missing name
   ```

2. Missing both email and phone:
   ```
   Row 7: Must provide email OR phone
   ```

3. Invalid email format (when provided):
   ```
   Row 3: Invalid email format 'notanemail'
   ```

## Testing

### Test Cases

1. **Valid: Name + Email + Phone**
   ```csv
   John Smith,john@example.com,555-1234
   ```
   ✅ Should create client

2. **Valid: Name + Email only**
   ```csv
   Jane Doe,jane@example.com,
   ```
   ✅ Should create client

3. **Valid: Name + Phone only**
   ```csv
   Bob Jones,,555-5678
   ```
   ✅ Should create client

4. **Invalid: Missing Name**
   ```csv
   ,john@example.com,555-1234
   ```
   ❌ Error: "Row X: Missing name"

5. **Invalid: Missing both Email and Phone**
   ```csv
   John Smith,,
   ```
   ❌ Error: "Row X: Must provide email OR phone"

6. **Invalid: Bad email format**
   ```csv
   Jane Doe,notanemail,
   ```
   ❌ Error: "Row X: Invalid email format 'notanemail'"

## Benefits of New Validation

1. **More Flexible**: Can add clients with just phone numbers
2. **More Practical**: Reflects real-world scenarios where you might not have email
3. **Better Data Quality**: Ensures you always have a name (most important for display)
4. **Proper Contact**: Ensures at least one method to reach the client

## Migration Notes

- **No database changes required**
- **Backward compatible**: Old CSVs with all three fields still work
- **New capability**: Can now import phone-only clients
- **Stricter**: Now requires name (was optional before)

## Server Status

✅ Server running with auto-reload on http://localhost:8000
✅ Changes applied and active
✅ Ready for testing

## Quick Test

Upload `sample_clients.csv` to test all three valid patterns in one upload!
