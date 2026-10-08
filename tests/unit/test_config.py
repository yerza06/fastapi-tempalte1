from src.core.config import PostgresConfig


def test_sqlalchemy_url():
    config = PostgresConfig(
        HOST="db",
        PORT=5433,
        USERNAME="user",
        PASSWORD="pass",
        DATABASE="app",
    )

    url = config.sqlalchemy_url()

    assert url.drivername == "postgresql+asyncpg"
    assert url.host == "db"
    assert url.port == 5433
    assert url.username == "user"
    assert url.password == "pass"
    assert url.database == "app"


def test_user_str(user):
    assert str(user) == user.email
