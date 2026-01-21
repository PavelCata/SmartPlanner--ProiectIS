from flask import Blueprint, redirect, url_for
from flask_login import login_required, current_user
from app import db
from services.notifications_service import mark_seen_bulk
from services.notifications_service import create_notification
from services.notifications_service import delete_all_notifications


def add_notification(user_id, text, type="info"):
    return create_notification(user_id=user_id, text=text, type=type, source="legacy")

notifications_bp = Blueprint("notifications", __name__, url_prefix="/notifications")


@notifications_bp.route("/clear")
@login_required
def clear_notifications():
    delete_all_notifications(current_user.id)
    return redirect(url_for("home.index"))



@notifications_bp.route("/seen")
@login_required
def mark_seen():
    mark_seen_bulk(current_user.id)
    return ("", 204)
