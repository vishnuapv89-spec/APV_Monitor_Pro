from flask import Blueprint, jsonify
from services.monitor_service import MonitorService
from models.monitor import Monitor
from extensions import db


api_bp = Blueprint("api", __name__, url_prefix="/api")


# ==========================================================
# API HEALTH CHECK
# ==========================================================

@api_bp.route("/health")
def api_health():
    """
    Simple API health check
    """

    return jsonify({
        "status": "ok",
        "service": "APV Monitor Pro API"
    })


# ==========================================================
# MONITOR TIMELINE API
# ==========================================================

@api_bp.route("/monitor/<int:monitor_id>/timeline")
def monitor_timeline(monitor_id):
    """
    Returns last 24h monitoring timeline
    Used for Live Status Timeline UI
    """

    monitor = db.session.get(Monitor, monitor_id)

    if not monitor:
        return jsonify({
            "error": "Monitor not found"
        }), 404

    timeline = MonitorService.get_status_timeline(monitor_id)

    return jsonify({
        "monitor_id": monitor.id,
        "url": monitor.url,
        "timeline": timeline
    })


# ==========================================================
# MONITOR SUMMARY API
# ==========================================================

@api_bp.route("/monitor/<int:monitor_id>/summary")
def monitor_summary(monitor_id):
    """
    Returns monitor statistics summary
    """

    monitor = db.session.get(Monitor, monitor_id)

    if not monitor:
        return jsonify({
            "error": "Monitor not found"
        }), 404

    uptime_24h = MonitorService.calculate_uptime_24h(monitor_id)
    uptime_30d = MonitorService.calculate_uptime_30d(monitor_id)

    response_stats = MonitorService.get_response_time_stats(monitor_id)

    total_incidents = MonitorService.get_total_incidents(monitor_id)

    return jsonify({
        "monitor_id": monitor.id,
        "url": monitor.url,
        "status": monitor.status,
        "uptime_24h": uptime_24h,
        "uptime_30d": uptime_30d,
        "response_time": response_stats,
        "total_incidents": total_incidents
    })


# ==========================================================
# MONITOR LIST API
# ==========================================================

@api_bp.route("/monitors")
def monitors_list():
    """
    Returns all monitors
    Used for dashboard widgets
    """

    monitors = db.session.execute(
        db.select(Monitor)
    ).scalars().all()

    data = []

    for monitor in monitors:

        data.append({
            "id": monitor.id,
            "url": monitor.url,
            "status": monitor.status,
            "response_time": monitor.response_time,
            "last_checked": monitor.last_checked.isoformat() if monitor.last_checked else None
        })

    return jsonify({
        "total": len(data),
        "monitors": data
    })


# ==========================================================
# GLOBAL MONITORING SUMMARY
# ==========================================================

@api_bp.route("/global/overview")
def global_overview():
    """
    Global monitoring statistics
    Used for dashboard summary widgets
    """

    total_monitors = db.session.execute(
        db.select(db.func.count()).select_from(Monitor)
    ).scalar()

    up_monitors = db.session.execute(
        db.select(db.func.count()).where(Monitor.status == "UP")
    ).scalar()

    down_monitors = db.session.execute(
        db.select(db.func.count()).where(Monitor.status == "DOWN")
    ).scalar()

    slow_monitors = db.session.execute(
        db.select(db.func.count()).where(Monitor.status == "SLOW")
    ).scalar()

    return jsonify({
        "total_monitors": total_monitors,
        "up": up_monitors,
        "down": down_monitors,
        "slow": slow_monitors
    })