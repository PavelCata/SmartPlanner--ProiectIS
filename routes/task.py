from flask import Blueprint, request, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime, date, time, timedelta
from app import db
from models import Task
from routes.notifications import add_notification

tasks_bp = Blueprint("tasks", __name__)

def parse_time_str(t_str: str) -> time:
    return datetime.strptime(t_str, "%H:%M").time()

def to_minutes(t):
    return t.hour * 60 + t.minute

def from_minutes(m):
    return time(m // 60, m % 60)

def find_free_slot(existing, duration):
    if not existing:
        return time(8, 0), from_minutes(8 * 60 + duration)
    current = to_minutes(existing[0].start_time)
    if current - 8 * 60 >= duration:
        return time(8, 0), from_minutes(8 * 60 + duration)
    for i in range(len(existing) - 1):
        end_prev = to_minutes(existing[i].end_time)
        start_next = to_minutes(existing[i+1].start_time)
        if start_next - end_prev >= duration:
            return from_minutes(end_prev), from_minutes(end_prev + duration)
    last_end = to_minutes(existing[-1].end_time)
    if 22*60 - last_end >= duration:
        return from_minutes(last_end), from_minutes(last_end + duration)
    return None

def move_task_to_next_day(task):
    original_date = task.date
    original_start = task.start_time.strftime("%H:%M")
    original_end = task.end_time.strftime("%H:%M")
    duration = to_minutes(task.end_time) - to_minutes(task.start_time)
    existing_today = Task.query.filter_by(
        user_id=task.user_id, date=task.date
    ).order_by(Task.start_time).all()
    existing_today = [t for t in existing_today if t.id != task.id]
    slot_today = find_free_slot(existing_today, duration)
    if slot_today:
        task.start_time, task.end_time = slot_today
        db.session.commit()
        flash(
            f"Taskul '{task.title}' a fost mutat in aceeasi zi ({task.date}) "
            f"la intervalul {task.start_time.strftime('%H:%M')}-"
            f"{task.end_time.strftime('%H:%M')} din cauza unui conflict.",
            "warning"
        )
        return

    next_day = task.date + timedelta(days=1)
    while True:
        existing = Task.query.filter_by(
            user_id=task.user_id, date=next_day
        ).order_by(Task.start_time).all()
        slot = find_free_slot(existing, duration)
        if slot:
            task.date = next_day
            task.start_time, task.end_time = slot
            db.session.commit()
            flash(
                f"Taskul '{task.title}' a fost mutat din {original_date} "
                f"({original_start}-{original_end}) în {task.date} "
                f"({task.start_time.strftime('%H:%M')}-{task.end_time.strftime('%H:%M')}) "
                f"pentru a-i gasi un loc liber.",
                "warning"
            )
            return
        next_day += timedelta(days=1)


@tasks_bp.route("/tasks", methods=["GET", "POST"])
@login_required
def view_tasks():
    date_str = request.values.get("date")
    if date_str:
        try:
            selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            flash("Data invalida, am folosit data de azi.", "warning")
            selected_date = date.today()
    else:
        selected_date = date.today()
        
    if request.method == "POST":        
        start_str = request.form.get("start")
        end_str = request.form.get("end")
        title = (request.form.get("title") or "").strip()

        importance = request.form.get("importance")
        low_mode = request.form.get("low_mode", None)
        
        if not (start_str and end_str and title):
            flash("Te rog completeaza toate campurile.", "danger")
            return redirect(url_for("tasks.view_tasks", date=selected_date.isoformat()))
        
        try:
            start_time = parse_time_str(start_str)
            end_time = parse_time_str(end_str)
        except ValueError:
            flash("Format invalid pentru ore (foloseste HH:MM).", "danger")
            return redirect(url_for("tasks.view_tasks", date=selected_date.isoformat()))

        if start_time >= end_time:
            flash("Ora de start trebuie sa fie mai mica decat ora de final.", "danger")
            return redirect(url_for("tasks.view_tasks", date=selected_date.isoformat()))

        duration = to_minutes(end_time) - to_minutes(start_time)
       
        existing = Task.query.filter_by(
            user_id=current_user.id, date=selected_date
        ).order_by(Task.start_time).all()

        if importance == "high":
            for t in existing:
                if not (end_time <= t.start_time or start_time >= t.end_time):
                    move_task_to_next_day(t)

        if importance == "medium":
            for t in existing:
                if not (end_time <= t.start_time or start_time >= t.end_time):
                    if t.importance == "low":
                        move_task_to_next_day(t)
                    else:
                        flash("Nu poti suprascrie un task important sau mediu!", "danger")
                        return redirect(url_for("tasks.view_tasks", date=selected_date.isoformat()))

        if importance == "low":
            if low_mode == "random":
                slot = find_free_slot(existing, duration)
                if slot:
                    start_time, end_time = slot
                else:
                    selected_date += timedelta(days=1)
                    start_time, end_time = time(9, 0), time(10, 0)
            else: 
                for t in existing:
                    if not (end_time <= t.start_time or start_time >= t.end_time):
                        move_task_to_next_day(t)

        new_task = Task(
            user_id=current_user.id,
            date=selected_date,
            start_time=start_time,
            end_time=end_time,
            title=title,
            importance=importance,
            low_mode=low_mode
        )

        db.session.add(new_task)
        db.session.commit()

        flash("Task creat cu succes.", "success")
        return redirect(url_for("tasks.view_tasks", date=selected_date.isoformat()))

    tasks = (
        Task.query
        .filter_by(user_id=current_user.id, date=selected_date)
        .order_by(Task.start_time)
        .all()
    )

    return render_template("index.html", selected_date=selected_date, tasks=tasks)


@tasks_bp.route("/tasks/<int:task_id>/delete", methods=["POST", "GET"])
@login_required
def delete_task(task_id):
   
    date_str = request.values.get("date")
    redirect_date = None
    if date_str:
        try:
            redirect_date = datetime.strptime(date_str, "%Y-%m-%d").date().isoformat()
        except ValueError:
            redirect_date = None

    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first()

    if not task:
        flash("Task inexistent sau nu ai drepturi asupra lui.", "danger")
    else:
        db.session.delete(task)
        db.session.commit()
        flash("Task sters.", "info")
        if redirect_date is None:
            redirect_date = task.date.isoformat()

    if redirect_date:
        return redirect(url_for("tasks.view_tasks", date=redirect_date))
    return redirect(url_for("tasks.view_tasks"))