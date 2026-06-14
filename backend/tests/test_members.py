"""
tests/test_members.py
"""
import pytest


@pytest.mark.asyncio
async def test_create_member(client):
    r = await client.post("/members", json={
        "name": "Bob Smith",
        "email": "bob_unique@example.com",
        "phone": "555-0102",
    })
    assert r.status_code == 201
    data = r.json()
    assert data["email"] == "bob_unique@example.com"
    assert data["active"] is True


@pytest.mark.asyncio
async def test_create_member_duplicate_email(client, member):
    r = await client.post("/members", json={
        "name": "Alice Clone",
        "email": member["email"],
    })
    assert r.status_code == 409
    assert "already registered" in r.json()["detail"]


@pytest.mark.asyncio
async def test_get_member(client, member):
    r = await client.get(f"/members/{member['id']}")
    assert r.status_code == 200
    assert r.json()["id"] == member["id"]


@pytest.mark.asyncio
async def test_get_member_not_found(client):
    r = await client.get("/members/99999")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_list_members(client, member):
    r = await client.get("/members")
    assert r.status_code == 200
    assert r.json()["total"] >= 1


@pytest.mark.asyncio
async def test_update_member(client, member):
    r = await client.patch(f"/members/{member['id']}", json={"phone": "999-9999"})
    assert r.status_code == 200
    assert r.json()["phone"] == "999-9999"


@pytest.mark.asyncio
async def test_update_member_duplicate_email(client, member, client_second_member=None):
    # Create a second member
    r2 = await client.post("/members", json={"name": "Carol", "email": "carol_u@example.com"})
    assert r2.status_code == 201
    carol_id = r2.json()["id"]

    # Try to set Carol's email to Alice's
    r = await client.patch(f"/members/{carol_id}", json={"email": member["email"]})
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_delete_member_soft(client, member):
    r = await client.delete(f"/members/{member['id']}")
    assert r.status_code == 204
    # Member should still exist but be inactive
    r2 = await client.get(f"/members/{member['id']}")
    assert r2.status_code == 200
    assert r2.json()["active"] is False
