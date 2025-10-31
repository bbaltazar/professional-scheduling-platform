#!/usr/bin/env python3
"""
Quick script to add the missing imports to main.py
"""

import re

# Read the file
with open('src/calendar_app/main.py', 'r') as f:
    content = f.read()

# Find the first BookingStatusUpdate, import location and add our imports after it
pattern = r'(        BookingStatusUpdate,\n)(        # Calendar models)'
replacement = r'\1        AppointmentSessionCreate,\n        AppointmentSessionUpdate,\n        AppointmentSessionResponse,\n        ClientDurationInsight,\n        ServiceDurationInsight,\n        DurationRecommendation,\n\2'

content = re.sub(pattern, replacement, content, count=1)

# Write back
with open('src/calendar_app/main.py', 'w') as f:
    f.write(content)

print("✅ Imports added successfully!")
