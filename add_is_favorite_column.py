#!/usr/bin/env python3
"""
Migration script to add is_favorite column to client_profiles table
"""
import sqlite3
import os

# Get the database path
db_path = os.path.join(os.path.dirname(__file__), "calendar_app.db")

print(f"Connecting to database: {db_path}")

# Connect to the database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Check if column already exists
    cursor.execute("PRAGMA table_info(client_profiles)")
    columns = [row[1] for row in cursor.fetchall()]

    if "is_favorite" in columns:
        print("✅ Column 'is_favorite' already exists!")
    else:
        print("Adding 'is_favorite' column...")
        cursor.execute(
            """
            ALTER TABLE client_profiles 
            ADD COLUMN is_favorite BOOLEAN DEFAULT 0 NOT NULL
        """
        )
        conn.commit()
        print("✅ Successfully added 'is_favorite' column!")

    # Verify the column was added
    cursor.execute("PRAGMA table_info(client_profiles)")
    print("\nCurrent client_profiles table structure:")
    for row in cursor.fetchall():
        print(f"  - {row[1]} ({row[2]})")

except Exception as e:
    print(f"❌ Error: {e}")
    conn.rollback()
finally:
    conn.close()

print("\n✅ Migration complete! Please restart the server.")
