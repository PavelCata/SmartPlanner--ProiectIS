from flask import Blueprint, request, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime, date, time, timedelta
from app import db
from models import Task
from routes.notifications import add_notification
from Proxies.adminProxy import restriction_proxy
from builder.task_builder import TaskBuilder, TaskDTO
from services.task_service import save_task
from datetime import timedelta, datetime

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

def find_slot_near_target(existing, duration, target_minutes, exclude_target=False):
    if not existing:
        if exclude_target:
            start_before = target_minutes - duration
            if start_before >= 8 * 60:
                return from_minutes(start_before), from_minutes(start_before + duration)
            start_after = target_minutes + 1
            if start_after + duration <= 22 * 60:
                return from_minutes(start_after), from_minutes(start_after + duration)
            return None
        return from_minutes(target_minutes), from_minutes(target_minutes + duration) 
    proposed_start = target_minutes
    proposed_end = target_minutes + duration
    if not exclude_target:
        can_place_at_target = True
        for t in existing:
            t_start = to_minutes(t.start_time)
            t_end = to_minutes(t.end_time)
            if not (proposed_end <= t_start or proposed_start >= t_end):
                can_place_at_target = False
                break
        if can_place_at_target and proposed_end <= 22 * 60:
            return from_minutes(proposed_start), from_minutes(proposed_end)
    slots = []
    first_start = to_minutes(existing[0].start_time)
    if first_start - 8 * 60 >= duration:
        slots.append((8 * 60, 8 * 60 + duration))
    for i in range(len(existing) - 1):
        end_prev = to_minutes(existing[i].end_time)
        start_next = to_minutes(existing[i + 1].start_time)
        if start_next - end_prev >= duration:
            slots.append((end_prev, end_prev + duration))
    last_end = to_minutes(existing[-1].end_time)
    if 22 * 60 - last_end >= duration:
        slots.append((last_end, last_end + duration))
    if not slots:
        return None
    if exclude_target:
        slots = [s for s in slots if s[0] != target_minutes]
    if not slots:
        return None
    best_slot = min(slots, key=lambda s: abs(s[0] - target_minutes))
    return from_minutes(best_slot[0]), from_minutes(best_slot[1])

def interval_distance(start_min, end_min, target_min):
    if start_min <= target_min <= end_min:
        return 0
    return min(abs(start_min - target_min), abs(end_min - target_min))

def slot_distance(slot, target_minutes):
    if not slot:
        return 10**9
    return abs(to_minutes(slot[0]) - target_minutes)

def find_task_near_target(existing, target_minutes, allowed_importances):
    candidates = [t for t in existing if t.importance in allowed_importances]
    if not candidates:
        return None
    return min(
        candidates,
        key=lambda t: interval_distance(
            to_minutes(t.start_time),
            to_minutes(t.end_time),
            target_minutes
        )
    )

def place_in_victim_interval(victim, duration, target_minutes):
    vs = to_minutes(victim.start_time)
    ve = to_minutes(victim.end_time)
    if ve - vs < duration:
        return None
    start_m = max(vs, min(target_minutes, ve - duration))
    return from_minutes(start_m), from_minutes(start_m + duration)


def pick_best_auto2pm_placement(existing, duration, target_minutes, allowed_importances):
    slot = find_slot_near_target(existing, duration, target_minutes)
    slot_d = slot_distance(slot, target_minutes)

    victim = find_task_near_target(existing, target_minutes, allowed_importances)
    if victim:
        victim_d = interval_distance(
            to_minutes(victim.start_time),
            to_minutes(victim.end_time),
            target_minutes
        )
        desired = place_in_victim_interval(victim, duration, target_minutes)
        if desired and victim_d < slot_d:
            return ("victim", victim, desired)

    if slot:
        return ("slot", slot)

    return (None, None)


