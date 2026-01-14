from dataclasses import dataclass
from datetime import date, time
from typing import Optional
from models import Task

@dataclass
class TaskDTO:
    user_id: int
    date: date
    start_time: time
    end_time: time
    title: str
    importance: str = "medium"
    low_mode: Optional[str] = None

class TaskBuilder:
    def __init__(self):
        self._data: Optional[TaskDTO] = None

    def from_dto(self, dto: TaskDTO) -> "TaskBuilder":
        self._data = dto
        return self

    def build(self) -> Task:
        if not self._data:
            raise ValueError("TaskBuilder: no data provided")

        if self._data.end_time <= self._data.start_time:
            raise ValueError("TaskBuilder: end_time must be after start_time")

        return Task(
            user_id=self._data.user_id,
            date=self._data.date,
            start_time=self._data.start_time,
            end_time=self._data.end_time,
            title=self._data.title,
            importance=self._data.importance,
            low_mode=self._data.low_mode,
        )
