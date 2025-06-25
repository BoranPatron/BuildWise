from httpx import AsyncClient

import pytest


@pytest.mark.asyncio
async def test_register_and_login(client):
    async with AsyncClient(app=client.app, base_url="http://test") as ac:
        response = await ac.post("/auth/register", json={"email": "user@example.com", "password": "secret"})
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "user@example.com"

        response = await ac.post(
            "/auth/login",
            data={"username": "user@example.com", "password": "secret"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert response.status_code == 200
        token = response.json()["access_token"]

        response = await ac.get(
            "/users/me", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert response.json()["email"] == "user@example.com"
