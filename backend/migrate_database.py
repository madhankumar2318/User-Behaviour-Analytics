"""
Database Migration Script
Adds ip_address and device_fingerprint columns to existing logs table
"""

import sqlite3


def migrate_database():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Check if columns already exist
    cursor.execute("PRAGMA table_info(logs)")
    columns = [column[1] for column in cursor.fetchall()]

    # Add ip_address column if it doesn't exist
    if "ip_address" not in columns:
        print("Adding ip_address column...")
        cursor.execute("ALTER TABLE logs ADD COLUMN ip_address TEXT")
        print("✅ ip_address column added")
    else:
        print("ℹ️ ip_address column already exists")

    # Add device_fingerprint column if it doesn't exist
    if "device_fingerprint" not in columns:
        print("Adding device_fingerprint column...")
        cursor.execute("ALTER TABLE logs ADD COLUMN device_fingerprint TEXT")
        print("✅ device_fingerprint column added")
    else:
        print("ℹ️ device_fingerprint column already exists")

    conn.commit()
    conn.close()
    print("\n✅ Database migration completed successfully!")


if __name__ == "__main__":
    migrate_database()
