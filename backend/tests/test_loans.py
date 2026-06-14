"""
tests/test_loans.py

Covers: borrow, return, duplicate borrow, unavailable book,
inactive member, already returned, overdue fine calculation.
"""
from datetime import datetime, timedelta, timezone
import pytest


@pytest.mark.asyncio
async def test_borrow_book(client, book, member):
    r = await client.post("/loans/borrow", json={
        "member_id": member["id"],
        "book_id":   book["id"],
        "loan_days": 14,
    })
    assert r.status_code == 201
    data = r.json()
    assert data["member_id"] == member["id"]
    assert data["book_id"]   == book["id"]
    assert data["returned_at"] is None
    assert data["overdue"] is False


@pytest.mark.asyncio
async def test_borrow_reduces_availability(client, book, loan):
    r = await client.get(f"/books/{book['id']}")
    assert r.json()["available"] == book["available"] - 1


@pytest.mark.asyncio
async def test_borrow_duplicate(client, book, member, loan):
    r = await client.post("/loans/borrow", json={
        "member_id": member["id"],
        "book_id":   book["id"],
    })
    assert r.status_code == 409
    assert "already has this book" in r.json()["detail"]


@pytest.mark.asyncio
async def test_borrow_no_copies(client, member):
    # Create a book with only 1 copy
    r = await client.post("/books", json={
        "title": "Single Copy Book",
        "author": "Author",
        "copies": 1,
    })
    bid = r.json()["id"]

    # First borrow succeeds
    r1 = await client.post("/loans/borrow", json={"member_id": member["id"], "book_id": bid})
    assert r1.status_code == 201

    # Second member borrows same book — should fail
    r2 = await client.post("/members", json={"name": "Bob", "email": "bob2x@example.com"})
    mid2 = r2.json()["id"]
    r3 = await client.post("/loans/borrow", json={"member_id": mid2, "book_id": bid})
    assert r3.status_code == 409
    assert "no available copies" in r3.json()["detail"]


@pytest.mark.asyncio
async def test_borrow_inactive_member(client, book, member):
    await client.delete(f"/members/{member['id']}")   # deactivate
    r = await client.post("/loans/borrow", json={
        "member_id": member["id"],
        "book_id":   book["id"],
    })
    assert r.status_code == 400
    assert "Inactive" in r.json()["detail"]


@pytest.mark.asyncio
async def test_borrow_nonexistent_book(client, member):
    r = await client.post("/loans/borrow", json={"member_id": member["id"], "book_id": 99999})
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_borrow_nonexistent_member(client, book):
    r = await client.post("/loans/borrow", json={"member_id": 99999, "book_id": book["id"]})
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_return_book(client, loan, book):
    r = await client.post(f"/loans/{loan['id']}/return")
    assert r.status_code == 200
    data = r.json()
    assert data["returned_at"] is not None

    # Availability should be restored
    r2 = await client.get(f"/books/{book['id']}")
    assert r2.json()["available"] == book["available"]


@pytest.mark.asyncio
async def test_return_already_returned(client, loan):
    await client.post(f"/loans/{loan['id']}/return")
    r = await client.post(f"/loans/{loan['id']}/return")
    assert r.status_code == 400
    assert "already been returned" in r.json()["detail"]


@pytest.mark.asyncio
async def test_return_not_found(client):
    r = await client.post("/loans/99999/return")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_list_loans(client, loan):
    r = await client.get("/loans")
    assert r.status_code == 200
    assert r.json()["total"] >= 1


@pytest.mark.asyncio
async def test_list_loans_filter_member(client, loan, member):
    r = await client.get(f"/loans?member_id={member['id']}")
    assert r.status_code == 200
    assert all(l["member_id"] == member["id"] for l in r.json()["loans"])


@pytest.mark.asyncio
async def test_list_loans_active_only(client, loan):
    r = await client.get("/loans?active_only=true")
    assert r.status_code == 200
    assert all(l["returned_at"] is None for l in r.json()["loans"])


@pytest.mark.asyncio
async def test_get_loan(client, loan):
    r = await client.get(f"/loans/{loan['id']}")
    assert r.status_code == 200
    assert r.json()["id"] == loan["id"]


@pytest.mark.asyncio
async def test_fine_calculation_on_return(client, db, book, member):
    """Loan created with past due_at; returning it should set a fine."""
    from app.models.orm import Loan as LoanORM

    now = datetime.now(timezone.utc)
    overdue_loan = LoanORM(
        member_id=member["id"],
        book_id=book["id"],
        borrowed_at=now - timedelta(days=20),
        due_at=now - timedelta(days=6),   # 6 days overdue
    )
    # Reduce availability directly
    from app.models.orm import Book as BookORM
    b = await db.get(BookORM, book["id"])
    b.available -= 1
    db.add(overdue_loan)
    await db.flush()

    r = await client.post(f"/loans/{overdue_loan.id}/return")
    assert r.status_code == 200
    data = r.json()
    # Fine = 6 days * $0.25 = $1.50
    assert data["fine_amount"] >= 1.50
    assert data["overdue"] is False   # returned, so no longer marked overdue
