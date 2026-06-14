"""
tests/test_health_dashboard.py
"""
import pytest


@pytest.mark.asyncio
async def test_health(client):
    r = await client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["database"] == "reachable"


@pytest.mark.asyncio
async def test_dashboard(client, book, member, loan):
    r = await client.get("/dashboard")
    assert r.status_code == 200
    data = r.json()
    assert data["total_books"]   >= 1
    assert data["total_members"] >= 1
    assert data["active_loans"]  >= 1
    assert "overdue_loans" in data
    assert "total_fines"   in data
