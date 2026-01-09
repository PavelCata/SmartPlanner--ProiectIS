from datetime import datetime, timedelta
from app import db
from sqlalchemy import func
from models import Task

class TaskFrequencyProxy:
    def __init__(self, user_id):
        self.user_id = user_id
        self._cache = None
        self._last_update = None
        self._cache_duration = timedelta(minutes=10)

    def get_top_tasks(self):
        if self._cache is not None and (datetime.now() - self._last_update) < self._cache_duration:
            print(f"DEBUG: return date din Cache pentru user {self.user_id}")
            return self._cache

        print(f"DEBUG: niterogam baza de date pentru user {self.user_id}")
        results = (
            db.session.query(
                Task.title,
                func.count(Task.id).label("freq"),
                func.avg((func.hour(Task.end_time) * 60 + func.minute(Task.end_time))-(func.hour(Task.start_time) * 60 + func.minute(Task.start_time))).label("avg_duration")
            )
            .filter(Task.user_id == self.user_id)
            .group_by(Task.title)
            .order_by(func.count(Task.id).desc())
            .limit(3)
            .all()
        )
    
        self._cache = results
        self._last_update = datetime.now()
        return self._cache