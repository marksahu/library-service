"""
tests/test_books.py

Covers: create, get, update, delete, list, and all error branches.
"""
import pytest


@pytest.mark.asyncio
async def test_create_book(client):
    r = await client.post("/books", json={
        "title": "The Pragmatic Programmer",
        "author": "David Thomas",
        "isbn": "9780135957059",
        "copies": 3,
    })
    assert r.status_code == 201
    data = r.json()
    assert data["title"] == "The Pragmatic Programmer"
    assert data["available"] == 3
    assert data["copies"] == 3


@pytest.mark.asyncio
async def test_create_book_duplicate_isbn(client, book):
    r = await client.post("/books", json={
        "title": "Another Title",
        "author": "Some Author",
        "isbn": book["isbn"],   # same ISBN
        "copies": 1,
    })
    assert r.status_code == 409
    assert "ISBN" in r.json()["detail"]


@pytest.mark.asyncio
async def test_get_book(client, book):
    r = await client.get(f"/books/{book['id']}")
    assert r.status_code == 200
    assert r.json()["id"] == book["id"]


@pytest.mark.asyncio
async def test_get_book_not_found(client):
    r = await client.get("/books/99999")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_list_books(client, book):
    r = await client.get("/books")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] >= 1
    assert any(b["id"] == book["id"] for b in data["books"])


@pytest.mark.asyncio
async def test_list_books_search(client, book):
    r = await client.get(f"/books?search={book['author']}")
    assert r.status_code == 200
    assert r.json()["total"] >= 1


@pytest.mark.asyncio
async def test_update_book(client, book):
    r = await client.patch(f"/books/{book['id']}", json={"genre": "Engineering"})
    assert r.status_code == 200
    assert r.json()["genre"] == "Engineering"


@pytest.mark.asyncio
async def test_update_book_increase_copies(client, book):
    r = await client.patch(f"/books/{book['id']}", json={"copies": book["copies"] + 1})
    assert r.status_code == 200
    data = r.json()
    assert data["copies"] == book["copies"] + 1
    assert data["available"] == book["available"] + 1


@pytest.mark.asyncio
async def test_update_book_copies_below_loaned(client, book, loan):
    # 1 copy is on loan; try to set copies to 0 → should fail
    r = await client.patch(f"/books/{book['id']}", json={"copies": 0})
    assert r.status_code in (400, 422)   # business rule or validation


@pytest.mark.asyncio
async def test_delete_book(client):
    r = await client.post("/books", json={"title": "Temp", "author": "X", "copies": 1})
    assert r.status_code == 201
    bid = r.json()["id"]
    r = await client.delete(f"/books/{bid}")
    assert r.status_code == 204
    assert (await client.get(f"/books/{bid}")).status_code == 404


@pytest.mark.asyncio
async def test_delete_book_with_active_loan(client, book, loan):
    r = await client.delete(f"/books/{book['id']}")
    assert r.status_code == 400
    assert "active loans" in r.json()["detail"]
