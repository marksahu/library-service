#!/usr/bin/env python3
"""
sample_client.py – demonstrates all core API operations against the running server.

Usage:
    python sample_client.py [--base-url http://localhost:8000]
"""
import sys
import json
import argparse
import httpx

BASE = "http://localhost:8000"


def hr(title: str):
    print(f"\n{'─'*55}")
    print(f"  {title}")
    print('─'*55)


def pp(data):
    print(json.dumps(data, indent=2, default=str))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default=BASE)
    args = parser.parse_args()
    base = args.base_url.rstrip("/")

    client = httpx.Client(base_url=base, timeout=10)

    # ── Health ──────────────────────────────────────────────────────────────
    hr("Health check")
    pp(client.get("/health").json())

    # ── Create a book ───────────────────────────────────────────────────────
    hr("Create a book")
    book = client.post("/books", json={
        "title": "Clean Code",
        "author": "Robert C. Martin",
        "isbn": "9780132350884",
        "genre": "Technology",
        "year": 2008,
        "copies": 2,
    }).json()
    pp(book)
    book_id = book["id"]

    # ── Create a member ─────────────────────────────────────────────────────
    hr("Register a member")
    member = client.post("/members", json={
        "name": "Diana Prince",
        "email": "diana@example.com",
        "phone": "555-0999",
        "address": "1 Amazon Way",
    }).json()
    pp(member)
    member_id = member["id"]

    # ── Borrow a book ───────────────────────────────────────────────────────
    hr("Borrow the book")
    loan = client.post("/loans/borrow", json={
        "member_id": member_id,
        "book_id": book_id,
        "loan_days": 14,
    }).json()
    pp(loan)
    loan_id = loan["id"]

    # ── List active loans for this member ───────────────────────────────────
    hr("Member's active loans")
    pp(client.get(f"/loans?member_id={member_id}&active_only=true").json())

    # ── Try to borrow same book again (should fail 409) ─────────────────────
    hr("Try duplicate borrow (expect 409)")
    r = client.post("/loans/borrow", json={"member_id": member_id, "book_id": book_id})
    print(f"Status: {r.status_code}  →  {r.json().get('detail')}")

    # ── Return the book ──────────────────────────────────────────────────────
    hr("Return the book")
    pp(client.post(f"/loans/{loan_id}/return").json())

    # ── Dashboard stats ──────────────────────────────────────────────────────
    hr("Dashboard stats")
    pp(client.get("/dashboard").json())

    print("\n✓ All sample operations completed.\n")


if __name__ == "__main__":
    main()
