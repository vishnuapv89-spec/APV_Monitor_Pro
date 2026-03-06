import requests
from flask import current_app

def send_telegram_message(chat_id, text):
    """
    Send message to Telegram user
    """

    bot_token = current_app.config["TELEGRAM_BOT_TOKEN"]

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }

    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print("Telegram send error:", e)


def extract_message(update):
    """
    Extract message text and chat_id from Telegram update
    """

    if "message" not in update:
        return None, None

    message = update["message"]

    chat_id = message["chat"]["id"]
    text = message.get("text", "")

    return chat_id, text