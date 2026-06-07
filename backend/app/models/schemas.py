"""
Pydantic v2 schemas for request/response validation.
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, field_validator


# ─── Book schemas ─────────────────────────────────────────────────────────────

class BookBase(BaseModel):
    title:  str = Field(..., min_length=1, max_length=255)
    author: str = Field(..., min_length=1, max_length=255)
    isbn:   Optional[str] = Field(None, max_length=20)
    genre:  Optional[str] = Field(None, max_length=100)
    year:   Optional[int] = Field(None, ge=1000, le=2100)
    copies: int           = Field(1, ge=1)


class BookCreate(BookBase):
    pass


class BookUpdate(BaseModel):
    title:  Optional[str] = Field(None, min_length=1, max_length=255)
    author: Optional[str] = Field(None, min_length=1, max_length=255)
    isbn:   Optional[str] = Field(None, max_length=20)
    genre:  Optional[str] = Field(None, max_length=100)
    year:   Optional[int] = Field(None, ge=1000, le=2100)
    copies: Optional[int] = Field(None, ge=1)


class BookOut(BookBase):
    id:        int
    available: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BookList(BaseModel):
    books: List[BookOut]
    total: int


# ─── Member schemas ───────────────────────────────────────────────────────────

class MemberBase(BaseModel):
    name:    str           = Field(..., min_length=1, max_length=255)
    email:   EmailStr
    phone:   Optional[str] = Field(None, max_length=30)
    address: Optional[str] = None


class MemberCreate(MemberBase):
    pass


class MemberUpdate(BaseModel):
    name:    Optional[str]   = Field(None, min_length=1, max_length=255)
    email:   Optional[EmailStr] = None
    phone:   Optional[str]   = Field(None, max_length=30)
    address: Optional[str]   = None
    active:  Optional[bool]  = None


class MemberOut(MemberBase):
    id:        int
    active:    bool
    joined_at:  datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MemberList(BaseModel):
    members: List[MemberOut]
    total:   int


# ─── Loan schemas ─────────────────────────────────────────────────────────────

class BorrowRequest(BaseModel):
    member_id: int = Field(..., gt=0)
    book_id:   int = Field(..., gt=0)
    loan_days: int = Field(14, ge=1, le=180)


class ReturnRequest(BaseModel):
    loan_id: int = Field(..., gt=0)


class LoanOut(BaseModel):
    id:          int
    member_id:   int
    book_id:     int
    member_name: str
    book_title:  str
    borrowed_at: datetime
    due_at:      datetime
    returned_at: Optional[datetime]
    overdue:     bool
    fine_amount: float

    model_config = {"from_attributes": True}


class LoanList(BaseModel):
    loans: List[LoanOut]
    total: int


# ─── Dashboard ────────────────────────────────────────────────────────────────

class DashboardStats(BaseModel):
    total_books:   int
    total_members: int
    active_loans:  int
    overdue_loans: int
    total_fines:   float
