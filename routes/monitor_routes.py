from flask import (
    Blueprint,
    request,
    redirect,
    session,
    url_for,
    jsonify,
    flash,
    render_template
)

from extensions import db

from models.monitor import Monitor
from models.incident import Incident
from models.monitor_log import MonitorLog

from services.monitor_service import MonitorService

from urllib.parse import urlparse
from sqlalchemy import or_

monitor_bp = Blueprint("monitor", __name__)


# ==========================================================
# HELPER — AUTH CHECK
# ==========================================================
def require_login():
    if not session.get("logged_in"):
        flash("Session expired. Please login again.", "error")
        return False
    return True


# ==========================================================
# ADD MONITOR
# ==========================================================
@monitor_bp.route("/add-monitor", methods=["POST"])
def add_monitor():

    if not require_login():
        return redirect(url_for("home"))

    raw_url = request.form.get("url", "").strip()

    if not raw_url:
        flash("Please enter a valid URL.", "error")
        return redirect(url_for("dashboard"))

    raw_url = raw_url.replace("https://https://", "https://")
    raw_url = raw_url.replace("http://http://", "http://")

    if not raw_url.startswith(("http://", "https://")):
        raw_url = "https://" + raw_url

    parsed = urlparse(raw_url)

    if not parsed.netloc:
        flash("Invalid URL format.", "error")
        return redirect(url_for("dashboard"))

    normalized_url = parsed.scheme + "://" + parsed.netloc + parsed.path

    existing = Monitor.query.filter_by(
        url=normalized_url,
        user_id=session.get("user_id")
    ).first()

    if existing:
        flash("Monitor already exists.", "error")
        return redirect(url_for("dashboard"))

    user_id = session.get("user_id")

    monitor = Monitor(
        url=normalized_url,
        user_id=user_id,
        created_by=user_id
    )

    db.session.add(monitor)
    db.session.commit()

    flash("Monitor added successfully ✅", "success")

    return redirect(url_for("dashboard"))


# ==========================================================
# EDIT MONITOR
# ==========================================================
@monitor_bp.route("/monitor/edit/<int:monitor_id>", methods=["GET", "POST"])
def edit_monitor(monitor_id):

    if not require_login():
        return redirect(url_for("home"))

    monitor = Monitor.query.get_or_404(monitor_id)

    if monitor.user_id != session.get("user_id"):
        flash("Unauthorized action.", "error")
        return redirect(url_for("dashboard"))

    if request.method == "POST":

        url = request.form.get("url", "").strip()

        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        parsed = urlparse(url)

        if not parsed.netloc:
            flash("Invalid URL format.", "error")
            return redirect(url_for("dashboard"))

        normalized_url = parsed.scheme + "://" + parsed.netloc + parsed.path

        monitor.url = normalized_url

        db.session.commit()

        flash("Monitor updated successfully ✏️", "success")

        return redirect(url_for("dashboard"))

    return render_template(
        "dashboard/edit_monitor.html",
        monitor=monitor
    )


# ==========================================================
# PAUSE / RESUME MONITOR
# ==========================================================
@monitor_bp.route("/pause-monitor/<int:monitor_id>", methods=["POST"])
def pause_monitor(monitor_id):

    if not require_login():
        return redirect(url_for("home"))

    monitor = Monitor.query.get_or_404(monitor_id)

    if monitor.user_id != session.get("user_id"):
        flash("Unauthorized action.", "error")
        return redirect(url_for("dashboard"))

    monitor.is_paused = not monitor.is_paused

    db.session.commit()

    if monitor.is_paused:
        flash("Monitor paused ⏸️", "success")
    else:
        flash("Monitor resumed ▶️", "success")

    return redirect(url_for("dashboard"))


# ==========================================================
# DELETE MONITOR
# ==========================================================
@monitor_bp.route("/delete-monitor/<int:monitor_id>", methods=["POST"])
def delete_monitor(monitor_id):

    if not require_login():
        return redirect(url_for("home"))

    monitor = Monitor.query.get_or_404(monitor_id)

    if monitor.user_id != session.get("user_id"):
        flash("Unauthorized action.", "error")
        return redirect(url_for("dashboard"))

    db.session.delete(monitor)
    db.session.commit()

    flash("Monitor deleted successfully 🗑️", "success")

    return redirect(url_for("dashboard"))


