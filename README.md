# Neighborhood Library Service

A full-stack library management application built with **Python (FastAPI)**, **PostgreSQL**, and **Next.js (React)**.

```
┌─────────────┐     REST/JSON      ┌──────────────────┐     asyncpg      ┌────────────────┐
│  Next.js    │ ◄────────────────► │  FastAPI (Python) │ ◄──────────────► │  PostgreSQL 16 │
│  Frontend   │  http://localhost  │  :8000            │                   │  :5432         │
│  :3000      │                    └──────────────────┘                   └────────────────┘
└─────────────┘
```

\---

## Features

|Area|Details|
|-|-|
|**Books**|Create, read, update, delete; copy tracking; full-text search|
|**Members**|Register, update, soft-delete; email uniqueness|
|**Loans**|Borrow (with availability check), return, list/filter|
|**Fines**|Auto-calculated at $0.25/day overdue, finalised on return|
|**Dashboard**|Live stats: totals, active loans, overdue count, fine total|
|**Validation**|Pydantic v2 – all inputs validated before hitting the DB|
|**Error handling**|Meaningful 4xx responses (409 on duplicate borrow, 404, etc.)|

\---

## Quick Start (Docker – recommended)

**Prerequisites**: Docker 24+ and Docker Compose v2.

```bash
git clone <repo-url> library-service
cd library-service

# Build and start all three services (db + backend + frontend)
docker compose up --build
```

|Service|URL|
|-|-|
|Frontend|http://localhost:3000|
|API docs|http://localhost:8000/docs|
|DB|localhost:5432 (user/pass: `library`)|

The PostgreSQL `init.sql` script runs automatically on first start, creating all tables, indexes, views, and seed data.

\---

## Local Development (without Docker)

### 1 · PostgreSQL

```bash
# macOS
brew install postgresql@16 \&\& brew services start postgresql@16

# Ubuntu / Debian
sudo apt install postgresql-16

# Create DB and user
psql -U postgres <<'SQL'
CREATE USER library WITH PASSWORD 'library';
CREATE DATABASE librarydb OWNER library;
\\c librarydb
SQL

psql -U library -d librarydb -f scripts/init.sql
```

### 2 · Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\\Scripts\\activate

pip install -r requirements.txt

# Configure database URL (defaults work with the setup above)
export DATABASE\_URL="postgresql+asyncpg://library:library@localhost:5432/librarydb"

uvicorn app.main:app --reload --port 8000
```

Open **http://localhost:8000/docs** for the interactive Swagger UI.

### 3 · Frontend

```bash
cd frontend
npm install

# Point at the local backend
echo 'NEXT\_PUBLIC\_API\_URL=http://localhost:8000' > .env.local

npm run dev
```

Open **http://localhost:3000**.

\---

## Project Structure

```
library-service/
├── backend/
│   ├── app/
│   │   ├── db/
│   │   │   └── session.py          # SQLAlchemy async engine \& session
│   │   ├── models/
│   │   │   ├── orm.py              # SQLAlchemy ORM models
│   │   │   └── schemas.py          # Pydantic v2 request/response schemas
│   │   ├── services/
│   │   │   ├── book\_service.py     # Book CRUD logic
│   │   │   ├── member\_service.py   # Member CRUD logic
│   │   │   └── loan\_service.py     # Borrow / Return / Fine logic
│   │   └── main.py                 # FastAPI app, all route handlers
│   ├── proto/
│   │   └── library.proto           # gRPC / Protobuf definitions (reference)
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── app/
│   │   ├── page.tsx                # Dashboard
│   │   ├── books/page.tsx          # Book catalogue CRUD
│   │   ├── members/page.tsx        # Member management
│   │   └── loans/page.tsx          # Loans – borrow \& return
│   ├── components/
│   │   └── Sidebar.tsx
│   ├── lib/
│   │   └── api.ts                  # Typed API client
│   └── Dockerfile
├── scripts/
│   ├── init.sql                    # Full DB schema + seed data
│   └── sample\_client.py            # CLI demo of all API operations
└── docker-compose.yml
```

\---

## REST API Reference

### Books

|Method|Path|Description|
|-|-|-|
|`POST`|`/books`|Create a book|
|`GET`|`/books`|List books (`?search=\&page=\&limit=`)|
|`GET`|`/books/{id}`|Get single book|
|`PATCH`|`/books/{id}`|Update book fields|
|`DELETE`|`/books/{id}`|Delete book (only if no active loans)|

### Members

|Method|Path|Description|
|-|-|-|
|`POST`|`/members`|Register member|
|`GET`|`/members`|List members|
|`GET`|`/members/{id}`|Get single member|
|`PATCH`|`/members/{id}`|Update member|
|`DELETE`|`/members/{id}`|Soft-delete (deactivate)|

### Loans

|Method|Path|Description|
|-|-|-|
|`POST`|`/loans/borrow`|Borrow a book|
|`POST`|`/loans/{id}/return`|Return a book + compute fine|
|`GET`|`/loans`|List loans (`?member\_id=\&book\_id=\&active\_only=true`)|
|`GET`|`/loans/{id}`|Get single loan|

### Other

|Method|Path|Description|
|-|-|-|
|`GET`|`/dashboard`|Aggregate statistics|
|`GET`|`/health`|Health check|

\---

## Database Schema

```
books
  id, title, author, isbn (unique), genre, year,
  copies, available (≤ copies), created\_at, updated\_at

