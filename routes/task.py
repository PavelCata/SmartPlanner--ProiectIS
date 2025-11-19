from flask import Blueprint, request, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime, date, time

from app import db
from models import Task

tasks_bp = Blueprint("tasks", __name__)

def parse_time_str(t_str: str) -> time:
    return datetime.strptime(t_str, "%H:%M").time()


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
            return redirect(
                url_for("tasks.view_tasks", date=selected_date.isoformat())
            )

        existing_tasks = Task.query.filter_by(
            user_id=current_user.id,
            date=selected_date
        ).all()

        for t in existing_tasks:
            if not (end_time <= t.start_time or start_time >= t.end_time):
                flash(
                    f"Interval ocupat de task-ul '{t.title}' "
                    f"({t.start_time.strftime('%H:%M')}-{t.end_time.strftime('%H:%M')}).",
                    "danger"
                )
                return redirect(
                    url_for("tasks.view_tasks", date=selected_date.isoformat())
                )

        new_task = Task(
            user_id=current_user.id,
            date=selected_date,
            start_time=start_time,
            end_time=end_time,
            title=title,
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
