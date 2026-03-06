from services.telegram_service import send_telegram_message
from services.user_service import connect_user_telegram


def handle_telegram_command(chat_id, text):
    """
    Process telegram commands
    """

    if not text:
        return

    parts = text.strip().split()

    command = parts[0].lower()

    # /connect TOKEN
    if command == "/connect":

        if len(parts) < 2:
            send_telegram_message(
                chat_id,
                "❌ Usage:\n/connect YOUR_TOKEN"
            )
            return

        token = parts[1]

        success = connect_user_telegram(token, chat_id)

        if success:
            send_telegram_message(
                chat_id,
                "✅ Telegram connected successfully!\n\nYou will now receive monitor alerts here."
            )
        else:
            send_telegram_message(
                chat_id,
                "❌ Invalid token.\nPlease check your dashboard and try again."
            )

    # /start command
    elif command == "/start":

        send_telegram_message(
            chat_id,
            "👋 Welcome to <b>APV Monitor Pro</b>\n\n"
            "To connect your account send:\n\n"
            "<code>/connect YOUR_TOKEN</code>"
        )

    else:
        send_telegram_message(
            chat_id,
            "❓ Unknown command.\n\nUse:\n/connect TOKEN"
        )