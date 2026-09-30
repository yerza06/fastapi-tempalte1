import enum

from src.core.database.base import Base, TimestampMixin

from sqlalchemy import String, Enum
from sqlalchemy.orm import Mapped, mapped_column

class UserRole(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"
    SUPERADMIN = "superadmin"


class User(Base, TimestampMixin):
    __tablename__ = "users"

    first_name: Mapped[str] = mapped_column(String(20), nullable=False)
    last_name: Mapped[str] = mapped_column(String(20), nullable=False)
    email: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.USER)

    def __str__(self) -> str:
        return f"{self.email}"
