#!/usr/bin/env python3
"""
Migration script to add Consumer and Referral tables.
This script adds the new tables without dropping existing data.
"""

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    inspect,
    text,
)
from sqlalchemy.orm import sessionmaker
from datetime import datetime

DATABASE_URL = "sqlite:///./calendar_app.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def check_table_exists(table_name):
    """Check if a table already exists in the database."""
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()


def run_migration():
    """Run the migration to add Consumer and Referral tables."""

    with engine.connect() as conn:
        # Add Consumer table
        if not check_table_exists("consumers"):
            print("Creating consumers table...")
            conn.execute(
                text(
                    """
                CREATE TABLE consumers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR,
                    email VARCHAR UNIQUE,
                    phone VARCHAR,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """
                )
            )
            conn.execute(text("CREATE INDEX ix_consumers_id ON consumers (id)"))
            conn.execute(text("CREATE INDEX ix_consumers_name ON consumers (name)"))
            conn.execute(text("CREATE INDEX ix_consumers_email ON consumers (email)"))
            conn.commit()
            print("✓ consumers table created")
        else:
            print("✓ consumers table already exists")

        # Add Referral table
        if not check_table_exists("referrals"):
            print("Creating referrals table...")
            conn.execute(
                text(
                    """
                CREATE TABLE referrals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    consumer_id INTEGER,
                    specialist_id INTEGER,
                    referred_by_specialist_id INTEGER NULL,
                    referred_by_workplace_id INTEGER NULL,
                    referral_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (consumer_id) REFERENCES consumers (id),
                    FOREIGN KEY (specialist_id) REFERENCES specialists (id),
                    FOREIGN KEY (referred_by_specialist_id) REFERENCES specialists (id),
                    FOREIGN KEY (referred_by_workplace_id) REFERENCES workplaces (id)
                )
            """
                )
            )
            conn.execute(text("CREATE INDEX ix_referrals_id ON referrals (id)"))
            conn.commit()
            print("✓ referrals table created")
        else:
            print("✓ referrals table already exists")

        # Check if consumer_id column exists in bookings table
        inspector = inspect(engine)
        bookings_columns = [col["name"] for col in inspector.get_columns("bookings")]

        if "consumer_id" not in bookings_columns:
            print("Adding consumer_id column to bookings table...")
            conn.execute(
                text(
                    """
                ALTER TABLE bookings ADD COLUMN consumer_id INTEGER REFERENCES consumers(id)
            """
                )
            )
            conn.commit()
            print("✓ consumer_id column added to bookings table")
        else:
            print("✓ consumer_id column already exists in bookings table")

    print("\n✅ Migration completed successfully!")
    print("\nNext steps:")
    print("1. Restart your server if it's running")
    print("2. Test the business browsing flow: http://localhost:8000/consumer")
    print("3. Bookings will now track referral sources (business vs professional)")


if __name__ == "__main__":
    print("=" * 60)
    print("Running migration: Add Consumer and Referral tracking")
    print("=" * 60)
    print()

    try:
        run_migration()
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback

        traceback.print_exc()
        exit(1)