members
  id, name, email (unique), phone, address,
  active, joined\_at, updated\_at

loans
  id, member\_id → members(id), book\_id → books(id),
  borrowed\_at, due\_at, returned\_at (NULL = still out),
  fine\_amount
```

**Key constraints**:

* `available <= copies` — enforced by DB check constraint
* Borrowing decrements `available`; returning increments it
* Fine = $0.25 × overdue days (calculated live; persisted on return)
* Members can only be deactivated (soft-delete), never hard-deleted, to preserve loan history

\---

## Running the Sample Client

```bash
# With the backend running on :8000
cd library-service
pip install httpx        # if not already installed
python scripts/sample\_client.py

# Against a different host
python scripts/sample\_client.py --base-url http://my-server:8000
```

The script exercises: health check → create book → register member → borrow → duplicate-borrow (409) → return → dashboard.

\---

## gRPC / Protobuf

`backend/proto/library.proto` contains a full Protobuf 3 service definition covering all entities and operations. The REST implementation was chosen for the running service for broad client compatibility, but the `.proto` file serves as a precise, language-neutral contract and can be compiled to a gRPC server with:

```bash
pip install grpcio grpcio-tools
python -m grpc\_tools.protoc \\
  -I backend/proto \\
  --python\_out=backend/app/proto\_generated \\
  --grpc\_python\_out=backend/app/proto\_generated \\
  backend/proto/library.proto
```

\---

## Environment Variables

|Variable|Default|Description|
|-|-|-|
|`DATABASE\_URL`|`postgresql+asyncpg://library:library@localhost:5432/librarydb`|Async DB URL|
|`SQL\_ECHO`|`false`|Log all SQL to stdout|
|`NEXT\_PUBLIC\_API\_URL`|`http://localhost:8000`|Backend URL for the frontend|

\---

## Tech Stack

|Layer|Technology|
|-|-|
|API server|Python 3.12 · FastAPI · Uvicorn|
|ORM|SQLAlchemy 2 (async) · asyncpg|
|Validation|Pydantic v2|
|Database|PostgreSQL 16|
|Frontend|Next.js 15 · React 18 · TypeScript|
|Containers|Docker · Docker Compose|
|Service contract|Protobuf 3 / gRPC (`.proto` provided)|





## How to run library-service



Assuming you have Docker Desktop installed (if not, download it from docker.com), here are the steps:



Make sure Docker Desktop is running Open Docker Desktop and wait for it to say "Engine running".



Check out the library-service



Open a terminal in that folder cmd \~/Desktop/library-service



Start everything - docker compose up --build



This will take 2–3 minutes the first time (downloading images, installing dependencies). You'll see logs from three services: db, backend, and frontend. 5. Wait for this line in the logs library\_backend | INFO: Application startup complete.



That means the API is ready. 6. Open the app



Frontend UI → http://localhost:3000 API docs (Swagger) → http://localhost:8000/docs



To stop everything- Press Ctrl + C in the terminal, then:- bashdocker compose down

