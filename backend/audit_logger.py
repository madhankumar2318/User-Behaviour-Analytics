"""
Audit Logger Module
Tracks all user actions for security and compliance
"""

import sqlite3
from datetime import datetime
import json


class AuditLogger:
    def __init__(self, db_path="database.db"):
        self.db_path = db_path
        self._init_audit_table()

    def _get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_audit_table(self):
        """Initialize audit_logs table if it doesn't exist"""
        conn = self._get_connection()

        conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                action TEXT NOT NULL,
                resource TEXT,
                details TEXT,
                ip_address TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        conn.commit()
        conn.close()

    def log_action(
        self, user_id, username, action, resource=None, details=None, ip_address=None
    ):
        """
        Log user action

        Args:
            user_id (int): User ID
            username (str): Username
            action (str): Action performed (e.g., 'LOGIN', 'CREATE_USER', 'VIEW_LOGS')
            resource (str): Resource affected (e.g., 'user:123', 'log:456')
            details (dict): Additional details as dictionary
            ip_address (str): IP address of user

        Returns:
            int: Log ID
        """
        # Convert details dict to JSON string
        if details and isinstance(details, dict):
            details = json.dumps(details)

        conn = self._get_connection()
        cursor = conn.execute(
            """
            INSERT INTO audit_logs (user_id, username, action, resource, details, ip_address)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (user_id, username, action, resource, details, ip_address),
        )

        log_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return log_id

    def log_login(self, user_id, username, success, ip_address=None):
        """
        Log login attempt

        Args:
            user_id (int): User ID (None if failed)
            username (str): Username attempted
            success (bool): Whether login was successful
            ip_address (str): IP address

        Returns:
            int: Log ID
        """
        action = "LOGIN_SUCCESS" if success else "LOGIN_FAILED"
        details = {"success": success}

        return self.log_action(
            user_id=user_id,
            username=username,
            action=action,
            resource=f"user:{user_id}" if user_id else None,
            details=details,
            ip_address=ip_address,
        )

    def log_logout(self, user_id, username, ip_address=None):
        """
        Log logout

        Args:
            user_id (int): User ID
            username (str): Username
            ip_address (str): IP address

        Returns:
            int: Log ID
        """
        return self.log_action(
            user_id=user_id,
            username=username,
            action="LOGOUT",
            resource=f"user:{user_id}",
            ip_address=ip_address,
        )

    def log_user_action(
        self, user_id, username, action_type, target_user_id=None, ip_address=None
    ):
        """
        Log user management action

        Args:
            user_id (int): Admin user ID
            username (str): Admin username
            action_type (str): Action type (CREATE_USER, UPDATE_USER, DELETE_USER, etc.)
            target_user_id (int): Target user ID
            ip_address (str): IP address

        Returns:
            int: Log ID
        """
        return self.log_action(
            user_id=user_id,
            username=username,
            action=action_type,
            resource=f"user:{target_user_id}" if target_user_id else None,
            ip_address=ip_address,
        )

    def log_data_access(
        self, user_id, username, resource_type, resource_id=None, ip_address=None
    ):
        """
        Log data access

        Args:
            user_id (int): User ID
            username (str): Username
            resource_type (str): Type of resource (LOGS, CHARTS, REPORTS, etc.)
            resource_id (str): Specific resource ID
            ip_address (str): IP address

        Returns:
            int: Log ID
        """
        action = f"VIEW_{resource_type}"
        resource = (
            f"{resource_type.lower()}:{resource_id}"
            if resource_id
            else resource_type.lower()
        )

        return self.log_action(
            user_id=user_id,
            username=username,
            action=action,
            resource=resource,
            ip_address=ip_address,
        )

    def get_user_activity(self, user_id, limit=100, offset=0):
        """
        Get activity history for specific user

        Args:
            user_id (int): User ID
            limit (int): Number of records to return
            offset (int): Offset for pagination

        Returns:
            list: List of audit log entries
        """
        conn = self._get_connection()

        logs = conn.execute(
            """
            SELECT * FROM audit_logs
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT ? OFFSET ?
        """,
            (user_id, limit, offset),
        ).fetchall()

        conn.close()

        return [dict(log) for log in logs]

    def get_all_activity(
        self, action_filter=None, start_date=None, end_date=None, limit=100, offset=0
    ):
        """
        Get all audit logs with optional filters

        Args:
            action_filter (str): Filter by action type
            start_date (str): Start date (ISO format)
            end_date (str): End date (ISO format)
            limit (int): Number of records
            offset (int): Offset for pagination

        Returns:
            list: List of audit log entries
        """
        conn = self._get_connection()

        query = "SELECT * FROM audit_logs WHERE 1=1"
        params = []

        if action_filter:
            query += " AND action = ?"
            params.append(action_filter)

        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date)

        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date)

        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        logs = conn.execute(query, params).fetchall()
        conn.close()

        return [dict(log) for log in logs]

    def get_login_history(self, user_id=None, limit=50):
        """
        Get login history

        Args:
            user_id (int): Filter by user ID (None for all users)
            limit (int): Number of records

        Returns:
            list: List of login attempts
        """
        conn = self._get_connection()

        if user_id:
            logs = conn.execute(
                """
                SELECT * FROM audit_logs
                WHERE user_id = ? AND action IN ('LOGIN_SUCCESS', 'LOGIN_FAILED')
                ORDER BY timestamp DESC
                LIMIT ?
            """,
                (user_id, limit),
            ).fetchall()
        else:
            logs = conn.execute(
                """
                SELECT * FROM audit_logs
                WHERE action IN ('LOGIN_SUCCESS', 'LOGIN_FAILED')
                ORDER BY timestamp DESC
                LIMIT ?
            """,
                (limit,),
            ).fetchall()

        conn.close()

        return [dict(log) for log in logs]

    def get_failed_login_attempts(self, username=None, hours=24, limit=50):
        """
        Get recent failed login attempts

        Args:
            username (str): Filter by username
            hours (int): Look back period in hours
            limit (int): Number of records

        Returns:
            list: List of failed login attempts
        """
        conn = self._get_connection()

        if username:
            logs = conn.execute(
                """
                SELECT * FROM audit_logs
                WHERE username = ? AND action = 'LOGIN_FAILED'
                AND timestamp >= datetime('now', '-' || ? || ' hours')
                ORDER BY timestamp DESC
                LIMIT ?
            """,
                (username, hours, limit),
            ).fetchall()
        else:
            logs = conn.execute(
                """
                SELECT * FROM audit_logs
                WHERE action = 'LOGIN_FAILED'
                AND timestamp >= datetime('now', '-' || ? || ' hours')
                ORDER BY timestamp DESC
                LIMIT ?
            """,
                (hours, limit),
            ).fetchall()

        conn.close()

        return [dict(log) for log in logs]

    def get_statistics(self):
        """
        Get audit log statistics

        Returns:
            dict: Statistics about audit logs
        """
        conn = self._get_connection()

        # Total logs
        total = conn.execute("SELECT COUNT(*) as count FROM audit_logs").fetchone()[
            "count"
        ]

        # Logs by action
        by_action = conn.execute("""
            SELECT action, COUNT(*) as count
            FROM audit_logs
            GROUP BY action
            ORDER BY count DESC
            LIMIT 10
        """).fetchall()

        # Recent activity (last 24 hours)
        recent = conn.execute("""
            SELECT COUNT(*) as count FROM audit_logs
            WHERE timestamp >= datetime('now', '-24 hours')
        """).fetchone()["count"]

        # Failed logins (last 24 hours)
        failed_logins = conn.execute("""
            SELECT COUNT(*) as count FROM audit_logs
            WHERE action = 'LOGIN_FAILED'
            AND timestamp >= datetime('now', '-24 hours')
        """).fetchone()["count"]

        conn.close()

        return {
            "total_logs": total,
            "recent_activity_24h": recent,
            "failed_logins_24h": failed_logins,
            "top_actions": [dict(row) for row in by_action],
        }


# Global instance
audit_logger = AuditLogger()


if __name__ == "__main__":
    # Test the audit logger
    print("Testing Audit Logger...")

    # Log some test actions
    print("\n=== Logging Test Actions ===")

    audit_logger.log_login(1, "admin", True, "127.0.0.1")
    audit_logger.log_action(1, "admin", "VIEW_LOGS", "logs", ip_address="127.0.0.1")
    audit_logger.log_user_action(1, "admin", "CREATE_USER", 2, "127.0.0.1")

    print("✅ Logged 3 test actions")

    # Get statistics
    print("\n=== Audit Statistics ===")
    stats = audit_logger.get_statistics()
    print(f"Total logs: {stats['total_logs']}")
    print(f"Recent activity (24h): {stats['recent_activity_24h']}")
    print(f"Failed logins (24h): {stats['failed_logins_24h']}")

    # Get recent activity
    print("\n=== Recent Activity ===")
    recent = audit_logger.get_all_activity(limit=5)
    for log in recent:
        print(f"- {log['timestamp']}: {log['username']} - {log['action']}")
