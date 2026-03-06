"""
APV Monitor Pro
Application Extensions

This module initializes all Flask extensions used across the
application. Extensions are created here and initialized inside
the Flask application factory (create_app).
"""

from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail


# ======================================================
# DATABASE (SQLAlchemy ORM)
# ======================================================

db = SQLAlchemy()


# ======================================================
# MAIL SERVICE (Email Alerts / Notifications)
# ======================================================

mail = Mail()