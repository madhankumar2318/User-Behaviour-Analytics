"""
User Manager Module
Handles user CRUD operations and management
"""

import sqlite3
from datetime import datetime
from auth import hash_password, verify_password, validate_password_strength


class UserManager:
    def __init__(self, db_path="database.db"):
        self.db_path = db_path
        self._init_users_table()

    def _get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_users_table(self):
        """Initialize users table if it doesn't exist"""
        conn = self._get_connection()

        # Create users table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'Viewer',
                full_name TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        """)

        # Check if default admin exists
        admin = conn.execute("SELECT * FROM users WHERE username = 'admin'").fetchone()

        if not admin:
            # Create default admin user
            admin_password = hash_password("admin123")
            conn.execute(
                """
                INSERT INTO users (username, email, password_hash, role, full_name)
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    "admin",
                    "admin@example.com",
                    admin_password,
                    "Admin",
                    "System Administrator",
                ),
            )

            print("✅ Created default admin user (username: admin, password: admin123)")
            print("⚠️  IMPORTANT: Change the admin password immediately!")

        conn.commit()
        conn.close()

    def create_user(self, username, email, password, role="Viewer", full_name=None):
        """
        Create new user

        Args:
            username (str): Unique username
            email (str): User email
            password (str): Plain text password
            role (str): User role (Admin, Analyst, Viewer)
            full_name (str): User's full name

        Returns:
            dict: Created user object (without password)
        """
        # Validate password
        is_valid, error_msg = validate_password_strength(password)
        if not is_valid:
            raise ValueError(error_msg)

        # Validate role
        if role not in ["Admin", "Analyst", "Viewer"]:
            raise ValueError("Invalid role. Must be Admin, Analyst, or Viewer")

        # Hash password
        password_hash = hash_password(password)

        conn = self._get_connection()

        try:
            cursor = conn.execute(
                """
                INSERT INTO users (username, email, password_hash, role, full_name)
                VALUES (?, ?, ?, ?, ?)
            """,
                (username, email, password_hash, role, full_name),
            )

            user_id = cursor.lastrowid
            conn.commit()

            # Return created user
            user = self.get_user_by_id(user_id)
            return user

        except sqlite3.IntegrityError as e:
            if "username" in str(e):
                raise ValueError("Username already exists")
            elif "email" in str(e):
                raise ValueError("Email already exists")
            else:
                raise ValueError(f"Database error: {e}")
        finally:
            conn.close()

    def get_user_by_id(self, user_id):
        """Get user by ID (without password)"""
        conn = self._get_connection()
        user = conn.execute(
            "SELECT id, username, email, role, full_name, is_active, created_at, updated_at, last_login FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        conn.close()

        if user:
            return dict(user)
        return None

    def get_user_by_username(self, username):
        """Get user by username (includes password hash for authentication)"""
        conn = self._get_connection()
        user = conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
        conn.close()

        if user:
            return dict(user)
        return None

    def get_user_by_email(self, email):
        """Get user by email"""
        conn = self._get_connection()
        user = conn.execute(
            "SELECT id, username, email, role, full_name, is_active FROM users WHERE email = ?",
            (email,),
        ).fetchone()
        conn.close()

        if user:
            return dict(user)
        return None

    def list_users(self, include_inactive=False):
        """
        List all users

        Args:
            include_inactive (bool): Include deactivated users

        Returns:
            list: List of user objects (without passwords)
        """
        conn = self._get_connection()

        if include_inactive:
            query = "SELECT id, username, email, role, full_name, is_active, created_at, last_login FROM users ORDER BY created_at DESC"
            users = conn.execute(query).fetchall()
        else:
            query = "SELECT id, username, email, role, full_name, is_active, created_at, last_login FROM users WHERE is_active = 1 ORDER BY created_at DESC"
            users = conn.execute(query).fetchall()

        conn.close()

        return [dict(user) for user in users]

    def update_user(self, user_id, updates):
        """
        Update user information

        Args:
            user_id (int): User ID
            updates (dict): Fields to update (email, role, full_name, is_active)

        Returns:
            dict: Updated user object
        """
        allowed_fields = ["email", "role", "full_name", "is_active"]

        # Filter out non-allowed fields
        updates = {k: v for k, v in updates.items() if k in allowed_fields}

        if not updates:
            raise ValueError("No valid fields to update")

        # Validate role if being updated
        if "role" in updates and updates["role"] not in ["Admin", "Analyst", "Viewer"]:
            raise ValueError("Invalid role")

        # Build UPDATE query
        set_clause = ", ".join([f"{field} = ?" for field in updates.keys()])
        set_clause += ", updated_at = CURRENT_TIMESTAMP"

        values = list(updates.values()) + [user_id]

        conn = self._get_connection()

        try:
            conn.execute(f"UPDATE users SET {set_clause} WHERE id = ?", values)
            conn.commit()

            # Return updated user
            user = self.get_user_by_id(user_id)
            return user

        except sqlite3.IntegrityError as e:
            raise ValueError(f"Update failed: {e}")
        finally:
            conn.close()

    def delete_user(self, user_id):
        """
        Delete user (soft delete - sets is_active to 0)

        Args:
            user_id (int): User ID

        Returns:
            bool: True if deleted successfully
        """
        # Don't allow deleting user ID 1 (default admin)
        if user_id == 1:
            raise ValueError("Cannot delete default admin user")

        conn = self._get_connection()
        conn.execute(
            "UPDATE users SET is_active = 0, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (user_id,),
        )
        conn.commit()
        conn.close()

        return True

    def change_password(self, user_id, old_password, new_password):
        """
        Change user password (requires old password)

        Args:
            user_id (int): User ID
            old_password (str): Current password
            new_password (str): New password

        Returns:
            bool: True if changed successfully
        """
        # Validate new password
        is_valid, error_msg = validate_password_strength(new_password)
        if not is_valid:
            raise ValueError(error_msg)

        # Get user with password hash
        conn = self._get_connection()
        user = conn.execute(
            "SELECT password_hash FROM users WHERE id = ?", (user_id,)
        ).fetchone()

        if not user:
            conn.close()
            raise ValueError("User not found")

        # Verify old password
        if not verify_password(old_password, user["password_hash"]):
            conn.close()
            raise ValueError("Current password is incorrect")

        # Hash new password
        new_hash = hash_password(new_password)

        # Update password
        conn.execute(
            "UPDATE users SET password_hash = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (new_hash, user_id),
        )
        conn.commit()
        conn.close()

        return True

    def reset_password(self, user_id, new_password):
        """
        Admin password reset (doesn't require old password)

        Args:
            user_id (int): User ID
            new_password (str): New password

        Returns:
            bool: True if reset successfully
        """
        # Validate new password
        is_valid, error_msg = validate_password_strength(new_password)
        if not is_valid:
            raise ValueError(error_msg)

        # Hash new password
        new_hash = hash_password(new_password)

        conn = self._get_connection()
        conn.execute(
            "UPDATE users SET password_hash = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (new_hash, user_id),
        )
        conn.commit()
        conn.close()

        return True

    def update_last_login(self, user_id):
        """Update user's last login timestamp"""
        conn = self._get_connection()
        conn.execute(
            "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?", (user_id,)
        )
        conn.commit()
        conn.close()

    def authenticate(self, username, password):
        """
        Authenticate user

        Args:
            username (str): Username
            password (str): Password

        Returns:
            dict: User object if authenticated, None otherwise
        """
        user = self.get_user_by_username(username)

        if not user:
            return None

        if not user["is_active"]:
            return None

        if verify_password(password, user["password_hash"]):
            # Remove password hash from returned object
            user_safe = {k: v for k, v in user.items() if k != "password_hash"}
            return user_safe

        return None


# Global instance
user_manager = UserManager()


if __name__ == "__main__":
    # Test the user manager
    print("Testing User Manager...")

    # List users
    print("\n=== Current Users ===")
    users = user_manager.list_users()
    for user in users:
        print(f"- {user['username']} ({user['role']}) - {user['email']}")

    # Test authentication
    print("\n=== Authentication Test ===")
    auth_result = user_manager.authenticate("admin", "admin123")
    if auth_result:
        print(f"✅ Authentication successful: {auth_result['username']}")
    else:
        print("❌ Authentication failed")
