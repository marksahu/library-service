"""
app/main.py

FastAPI application – routing only.
Business logic lives in services; DB queries live in repositories.
"""
import os
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Depends, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    LibraryError, NotFoundError, ConflictError, BusinessRuleError,
)
from app.core.logging import configure_logging, get_logger
from app.core.middleware import RequestContextMiddleware
from app.db.session import engine, Base, get_db
from app.models import orm  # noqa: F401 – registers ORM models with Base
from app.models.schemas import (
    BookCreate, BookUpdate, BookOut, BookList,
    MemberCreate, MemberUpdate, MemberOut, MemberList,
    BorrowRequest, LoanOut, LoanList,
    DashboardStats,
)
from app.services import book_service, member_service, loan_service, dashboard_service

configure_logging(os.environ.get("LOG_LEVEL", "INFO"))
logger = get_logger(__name__)


# ─── Lifespan ─────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("application_startup")
    yield
    logger.info("application_shutdown")


# ─── App ──────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Neighborhood Library Service",
    description="REST API for managing library books, members, and borrowing.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(RequestContextMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Global exception handlers ────────────────────────────────────────────────

_STATUS_MAP = {
    NotFoundError:     404,
    ConflictError:     409,
    BusinessRuleError: 400,
}


@app.exception_handler(LibraryError)
async def library_error_handler(request: Request, exc: LibraryError) -> JSONResponse:
    status_code = _STATUS_MAP.get(type(exc), 500)
    logger.warning(
        "domain_error",
        error_type=type(exc).__name__,
        message=exc.message,
        path=request.url.path,
    )
    return JSONResponse(status_code=status_code, content={"detail": exc.message})


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("unhandled_error", path=request.url.path)
    return JSONResponse(status_code=500, content={"detail": "An unexpected error occurred."})


# ─── Books ────────────────────────────────────────────────────────────────────

@app.post("/books", response_model=BookOut, status_code=201, tags=["Books"])
async def create_book(data: BookCreate, db: AsyncSession = Depends(get_db)):
    return await book_service.create_book(db, data)


@app.get("/books", response_model=BookList, tags=["Books"])
async def list_books(
    search: Optional[str] = Query(None),
    page:   int = Query(1,  ge=1),
    limit:  int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    books, total = await book_service.list_books(db, search, page, limit)
    return BookList(books=books, total=total)


@app.get("/books/{book_id}", response_model=BookOut, tags=["Books"])
async def get_book(book_id: int, db: AsyncSession = Depends(get_db)):
    return await book_service.get_book(db, book_id)


@app.patch("/books/{book_id}", response_model=BookOut, tags=["Books"])
async def update_book(book_id: int, data: BookUpdate, db: AsyncSession = Depends(get_db)):
    return await book_service.update_book(db, book_id, data)


@app.delete("/books/{book_id}", status_code=204, tags=["Books"])
async def delete_book(book_id: int, db: AsyncSession = Depends(get_db)):
    await book_service.delete_book(db, book_id)


# ─── Members ──────────────────────────────────────────────────────────────────

@app.post("/members", response_model=MemberOut, status_code=201, tags=["Members"])
async def create_member(data: MemberCreate, db: AsyncSession = Depends(get_db)):
    return await member_service.create_member(db, data)


@app.get("/members", response_model=MemberList, tags=["Members"])
async def list_members(
    search: Optional[str] = Query(None),
    page:   int = Query(1, ge=1),
    limit:  int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    members, total = await member_service.list_members(db, search, page, limit)
    return MemberList(members=members, total=total)


@app.get("/members/{member_id}", response_model=MemberOut, tags=["Members"])
async def get_member(member_id: int, db: AsyncSession = Depends(get_db)):
    return await member_service.get_member(db, member_id)


@app.patch("/members/{member_id}", response_model=MemberOut, tags=["Members"])
async def update_member(member_id: int, data: MemberUpdate, db: AsyncSession = Depends(get_db)):
    return await member_service.update_member(db, member_id, data)


@app.delete("/members/{member_id}", status_code=204, tags=["Members"])
async def delete_member(member_id: int, db: AsyncSession = Depends(get_db)):
    await member_service.delete_member(db, member_id)


# ─── Loans ────────────────────────────────────────────────────────────────────

@app.post("/loans/borrow", response_model=LoanOut, status_code=201, tags=["Loans"])
async def borrow_book(data: BorrowRequest, db: AsyncSession = Depends(get_db)):
    return await loan_service.borrow_book(db, data)


@app.post("/loans/{loan_id}/return", response_model=LoanOut, tags=["Loans"])
async def return_book(loan_id: int, db: AsyncSession = Depends(get_db)):
    return await loan_service.return_book(db, loan_id)


@app.get("/loans", response_model=LoanList, tags=["Loans"])
async def list_loans(
    member_id:   Optional[int] = Query(None),
    book_id:     Optional[int] = Query(None),
    active_only: bool          = Query(False),
    page:        int           = Query(1, ge=1),
    limit:       int           = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    loans, total = await loan_service.list_loans(db, member_id, book_id, active_only, page, limit)
    return LoanList(loans=loans, total=total)


@app.get("/loans/{loan_id}", response_model=LoanOut, tags=["Loans"])
async def get_loan(loan_id: int, db: AsyncSession = Depends(get_db)):
    return await loan_service.get_loan(db, loan_id)


# ─── Dashboard ────────────────────────────────────────────────────────────────

@app.get("/dashboard", response_model=DashboardStats, tags=["Dashboard"])
async def dashboard(db: AsyncSession = Depends(get_db)):
    return await dashboard_service.get_stats(db)


# ─── Health (DB-aware) ────────────────────────────────────────────────────────

@app.get("/health", tags=["Health"])
async def health(db: AsyncSession = Depends(get_db)):
    try:
        from sqlalchemy import text
        await db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "reachable"}
    except Exception as exc:
        logger.error("health_check_failed", error=str(exc))
        return JSONResponse(
            status_code=503,
            content={"status": "degraded", "database": "unreachable"},
        )
