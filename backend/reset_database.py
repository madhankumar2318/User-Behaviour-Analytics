import sqlite3
import os

# Delete old database if exists
if os.path.exists("database.db"):
    os.remove("database.db")
    print("✅ Old database deleted")

# Create new database
conn = sqlite3.connect("database.db")
cursor = conn.cursor()

# Create table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        login_time TEXT,
        location TEXT,
        downloads INTEGER,
        failed_attempts INTEGER,
        status TEXT DEFAULT 'Active'
    )
""")

# Insert sample data
sample_data = [
    ("user_001", "09:30", "New York", 5, 0),
    ("user_001", "09:45", "New York", 7, 0),
    ("user_001", "10:15", "New York", 6, 0),
    ("user_002", "14:20", "London", 12, 1),
    ("user_002", "14:35", "London", 15, 0),
    ("user_003", "23:45", "Tokyo", 25, 3),
    ("user_003", "02:30", "Singapore", 30, 5),
    ("user_004", "11:00", "Mumbai", 8, 0),
    ("user_004", "11:30", "Mumbai", 9, 0),
    ("user_005", "16:45", "Berlin", 20, 2),
]

cursor.executemany("""
    INSERT INTO logs (user_id, login_time, location, downloads, failed_attempts)
    VALUES (?, ?, ?, ?, ?)
""", sample_data)

conn.commit()
conn.close()

print("✅ Database reset successfully!")
print(f"✅ Added {len(sample_data)} sample records")
print("\nSample users:")
print("  - user_001: Normal behavior (New York, morning logins)")
print("  - user_002: Slightly elevated downloads (London)")
print("  - user_003: HIGH RISK (late night logins, unusual location, high downloads)")
print("  - user_004: Normal behavior (Mumbai)")
print("  - user_005: Moderate risk (high downloads, failed attempts)")
