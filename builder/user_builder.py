from dataclasses import dataclass
from typing import Optional
from models import User

@dataclass
class UserDTO:
    username: str
    email: str
    password_hash: str
    role: str = "user"
    restricted: bool = False

class UserBuilder:
    def __init__(self):
        self._dto: Optional[UserDTO] = None

    def from_dto(self, dto: UserDTO) -> "UserBuilder":
        self._dto = dto
        return self

    def build(self) -> User:
        if not self._dto:
            raise ValueError("UserBuilder: missing dto")

        return User(
            username=self._dto.username,
            email=self._dto.email,
            password_hash=self._dto.password_hash,
            role=self._dto.role,
            restricted=self._dto.restricted,
        )
