# ======================================================
# APV Monitor Pro
# Configuration
# ======================================================

import os
from dotenv import load_dotenv


# ======================================================
# BASE PATHS
# ======================================================

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_PATH = os.path.join(BASE_DIR, "instance")

os.makedirs(INSTANCE_PATH, exist_ok=True)


# ======================================================
# LOAD ENV FILE (LOCAL + PRODUCTION SAFE)
# ======================================================

ENV_PATH = os.path.join(BASE_DIR, ".env")

if os.path.exists(ENV_PATH):
    load_dotenv(ENV_PATH)
else:
    load_dotenv()


# ======================================================
# ENV HELPERS
# ======================================================

def env(key, default=None):
    return os.getenv(key, default)


def env_int(key, default=0):
    try:
        return int(os.getenv(key, default))
    except Exception:
        return default


def env_float(key, default=0.0):
    try:
        return float(os.getenv(key, default))
    except Exception:
        return default


def env_bool(key, default=False):
    return str(os.getenv(key, default)).lower() == "true"


# ======================================================
# DATABASE URL FIX (Render postgres compatibility)
# ======================================================

DATABASE_URL = env("DATABASE_URL")

if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgres://",
        "postgresql://",
        1
    )


# ======================================================
# CONFIG CLASS
# ======================================================

class Config:
    """
    APV Monitor Pro
    Production + Development Configuration
    """

    # --------------------------------------------------
    # APPLICATION
    # --------------------------------------------------

    APP_NAME = "APV Monitor Pro"

    SECRET_KEY = env(
        "SECRET_KEY",
        "apv_monitor_dev_secret"
    )

    # --------------------------------------------------
    # DATABASE
    # --------------------------------------------------

    if DATABASE_URL:
        SQLALCHEMY_DATABASE_URI = DATABASE_URL
    else:
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(INSTANCE_PATH, 'apv_monitor.db')}"

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SQLALCHEMY_ENGINE_OPTIONS = {
        "connect_args": {
            "check_same_thread": False
        },
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "pool_size": 5,
        "max_overflow": 10
    }

    # --------------------------------------------------
    # MAIL CONFIGURATION
    # --------------------------------------------------

    MAIL_SERVER = env(
        "MAIL_SERVER",
        "smtp.office365.com"
    )

    MAIL_PORT = env_int(
        "MAIL_PORT",
        587
    )

    MAIL_USE_TLS = True
    MAIL_USE_SSL = False

    MAIL_USERNAME = env("MAIL_USERNAME")
    MAIL_PASSWORD = env("MAIL_PASSWORD")

    MAIL_DEFAULT_SENDER = (
        env("MAIL_SENDER_NAME", "APV Monitor Pro"),
        MAIL_USERNAME
    )

    # Prevent SMTP crashes on Render free plan
    MAIL_SUPPRESS_SEND = env_bool(
        "MAIL_SUPPRESS_SEND",
        True
    )

    MAIL_MAX_EMAILS = None

    # --------------------------------------------------
    # TELEGRAM ALERT SYSTEM
    # --------------------------------------------------

    TELEGRAM_BOT_TOKEN = env("TELEGRAM_BOT_TOKEN")

    TELEGRAM_CHAT_ID = env("TELEGRAM_CHAT_ID")

    TELEGRAM_API_URL = "https://api.telegram.org"

    TELEGRAM_TIMEOUT = env_int(
        "TELEGRAM_TIMEOUT",
        10
    )

    TELEGRAM_RETRIES = env_int(
        "TELEGRAM_RETRIES",
        3
    )

    # --------------------------------------------------
    # MONITORING ENGINE
    # --------------------------------------------------

    # Faster failure detection
    MONITOR_TIMEOUT = env_int(
        "MONITOR_TIMEOUT",
        5
    )

    DEFAULT_CHECK_INTERVAL = env_int(
        "DEFAULT_CHECK_INTERVAL",
        60
    )

    MAX_MONITOR_RETRIES = env_int(
        "MAX_MONITOR_RETRIES",
        2
    )

    MONITOR_RETRY_DELAY = env_int(
        "MONITOR_RETRY_DELAY",
        2
    )

    SLOW_RESPONSE_THRESHOLD = env_float(
        "SLOW_RESPONSE_THRESHOLD",
        2.0
    )

    # --------------------------------------------------
    # ALERT THRESHOLDS
    # --------------------------------------------------

    FAILURE_THRESHOLD = env_int(
        "FAILURE_THRESHOLD",
        3
    )

    RECOVERY_THRESHOLD = env_int(
        "RECOVERY_THRESHOLD",
        2
    )

    SSL_EXPIRING_DAYS = env_int(
        "SSL_EXPIRING_DAYS",
        15
    )

    # --------------------------------------------------
    # SSL MONITORING
    # --------------------------------------------------

    SSL_CHECK_INTERVAL_HOURS = env_int(
        "SSL_CHECK_INTERVAL_HOURS",
        12
    )

    # --------------------------------------------------
    # SCHEDULER SETTINGS
    # --------------------------------------------------

    # Render-safe scheduler interval
    SCHEDULER_INTERVAL_SECONDS = env_int(
        "SCHEDULER_INTERVAL_SECONDS",
        60
    )

    MAX_WORKER_THREADS = env_int(
        "MAX_WORKER_THREADS",
        1
    )

    # --------------------------------------------------
    # HTTP REQUEST SETTINGS
    # --------------------------------------------------

    MONITOR_USER_AGENT = env(
        "MONITOR_USER_AGENT",
        "APV Monitor Pro Monitoring Engine"
    )

    FOLLOW_REDIRECTS = True

    # --------------------------------------------------
    # ENVIRONMENT
    # --------------------------------------------------

    DEBUG = env_bool(
        "DEBUG",
        False
    )

    ENV = env(
        "FLASK_ENV",
        "production"
    )


# ======================================================
# ENVIRONMENT VALIDATION
# ======================================================

REQUIRED_ENV_VARS = [
    "MAIL_USERNAME",
    "MAIL_PASSWORD",
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_CHAT_ID"
]

for var in REQUIRED_ENV_VARS:

    if not os.getenv(var):

        print(
            f"⚠️ Warning: Environment variable '{var}' is not set"
        )