from datetime import datetime, date, time
from app import db
from models import Notification, NotificationPreference
from builder.notification_builder import NotificationBuilder, NotificationDTO


CATEGORY_TO_FIELD = {
    "social": "allow_social",
    "tasks": "allow_tasks",
    "insights": "allow_insights",
}

def _is_in_quiet_hours(now_t: time, start: time, end: time) -> bool:
    if start < end:
        return start <= now_t < end
    return now_t >= start or now_t < end

def get_or_create_pref(user_id: int) -> NotificationPreference:
    pref = NotificationPreference.query.filter_by(user_id=user_id).first()
    if not pref:
        pref = NotificationPreference(user_id=user_id)
        db.session.add(pref)
        db.session.commit()
    return pref

def _allowed_by_pref(pref: NotificationPreference, category: str | None) -> bool:
    if not category:
        return True
    field = CATEGORY_TO_FIELD.get(category)
    if not field:
        return True
    return bool(getattr(pref, field, True))

def _quiet_now(pref: NotificationPreference) -> bool:
    if not pref.quiet_enabled or not pref.quiet_start or not pref.quiet_end:
        return False
    return _is_in_quiet_hours(datetime.now().time(), pref.quiet_start, pref.quiet_end)

def notification_exists_today(user_id: int, dedupe_key: str) -> bool:
    if not dedupe_key:
        return False

    today = date.today()
    start = datetime.combine(today, time.min)
    end = datetime.combine(today, time.max)

    return db.session.query(Notification.id).filter(
        Notification.user_id == user_id,
        Notification.dedupe_key == dedupe_key,
        Notification.created_at >= start,
        Notification.created_at <= end,
        Notification.status != "deleted",
    ).first() is not None

def create_notification(
    user_id: int,
    text: str,
    *,
    type: str = "info",
    category: str | None = None,
    source: str = "app",
    priority: str = "normal",
    dedupe_key: str | None = None,
):
    if dedupe_key and notification_exists_today(user_id, dedupe_key):
        return None

    pref = get_or_create_pref(user_id)

    if not _allowed_by_pref(pref, category):
        return None

    now = datetime.utcnow()
    status = "queued" if _quiet_now(pref) else "unseen"
    delivered_at = None if status == "queued" else now

    dto = NotificationDTO(
        user_id=user_id,
        text=text,
        type=type,
        category=category,
        source=source,
        priority=priority,
        dedupe_key=dedupe_key,
        status=status,
        seen=False,
        created_at=now,
        delivered_at=delivered_at,
    )

    n = NotificationBuilder().from_dto(dto).build()
    db.session.add(n)
    db.session.commit()
    return n


def add_notification(user_id, message, category="info"):
    return create_notification(
        user_id=user_id,
        text=message,
        type=category,
        category=None,
        source="legacy",
        dedupe_key=None
    )

def deliver_queued(user_id: int) -> int:
    pref = get_or_create_pref(user_id)
    if _quiet_now(pref):
        return 0

    now = datetime.utcnow()
    q = Notification.query.filter_by(user_id=user_id, status="queued")
    count = q.count()
    q.update({"status": "unseen", "delivered_at": now})
    db.session.commit()
    return count

def mark_seen_bulk(user_id: int):
    now = datetime.utcnow()
    Notification.query.filter_by(user_id=user_id, status="unseen") \
        .update({"status": "seen", "seen": True, "seen_at": now})
    db.session.commit()

def update_preferences(
    user_id: int,
    *,
    quiet_enabled: bool,
    quiet_start,
    quiet_end,
    allow_social: bool,
    allow_tasks: bool,
    allow_insights: bool
):
    pref = get_or_create_pref(user_id)
    pref.quiet_enabled = quiet_enabled
    pref.quiet_start = quiet_start
    pref.quiet_end = quiet_end
    pref.allow_social = allow_social
    pref.allow_tasks = allow_tasks
    pref.allow_insights = allow_insights
    pref.updated_at = datetime.utcnow()
    db.session.commit()
    return pref

def delete_all_notifications(user_id: int):
    now = datetime.utcnow()
    Notification.query.filter(
        Notification.user_id == user_id,
        Notification.status != "deleted"
    ).update({
        "status": "deleted",
        "deleted_at": now
    })
    db.session.commit()