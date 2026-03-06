from extensions import db
from datetime import datetime


class MonitorLog(db.Model):
    """
    APV Monitor Pro
    Monitor Log Model

    Stores every monitoring check result.

    Used for:
    - uptime analytics
    - response time graphs
    - activity charts
    - incident detection
    - SLA calculations
    - debugging failures
    """

    __tablename__ = "monitor_logs"

    # ======================================================
    # PRIMARY KEY
    # ======================================================

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # ======================================================
    # RELATIONSHIP
    # ======================================================

    monitor_id = db.Column(
        db.Integer,
        db.ForeignKey("monitors.id"),
        nullable=False,
        index=True
    )

    # ======================================================
    # STATUS DATA
    # ======================================================

    status = db.Column(
        db.String(20),
        nullable=False,
        index=True
    )
    # Possible values:
    # UP / DOWN / SLOW

    response_time = db.Column(
        db.Float,
        nullable=True
    )
    # seconds

    latency_ms = db.Column(
        db.Integer,
        nullable=True
    )
    # precise latency

    http_status_code = db.Column(
        db.Integer,
        nullable=True
    )

    error_message = db.Column(
        db.String(500),
        nullable=True
    )
    # timeout / connection error / ssl error etc

    # ======================================================
    # MONITORING META
    # ======================================================

    location = db.Column(
        db.String(50),
        nullable=True
    )
    # monitoring node location (future multi-region support)

    is_alert_sent = db.Column(
        db.Boolean,
        default=False
    )

    # ======================================================
    # TIMESTAMPS
    # ======================================================

    checked_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    # ======================================================
    # TABLE OPTIMIZATION
    # ======================================================

    __table_args__ = (

        # monitor timeline queries
        db.Index(
            "idx_monitor_time",
            "monitor_id",
            "checked_at"
        ),

        # uptime calculations
        db.Index(
            "idx_monitor_status",
            "monitor_id",
            "status"
        ),

    )

    # ======================================================
    # HELPER METHODS
    # ======================================================

    def is_up(self):
        return self.status == "UP"

    def is_down(self):
        return self.status == "DOWN"

    def is_slow(self):
        return self.status == "SLOW"

    # ======================================================
    # REPRESENTATION
    # ======================================================

    def __repr__(self):

        return (
            f"<MonitorLog "
            f"id={self.id} "
            f"monitor={self.monitor_id} "
            f"status={self.status} "
            f"response={self.response_time}s "
            f"http={self.http_status_code} "
            f"time={self.checked_at}>"
        )