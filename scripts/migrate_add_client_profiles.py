#!/usr/bin/env python3
"""
Migration script to add client_profiles table for professional client management.
This allows professionals to:
- Add private notes about clients
- Rate clients 1-10
- Track appointment history notes
- Consolidate clients by matching email OR phone
"""

import sys
import os

# Add parent directory to path
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from sqlalchemy import create_engine, inspect
from calendar_app.database import Base, ClientProfile, get_db
from datetime import datetime


def main():
    """Run the migration to add client_profiles table"""

    # Database URL
    DATABASE_URL = "sqlite:///./calendar_app.db"

    print("=" * 70)
    print("CLIENT PROFILES MIGRATION")
    print("=" * 70)
    print()

    # Create engine
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

    # Check if table already exists
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    if "client_profiles" in existing_tables:
        print("✓ client_profiles table already exists")
        print()

        # Show current profile count
        from sqlalchemy.orm import Session

        with Session(engine) as session:
            from calendar_app.database import ClientProfile

            count = session.query(ClientProfile).count()
            print(f"  Current profiles: {count}")

        print()
        print("Migration not needed. Exiting.")
        return

    print("Creating client_profiles table...")
    print()

    # Create the table
    Base.metadata.create_all(bind=engine, tables=[ClientProfile.__table__])

    print("✓ client_profiles table created successfully!")
    print()

    # Verify table creation
    inspector = inspect(engine)
    columns = inspector.get_columns("client_profiles")

    print("Table structure:")
    print("-" * 70)
    for col in columns:
        print(
            f"  {col['name']:20s} {str(col['type']):15s} {'NOT NULL' if not col['nullable'] else 'NULL'}"
        )
    print()

    # Show constraints
    pk = inspector.get_pk_constraint("client_profiles")
    if pk:
        print(f"Primary Key: {', '.join(pk['constrained_columns'])}")

    uniques = inspector.get_unique_constraints("client_profiles")
    if uniques:
        for uc in uniques:
            print(f"Unique Constraint: {uc['name']} on {', '.join(uc['column_names'])}")
    print()

    print("=" * 70)
    print("MIGRATION COMPLETE!")
    print("=" * 70)
    print()
    print("What's new:")
    print("  ✓ Professionals can now add private notes about clients")
    print("  ✓ Rate clients 1-10 for internal reference")
    print("  ✓ Track appointment history with dated notes")
    print("  ✓ Clients are consolidated by matching email OR phone")
    print()
    print("New Endpoints:")
    print("  GET  /professional/clients?specialist_id=X")
    print("  GET  /professional/clients/{consumer_id}?specialist_id=X")
    print("  PUT  /professional/clients/{consumer_id}/profile?specialist_id=X")
    print()
    print("UI:")
    print("  👥 New 'Clients' tab in professional dashboard")
    print("  📋 Click any client to view details and manage profile")
    print()


if __name__ == "__main__":
    main()