# ==========================================================
# MONITOR OVERVIEW
# ==========================================================
@monitor_bp.route("/monitor/<int:monitor_id>/overview")
def monitor_overview(monitor_id):

    if not require_login():
        return redirect(url_for("home"))

    monitor = Monitor.query.get_or_404(monitor_id)

    if monitor.user_id != session.get("user_id"):
        flash("Unauthorized access.", "error")
        return redirect(url_for("dashboard"))

    uptime_24h = MonitorService.calculate_uptime_24h(monitor.id)
    uptime_7d = MonitorService.calculate_uptime_range(monitor.id, 7)
    uptime_30d = MonitorService.calculate_uptime_range(monitor.id, 30)
    uptime_365d = MonitorService.calculate_uptime_range(monitor.id, 365)

    total_incidents = Incident.query.filter_by(monitor_id=monitor.id).count()

    open_incidents = Incident.query.filter_by(
        monitor_id=monitor.id,
        lifecycle_status="ONGOING"
    ).count()

    resolved_incidents = Incident.query.filter_by(
        monitor_id=monitor.id,
        lifecycle_status="RESOLVED"
    ).count()

    mtbf = MonitorService.calculate_mtbf(monitor.id)

    response_stats = MonitorService.get_response_time_stats(monitor.id)

    return render_template(
        "dashboard/overview.html",
        monitor=monitor,
        uptime_24h=uptime_24h,
        uptime_7d=uptime_7d,
        uptime_30d=uptime_30d,
        uptime_365d=uptime_365d,
        total_incidents=total_incidents,
        open_incidents=open_incidents,
        resolved_incidents=resolved_incidents,
        mtbf=mtbf,
        response_min=response_stats.get("min"),
        response_max=response_stats.get("max"),
        response_avg=response_stats.get("avg")
    )


# ==========================================================
# MONITOR ANALYTICS
# ==========================================================
@monitor_bp.route("/monitor/<int:monitor_id>/analytics")
def monitor_analytics(monitor_id):

    if not require_login():
        return redirect(url_for("home"))

    monitor = Monitor.query.get_or_404(monitor_id)

    if monitor.user_id != session.get("user_id"):
        flash("Unauthorized access.", "error")
        return redirect(url_for("dashboard"))

    return render_template(
        "analytics.html",
        monitors=[monitor]
    )


# ==========================================================
# MONITOR LOGS
# ==========================================================
@monitor_bp.route("/monitor/<int:monitor_id>/logs")
def monitor_logs(monitor_id):

    if not require_login():
        return redirect(url_for("home"))

    monitor = Monitor.query.get_or_404(monitor_id)

    if monitor.user_id != session.get("user_id"):
        flash("Unauthorized access.", "error")
        return redirect(url_for("dashboard"))

    logs = (
        MonitorLog.query
        .filter_by(monitor_id=monitor.id)
        .order_by(MonitorLog.checked_at.desc())
        .limit(500)
        .all()
    )

    return render_template(
        "dashboard/logs.html",
        monitor=monitor,
        logs=logs
    )


# ==========================================================
# MONITOR INCIDENTS
# ==========================================================
@monitor_bp.route("/monitor/<int:monitor_id>/incidents")
def view_incidents(monitor_id):

    if not require_login():
        return redirect(url_for("home"))

    monitor = Monitor.query.get_or_404(monitor_id)

    if monitor.user_id != session.get("user_id"):
        flash("Unauthorized access.", "error")
        return redirect(url_for("dashboard"))

    lifecycle = request.args.get("lifecycle")
    status_filter = request.args.get("status")
    search = request.args.get("search")
    sort = request.args.get("sort", "latest")

    query = Incident.query.filter_by(monitor_id=monitor.id)

    if lifecycle in ["ONGOING", "RESOLVED"]:
        query = query.filter_by(lifecycle_status=lifecycle)

    if status_filter:
        query = query.filter_by(status=status_filter)

    if search:
        query = query.filter(
            or_(
                Incident.root_cause.ilike(f"%{search}%"),
                Incident.message.ilike(f"%{search}%")
            )
        )

    if sort == "latest":
        query = query.order_by(Incident.started_at.desc())
    else:
        query = query.order_by(Incident.started_at.asc())

    incidents = query.all()

    return render_template(
        "dashboard/incidents.html",
        monitor=monitor,
        incidents=incidents
    )


# ==========================================================
# GLOBAL INCIDENT PAGE
# ==========================================================
@monitor_bp.route("/incidents")
def global_incidents():

    if not require_login():
        return redirect(url_for("home"))

    lifecycle = request.args.get("lifecycle")
    search = request.args.get("search")

    query = Incident.query.join(Monitor).filter(
        Monitor.user_id == session.get("user_id")
    )

    if lifecycle in ["ONGOING", "RESOLVED"]:
        query = query.filter(
            Incident.lifecycle_status == lifecycle
        )

    if search:
        query = query.filter(
            or_(
                Incident.root_cause.ilike(f"%{search}%"),
                Monitor.url.ilike(f"%{search}%")
            )
        )

    incidents = query.order_by(
        Incident.started_at.desc()
    ).all()

    return render_template(
        "dashboard/global_incidents.html",
        incidents=incidents
    )


# ==========================================================
# API — MONITOR LIST
# ==========================================================
@monitor_bp.route("/api/monitors")
def get_monitors_api():

    if not session.get("logged_in"):
        return jsonify({"error": "Unauthorized"}), 401

    monitors = Monitor.query.filter_by(
        user_id=session.get("user_id")
    ).all()

    data = []

    for m in monitors:

        data.append({
            "id": m.id,
            "url": m.url,
            "status": m.status,
            "response_time": m.response_time,
            "ssl_days_remaining": m.ssl_days_remaining,
            "last_checked": (
                m.last_checked.strftime("%Y-%m-%d %H:%M:%S")
                if m.last_checked else None
            )
        })

    return jsonify(data)