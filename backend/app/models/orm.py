"""
SQLAlchemy ORM models mirroring the PostgreSQL schema.
"""
from datetime import datetime
from sqlalchemy import (
    Boolean, CheckConstraint, Column, DateTime, ForeignKey,
    Integer, Numeric, String, Text, func,
)
from sqlalchemy.orm import relationship
from app.db.session import Base


class Book(Base):
    __tablename__ = "books"

    id        = Column(Integer, primary_key=True, index=True)
    title     = Column(String(255), nullable=False)
    author    = Column(String(255), nullable=False)
    isbn      = Column(String(20), unique=True, nullable=True)
    genre     = Column(String(100), nullable=True)
    year      = Column(Integer, nullable=True)
    copies    = Column(Integer, nullable=False, default=1)
    available = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    loans = relationship("Loan", back_populates="book")

    __table_args__ = (
        CheckConstraint("available <= copies", name="available_lte_copies"),
        CheckConstraint("copies >= 0",        name="copies_non_negative"),
        CheckConstraint("available >= 0",     name="available_non_negative"),
    )


class Member(Base):
    __tablename__ = "members"

    id        = Column(Integer, primary_key=True, index=True)
    name      = Column(String(255), nullable=False)
    email     = Column(String(255), nullable=False, unique=True)
    phone     = Column(String(30), nullable=True)
    address   = Column(Text, nullable=True)
    active    = Column(Boolean, nullable=False, default=True)
    joined_at  = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    loans = relationship("Loan", back_populates="member")


class Loan(Base):
    __tablename__ = "loans"

    id          = Column(Integer, primary_key=True, index=True)
    member_id   = Column(Integer, ForeignKey("members.id", ondelete="RESTRICT"), nullable=False)
    book_id     = Column(Integer, ForeignKey("books.id",   ondelete="RESTRICT"), nullable=False)
    borrowed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    due_at      = Column(DateTime(timezone=True), nullable=False)
    returned_at = Column(DateTime(timezone=True), nullable=True)
    fine_amount = Column(Numeric(8, 2), nullable=False, default=0.00)

    member = relationship("Member", back_populates="loans")
    book   = relationship("Book",   back_populates="loans")
