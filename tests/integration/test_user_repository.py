import pytest
from sqlalchemy.exc import DBAPIError, IntegrityError

from src.modules.users.models import UserRole


class TestCreate:
    async def test_fills_db_defaults(self, db_user):
        assert db_user.id is not None
        assert db_user.role == UserRole.USER
        assert db_user.created_at is not None
        assert db_user.updated_at is not None
        assert db_user.created_at.tzinfo is not None

    async def test_custom_role(self, repo):
        user = await repo.create(
            first_name="Admin",
            last_name="Admin",
            email="admin@example.com",
            password_hash="hash",
            role=UserRole.ADMIN,
        )

        assert (await repo.get_by_id(user.id)).role == UserRole.ADMIN

    async def test_duplicate_email(self, repo, db_user):
        with pytest.raises(IntegrityError):
            await repo.create(
                first_name="Other",
                last_name="Other",
                email=db_user.email,
                password_hash="hash",
            )

    async def test_too_long_first_name(self, repo):
        with pytest.raises(DBAPIError):
            await repo.create(
                first_name="a" * 21,
                last_name="Doe",
                email="long@example.com",
                password_hash="hash",
            )


class TestGetById:
    async def test_found(self, repo, db_user):
        user = await repo.get_by_id(db_user.id)

        assert user is not None
        assert user.email == db_user.email

    async def test_not_found(self, repo):
        assert await repo.get_by_id(999_999) is None


class TestGetByEmail:
    async def test_found(self, repo, db_user):
        user = await repo.get_by_email(db_user.email)

        assert user is not None
        assert user.id == db_user.id

    async def test_not_found(self, repo):
        assert await repo.get_by_email("nobody@example.com") is None


async def test_tests_are_isolated(repo):
    # NOTE: db_user из других тестов не должен остаться в базе
    assert await repo.get_by_email("john@example.com") is None
