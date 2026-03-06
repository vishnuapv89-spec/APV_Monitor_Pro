# ==========================================================
# APV Monitor Pro
# Scheduler Jobs
# ==========================================================

from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta

from flask import current_app

from extensions import db
from models.monitor import Monitor
from services.monitor_service import MonitorService


# ==========================================================
# GLOBAL SCHEDULER INSTANCE
# ==========================================================

scheduler = BackgroundScheduler()


# ==========================================================
# MAIN MONITOR LOOP
# ==========================================================

def run_monitor_checks(app):
    """
    Main monitoring loop executed by APScheduler.

    Runs monitors sequentially to avoid database locking
    and excessive concurrency.
    """

    with app.app_context():

        try:

            monitors = Monitor.query.all()

            if not monitors:
                return

            now = datetime.utcnow()

            for monitor in monitors:

                try:

                    # ------------------------------------------
                    # Skip paused monitors
                    # ------------------------------------------

                    if getattr(monitor, "is_paused", False):
                        continue

                    interval = getattr(
                        monitor,
                        "check_interval",
                        current_app.config.get(
                            "DEFAULT_CHECK_INTERVAL",
                            60
                        )
                    )

                    last_checked = getattr(
                        monitor,
                        "last_checked_at",
                        None
                    )

                    should_run = False

                    # ------------------------------------------
                    # First run (never checked)
                    # ------------------------------------------

                    if not last_checked:

                        should_run = True

                    else:

                        next_check = last_checked + timedelta(
                            seconds=interval
                        )

                        if now >= next_check:

                            should_run = True

                    if not should_run:
                        continue

                    # ------------------------------------------
                    # Execute monitor safely
                    # ------------------------------------------

                    run_single_monitor(app, monitor.id)

                except Exception as monitor_error:

                    print(
                        f"[{datetime.utcnow()}] "
                        f"[MONITOR LOOP ERROR] "
                        f"(monitor_id={monitor.id}) "
                        f"{str(monitor_error)}"
                    )

        except Exception as scheduler_error:

            print(
                f"[{datetime.utcnow()}] "
                f"[SCHEDULER LOOP ERROR] "
                f"{str(scheduler_error)}"
            )

        finally:

            # Ensure DB session cleanup
            db.session.remove()


# ==========================================================
# SINGLE MONITOR EXECUTION
# ==========================================================

def run_single_monitor(app, monitor_id):
    """
    Executes a single monitor check safely.
    Isolated execution prevents full loop failure.
    """

    with app.app_context():

        try:

            monitor = db.session.get(Monitor, monitor_id)

            if not monitor:
                return

            # ------------------------------------------
            # Run monitoring engine
            # ------------------------------------------

            MonitorService.check_url(monitor)

            # ------------------------------------------
            # Update last check timestamp
            # ------------------------------------------

            monitor.last_checked_at = datetime.utcnow()

            db.session.commit()

        except Exception as execution_error:

            db.session.rollback()

            print(
                f"[{datetime.utcnow()}] "
                f"[MONITOR EXECUTION FAILED] "
                f"(monitor_id={monitor_id}) "
                f"{str(execution_error)}"
            )

        finally:

            db.session.remove()


# ==========================================================
# START SCHEDULER
# ==========================================================

def start_scheduler(app):
    """
    Starts the monitoring scheduler safely.

    Prevents duplicate job registration and ensures
    a single scheduler instance runs in the application.
    """

    try:

        job_id = "apv_monitor_scheduler"

        existing_job = scheduler.get_job(job_id)

        interval = app.config.get(
            "SCHEDULER_INTERVAL_SECONDS",
            30
        )

        if not existing_job:

            scheduler.add_job(
                id=job_id,
                func=run_monitor_checks,
                trigger="interval",
                seconds=interval,
                args=[app],
                replace_existing=True,
                max_instances=1,
                coalesce=True
            )

        if not scheduler.running:

            scheduler.start()

            print(
                f"🚀 APV Monitor Pro Scheduler Started "
                f"(interval: {interval} seconds)"
            )

    except Exception as e:

        print(
            f"[{datetime.utcnow()}] "
            f"[SCHEDULER STARTUP FAILED] "
            f"{str(e)}"
        )