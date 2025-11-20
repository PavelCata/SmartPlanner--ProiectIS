from flask import Blueprint, redirect, render_template, request, url_for, flash
from flask_login import current_user, login_required
from models import User, Friendship
from app import db

friends_bp = Blueprint("friends", __name__, url_prefix="/friends")

@friends_bp.route("/")
@login_required
def list_friends():
    friends = Friendship.query.filter(
        ((Friendship.sender_id == current_user.id) | 
         (Friendship.receiver_id == current_user.id)),
        Friendship.status == "accepted"
    ).all()

    pending = Friendship.query.filter_by(receiver_id=current_user.id, status="pending").all()

    users = User.query.filter(User.id != current_user.id).all()

    return render_template(
        "friends.html",
        friends=friends,
        received_requests=pending,  
        users=users
    )

@friends_bp.route("/add/<int:user_id>")
@login_required
def send_request(user_id):
    if user_id == current_user.id:
        flash("Nu poti sa iti trimiti cerere singur!", "warning")
        return redirect(url_for("friends.list_friends"))

    existing = Friendship.query.filter(
        ((Friendship.sender_id == current_user.id) & (Friendship.receiver_id == user_id)) |
        ((Friendship.sender_id == user_id) & (Friendship.receiver_id == current_user.id))
    ).first()

    if existing:
        flash("Există deja o conexiune sau cerere!", "info")
        return redirect(url_for("friends.list_friends"))

    req = Friendship(sender_id=current_user.id, receiver_id=user_id)
    db.session.add(req)
    db.session.commit()

    flash("Cerere trimisa!", "success")
    return redirect(url_for("friends.list_friends"))


@friends_bp.route("/accept/<int:req_id>")
@login_required
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

