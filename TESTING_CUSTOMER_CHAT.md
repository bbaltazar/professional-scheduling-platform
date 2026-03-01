# Testing the Terminal Customer Chat Feature

## Overview
When you cancel a booking, the system will automatically start a conversation with the customer in your **terminal/console** where the server is running. This simulates what would happen with real SMS/email integration.

## How to Test

### 1. Start Your Server
```bash
./start.sh
```

Keep the terminal visible so you can see the conversation output.

### 2. Log into Professional Dashboard
- Go to http://127.0.0.1:8000/professional
- Log in with your credentials

### 3. Cancel a Booking

#### Option A: Via Dashboard UI
1. Go to the **Bookings** tab
2. Find a confirmed booking
3. Click **"Cancel Booking"** button
4. Enter a cancellation reason (e.g., "Family emergency", "Double booked")
5. Submit

#### Option B: Via API
```bash
curl -X PUT http://127.0.0.1:8000/booking/123/status \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "status": "cancelled",
    "notes": "Unexpected scheduling conflict"
  }'
```

### 4. Check Your Terminal

You should see output like this in your server terminal:

```
================================================================================
📱 TERMINAL CUSTOMER CHAT SIMULATOR
================================================================================

👤 Customer: John Smith
📧 Email: john.smith@example.com
📞 Phone: +14155551234

📅 Cancelled Appointment:
   Service: Haircut
   Date/Time: Friday, March 1 at 2:00 PM
   Professional: Sarah Johnson
   Reason: Family emergency

--------------------------------------------------------------------------------

💬 FROM SARAH JOHNSON:
Hi John,

I sincerely apologize, but I need to cancel your Haircut appointment
scheduled for Friday, March 1 at 2:00 PM.

Family emergency

I'd love to reschedule with you. Here are your options:

1. Same time next week: Friday, March 8 at 2:00 PM
2. Next available: Monday, March 4 at 10:00 AM
3. Next available: Tuesday, March 5 at 3:00 PM

4. View my full calendar and book yourself:
   http://127.0.0.1:8000/consumer/book/1

Please reply with your preferred option number, or let me know if you'd
like to discuss other times that work better for you.

Thank you for your understanding,
- Sarah Johnson

--------------------------------------------------------------------------------

💬 AWAITING CUSTOMER RESPONSE...
   (In production, this would be sent via SMS/Email and wait for reply)

================================================================================
```

## What the System Does

1. **Captures Customer Details**: Shows who you're contacting (name, email, phone)
2. **Shows Appointment Info**: Displays what was cancelled (service, date, time)
3. **Apologizes**: Professional tone with your cancellation reason
4. **Offers Alternatives**:
   - Same time next week (if available)
   - Next 2-3 available time slots
   - Link to self-book from calendar
5. **Logs Conversation**: Returns metadata for tracking

## Future Integration

This terminal output is exactly what will be sent via:
- **Twilio SMS** (when you add `TWILIO_ACCOUNT_SID` and `TWILIO_AUTH_TOKEN`)
- **Email** (via SendGrid, Mailgun, or similar)

The conversation structure is already built - just need to swap the `print()` statements with actual API calls.

## Testing Different Scenarios

### Test 1: Cancellation with Availability
- Cancel a booking for this week
- Should show alternative times

### Test 2: Cancellation Far in Future
- Cancel a booking 2+ weeks out
- Should show same time next week option

### Test 3: Cancellation with Reason
- Provide detailed reason: "Unexpected family emergency"
- Should include reason in message

### Test 4: Cancellation Without Reason
- Leave reason blank
- Should still work with generic apology

## Customization

You can customize the conversation in `src/calendar_app/customer_chat.py`:
- Message tone and wording
- Number of alternative slots offered
- Format of date/time display
- Booking URL structure

## Notes

- Conversation only triggers when status changes TO 'cancelled' (not if already cancelled)
- Requires authentication (specialist must own the booking)
- Works with any booking that has client email
- Finds alternatives based on your actual availability in the calendar
