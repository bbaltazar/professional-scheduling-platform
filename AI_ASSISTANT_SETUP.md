# AI Assistant Setup Guide

The calendar app now includes an AI-powered message drafting assistant powered by Google Gemini.

## Features

- **Draft Reschedule Messages**: Automatically generate professional rescheduling messages for appointments
- **Draft Confirmation Messages**: Create friendly confirmation messages with appointment details
- **Smart Context**: AI understands the booking details (client, service, time) and generates personalized messages
- **Copy to Clipboard**: Easy one-click copying of generated messages

## Setup Instructions

### 1. Get a Gemini API Key (FREE)

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Get API Key" or "Create API Key"
4. Copy the API key

**Note**: Gemini has a generous free tier:
- 15 requests per minute
- 1,500 requests per day
- Perfect for small to medium professional practices

### 2. Add API Key to Environment

Add the following to your `.env` file:

```bash
GEMINI_API_KEY=your_api_key_here
```

Or set it as an environment variable:

```bash
export GEMINI_API_KEY=your_api_key_here
```

### 3. Restart the Server

```bash
./start.sh
```

## Usage

### From the Bookings Tab:

1. Go to the **Bookings** tab in your professional dashboard
2. Find a confirmed booking
3. Click the **✉️ Draft Message** button
4. Choose message type:
   - **Reschedule Request**: For when you need to change the appointment
   - **Appointment Confirmation**: For confirming upcoming appointments
5. Fill in optional fields:
   - Reason for rescheduling (e.g., "Unexpected scheduling conflict")
   - Suggested alternative times (one per line)
6. Click **✨ Generate Message**
7. Review the AI-generated message
8. Click **📋 Copy to Clipboard** to copy
9. Paste into your email client or SMS app

### Example Workflow:

**Rescheduling an appointment:**
1. Open booking for "John Smith - Haircut on 2/28 at 2:00 PM"
2. Click "Draft Message"
3. Select "Reschedule Request"
4. Enter reason: "Family emergency"
5. Enter alternatives:
   ```
   Friday 3/1 at 3:00 PM
   Monday 3/4 at 10:00 AM
   ```
6. Generate message
7. AI creates a professional, empathetic message
8. Copy and send to client

## What the AI Does

The AI assistant:
- Uses booking details (client name, service, date/time, professional name)
- Crafts professional, empathetic messages
- Maintains your professional tone
- Includes relevant details and alternatives
- Generates appropriate subject lines
- Handles edge cases gracefully (missing data, API failures)

## Fallback Behavior

If the API key is not set or the API is unavailable:
- The system will show an error message
- A basic template message is provided as fallback
- No functionality is broken - you can still manage bookings normally

## Privacy & Security

- Messages are generated on-demand (not stored)
- Client data is sent to Google's API only when you click "Generate"
- No message content is logged or persisted
- API key is stored securely in environment variables

## Cost

With Gemini's free tier:
- **0-50 messages/day**: FREE
- **51-1,500 messages/day**: FREE
- **1,500+ messages/day**: You'll need to upgrade (but this is A LOT of messages)

For most professional practices, you'll never hit the free tier limits.

## Troubleshooting

### "AI assistant not configured" error

**Solution**: Make sure `GEMINI_API_KEY` is set in your `.env` file and restart the server.

### "Failed to generate message" error

**Possible causes**:
1. Invalid API key - check it's correct
2. Rate limit exceeded - wait a minute and try again
3. Network issues - check your internet connection

### Messages are too formal/informal

The AI is trained to be professional but warm. If you want different tone:
- Edit the generated message before sending
- Click "Regenerate" for a new variation
- The AI learns from the context of your service and booking details

## Future Enhancements

Planned features:
- SMS integration (send directly from app)
- Email integration (send directly from app)
- Message templates and customization
- Tone adjustment (formal, casual, friendly)
- Multi-language support
