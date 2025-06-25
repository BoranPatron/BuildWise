from httpx import AsyncClient
import pytest


@pytest.mark.asyncio
async def test_create_and_get_projects(client):
    async with AsyncClient(app=client.app, base_url="http://test") as ac:
        await ac.post("/auth/register", json={"email": "proj@example.com", "password": "secret"})
        login_resp = await ac.post(
            "/auth/login",
            data={"username": "proj@example.com", "password": "secret"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        token = login_resp.json()["access_token"]

        project_data = {"name": "House", "description": "Build a house"}
        resp = await ac.post(
            "/projects/",
            json=project_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        project = resp.json()
        assert project["name"] == "House"

        resp = await ac.get(
            "/projects/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        projects = resp.json()
        assert len(projects) == 1
        assert projects[0]["name"] == "House"
