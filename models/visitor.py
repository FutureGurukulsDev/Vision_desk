"""Visitor database model."""
from datetime import datetime, timezone
from services.database import db

class Visitor(db.Model):
    __tablename__ = "visitors"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, index=True)
    company = db.Column(db.String(120), nullable=False, index=True)
    phone = db.Column(db.String(40), nullable=False)
    email = db.Column(db.String(160), nullable=True)
    purpose = db.Column(db.String(255), nullable=False, index=True)
    person_to_meet = db.Column(db.String(120), nullable=False)
    photo_path = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(40), nullable=False, default="Waiting", index=True)
    arrival_time = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    messages = db.relationship("Message", back_populates="visitor", cascade="all, delete-orphan", lazy="dynamic")
    photos = db.relationship("VisitorPhoto", back_populates="visitor", cascade="all, delete-orphan", lazy="select", order_by="VisitorPhoto.id")

    def to_dict(self):
        photo_paths = [photo.path for photo in self.photos]
        if self.photo_path and self.photo_path not in photo_paths:
            photo_paths.insert(0, self.photo_path)
        return {"id": self.id, "name": self.name, "company": self.company, "phone": self.phone,
                "email": self.email, "purpose": self.purpose, "person_to_meet": self.person_to_meet,
                "photo_path": self.photo_path, "photo_paths": photo_paths, "status": self.status,
                "arrival_time": self.arrival_time.isoformat(),
                "arrival_display": self.arrival_time.strftime("%d %b %Y, %I:%M %p")}