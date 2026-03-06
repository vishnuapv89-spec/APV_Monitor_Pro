# ==========================================================
# APV Monitor Pro
# Telegram Service
# ==========================================================

import requests

from flask import current_app


# ==========================================================
# SEND TELEGRAM MESSAGE
# ==========================================================

def send_telegram_message(chat_id, text):
    """
    Sends a message to a Telegram chat using bot API.
    """

    try:

        bot_token = current_app.config.get("TELEGRAM_BOT_TOKEN")
        api_url = current_app.config.get(
            "TELEGRAM_API_URL",
            "https://api.telegram.org"
        )

        timeout = current_app.config.get("TELEGRAM_TIMEOUT", 10)
        retries = current_app.config.get("TELEGRAM_RETRIES", 3)

        if not bot_token:
            print("⚠️ Telegram bot token not configured")
            return False

        url = f"{api_url}/bot{bot_token}/sendMessage"

        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML"
        }

        for attempt in range(retries):

            try:

                response = requests.post(
                    url,
                    json=payload,
                    timeout=timeout
                )

                if response.status_code == 200:
                    return True

                else:

                    print(
                        f"[TELEGRAM API ERROR] "
                        f"status={response.status_code} "
                        f"response={response.text}"
                    )

            except requests.exceptions.RequestException as request_error:

                print(
                    f"[TELEGRAM NETWORK ERROR] "
                    f"{str(request_error)}"
                )

        return False

    except Exception as e:

        print(
            f"[TELEGRAM SERVICE ERROR] "
            f"{str(e)}"
        )

        return False


# ==========================================================
# EXTRACT TELEGRAM MESSAGE FROM WEBHOOK
# ==========================================================

def extract_message(update):
    """
    Extract chat_id and message text from Telegram webhook update.
    """

    try:

        if not update:
            return None, None

        message = update.get("message")

        if not message:
            return None, None

        chat = message.get("chat")

        if not chat:
            return None, None

        chat_id = chat.get("id")

        text = message.get("text", "")

        return chat_id, text

    except Exception as e:

        print(
            f"[TELEGRAM UPDATE PARSE ERROR] "
            f"{str(e)}"
        )

        return None, None