"""
Loan service – borrow, return, fine calculation.
Fine rate: $0.25 per overdue day.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple, List
from decimal import Decimal

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import HTTPException

from app.models.orm import Book, Member, Loan
from app.models.schemas import BorrowRequest, LoanOut

FINE_PER_DAY = Decimal("0.25")
DEFAULT_LOAN_DAYS = 14


def _build_loan_out(loan: Loan) -> LoanOut:
    """Enrich a Loan ORM object into the response schema."""
    now = datetime.now(timezone.utc)
    due = loan.due_at.replace(tzinfo=timezone.utc) if loan.due_at.tzinfo is None else loan.due_at
    overdue = loan.returned_at is None and now > due

    if overdue:
        days_late = (now - due).total_seconds() / 86400
        fine = round(float(FINE_PER_DAY) * days_late, 2)
    else:
        fine = float(loan.fine_amount)

    return LoanOut(
        id=loan.id,
        member_id=loan.member_id,
        book_id=loan.book_id,
        member_name=loan.member.name,
        book_title=loan.book.title,
        borrowed_at=loan.borrowed_at,
        due_at=loan.due_at,
        returned_at=loan.returned_at,
        overdue=overdue,
        fine_amount=fine,
    )


async def _load_loan(db: AsyncSession, loan_id: int) -> Loan:
    result = await db.execute(
        select(Loan)
        .options(selectinload(Loan.member), selectinload(Loan.book))
        .where(Loan.id == loan_id)
    )
    loan = result.scalar_one_or_none()
    if not loan:
        raise HTTPException(404, detail=f"Loan {loan_id} not found.")
    return loan


async def borrow_book(db: AsyncSession, data: BorrowRequest) -> LoanOut:
    # Validate member
    member = await db.get(Member, data.member_id)
    if not member:
        raise HTTPException(404, detail=f"Member {data.member_id} not found.")
    if not member.active:
        raise HTTPException(400, detail="Inactive member cannot borrow books.")

    # Validate book
    book = await db.get(Book, data.book_id)
    if not book:
        raise HTTPException(404, detail=f"Book {data.book_id} not found.")
    if book.available < 1:
        raise HTTPException(409, detail=f"'{book.title}' has no available copies right now.")

    # Check member doesn't already have this book out
    existing = await db.scalar(
        select(Loan).where(
            and_(
                Loan.member_id == data.member_id,
                Loan.book_id   == data.book_id,
                Loan.returned_at.is_(None),
            )
        )
    )
    if existing:
        raise HTTPException(409, detail="This member already has this book checked out.")

    # Create loan
    loan_days = data.loan_days or DEFAULT_LOAN_DAYS
    now = datetime.now(timezone.utc)
    loan = Loan(
        member_id=data.member_id,
        book_id=data.book_id,
        borrowed_at=now,
        due_at=now + timedelta(days=loan_days),
    )
    book.available -= 1
    db.add(loan)
    await db.flush()

    loan = await _load_loan(db, loan.id)
    return _build_loan_out(loan)


async def return_book(db: AsyncSession, loan_id: int) -> LoanOut:
    loan = await _load_loan(db, loan_id)

    if loan.returned_at is not None:
        raise HTTPException(400, detail="This book has already been returned.")

    now = datetime.now(timezone.utc)
    loan.returned_at = now

    # Calculate final fine
    due = loan.due_at.replace(tzinfo=timezone.utc) if loan.due_at.tzinfo is None else loan.due_at
    if now > due:
        days_late = (now - due).total_seconds() / 86400
        loan.fine_amount = round(float(FINE_PER_DAY) * days_late, 2)

    # Restore book availability
    loan.book.available += 1

    await db.flush()
    return _build_loan_out(loan)


async def get_loan(db: AsyncSession, loan_id: int) -> LoanOut:
    loan = await _load_loan(db, loan_id)
    return _build_loan_out(loan)


async def list_loans(
    db: AsyncSession,
    member_id: Optional[int] = None,
    book_id: Optional[int] = None,
    active_only: bool = False,
    page: int = 1,
    limit: int = 20,
) -> Tuple[List[LoanOut], int]:
    query = (
        select(Loan)
        .options(selectinload(Loan.member), selectinload(Loan.book))
    )
    if member_id:
        query = query.where(Loan.member_id == member_id)
    if book_id:
        query = query.where(Loan.book_id == book_id)
    if active_only:
        query = query.where(Loan.returned_at.is_(None))

    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    loans = (await db.scalars(
        query.order_by(Loan.borrowed_at.desc())
             .offset((page - 1) * limit)
             .limit(limit)
    )).all()

    return [_build_loan_out(l) for l in loans], total or 0
