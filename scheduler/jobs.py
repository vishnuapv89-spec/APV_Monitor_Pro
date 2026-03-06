from apscheduler.schedulers.background import BackgroundScheduler
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

from extensions import db
from models.monitor import Monitor
from services.monitor_service import MonitorService


# ==========================================================
# GLOBAL SCHEDULER + WORKER POOL
# ==========================================================

scheduler = BackgroundScheduler()

# Worker pool for parallel monitor execution
executor = ThreadPoolExecutor(max_workers=10)


# ==========================================================
# MAIN MONITOR LOOP
# ==========================================================

def run_monitor_checks(app):
    """
    Main monitoring loop executed by APScheduler.
    Determines which monitors need checking.
    """

    with app.app_context():

        try:

            monitors = Monitor.query.all()

            if not monitors:
                return

            now = datetime.utcnow()

            futures = []

            for monitor in monitors:

                try:

                    # ------------------------------------------
                    # Skip paused monitors
                    # ------------------------------------------

                    if getattr(monitor, "is_paused", False):
                        continue

                    interval = getattr(monitor, "check_interval", 60)

                    last_checked = getattr(
                        monitor,
                        "last_checked_at",
                        None
                    )

                    should_run = False

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
                    # Submit monitor job to worker pool
                    # ------------------------------------------

                    futures.append(
                        executor.submit(
                            run_single_monitor,
                            app,
                            monitor.id
                        )
                    )

                except Exception as monitor_error:

                    print(
                        f"[{datetime.utcnow()}] "
                        f"[MONITOR LOOP ERROR] "
                        f"(ID={monitor.id}) "
                        f"{str(monitor_error)}"
                    )

            # ------------------------------------------
            # Wait for worker completion
            # ------------------------------------------

            for future in futures:

                try:
                    future.result()

                except Exception as worker_error:

                    print(
                        f"[{datetime.utcnow()}] "
                        f"[MONITOR WORKER ERROR] "
                        f"{str(worker_error)}"
                    )

        except Exception as e:

            print(
                f"[{datetime.utcnow()}] "
                f"[SCHEDULER LOOP ERROR] "
                f"{str(e)}"
            )

        finally:

            # Cleanup SQLAlchemy session after scheduler cycle
            db.session.remove()


# ==========================================================
# SINGLE MONITOR EXECUTION
# ==========================================================

def run_single_monitor(app, monitor_id):
    """
    Executes one monitor check safely inside Flask context.
    """

    with app.app_context():

        try:

            monitor = db.session.get(Monitor, monitor_id)

            if not monitor:
                return

            # -------------------------------------------------
            # Execute monitoring engine
            # -------------------------------------------------

            MonitorService.check_url(monitor)

            # -------------------------------------------------
            # Update last check timestamp
            # -------------------------------------------------

            monitor.last_checked_at = datetime.utcnow()

            db.session.commit()

        except Exception as e:

            db.session.rollback()

            print(
                f"[{datetime.utcnow()}] "
                f"[MONITOR EXECUTION FAILED] "
                f"(ID={monitor_id}) "
                f"{str(e)}"
            )

        finally:

            # Prevent session leakage in worker threads
            db.session.remove()


# ==========================================================
# START SCHEDULER
# ==========================================================

def start_scheduler(app):
    """
    Initializes monitoring scheduler safely.
    Prevents duplicate scheduler jobs.
    """

    try:

        job_id = "monitor_job"

        existing_job = scheduler.get_job(job_id)

        if not existing_job:

            scheduler.add_job(
                id=job_id,
                func=run_monitor_checks,
                trigger="interval",
                seconds=30,
                args=[app],
                replace_existing=True,
                max_instances=1,
                coalesce=True
            )

        if not scheduler.running:

            scheduler.start()

            print(
                "🚀 APV Monitor Pro Scheduler Started "
                "(interval: 30 seconds)"
            )

    except Exception as e:

        print(
            f"[{datetime.utcnow()}] "
            f"[SCHEDULER STARTUP FAILED] "
            f"{str(e)}"
        )