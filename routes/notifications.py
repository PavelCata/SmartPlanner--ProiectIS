from flask import Blueprint, redirect, url_for
from flask_login import login_required, current_user
from app import db
from models import Notification

def add_notification(user_id, text, type="info"):
    n = Notification(user_id=user_id, text=text, type=type)
    db.session.add(n)
    db.session.commit()


notifications_bp = Blueprint("notifications", __name__, url_prefix="/notifications")

@notifications_bp.route("/clear")
@login_required
def clear_notifications():
    Notification.query.filter_by(user_id=current_user.id, seen=False)\
                      .update({"seen": True})

    db.session.commit()

    return redirect(url_for("home.index"))