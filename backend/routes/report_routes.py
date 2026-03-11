"""
Report Blueprint
Routes: GET /reports/generate
"""

from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, send_file
from auth import token_required, role_required
from report_generator import report_generator

report_bp = Blueprint("reports", __name__, url_prefix="/reports")


# -------------------------
# GET /reports/generate
# -------------------------
@report_bp.route("/generate", methods=["GET"])
@token_required
@role_required(["Admin", "Analyst"])
def generate_report():
    """
    Generate and stream a PDF risk report.

    Query params:
      type  = daily | weekly | monthly | custom  (default: weekly)
      start = YYYY-MM-DD  (required when type=custom)
      end   = YYYY-MM-DD  (required when type=custom)
    """
    try:
        report_type = request.args.get("type", "weekly").lower()
        today = datetime.utcnow()

        if report_type == "daily":
            start = (today - timedelta(days=1)).strftime("%Y-%m-%d")
            end   = today.strftime("%Y-%m-%d")

        elif report_type == "weekly":
            start = (today - timedelta(days=7)).strftime("%Y-%m-%d")
            end   = today.strftime("%Y-%m-%d")

        elif report_type == "monthly":
            start = (today - timedelta(days=30)).strftime("%Y-%m-%d")
            end   = today.strftime("%Y-%m-%d")

        elif report_type == "custom":
            start = request.args.get("start")
            end   = request.args.get("end")
            if not start or not end:
                return jsonify({"error": "start and end dates required for custom range"}), 400
            # Validate format
            try:
                datetime.strptime(start, "%Y-%m-%d")
                datetime.strptime(end,   "%Y-%m-%d")
            except ValueError:
                return jsonify({"error": "Dates must be YYYY-MM-DD format"}), 400
        else:
            return jsonify({"error": "type must be daily, weekly, monthly, or custom"}), 400

        pdf_buffer = report_generator.generate_pdf_report(start, end, report_type)

        filename = f"uba_report_{start}_to_{end}.pdf"
        return send_file(
            pdf_buffer,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=filename,
        )

    except Exception as e:
        import logging
        logging.exception("Report generation failed")
        return jsonify({"error": f"Report generation failed: {str(e)}"}), 500
