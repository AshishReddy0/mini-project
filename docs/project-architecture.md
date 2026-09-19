# Study Companion - System Architecture & Technical Design

## 1. Executive Summary

**Study Companion** is an AI-powered academic workspace system designed to transform raw course materials, textbooks, and multi-unit Question Banks into structured, unit-classified concept graphs, interactive learning pathways, and exam-focused revision content.

---

## 2. Core System Modules

### 2.1 Workspace & Document Engine
- **Subject Isolation**: Encapsulates study materials, concept graphs, revision histories, and AI chat sessions per academic subject workspace.
- **Document Extractor**: Multi-stage text extraction utilizing `pypdf`, `pdfplumber`, and `python-docx`.
- **Portion Feeding**: Allows students to append specific text portions or multi-unit Question Banks directly to an existing workspace graph.

---

### 2.2 Concept Syllabus & Multi-Pass Unit Engine
- **Unit Chunking Engine**: Detects unit/chapter headings (`Unit 1` to `Unit 5`, `UNIT-I` to `UNIT-V`, `Module 1..5`, etc.) using regex splitting. Executes focused multi-pass extraction calls to ensure **100% question coverage across all units** without hitting LLM output token limits.
- **Unit Normalization (`clean_unit_name`)**: Converts numeric, Roman numeral (`UNIT-I` $\rightarrow$ `Unit 1`), and custom unit strings into standardized unit tags.
- **Unit Tab Filtering**: Provides clickable unit tabs (`All Units`, `📁 Unit 1 (n)`, `📁 Unit 2 (n)`...) with live concept counts.

---

### 2.3 Gated Mastery Learning Pathway (DAG)
- **Topological Dependency Graph**: Models prerequisite relationships between concept nodes.
- **Node Mastery States**:
  - `LOCKED`: Prerequisite concepts are not yet mastered.
  - `UNLOCKED`: Prerequisite concepts are cleared; topic ready to attempt.
  - `MASTERED`: Concept passed via MCQ Quiz ($\ge 2/3$ score) or AI Explain-Back ($\ge 70/100$ score).
- **Mastery Gated Evaluation**: Automatically computes and unlocks downstream dependency nodes upon concept mastery.

---

### 2.4 Concept Syllabus PDF Report Generator
- **Engine**: ReportLab document flowable builder (`SimpleDocTemplate`, `Paragraph`, `Table`, `KeepTogether`).
- **Structure**:
  1. **Executive Progress Stats**: Total concepts, learned/mastered count & percentage, unlocked count, and locked count.
  2. **Learned vs. Left-to-Do Lists**: Quick reference status breakdown.
  3. **Unit-Wise Question & Reference Answer Guide**: Formatted reference study guide grouped strictly unit-by-unit with ReportLab HTML tag formatting (`<b>`, `<font>`).

---

### 2.5 Robust AI JSON Parsing & Auto-Repair
- **`parse_json_from_ai`**: Multi-tiered JSON repair function handling:
  - Markdown fence block stripping (` ```json...``` `).
  - Unescaped newline and control character parsing (`strict=False`).
  - Truncated string closure and bracket balancing (`[`, `{`).
  - Fallback regex object extraction.

---

## 3. Technology Stack

| Layer | Component | Description |
|---|---|---|
| **Frontend** | React 18 & Vite | Component-driven SPA architecture |
| **Styling** | Vanilla CSS | Custom design system with glassmorphism UI |
| **Backend Framework** | FastAPI & Uvicorn | Async REST API service |
| **ORM & Database** | SQLAlchemy & PostgreSQL / SQLite | Data persistence & relational model |
| **AI LLM API** | Gemini API & Groq LLM API | AI extraction, grading, and chat response |
| **PDF Generation** | ReportLab | Programmatic PDF report synthesis |
| **Document Processing** | PyPDF, pdfplumber, python-docx | Text extraction from documents |

---

## 4. Entity Relationship Diagram (Schema Overview)

```
[ User ] (1) ───< (N) [ Workspace ]
                          │
                          ├───< (N) [ Document ] ─── (1) [ ExtractedText ]
                          │
                          ├───< (N) [ ConceptNode ] ───< (N) [ NodeMastery ]
                          │             │
                          │             └───< (N) [ ConceptEdge (Prerequisites) ]
                          │
                          ├───< (N) [ GeneratedContent ]
                          │
                          └───< (N) [ ChatHistory ]
```

---

## 5. End-to-End Multi-Pass Concept Extraction Flow

```
User uploads Question Bank / Portion Text
                 │
                 ▼
Document Extractor (PyPDF / pdfplumber / docx)
                 │
                 ▼
Unit Heading Regex Splitter (UNIT-I, UNIT-II, UNIT-III...)
                 │
  ┌──────────────┼──────────────┬──────────────┬──────────────┐
  ▼              ▼              ▼              ▼              ▼
[Unit 1 Chunk] [Unit 2 Chunk] [Unit 3 Chunk] [Unit 4 Chunk] [Unit 5 Chunk]
  │              │              │              │              │
  └──────────────┴──────────────┼──────────────┴──────────────┘
                                ▼
                       Gemini AI Extraction
                                │
                                ▼
              Unit Normalization (clean_unit_name)
                                │
                                ▼
                   Cycle Detection & DAG Validation
                                │
                                ▼
                Database Persistence & Mastery Sync
                                │
                                ▼
               React Frontend Interactive Unit Tabs
```
