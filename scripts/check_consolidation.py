#!/usr/bin/env python3
"""
Check client consolidation in the database
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from calendar_app.database import SessionLocal, Consumer, Booking

def main():
    db = SessionLocal()
    
    print("=" * 70)
    print("CONSUMERS IN DATABASE")
    print("=" * 70)
    consumers = db.query(Consumer).order_by(Consumer.id).all()
    for c in consumers:
        print(f"ID: {c.id:3d} | Name: {c.name:25s} | Email: {c.email or 'None':30s} | Phone: {c.phone or 'None'}")
    
    print("\n" + "=" * 70)
    print("BOOKINGS IN DATABASE")
    print("=" * 70)
    bookings = db.query(Booking).order_by(Booking.id).all()
    for b in bookings:
        if b.consumer_id:
            consumer = db.query(Consumer).filter(Consumer.id == b.consumer_id).first()
            print(f"Booking ID: {b.id:3d} | Consumer ID: {b.consumer_id:3d} | Name: {consumer.name if consumer else 'Unknown':25s} | Date: {b.date}")
        else:
            print(f"Booking ID: {b.id:3d} | LEGACY | Email: {b.client_email or 'None':30s} | Phone: {b.client_phone or 'None':15s} | Date: {b.date}")
    
    print("\n" + "=" * 70)
    print("CONSOLIDATION ANALYSIS")
    print("=" * 70)
    
    # Group by email
    print("\nGrouped by Email:")
    email_groups = {}
    for c in consumers:
        if c.email:
            if c.email not in email_groups:
                email_groups[c.email] = []
            email_groups[c.email].append(c)
    
    for email, consumer_list in email_groups.items():
        if len(consumer_list) > 1:
            print(f"\n⚠️  DUPLICATE EMAIL: {email}")
            for c in consumer_list:
                print(f"    Consumer ID: {c.id}, Name: {c.name}, Phone: {c.phone}")
    
    # Group by phone
    print("\nGrouped by Phone:")
    phone_groups = {}
    for c in consumers:
        if c.phone:
            if c.phone not in phone_groups:
                phone_groups[c.phone] = []
            phone_groups[c.phone].append(c)
    
    for phone, consumer_list in phone_groups.items():
        if len(consumer_list) > 1:
            print(f"\n⚠️  DUPLICATE PHONE: {phone}")
            for c in consumer_list:
                print(f"    Consumer ID: {c.id}, Name: {c.name}, Email: {c.email}")
    
    db.close()

if __name__ == "__main__":
    main()
