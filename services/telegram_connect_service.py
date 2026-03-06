import secrets
from datetime import datetime, timedelta

from extensions import db
from models.user import User


# =========================================================
# CONFIGURATION
# =========================================================

# Token expiration time (minutes)
TOKEN_EXPIRY_MINUTES = 10


# =========================================================
# GENERATE TELEGRAM CONNECT TOKEN
# =========================================================

def generate_connect_token(user_id):
    """
    Generate a secure Telegram connection token for a user.
    Used in command: /connect TOKEN
    """

    user = db.session.get(User, user_id)

    if not user:
        return None

    # Prevent generating token if already connected
    if user.telegram_connected:
        return None

    token = secrets.token_hex(16)

    user.telegram_connect_token = token
    user.telegram_token_created_at = datetime.utcnow()

    db.session.commit()

    return token


# =========================================================
# VALIDATE TOKEN
# =========================================================

def validate_connect_token(token):
    """
    Validate Telegram connection token
    """

    if not token:
        return None

    user = db.session.execute(
        db.select(User).where(User.telegram_connect_token == token)
    ).scalar_one_or_none()

    if not user:
        return None

    # Check token expiry
    if not user.telegram_token_created_at:
        return None

    expiry_time = user.telegram_token_created_at + timedelta(
        minutes=TOKEN_EXPIRY_MINUTES
    )

    if datetime.utcnow() > expiry_time:

        # Expired token cleanup
        user.telegram_connect_token = None
        user.telegram_token_created_at = None
        db.session.commit()

        return None

    return user


# =========================================================
# CONNECT TELEGRAM ACCOUNT
# =========================================================

def connect_user_telegram(token, chat_id):
    """
    Connect Telegram account using token + chat_id
    """

    user = validate_connect_token(token)

    if not user:
        return False, "Invalid or expired token"

    chat_id = str(chat_id)

    # Prevent same chat linked to multiple users
    existing = db.session.execute(
        db.select(User).where(User.telegram_chat_id == chat_id)
    ).scalar_one_or_none()

    if existing and existing.id != user.id:
        return False, "Telegram account already linked to another user"

    # Link telegram
    user.connect_telegram(chat_id)

    db.session.commit()

    return True, user


# =========================================================
# DISCONNECT TELEGRAM
# =========================================================

def disconnect_user_telegram(user_id):
    """
    Remove Telegram integration
    """

    user = db.session.get(User, user_id)

    if not user:
        return False

    user.disconnect_telegram()

    db.session.commit()

    return True


# =========================================================
# TELEGRAM CONNECTION STATUS
# =========================================================

def get_telegram_status(user_id):
    """
    Return Telegram connection status for UI
    """

    user = db.session.get(User, user_id)

    if not user:
        return None

    return {
        "connected": user.telegram_connected,
        "chat_id": user.telegram_chat_id,
        "alerts_enabled": user.telegram_alerts_enabled,
        "connected_at": user.telegram_connected_at
    }


# =========================================================
# TOGGLE TELEGRAM ALERTS
# =========================================================

def toggle_telegram_alerts(user_id, enabled):
    """
    Enable or disable Telegram alerts
    """

    user = db.session.get(User, user_id)

    if not user:
        return False

    user.telegram_alerts_enabled = bool(enabled)

    db.session.commit()

    return True