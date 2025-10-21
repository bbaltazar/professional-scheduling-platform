# CSV Client Upload Feature

## Overview
Professionals can now bulk import their client list by uploading a CSV file in the "Your Clients" section.

## How to Use

1. Navigate to the **Your Clients** tab in your professional dashboard
2. Click the **Upload CSV** button (next to the Refresh button)
3. In the modal that appears, click **Choose CSV File**
4. Select your CSV file
5. Click **Upload Clients**

## CSV File Format

Your CSV file should contain client information with the following columns:

```csv
name,email,phone
John Smith,john.smith@example.com,555-0100
Jane Doe,jane.doe@example.com,555-0200
Michael Johnson,michael.j@example.com,555-0300
```

### Column Details:

- **email** (Required): Client's email address. Used as unique identifier.
- **name** (Optional): Client's full name. If not provided, uses email prefix.
- **phone** (Optional): Client's phone number. Any format accepted.

### CSV File Requirements:

✅ **Accepted:**
- With or without header row (auto-detected)
- Various CSV formats (comma-separated values)
- UTF-8 encoding
- Empty optional fields
- Extra spaces (auto-trimmed)

❌ **Rejected:**
- Missing email addresses
- Invalid email format (must contain @ and .)
- Non-CSV file types
- Non-UTF-8 encoding

## Features

### Duplicate Handling
- Clients with existing email addresses are automatically skipped
- No overwriting of existing client data
- Shows count of skipped duplicates in results

### Error Reporting
- Invalid rows are skipped with error messages
- Shows first 10 errors for review
- Provides summary of successful imports

### Automatic Profile Creation
- Creates Consumer records in database
- Creates ClientProfile records linking to your specialist account
- Clients immediately appear in your client list
- Ready for adding rankings, notes, and bio

## Example Files

### Basic CSV (with header)
```csv
name,email,phone
John Smith,john@example.com,555-0100
Jane Doe,jane@example.com,555-0200
```

### CSV (without header)
```csv
John Smith,john@example.com,555-0100
Jane Doe,jane@example.com,555-0200
```

### CSV (email only)
```csv
email
john@example.com
jane@example.com
```

### CSV (minimal - just emails)
```csv
john@example.com
jane@example.com
```

## Upload Results

After upload, you'll see a summary showing:
- ✅ Number of clients successfully added
- ⏭️ Number of duplicates skipped
- ⚠️ Number of rows with errors (if any)
- 📊 Total rows processed

The client list will automatically refresh to show your new clients.

## Technical Details

### Backend Endpoint
```
POST /professional/clients/upload-csv?specialist_id={id}
```

### Database Operations
1. Checks for existing Consumer by email
2. Creates new Consumer if not found
3. Creates ClientProfile linking Consumer to Specialist
4. Skips if ClientProfile already exists
5. All operations in single transaction (all-or-nothing)

### Security
- Validates specialist_id
- Checks file type (.csv only)
- Validates email format
- UTF-8 encoding validation
- Transaction rollback on errors

## Troubleshooting

**Q: Upload fails with "File encoding error"**
A: Save your CSV file with UTF-8 encoding. In Excel: Save As > CSV UTF-8

**Q: Some rows are skipped**
A: Check error messages in upload results. Common issues:
   - Missing email address
   - Invalid email format
   - Empty rows

**Q: Duplicates not showing in my list**
A: Duplicates (by email) are automatically skipped to prevent double-entries

**Q: Client names showing as email prefixes**
A: This happens when the name column is empty. The system uses the part before @ as the name.

## Sample CSV File

A sample CSV file is included in the project root: `sample_clients.csv`

You can use this file to test the upload feature with 8 sample clients.
