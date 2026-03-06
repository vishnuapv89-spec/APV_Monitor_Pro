from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    g
)

from extensions import db
from services.telegram_connect_service import generate_connect_token


# ==========================================================
# SETTINGS BLUEPRINT
# ==========================================================

settings_bp = Blueprint(
    "settings",
    __name__
)


# ==========================================================
# SETTINGS PAGE
# ==========================================================

@settings_bp.route("/settings")
def settings_page():

    # user must be logged in
    if not g.current_user:
        return redirect(url_for("auth.login"))

    return render_template(
        "dashboard/settings.html",
        user=g.current_user,
        connect_token=None
    )


# ==========================================================
# GENERATE TELEGRAM CONNECT TOKEN
# ==========================================================

@settings_bp.route("/settings/telegram/connect")
def connect_telegram():

    if not g.current_user:
        return redirect(url_for("auth.login"))

    # generate token
    token = generate_connect_token(g.current_user.id)

    return render_template(
        "dashboard/settings.html",
        user=g.current_user,
        connect_token=token
    )


# ==========================================================
# DISCONNECT TELEGRAM
# ==========================================================

@settings_bp.route("/settings/telegram/disconnect")
def disconnect_telegram():

    if not g.current_user:
        return redirect(url_for("auth.login"))

    user = g.current_user

    # remove telegram connection
    user.telegram_chat_id = None
    user.telegram_connected = False
    user.telegram_connected_at = None

    db.session.commit()

    return redirect(
        url_for("settings.settings_page")
    )