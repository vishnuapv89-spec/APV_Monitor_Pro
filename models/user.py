from extensions import db
from datetime import datetime, timedelta


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    # ================= BASIC INFO =================
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password = db.Column(db.String(255), nullable=False)

    # ================= ROLE SYSTEM =================
    role = db.Column(db.String(50), default="viewer")
    # superadmin / admin / viewer

    # ================= ACCOUNT STATUS =================
    is_verified = db.Column(db.Boolean, default=False)

    # ================= TELEGRAM INTEGRATION =================

    # Telegram chat id (received from bot)
    telegram_chat_id = db.Column(db.String(100), nullable=True)

    # Whether telegram is connected
    telegram_connected = db.Column(db.Boolean, default=False)

    # Whether telegram alerts are enabled
    telegram_alerts_enabled = db.Column(db.Boolean, default=True)

    # Time of connection
    telegram_connected_at = db.Column(db.DateTime, nullable=True)

    # Secure token used for connecting telegram
    telegram_connect_token = db.Column(
        db.String(120),
        nullable=True,
        index=True
    )

    # Token creation time
    telegram_token_created_at = db.Column(
        db.DateTime,
        nullable=True
    )

    # ================= AUDIT FIELDS =================
    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    # ================= RELATIONSHIP =================
    monitors = db.relationship(
        "Monitor",
        backref="owner",
        lazy=True,
        cascade="all, delete",
        foreign_keys="Monitor.user_id"
    )

    # ================= HELPER METHODS =================

    def connect_telegram(self, chat_id):
        """
        Link user's Telegram account
        """

        self.telegram_chat_id = str(chat_id)
        self.telegram_connected = True
        self.telegram_connected_at = datetime.utcnow()

        # Clear token after successful connection
        self.telegram_connect_token = None
        self.telegram_token_created_at = None

    def disconnect_telegram(self):
        """
        Remove Telegram integration
        """

        self.telegram_chat_id = None
        self.telegram_connected = False
        self.telegram_connected_at = None
        self.telegram_connect_token = None
        self.telegram_token_created_at = None

    def telegram_ready(self):
        """
        Check if Telegram alerts can be sent
        """

        if (
            self.telegram_connected
            and self.telegram_chat_id
            and self.telegram_alerts_enabled
        ):
            return True

        return False

    def telegram_token_valid(self):
        """
        Token expiry check (15 minutes validity)
        """

        if not self.telegram_token_created_at:
            return False

        expiry = self.telegram_token_created_at + timedelta(minutes=15)

        return datetime.utcnow() <= expiry

    def __repr__(self):
        return f"<User {self.email}>"