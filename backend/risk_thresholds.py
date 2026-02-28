"""
Risk Threshold Configuration
Allows custom risk threshold settings per user or globally
"""

import sqlite3
import json


class RiskThresholdManager:
    def __init__(self, db_path="database.db"):
        self.db_path = db_path
        self.init_table()

    def init_table(self):
        """Initialize risk threshold configuration table"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS risk_thresholds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                threshold_type TEXT,
                threshold_value INTEGER,
                notification_enabled INTEGER DEFAULT 1,
                notification_channels TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, threshold_type)
            )
        """)

        # Insert default global thresholds if not exists
        defaults = [
            (None, "high_risk", 70, 1, json.dumps(["email", "slack"])),
            (
                None,
                "critical_risk",
                90,
                1,
                json.dumps(["email", "sms", "slack", "teams"]),
            ),
            (None, "failed_attempts", 5, 1, json.dumps(["email"])),
            (None, "unusual_downloads", 100, 1, json.dumps(["slack"])),
        ]

        for default in defaults:
            try:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO risk_thresholds 
                    (user_id, threshold_type, threshold_value, notification_enabled, notification_channels)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    default,
                )
            except:
                pass

        conn.commit()
        conn.close()

    def get_threshold(self, threshold_type, user_id=None):
        """Get threshold value for a specific type and user"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        # Try to get user-specific threshold first
        if user_id:
            result = conn.execute(
                """
                SELECT * FROM risk_thresholds 
                WHERE user_id = ? AND threshold_type = ?
            """,
                (user_id, threshold_type),
            ).fetchone()

            if result:
                conn.close()
                return dict(result)

        # Fall back to global threshold
        result = conn.execute(
            """
            SELECT * FROM risk_thresholds 
            WHERE user_id IS NULL AND threshold_type = ?
        """,
            (threshold_type,),
        ).fetchone()

        conn.close()
        return dict(result) if result else None

    def set_threshold(
        self,
        threshold_type,
        threshold_value,
        user_id=None,
        notification_enabled=True,
        notification_channels=None,
    ):
        """Set or update threshold"""
        if notification_channels is None:
            notification_channels = ["email"]

        conn = sqlite3.connect(self.db_path)
        conn.execute(
            """
            INSERT OR REPLACE INTO risk_thresholds 
            (user_id, threshold_type, threshold_value, notification_enabled, notification_channels)
            VALUES (?, ?, ?, ?, ?)
        """,
            (
                user_id,
                threshold_type,
                threshold_value,
                1 if notification_enabled else 0,
                json.dumps(notification_channels),
            ),
        )

        conn.commit()
        conn.close()
        return True

    def get_all_thresholds(self, user_id=None):
        """Get all thresholds for a user or global"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        if user_id:
            results = conn.execute(
                """
                SELECT * FROM risk_thresholds 
                WHERE user_id = ? OR user_id IS NULL
                ORDER BY user_id DESC
            """,
                (user_id,),
            ).fetchall()
        else:
            results = conn.execute("""
                SELECT * FROM risk_thresholds 
                WHERE user_id IS NULL
            """).fetchall()

        conn.close()
        return [dict(row) for row in results]

    def check_threshold_breach(self, threshold_type, value, user_id=None):
        """Check if a value breaches the threshold"""
        threshold = self.get_threshold(threshold_type, user_id)

        if not threshold:
            return False, None

        breached = value >= threshold["threshold_value"]
        return breached, threshold


# Global instance
risk_threshold_manager = RiskThresholdManager()
