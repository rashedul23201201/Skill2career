# SKILL2CAREER

### Bangladesh Job Preparation Ecosystem
**Tagline:** *Learn Today, Get Hired Tomorrow*

[![Python](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19-61DAFB.svg)](https://react.dev/)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-v3-38B2AC.svg)](https://tailwindcss.com/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.x-red.svg)](https://www.sqlalchemy.org/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0%2B-orange.svg)](https://www.mysql.com/)

---

## 1. Project Overview

**SKILL2CAREER** is a comprehensive software engineering platform engineered to bridge Bangladesh's technical higher education output with nationwide and international career opportunities. The platform acts as a unified digital ecosystem connecting:

* **Learners / Job Seekers:** University students and professionals building demonstrable technical competencies.
* **Instructors / Mentors:** Industry practitioners and academic educators publishing courses and administering mock evaluations.
* **Hiring Companies:** Tech enterprises and startups seeking vetted candidates through competency-based recruitment.
* **System Administrators:** Academic institutions and ecosystem moderators ensuring platform integrity.

---

## 2. Key Foundation Features

* **Clean Layered Architecture:** Strict separation between Presentation, API Routing, Business Logic, Data Access, and Persistence.
* **Enterprise Authentication:** Cryptographic password hashing (Bcrypt), signed JWT tokens, and OAuth2 Bearer token flows.
* **Role-Based Access Control (RBAC):** Extensible authorization dependencies supporting `LEARNER`, `INSTRUCTOR`, `COMPANY`, and `ADMIN`.
* **Database Migrations:** Automated database schema versioning using Alembic backed by MySQL.
* **Centralized API Client:** Axios instance with auto-token injection, 401 handling, and unified error format.
* **Persistent Auth Context:** React context provider managing login, registration, and session restoration.
* **Production-Grade Design System:** Tailored Tailwind configuration based on Primary Navy, Emerald, Slate, Amber, and Crimson palettes.
* **Automated Pytest Testing:** Fully isolated test database fixtures for rapid and deterministic test execution.
* **Container Ready:** Dockerfile and Docker Compose orchestration for MySQL and FastAPI services.

---

## 3. Technology Stack

### Backend
* **Language:** Python 3.12+ (tested up to 3.14)
* **Framework:** FastAPI
* **ORM:** SQLAlchemy 2.x
* **Data Validation:** Pydantic v2
* **Database:** MySQL 8.0+
* **Migrations:** Alembic
* **Security:** Bcrypt + PyJWT
* **Server:** Uvicorn
* **Test Runner:** Pytest + HTTPX

### Frontend
* **UI Library:** React 19
* **Build Tool:** Vite
* **Styling:** Tailwind CSS v3
* **Icons:** Lucide React
* **Routing:** React Router v7
* **HTTP Client:** Axios

### Development & Tooling
* **Version Control:** Git & GitHub
* **Orchestration:** Docker & Docker Compose
* **Package Management:** `pip` (Python), `npm` (Node.js)

---

## 4. Architecture

SKILL2CAREER enforces a unidirectional layered architectural pattern:

```text
Presentation Layer (React 19 + Vite + Tailwind CSS)
                       ↓  REST / JSON
       API / Router Layer (`backend/app/routers/`)
                       ↓  Pydantic v2 Schemas
 Business Logic / Service Layer (`backend/app/services/`)
                       ↓  Business Rules & Exceptions
 Data Access / Repository Layer (`backend/app/repositories/`)
                       ↓  Database Queries
             SQLAlchemy 2.x ORM (`backend/app/models/`)
                       ↓  Mapped SQL
                 MySQL 8.0+ Database
```

---

## 5. Repository Structure

```text
SKILL2CAREER/
│
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                     # Application entry point & middleware
│   │   ├── core/                       # Settings, Bcrypt security, exceptions
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   └── exceptions.py
│   │   ├── database/                   # SQLAlchemy engine, session, DeclarativeBase
│   │   │   ├── base.py
│   │   │   └── session.py
│   │   ├── models/                     # Database entities (User, UserRole)
│   │   │   └── user.py
│   │   ├── schemas/                    # Pydantic request/response validation
│   │   │   └── auth.py
│   │   ├── repositories/               # Data access layer
│   │   │   └── user_repository.py
│   │   ├── services/                   # Business logic layer
│   │   │   └── auth_service.py
│   │   ├── routers/                    # API v1 endpoints
│   │   │   ├── health.py
│   │   │   └── auth.py
│   │   └── dependencies/               # Auth & RBAC injection dependencies
│   │       └── auth.py
│   │
│   ├── tests/                          # Automated test suite
│   │   ├── conftest.py                 # Isolated in-memory DB fixture
│   │   ├── test_health.py              # Health check test
│   │   └── test_auth.py                # Registration, login, /me tests
│   │
│   ├── alembic/                        # Migration scripts
│   │   ├── versions/
│   │   └── env.py
│   │
│   ├── alembic.ini
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── .env.example
│   └── README.md
│
├── frontend/
│   ├── src/
│   │   ├── assets/
│   │   ├── components/
│   │   │   ├── common/                 # Navbar, Footer, ProtectedRoute
│   │   │   ├── forms/                  # Button, Input
│   │   │   └── layout/
│   │   ├── pages/                      # Home, Login, Register, Dashboard, NotFound
│   │   ├── layouts/                    # MainLayout
│   │   ├── services/                   # api.js, authService.js
│   │   ├── hooks/                      # useAuth.js
│   │   ├── context/                    # AuthContext.jsx
│   │   ├── routes/                     # AppRoutes.jsx
│   │   ├── constants/                  # Routes, roles, API URL
│   │   ├── utils/                      # Storage & error helpers
│   │   ├── App.jsx
│   │   ├── index.css                   # Tailwind base & typography
│   │   └── main.jsx
│   │
│   ├── package.json
│   ├── tailwind.config.js
│   ├── vite.config.js
│   ├── .env.example
│   └── README.md
│
├── docs/
│   ├── architecture/                   # Architectural designs & layer specs
│   ├── api/                            # OpenAPI endpoint contracts
│   └── development/                    # Git workflow & Agile sprint roadmap
│
├── docker-compose.yml                  # MySQL + Backend local orchestration
├── .gitignore
└── README.md
```

---

## 6. Prerequisites

* **Python:** 3.12 or newer
* **Node.js:** v18 or newer (v20+ recommended)
* **MySQL:** 8.0 or newer (or Docker)
* **Git:** 2.x+

---

## 7. Environment Configuration

### Root & Backend `.env`
Copy `backend/.env.example` to `backend/.env`:

```bash
cp backend/.env.example backend/.env
```

Variables:
```env
APP_NAME=SKILL2CAREER
APP_ENV=development
DEBUG=true

# Database (MySQL)
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/skill2career

# Security & JWT
JWT_SECRET_KEY=change_this_in_production_super_secret_key_minimum_32_characters
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Frontend & CORS
FRONTEND_URL=http://localhost:5173
ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

### Frontend `.env`
Copy `frontend/.env.example` to `frontend/.env`:

```bash
cp frontend/.env.example frontend/.env
```

Variables:
```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

---

## 8. Database Setup & Migrations

Create the database in MySQL:

```sql
CREATE DATABASE IF NOT EXISTS skill2career CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Run Alembic migrations from the `backend/` folder:

```bash
cd backend
alembic upgrade head
```

---

## 9. Running the Project Locally

### Running the Backend

```bash
# 1. From root, navigate to backend
cd backend

# 2. Activate virtual environment
# Windows:
..\.venv\Scripts\Activate.ps1
# Linux/macOS:
source ../.venv/bin/activate

# 3. Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

* API Docs (Swagger): [http://localhost:8000/docs](http://localhost:8000/docs)
* Health Endpoint: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)

### Running the Frontend

```bash
# 1. In a separate terminal, navigate to frontend
cd frontend

# 2. Start Vite dev server
npm run dev
```

* Web App: [http://localhost:5173](http://localhost:5173)

---

## 10. Running Tests

Run the backend Pytest test suite:

```bash
cd backend
pytest -v
```

All tests execute in-memory with zero external service dependencies.

---

## 11. Docker Deployment (Optional)

To start MySQL and the FastAPI backend using Docker Compose:

```bash
docker-compose up --build -d
```

---

## 12. Team Git Workflow (5 Developers)

1. Branch off `main`: `git checkout -b feature/S2C-<ticket>-<description>`
2. Follow Conventional Commits: `[S2C-101] feat: add course catalog repository`
3. Run `pytest` and `npm run build` locally before opening PRs.
4. Require at least 1 team code review approval before merging to `main`.
5. For migrations, always create a new Alembic version script (`alembic revision --autogenerate`). Never edit applied migrations.
