from extensions import db
from datetime import datetime


class Incident(db.Model):
    """
    APV Monitor Pro
    Incident Model

    Represents a downtime or issue detected by the monitoring engine.
    """

    __tablename__ = "incidents"

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
    # INCIDENT TYPE (PRESERVED)
    # ======================================================

    # ⚠️ DO NOT REMOVE (existing system dependency)
    status = db.Column(
        db.String(50),
        nullable=False,
        index=True
    )
    # DOWN / SSL_EXPIRING / SSL_EXPIRED / SLOW

    message = db.Column(
        db.String(500),
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        index=True
    )

    # ======================================================
    # INCIDENT LIFECYCLE
    # ======================================================

    lifecycle_status = db.Column(
        db.String(20),
        default="ONGOING",
        nullable=False,
        index=True
    )
    # ONGOING / RESOLVED

    started_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )

    resolved_at = db.Column(
        db.DateTime,
        nullable=True,
        index=True
    )

    duration_seconds = db.Column(
        db.Integer,
        nullable=True
    )

    # ======================================================
    # ROOT CAUSE INFORMATION
    # ======================================================

    root_cause = db.Column(
        db.String(255),
        default="Unknown"
    )
    # Timeout / HTTP 500 / SSL / DNS / etc

    http_status_code = db.Column(
        db.Integer,
        nullable=True
    )

    # ======================================================
    # VISIBILITY (STATUS PAGE FUTURE FEATURE)
    # ======================================================

    visibility = db.Column(
        db.String(20),
        default="PUBLIC"
    )
    # PUBLIC / PRIVATE

    # ======================================================
    # COMMENTS (FUTURE INCIDENT DISCUSSION)
    # ======================================================

    comment_count = db.Column(
        db.Integer,
        default=0
    )

    # ======================================================
    # HELPER METHODS
    # ======================================================

    def resolve(self):
        """
        Safely resolve the incident.
        """

        if self.lifecycle_status == "RESOLVED":
            return

        self.lifecycle_status = "RESOLVED"
        self.resolved_at = datetime.utcnow()

        self.calculate_duration()

    def calculate_duration(self):
        """
        Calculates incident duration in seconds.
        """

        if self.started_at and self.resolved_at:

            duration = (
                self.resolved_at - self.started_at
            ).total_seconds()

            self.duration_seconds = int(duration)

    # ======================================================
    # REPRESENTATION
    # ======================================================

    def __repr__(self):

        return (
            f"<Incident "
            f"id={self.id} "
            f"monitor={self.monitor_id} "
            f"type={self.status} "
            f"state={self.lifecycle_status}>"
        )