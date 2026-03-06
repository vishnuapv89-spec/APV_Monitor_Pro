import requests
import time

from datetime import datetime
from flask import current_app


# ======================================================
# TELEGRAM CONFIG
# ======================================================

TELEGRAM_TIMEOUT = 10
TELEGRAM_RETRIES = 3
RETRY_DELAY = 2


# ======================================================
# INTERNAL TELEGRAM SENDER
# ======================================================

def send_telegram_message(chat_id: str, message: str):
    """
    Send Telegram message to specific user chat
    """

    bot_token = current_app.config.get("TELEGRAM_BOT_TOKEN")

    if not bot_token:
        current_app.logger.error("[APV Monitor] Telegram bot token missing")
        return False

    if not chat_id:
        current_app.logger.error("[APV Monitor] Telegram chat id missing")
        return False

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }

    for attempt in range(TELEGRAM_RETRIES):

        try:

            response = requests.post(
                url,
                json=payload,
                timeout=TELEGRAM_TIMEOUT
            )

            if response.status_code == 200:
                return True

            current_app.logger.error(
                "[APV Monitor] Telegram API error: %s %s",
                response.status_code,
                response.text
            )

        except Exception as e:

            current_app.logger.error(
                "[APV Monitor] Telegram alert failed: %s",
                str(e)
            )

        if attempt < TELEGRAM_RETRIES - 1:
            time.sleep(RETRY_DELAY)

    return False


# ======================================================
# COMMON ALERT FOOTER
# ======================================================

def _alert_footer():

    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    return (
        "\n\n"
        f"*Time:* {now}\n"
        "_APV Monitor Pro_"
    )


# ======================================================
# MONITOR DOWN ALERT
# ======================================================

def send_down_alert(chat_id: str, monitor_url: str, reason: str):
    """
    Telegram DOWN alert
    """

    message = (
        "🔴 *MONITOR DOWN*\n\n"
        f"*URL:* `{monitor_url}`\n"
        f"*Reason:* {reason}"
        f"{_alert_footer()}"
    )

    send_telegram_message(chat_id, message)


# ======================================================
# MONITOR RECOVERY ALERT
# ======================================================

def send_recovery_alert(chat_id: str, monitor_url: str):
    """
    Telegram RECOVERY alert
    """

    message = (
        "🟢 *MONITOR RECOVERED*\n\n"
        f"*URL:* `{monitor_url}`\n"
        "*Status:* Service Restored"
        f"{_alert_footer()}"
    )

    send_telegram_message(chat_id, message)


# ======================================================
# SLOW RESPONSE ALERT
# ======================================================

def send_slow_alert(chat_id: str, monitor_url: str, response_time: float):
    """
    Telegram SLOW response alert
    """

    response_time = round(response_time, 3)

    message = (
        "⚠️ *SLOW RESPONSE DETECTED*\n\n"
        f"*URL:* `{monitor_url}`\n"
        f"*Response Time:* {response_time}s"
        f"{_alert_footer()}"
    )

    send_telegram_message(chat_id, message)


# ======================================================
# SSL EXPIRING ALERT
# ======================================================

def send_ssl_expiring_alert(chat_id: str, monitor_url: str, days_left: int):
    """
    Telegram SSL expiring alert
    """

    message = (
        "🔐 *SSL CERTIFICATE EXPIRING*\n\n"
        f"*URL:* `{monitor_url}`\n"
        f"*Days Remaining:* {days_left}"
        f"{_alert_footer()}"
    )

    send_telegram_message(chat_id, message)


# ======================================================
# SSL EXPIRED ALERT
# ======================================================

def send_ssl_expired_alert(chat_id: str, monitor_url: str):
    """
    Telegram SSL expired alert
    """

    message = (
        "❌ *SSL CERTIFICATE EXPIRED*\n\n"
        f"*URL:* `{monitor_url}`"
        f"{_alert_footer()}"
    )

    send_telegram_message(chat_id, message)


# ======================================================
# GENERIC SSL ALERT
# ======================================================

def send_ssl_alert(chat_id: str, monitor_url: str, message_text: str):
    """
    Generic SSL alert
    """

    message = (
        "🔐 *SSL ALERT*\n\n"
        f"*URL:* `{monitor_url}`\n"
        f"*Message:* {message_text}"
        f"{_alert_footer()}"
    )

    send_telegram_message(chat_id, message)