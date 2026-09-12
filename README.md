# 📚 Study Companion

**Study Companion** is an AI-powered academic workspace platform designed to organize course study materials, extract multi-unit concept syllabi, visualize prerequisite pathways, and generate exam-oriented learning resources.

---

## ✨ Features & System Capabilities

### 🔐 1. Authentication & Workspace Isolation
- **User Authentication**: Registration, Login, and JWT Token-based session management.
- **Subject-Based Workspaces**: Organize study materials by course/subject (e.g., *Operating Systems*, *Computer Networks*, *IoT*, *Machine Learning*).
- **Contextual Isolation**: Each workspace maintains isolated documents, concept graphs, chat history, and generated revision outputs.

---

### 📑 2. Document Processing & Portion Feeding
- **Supported File Types**: Upload PDF (`.pdf`), Word (`.docx`), and Text (`.txt`) study materials.
- **Portion Text Feeding**: Append specific unit text or question banks directly using the `+ Feed Portion` interface.
- **Automatic Text Extraction**: Uses `pypdf`, `pdfplumber`, and `python-docx` text extraction pipelines.

---

### 🗺️ 3. Concept Syllabus & Multi-Unit Graph pathways
- **Multi-Unit Scanning Engine**: Automatically detects and splits multi-unit Question Banks and course files (`Unit 1` to `Unit 5` / `UNIT-I` to `UNIT-V`).
- **Clickable Unit Tabs**: Filter concepts by unit tabs (e.g. `All Units`, `📁 Unit 1 (15)`, `📁 Unit 2 (16)`...) with concept counts.
- **Gated Learning DAG**: Topological prerequisite graph mapping locked, unlocked, and mastered concept states.
- **Mastery Gated Checks**:
  - **MCQ Practice Quizzes**: 3-question mini-quizzes per topic.
  - **Active Recall Explain-Back**: Interactive student explanations graded by AI with score and feedback.
- **Clear Feed Action**: Trash bin action to reset/re-feed workspace syllabi.

---

### 📜 4. Concept Syllabus PDF Export Report
- **Overall Unit-Wise Export**: Generate and download a PDF report containing:
  - **Executive Progress Summary**: Learned vs. left to do concept counts and percentages.
  - **Status Breakdown**: Clear lists of mastered, in-progress, and locked topics.
  - **Unit-Wise Question & Reference Answer Guide**: Formatted reference study guide grouped strictly unit-by-unit.

---

### 🤖 5. Academic AI Copilot & Logic Flows
- **Workspace-Aware Chat**: Ask questions grounded in uploaded study material context.
- **Logic Flow & Mind Maps**: Visual step-by-step process flows for complex algorithms and architectures.
- **JSON Auto-Repair**: Engine to handle truncated or unescaped AI JSON responses.

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| **Frontend** | React 18, Vite, Lucide Icons, Vanilla CSS |
| **Backend** | Python 3.11, FastAPI, Uvicorn |
| **Database** | PostgreSQL / SQLite (SQLAlchemy ORM) |
| **AI Models** | Gemini API & Groq LLM API |
| **PDF Report Generation** | ReportLab |
| **Document Processing** | PyPDF, pdfplumber, python-docx |

---

## 🚀 Getting Started

### Prerequisites
- **Python**: `3.11` (recommended)
- **Node.js**: `18+`
- **PostgreSQL**: (or SQLite for development)

---

### 1️⃣ Clone Repository
```bash
git clone <repository-url>
cd mini-project
```

---

### 2️⃣ Backend Setup
```bash
cd backend

# Create Virtual Environment
python -m venv venv

# Activate Virtual Environment
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Mac/Linux:
source venv/bin/activate

# Install Dependencies
pip install -r requirements.txt

# Configure Environment Variables (.env)
cp .env.example .env
```

**Configure `.env`**:
```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/MiniProject
JWT_SECRET_KEY=your_secret_key
JWT_EXPIRE_MINUTES=1440
GEMINI_API_KEY=your_gemini_api_key
```

**Run Backend Server**:
```bash
uvicorn app.main:app --reload
```
- API Base URL: `http://localhost:8000`
- Swagger UI Docs: `http://localhost:8000/docs`

---

### 3️⃣ Frontend Setup
Open a new terminal window:
```bash
cd frontend

# Install Dependencies
npm install

# Configure Environment Variables (.env)
cp .env.example .env
```

**Configure `frontend/.env`**:
```env
VITE_API_URL=http://localhost:8000
```

**Run Frontend Dev Server**:
```bash
npm run dev
```
- Frontend Application: `http://localhost:5173`

---

## 📁 Project Structure

```
mini-project/
├── backend/
│   ├── app/
│   │   ├── models/        # SQLAlchemy Models (User, Workspace, ConceptNode...)
│   │   ├── routes/        # FastAPI API Endpoints (Auth, Graph, Content, Chat)
│   │   ├── schemas/       # Pydantic Input/Output Schemas
│   │   ├── services/      # Business Logic (Graph, Gemini, PDF Export, Content)
│   │   ├── database.py    # DB Connection Setup
│   │   └── main.py        # FastAPI Application Entry
│   ├── uploads/           # Permanent Upload Storage
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── api.js         # Axios API Client & Services
│   │   ├── components/   # React Components (AnimatedRoadmap, ConceptGraphPanel...)
│   │   ├── styles/        # CSS Design System
│   │   └── App.jsx        # Main Layout & Workspace Routing
│   └── package.json
│
├── project-architecture.md # Technical Architecture Document
└── README.md
```
