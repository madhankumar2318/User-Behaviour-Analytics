"""
Scheduled Report Generator
Generates polished PDF reports with a branded header, summary stats table,
risk breakdown, and high-risk activity listing.
"""

from datetime import datetime, timedelta
import sqlite3
import io

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle,
    Paragraph, Spacer, HRFlowable,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


# ── Brand colours ───────────────────────────────────────────────
BRAND_DARK  = colors.HexColor("#0f172a")
BRAND_CYAN  = colors.HexColor("#00b4d8")
BRAND_AMBER = colors.HexColor("#f59e0b")
BRAND_RED   = colors.HexColor("#ef4444")
BRAND_GREEN = colors.HexColor("#10b981")
BRAND_GREY  = colors.HexColor("#64748b")
BRAND_LIGHT = colors.HexColor("#f1f5f9")


def _styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("rpt_title", fontSize=22, fontName="Helvetica-Bold",
                                textColor=BRAND_DARK, spaceAfter=4,
                                alignment=TA_LEFT),
        "subtitle": ParagraphStyle("rpt_sub", fontSize=10, fontName="Helvetica",
                                   textColor=BRAND_GREY, spaceAfter=2),
        "section": ParagraphStyle("rpt_sec", fontSize=12, fontName="Helvetica-Bold",
                                  textColor=BRAND_DARK, spaceBefore=14, spaceAfter=6),
        "body":    ParagraphStyle("rpt_body", fontSize=9, fontName="Helvetica",
                                  textColor=BRAND_DARK),
        "footer":  ParagraphStyle("rpt_foot", fontSize=8, fontName="Helvetica",
                                  textColor=BRAND_GREY, alignment=TA_CENTER),
    }


