from flask import Blueprint, redirect, render_template, request, url_for, flash
from flask_login import current_user, login_required
from models import User, Friendship
from app import db
from services.notifications_service import add_notification
from Proxies.adminProxy import restriction_proxy

friends_bp = Blueprint("friends", __name__, url_prefix="/friends")

@friends_bp.route("/")
@login_required
def list_friends():
    friends = Friendship.query.filter(
        ((Friendship.sender_id == current_user.id) |
         (Friendship.receiver_id == current_user.id)),
        Friendship.status == "accepted"
    ).all()

    received_requests = Friendship.query.filter_by(
        receiver_id=current_user.id,
        status="pending"
    ).all()

    all_users = User.query.filter(User.id != current_user.id).all()

    relations = Friendship.query.filter(
        (Friendship.sender_id == current_user.id) |
        (Friendship.receiver_id == current_user.id)
    ).all()

    relation_status = {}

    for r in relations:
        other_id = r.receiver_id if r.sender_id == current_user.id else r.sender_id

        if r.status == "accepted":
            relation_status[other_id] = "accepted"
        elif r.sender_id == current_user.id:
            relation_status[other_id] = "pending_sent"
        else:
            relation_status[other_id] = "pending_received"

    return render_template(
        "friends.html",
        friends=friends,
        received_requests=received_requests,
        users=all_users,
        relation_status=relation_status
    )


@friends_bp.route("/add/<int:user_id>")
@login_required
@restriction_proxy
def send_request(user_id):
    if user_id == current_user.id:
        flash("Nu poti sa iti trimiti cerere singur!", "warning")
        return redirect(url_for("friends.list_friends"))

    existing = Friendship.query.filter(
        ((Friendship.sender_id == current_user.id) & (Friendship.receiver_id == user_id)) |
        ((Friendship.sender_id == user_id) & (Friendship.receiver_id == current_user.id))
    ).first()

    if existing:
        flash("Cerere deja trimisa!", "info")
        return redirect(url_for("friends.list_friends"))

    req = Friendship(sender_id=current_user.id, receiver_id=user_id)
    db.session.add(req)
    db.session.commit()

    add_notification(user_id, f"{current_user.username} ti-a trimis o cerere de prietenie!","info")
    
    flash("Cerere trimisa!", "success")
    return redirect(url_for("friends.list_friends"))


@friends_bp.route("/accept/<int:req_id>")
@login_required
@restriction_proxy
def accept(req_id):
    req = Friendship.query.get(req_id)
    if req and req.receiver_id == current_user.id:
        req.status = "accepted"
        db.session.commit()
        flash("Cerere acceptata!", "success")
    
    return redirect(url_for("friends.list_friends"))

@friends_bp.route("/reject/<int:req_id>")
@login_required
def reject(req_id):
    req = Friendship.query.get(req_id)
    if req and req.receiver_id == current_user.id:
        db.session.delete(req)
        db.session.commit()
        flash("Cerere respinsa!", "info")
    return redirect(url_for("friends.list_friends"))


@friends_bp.route("/remove/<int:friend_id>")
@login_required
def remove(friend_id):
    f = Friendship.query.get(friend_id)
    if f and (f.sender_id == current_user.id or f.receiver_id == current_user.id):
        db.session.delete(f)
        db.session.commit()
        flash("Prieten sters!", "warning")
    return redirect(url_for("friends.list_friends"))

