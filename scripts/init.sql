-- ============================================================
--  Neighborhood Library Service – Database Schema
--  PostgreSQL 15+
-- ============================================================

-- Enable UUID extension (optional, kept for extensibility)
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ─── Books ───────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS books (
    id         SERIAL PRIMARY KEY,
    title      VARCHAR(255) NOT NULL,
    author     VARCHAR(255) NOT NULL,
    isbn       VARCHAR(20)  UNIQUE,
    genre      VARCHAR(100),
    year       SMALLINT     CHECK (year BETWEEN 1000 AND 2100),
    copies     INT          NOT NULL DEFAULT 1 CHECK (copies >= 0),
    available  INT          NOT NULL DEFAULT 1 CHECK (available >= 0),
    created_at TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    CONSTRAINT available_lte_copies CHECK (available <= copies)
);

CREATE INDEX idx_books_title  ON books USING gin(to_tsvector('english', title));
CREATE INDEX idx_books_author ON books USING gin(to_tsvector('english', author));
CREATE INDEX idx_books_isbn   ON books (isbn) WHERE isbn IS NOT NULL;

-- ─── Members ─────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS members (
    id         SERIAL PRIMARY KEY,
    name       VARCHAR(255) NOT NULL,
    email      VARCHAR(255) NOT NULL UNIQUE,
    phone      VARCHAR(30),
    address    TEXT,
    active     BOOLEAN      NOT NULL DEFAULT TRUE,
    joined_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_members_email  ON members (email);
CREATE INDEX idx_members_name   ON members USING gin(to_tsvector('english', name));
CREATE INDEX idx_members_active ON members (active);

-- ─── Loans ───────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS loans (
    id          SERIAL PRIMARY KEY,
    member_id   INT         NOT NULL REFERENCES members(id) ON DELETE RESTRICT,
    book_id     INT         NOT NULL REFERENCES books(id)   ON DELETE RESTRICT,
    borrowed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    due_at      TIMESTAMPTZ NOT NULL,
    returned_at TIMESTAMPTZ,          -- NULL while book is still out
    fine_amount NUMERIC(8,2) NOT NULL DEFAULT 0.00,

    CONSTRAINT returned_after_borrowed CHECK (
        returned_at IS NULL OR returned_at >= borrowed_at
    )
);

CREATE INDEX idx_loans_member     ON loans (member_id);
CREATE INDEX idx_loans_book       ON loans (book_id);
CREATE INDEX idx_loans_active     ON loans (returned_at) WHERE returned_at IS NULL;
CREATE INDEX idx_loans_overdue    ON loans (due_at)      WHERE returned_at IS NULL;

-- ─── Auto-update updated_at ──────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_books_updated_at
    BEFORE UPDATE ON books
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_members_updated_at
    BEFORE UPDATE ON members
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ─── Fine calculation view ────────────────────────────────────────────────────
-- Fine rate: $0.25 per day overdue

CREATE OR REPLACE VIEW active_loans_view AS
SELECT
    l.id,
    l.member_id,
    l.book_id,
    m.name   AS member_name,
    b.title  AS book_title,
    l.borrowed_at,
    l.due_at,
    l.returned_at,
    CASE
        WHEN l.returned_at IS NULL AND NOW() > l.due_at
        THEN ROUND(EXTRACT(EPOCH FROM (NOW() - l.due_at)) / 86400 * 0.25, 2)
        ELSE l.fine_amount
    END AS fine_amount,
    (l.returned_at IS NULL AND NOW() > l.due_at) AS overdue
FROM loans l
JOIN members m ON m.id = l.member_id
JOIN books   b ON b.id = l.book_id;

-- ─── Seed data (sample) ──────────────────────────────────────────────────────

INSERT INTO books (title, author, isbn, genre, year, copies, available) VALUES
  ('The Hitchhiker''s Guide to the Galaxy', 'Douglas Adams',     '9780345391803', 'Science Fiction', 1979, 3, 3),
  ('To Kill a Mockingbird',                 'Harper Lee',         '9780061935466', 'Classic Fiction',  1960, 2, 2),
  ('1984',                                  'George Orwell',      '9780451524935', 'Dystopian',        1949, 4, 4),
  ('The Great Gatsby',                      'F. Scott Fitzgerald','9780743273565', 'Classic Fiction',  1925, 2, 2),
  ('Dune',                                  'Frank Herbert',      '9780441013593', 'Science Fiction', 1965, 3, 3),
  ('The Pragmatic Programmer',              'David Thomas',       '9780135957059', 'Technology',       2019, 2, 2)
ON CONFLICT DO NOTHING;

INSERT INTO members (name, email, phone, address) VALUES
  ('Alice Johnson', 'alice@example.com', '555-0101', '12 Maple St, Townsville'),
  ('Bob Smith',     'bob@example.com',   '555-0102', '34 Oak Ave, Townsville'),
  ('Carol White',   'carol@example.com', '555-0103', '56 Pine Rd, Townsville')
ON CONFLICT DO NOTHING;
