from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr

from src.modules.users.models import UserRole


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    first_name: str
    last_name: str
    email: EmailStr
    role: UserRole
    created_at: datetime
