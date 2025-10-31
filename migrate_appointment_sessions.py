"""
Database migration to add appointment_sessions table
Run this script to update your database schema
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from calendar_app.database import engine, Base, AppointmentSession

def migrate():
    """Create the appointment_sessions table"""
    print("Creating appointment_sessions table...")
    
    try:
        # Create all tables (will only create if they don't exist)
        Base.metadata.create_all(bind=engine)
        print("✅ Migration completed successfully!")
        print("✅ appointment_sessions table is ready")
        
        # Verify table was created
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        if 'appointment_sessions' in tables:
            print("✅ Verified: appointment_sessions table exists")
            columns = inspector.get_columns('appointment_sessions')
            print(f"   Columns: {[col['name'] for col in columns]}")
        else:
            print("❌ Error: appointment_sessions table not found")
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise

if __name__ == "__main__":
    print("=" * 60)
    print("Appointment Duration Tracking - Database Migration")
    print("=" * 60)
    
    response = input("\nThis will create the appointment_sessions table. Continue? (y/n): ")
    
    if response.lower() == 'y':
        migrate()
    else:
        print("Migration cancelled.")
