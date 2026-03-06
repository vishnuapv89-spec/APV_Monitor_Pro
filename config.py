import os
from dotenv import load_dotenv


# ======================================================
# LOAD ENVIRONMENT VARIABLES
# ======================================================

load_dotenv()


# ======================================================
# BASE PATHS
# ======================================================

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_PATH = os.path.join(BASE_DIR, "instance")

# Ensure instance directory exists
os.makedirs(INSTANCE_PATH, exist_ok=True)


# ======================================================
# CONFIG CLASS
# ======================================================

class Config:
    """
    APV Monitor Pro
    Production + Demo Configuration
    """

    # --------------------------------------------------
    # APPLICATION
    # --------------------------------------------------

    APP_NAME = "APV Monitor Pro"

    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        "apv_monitor_dev_secret"
    )

    # --------------------------------------------------
    # DATABASE
    # --------------------------------------------------

    DATABASE_URL = os.getenv("DATABASE_URL")

    if DATABASE_URL:
        SQLALCHEMY_DATABASE_URI = DATABASE_URL
    else:
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(INSTANCE_PATH, 'apv_monitor.db')}"

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # SQLite concurrency protection
    SQLALCHEMY_ENGINE_OPTIONS = {
        "connect_args": {
            "check_same_thread": False
        },
        "pool_pre_ping": True,
        "pool_recycle": 300
    }

    # --------------------------------------------------
    # MAIL CONFIGURATION
    # --------------------------------------------------

    MAIL_SERVER = os.getenv(
        "MAIL_SERVER",
        "smtp.office365.com"
    )

    MAIL_PORT = int(os.getenv(
        "MAIL_PORT",
        587
    ))

    MAIL_USE_TLS = True
    MAIL_USE_SSL = False

    MAIL_USERNAME = os.getenv(
        "MAIL_USERNAME"
    )

    MAIL_PASSWORD = os.getenv(
        "MAIL_PASSWORD"
    )

    MAIL_DEFAULT_SENDER = os.getenv(
        "MAIL_DEFAULT_SENDER",
        "APV Monitor Pro <vishnu.srivastava@apvtechnologies.com>"
    )

    # Prevent crash if SMTP unavailable
    MAIL_SUPPRESS_SEND = os.getenv(
        "MAIL_SUPPRESS_SEND",
        "False"
    ) == "True"

    MAIL_MAX_EMAILS = None


    # --------------------------------------------------
    # TELEGRAM ALERT SYSTEM
    # --------------------------------------------------

    TELEGRAM_BOT_TOKEN = os.getenv(
        "TELEGRAM_BOT_TOKEN",
        "7995905567:AAFEayHbuUUkVbnwDfbOxZTopHwgv5buxGs"
    )

    TELEGRAM_CHAT_ID = os.getenv(
        "TELEGRAM_CHAT_ID",
        "6794289927"
    )

    TELEGRAM_API_URL = "https://api.telegram.org"

    TELEGRAM_TIMEOUT = int(os.getenv(
        "TELEGRAM_TIMEOUT",
        10
    ))

    TELEGRAM_RETRIES = int(os.getenv(
        "TELEGRAM_RETRIES",
        3
    ))


    # --------------------------------------------------
    # MONITORING ENGINE
    # --------------------------------------------------

    MONITOR_TIMEOUT = int(os.getenv(
        "MONITOR_TIMEOUT",
        10
    ))

    DEFAULT_CHECK_INTERVAL = int(os.getenv(
        "DEFAULT_CHECK_INTERVAL",
        60
    ))

    MAX_MONITOR_RETRIES = int(os.getenv(
        "MAX_MONITOR_RETRIES",
        3
    ))

    MONITOR_RETRY_DELAY = int(os.getenv(
        "MONITOR_RETRY_DELAY",
        2
    ))

    SLOW_RESPONSE_THRESHOLD = float(os.getenv(
        "SLOW_RESPONSE_THRESHOLD",
        2.0
    ))


    # --------------------------------------------------
    # ALERT THRESHOLDS
    # --------------------------------------------------

    FAILURE_THRESHOLD = int(os.getenv(
        "FAILURE_THRESHOLD",
        3
    ))

    RECOVERY_THRESHOLD = int(os.getenv(
        "RECOVERY_THRESHOLD",
        2
    ))

    SSL_EXPIRING_DAYS = int(os.getenv(
        "SSL_EXPIRING_DAYS",
        15
    ))


    # --------------------------------------------------
    # SSL MONITORING
    # --------------------------------------------------

    SSL_CHECK_INTERVAL_HOURS = int(os.getenv(
        "SSL_CHECK_INTERVAL_HOURS",
        12
    ))


    # --------------------------------------------------
    # SCHEDULER SETTINGS
    # --------------------------------------------------

    SCHEDULER_INTERVAL_SECONDS = int(os.getenv(
        "SCHEDULER_INTERVAL_SECONDS",
        30
    ))

    # IMPORTANT for SQLite locking
    MAX_WORKER_THREADS = int(os.getenv(
        "MAX_WORKER_THREADS",
        1
    ))


    # --------------------------------------------------
    # HTTP REQUEST SETTINGS
    # --------------------------------------------------

    MONITOR_USER_AGENT = os.getenv(
        "MONITOR_USER_AGENT",
        "APV Monitor Pro Monitoring Engine"
    )

    FOLLOW_REDIRECTS = True


    # --------------------------------------------------
    # ENVIRONMENT
    # --------------------------------------------------

    DEBUG = os.getenv(
        "DEBUG",
        "False"
    ) == "True"

    ENV = os.getenv(
        "FLASK_ENV",
        "production"
    )