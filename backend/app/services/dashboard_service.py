"""
app/services/dashboard_service.py

Aggregates library-wide statistics.
Previously inline in main.py — extracted for testability and separation.
"""
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schemas import DashboardStats
from app.repositories.book_repo import BookRepository
from app.repositories.loan_repo import LoanRepository
from app.repositories.member_repo import MemberRepository


async def get_stats(db: AsyncSession) -> DashboardStats:
    now = datetime.now(timezone.utc)
    total_books   = await BookRepository(db).count_total()
    total_members = await MemberRepository(db).count_active()
    active_loans  = await LoanRepository(db).count_active()
    overdue_loans = await LoanRepository(db).count_overdue(now)
    total_fines   = await LoanRepository(db).sum_fines()

    return DashboardStats(
        total_books=total_books,
        total_members=total_members,
        active_loans=active_loans,
        overdue_loans=overdue_loans,
        total_fines=total_fines,
    )
