"""Persistent manager quick-message buttons."""
from services.database import db

class QuickButton(db.Model):
    __tablename__ = "quick_buttons"
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(80), nullable=False)
    message = db.Column(db.String(500), nullable=False)
    is_custom = db.Column(db.Boolean, nullable=False, default=True)
    hidden = db.Column(db.Boolean, nullable=False, default=False)
    sort_order = db.Column(db.Integer, nullable=False, default=0)
    def to_dict(self):
        return {"id": self.id, "label": self.label, "message": self.message, "is_custom": self.is_custom, "hidden": self.hidden}