"""
Scheduled Report Generator
Generates and emails periodic reports (daily, weekly, monthly)
"""

from datetime import datetime, timedelta
import sqlite3
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import io


class ReportGenerator:
    def __init__(self, db_path="database.db"):
        self.db_path = db_path

    def get_report_data(self, start_date, end_date):
        """Get data for report period"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        # Get logs in date range
        logs = conn.execute(
            """
            SELECT * FROM logs 
            WHERE login_time BETWEEN ? AND ?
            ORDER BY login_time DESC
        """,
            (start_date, end_date),
        ).fetchall()

        # Get statistics
        stats = {
            "total_activities": len(logs),
            "high_risk_count": len([l for l in logs if l["status"] == "HIGH_RISK"]),
            "locked_count": len([l for l in logs if l["status"] == "LOCKED"]),
            "unique_users": len(set(l["user_id"] for l in logs)),
            "avg_risk_score": (
                sum(l["risk_score"] for l in logs) / len(logs) if logs else 0
            ),
        }

        conn.close()
        return [dict(log) for log in logs], stats

    def generate_pdf_report(self, start_date, end_date, report_type="daily"):
        """Generate PDF report"""
        logs, stats = self.get_report_data(start_date, end_date)

        # Create PDF buffer
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()

        # Title
        title = Paragraph(
            f"<b>User Behavior Analytics Report</b><br/>{report_type.capitalize()} Report",
            styles["Title"],
        )
        elements.append(title)
        elements.append(Spacer(1, 12))

        # Date range
        date_range = Paragraph(f"Period: {start_date} to {end_date}", styles["Normal"])
        elements.append(date_range)
        elements.append(Spacer(1, 12))

        # Statistics
        stats_data = [
            ["Metric", "Value"],
            ["Total Activities", str(stats["total_activities"])],
            ["High Risk Activities", str(stats["high_risk_count"])],
            ["Locked Accounts", str(stats["locked_count"])],
            ["Unique Users", str(stats["unique_users"])],
            ["Average Risk Score", f"{stats['avg_risk_score']:.2f}"],
        ]

        stats_table = Table(stats_data)
        stats_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 14),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ]
            )
        )

        elements.append(stats_table)
        elements.append(Spacer(1, 20))

        # Recent high-risk activities
        high_risk_logs = [l for l in logs if l["status"] == "HIGH_RISK"][:10]
        if high_risk_logs:
            elements.append(
                Paragraph("<b>Top 10 High-Risk Activities</b>", styles["Heading2"])
            )
            elements.append(Spacer(1, 12))

            log_data = [["User ID", "Risk Score", "Location", "Time"]]
            for log in high_risk_logs:
                log_data.append(
                    [
                        log["user_id"],
                        str(log["risk_score"]),
                        log["location"],
                        log["login_time"],
                    ]
                )

            log_table = Table(log_data)
            log_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, 0), 10),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                        ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ]
                )
            )

            elements.append(log_table)

        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        return buffer

    def generate_daily_report(self):
        """Generate daily report"""
        today = datetime.now().strftime("%Y-%m-%d")
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        return self.generate_pdf_report(yesterday, today, "daily")

    def generate_weekly_report(self):
        """Generate weekly report"""
        today = datetime.now()
        week_ago = today - timedelta(days=7)
        return self.generate_pdf_report(
            week_ago.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d"), "weekly"
        )

    def generate_monthly_report(self):
        """Generate monthly report"""
        today = datetime.now()
        month_ago = today - timedelta(days=30)
        return self.generate_pdf_report(
            month_ago.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d"), "monthly"
        )


# Global instance
report_generator = ReportGenerator()
