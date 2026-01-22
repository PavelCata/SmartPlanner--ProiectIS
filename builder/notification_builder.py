from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from models import Notification


@dataclass
class NotificationDTO:
    user_id: int
    text: str
    type: str = "info"
    category: Optional[str] = None
    source: str = "app"
    priority: str = "normal"
    dedupe_key: Optional[str] = None
    status: str = "unseen"
    seen: bool = False
    created_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None

class NotificationBuilder:
    def __init__(self):
        self._dto: Optional[NotificationDTO] = None

    def from_dto(self, dto: NotificationDTO) -> "NotificationBuilder":
        self._dto = dto
        return self

    def build(self) -> Notification:
        if not self._dto:
            raise ValueError("NotificationBuilder: missing dto")

        now = self._dto.created_at or datetime.utcnow()

        return Notification(
            user_id=self._dto.user_id,
            text=self._dto.text,
            type=self._dto.type,
            seen=self._dto.seen,
            status=self._dto.status,
            category=self._dto.category,
            source=self._dto.source,
            priority=self._dto.priority,
            dedupe_key=self._dto.dedupe_key,
            created_at=now,
            delivered_at=self._dto.delivered_at,
        )
