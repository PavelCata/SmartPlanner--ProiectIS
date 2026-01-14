from app import db
from models import Task

def save_task(task: Task) -> Task:
    db.session.add(task)
    db.session.commit()
    return task
