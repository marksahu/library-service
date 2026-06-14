"""
app/repositories/member_repo.py
"""
from typing import Optional, List, Tuple

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.orm import Member


class MemberRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_by_id(self, member_id: int) -> Optional[Member]:
        return await self._db.get(Member, member_id)

    async def get_by_email(self, email: str, exclude_id: Optional[int] = None) -> Optional[Member]:
        stmt = select(Member).where(Member.email == email)
        if exclude_id is not None:
            stmt = stmt.where(Member.id != exclude_id)
        return await self._db.scalar(stmt)

    async def list(
        self,
        search: Optional[str],
        page: int,
        limit: int,
    ) -> Tuple[List[Member], int]:
        stmt = select(Member)
        if search:
            pattern = f"%{search}%"
            stmt = stmt.where(
                or_(Member.name.ilike(pattern), Member.email.ilike(pattern))
            )
        total = await self._db.scalar(select(func.count()).select_from(stmt.subquery()))
        members = (
            await self._db.scalars(
                stmt.order_by(Member.name)
                    .offset((page - 1) * limit)
                    .limit(limit)
            )
        ).all()
        return list(members), total or 0

    async def save(self, member: Member) -> Member:
        self._db.add(member)
        await self._db.flush()
        await self._db.refresh(member)
        return member

    async def count_active(self) -> int:
        return (
            await self._db.scalar(
                select(func.count()).select_from(Member).where(Member.active == True)
            )
            or 0
        )
