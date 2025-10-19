#!/bin/bash
# Simple startup script for the Calendar Booking App

echo "🚀 Starting Calendar Booking App..."
echo "📍 Project: /Users/brianabaltazar/SoftwareEngineering/apps/calendar_app"
echo ""

cd /Users/brianabaltazar/SoftwareEngineering/apps/calendar_app

# Check if poetry is available
if ! command -v poetry &> /dev/null; then
    echo "❌ Poetry not found. Please install Poetry first."
    exit 1
fi

echo "✅ Using Poetry environment"
echo "🌐 Starting server on http://127.0.0.1:8000"
echo ""
echo "Access Points:"
echo "  👔 Professional: http://127.0.0.1:8000/professional"
echo "  🛍️  Consumer:     http://127.0.0.1:8000/consumer"
echo "  📚 API Docs:     http://127.0.0.1:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

poetry run uvicorn src.calendar_app.main:app --reload --host 127.0.0.1 --port 8000
