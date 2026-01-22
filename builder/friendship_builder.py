from dataclasses import dataclass
from typing import Optional
from models import Friendship

@dataclass
class FriendshipDTO:
    sender_id: int
    receiver_id: int
    status: str = "pending"

class FriendshipBuilder:
    def __init__(self):
        self._dto: Optional[FriendshipDTO] = None

    def from_dto(self, dto: FriendshipDTO) -> "FriendshipBuilder":
        self._dto = dto
        return self

    def build(self) -> Friendship:
        if not self._dto:
            raise ValueError("FriendshipBuilder: missing dto")

        return Friendship(
            sender_id=self._dto.sender_id,
            receiver_id=self._dto.receiver_id,
            status=self._dto.status
        )
