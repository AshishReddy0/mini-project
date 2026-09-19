import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT

def create_manual_pdf(filename):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=colors.HexColor('#0f172a'),
        alignment=TA_CENTER,
        spaceAfter=6
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#2563eb'),
        alignment=TA_CENTER,
        spaceAfter=15
    )

    h1_style = ParagraphStyle(
        'H1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=19,
        textColor=colors.HexColor('#1e293b'),
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'H2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#2563eb'),
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor('#334155'),
        spaceAfter=6
    )

    bullet_style = ParagraphStyle(
        'Bullet',
        parent=body_style,
        leftIndent=12,
        firstLineIndent=-8,
        spaceAfter=4
    )

    code_style = ParagraphStyle(
        'CodeBlock',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor('#0f172a'),
        backColor=colors.HexColor('#f1f5f9'),
        borderColor=colors.HexColor('#cbd5e1'),
        borderWidth=0.5,
        borderPadding=6,
        spaceBefore=4,
        spaceAfter=6,
        borderRadius=4
    )

    q_title_style = ParagraphStyle(
        'QTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#1e1b4b'),
        spaceBefore=6,
        spaceAfter=2,
        keepWithNext=True
    )

    a_box_style = ParagraphStyle(
        'ABox',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#1e293b'),
        backColor=colors.HexColor('#eff6ff'),
        borderColor=colors.HexColor('#bfdbfe'),
        borderWidth=0.5,
        borderPadding=6,
        spaceBefore=2,
        spaceAfter=8,
        borderRadius=4
    )

    story = []

    # Title & Header
    story.append(Paragraph("Study Companion — Project Review & Guide Manual", title_style))
    story.append(Paragraph("Comprehensive Technical Reference, System Architecture & Viva Preparation", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#2563eb'), spaceBefore=0, spaceAfter=12))

    # Section 1: Executive Summary
    story.append(Paragraph("1. Executive Summary & Core Value Proposition", h1_style))
    story.append(Paragraph(
        "<b>Study Companion</b> is an AI-powered, subject-isolated academic workspace platform designed to transform "
        "raw study materials (PDFs, DOCX files, text notes) into structured learning resources, active recall quizzes, "
        "interactive knowledge dependency graphs (DAGs), step-by-step logic flow process visualizers, and subject-bounded AI chat assistance.",
        body_style
    ))

    story.append(Paragraph("Key Core Solutions:", h2_style))
    story.append(Paragraph("• <b>Subject Isolation:</b> Dedicated workspaces (e.g., Operating Systems, DWDM) isolate documents and chat history, preventing AI context bleed between unrelated subjects.", bullet_style))
    story.append(Paragraph("• <b>Structured Content Generation:</b> Converts documents into Revision Notes, 2/5/10-mark Solved Exam Guides (with examiner coaching boxes), and Interactive MCQ Quizzes.", bullet_style))
    story.append(Paragraph("• <b>Concept Dependency Graph (DAG):</b> Extracts 8–20 key concepts, enforces strict prerequisites, detects and breaks circular dependencies via Depth-First Search (DFS), and tracks node mastery.", bullet_style))
    story.append(Paragraph("• <b>Active Recall ('Explain-Back') Mode:</b> Evaluates student explanation text against concept summaries, returning an automated score (0–100) and actionable coaching feedback.", bullet_style))
    story.append(Paragraph("• <b>Interactive Logic Flow Simulator:</b> Visualizes technical algorithms and multi-step processes as interactive flowcharts with step-by-step simulation controls.", bullet_style))

    story.append(Spacer(1, 8))

    # Section 2: Technology Stack
    story.append(Paragraph("2. Technology Stack Breakdown", h1_style))
    
    tech_data = [
        [Paragraph("<b>Layer</b>", body_style), Paragraph("<b>Technology</b>", body_style), Paragraph("<b>Role & Purpose in System</b>", body_style)],
        [Paragraph("Frontend UI", body_style), Paragraph("React 18 + Vite", body_style), Paragraph("Fast component-based single-page application with browser-style multi-tab manager.", body_style)],
        [Paragraph("Frontend Styling", body_style), Paragraph("Vanilla CSS (Design System)", body_style), Paragraph("Custom dark/light themes, glassmorphism, dynamic animations, responsive grid/flexbox.", body_style)],
        [Paragraph("Icons", body_style), Paragraph("Lucide React", body_style), Paragraph("Clean vector icons (BookOpen, Map, Send, Lock, CheckCircle).", body_style)],
        [Paragraph("Backend API", body_style), Paragraph("FastAPI (Python 3.11)", body_style), Paragraph("High-performance async web framework with automatic Pydantic validation & OpenAPI docs.", body_style)],
        [Paragraph("ASGI Server", body_style), Paragraph("Uvicorn", body_style), Paragraph("Asynchronous web server running FastAPI on localhost:8000.", body_style)],
        [Paragraph("ORM & Database", body_style), Paragraph("SQLAlchemy 2.0 + PostgreSQL", body_style), Paragraph("Relational data persistence for Users, Workspaces, Documents, Concept Graphs, and Chat.", body_style)],
        [Paragraph("Security & Auth", body_style), Paragraph("PyJWT + Passlib (Bcrypt)", body_style), Paragraph("Password hashing (bcrypt) and stateless JWT Bearer token authentication.", body_style)],
        [Paragraph("Parsers", body_style), Paragraph("PyPDF + python-docx", body_style), Paragraph("Extracting raw plain text from PDF pages and DOCX paragraphs.", body_style)],
        [Paragraph("AI Model", body_style), Paragraph("Google Gemini API<br/>(gemini-2.5-flash)", body_style), Paragraph("LLM integration for Markdown notes, exam answers, JSON graphs, and active recall grading.", body_style)]
    ]

    t_tech = Table(tech_data, colWidths=[85, 115, 340])
    t_tech.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f1f5f9')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor('#0f172a')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_tech)
    story.append(Spacer(1, 10))

    # Section 3: Architecture & Data Flow
    story.append(Paragraph("3. High-Level System Architecture & Flow", h1_style))
    story.append(Paragraph(
        "The application follows a clean 3-tier decoupled architecture:<br/>"
        "1. <b>React SPA Frontend</b> → Communicates via HTTP REST endpoints carrying JWT Bearer authorization.<br/>"
        "2. <b>FastAPI Layered Backend</b> → Request Handlers (Routes) → Business Logic & Algorithms (Services) → Data Schemas (Pydantic/SQLAlchemy).<br/>"
        "3. <b>PostgreSQL Database & Google Gemini API</b> → Dual persistence and intelligence providers.",
        body_style
    ))

    arch_diagram = (
        "+-----------------------------------------------------------------------------------+\n"
        "|                                REACT FRONTEND SPA                                 |\n"
        "|   [WorkspaceSidebar]   |   [TabManager] (Browser Tabs)   |   [AnimatedRoadmap]    |\n"
        "+-----------------------------------------+-----------------------------------------+\n"
        "                                          | HTTP REST (JWT Bearer Auth)\n"
        "                                          v\n"
        "+-----------------------------------------------------------------------------------+\n"
        "|                                 FASTAPI BACKEND                                   |\n"
        "|  Routes:   auth.py | workspaces.py | documents.py | content.py | graph.py        |\n"
        "|  Services: graph_service.py | content_service.py | chat_service.py              |\n"
        "+--------------------+------------------------------------+-------------------------+\n"
        "                     |                                    |\n"
        "                     v                                    v\n"
        "+-------------------------------------+  +------------------------------------------+\n"
        "|         POSTGRESQL DATABASE         |  |             GOOGLE GEMINI API            |\n"
        "|  (Users, Workspaces, Documents,     |  |       Model: gemini-2.5-flash            |\n"
        "|   GeneratedContent, ConceptNodes,   |  |  (Markdown Notes, Solved Exam Guides,    |\n"
        "|   ConceptEdges, NodeMastery, Chat)  |  |   JSON Concept Graph, Active Recall)     |\n"
        "+-------------------------------------+  +------------------------------------------+"
    )
    story.append(Paragraph(arch_diagram.replace('\n', '<br/>').replace(' ', '&nbsp;'), code_style))

    story.append(Spacer(1, 10))

    # Section 4: File Breakdown
    story.append(Paragraph("4. Complete File-by-File Breakdown & Responsibilities", h1_style))

    files_info = [
        ("backend/app/main.py", "FastAPI app setup, CORS middleware configuration, DB auto-init lifespan handler, router inclusions, and static file mounting (/uploads)."),
        ("backend/app/config.py", "Environment variables loader (DATABASE_URL, JWT_SECRET_KEY, GEMINI_API_KEY), storage paths, and upload size/MIME type constraints."),
        ("backend/app/database.py", "SQLAlchemy engine, session factory (get_db dependency), Base model, and safe table schema migrations (_safe_add_column)."),
        ("backend/app/models/concept_graph.py", "Database schemas for ConceptNode (title, summary, sub_points JSONB, answer_cache), ConceptEdge (prerequisites), and NodeMastery (LOCKED/UNLOCKED/MASTERED)."),
        ("backend/app/models/generated_content.py", "GeneratedContent table storing AI outputs (REVISION, EXAM, QUIZ, LOGIC_FLOW) with titles and metadata."),
        ("backend/app/services/graph_service.py", "Core graph algorithms: detect_and_resolve_cycles (DFS DAG builder), generate_concept_graph, evaluate_mastery_states, grade_explanation, and generate_node_answer caching."),
        ("backend/app/services/content_service.py", "Prompt engineering for Revision Guides, Exam Preparation (with Exam Coaching Boxes), MCQ Quizzes, and Logic Flow step JSON."),
        ("backend/app/services/chat_service.py", "Workspace-bounded chat service. Merges document context with active concept focus to generate precise AI answers."),
        ("backend/app/routes/graph.py", "API routes for graph generation (/graph/generate), graph fetch (/graph), node answer (/node/answer), and mastery submission (/attempt)."),
        ("frontend/src/App.jsx", "Root layout component. Manages auth session, dark/light theme, workspace state, browser tab lifecycle, and chat state."),
        ("frontend/src/components/AnimatedRoadmap.jsx", "Interactive roadmap visualizer. Handles portion text selection, format customization, concept node lock status, and progress bar."),
        ("frontend/src/components/LogicFlowPanel.jsx", "Step-by-step flowchart simulator with playback controls (Play, Pause, Step Forward/Back, Speed selector)."),
        ("frontend/src/components/TabManager.jsx", "Center panel with browser tabs. Pins Chat Copilot tab, renders document previews, and node reference answers.")
    ]

    for fname, desc in files_info:
        story.append(Paragraph(f"<b>• {fname}</b>: {desc}", body_style))

    story.append(Spacer(1, 10))

    # Section 5: Viva / Guide Review Q&A
    story.append(Paragraph("5. Viva & Project Review Question & Answer Cheat Sheet", h1_style))

    viva_qa = [
        ("Q1: Why did you choose FastAPI over Flask or Django?",
         "FastAPI is built on modern Python 3.11 asynchronous standards (asyncio) and ASGI (uvicorn), providing performance on par with Node.js and Go. It enforces data validation using Pydantic and automatically generates interactive OpenAPI documentation (/docs)."),

        ("Q2: How do you handle JWT authentication securely?",
         "Upon user login in auth_service.py, a signed JWT token is returned using HS256 encryption. The React client stores the token in local storage and includes it in the Authorization: Bearer header for every request. Routes validate the token using FastAPI's Depends(get_current_user) dependency."),

        ("Q3: How does the AI prevent context confusion between different subjects?",
         "Through Subject-Isolated Workspaces. Every document, chat message, and concept graph is strictly bound to a workspace_id foreign key. When querying Gemini, the backend extracts text exclusively from documents belonging to the active workspace."),

        ("Q4: How do you extract text from uploaded PDF and Word files?",
         "When a document is uploaded in document_service.py, we validate the file extension. For PDFs, we use pypdf.PdfReader to extract text page-by-page. For Word files, python-docx parses paragraphs. The raw text is stored in the ExtractedText table."),

        ("Q5: What happens if Gemini generates a circular dependency in the graph?",
         "In graph_service.py, we run a cycle resolution algorithm (detect_and_resolve_cycles) using Depth-First Search (DFS). If a cycle (A -> B -> C -> A) is detected, the back-edge prerequisite is stripped out, guaranteeing a Directed Acyclic Graph (DAG)."),

        ("Q6: How does the system ensure generated answers don't hallucinate?",
         "In content_service.py and chat_service.py, prompts include strict context-bounding instructions: 'Stay strictly within the context of the provided study materials. If the answer cannot be found, state that clearly.'"),

        ("Q7: How is answer generation optimized for fast response times?",
         "We implement Answer Caching on concept nodes. When a student clicks a concept for the first time, Gemini generates a detailed reference answer which is saved in ConceptNode.answer_cache. Subsequent clicks load instantly from PostgreSQL without calling the Gemini API again.")
    ]

    for q, a in viva_qa:
        story.append(Paragraph(q, q_title_style))
        story.append(Paragraph(a, a_box_style))

    doc.build(story)
    print("PDF build successful:", filename)

if __name__ == "__main__":
    pdf_path = os.path.join(os.getcwd(), "Study_Companion_Project_Guide_Manual.pdf")
    create_manual_pdf(pdf_path)
    
    # Also save to artifact directory
    artifact_dir = r"C:\Users\Ashish Reddy\.gemini\antigravity-ide\brain\75cd5ee9-e50d-412c-a2b5-ad8cb68d0245"
    if os.path.exists(artifact_dir):
        create_manual_pdf(os.path.join(artifact_dir, "Study_Companion_Project_Guide_Manual.pdf"))
