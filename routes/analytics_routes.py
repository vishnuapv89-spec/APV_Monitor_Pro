from flask import Blueprint, render_template, jsonify, session
from models.monitor import Monitor
from models.incident import Incident
from models.monitor_log import MonitorLog
from extensions import db

analytics_bp = Blueprint("analytics", __name__, url_prefix="/analytics")


# ================= ANALYTICS DASHBOARD =================

@analytics_bp.route("/")
def analytics_dashboard():

    if not session.get("logged_in"):
        return {"error": "Unauthorized"}, 401

    user_id = session.get("user_id")

    monitors = db.session.query(Monitor).filter_by(
        user_id=user_id
    ).all()

    return render_template(
        "analytics.html",
        monitors=monitors
    )


# ================= RESPONSE TIME DATA =================

@analytics_bp.route("/response_time/<int:monitor_id>")
def response_time_data(monitor_id):

    logs = (
        db.session.query(MonitorLog)
        .filter_by(monitor_id=monitor_id)
        .order_by(MonitorLog.checked_at.asc())
        .limit(100)
        .all()
    )

    data = {
        "labels": [log.checked_at.strftime("%H:%M") for log in logs],
        "values": [log.response_time for log in logs],
    }

    return jsonify(data)


# ================= UPTIME STATS =================

@analytics_bp.route("/uptime/<int:monitor_id>")
def uptime_stats(monitor_id):

    logs = db.session.query(MonitorLog).filter_by(
        monitor_id=monitor_id
    ).all()

    total = len(logs)

    up = len([l for l in logs if l.status == "UP"])
    down = len([l for l in logs if l.status == "DOWN"])

    uptime = 0

    if total > 0:
        uptime = round((up / total) * 100, 2)

    return jsonify({
        "uptime": uptime,
        "up": up,
        "down": down
    })


# ================= INCIDENT TIMELINE =================

@analytics_bp.route("/incidents/<int:monitor_id>")
def incident_timeline(monitor_id):

    incidents = (
        db.session.query(Incident)
        .filter_by(monitor_id=monitor_id)
        .order_by(Incident.started_at.desc())
        .limit(20)
        .all()
    )

    data = []

    for i in incidents:

        data.append({
            "start": i.started_at.strftime("%Y-%m-%d %H:%M"),
            "end": (
                i.resolved_at.strftime("%Y-%m-%d %H:%M")
                if i.resolved_at else "Ongoing"
            )
        })

    return jsonify(data)