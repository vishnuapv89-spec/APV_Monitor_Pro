from flask import Blueprint, render_template
from extensions import db
from models.user import User
from models.monitor import Monitor
from services.monitor_service import MonitorService


status_bp = Blueprint("status", __name__)


@status_bp.route("/status/<username>")
def public_status(username):

    # ================= FIND USER =================

    user = db.session.execute(
        db.select(User).where(User.email.like(f"{username}%"))
    ).scalars().first()

    if not user:
        return "User not found", 404

    # ================= GET MONITORS =================

    monitors = db.session.execute(
        db.select(Monitor).where(Monitor.user_id == user.id)
    ).scalars().all()

    monitor_list = []

    # ================= BUILD STATUS DATA =================

    for monitor in monitors:

        try:
            uptime = MonitorService.calculate_uptime_24h(monitor.id)
        except:
            uptime = 0

        try:
            incidents = MonitorService.get_total_incidents(monitor.id)
        except:
            incidents = 0

        monitor_list.append({
            "url": monitor.url,
            "status": monitor.status,
            "response_time": monitor.response_time,
            "uptime": uptime,
            "incidents": incidents,
            "last_checked": monitor.last_checked
        })

    # ================= RENDER PAGE =================

    return render_template(
        "status/status_page.html",
        monitors=monitor_list,
        username=username
    )