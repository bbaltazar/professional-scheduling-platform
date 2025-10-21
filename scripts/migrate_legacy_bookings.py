#!/usr/bin/env python3
"""
Migrate legacy bookings to use Consumer records.
This script:
1. Finds all bookings without consumer_id
2. For each booking, finds or creates a matching Consumer
3. Links the booking to the consumer
4. Handles consolidation (same email/phone = same consumer)
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from calendar_app.database import SessionLocal, Consumer, Booking
from sqlalchemy import or_, func
from datetime import datetime

def normalize_email(email):
    """Normalize email for comparison (lowercase, strip whitespace)"""
    if not email:
        return None
    return email.strip().lower()

def normalize_phone(phone):
    """Normalize phone for comparison (remove all non-digits)"""
    if not phone:
        return None
    # Remove all non-digit characters
    return ''.join(c for c in phone if c.isdigit())

def find_or_create_consumer(db, name, email, phone):
    """
    Find existing consumer by email OR phone (case-insensitive, normalized).
    If multiple consumers match, return the first one (they should be merged later).
    If no consumer exists, create a new one.
    """
    norm_email = normalize_email(email)
    norm_phone = normalize_phone(phone)
    
    # Try to find existing consumer by normalized email or phone
    conditions = []
    if norm_email:
        # Case-insensitive email search
        conditions.append(func.lower(Consumer.email) == norm_email)
    if norm_phone:
        # Find consumers whose phone matches when normalized
        all_consumers = db.query(Consumer).all()
        for consumer in all_consumers:
            if normalize_phone(consumer.phone) == norm_phone:
                print(f"  ✓ Found existing consumer by phone: {consumer.name} (ID: {consumer.id})")
                return consumer
    
    if norm_email:
        consumer = db.query(Consumer).filter(func.lower(Consumer.email) == norm_email).first()
        if consumer:
            print(f"  ✓ Found existing consumer by email: {consumer.name} (ID: {consumer.id})")
            return consumer
    
    # No existing consumer found, create new one
    consumer = Consumer(
        name=name,
        email=email,
        phone=phone,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(consumer)
    db.flush()  # Get ID without committing
    print(f"  ➕ Created new consumer: {name} (ID: {consumer.id})")
    return consumer

def main():
    db = SessionLocal()
    
    print("=" * 70)
    print("LEGACY BOOKING MIGRATION")
    print("=" * 70)
    print()
    
    # Find all legacy bookings (no consumer_id)
    legacy_bookings = db.query(Booking).filter(Booking.consumer_id.is_(None)).all()
    
    print(f"Found {len(legacy_bookings)} legacy bookings to migrate")
    print()
    
    if len(legacy_bookings) == 0:
        print("✓ No legacy bookings found. All bookings already have consumer records.")
        db.close()
        return
    
    migrated_count = 0
    skipped_count = 0
    
    for booking in legacy_bookings:
        print(f"Processing Booking ID {booking.id}:")
        print(f"  Name: {booking.client_name}")
        print(f"  Email: {booking.client_email}")
        print(f"  Phone: {booking.client_phone}")
        
        if not booking.client_email and not booking.client_phone:
            print(f"  ⚠️  SKIPPED: No email or phone to match")
            skipped_count += 1
            continue
        
        # Find or create consumer
        consumer = find_or_create_consumer(
            db,
            booking.client_name,
            booking.client_email,
            booking.client_phone
        )
        
        # Link booking to consumer
        booking.consumer_id = consumer.id
        migrated_count += 1
        print()
    
    # Commit all changes
    try:
        db.commit()
        print("=" * 70)
        print(f"✓ Migration complete!")
        print(f"  Migrated: {migrated_count} bookings")
        print(f"  Skipped: {skipped_count} bookings")
        print("=" * 70)
        print()
        
        # Show consolidation summary
        print("CONSOLIDATION SUMMARY")
        print("=" * 70)
        consumers = db.query(Consumer).all()
        print(f"Total consumers: {len(consumers)}")
        
        # Check for emails that should be consolidated
        print("\nConsumers by normalized email:")
        email_map = {}
        for c in consumers:
            norm_email = normalize_email(c.email)
            if norm_email:
                if norm_email not in email_map:
                    email_map[norm_email] = []
                email_map[norm_email].append(c)
        
        for norm_email, consumer_list in email_map.items():
            if len(consumer_list) > 1:
                print(f"\n⚠️  Multiple consumers with email '{norm_email}':")
                for c in consumer_list:
                    booking_count = db.query(Booking).filter(Booking.consumer_id == c.id).count()
                    print(f"    ID: {c.id}, Name: {c.name}, Phone: {c.phone}, Bookings: {booking_count}")
            else:
                c = consumer_list[0]
                booking_count = db.query(Booking).filter(Booking.consumer_id == c.id).count()
                print(f"  {norm_email}: {c.name} (ID: {c.id}, {booking_count} bookings)")
        
        # Check for phones that should be consolidated
        print("\nConsumers by normalized phone:")
        phone_map = {}
        for c in consumers:
            norm_phone = normalize_phone(c.phone)
            if norm_phone:
                if norm_phone not in phone_map:
                    phone_map[norm_phone] = []
                phone_map[norm_phone].append(c)
        
        for norm_phone, consumer_list in phone_map.items():
            if len(consumer_list) > 1:
                print(f"\n⚠️  Multiple consumers with phone '{norm_phone}':")
                for c in consumer_list:
                    booking_count = db.query(Booking).filter(Booking.consumer_id == c.id).count()
                    print(f"    ID: {c.id}, Name: {c.name}, Email: {c.email}, Bookings: {booking_count}")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error during migration: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main()
