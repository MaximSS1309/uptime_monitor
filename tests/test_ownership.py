import pytest

SITE = {"name": "Example", "url": "https://example.com"}


class TestAuthRequired:
    @pytest.mark.parametrize(
        "method, path",
        [
            ("POST", "/sites/"),
            ("GET", "/sites/"),
            ("GET", "/sites/1"),
            ("PUT", "/sites/1"),
            ("DELETE", "/sites/1"),
            ("GET", "/sites/1/logs"),
        ],
    )
    async def test_sites_endpoints_require_token(self, client, method, path):
        response = await client.request(method, path, json=SITE)

        assert response.status_code == 401


class TestIsolation:
    async def test_user_sees_only_own_sites(self, auth_client, other_client):
        await auth_client.post("/sites/", json={"name": "Mine", "url": "https://mine.com"})
        await other_client.post("/sites/", json={"name": "Theirs", "url": "https://theirs.com"})

        mine = (await auth_client.get("/sites/")).json()
        theirs = (await other_client.get("/sites/")).json()

        assert [s["name"] for s in mine] == ["Mine"]
        assert [s["name"] for s in theirs] == ["Theirs"]

    async def test_cannot_get_other_users_site(self, auth_client, other_client):
        site = (await auth_client.post("/sites/", json=SITE)).json()

        response = await other_client.get(f"/sites/{site['id']}")

        assert response.status_code == 404

    async def test_cannot_update_other_users_site(self, auth_client, other_client):
        site = (await auth_client.post("/sites/", json=SITE)).json()

        response = await other_client.put(
            f"/sites/{site['id']}", json={"name": "Hacked"}
        )

        assert response.status_code == 404
        unchanged = (await auth_client.get(f"/sites/{site['id']}")).json()
        assert unchanged["name"] == "Example"

    async def test_cannot_delete_other_users_site(self, auth_client, other_client):
        site = (await auth_client.post("/sites/", json=SITE)).json()

        response = await other_client.delete(f"/sites/{site['id']}")

        assert response.status_code == 404
        still_there = await auth_client.get(f"/sites/{site['id']}")
        assert still_there.status_code == 200

    async def test_cannot_read_other_users_logs(self, auth_client, other_client):
        site = (await auth_client.post("/sites/", json=SITE)).json()

        response = await other_client.get(f"/sites/{site['id']}/logs")

        assert response.status_code == 404

    async def test_same_url_allowed_for_different_users(self, auth_client, other_client):
        first = await auth_client.post("/sites/", json=SITE)
        second = await other_client.post("/sites/", json=SITE)

        assert first.status_code == 200
        assert second.status_code == 200
        assert first.json()["id"] != second.json()["id"]