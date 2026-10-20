from datetime import timedelta

import pytest

from src.modules.auth.utils import create_refresh_token, encode_jwt
from tests.conftest import PASSWORD

REGISTER_DATA = {
    "first_name": "Jane",
    "last_name": "Doe",
    "email": "jane@example.com",
    "password": PASSWORD,
}


async def test_home(client):
    response = await client.get("/")

    assert response.status_code == 200
    assert response.json() == {"message": "Hello World!"}


class TestRegister:
    async def test_success(self, client):
        response = await client.post("/auth/register", json=REGISTER_DATA)

        assert response.status_code == 201
        body = response.json()
        assert set(body) == {
            "id",
            "first_name",
            "last_name",
            "email",
            "role",
            "created_at",
        }
        assert body["email"] == REGISTER_DATA["email"]
        assert body["role"] == "user"

    async def test_duplicate_email(self, client, db_user):
        response = await client.post(
            "/auth/register", json={**REGISTER_DATA, "email": db_user.email}
        )

        assert response.status_code == 409
        assert response.json() == {"detail": "User with this email already exists"}

    @pytest.mark.parametrize(
        ("field", "value"),
        [
            ("email", "not-an-email"),
            ("password", "short"),
            ("first_name", ""),
        ],
    )
    async def test_validation_error(self, client, field, value):
        response = await client.post(
            "/auth/register", json={**REGISTER_DATA, field: value}
        )

        assert response.status_code == 422
        assert response.json()["detail"][0]["loc"] == ["body", field]

    async def test_missing_body(self, client):
        response = await client.post("/auth/register")

        assert response.status_code == 422


class TestLogin:
    async def test_success(self, tokens):
        assert tokens["token_type"] == "bearer"
        assert tokens["access_token"]
        assert tokens["refresh_token"]

    @pytest.mark.parametrize(
        ("email", "password"),
        [
            ("john@example.com", "wrong-password"),
            ("nobody@example.com", PASSWORD),
        ],
        ids=["wrong-password", "unknown-email"],
    )
    async def test_invalid_credentials(self, client, db_user, email, password):
        response = await client.post(
            "/auth/login", json={"email": email, "password": password}
        )

        assert response.status_code == 401
        assert response.json() == {"detail": "Invalid email or password"}
        assert response.headers["WWW-Authenticate"] == "Bearer"


class TestMe:
    async def test_success(self, client, db_user, auth_headers):
        response = await client.get("/auth/me", headers=auth_headers)

        assert response.status_code == 200
        body = response.json()
        assert body["id"] == db_user.id
        assert body["email"] == db_user.email
        assert "password_hash" not in body

    async def test_without_token(self, client):
        response = await client.get("/auth/me")

        assert response.status_code == 401

    async def test_invalid_token(self, client):
        response = await client.get(
            "/auth/me", headers={"Authorization": "Bearer not-a-jwt"}
        )

        assert response.status_code == 401
        assert response.json() == {"detail": "Invalid token"}

    async def test_expired_token(self, client, db_user):
        token = encode_jwt(
            {"sub": str(db_user.id), "type": "access"}, timedelta(seconds=-1)
        )

        response = await client.get(
            "/auth/me", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 401
        assert response.json() == {"detail": "Token has expired"}

    async def test_refresh_token_rejected(self, client, db_user):
        token = create_refresh_token(db_user)

        response = await client.get(
            "/auth/me", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 401
        assert response.json() == {"detail": "Invalid token type"}


class TestRefresh:
    async def test_success(self, client, tokens):
        response = await client.post(
            "/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
        )

        assert response.status_code == 200
        new_access = response.json()["access_token"]

        me = await client.get(
            "/auth/me", headers={"Authorization": f"Bearer {new_access}"}
        )
        assert me.status_code == 200

    async def test_access_token_rejected(self, client, tokens):
        response = await client.post(
            "/auth/refresh", json={"refresh_token": tokens["access_token"]}
        )

        assert response.status_code == 401
        assert response.json() == {"detail": "Invalid token type"}


async def test_full_flow(client):
    register = await client.post("/auth/register", json=REGISTER_DATA)
    assert register.status_code == 201

    login = await client.post(
        "/auth/login",
        json={"email": REGISTER_DATA["email"], "password": PASSWORD},
    )
    assert login.status_code == 200

    me = await client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {login.json()['access_token']}"},
    )
    assert me.status_code == 200
    assert me.json()["id"] == register.json()["id"]
