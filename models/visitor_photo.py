"""Additional photos attached to a visitor registration."""
from services.database import db

class VisitorPhoto(db.Model):
    __tablename__ = "visitor_photos"
    id = db.Column(db.Integer, primary_key=True)
    visitor_id = db.Column(db.Integer, db.ForeignKey("visitors.id"), nullable=False, index=True)
    path = db.Column(db.String(255), nullable=False)
    visitor = db.relationship("Visitor", back_populates="photos")