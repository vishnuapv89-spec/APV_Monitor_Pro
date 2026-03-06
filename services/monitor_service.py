import requests
import socket
import ssl
import time

from datetime import datetime, timedelta
from urllib.parse import urlparse
from sqlalchemy import func

from extensions import db
from models.monitor import Monitor
from models.incident import Incident
from models.monitor_log import MonitorLog

from alerts.email_alerts import EmailAlerts
from alerts.telegram_alerts import (
    send_down_alert,
    send_recovery_alert,
    send_slow_alert,
    send_ssl_alert
)


class MonitorService:
    """
    APV Monitor Pro
    Enterprise Monitoring Engine
    """

    session = requests.Session()

    session.headers.update({
        "User-Agent": "APV Monitor Pro"
    })

    TIMEOUT = 10
    MAX_RETRIES = 3
    RETRY_DELAY = 2

    SLOW_THRESHOLD = 2.0


    # ==========================================================
    # TELEGRAM ELIGIBILITY CHECK
    # ==========================================================

    @staticmethod
    def _get_user_chat_id(monitor: Monitor):

        user = monitor.owner

        if not user:
            return None

        if not user.telegram_connected:
            return None

        if not user.telegram_chat_id:
            return None

        if not user.telegram_alerts_enabled:
            return None

        return user.telegram_chat_id


    # ==========================================================
    # MAIN MONITOR CHECK
    # ==========================================================

    @staticmethod
    def check_url(monitor: Monitor):

        now = datetime.utcnow()

        status = "DOWN"
        response_time = None
        root_cause = None
        http_code = None

        previous_status = monitor.status

        for attempt in range(MonitorService.MAX_RETRIES):

            try:

                start = time.perf_counter()

                response = MonitorService.session.get(
                    monitor.url,
                    timeout=MonitorService.TIMEOUT,
                    allow_redirects=True
                )

                end = time.perf_counter()

                response_time = round(end - start, 3)
                http_code = response.status_code

                if http_code >= 400:
                    status = "DOWN"
                    root_cause = f"HTTP {http_code}"

                else:
                    status = "UP"

                    if response_time > MonitorService.SLOW_THRESHOLD:
                        status = "SLOW"
                        root_cause = "High Response Time"

                break

            except requests.exceptions.Timeout:
                root_cause = "Connection Timeout"

            except requests.exceptions.ConnectionError:
                root_cause = "Connection Failed"

            except Exception as e:
                root_cause = str(e)

            if attempt < MonitorService.MAX_RETRIES - 1:
                time.sleep(MonitorService.RETRY_DELAY)

        ssl_days = monitor.ssl_days_remaining

        should_check_ssl = (
            monitor.last_ssl_check is None
            or (now - monitor.last_ssl_check) > timedelta(hours=12)
        )

        if should_check_ssl:

            ssl_days = MonitorService.check_ssl(monitor.url)
            monitor.last_ssl_check = now

        if ssl_days is not None and ssl_days <= 0:

            status = "DOWN"
            root_cause = "SSL Certificate Expired"

        open_incident = Incident.query.filter_by(
            monitor_id=monitor.id,
            lifecycle_status="ONGOING"
        ).first()

        if previous_status != status:

            chat_id = MonitorService._get_user_chat_id(monitor)

            if status == "DOWN":

                if not open_incident:

                    MonitorService.create_incident(
                        monitor.id,
                        status,
                        root_cause or "Service Down",
                        root_cause,
                        http_code
                    )

                EmailAlerts.send_monitor_down(monitor, root_cause)

                if chat_id:
                    send_down_alert(
                        chat_id,
                        monitor.url,
                        root_cause or "Service Down"
                    )

            elif status == "SLOW":

                EmailAlerts.send_monitor_slow(monitor, response_time)

                if chat_id:
                    send_slow_alert(
                        chat_id,
                        monitor.url,
                        response_time
                    )

            elif status == "UP":

                if open_incident:
                    open_incident.resolve()

                EmailAlerts.send_monitor_recovered(monitor)

                if chat_id:
                    send_recovery_alert(
                        chat_id,
                        monitor.url
                    )

        log = MonitorLog(
            monitor_id=monitor.id,
            status=status,
            response_time=response_time,
            http_status_code=http_code,
            checked_at=now
        )

        db.session.add(log)

        monitor.status = status
        monitor.response_time = response_time
        monitor.last_checked = now
        monitor.ssl_days_remaining = ssl_days if ssl_days else 0

        if ssl_days is not None:
            MonitorService._handle_ssl_incidents(monitor, ssl_days)

        db.session.commit()


    # ==========================================================
    # SSL INCIDENT LOGIC
    # ==========================================================

    @staticmethod
    def _handle_ssl_incidents(monitor: Monitor, ssl_days):

        chat_id = MonitorService._get_user_chat_id(monitor)

        if ssl_days <= 0:

            existing = Incident.query.filter_by(
                monitor_id=monitor.id,
                status="SSL_EXPIRED",
                lifecycle_status="ONGOING"
            ).first()

            if not existing:

                MonitorService.create_incident(
                    monitor.id,
                    "SSL_EXPIRED",
                    "SSL Certificate Expired",
                    "SSL Certificate Expired"
                )

                EmailAlerts.send_ssl_expired(monitor)

                if chat_id:
                    send_ssl_alert(chat_id, monitor.url, "SSL EXPIRED")

        elif ssl_days < 15:

            existing = Incident.query.filter_by(
                monitor_id=monitor.id,
                status="SSL_EXPIRING",
                lifecycle_status="ONGOING"
            ).first()

            if not existing:

                MonitorService.create_incident(
                    monitor.id,
                    "SSL_EXPIRING",
                    f"SSL expiring in {ssl_days} days",
                    "SSL Expiring Soon"
                )

                EmailAlerts.send_ssl_expiring(monitor, ssl_days)

                if chat_id:
                    send_ssl_alert(
                        chat_id,
                        monitor.url,
                        f"SSL expiring in {ssl_days} days"
                    )

        else:

            open_ssl = Incident.query.filter(
                Incident.monitor_id == monitor.id,
                Incident.status.in_(["SSL_EXPIRING", "SSL_EXPIRED"]),
                Incident.lifecycle_status == "ONGOING"
            ).all()

            for inc in open_ssl:
                inc.resolve()


    # ==========================================================
    # SSL CHECK
    # ==========================================================

    @staticmethod
    def check_ssl(url):

        try:

            parsed = urlparse(url)
            hostname = parsed.hostname

            if not hostname:
                return None

            context = ssl.create_default_context()

            with context.wrap_socket(
                socket.socket(),
                server_hostname=hostname
            ) as sock:

                sock.settimeout(5)
                sock.connect((hostname, 443))

                cert = sock.getpeercert()

            expiry_date = datetime.strptime(
                cert["notAfter"],
                "%b %d %H:%M:%S %Y %Z"
            )

            return (expiry_date - datetime.utcnow()).days

        except Exception:
            return None


    # ==========================================================
    # INCIDENT CREATION
    # ==========================================================

    @staticmethod
    def create_incident(
        monitor_id,
        status,
        message,
        root_cause=None,
        http_status_code=None
    ):

        incident = Incident(
            monitor_id=monitor_id,
            status=status,
            message=message,
            root_cause=root_cause,
            http_status_code=http_status_code,
            lifecycle_status="ONGOING",
            started_at=datetime.utcnow()
        )

        db.session.add(incident)


    # ==========================================================
    # UPTIME CALCULATION
    # ==========================================================

    @staticmethod
    def calculate_uptime_range(monitor_id, days):

        now = datetime.utcnow()
        start_date = now - timedelta(days=days)

        total_checks = MonitorLog.query.filter(
            MonitorLog.monitor_id == monitor_id,
            MonitorLog.checked_at >= start_date
        ).count()

        if total_checks == 0:
            return 100.0

        down_checks = MonitorLog.query.filter(
            MonitorLog.monitor_id == monitor_id,
            MonitorLog.status == "DOWN",
            MonitorLog.checked_at >= start_date
        ).count()

        uptime_percentage = ((total_checks - down_checks) / total_checks) * 100

        return round(uptime_percentage, 3)


    @staticmethod
    def calculate_uptime_24h(monitor_id):
        return MonitorService.calculate_uptime_range(monitor_id, 1)


    @staticmethod
    def calculate_uptime_30d(monitor_id):
        return MonitorService.calculate_uptime_range(monitor_id, 30)


    # ==========================================================
    # RESPONSE TIME STATS
    # ==========================================================

    @staticmethod
    def get_response_time_stats(monitor_id, days=7):

        start_date = datetime.utcnow() - timedelta(days=days)

        stats = db.session.query(
            func.min(MonitorLog.response_time),
            func.max(MonitorLog.response_time),
            func.avg(MonitorLog.response_time)
        ).filter(
            MonitorLog.monitor_id == monitor_id,
            MonitorLog.checked_at >= start_date,
            MonitorLog.response_time.isnot(None)
        ).first()

        return {
            "min": round(stats[0], 3) if stats and stats[0] else 0,
            "max": round(stats[1], 3) if stats and stats[1] else 0,
            "avg": round(stats[2], 3) if stats and stats[2] else 0
        }


    # ==========================================================
    # MTBF
    # ==========================================================

    @staticmethod
    def calculate_mtbf(monitor_id):

        incidents = Incident.query.filter_by(
            monitor_id=monitor_id
        ).order_by(
            Incident.started_at.asc()
        ).all()

        if len(incidents) < 2:
            return 0

        intervals = []

        for i in range(1, len(incidents)):

            prev = incidents[i - 1]
            curr = incidents[i]

            if prev.resolved_at:

                delta = (
                    curr.started_at - prev.resolved_at
                ).total_seconds()

                intervals.append(delta)

        if not intervals:
            return 0

        avg_seconds = sum(intervals) / len(intervals)
        avg_hours = avg_seconds / 3600

        return round(avg_hours, 2)


    # ==========================================================
    # LOG HELPERS
    # ==========================================================

    @staticmethod
    def get_logs_last_24h(monitor_id):

        start_date = datetime.utcnow() - timedelta(hours=24)

        return MonitorLog.query.filter(
            MonitorLog.monitor_id == monitor_id,
            MonitorLog.checked_at >= start_date
        ).order_by(
            MonitorLog.checked_at.asc()
        ).all()


    @staticmethod
    def get_logs_by_days(monitor_id, days):

        start_date = datetime.utcnow() - timedelta(days=days)

        return MonitorLog.query.filter(
            MonitorLog.monitor_id == monitor_id,
            MonitorLog.checked_at >= start_date
        ).order_by(
            MonitorLog.checked_at.asc()
        ).all()


    @staticmethod
    def get_total_incidents(monitor_id):

        return Incident.query.filter_by(
            monitor_id=monitor_id
        ).count()


    # ==========================================================
    # LIVE STATUS TIMELINE (LAST 24 HOURS)
    # ==========================================================

    @staticmethod
    def get_status_timeline(monitor_id):

        start_time = datetime.utcnow() - timedelta(hours=24)

        logs = MonitorLog.query.filter(
            MonitorLog.monitor_id == monitor_id,
            MonitorLog.checked_at >= start_time
        ).order_by(
            MonitorLog.checked_at.asc()
        ).all()

        timeline = []

        for log in logs:

            status = log.status

            if status == "UP" and log.response_time:
                if log.response_time > MonitorService.SLOW_THRESHOLD:
                    status = "SLOW"

            timeline.append({
                "status": status,
                "response_time": log.response_time,
                "timestamp": log.checked_at.isoformat()
            })

        return timeline