class ReportGenerator:
    def __init__(self, db_path="database.db"):
        self.db_path = db_path

    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # ── Data retrieval ──────────────────────────────────────────
    def get_report_data(self, start_date: str, end_date: str):
        """Fetch logs and computed stats for the given date range."""
        conn = self._conn()

        # Inclusive range: compare against ISO prefix so HH:MM rows still match
        logs = conn.execute("""
            SELECT user_id, login_time, location, downloads,
                   failed_attempts, risk_score, status, ip_address
            FROM   logs
            WHERE  login_time >= ?
            AND    login_time <  date(?, '+1 day')
            ORDER  BY login_time DESC
        """, (start_date, end_date)).fetchall()

        conn.close()

        log_list = [dict(r) for r in logs]

        total      = len(log_list)
        high_risk  = [l for l in log_list if l["status"] == "HIGH_RISK"]
        locked     = [l for l in log_list if l["status"] == "LOCKED"]
        active     = [l for l in log_list if l["status"] == "ACTIVE"]
        users      = set(l["user_id"] for l in log_list)
        avg_risk   = (sum(l.get("risk_score") or 0 for l in log_list) / total) if total else 0
        max_risk   = max((l.get("risk_score") or 0 for l in log_list), default=0)

        stats = {
            "total":      total,
            "active":     len(active),
            "high_risk":  len(high_risk),
            "locked":     len(locked),
            "users":      len(users),
            "avg_risk":   round(avg_risk, 1),
            "max_risk":   round(max_risk, 1),
        }
        return log_list, stats

    # ── PDF builder ─────────────────────────────────────────────
    def generate_pdf_report(self, start_date: str, end_date: str, report_type: str = "custom"):
        logs, stats = self.get_report_data(start_date, end_date)
        st = _styles()

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer, pagesize=letter,
            leftMargin=0.65*inch, rightMargin=0.65*inch,
            topMargin=0.65*inch,  bottomMargin=0.65*inch,
        )

        elems = []
        W = doc.width          # printable width

        # ── branded header bar ──────────────────────────────────
        header_data = [[
            Paragraph("🔍  User Behavior Analytics", st["title"]),
            Paragraph(
                f"{report_type.upper()} REPORT<br/>"
                f"<font color='#64748b'>{start_date}  →  {end_date}</font>",
                ParagraphStyle("hdr_r", fontSize=10, fontName="Helvetica",
                               alignment=TA_RIGHT, textColor=BRAND_DARK),
            ),
        ]]
        header_tbl = Table(header_data, colWidths=[W*0.6, W*0.4])
        header_tbl.setStyle(TableStyle([
            ("VALIGN",      (0,0), (-1,-1), "MIDDLE"),
            ("BACKGROUND",  (0,0), (-1,-1), BRAND_LIGHT),
            ("TOPPADDING",  (0,0), (-1,-1), 10),
            ("BOTTOMPADDING",(0,0),(-1,-1), 10),
            ("LEFTPADDING", (0,0), (0,-1),  14),
            ("RIGHTPADDING",(-1,0),(-1,-1), 14),
            ("ROUNDEDCORNERS", (0,0), (-1,-1), 6),
        ]))
        elems.append(header_tbl)
        elems.append(Spacer(1, 14))
        elems.append(HRFlowable(width="100%", thickness=1.5,
                                color=BRAND_CYAN, spaceAfter=12))

        # Generated timestamp
        elems.append(Paragraph(
            f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}   |   "
            f"Prepared by: User Behavior Analytics Platform",
            st["footer"],
        ))
        elems.append(Spacer(1, 18))

        # ── summary stats grid ──────────────────────────────────
        elems.append(Paragraph("Executive Summary", st["section"]))

        def stat_cell(label, value, colour=BRAND_DARK):
            return [
                Paragraph(f"<b><font color='#{colour.hexval()[1:]}'>{value}</font></b>",
                          ParagraphStyle("sv", fontSize=20, fontName="Helvetica-Bold",
                                         alignment=TA_CENTER)),
                Paragraph(label,
                          ParagraphStyle("sl", fontSize=8, fontName="Helvetica",
                                         textColor=BRAND_GREY, alignment=TA_CENTER)),
            ]

        def hex_of(c):
            """Return 6-char hex string for a ReportLab color."""
            r = int(c.red   * 255)
            g = int(c.green * 255)
            b = int(c.blue  * 255)
            return f"{r:02x}{g:02x}{b:02x}"

        stats_grid = [
            [
                Paragraph(f"<b><font color='#{hex_of(BRAND_DARK)}'>{stats['total']}</font></b>",
                          ParagraphStyle("sv", fontSize=20, fontName="Helvetica-Bold", alignment=TA_CENTER)),
                Paragraph(f"<b><font color='#{hex_of(BRAND_GREEN)}'>{stats['active']}</font></b>",
                          ParagraphStyle("sv", fontSize=20, fontName="Helvetica-Bold", alignment=TA_CENTER)),
                Paragraph(f"<b><font color='#{hex_of(BRAND_AMBER)}'>{stats['high_risk']}</font></b>",
                          ParagraphStyle("sv", fontSize=20, fontName="Helvetica-Bold", alignment=TA_CENTER)),
                Paragraph(f"<b><font color='#{hex_of(BRAND_RED)}'>{stats['locked']}</font></b>",
                          ParagraphStyle("sv", fontSize=20, fontName="Helvetica-Bold", alignment=TA_CENTER)),
                Paragraph(f"<b><font color='#{hex_of(BRAND_CYAN)}'>{stats['avg_risk']}</font></b>",
                          ParagraphStyle("sv", fontSize=20, fontName="Helvetica-Bold", alignment=TA_CENTER)),
                Paragraph(f"<b><font color='#{hex_of(BRAND_GREY)}'>{stats['users']}</font></b>",
                          ParagraphStyle("sv", fontSize=20, fontName="Helvetica-Bold", alignment=TA_CENTER)),
            ],
            [
                Paragraph("Total Events",    ParagraphStyle("sl", fontSize=8, fontName="Helvetica", textColor=BRAND_GREY, alignment=TA_CENTER)),
                Paragraph("Active",          ParagraphStyle("sl", fontSize=8, fontName="Helvetica", textColor=BRAND_GREY, alignment=TA_CENTER)),
                Paragraph("High Risk",       ParagraphStyle("sl", fontSize=8, fontName="Helvetica", textColor=BRAND_GREY, alignment=TA_CENTER)),
                Paragraph("Locked",          ParagraphStyle("sl", fontSize=8, fontName="Helvetica", textColor=BRAND_GREY, alignment=TA_CENTER)),
                Paragraph("Avg Risk Score",  ParagraphStyle("sl", fontSize=8, fontName="Helvetica", textColor=BRAND_GREY, alignment=TA_CENTER)),
                Paragraph("Unique Users",    ParagraphStyle("sl", fontSize=8, fontName="Helvetica", textColor=BRAND_GREY, alignment=TA_CENTER)),
            ],
        ]

        cw = W / 6
        sg_tbl = Table(stats_grid, colWidths=[cw]*6)
        sg_tbl.setStyle(TableStyle([
            ("BACKGROUND",   (0,0), (-1,-1), BRAND_LIGHT),
            ("TOPPADDING",   (0,0), (-1,-1), 10),
            ("BOTTOMPADDING",(0,0), (-1,-1), 8),
            ("GRID",         (0,0), (-1,-1), 0.5, colors.white),
            ("ROUNDEDCORNERS",(0,0),(-1,-1), 6),
        ]))
        elems.append(sg_tbl)
        elems.append(Spacer(1, 20))

        # ── risk breakdown bar ──────────────────────────────────
        if stats["total"] > 0:
            elems.append(Paragraph("Risk Breakdown", st["section"]))

            def pct(n):
                return round(n / stats["total"] * 100, 1) if stats["total"] else 0

            breakdown = [
                ["Status",      "Count", "Percentage"],
                ["✅ Active",    stats["active"],    f"{pct(stats['active'])}%"],
                ["⚠️ High Risk", stats["high_risk"], f"{pct(stats['high_risk'])}%"],
                ["🔒 Locked",    stats["locked"],    f"{pct(stats['locked'])}%"],
            ]
            bd_tbl = Table(breakdown, colWidths=[W*0.5, W*0.25, W*0.25])
            bd_tbl.setStyle(TableStyle([
                ("BACKGROUND",   (0,0), (-1,0),  BRAND_DARK),
                ("TEXTCOLOR",    (0,0), (-1,0),  colors.white),
                ("FONTNAME",     (0,0), (-1,0),  "Helvetica-Bold"),
                ("FONTSIZE",     (0,0), (-1,-1), 9),
                ("ALIGN",        (1,0), (-1,-1), "CENTER"),
                ("ROWBACKGROUNDS",(0,1),(-1,-1), [colors.white, BRAND_LIGHT]),
                ("GRID",         (0,0), (-1,-1), 0.4, colors.HexColor("#e2e8f0")),
                ("TOPPADDING",   (0,0), (-1,-1), 6),
                ("BOTTOMPADDING",(0,0), (-1,-1), 6),
                ("LEFTPADDING",  (0,0), (-1,-1), 8),
            ]))
            elems.append(bd_tbl)
            elems.append(Spacer(1, 20))

        # ── high-risk activity log ──────────────────────────────
        flagged = [l for l in logs if l["status"] in ("HIGH_RISK", "LOCKED")][:20]
        if flagged:
            elems.append(Paragraph("Flagged Activity Log (top 20)", st["section"]))

            rows = [["User ID", "Time", "Location", "Risk Score", "Status", "IP Address"]]
            for log in flagged:
                # Format datetime nicely if full ISO
                t = log.get("login_time", "")
                try:
                    t = datetime.strptime(t, "%Y-%m-%dT%H:%M:%S").strftime("%Y-%m-%d %H:%M")
                except Exception:
                    pass
                rows.append([
                    log.get("user_id", ""),
                    t,
                    log.get("location", ""),
                    str(round(log.get("risk_score") or 0, 1)),
                    log.get("status", ""),
                    log.get("ip_address", "N/A"),
                ])

            col_w = [W*0.18, W*0.17, W*0.15, W*0.12, W*0.13, W*0.25]
            lg_tbl = Table(rows, colWidths=col_w, repeatRows=1)
            lg_tbl.setStyle(TableStyle([
                ("BACKGROUND",    (0,0), (-1,0),  BRAND_DARK),
                ("TEXTCOLOR",     (0,0), (-1,0),  colors.white),
                ("FONTNAME",      (0,0), (-1,0),  "Helvetica-Bold"),
                ("FONTSIZE",      (0,0), (-1,-1), 8),
                ("ALIGN",         (3,1), (4,-1),  "CENTER"),
                ("ROWBACKGROUNDS",(0,1), (-1,-1), [colors.white, BRAND_LIGHT]),
                ("GRID",          (0,0), (-1,-1), 0.4, colors.HexColor("#e2e8f0")),
                ("TOPPADDING",    (0,0), (-1,-1), 5),
                ("BOTTOMPADDING", (0,0), (-1,-1), 5),
                ("LEFTPADDING",   (0,0), (-1,-1), 6),
            ]))
            elems.append(lg_tbl)

        elems.append(Spacer(1, 24))
        elems.append(HRFlowable(width="100%", thickness=0.5, color=BRAND_GREY))
        elems.append(Spacer(1, 6))
        elems.append(Paragraph(
            f"User Behavior Analytics Platform  ·  Confidential  ·  "
            f"Report generated {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
            st["footer"],
        ))

        doc.build(elems)
        buffer.seek(0)
        return buffer

    # ── convenience wrappers ────────────────────────────────────
    def generate_daily_report(self):
        today     = datetime.utcnow().strftime("%Y-%m-%d")
        yesterday = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
        return self.generate_pdf_report(yesterday, today, "daily")

    def generate_weekly_report(self):
        today    = datetime.utcnow()
        week_ago = (today - timedelta(days=7)).strftime("%Y-%m-%d")
        return self.generate_pdf_report(week_ago, today.strftime("%Y-%m-%d"), "weekly")

    def generate_monthly_report(self):
        today     = datetime.utcnow()
        month_ago = (today - timedelta(days=30)).strftime("%Y-%m-%d")
        return self.generate_pdf_report(month_ago, today.strftime("%Y-%m-%d"), "monthly")


# Global instance
report_generator = ReportGenerator()
