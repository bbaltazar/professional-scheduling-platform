#!/bin/bash
# Delete the Sunday-only recurring schedule (ID 821) and all its instances

SPECIALIST_ID=6
SCHEDULE_ID=821

echo "Deleting recurring schedule ID $SCHEDULE_ID (Sunday-only)..."

curl -X DELETE "http://localhost:8000/specialist/${SPECIALIST_ID}/calendar/events/${SCHEDULE_ID}?delete_series=true" \
  -H "Content-Type: application/json"

echo ""
echo "Done! Restart the server and check the consumer booking page."
