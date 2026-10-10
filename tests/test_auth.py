from datetime import datetime, timedelta, timezone

import jwt

from app.auth import ALGORITHM, SECRET_KEY

EMAIL = "user@example.com"
PASSWORD = "supersecret123"


async def register(client, email=EMAIL, password=PASSWORD):
    return await client.post(
        "/auth/register", json={"email": email, "password": password}
    )


async def login(client, email=EMAIL, password=PASSWORD):
    # OAuth2-форма: поле називається username, але передаємо email
    return await client.post(
        "/auth/login", data={"username": email, "password": password}
    )


async def get_token(client):
    await register(client)
    return (await login(client)).json()["access_token"]


class TestRegister:
    async def test_register_success(self, client):
        response = await register(client)

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == EMAIL
        assert "id" in data
        # пароль у відповідь потрапляти не повинен
        assert "password" not in data
        assert "hashed_password" not in data

    async def test_register_normalizes_email_to_lowercase(self, client):
        response = await register(client, email="User@Example.com")

        assert response.status_code == 201
        assert response.json()["email"] == "user@example.com"

    async def test_register_duplicate_email_returns_409(self, client):
        await register(client)
        response = await register(client)

        assert response.status_code == 409

    async def test_register_duplicate_email_is_case_insensitive(self, client):
        await register(client)
        response = await register(client, email="USER@example.com")

        assert response.status_code == 409

    async def test_register_invalid_email_returns_422(self, client):
        response = await register(client, email="not-an-email")

        assert response.status_code == 422

    async def test_register_short_password_returns_422(self, client):
        response = await register(client, password="short")

        assert response.status_code == 422


class TestLogin:
    async def test_login_success_returns_token(self, client):
        await register(client)

        response = await login(client)

        assert response.status_code == 200
        data = response.json()
        assert data["token_type"] == "bearer"
        assert data["access_token"]

    async def test_login_wrong_password_returns_401(self, client):
        await register(client)

        response = await login(client, password="wrong-password")

        assert response.status_code == 401

    async def test_login_unknown_user_returns_401(self, client):
        response = await login(client, email="nobody@example.com")

        assert response.status_code == 401


class TestMe:
    async def test_me_with_valid_token(self, client):
        token = await get_token(client)

        response = await client.get(
            "/auth/me", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        assert response.json()["email"] == EMAIL

    async def test_me_without_token_returns_401(self, client):
        response = await client.get("/auth/me")

        assert response.status_code == 401

    async def test_me_with_garbage_token_returns_401(self, client):
        response = await client.get(
            "/auth/me", headers={"Authorization": "Bearer not.a.token"}
        )

        assert response.status_code == 401

    async def test_me_with_expired_token_returns_401(self, client):
        user = (await register(client)).json()
        expired = jwt.encode(
            {
                "sub": str(user["id"]),
                "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
            },
            SECRET_KEY,
            algorithm=ALGORITHM,
        )

        response = await client.get(
            "/auth/me", headers={"Authorization": f"Bearer {expired}"}
        )

        assert response.status_code == 401