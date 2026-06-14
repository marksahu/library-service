"""
app/repositories/loan_repo.py
"""
from datetime import datetime
from typing import Optional, List, Tuple

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.orm import Loan


class LoanRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_by_id(self, loan_id: int) -> Optional[Loan]:
        result = await self._db.execute(
            select(Loan)
            .options(selectinload(Loan.member), selectinload(Loan.book))
            .where(Loan.id == loan_id)
        )
        return result.scalar_one_or_none()

    async def find_active(self, member_id: int, book_id: int) -> Optional[Loan]:
        """Return the open loan for a (member, book) pair, if any."""
        return await self._db.scalar(
            select(Loan).where(
                and_(
                    Loan.member_id == member_id,
                    Loan.book_id == book_id,
                    Loan.returned_at.is_(None),
                )
            )
        )

    async def list(
        self,
        member_id: Optional[int],
        book_id: Optional[int],
        active_only: bool,
        page: int,
        limit: int,
    ) -> Tuple[List[Loan], int]:
        stmt = select(Loan).options(
            selectinload(Loan.member), selectinload(Loan.book)
        )
        if member_id:
            stmt = stmt.where(Loan.member_id == member_id)
        if book_id:
            stmt = stmt.where(Loan.book_id == book_id)
        if active_only:
            stmt = stmt.where(Loan.returned_at.is_(None))

        total = await self._db.scalar(select(func.count()).select_from(stmt.subquery()))
        loans = (
            await self._db.scalars(
                stmt.order_by(Loan.borrowed_at.desc())
                    .offset((page - 1) * limit)
                    .limit(limit)
            )
        ).all()
        return list(loans), total or 0

    async def save(self, loan: Loan) -> Loan:
        self._db.add(loan)
        await self._db.flush()
        return loan

    async def count_active(self) -> int:
        return (
            await self._db.scalar(
                select(func.count()).select_from(Loan).where(Loan.returned_at.is_(None))
            )
            or 0
        )

    async def count_overdue(self, now: datetime) -> int:
        return (
            await self._db.scalar(
                select(func.count()).select_from(Loan).where(
                    and_(Loan.returned_at.is_(None), Loan.due_at < now)
                )
            )
            or 0
        )

    async def sum_fines(self) -> float:
        result = await self._db.scalar(
            select(func.coalesce(func.sum(Loan.fine_amount), 0)).where(
                Loan.fine_amount > 0
            )
        )
        return float(result or 0)
