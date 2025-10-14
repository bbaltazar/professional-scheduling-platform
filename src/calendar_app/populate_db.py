#!/usr/bin/env python3
"""
Populate the database with fake professionals for testing consumer functionality.
"""

import requests
import json
from datetime import date, time, timedelta
from typing import List

BASE_URL = "http://127.0.0.1:8001"

# Fake professional data
FAKE_PROFESSIONALS = [
    {
        "name": "Dr. Sarah Johnson",
        "email": "sarah.johnson@healthcenter.com",
        "bio": "General practitioner with 15 years of experience. Specializes in preventive care and family medicine.",
        "phone": "+1-555-0101",
        "services": [
            {"name": "General Consultation", "price": 150.0, "duration": 30},
            {"name": "Physical Exam", "price": 200.0, "duration": 45},
            {"name": "Follow-up Visit", "price": 100.0, "duration": 15},
        ],
    },
    {
        "name": "Dr. Michael Chen",
        "email": "michael.chen@dentalcare.com",
        "bio": "Experienced dentist specializing in cosmetic and preventive dentistry. State-of-the-art equipment.",
        "phone": "+1-555-0102",
        "services": [
            {"name": "Teeth Cleaning", "price": 120.0, "duration": 60},
            {"name": "Dental Exam", "price": 80.0, "duration": 30},
            {"name": "Filling", "price": 200.0, "duration": 45},
            {"name": "Teeth Whitening", "price": 350.0, "duration": 90},
        ],
    },
    {
        "name": "Lisa Rodriguez, LMFT",
        "email": "lisa.rodriguez@therapy.com",
        "bio": "Licensed marriage and family therapist. Specializes in anxiety, depression, and relationship counseling.",
        "phone": "+1-555-0103",
        "services": [
            {"name": "Individual Therapy", "price": 180.0, "duration": 50},
            {"name": "Couples Therapy", "price": 220.0, "duration": 60},
            {"name": "Initial Consultation", "price": 200.0, "duration": 60},
        ],
    },
    {
        "name": "David Park, PT",
        "email": "david.park@physicaltherapy.com",
        "bio": "Physical therapist specializing in sports injuries and rehabilitation. Former collegiate athlete.",
        "phone": "+1-555-0104",
        "services": [
            {"name": "Physical Therapy Session", "price": 160.0, "duration": 45},
            {"name": "Initial Assessment", "price": 200.0, "duration": 60},
            {"name": "Sports Injury Consultation", "price": 180.0, "duration": 30},
        ],
    },
    {
        "name": "Amanda Thompson, RD",
        "email": "amanda.thompson@nutrition.com",
        "bio": "Registered dietitian with expertise in weight management and sports nutrition. Personalized meal plans.",
        "phone": "+1-555-0105",
        "services": [
            {"name": "Nutrition Consultation", "price": 140.0, "duration": 45},
            {"name": "Meal Plan Development", "price": 200.0, "duration": 60},
            {"name": "Follow-up Session", "price": 100.0, "duration": 30},
        ],
    },
]


def create_availability_for_professional(
    specialist_id: int, start_date: date, num_days: int = 14
):
    """Create availability slots for a professional for the next num_days days."""
    availability_slots = []

    for day_offset in range(num_days):
        current_date = start_date + timedelta(days=day_offset)

        # Skip weekends for some variety
        if current_date.weekday() >= 5:  # Saturday = 5, Sunday = 6
            continue

        # Morning availability (9 AM - 12 PM)
        availability_slots.append(
            {
                "date": current_date.isoformat(),
                "start_time": "09:00:00",
                "end_time": "12:00:00",
            }
        )

        # Afternoon availability (1 PM - 5 PM)
        availability_slots.append(
            {
                "date": current_date.isoformat(),
                "start_time": "13:00:00",
                "end_time": "17:00:00",
            }
        )

    return availability_slots


def populate_database():
    print("Populating database with fake professionals...")
    print("=" * 50)

    start_date = date.today()

    for i, prof_data in enumerate(FAKE_PROFESSIONALS, 1):
        print(f"\n{i}. Creating {prof_data['name']}...")

        # Create specialist
        specialist_data = {
            "name": prof_data["name"],
            "email": prof_data["email"],
            "bio": prof_data["bio"],
            "phone": prof_data["phone"],
        }

        response = requests.post(f"{BASE_URL}/specialist/", json=specialist_data)
        if response.status_code != 200:
            print(f"   ✗ Failed to create specialist: {response.text}")
            continue

        specialist = response.json()
        specialist_id = specialist["id"]
        print(f"   ✓ Created specialist (ID: {specialist_id})")

        # Add services
        services_data = prof_data["services"]
        response = requests.put(
            f"{BASE_URL}/specialist/{specialist_id}/services", json=services_data
        )
        if response.status_code != 200:
            print(f"   ✗ Failed to add services: {response.text}")
            continue

        print(f"   ✓ Added {len(services_data)} services")

        # Add availability
        availability_data = create_availability_for_professional(
            specialist_id, start_date
        )
        response = requests.post(
            f"{BASE_URL}/specialist/{specialist_id}/availability",
            json=availability_data,
        )
        if response.status_code != 200:
            print(f"   ✗ Failed to add availability: {response.text}")
            continue

        print(f"   ✓ Added {len(availability_data)} availability slots")

    print(f"\n{'='*50}")
    print("✓ Database population complete!")
    print("\nYou can now:")
    print("1. Browse professionals at: GET /catalog/specialists")
    print("2. View availability at: GET /specialist/{id}/availability/{date}")
    print("3. Make bookings at: POST /booking/")
    print("4. View the API docs at: http://127.0.0.1:8001/docs")


if __name__ == "__main__":
    try:
        populate_database()
    except requests.exceptions.ConnectionError:
        print("✗ Error: Could not connect to the server.")
        print("Make sure the server is running on http://127.0.0.1:8001")
        print("Run: uvicorn main:app --reload --port 8001")
    except Exception as e:
        print(f"✗ Error: {e}")
