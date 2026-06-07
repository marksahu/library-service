"""
Book CRUD service.
"""
from typing import Optional, Tuple, List
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.orm import Book
from app.models.schemas import BookCreate, BookUpdate


async def create_book(db: AsyncSession, data: BookCreate) -> Book:
    # Check ISBN uniqueness
    if data.isbn:
        existing = await db.scalar(select(Book).where(Book.isbn == data.isbn))
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A book with ISBN '{data.isbn}' already exists."
            )
    book = Book(**data.model_dump(), available=data.copies)
    db.add(book)
    await db.flush()
    await db.refresh(book)
    return book


async def get_book(db: AsyncSession, book_id: int) -> Book:
    book = await db.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail=f"Book {book_id} not found.")
    return book


async def update_book(db: AsyncSession, book_id: int, data: BookUpdate) -> Book:
    book = await get_book(db, book_id)
    updates = data.model_dump(exclude_unset=True)

    # If copies change, adjust available proportionally
    if "copies" in updates:
        delta = updates["copies"] - book.copies
        new_available = book.available + delta
        if new_available < 0:
            raise HTTPException(
                status_code=400,
                detail="Cannot reduce copies below the number currently on loan."
            )
        book.available = new_available

    # ISBN uniqueness check
    if "isbn" in updates and updates["isbn"] != book.isbn:
        existing = await db.scalar(
            select(Book).where(Book.isbn == updates["isbn"], Book.id != book_id)
        )
        if existing:
            raise HTTPException(409, detail=f"ISBN '{updates['isbn']}' already in use.")

    for key, val in updates.items():
        setattr(book, key, val)

    await db.flush()
    await db.refresh(book)
    return book


async def delete_book(db: AsyncSession, book_id: int) -> None:
    book = await get_book(db, book_id)
    if book.available != book.copies:
        raise HTTPException(400, detail="Cannot delete a book that has active loans.")
    await db.delete(book)


async def list_books(
    db: AsyncSession,
    search: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
) -> Tuple[List[Book], int]:
    query = select(Book)
    if search:
        pattern = f"%{search}%"
        query = query.where(
            or_(Book.title.ilike(pattern), Book.author.ilike(pattern))
        )
    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    books = (await db.scalars(
        query.order_by(Book.title).offset((page - 1) * limit).limit(limit)
    )).all()
    return books, total or 0
