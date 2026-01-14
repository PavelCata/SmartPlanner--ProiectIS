from app import db
from models import Notification

def add_notification(user_id, message, category="info"):
    notif = Notification(
        user_id=user_id,
        message=message,
        category=category,
        seen=False
    )
    db.session.add(notif)
    db.session.commit()
