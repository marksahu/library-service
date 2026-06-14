"""
app/services/member_service.py

Member business logic.  No FastAPI imports.
"""
from typing import Optional, Tuple, List

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ConflictError
from app.core.logging import get_logger
from app.models.orm import Member
from app.models.schemas import MemberCreate, MemberUpdate
from app.repositories.member_repo import MemberRepository

logger = get_logger(__name__)


async def create_member(db: AsyncSession, data: MemberCreate) -> Member:
    repo = MemberRepository(db)
    if await repo.get_by_email(data.email):
        raise ConflictError(f"Email '{data.email}' is already registered.")
    member = Member(**data.model_dump())
    member = await repo.save(member)
    logger.info("member_created", member_id=member.id, email=member.email)
    return member


async def get_member(db: AsyncSession, member_id: int) -> Member:
    member = await MemberRepository(db).get_by_id(member_id)
    if not member:
        raise NotFoundError(f"Member {member_id} not found.")
    return member


async def update_member(db: AsyncSession, member_id: int, data: MemberUpdate) -> Member:
    repo = MemberRepository(db)
    member = await repo.get_by_id(member_id)
    if not member:
        raise NotFoundError(f"Member {member_id} not found.")

    updates = data.model_dump(exclude_unset=True)
    if "email" in updates and updates["email"] != member.email:
        if await repo.get_by_email(updates["email"], exclude_id=member_id):
            raise ConflictError(f"Email '{updates['email']}' is already in use.")

    for k, v in updates.items():
        setattr(member, k, v)

    member = await repo.save(member)
    logger.info("member_updated", member_id=member.id)
    return member


async def delete_member(db: AsyncSession, member_id: int) -> None:
    repo = MemberRepository(db)
    member = await repo.get_by_id(member_id)
    if not member:
        raise NotFoundError(f"Member {member_id} not found.")
    member.active = False          # soft-delete preserves loan history
    await repo.save(member)
    logger.info("member_deactivated", member_id=member_id)


async def list_members(
    db: AsyncSession,
    search: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
) -> Tuple[List[Member], int]:
    return await MemberRepository(db).list(search, page, limit)
