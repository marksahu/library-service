"""
app/repositories/book_repo.py

All database access for the Book entity.
Services call repository methods; they never build SQLAlchemy queries directly.
"""
from typing import Optional, List, Tuple

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.orm import Book


class BookRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_by_id(self, book_id: int) -> Optional[Book]:
        return await self._db.get(Book, book_id)

    async def get_by_isbn(self, isbn: str, exclude_id: Optional[int] = None) -> Optional[Book]:
        stmt = select(Book).where(Book.isbn == isbn)
        if exclude_id is not None:
            stmt = stmt.where(Book.id != exclude_id)
        return await self._db.scalar(stmt)

    async def list(
        self,
        search: Optional[str],
        page: int,
        limit: int,
    ) -> Tuple[List[Book], int]:
        stmt = select(Book)
        if search:
            pattern = f"%{search}%"
            stmt = stmt.where(
                or_(Book.title.ilike(pattern), Book.author.ilike(pattern))
            )
        total = await self._db.scalar(select(func.count()).select_from(stmt.subquery()))
        books = (
            await self._db.scalars(
                stmt.order_by(Book.title)
                    .offset((page - 1) * limit)
                    .limit(limit)
            )
        ).all()
        return list(books), total or 0

    async def save(self, book: Book) -> Book:
        self._db.add(book)
        await self._db.flush()
        await self._db.refresh(book)
        return book

    async def delete(self, book: Book) -> None:
        await self._db.delete(book)
        await self._db.flush()

    async def count_total(self) -> int:
        return await self._db.scalar(select(func.count()).select_from(Book)) or 0
