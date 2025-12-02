from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user, login_required
from models import Task
from datetime import datetime, date, time
from models import Friendship
from models import Notification
from routes.notifications import add_notification

home_bp = Blueprint("home", __name__)

@home_bp.route("/")
@login_required
def index():
    today = date.today()
    now = datetime.now().time()
    tasks_today = Task.query.filter_by(user_id=current_user.id, date=today).order_by(Task.start_time).all()
    overdue_t = Task.query.filter(Task.user_id == current_user.id, Task.date < today).all()

    next_task = None
    for t in tasks_today:
        if t.start_time > now:
            next_task = t
            break
       
    return render_template(
        "index.html",
        tasks_today=tasks_today,
        overdue_tasks=overdue_t,
        next_task=next_task,
        selected_date=today,
        tasks=tasks_today,
    )

    return render_template("index.html", tasks_today=tasks_today,overdue_tasks=overdue_t, next_task=next_task, selected_date=today, tasks = tasks_today)
