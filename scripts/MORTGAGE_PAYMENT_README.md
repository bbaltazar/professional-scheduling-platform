# Automated Mortgage Payment Script

This script automates the mortgage payment process on portal.hoaorganizers.com using Selenium WebDriver.

## Prerequisites

1. **Python 3.7+** installed
2. **Chrome browser** installed
3. **ChromeDriver** installed (or use selenium manager which auto-downloads)

## Installation

1. Install required Python packages:
```bash
pip install selenium
```

2. Set up your environment variables by creating `.env.mortgage` file:
```bash
cp .env.mortgage.example .env.mortgage
```

3. Edit `.env.mortgage` with your actual credentials:
```bash
# Edit the file with your actual values
nano .env.mortgage
```

Or set them directly in your terminal:
```bash
export MORTGAGE_EMAIL="your.email@example.com"
export MORTGAGE_PASSWORD="your_password_here"
export MORTGAGE_PHONE="1234567890"
export MORTGAGE_ROUTING_NUMBER="123456789"
export MORTGAGE_ACCOUNT_NUMBER="1234567890"
```

## Usage

### Option 1: Run with environment file
```bash
# Load environment variables
source .env.mortgage

# Run the script
python scripts/pay_mortgage.py
```

### Option 2: Run with inline environment variables
```bash
MORTGAGE_EMAIL="your@email.com" \
MORTGAGE_PASSWORD="yourpass" \
MORTGAGE_PHONE="1234567890" \
MORTGAGE_ROUTING_NUMBER="123456789" \
MORTGAGE_ACCOUNT_NUMBER="1234567890" \
python scripts/pay_mortgage.py
```

### Option 3: Make it executable and run directly
```bash
chmod +x scripts/pay_mortgage.py
source .env.mortgage
./scripts/pay_mortgage.py
```

## Headless Mode

To run the script without opening a visible browser window, uncomment this line in the script:
```python
chrome_options.add_argument('--headless')
```

## Scheduling with Cron

To automate monthly payments, add to your crontab:

```bash
# Edit crontab
crontab -e

# Add this line to run on the 1st of every month at 9 AM
0 9 1 * * cd /Users/brianabaltazar/SoftwareEngineering/apps/calendar_app && source .env.mortgage && /usr/bin/python3 scripts/pay_mortgage.py >> /tmp/mortgage_payment.log 2>&1
```

## Screenshots

The script automatically saves screenshots:
- **Success**: `/tmp/mortgage_payment_YYYYMMDD_HHMMSS.png`
- **Error**: `/tmp/mortgage_error_YYYYMMDD_HHMMSS.png`

## Troubleshooting

### ChromeDriver Issues
If you get ChromeDriver errors, install it manually:
```bash
# On macOS with Homebrew
brew install chromedriver

# Or download from: https://chromedriver.chromium.org/
```

### Element Not Found
If the script fails to find elements, the website structure may have changed. You can:
1. Run without headless mode to see what's happening
2. Check the error screenshot in `/tmp/`
3. Update the selectors in the script

### Timeout Errors
If steps are timing out, increase the timeout values in `wait_and_click()` and `wait_and_send_keys()` calls.

## Security Notes

⚠️ **IMPORTANT**: 
- Never commit `.env.mortgage` to git (it's in .gitignore)
- Keep your credentials secure
- Consider using a password manager or secrets vault
- Review the script before running to ensure it matches the current website

## What the Script Does

1. Opens Chrome browser
2. Navigates to login page
3. Clicks "Log in with password"
4. Enters email and password
5. Logs in
6. Clicks "Make online payment"
7. Enters phone number
8. Selects "Pay by eCheck"
9. Enters routing number
10. Enters account number (twice for confirmation)
11. Checks the agreement checkbox
12. Clicks "Next"
13. Clicks "Submit Payment"
14. Waits for confirmation
15. Takes a screenshot
16. Closes browser

## License

Personal use only. Use at your own risk.
