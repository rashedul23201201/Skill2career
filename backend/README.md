# SKILL2CAREER - Backend Foundation

> **Bangladesh Job Preparation Ecosystem**  
> *Tagline:* Learn Today, Get Hired Tomorrow

---

## 1. Overview

The backend is built with **FastAPI**, **SQLAlchemy 2.x**, **Pydantic v2**, and **Alembic**, backed by **MySQL**. It follows a strict **Clean Layered Architecture** separating API routing, business logic, data access, and database modeling.

```text
Presentation Layer (Frontend / API Clients)
              ↓
      API / Router Layer (`app/routers/`)
              ↓
  Business Logic / Service Layer (`app/services/`)
              ↓
 Data Access / Repository Layer (`app/repositories/`)
              ↓
        SQLAlchemy ORM (`app/models/`)
              ↓
        MySQL Database
```

---

## 2. Directory Structure

```text
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                     # FastAPI entrypoint, middleware, routes
│   │
│   ├── core/                       # Core configuration, security & exceptions
│   │   ├── __init__.py
│   │   ├── config.py               # Pydantic v2 BaseSettings
│   │   ├── security.py             # Bcrypt hashing & PyJWT tokens
│   │   └── exceptions.py           # Standardized error handling
│   │
│   ├── database/                   # Database engine & session management
│   │   ├── __init__.py
│   │   ├── base.py                 # SQLAlchemy DeclarativeBase
│   │   └── session.py              # Engine & get_db dependency
│   │
│   ├── models/                     # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   └── user.py                 # User model & UserRole enum
│   │
│   ├── schemas/                    # Pydantic validation & response schemas
│   │   ├── __init__.py
│   │   └── auth.py                 # Registration, login & user schemas
│   │
│   ├── repositories/               # Data access layer
│   │   ├── __init__.py
│   │   └── user_repository.py      # User entity queries
│   │
│   ├── services/                   # Business logic layer
│   │   ├── __init__.py
│   │   └── auth_service.py         # Authentication & user workflows
│   │
│   ├── routers/                    # API v1 endpoints
│   │   ├── __init__.py
│   │   ├── health.py               # GET /api/v1/health
│   │   └── auth.py                 # /api/v1/auth endpoints
│   │
│   └── dependencies/               # Reusable FastAPI dependencies
│       ├── __init__.py
│       └── auth.py                 # get_current_user & require_role
│
├── tests/                          # Pytest test suite
│   ├── __init__.py
│   ├── conftest.py                 # Isolated test database fixture
│   ├── test_health.py              # Health check test
│   └── test_auth.py                # Registration & JWT auth tests
│
├── alembic/                        # Database migration system
│   ├── versions/                   # Migration revision scripts
│   ├── env.py                      # Alembic migration environment
│   └── script.py.mako              # Revision template
│
├── alembic.ini                     # Alembic configuration
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment template
└── README.md                       # Backend documentation
```

---

## 3. Prerequisites

* **Python 3.12+**
* **MySQL 8.0+**
* **Virtualenv** (`venv`)

---

## 4. Environment Configuration

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Key environment variables:

```env
APP_NAME=SKILL2CAREER
APP_ENV=development
DEBUG=true

DATABASE_URL=mysql+pymysql://root:password@localhost:3306/skill2career

JWT_SECRET_KEY=change_this_in_production_super_secret_key_minimum_32_characters
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

FRONTEND_URL=http://localhost:5173
ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

---

## 5. Setup & Installation

### Create & activate virtual environment

```bash
# Windows (PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### Install dependencies

```bash
pip install -r requirements.txt
```

---

## 6. Database Migrations (Alembic)

Ensure your MySQL server is running and database `skill2career` is created:

```sql
CREATE DATABASE IF NOT EXISTS skill2career CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Run migrations:

```bash
# Apply migrations to latest revision
alembic upgrade head

# Generate a new migration revision
alembic revision --autogenerate -m "describe_changes"

# Rollback one migration
alembic downgrade -1
```

---

## 7. Running the Application

Start the development server with Uvicorn:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

* **Interactive OpenAPI Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
* **ReDoc Docs:** [http://localhost:8000/redoc](http://localhost:8000/redoc)
* **Health Check:** [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)

---

## 8. Running Tests

Run the test suite with Pytest:

```bash
pytest -v
```

The tests run in-memory and execute cleanly without requiring external databases.

---

## 9. Current API Endpoints

| Method | Endpoint | Description | Auth Required | Roles |
|---|---|---|---|---|
| `GET` | `/` | Service metadata & links | No | Any |
| `GET` | `/api/v1/health` | Health check endpoint | No | Any |
| `POST` | `/api/v1/auth/register` | Register new user | No | Any |
| `POST` | `/api/v1/auth/login` | Login and get JWT token | No | Any |
| `GET` | `/api/v1/auth/me` | Current user profile | Yes (Bearer) | Any authenticated |

---

## 10. Role Authorization Usage

To protect future endpoints by role in sprint tickets, simply use the `require_role` dependency:

```python
from app.dependencies.auth import require_role
from app.models.user import UserRole, User

@router.get("/company/jobs")
def get_company_jobs(
    current_user: User = Depends(require_role(UserRole.COMPANY, UserRole.ADMIN))
):
    ...
```
