from flask import Blueprint, redirect, render_template, request, url_for, flash
from flask_login import current_user, login_required
from models import User, Friendship, Notification, Task
from app import db
from services.notifications_service import add_notification
from Proxies.adminProxy import restriction_proxy
from datetime import datetime, timedelta
from builder.task_builder import TaskBuilder, TaskDTO
from services.task_service import save_task



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


ALLOWED_SHARED_TASKS = {"Gym", "Plimbare", "Cafea", "Biblioteca"}

def _parse_invite(text: str):
    if not text or not text.startswith("TASK_INVITE|"):
        return None
    parts = text.split("|")[1:]
    d = {}
    for p in parts:
        if "=" in p:
            k, v = p.split("=", 1)
            d[k] = v
    if "from" not in d or "task" not in d:
        return None
    return {"from_id": int(d["from"]), "task": d["task"]}

def _has_conflict(user_id, date_obj, start_t, end_t):
    tasks = Task.query.filter_by(user_id=user_id, date=date_obj).all()
    for t in tasks:
        if not (end_t <= t.start_time or start_t >= t.end_time):
            return True
    return False


@friends_bp.route("/invite_task/<int:friend_id>/<string:task_name>")
@login_required
@restriction_proxy
def invite_task(friend_id, task_name):
    task_name = (task_name or "").strip()

    if task_name not in ALLOWED_SHARED_TASKS:
        flash("Task invalid.", "danger")
        return redirect(url_for("friends.list_friends"))

    payload = f"TASK_INVITE|from={current_user.id}|task={task_name}"
    add_notification(friend_id, payload, "info")

    flash("Invitatia a fost trimis.", "success")
    return redirect(url_for("friends.list_friends"))


@friends_bp.route("/invite_task/schedule/<int:notif_id>", methods=["GET", "POST"])
@login_required
@restriction_proxy
def schedule_invite_task(notif_id):
    n = Notification.query.get_or_404(notif_id)

    if n.user_id != current_user.id:
        flash("Nu ai acces la invitatia asta.", "danger")
        return redirect(url_for("friends.list_friends"))

    data = _parse_invite(n.text)
    if not data:
        flash("Invitatie invalida.", "danger")
        return redirect(url_for("friends.list_friends"))

    sender_id = data["from_id"]
    task_name = data["task"]

    sender_user = User.query.get(sender_id)
    if not sender_user:
        flash("Prietenul nu mai exista.", "danger")
        return redirect(url_for("friends.list_friends"))

    if request.method == "GET":
        return render_template("invite_schedule.html", notif=n, task_name=task_name)

    day = request.form.get("day")  
    start_str = request.form.get("start")
    end_str = request.form.get("end")

    date_obj = datetime.today().date()
    if day == "tomorrow":
        date_obj = date_obj + timedelta(days=1)

    try:
        start_t = datetime.strptime(start_str, "%H:%M").time()
        end_t = datetime.strptime(end_str, "%H:%M").time()
    except:
        flash("Ore invalide.", "danger")
        return redirect(url_for("friends.schedule_invite_task", notif_id=notif_id))

    if start_t >= end_t:
        flash("Ora de start trebuie sa fie mai mica decat ora de final.", "danger")
        return redirect(url_for("friends.schedule_invite_task", notif_id=notif_id))

    if _has_conflict(current_user.id, date_obj, start_t, end_t) or _has_conflict(sender_id, date_obj, start_t, end_t):
        flash("Conflict in program (la tine sau la prieten). Alege alt interval.", "warning")
        return redirect(url_for("friends.schedule_invite_task", notif_id=notif_id))

    # creeaza task la amandoi 
    t_receiver = TaskBuilder().from_dto(TaskDTO(
        user_id=current_user.id,
        date=date_obj,
        start_time=start_t,
        end_time=end_t,
        title=task_name,  
        importance="medium",
        low_mode=None
    )).build()
    t_receiver.title = f"{task_name} (cu {sender_user.username})"

    t_sender = TaskBuilder().from_dto(TaskDTO(
        user_id=sender_id,
        date=date_obj,
        start_time=start_t,
        end_time=end_t,
        title=task_name, 
        importance="medium",
        low_mode=None
    )).build()
    t_sender.title = f"{task_name} (cu {current_user.username})"

    save_task(t_receiver)
    save_task(t_sender)

    n.seen = True
    n.text = f"TASK_INVITE_ACCEPTED|from={sender_id}|task={task_name}"
    db.session.commit()

    add_notification(
        sender_id,
        f"{current_user.username} a ACCEPTAT: {task_name} ({date_obj.isoformat()} {start_str}-{end_str})",
        "success"
    )

    flash("Task creat la amandoi ", "success")
    return redirect(url_for("tasks.view_tasks", date=date_obj.isoformat()))



@friends_bp.route("/invite_task/reject/<int:notif_id>")
@login_required
@restriction_proxy
def reject_invite_task(notif_id):
    n = Notification.query.get_or_404(notif_id)

    if n.user_id != current_user.id:
        flash("Nu ai acces la invitatia asta.", "danger")
        return redirect(url_for("friends.list_friends"))

    data = _parse_invite(n.text)
    if not data:
        flash("Invitatie invalida.", "danger")
        return redirect(url_for("friends.list_friends"))

    sender_id = data["from_id"]
    task_name = data["task"]

    sender_user = User.query.get(sender_id)
    if not sender_user:
        flash("Prietenul nu mai exista.", "danger")
        return redirect(url_for("friends.list_friends"))


    n.seen = True
    n.text = f"TASK_INVITE_REJECTED|from={sender_id}|task={task_name}"
    db.session.commit()

    add_notification(sender_id, f"{current_user.username} a REFUZAT: {task_name}", "warning")
    flash("Ai refuzat invitatia.", "info")
    return redirect(url_for("friends.list_friends"))
