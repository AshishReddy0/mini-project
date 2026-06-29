## Study Companion

AI-powered academic workspace for organizing study materials, generating revision content, quizzes, exam preparation, and workspace-based learning.

## Project Status
 Completed Features
- Authentication
   User registration, User login and JWT base authentication
- Workspace Management
   Create workspaces and view workspaces
- Document Management
   Upload PDF or DOCX files and store extracted text in the database
- AI Content Generation
   
## Database

Stores:

Users, 
Workspaces, 
Documents, 
Extracted text, 
Generated content, 
Chat history

## Prerequisites

Install these before starting:

| Tool | Version | Check with |
|---|---|---|
| Python | **3.11** (required) | `py -3.11 --version` |
| Node.js | 18+ | `node --version` |
| PostgreSQL | any recent | running via pgAdmin or Windows service |
| npm | comes with Node | `npm --version` |

> **Important:** Use Python 3.11 for the backend. Python 3.14 may fail to install `psycopg2-binary` and `pydantic-core`.

## Step 1 — Clone Repository

- git clone your-fork-repository-url
- cd mini-project

## Step 2 — PostgreSQL Setup

- Start PostgreSQL.
- Create database:
  CREATE DATABASE "MiniProject";

## Step 3 — Backend Setup

1. Go to backend:  cd backend

   - Windows:
     py -3.11 -m venv venv
     venv\Scripts\activate

   - Mac/Linux:
    python3 -m venv venv
    source venv/bin/activate

2. Install dependencies:
   pip install -r requirements.txt
   
3. Configure environment variables:
   A backend/.env file should already exist. If not, create it from the example:
   copy .env.example .env
   

  DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/MiniProject
  JWT_SECRET_KEY=your_secret_key
  JWT_EXPIRE_MINUTES=1440
  GEMINI_API_KEY=your_gemini_api_key

**Password special characters:** If your password contains @, #, or %, URL-encode them in DATABASE_URL. 
| Character in password | Use in URL |
| @ | %40 |
| # | %23 |
| % | %25 | 
Example: password Rise@-1 → Rise%40-1
env
DATABASE_URL=postgresql://postgres:Rise%40-1@localhost:5432/MiniProject

 4. Start backend:
    uvicorn app.main:app --reload

   Backend: http://localhost:8000
   Swagger: http://localhost:8000/docs
   Health: http://localhost:8000/health
           http://localhost:8000/health/db

## Step 4 Frontend Setup

1. Open **second** terminal:
   cd frontend
   
3. Install:
   npm install
   
4. Configure environment variables:
   copy .env.example .env
   Edit:

   VITE_API_URL=http://localhost:8000

5. Start frontend:
   npm run dev

   Frontend: http://localhost:5173

## Project Structure
mini-project/
├── backend/
│   ├── app/
│   ├── uploads/
│   ├── .env.example
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   ├── components/
│   ├── .env.example
│
└── README.md

## How to Use

- Register/Login: 
   Create account and login.

- Create Workspace (example: Operating System): 
  Upload Documents (PDF or DOCX),
  Each document belongs to a workspace.

- Generate Content: 
  Revision Notes, 
  Exam Preparation, 
  Quiz(View score, Review mistakes)
  
- Content History: 
  View previous generated content, 
  Delete old content
  
- Workspace Chat: 
  Ask questions based on uploaded study material, 
  Chat is stored workspace-wise.

## Daily Development

Terminal 1 Backend:
cd backend
venv\Scripts\activate
uvicorn app.main:app --reload

Terminal 2 Frontend:
cd frontend
npm run dev

## Future Improvements

Voice input, 
Flashcards, 
Progress analytics, 
Export notes as PDF, 
Leaderboard, 
Study streak tracking
