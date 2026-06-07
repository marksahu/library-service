"""
Member CRUD service.
"""
from typing import Optional, Tuple, List
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.models.orm import Member
from app.models.schemas import MemberCreate, MemberUpdate


async def create_member(db: AsyncSession, data: MemberCreate) -> Member:
    existing = await db.scalar(select(Member).where(Member.email == data.email))
    if existing:
        raise HTTPException(409, detail=f"Email '{data.email}' is already registered.")
    member = Member(**data.model_dump())
    db.add(member)
    await db.flush()
    await db.refresh(member)
    return member


async def get_member(db: AsyncSession, member_id: int) -> Member:
    member = await db.get(Member, member_id)
    if not member:
        raise HTTPException(404, detail=f"Member {member_id} not found.")
    return member


async def update_member(db: AsyncSession, member_id: int, data: MemberUpdate) -> Member:
    member = await get_member(db, member_id)
    updates = data.model_dump(exclude_unset=True)
    if "email" in updates and updates["email"] != member.email:
        clash = await db.scalar(
            select(Member).where(Member.email == updates["email"], Member.id != member_id)
        )
        if clash:
            raise HTTPException(409, detail=f"Email '{updates['email']}' is already in use.")
    for k, v in updates.items():
        setattr(member, k, v)
    await db.flush()
    await db.refresh(member)
    return member


async def delete_member(db: AsyncSession, member_id: int) -> None:
    member = await get_member(db, member_id)
    # soft-delete: just deactivate
    member.active = False
    await db.flush()


async def list_members(
    db: AsyncSession,
    search: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
) -> Tuple[List[Member], int]:
    query = select(Member)
    if search:
        pattern = f"%{search}%"
        query = query.where(
            or_(Member.name.ilike(pattern), Member.email.ilike(pattern))
        )
    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    members = (await db.scalars(
        query.order_by(Member.name).offset((page - 1) * limit).limit(limit)
    )).all()
    return members, total or 0
