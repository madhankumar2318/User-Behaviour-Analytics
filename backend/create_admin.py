"""
One-time script to create the default admin user.
Run from the backend/ directory: python create_admin.py
"""
import sys
sys.path.insert(0, ".")

from db import get_db_connection, create_table
from user_manager import user_manager

# Ensure all tables exist
create_table()

# Remove old admin if present (allows safe re-run)
conn = get_db_connection()
conn.execute("DELETE FROM users WHERE username = 'admin'")
conn.commit()
conn.close()

# Create fresh admin account
user = user_manager.create_user(
    username="admin",
    email="admin@example.com",
    password="Admin123!",
    role="Admin",
    full_name="Administrator",
)
print("✅ Admin user created successfully!")
print()
print("  Username : admin")
print("  Password : Admin123!")
print("  Role     : Admin")