def move_task_to_next_day(task, prefer_target_time=None):
    original_date = task.date
    original_start = task.start_time.strftime("%H:%M")
    original_end = task.end_time.strftime("%H:%M")
    duration = to_minutes(task.end_time) - to_minutes(task.start_time)
    existing_today = Task.query.filter_by(
        user_id=task.user_id, date=task.date
    ).order_by(Task.start_time).all()
    existing_today = [t for t in existing_today if t.id != task.id]
    if prefer_target_time is not None:
        slot_today = find_slot_near_target(
            existing_today,
            duration,
            prefer_target_time,
            exclude_target=True
        )
    else:
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
                f"({original_start}-{original_end}) in {task.date} "
                f"({task.start_time.strftime('%H:%M')}-{task.end_time.strftime('%H:%M')}) "
                f"pentru a-i gasi un loc liber.",
                "warning"
            )
            return
        next_day += timedelta(days=1)

@tasks_bp.route("/tasks", methods=["GET", "POST"])
@login_required
@restriction_proxy
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
        auto_2pm = request.form.get("auto_2pm", None)
        if not title:
            flash("Te rog completeaza titlul.", "danger")
            return redirect(url_for("tasks.view_tasks", date=selected_date.isoformat()))        
        if auto_2pm:
            duration_str = request.form.get("duration")
            if not duration_str:
                flash("Te rog specifica durata in minute.", "danger")
                return redirect(url_for("tasks.view_tasks", date=selected_date.isoformat()))
            try:
                duration = int(duration_str)
            except ValueError:
                flash("Durata trebuie sa fie un numar.", "danger")
                return redirect(url_for("tasks.view_tasks", date=selected_date.isoformat()))
            target_time = 14 * 60
            start_time = from_minutes(target_time)
            end_time = from_minutes(target_time + duration)
            existing = Task.query.filter_by(
                user_id=current_user.id, date=selected_date
            ).order_by(Task.start_time).all()
            if importance == "high":
                for t in existing:
                    if not (end_time <= t.start_time or start_time >= t.end_time):
                        if t.importance in ("medium", "low"):
                            move_task_to_next_day(t, prefer_target_time=target_time)
                    existing = Task.query.filter_by(user_id=current_user.id, date=selected_date).order_by(Task.start_time).all()
                    kind = pick_best_auto2pm_placement(existing, duration, target_time, allowed_importances=("medium", "low"))
                    if kind[0] == "victim":
                        _, victim, (start_time, end_time) = kind
                        victim_start_minutes = to_minutes(victim.start_time)
                        move_task_to_next_day(victim, prefer_target_time=victim_start_minutes)
                        flash(f"Am mutat '{victim.title}' si am pus taskul important mai aproape de 14:00.", "info")
                    elif kind[0] == "slot":
                        _, (start_time, end_time) = kind
                        flash(f"Task adaugat la {start_time.strftime('%H:%M')}-{end_time.strftime('%H:%M')} (cat mai aproape de 14:00).", "info")
                    else:
                        flash("Nu exista timp liber pentru acest task important.", "danger")
                        return redirect(url_for("tasks.view_tasks", date=selected_date.isoformat()))
            elif importance == "medium":
                for t in existing:
                    if not (end_time <= t.start_time or start_time >= t.end_time):
                        if t.importance == "low":
                            move_task_to_next_day(t, prefer_target_time=target_time)
                    existing = Task.query.filter_by(user_id=current_user.id, date=selected_date).order_by(Task.start_time).all()
                    kind = pick_best_auto2pm_placement(existing, duration, target_time, allowed_importances=("low",))
                    if kind[0] == "victim":
                        _, victim, (start_time, end_time) = kind
                        victim_start_minutes = to_minutes(victim.start_time)
                        move_task_to_next_day(victim, prefer_target_time=victim_start_minutes)
                        flash(f"Am mutat '{victim.title}' si am pus taskul (mediu) mai aproape de 14:00.", "info")
                    elif kind[0] == "slot":
                        _, (start_time, end_time) = kind
                        flash(f"Task adaugat la {start_time.strftime('%H:%M')}-{end_time.strftime('%H:%M')} (cel mai aproape de 14:00).", "info")
                    else:
                        flash("Nu exista timp liber", "warning")
                        return redirect(url_for("tasks.view_tasks", date=selected_date.isoformat()))
            elif importance == "low":
                slot = find_slot_near_target(existing, duration, target_time)
                if slot:
                    start_time, end_time = slot
                    flash(f"Task adaugat la {start_time.strftime('%H:%M')}-{end_time.strftime('%H:%M')} (cel mai aproape de 14:00).", "info")
                else:
                    flash("Nu exista timp liber", "warning")
                    return redirect(url_for("tasks.view_tasks", date=selected_date.isoformat()))
        else:
            if not (start_str and end_str):
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
                        if t.importance in ("medium", "low"):
                            move_task_to_next_day(t)
                        else:
                            flash("Nu poti suprascrie un task important!", "danger")
                            return redirect(url_for("tasks.view_tasks", date=selected_date.isoformat()))
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
                            flash("Nu poti suprascrie un task important sau mediu!", "danger")
                            return redirect(url_for("tasks.view_tasks", date=selected_date.isoformat()))
        dto = TaskDTO(
            user_id=current_user.id,
            date=selected_date,
            start_time=start_time,
            end_time=end_time,
            title=title,
            importance=importance,
            low_mode=low_mode
        )

        new_task = TaskBuilder().from_dto(dto).build()
        save_task(new_task)

        flash("Task creat cu succes.", "success")
        return redirect(url_for("tasks.view_tasks", date=selected_date.isoformat()))
    tasks = (
        Task.query
        .filter_by(user_id=current_user.id, date=selected_date)
        .order_by(Task.start_time)
        .all()
    )


    total_today = len(tasks)
    done_today = sum(1 for t in tasks if t.status == "done")
    missed_today = sum(1 for t in tasks if t.status == "missed")
    pending_today = sum(1 for t in tasks if t.status == "pending")

    start_week = selected_date - timedelta(days=selected_date.weekday())   
    end_week = start_week + timedelta(days=6)                            

    week_tasks = Task.query.filter(
        Task.user_id == current_user.id,
        Task.date >= start_week,
        Task.date <= end_week
    ).all()

    done_week = sum(1 for t in week_tasks if t.status == "done")
    missed_week = sum(1 for t in week_tasks if t.status == "missed")

    den = (done_week + missed_week)
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

    last30 = Task.query.filter(
        Task.user_id == current_user.id
    ).order_by(Task.date.desc(), Task.start_time.desc()).limit(30).all()

    done_last30 = sum(1 for t in last30 if t.status == "done")
    last30_total = len(last30)

    return render_template(
        "index.html",
        selected_date=selected_date,
        tasks=tasks,

        total_today=total_today,
        done_today=done_today,
        missed_today=missed_today,
        pending_today=pending_today,

        weekly_rate=weekly_rate,
        best_interval=best_interval,

        done_last30=done_last30,
        last30_total=last30_total
    )



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

@tasks_bp.route("/tasks/<int:task_id>/status", methods=["POST"])
@login_required
def set_task_status(task_id):
    status = request.form.get("status")  
    date_str = request.values.get("date")

    if status not in ("done", "missed", "pending"):
        flash("Status invalid.", "danger")
        return redirect(url_for("tasks.view_tasks", date=date_str) if date_str else url_for("tasks.view_tasks"))

    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first()
    if not task:
        flash("Task inexistent sau nu ai drepturi asupra lui.", "danger")
        return redirect(url_for("tasks.view_tasks", date=date_str) if date_str else url_for("tasks.view_tasks"))

    task.status = status
    db.session.commit()
    flash("Status actualizat.", "success")

    return redirect(url_for("tasks.view_tasks", date=date_str) if date_str else url_for("tasks.view_tasks"))
