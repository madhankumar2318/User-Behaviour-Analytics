"""
Reset admin password to 'admin123' — bypasses the strength validator
so it matches the original _init_users_table default.
Run from backend/ directory: python reset_admin_password.py
"""
import sys
sys.path.insert(0, ".")

import sqlite3
from auth import hash_password

db_path = "database.db"
conn = sqlite3.connect(db_path)

# Hash 'admin123' directly (bypassing validate_password_strength)
new_hash = hash_password("admin123")

conn.execute(
    "UPDATE users SET password_hash = ? WHERE username = 'admin'",
    (new_hash,)
)
conn.commit()

row = conn.execute("SELECT id, username, role FROM users WHERE username='admin'").fetchone()
conn.close()

if row:
    print(f"✅ Admin password reset successfully!")
    print(f"   id={row[0]}, username={row[1]}, role={row[2]}")
    print()
    print("  Username : admin")
    print("  Password : admin123")
else:
    print("❌ Admin user not found in database")
