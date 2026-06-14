"""
app/services/loan_service.py

Loan business logic – borrow, return, fine calculation.
Fine rate: $0.25 per overdue day.
No FastAPI imports.
"""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional, Tuple, List

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ConflictError, BusinessRuleError
from app.core.logging import get_logger
from app.models.orm import Loan
from app.models.schemas import BorrowRequest, LoanOut
from app.repositories.book_repo import BookRepository
from app.repositories.loan_repo import LoanRepository
from app.repositories.member_repo import MemberRepository

logger = get_logger(__name__)

FINE_PER_DAY = Decimal("0.25")
DEFAULT_LOAN_DAYS = 14


def _compute_fine(due_at: datetime, now: datetime) -> float:
    """Calculate live fine for an unreturned overdue loan."""
    due = due_at.replace(tzinfo=timezone.utc) if due_at.tzinfo is None else due_at
    if now <= due:
        return 0.0
    days_late = (now - due).total_seconds() / 86400
    return round(float(FINE_PER_DAY) * days_late, 2)


def _to_loan_out(loan: Loan) -> LoanOut:
    now = datetime.now(timezone.utc)
    if loan.returned_at is None:
        fine = _compute_fine(loan.due_at, now)
        overdue = fine > 0
    else:
        fine = float(loan.fine_amount)
        overdue = False

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


async def borrow_book(db: AsyncSession, data: BorrowRequest) -> LoanOut:
    member_repo = MemberRepository(db)
    book_repo   = BookRepository(db)
    loan_repo   = LoanRepository(db)

    member = await member_repo.get_by_id(data.member_id)
    if not member:
        raise NotFoundError(f"Member {data.member_id} not found.")
    if not member.active:
        raise BusinessRuleError("Inactive member cannot borrow books.")

    book = await book_repo.get_by_id(data.book_id)
    if not book:
        raise NotFoundError(f"Book {data.book_id} not found.")
    if book.available < 1:
        raise ConflictError(f"'{book.title}' has no available copies right now.")

    if await loan_repo.find_active(data.member_id, data.book_id):
        raise ConflictError("This member already has this book checked out.")

    loan_days = data.loan_days or DEFAULT_LOAN_DAYS
    now = datetime.now(timezone.utc)
    loan = Loan(
        member_id=data.member_id,
        book_id=data.book_id,
        borrowed_at=now,
        due_at=now + timedelta(days=loan_days),
    )
    book.available -= 1
    loan = await loan_repo.save(loan)

    # Reload with relationships for the response
    loan = await loan_repo.get_by_id(loan.id)
    logger.info("book_borrowed", loan_id=loan.id, member_id=data.member_id, book_id=data.book_id)
    return _to_loan_out(loan)


async def return_book(db: AsyncSession, loan_id: int) -> LoanOut:
    loan_repo = LoanRepository(db)
    loan = await loan_repo.get_by_id(loan_id)
    if not loan:
        raise NotFoundError(f"Loan {loan_id} not found.")
    if loan.returned_at is not None:
        raise BusinessRuleError("This book has already been returned.")

    now = datetime.now(timezone.utc)
    loan.returned_at = now
    loan.fine_amount = _compute_fine(loan.due_at, now)
    loan.book.available += 1

    await loan_repo.save(loan)
    logger.info(
        "book_returned",
        loan_id=loan_id,
        fine_amount=float(loan.fine_amount),
    )
    return _to_loan_out(loan)


async def get_loan(db: AsyncSession, loan_id: int) -> LoanOut:
    loan = await LoanRepository(db).get_by_id(loan_id)
    if not loan:
        raise NotFoundError(f"Loan {loan_id} not found.")
    return _to_loan_out(loan)


async def list_loans(
    db: AsyncSession,
    member_id: Optional[int] = None,
    book_id: Optional[int] = None,
    active_only: bool = False,
    page: int = 1,
    limit: int = 20,
) -> Tuple[List[LoanOut], int]:
    loans, total = await LoanRepository(db).list(member_id, book_id, active_only, page, limit)
    return [_to_loan_out(l) for l in loans], total
