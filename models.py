from app import db
from flask_login import UserMixin

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(10), nullable=False, default="user")
    restricted = db.Column(db.Boolean, default=False)

    tasks = db.relationship("Task", backref="user", lazy=True, cascade="all,delete")


class Task(db.Model):
    __tablename__ = "tasks"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    title = db.Column(db.String(255), nullable=False)
    importance = db.Column(db.String(10), nullable=False, default="medium")  
    low_mode = db.Column(db.String(10), nullable=True)
    status = db.Column(db.String(10), nullable=False, default="pending")
    def to_dict(self):
        return {
            "id": self.id,
            "date": self.date.isoformat(),
            "start": self.start_time.strftime("%H:%M"),
            "end": self.end_time.strftime("%H:%M"),
            "title": self.title,
            "importance": self.importance,
            "low_mode": self.low_mode,
            "status": self.status,
        }

class Friendship(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    status = db.Column(db.String(20), default="pending")

    sender = db.relationship("User", foreign_keys=[sender_id])
    receiver = db.relationship("User", foreign_keys=[receiver_id])

from datetime import datetime

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    text = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(20), default="info")
    seen = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(20), nullable=False, default="unseen")
    category = db.Column(db.String(20), nullable=True)
    source = db.Column(db.String(40), nullable=True)
    priority = db.Column(db.String(10), nullable=False, default="normal")
    dedupe_key = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    delivered_at = db.Column(db.DateTime, nullable=True)
    seen_at = db.Column(db.DateTime, nullable=True)
    archived_at = db.Column(db.DateTime, nullable=True)
    deleted_at = db.Column(db.DateTime, nullable=True)

from datetime import datetime

class NotificationPreference(db.Model):
    __tablename__ = "notification_preference"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), unique=True, nullable=False)
    quiet_enabled = db.Column(db.Boolean, default=False, nullable=False)
    quiet_start = db.Column(db.Time, nullable=True)
    quiet_end = db.Column(db.Time, nullable=True)
    allow_social = db.Column(db.Boolean, default=True, nullable=False)
    allow_tasks = db.Column(db.Boolean, default=True, nullable=False)
    allow_insights = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, nullable=True)

