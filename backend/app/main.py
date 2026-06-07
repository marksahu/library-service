"""
Neighborhood Library Service – FastAPI application entry point.
"""
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Depends, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import engine, Base, AsyncSessionLocal, get_db
from app.models import orm  # noqa: F401 – register all ORM models with Base
from app.models.schemas import (
    BookCreate, BookUpdate, BookOut, BookList,
    MemberCreate, MemberUpdate, MemberOut, MemberList,
    BorrowRequest, LoanOut, LoanList,
    DashboardStats,
)
from app.services import book_service, member_service, loan_service
from app.models.orm import Loan


# ─── Lifespan ─────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables if they don't exist (DDL already in init.sql; this is a safety net)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


# ─── App ──────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Neighborhood Library Service",
    description="REST API for managing library books, members, and borrowing operations.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten in production
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Books ────────────────────────────────────────────────────────────────────

@app.post("/books", response_model=BookOut, status_code=201, tags=["Books"])
async def create_book(data: BookCreate, db: AsyncSession = Depends(get_db)):
    return await book_service.create_book(db, data)


@app.get("/books", response_model=BookList, tags=["Books"])
async def list_books(
    search: Optional[str] = Query(None, description="Search by title or author"),
    page:   int = Query(1,  ge=1),
    limit:  int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    books, total = await book_service.list_books(db, search, page, limit)
    return BookList(books=books, total=total)


@app.get("/books/{book_id}", response_model=BookOut, tags=["Books"])
async def get_book(book_id: int, db: AsyncSession = Depends(get_db)):
    return await book_service.get_book(db, book_id)


@app.patch("/books/{book_id}", response_model=BookOut, tags=["Books"])
async def update_book(book_id: int, data: BookUpdate, db: AsyncSession = Depends(get_db)):
    return await book_service.update_book(db, book_id, data)


@app.delete("/books/{book_id}", status_code=204, tags=["Books"])
async def delete_book(book_id: int, db: AsyncSession = Depends(get_db)):
    await book_service.delete_book(db, book_id)


# ─── Members ──────────────────────────────────────────────────────────────────

@app.post("/members", response_model=MemberOut, status_code=201, tags=["Members"])
async def create_member(data: MemberCreate, db: AsyncSession = Depends(get_db)):
    return await member_service.create_member(db, data)


@app.get("/members", response_model=MemberList, tags=["Members"])
async def list_members(
    search: Optional[str] = Query(None),
    page:   int = Query(1, ge=1),
    limit:  int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    members, total = await member_service.list_members(db, search, page, limit)
    return MemberList(members=members, total=total)


@app.get("/members/{member_id}", response_model=MemberOut, tags=["Members"])
async def get_member(member_id: int, db: AsyncSession = Depends(get_db)):
    return await member_service.get_member(db, member_id)


@app.patch("/members/{member_id}", response_model=MemberOut, tags=["Members"])
async def update_member(member_id: int, data: MemberUpdate, db: AsyncSession = Depends(get_db)):
    return await member_service.update_member(db, member_id, data)


@app.delete("/members/{member_id}", status_code=204, tags=["Members"])
async def delete_member(member_id: int, db: AsyncSession = Depends(get_db)):
    await member_service.delete_member(db, member_id)


# ─── Loans ────────────────────────────────────────────────────────────────────

@app.post("/loans/borrow", response_model=LoanOut, status_code=201, tags=["Loans"])
async def borrow_book(data: BorrowRequest, db: AsyncSession = Depends(get_db)):
    return await loan_service.borrow_book(db, data)


@app.post("/loans/{loan_id}/return", response_model=LoanOut, tags=["Loans"])
async def return_book(loan_id: int, db: AsyncSession = Depends(get_db)):
    return await loan_service.return_book(db, loan_id)


@app.get("/loans", response_model=LoanList, tags=["Loans"])
async def list_loans(
    member_id:   Optional[int]  = Query(None),
    book_id:     Optional[int]  = Query(None),
    active_only: bool           = Query(False),
    page:        int            = Query(1, ge=1),
    limit:       int            = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    loans, total = await loan_service.list_loans(db, member_id, book_id, active_only, page, limit)
    return LoanList(loans=loans, total=total)


@app.get("/loans/{loan_id}", response_model=LoanOut, tags=["Loans"])
async def get_loan(loan_id: int, db: AsyncSession = Depends(get_db)):
    return await loan_service.get_loan(db, loan_id)


# ─── Dashboard ────────────────────────────────────────────────────────────────

@app.get("/dashboard", response_model=DashboardStats, tags=["Dashboard"])
async def dashboard(db: AsyncSession = Depends(get_db)):
    from app.models.orm import Book, Member
    from datetime import datetime, timezone

    total_books   = await db.scalar(select(func.count()).select_from(Book))
    total_members = await db.scalar(select(func.count()).select_from(Member).where(Member.active == True))
    active_loans  = await db.scalar(
        select(func.count()).select_from(Loan).where(Loan.returned_at.is_(None))
    )
    now = datetime.now(timezone.utc)
    overdue_loans = await db.scalar(
        select(func.count()).select_from(Loan).where(
            and_(Loan.returned_at.is_(None), Loan.due_at < now)
        )
    )
    total_fines = await db.scalar(
        select(func.coalesce(func.sum(Loan.fine_amount), 0)).where(Loan.fine_amount > 0)
    )

    return DashboardStats(
        total_books=total_books or 0,
        total_members=total_members or 0,
        active_loans=active_loans or 0,
        overdue_loans=overdue_loans or 0,
        total_fines=float(total_fines or 0),
    )


# ─── Health ───────────────────────────────────────────────────────────────────

@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok"}
