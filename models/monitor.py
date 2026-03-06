from extensions import db
from datetime import datetime


class Monitor(db.Model):
    """
    APV Monitor Pro
    Monitor Model

    Represents a monitored endpoint (URL).
    """

    __tablename__ = "monitors"

    # ======================================================
    # PRIMARY KEY
    # ======================================================

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # ======================================================
    # MONITOR INFORMATION
    # ======================================================

    url = db.Column(
        db.String(500),
        nullable=False,
        index=True
    )

    status = db.Column(
        db.String(20),
        default="UNKNOWN",
        nullable=False,
        index=True
    )
    # Possible values:
    # UNKNOWN / UP / DOWN / SLOW

    response_time = db.Column(
        db.Float,
        nullable=True
    )

    # ======================================================
    # MONITOR CONTROL
    # ======================================================

    is_paused = db.Column(
        db.Boolean,
        default=False,
        nullable=False,
        index=True
    )

    check_interval = db.Column(
        db.Integer,
        default=60,
        nullable=False
    )

    last_checked_at = db.Column(
        db.DateTime,
        nullable=True,
        index=True
    )

    # ======================================================
    # FAILURE / RECOVERY COUNTERS
    # ======================================================

    failure_count = db.Column(
        db.Integer,
        default=0,
        nullable=False
    )

    recovery_count = db.Column(
        db.Integer,
        default=0,
        nullable=False
    )

    # ======================================================
    # SSL INFORMATION
    # ======================================================

    ssl_expiry_date = db.Column(
        db.DateTime,
        nullable=True
    )

    ssl_days_remaining = db.Column(
        db.Integer,
        default=0
    )

    last_ssl_check = db.Column(
        db.DateTime,
        nullable=True,
        index=True
    )

    # ======================================================
    # TIMESTAMPS
    # ======================================================

    last_checked = db.Column(
        db.DateTime,
        nullable=True,
        index=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )

    # ======================================================
    # USER OWNERSHIP (MULTI USER SUPPORT)
    # ======================================================

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    # IMPORTANT
    # This column already exists in database
    # so we must define it in model

    created_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    # ======================================================
    # RELATIONSHIPS
    # ======================================================

    incidents = db.relationship(
        "Incident",
        backref="monitor",
        lazy="select",
        cascade="all, delete-orphan"
    )

    logs = db.relationship(
        "MonitorLog",
        backref="monitor",
        lazy="select",
        cascade="all, delete-orphan"
    )

    # ======================================================
    # HELPER METHODS
    # ======================================================

    def reset_failure(self):
        self.failure_count = 0

    def reset_recovery(self):
        self.recovery_count = 0

    def increment_failure(self):
        self.failure_count += 1

    def increment_recovery(self):
        self.recovery_count += 1

    def is_active(self):
        """
        Check if monitor should run
        """
        return not self.is_paused

    # ======================================================
    # REPRESENTATION
    # ======================================================

    def __repr__(self):
        return f"<Monitor id={self.id} url={self.url} status={self.status}>"