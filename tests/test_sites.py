import pytest


async def create_site(client, name="Example", url="https://example.com"):
    response = await client.post("/sites/", json={"name": name, "url": url})
    return response


class TestCreateSite:
    async def test_create_site_success(self, client):
        response = await create_site(client)

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Example"
        assert data["url"] == "https://example.com/"
        assert data["is_online"] is True
        assert "id" in data

    async def test_create_site_duplicate_url_returns_409(self, client):
        await create_site(client, name="First", url="https://duplicate.com")
        response = await create_site(client, name="Second", url="https://duplicate.com")

        assert response.status_code == 409

    async def test_create_site_invalid_url_returns_422(self, client):
        response = await client.post(
            "/sites/", json={"name": "Bad", "url": "not-a-url"}
        )

        assert response.status_code == 422


class TestGetSites:
    async def test_get_all_sites_empty(self, client):
        response = await client.get("/sites/")

        assert response.status_code == 200
        assert response.json() == []

    async def test_get_all_sites_returns_created_sites(self, client):
        await create_site(client, name="Site A", url="https://a.com")
        await create_site(client, name="Site B", url="https://b.com")

        response = await client.get("/sites/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert {s["name"] for s in data} == {"Site A", "Site B"}

    async def test_pagination_limits_results(self, client):
        for i in range(5):
            await create_site(client, name=f"Site {i}", url=f"https://site{i}.com")

        response = await client.get("/sites/?skip=0&limit=2")

        assert response.status_code == 200
        assert len(response.json()) == 2

    async def test_get_single_site(self, client):
        created = (await create_site(client)).json()

        response = await client.get(f"/sites/{created['id']}")

        assert response.status_code == 200
        assert response.json()["id"] == created["id"]

    async def test_get_single_site_not_found(self, client):
        response = await client.get("/sites/9999")

        assert response.status_code == 404


class TestUpdateSite:
    async def test_update_site_name(self, client):
        created = (await create_site(client)).json()

        response = await client.put(
            f"/sites/{created['id']}", json={"name": "Renamed"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Renamed"
        assert data["url"] == created["url"]  # url лишився незмінним

    async def test_update_site_not_found(self, client):
        response = await client.put("/sites/9999", json={"name": "Nope"})

        assert response.status_code == 404

    async def test_update_site_to_duplicate_url_returns_409(self, client):
        await create_site(client, name="First", url="https://first.com")
        second = (await create_site(client, name="Second", url="https://second.com")).json()

        response = await client.put(
            f"/sites/{second['id']}", json={"url": "https://first.com"}
        )

        assert response.status_code == 409


class TestDeleteSite:
    async def test_delete_site(self, client):
        created = (await create_site(client)).json()

        response = await client.delete(f"/sites/{created['id']}")
        assert response.status_code == 204

        follow_up = await client.get(f"/sites/{created['id']}")
        assert follow_up.status_code == 404

    async def test_delete_site_not_found(self, client):
        response = await client.delete("/sites/9999")

        assert response.status_code == 404


class TestSiteLogs:
    async def test_get_logs_for_nonexistent_site_returns_404(self, client):
        response = await client.get("/sites/9999/logs")

        assert response.status_code == 404

    async def test_get_logs_for_new_site_is_empty(self, client):
        created = (await create_site(client)).json()

        response = await client.get(f"/sites/{created['id']}/logs")

        assert response.status_code == 200
        assert response.json() == []
