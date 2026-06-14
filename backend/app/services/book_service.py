"""
app/services/book_service.py

Book business logic.  No FastAPI imports — only domain exceptions.
"""
from typing import Optional, Tuple, List

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ConflictError, BusinessRuleError
from app.core.logging import get_logger
from app.models.orm import Book
from app.models.schemas import BookCreate, BookUpdate
from app.repositories.book_repo import BookRepository

logger = get_logger(__name__)


async def create_book(db: AsyncSession, data: BookCreate) -> Book:
    repo = BookRepository(db)
    if data.isbn:
        if await repo.get_by_isbn(data.isbn):
            raise ConflictError(f"A book with ISBN '{data.isbn}' already exists.")
    book = Book(**data.model_dump(), available=data.copies)
    book = await repo.save(book)
    logger.info("book_created", book_id=book.id, title=book.title)
    return book


async def get_book(db: AsyncSession, book_id: int) -> Book:
    book = await BookRepository(db).get_by_id(book_id)
    if not book:
        raise NotFoundError(f"Book {book_id} not found.")
    return book


async def update_book(db: AsyncSession, book_id: int, data: BookUpdate) -> Book:
    repo = BookRepository(db)
    book = await repo.get_by_id(book_id)
    if not book:
        raise NotFoundError(f"Book {book_id} not found.")

    updates = data.model_dump(exclude_unset=True)

    if "copies" in updates:
        delta = updates["copies"] - book.copies
        new_available = book.available + delta
        if new_available < 0:
            raise BusinessRuleError(
                "Cannot reduce copies below the number currently on loan."
            )
        book.available = new_available

    if "isbn" in updates and updates["isbn"] != book.isbn:
        if await repo.get_by_isbn(updates["isbn"], exclude_id=book_id):
            raise ConflictError(f"ISBN '{updates['isbn']}' is already in use.")

    for key, val in updates.items():
        setattr(book, key, val)

    book = await repo.save(book)
    logger.info("book_updated", book_id=book.id)
    return book


async def delete_book(db: AsyncSession, book_id: int) -> None:
    repo = BookRepository(db)
    book = await repo.get_by_id(book_id)
    if not book:
        raise NotFoundError(f"Book {book_id} not found.")
    if book.available != book.copies:
        raise BusinessRuleError("Cannot delete a book that has active loans.")
    await repo.delete(book)
    logger.info("book_deleted", book_id=book_id)


async def list_books(
    db: AsyncSession,
    search: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
) -> Tuple[List[Book], int]:
    return await BookRepository(db).list(search, page, limit)
