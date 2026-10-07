import asyncio
import sys
from getpass import getpass

from pydantic import EmailStr, TypeAdapter, ValidationError

from src.core.database.session import engine, session_factory
from src.modules.auth.utils import hash_password
from src.modules.users.models import UserRole
from src.modules.users.repository import UserRepository
from src.modules.users.schema import UserRead

NAME_MAX_LENGTH = 20
EMAIL_MAX_LENGTH = 50
PASSWORD_MIN_LENGTH = 8

email_adapter = TypeAdapter(EmailStr)


def ask_name(label: str) -> str:
    while True:
        value = input(f"{label}: ").strip()
        if not value:
            print("  Поле не может быть пустым")
        elif len(value) > NAME_MAX_LENGTH:
            print(f"  Максимум {NAME_MAX_LENGTH} символов")
        else:
            return value


def ask_email() -> str:
    while True:
        value = input("Email: ").strip()
        if len(value) > EMAIL_MAX_LENGTH:
            print(f"  Максимум {EMAIL_MAX_LENGTH} символов")
            continue
        try:
            return email_adapter.validate_python(value)
        except ValidationError:
            print("  Некорректный email")


def ask_password() -> str:
    while True:
        password = getpass("Password: ")
        if len(password) < PASSWORD_MIN_LENGTH:
            print(f"  Минимум {PASSWORD_MIN_LENGTH} символов")
            continue
        if password != getpass("Confirm password: "):
            print("  Пароли не совпадают")
            continue
        return password


def ask_role() -> UserRole:
    roles = list(UserRole)
    print("Role:")
    for i, role in enumerate(roles, start=1):
        print(f"  {i}. {role.value}")

    while True:
        value = input(f"Выберите роль [1-{len(roles)}]: ").strip()
        if value.isdigit() and 1 <= int(value) <= len(roles):
            return roles[int(value) - 1]
        print("  Некорректный выбор")


def print_user(user: UserRead) -> None:
    print("\nПользователь создан:")
    print(f"  ID:         {user.id}")
    print(f"  First Name: {user.first_name}")
    print(f"  Last Name:  {user.last_name}")
    print(f"  Email:      {user.email}")
    print(f"  Role:       {user.role.value}")
    print(f"  Created At: {user.created_at:%Y-%m-%d %H:%M:%S}")


async def main() -> int:
    first_name = ask_name("First name")
    last_name = ask_name("Last name")
    email = ask_email()
    password = ask_password()
    role = ask_role()

    try:
        async with session_factory() as session:
            users = UserRepository(session)
            if await users.get_by_email(email):
                print(f"\nОшибка: пользователь с email {email} уже существует")
                return 1

            user = await users.create(
                first_name=first_name,
                last_name=last_name,
                email=email,
                password_hash=hash_password(password),
                role=role,
            )
            print_user(UserRead.model_validate(user))
    finally:
        await engine.dispose()

    return 0


if __name__ == "__main__":
    try:
        sys.exit(asyncio.run(main()))
    except KeyboardInterrupt:
        print("\nОтменено")
        sys.exit(130)
