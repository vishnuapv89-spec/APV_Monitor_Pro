from flask_mail import Message
from extensions import mail
from models.user import User
from models.monitor import Monitor
from datetime import datetime


class EmailAlerts:
    """
    APV Monitor Pro
    Enterprise Email Alert System
    """

    # ======================================================
    # INTERNAL HELPERS
    # ======================================================

    @staticmethod
    def _utc_time():
        return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    # ------------------------------------------------------

    @staticmethod
    def _get_monitor_user(monitor: Monitor):
        """
        Fetch monitor owner
        """

        try:
            return monitor.owner

        except Exception as e:
            print(f"[EMAIL USER FETCH ERROR] {str(e)}")
            return None

    # ------------------------------------------------------

    @staticmethod
    def _email_footer():

        return """
APV Monitor Pro
Enterprise Monitoring Platform
"""

    # ------------------------------------------------------

    @staticmethod
    def _build_email(title, content):

        text_body = f"""
{title}

{content}

Time (UTC):
{EmailAlerts._utc_time()}

{EmailAlerts._email_footer()}
"""

        html_body = f"""
<h2>{title}</h2>

<p>{content.replace(chr(10), "<br>")}</p>

<p><b>Time (UTC):</b> {EmailAlerts._utc_time()}</p>

<hr>

<p><b>APV Monitor Pro</b><br>
Enterprise Monitoring Platform</p>
"""

        return text_body, html_body

    # ------------------------------------------------------

    @staticmethod
    def _send_email(recipient, subject, text_body, html_body):

        if not recipient:
            print("[EMAIL ALERT] Missing recipient")
            return

        try:

            msg = Message(
                subject=subject,
                recipients=[recipient],
                body=text_body,
                html=html_body
            )

            mail.send(msg)

        except Exception as e:
            print(f"[EMAIL SEND ERROR] {str(e)}")

    # ======================================================
    # MONITOR DOWN ALERT
    # ======================================================

    @staticmethod
    def send_monitor_down(monitor: Monitor, reason=None):

        try:

            user = EmailAlerts._get_monitor_user(monitor)

            if not user:
                return

            subject = f"🚨 Monitor DOWN - {monitor.url}"

            content = f"""
Monitor URL:
{monitor.url}

Status:
DOWN

Reason:
{reason or "Unknown Error"}

Please investigate the issue immediately.
"""

            text_body, html_body = EmailAlerts._build_email(
                "Monitor DOWN",
                content
            )

            EmailAlerts._send_email(
                user.email,
                subject,
                text_body,
                html_body
            )

        except Exception as e:
            print(f"[DOWN ALERT FAILED] {str(e)}")

    # ======================================================
    # MONITOR RECOVERED ALERT
    # ======================================================

    @staticmethod
    def send_monitor_recovered(monitor: Monitor):

        try:

            user = EmailAlerts._get_monitor_user(monitor)

            if not user:
                return

            subject = f"✅ Monitor RECOVERED - {monitor.url}"

            content = f"""
Monitor URL:
{monitor.url}

Status:
RECOVERED

Your monitored service is now back online.
"""

            text_body, html_body = EmailAlerts._build_email(
                "Monitor Recovered",
                content
            )

            EmailAlerts._send_email(
                user.email,
                subject,
                text_body,
                html_body
            )

        except Exception as e:
            print(f"[RECOVERY ALERT FAILED] {str(e)}")

    # ======================================================
    # SLOW RESPONSE ALERT
    # ======================================================

    @staticmethod
    def send_monitor_slow(monitor: Monitor, response_time):

        try:

            user = EmailAlerts._get_monitor_user(monitor)

            if not user:
                return

            subject = f"⚠️ Slow Response - {monitor.url}"

            content = f"""
Monitor URL:
{monitor.url}

Status:
SLOW RESPONSE

Response Time:
{response_time} seconds

Performance degradation detected.
"""

            text_body, html_body = EmailAlerts._build_email(
                "Slow Response Detected",
                content
            )

            EmailAlerts._send_email(
                user.email,
                subject,
                text_body,
                html_body
            )

        except Exception as e:
            print(f"[SLOW ALERT FAILED] {str(e)}")

    # ======================================================
    # SSL EXPIRING ALERT
    # ======================================================

    @staticmethod
    def send_ssl_expiring(monitor: Monitor, days_remaining):

        try:

            user = EmailAlerts._get_monitor_user(monitor)

            if not user:
                return

            subject = f"⚠️ SSL Expiring Soon - {monitor.url}"

            content = f"""
Monitor URL:
{monitor.url}

SSL Certificate Warning

Your SSL certificate will expire in:
{days_remaining} days

Please renew the certificate before expiration.
"""

            text_body, html_body = EmailAlerts._build_email(
                "SSL Certificate Expiring",
                content
            )

            EmailAlerts._send_email(
                user.email,
                subject,
                text_body,
                html_body
            )

        except Exception as e:
            print(f"[SSL EXPIRING ALERT FAILED] {str(e)}")

    # ======================================================
    # SSL EXPIRED ALERT
    # ======================================================

    @staticmethod
    def send_ssl_expired(monitor: Monitor):

        try:

            user = EmailAlerts._get_monitor_user(monitor)

            if not user:
                return

            subject = f"❌ SSL Certificate Expired - {monitor.url}"

            content = f"""
Monitor URL:
{monitor.url}

SSL Certificate Status:
EXPIRED

Visitors may see security warnings.

Please renew the SSL certificate immediately.
"""

            text_body, html_body = EmailAlerts._build_email(
                "SSL Certificate Expired",
                content
            )

            EmailAlerts._send_email(
                user.email,
                subject,
                text_body,
                html_body
            )

        except Exception as e:
            print(f"[SSL EXPIRED ALERT FAILED] {str(e)}")