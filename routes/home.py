from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user, login_required
from models import Task
from datetime import datetime, date, time, timedelta
from models import Friendship
from models import Notification
from app import db
from sqlalchemy import func
from routes.notifications import add_notification
from Proxies.taskProxy import TaskFrequencyProxy

home_bp = Blueprint("home", __name__)

user_proxies = {}

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

    if current_user.id not in user_proxies:
        user_proxies[current_user.id] = TaskFrequencyProxy(current_user.id)

    top_tasks = user_proxies[current_user.id].get_top_tasks()


    total_today = len(tasks_today)
    done_today = sum(1 for t in tasks_today if t.status == "done")
    missed_today = sum(1 for t in tasks_today if t.status == "missed")
    pending_today = sum(1 for t in tasks_today if t.status == "pending")

    start_week = today - timedelta(days=today.weekday())
    end_week = start_week + timedelta(days=6)

    week_tasks = Task.query.filter(
        Task.user_id == current_user.id,
        Task.date >= start_week,
        Task.date <= end_week
    ).all()

    done_week = sum(1 for t in week_tasks if t.status == "done")
    week_total = len(week_tasks)
    missed_week = sum(1 for t in week_tasks if t.status == "missed")

    den = done_week + missed_week
    weekly_rate = round((done_week / den) * 100) if den > 0 else 0

    bins = {}
    for t in week_tasks:
        if t.status != "done":
            continue
        hour = t.start_time.hour
        bucket_start = (hour // 2) * 2
        key = f"{bucket_start:02d}:00–{bucket_start+2:02d}:00"
        bins[key] = bins.get(key, 0) + 1

    best_interval = max(bins, key=bins.get) if bins else "—"


    return render_template(
        "index.html",
        tasks_today=tasks_today,
        overdue_tasks=overdue_t,
        next_task=next_task,
        selected_date=today,
        tasks=tasks_today,
        top_tasks=top_tasks,

        total_today=total_today,
        done_today=done_today,
        missed_today=missed_today,
        pending_today=pending_today,

        weekly_rate=weekly_rate,
        best_interval=best_interval,

        done_week=done_week,
        week_total=week_total
    )