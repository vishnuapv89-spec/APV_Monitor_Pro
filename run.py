# ==========================================================
# APV Monitor Pro
# Application Entry Point
# ==========================================================

import os
from datetime import datetime, timedelta

from flask import (
    Flask,
    render_template,
    session,
    redirect,
    url_for,
    jsonify,
    request,
    g
)

from werkzeug.security import generate_password_hash

from config import Config
from extensions import init_extensions, db


# ==========================================================
# MODELS
# ==========================================================

from models.user import User
from models.monitor import Monitor
from models.incident import Incident
from models.monitor_log import MonitorLog


# ==========================================================
# SERVICES
# ==========================================================

from services.monitor_service import MonitorService


# ==========================================================
# BLUEPRINTS
# ==========================================================

from routes.auth_routes import auth_bp
from routes.monitor_routes import monitor_bp
from routes.settings_routes import settings_bp
from routes.telegram_routes import telegram_bp
from routes.status_routes import status_bp
from routes.analytics_routes import analytics_bp
from routes.api_routes import api_bp


# ==========================================================
# SCHEDULER
# ==========================================================

from scheduler.jobs import start_scheduler


# ==========================================================
# APPLICATION FACTORY
# ==========================================================

def create_app():

    app = Flask(__name__)
    app.config.from_object(Config)

    # ======================================================
    # SESSION SECURITY
    # ======================================================

    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=False,
        PERMANENT_SESSION_LIFETIME=timedelta(hours=24)
    )

    # ======================================================
    # EXTENSIONS
    # ======================================================

    init_extensions(app)

    print("📧 MAIL USER:", app.config.get("MAIL_USERNAME"))
    print("📧 MAIL PASSWORD:", bool(app.config.get("MAIL_PASSWORD")))

    # ======================================================
    # REGISTER BLUEPRINTS
    # ======================================================

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(monitor_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(telegram_bp)
    app.register_blueprint(status_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(api_bp)

    # ======================================================
    # DATABASE INITIALIZATION
    # ======================================================

    with app.app_context():

        db.create_all()

        ensure_default_superadmin()

        start_background_scheduler(app)

    # ======================================================
    # USER CONTEXT BINDING
    # ======================================================

    @app.before_request
    def bind_current_user():

        g.current_user = None

        if not session.get("logged_in"):
            return

        user_id = session.get("user_id")

        if not user_id:
            session.clear()
            return

        user = db.session.get(User, user_id)

        if not user:
            session.clear()
            return redirect(url_for("home"))

        g.current_user = user

    # ======================================================
    # HOME PAGE
    # ======================================================

    @app.route("/")
    def home():

        if g.current_user:
            return redirect(url_for("dashboard"))

        return render_template("home.html")

    # ======================================================
    # DASHBOARD
    # ======================================================

    @app.route("/dashboard")
    def dashboard():

        if not g.current_user:
            return redirect(url_for("auth.login"))

        monitors = db.session.execute(
            db.select(Monitor).where(
                Monitor.user_id == g.current_user.id
            )
        ).scalars().all()

        enriched_monitors = []

        for monitor in monitors:

            uptime_24h = MonitorService.calculate_uptime_range(monitor.id, 1)
            uptime_7d = MonitorService.calculate_uptime_range(monitor.id, 7)
            uptime_30d = MonitorService.calculate_uptime_range(monitor.id, 30)
            uptime_365d = MonitorService.calculate_uptime_range(monitor.id, 365)

            incidents = MonitorService.get_total_incidents(monitor.id)

            response_stats = MonitorService.get_response_time_stats(
                monitor.id
            )

            mtbf = MonitorService.calculate_mtbf(monitor.id)

            enriched_monitors.append({

                "data": monitor,

                "uptime": uptime_24h,
                "uptime_7d": uptime_7d,
                "uptime_30d": uptime_30d,
                "uptime_365d": uptime_365d,

                "incidents": incidents,

                "response_min": response_stats["min"],
                "response_max": response_stats["max"],
                "response_avg": response_stats["avg"],

                "mtbf": mtbf
            })

        return render_template(
            "dashboard/index.html",
            monitors=enriched_monitors
        )

    # ======================================================
    # GLOBAL INCIDENTS PAGE
    # ======================================================

    @app.route("/incidents")
    def global_incidents():

        if not g.current_user:
            return redirect(url_for("auth.login"))

        incidents = db.session.execute(

            db.select(Incident)
            .join(Monitor)
            .where(Monitor.user_id == g.current_user.id)
            .order_by(Incident.started_at.desc())

        ).scalars().all()

        return render_template(
            "dashboard/global_incidents.html",
            incidents=incidents
        )

    # ======================================================
    # HEALTH CHECK
    # ======================================================

    @app.route("/health")
    def health():

        return {

            "status": "OK",
            "timestamp": datetime.utcnow().isoformat()

        }, 200

    return app


# ==========================================================
# INTERNAL HELPERS
# ==========================================================

def ensure_default_superadmin():

    existing = db.session.execute(
        db.select(User).filter_by(role="superadmin")
    ).scalar_one_or_none()

    if not existing:

        admin = User(

            email="vishnu.srivastava@apvtechnologies.com",
            password=generate_password_hash("Admin@123"),
            role="superadmin",
            is_verified=True

        )

        db.session.add(admin)
        db.session.commit()

        print("✅ Default Superadmin Created")


def start_background_scheduler(app):

    if app.config.get("SCHEDULER_STARTED"):
        return

    try:

        start_scheduler(app)

        app.config["SCHEDULER_STARTED"] = True

        print("🚀 Background Monitoring Scheduler Started")

    except Exception as e:

        print("Scheduler start failed:", str(e))


# ==========================================================
# APP BOOT
# ==========================================================

app = create_app()


if __name__ == "__main__":

    debug_mode = os.environ.get("FLASK_ENV") != "production"

    app.run(

        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5004)),
        debug=debug_mode,
        use_reloader=False

    )