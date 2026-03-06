from flask import Blueprint, request, jsonify, current_app
import requests
import logging

from services.telegram_connect_service import connect_user_telegram


# =====================================================
# BLUEPRINT
# =====================================================

telegram_bp = Blueprint("telegram", __name__)

logger = logging.getLogger(__name__)


# =====================================================
# TELEGRAM SEND MESSAGE
# =====================================================

def send_telegram_reply(chat_id: str, text: str):
    """
    Send message back to Telegram user
    """

    bot_token = current_app.config.get("TELEGRAM_BOT_TOKEN")

    if not bot_token:
        logger.error("TELEGRAM_BOT_TOKEN not configured")
        return False

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }

    try:

        response = requests.post(
            url,
            json=payload,
            timeout=10
        )

        if response.status_code != 200:
            logger.error(
                "Telegram API error | status=%s | response=%s",
                response.status_code,
                response.text
            )
            return False

        return True

    except Exception as e:

        logger.exception("Telegram send error")
        return False


# =====================================================
# PARSE TELEGRAM MESSAGE
# =====================================================

def extract_message(data):
    """
    Safely extract Telegram message fields
    """

    message = data.get("message")

    if not message:
        return None, None

    chat = message.get("chat")

    if not chat:
        return None, None

    chat_id = str(chat.get("id"))

    text = message.get("text", "").strip()

    if not text:
        return chat_id, None

    return chat_id, text


# =====================================================
# TELEGRAM COMMAND HANDLER
# =====================================================

def handle_command(chat_id, text):

    parts = text.split()
    command = parts[0].lower()

    # =====================================================
    # /start
    # =====================================================

    if command == "/start":

        msg = (
            "*👋 Welcome to APV Monitor Pro Bot*\n\n"
            "To connect Telegram alerts:\n\n"
            "1️⃣ Login to dashboard\n"
            "2️⃣ Go to *Settings → Telegram*\n"
            "3️⃣ Generate connection command\n"
            "4️⃣ Send it here\n\n"
            "*Example:*\n"
            "`/connect YOUR_TOKEN`"
        )

        send_telegram_reply(chat_id, msg)
        return "start"

    # =====================================================
    # /connect TOKEN
    # =====================================================

    if command == "/connect":

        if len(parts) != 2:

            send_telegram_reply(
                chat_id,
                "❌ *Invalid command*\n\n"
                "Correct format:\n"
                "`/connect YOUR_TOKEN`"
            )

            return "invalid_format"

        token = parts[1].strip()

        success, result = connect_user_telegram(token, chat_id)

        if not success:

            send_telegram_reply(
                chat_id,
                "❌ *Connection failed*\n\n"
                "Token invalid or expired.\n"
                "Please generate a new token from dashboard."
            )

            return "connect_failed"

        user = result

        send_telegram_reply(
            chat_id,
            f"✅ *Telegram connected successfully!*\n\n"
            f"*Account:* {user.email}\n"
            "You will now receive uptime alerts here."
        )

        return "connected"

    # =====================================================
    # /status
    # =====================================================

    if command == "/status":

        send_telegram_reply(
            chat_id,
            "📡 *APV Monitor Pro Bot*\n\n"
            "If Telegram is connected, you will receive alerts here.\n\n"
            "Use `/start` for instructions."
        )

        return "status"

    # =====================================================
    # UNKNOWN COMMAND
    # =====================================================

    send_telegram_reply(
        chat_id,
        "❓ *Unknown command*\n\n"
        "Use `/start` to see instructions."
    )

    return "unknown_command"


# =====================================================
# TELEGRAM WEBHOOK
# =====================================================

@telegram_bp.route("/telegram/webhook", methods=["POST"])
def telegram_webhook():
    """
    Telegram webhook endpoint
    """

    try:

        data = request.get_json(silent=True)

        if not data:
            return jsonify({"status": "no_data"}), 200

        chat_id, text = extract_message(data)

        if not chat_id:
            return jsonify({"status": "no_chat"}), 200

        if not text:
            return jsonify({"status": "no_text"}), 200

        result = handle_command(chat_id, text)

        return jsonify({"status": result}), 200

    except Exception:

        logger.exception("Telegram webhook error")

        return jsonify({"status": "error"}), 200