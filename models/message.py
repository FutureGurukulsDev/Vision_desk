"""Manager and reception message database model."""

from datetime import datetime, timezone

from services.database import db


class Message(db.Model):
    """Stores realtime instructions and status notes for visitors."""

    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    visitor_id = db.Column(db.Integer, db.ForeignKey("visitors.id"), nullable=True)
    sender = db.Column(db.String(80), nullable=False)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

    visitor = db.relationship("Visitor", back_populates="messages")

    def to_dict(self) -> dict:
        """Return a JSON-friendly representation for SocketIO and APIs."""
        return {
            "id": self.id,
            "visitor_id": self.visitor_id,
            "sender": self.sender,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "timestamp_display": self.timestamp.strftime("%d %b %Y, %I:%M %p"),
        }
