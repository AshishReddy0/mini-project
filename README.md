# Study Companion

AI-powered academic workspace for organizing study materials by subject.

## Phase 2 — Current Status

Backend (FastAPI), database (PostgreSQL), and a minimal React frontend are set up.

- Authentication (register, login, JWT)
- Workspace CRUD
- PDF document upload (metadata stored; text extraction in Phase 3)
- Chat & content APIs (placeholder responses until Phase 3)

---

## Prerequisites

Install these before starting:

| Tool | Version | Check with |
|---|---|---|
| Python | **3.11** (required) | `py -3.11 --version` |
| Node.js | 18+ | `node --version` |
| PostgreSQL | any recent | running via pgAdmin or Windows service |
| npm | comes with Node | `npm --version` |

> **Important:** Use Python 3.11 for the backend. Python 3.14 may fail to install `psycopg2-binary` and `pydantic-core`.

---

## Step 1 — PostgreSQL Database Setup

### 1.1 Start PostgreSQL

Make sure PostgreSQL is running (pgAdmin or Windows Services).

### 1.2 Create the database (one time only)

Open **pgAdmin → Query Tool** (or any SQL client) and run:

```sql
CREATE DATABASE "MiniProject";
```

If the database already exists, skip this step.

### 1.3 Project database settings

| Variable | Value |
|---|---|
| `DB_USER` | `postgres` |
| `DB_HOST` | `localhost` |
| `DB_NAME` | `MiniProject` |
| `DB_PASSWORD` | your pgAdmin password |

Tables are created automatically when the backend starts — no manual SQL migrations needed in Phase 2.

---

## Step 2 — Backend Setup

Open a terminal in the project root, then:

### 2.1 Go to the backend folder

```powershell
cd mini-project\backend
```

### 2.2 Create and activate a virtual environment

```powershell
py -3.11 -m venv venv
venv\Scripts\activate
```

You should see `(venv)` at the start of your terminal prompt.

### 2.3 Install Python dependencies

```powershell
pip install -r requirements.txt
```

### 2.4 Configure environment variables

A `backend/.env` file should already exist. If not, create it from the example:

```powershell
copy .env.example .env
```

Edit `backend/.env` and set your database connection:

```env
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/MiniProject
JWT_SECRET_KEY=study-companion-local-dev-secret-change-in-production
JWT_EXPIRE_MINUTES=1440
```

**Password special characters:** If your password contains `@`, `#`, or `%`, URL-encode them in `DATABASE_URL`.

| Character in password | Use in URL |
|---|---|
| `@` | `%40` |
| `#` | `%23` |
| `%` | `%25` |

Example: password `Rise@-1` → `Rise%40-1`

```env
DATABASE_URL=postgresql://postgres:Rise%40-1@localhost:5432/MiniProject
```

### 2.5 Start the backend server

```powershell
uvicorn app.main:app --reload
```

Expected output:

```text
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

**Verify backend:**

| URL | Expected result |
|---|---|
| http://localhost:8000/health | `{ "status": "ok" }` |
| http://localhost:8000/health/db | `{ "status": "ok", "database": "connected" }` |
| http://localhost:8000/docs | Swagger API documentation |

If `/health/db` shows `"database": "disconnected"`:

1. Confirm PostgreSQL is running
2. Confirm database `MiniProject` exists
3. Check `DATABASE_URL` username, password (URL-encoded), and database name in `.env`
4. Restart the backend after changing `.env`

---

## Step 3 — Frontend Setup

Open a **second terminal** (keep the backend running in the first).

### 3.1 Go to the frontend folder

```powershell
cd mini-project\frontend
```

### 3.2 Install dependencies

```powershell
npm install
```

### 3.3 Configure environment variables

A `frontend/.env` file should already exist. If not:

```powershell
copy .env.example .env
```

Contents:

```env
VITE_API_URL=http://localhost:8000
```

### 3.4 Start the frontend dev server

```powershell
npm run dev
```

Open: **http://localhost:5173**

---

## Step 4 — Quick Smoke Test (Browser)

With both servers running:

1. Open http://localhost:5173
2. Check **System Status** — API should show `ok`, Database should show `connected`
3. Click **Register** — create an account (name, email, password)
4. **Login** with the same credentials
5. Create a workspace (e.g. `Operating Systems`)
6. Click **Refresh Workspaces** — your workspace should appear

### Optional — test via Swagger

1. Open http://localhost:8000/docs
2. `POST /auth/register` → create a user
3. `POST /auth/login` → copy the `access_token`
4. Click **Authorize** (top right) → paste `Bearer <your-token>`
5. Try `POST /workspaces`, upload a PDF via `POST /workspaces/{id}/documents`, etc.

---

## Step 5 — Run Backend Tests

In the backend terminal (with venv activated):

```powershell
cd mini-project\backend
venv\Scripts\activate
pytest
```

Expected: **2 passed** (`test_health_endpoint`, `test_health_db_endpoint`)

---

## Daily Development — Quick Start

After the first-time setup, you only need two terminals:

**Terminal 1 — Backend:**

```powershell
cd mini-project\backend
venv\Scripts\activate
uvicorn app.main:app --reload
```

**Terminal 2 — Frontend:**

```powershell
cd mini-project\frontend
npm run dev
```

---

## Project Structure (short)

```text
mini-project/
├── backend/          # FastAPI + PostgreSQL
│   ├── app/          # application code
│   ├── uploads/      # uploaded PDF files (created at runtime)
│   ├── .env          # local secrets (do not commit)
│   └── requirements.txt
└── frontend/         # React + Vite
    ├── src/
    └── .env
```

---

## Troubleshooting

| Problem | Solution |
|---|---|
| `ModuleNotFoundError: No module named 'app'` | Run `uvicorn` from the `backend/` folder, not project root |
| `database: disconnected` | Check PostgreSQL is running, `MiniProject` DB exists, `.env` password is URL-encoded |
| `pip install` fails on psycopg2 | Use `py -3.11 -m venv venv`, not Python 3.14 |
| Frontend shows API `unreachable` | Start backend first on port 8000 |
| CORS errors in browser | Backend allows `localhost:5173` — use that URL, not a different port |
| `Email is already registered` | User exists — use Login instead |
| Upload fails | Only PDF files, max 10 MB |

---

## What Comes Next (Phase 3)

- PDF text extraction (PyPDF2 + pdfplumber)
- Gemini API integration
- Real revision, exam, quiz, and chat responses
