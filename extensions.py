"""
APV Monitor Pro
Application Extensions

This module defines all Flask extensions used across the
application. Extensions are created here and initialized
inside the Flask application factory (create_app).
"""

from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail


# ======================================================
# DATABASE (SQLAlchemy ORM)
# ======================================================

db: SQLAlchemy = SQLAlchemy()


# ======================================================
# MAIL SERVICE (Email Alerts / Notifications)
# ======================================================

mail: Mail = Mail()


# ======================================================
# EXTENSION INITIALIZER
# ======================================================

def init_extensions(app):
    """
    Initialize all Flask extensions.

    Called inside create_app() to bind extensions
    to the Flask application instance.
    """

    db.init_app(app)
    mail.init_app(app)