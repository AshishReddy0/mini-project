import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT

def create_technical_code_pdf(filename):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    # Color palette tailored for technical code reference
    primary_color = colors.HexColor('#0f172a')   # Deep Slate
    accent_color = colors.HexColor('#2563eb')    # Blue Accent
    teal_color = colors.HexColor('#0d9488')      # Teal Accent
    purple_color = colors.HexColor('#7c3aed')    # Purple Accent
    code_bg = colors.HexColor('#1e293b')         # Dark Code Background
    code_text = colors.HexColor('#f8fafc')       # Light Code Text
    body_text = colors.HexColor('#334155')       # Body Slate
    box_bg = colors.HexColor('#f8fafc')          # Light Box
    border_col = colors.HexColor('#cbd5e1')      # Border Gray

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=22,
        leading=26,
        textColor=primary_color,
        alignment=TA_CENTER,
        spaceAfter=4
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        leading=15,
        textColor=accent_color,
        alignment=TA_CENTER,
        spaceAfter=12
    )

    h1_style = ParagraphStyle(
        'H1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13.5,
        leading=17,
        textColor=primary_color,
        spaceBefore=12,
        spaceAfter=5,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'H2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14.5,
        textColor=teal_color,
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.8,
        leading=12.5,
        textColor=body_text,
        spaceAfter=5
    )

    bullet_style = ParagraphStyle(
        'Bullet',
        parent=body_style,
        leftIndent=10,
        firstLineIndent=-6,
        spaceAfter=3
    )

    code_style = ParagraphStyle(
        'CodeSnippet',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=7.8,
        leading=10,
        textColor=code_text,
        backColor=code_bg,
        borderColor=border_col,
        borderWidth=0.5,
        borderPadding=6,
        spaceBefore=4,
        spaceAfter=6,
        borderRadius=4
    )

    box_style = ParagraphStyle(
        'TechBox',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=primary_color,
        backColor=box_bg,
        borderColor=border_col,
        borderWidth=0.5,
        borderPadding=5,
        spaceBefore=3,
        spaceAfter=6,
        borderRadius=4
    )

    story = []

    # Title & Header
    story.append(Paragraph("Study Companion — Technical Code & Technology Reference Manual", title_style))
    story.append(Paragraph("Deep-Dive Guide: Technologies, Frameworks, Code Implementation & Architecture Interconnections", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=accent_color, spaceBefore=0, spaceAfter=10))

    # SECTION 1: THE FULL TECHNOLOGY STACK
    story.append(Paragraph("1. Technology Stack Breakdown & System Roles", h1_style))
    story.append(Paragraph(
        "Study Companion is built as a modern, decoupled 3-tier web application. Every technology component has been "
        "specifically chosen to ensure asynchronous non-blocking performance, strong type safety, strict subject isolation, "
        "and seamless real-time user interaction.",
        body_style
    ))

    tech_overview = [
        ("1. React 18 (Frontend Framework)",
         "What it is: A declarative, component-based JavaScript UI library for building interactive Single Page Applications (SPAs).<br/>"
         "How we use it: Used to construct modular components like App.jsx, TabManager.jsx, ConceptGraphPanel.jsx, AnimatedRoadmap.jsx, and LogicFlowPanel.jsx. Manages state via useState, useEffect, and useRef without full-page reloads."),

        ("2. Node.js & npm (Runtime & Package Manager)",
         "What it is: Node.js is a server-side JavaScript engine; npm is its package manager.<br/>"
         "How we use it: Used during development to execute Vite development server (npm run dev), manage dependencies (axios, lucide-react, react-dom), and bundle production static assets."),

        ("3. FastAPI & Uvicorn (Backend Web Framework & ASGI Server)",
         "What it is: FastAPI is a high-performance Python 3.11 web framework built on Starlette and Pydantic. Uvicorn is an Asynchronous Server Gateway Interface (ASGI) web server.<br/>"
         "How we use it: Powers all backend HTTP REST endpoints (/auth, /workspaces, /documents, /graph, /content, /chat). Executes non-blocking async handlers and enforces strict input/output Pydantic schema validation."),

        ("4. PostgreSQL & SQLAlchemy 2.0 (Relational DB & ORM)",
         "What it is: PostgreSQL is an enterprise object-relational database. SQLAlchemy is Python's premier Object-Relational Mapper (ORM).<br/>"
         "How we use it: Persists relational data models (User, Workspace, Document, ExtractedText, ConceptNode, ConceptEdge, NodeMastery, ChatHistory). Uses JSONB columns for flexible non-relational node attributes and reference answer caching."),

        ("5. JSON (JavaScript Object Notation)",
         "What it is: A lightweight data-interchange text format.<br/>"
         "How we use it: Acts as the primary data exchange language across all system boundaries: HTTP REST requests/responses between React & FastAPI, structured prompt inputs/outputs for Gemini LLM, and JSONB columns in PostgreSQL."),

        ("6. Google Gemini API (gemini-2.5-flash LLM)",
         "What it is: A state-of-the-art multimodal AI model provided by Google DeepMind.<br/>"
         "How we use it: Performs multi-unit syllabus extraction, reference answer generation, MCQ quiz creation, AI Explain-Back active recall grading (0-100 score), and workspace-aware copilot chat answers."),

        ("7. JWT Authentication & bcrypt (Security Layer)",
         "What it is: PyJWT provides JSON Web Token encoding/decoding; Passlib provides bcrypt password hashing.<br/>"
         "How we use it: Hashes user passwords during signup, issues signed HS256 Bearer tokens upon login, and validates user authentication on every protected API route via FastAPI's Depends(get_current_user).")
    ]

    for title, desc in tech_overview:
        story.append(Paragraph(f"<b>{title}</b>", h2_style))
        story.append(Paragraph(desc, box_style))

    story.append(Spacer(1, 6))

    # SECTION 2: TECHNOLOGY INTERCONNECTION & DATA FLOW
    story.append(Paragraph("2. System Interconnections & Data Flow Architecture", h1_style))
    story.append(Paragraph(
        "The diagram below illustrates how raw user input flows from the React SPA frontend, through FastAPI middleware and controllers, "
        "to PostgreSQL and the Gemini API, and back as JSON data to render reactive UI updates:",
        body_style
    ))

    architecture_ascii = (
        "+---------------------------------------------------------------------------------------------------+\n"
        "|                                     REACT 18 FRONTEND SPA (Vite)                                  |\n"
        "|  App.jsx  <--->  TabManager  <--->  ConceptGraphPanel  <--->  AnimatedRoadmap  <--->  api.js       |\n"
        "+---------------------------------------------------+-----------------------------------------------+ \n"
        "                                                    | Axios HTTP Requests (JSON + JWT Authorization)\n"
        "                                                    v\n"
        "+---------------------------------------------------------------------------------------------------+\n"
        "|                                       FASTAPI ASGI BACKEND (Uvicorn)                              |\n"
        "|  Middleware: CORSMiddleware  |  Security: PyJWT Bearer Auth  |  Validation: Pydantic Schemas     |\n"
        "|  Routes:     auth.py  |  workspaces.py  |  documents.py  |  graph.py  |  content.py  |  chat.py   |\n"
        "|  Services:   graph_service.py  |  content_service.py  |  chat_service.py  |  gemini_service.py   |\n"
        "+-------------------------+-------------------------------------------------+-----------------------+\n"
        "                          | SQLAlchemy ORM 2.0                              | HTTP REST Calls (API Key)\n"
        "                          v                                                 v\n"
        "+---------------------------------------------------+  +--------------------------------------------+\n"
        "|                POSTGRESQL DATABASE                |  |             GOOGLE GEMINI API              |\n"
        "|  Tables: users, workspaces, documents,            |  |          Model: gemini-2.5-flash           |\n"
        "|  extracted_text, concept_nodes, concept_edges,    |  |  Generates: Unit Syllabus, JSON Graph,     |\n"
        "|  node_mastery, generated_content, chat_history    |  |  Reference Answers, Explain-Back Grading   |\n"
        "+---------------------------------------------------+  +--------------------------------------------+"
    )
    story.append(Paragraph(architecture_ascii.replace('\n', '<br/>').replace(' ', '&nbsp;'), code_style))

    story.append(Spacer(1, 6))

    # SECTION 3: CODE IMPLEMENTATION DEEP DIVE
    story.append(Paragraph("3. Deep-Dive Code Implementation & Annotations", h1_style))

    story.append(Paragraph("A. Database Models — SQLAlchemy ORM (backend/app/models/concept_graph.py)", h2_style))
    story.append(Paragraph("This file defines the relational tables for Concept Nodes, Prerequisites Edges, and Mastery States:", body_style))

    code_orm = (
        "import uuid\n"
        "from sqlalchemy import Column, String, Text, ForeignKey, Table, Integer, DateTime\n"
        "from sqlalchemy.dialects.postgresql import UUID, JSONB\n"
        "from sqlalchemy.orm import relationship\n"
        "from app.database import Base\n\n"
        "class ConceptNode(Base):\n"
        "    __tablename__ = 'concept_nodes'\n\n"
        "    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)\n"
        "    workspace_id = Column(UUID(as_uuid=True), ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=False)\n"
        "    title = Column(String(255), nullable=False)\n"
        "    unit = Column(String(50), nullable=True, default='Unit 1')\n"
        "    summary = Column(Text, nullable=True)\n"
        "    sub_points = Column(JSONB, nullable=True) # JSON array of topic bullets\n"
        "    answer_cache = Column(Text, nullable=True) # Caches AI generated markdown answer\n\n"
        "    workspace = relationship('Workspace', back_populates='concept_nodes')\n"
        "    mastery = relationship('NodeMastery', back_populates='node', uselist=False, cascade='all, delete-orphan')\n"
        "    prerequisites = relationship('ConceptNode', secondary='concept_edges',\n"
        "                                 primaryjoin='ConceptNode.id==ConceptEdge.node_id',\n"
        "                                 secondaryjoin='ConceptNode.id==ConceptEdge.prerequisite_id')"
    )
    story.append(Paragraph(code_orm.replace('\n', '<br/>').replace(' ', '&nbsp;'), code_style))

    story.append(Spacer(1, 6))

    story.append(Paragraph("B. DFS Cycle Resolution Algorithm (backend/app/services/graph_service.py)", h2_style))
    story.append(Paragraph("Ensures AI-generated prerequisite links never form circular loops, enforcing a strict Directed Acyclic Graph (DAG):", body_style))

    code_dfs = (
        "def detect_and_resolve_cycles(nodes_dict, edges_list):\n"
        "    \"\"\"\n"
        "    Runs Depth-First Search (DFS) back-edge detection.\n"
        "    Strips out any back-edges pointing to nodes in current recursion stack.\n"
        "    \"\"\"\n"
        "    adj = {n_id: [] for n_id in nodes_dict}\n"
        "    for src, dst in edges_list:\n"
        "        if src in adj:\n"
        "            adj[src].append(dst)\n\n"
        "    visited = set()\n"
        "    rec_stack = set()\n"
        "    clean_edges = []\n\n"
        "    def dfs(u):\n"
        "        visited.add(u)\n"
        "        rec_stack.add(u)\n"
        "        for v in adj.get(u, []):\n"
        "            if v in rec_stack:\n"
        "                # Back-edge detected! Skip this edge to break the cycle\n"
        "                continue\n"
        "            clean_edges.append((u, v))\n"
        "            if v not in visited:\n"
        "                dfs(v)\n"
        "        rec_stack.remove(u)\n\n"
        "    for node_id in nodes_dict:\n"
        "        if node_id not in visited:\n"
        "            dfs(node_id)\n"
        "    return clean_edges"
    )
    story.append(Paragraph(code_dfs.replace('\n', '<br/>').replace(' ', '&nbsp;'), code_style))

    story.append(Spacer(1, 6))

    story.append(Paragraph("C. Robust AI JSON Auto-Repair Parser (backend/app/services/gemini_service.py)", h2_style))
    story.append(Paragraph("Handles unescaped quotes, Markdown fences, and truncated JSON responses from the Gemini API:", body_style))

    code_json_repair = (
        "import json, re\n\n"
        "def parse_json_from_ai(text: str) -> dict:\n"
        "    \"\"\"\n"
        "    Multi-tiered JSON repair parser for AI responses.\n"
        "    \"\"\"\n"
        "    # Step 1: Strip Markdown ```json ... ``` code fences\n"
        "    cleaned = re.sub(r'```(?:json)?\\s*(.*?)\\s*```', r'\\1', text, flags=re.DOTALL).strip()\n\n"
        "    # Step 2: Try direct json.loads with strict=False to allow raw control characters\n"
        "    try:\n"
        "        return json.loads(cleaned, strict=False)\n"
        "    except json.JSONDecodeError:\n"
        "        pass\n\n"
        "    # Step 3: Extract outer JSON object / array using regex\n"
        "    match = re.search(r'(\\{.*\\}|\\[.*\\])', cleaned, re.DOTALL)\n"
        "    if match:\n"
        "        try:\n"
        "            return json.loads(match.group(1), strict=False)\n"
        "        except json.JSONDecodeError:\n"
        "            pass\n\n"
        "    # Step 4: Fallback auto-closing brackets if truncated by LLM token limit\n"
        "    open_braces = cleaned.count('{') - cleaned.count('}')\n"
        "    open_brackets = cleaned.count('[') - cleaned.count(']')\n"
        "    repaired = cleaned + (']' * open_brackets) + ('}' * open_braces)\n"
        "    return json.loads(repaired, strict=False)"
    )
    story.append(Paragraph(code_json_repair.replace('\n', '<br/>').replace(' ', '&nbsp;'), code_style))

    story.append(Spacer(1, 6))

    story.append(Paragraph("D. JWT Security & Password Hashing (backend/app/utils/security.py)", h2_style))
    story.append(Paragraph("Handles secure bcrypt password hashing and HS256 JWT access token generation:", body_style))

    code_sec = (
        "import jwt\n"
        "from datetime import datetime, timedelta\n"
        "from passlib.context import CryptContext\n"
        "from app.config import settings\n\n"
        "pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')\n\n"
        "def hash_password(password: str) -> str:\n"
        "    return pwd_context.hash(password)\n\n"
        "def verify_password(plain_password: str, hashed_password: str) -> bool:\n"
        "    return pwd_context.verify(plain_password, hashed_password)\n\n"
        "def create_access_token(data: dict, expires_delta: timedelta = None) -> str:\n"
        "    to_encode = data.copy()\n"
        "    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.JWT_EXPIRE_MINUTES))\n"
        "    to_encode.update({'exp': expire})\n"
        "    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm='HS256')"
    )
    story.append(Paragraph(code_sec.replace('\n', '<br/>').replace(' ', '&nbsp;'), code_style))

    story.append(Spacer(1, 6))

    story.append(Paragraph("E. React API Interceptor & Auth State (frontend/src/api.js)", h2_style))
    story.append(Paragraph("Attaches JWT token to all HTTP requests and provides unified error handling:", body_style))

    code_api = (
        "import axios from 'axios';\n\n"
        "const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';\n"
        "let authToken = localStorage.getItem('token');\n\n"
        "export function setToken(token) {\n"
        "  authToken = token;\n"
        "  if (token) localStorage.setItem('token', token);\n"
        "  else localStorage.removeItem('token');\n"
        "}\n\n"
        "async function request(endpoint, options = {}) {\n"
        "  const headers = { 'Content-Type': 'application/json', ...options.headers };\n"
        "  if (authToken) headers['Authorization'] = `Bearer ${authToken}`;\n"
        "  const res = await fetch(`${API_BASE}${endpoint}`, { ...options, headers });\n"
        "  if (!res.ok) {\n"
        "    const err = await res.json().catch(() => ({}));\n"
        "    throw new Error(err.detail || 'API Request Failed');\n"
        "  }\n"
        "  return res.json();\n"
        "}"
    )
    story.append(Paragraph(code_api.replace('\n', '<br/>').replace(' ', '&nbsp;'), code_style))

    story.append(Spacer(1, 6))

    # SECTION 4: FULL TECH RELATIONSHIP MATRIX
    story.append(Paragraph("4. Technology Interconnection Matrix", h1_style))

    matrix_data = [
        [Paragraph("<b>Technology</b>", body_style), Paragraph("<b>Layer & Role</b>", body_style), Paragraph("<b>Connected Component</b>", body_style), Paragraph("<b>Input / Output Payload</b>", body_style)],
        [Paragraph("React 18", body_style), Paragraph("Frontend SPA UI", body_style), Paragraph("Axios API Client (api.js)", body_style), Paragraph("User clicks $\\rightarrow$ JSON REST payloads", body_style)],
        [Paragraph("FastAPI", body_style), Paragraph("Backend REST Server", body_style), Paragraph("React SPA & PostgreSQL", body_style), Paragraph("HTTP JSON Requests $\\rightarrow$ Pydantic validation", body_style)],
        [Paragraph("SQLAlchemy", body_style), Paragraph("ORM Data Access", body_style), Paragraph("PostgreSQL Database", body_style), Paragraph("Python objects $\\rightarrow$ SQL queries & JSONB", body_style)],
        [Paragraph("Gemini API", body_style), Paragraph("LLM Intelligence", body_style), Paragraph("gemini_service.py", body_style), Paragraph("Document context text $\\rightarrow$ Structured JSON output", body_style)],
        [Paragraph("ReportLab", body_style), Paragraph("PDF Synthesis", body_style), Paragraph("graph.py route", body_style), Paragraph("PostgreSQL nodes $\\rightarrow$ Binary PDF stream", body_style)],
        [Paragraph("PyJWT / bcrypt", body_style), Paragraph("Security Auth", body_style), Paragraph("auth.py & FastAPI Depends", body_style), Paragraph("Password string $\\rightarrow$ HS256 Bearer Token", body_style)]
    ]

    t_matrix = Table(matrix_data, colWidths=[75, 100, 150, 215])
    t_matrix.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f1f5f9')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_matrix)

    doc.build(story)
    print("Technical Code PDF generated successfully at:", filename)

if __name__ == "__main__":
    pdf_path = os.path.join(os.getcwd(), "Study_Companion_Technical_Code_Manual.pdf")
    create_technical_code_pdf(pdf_path)

    # Save copy to artifact directory
    artifact_dir = r"C:\Users\Ashish Reddy\.gemini\antigravity-ide\brain\1a59b9f1-4835-4bed-b1d3-39e274115aa8"
    if os.path.exists(artifact_dir):
        artifact_pdf_path = os.path.join(artifact_dir, "Study_Companion_Technical_Code_Manual.pdf")
        create_technical_code_pdf(artifact_pdf_path)
        print("Artifact copy created at:", artifact_pdf_path)
