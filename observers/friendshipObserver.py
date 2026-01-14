from sqlalchemy import event
from app import db
from models import Friendship, Notification

@event.listens_for(Friendship, "after_update")
def after_friendship_update(mapper, connection, target):
    if target.status == "accepted":
        notif = Notification(
            user_id=target.sender_id,
            text="Cererea ta de prietenie a fost acceptata! 🎉", 
            type="success", 
        )
        db.session.add(notif)
