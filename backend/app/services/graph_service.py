import json
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.workspace import Workspace
from app.models.concept_graph import ConceptNode, ConceptEdge, NodeMastery, MasteryStatus
from app.services.gemini_service import generate_content

def clear_workspace_graph(db: Session, workspace_id: UUID):
    """Delete all concept nodes, edges, and masteries for a workspace."""
    db.query(ConceptNode).filter(ConceptNode.workspace_id == workspace_id).delete(synchronize_session=False)
    db.commit()

def parse_json_from_ai(text: str):
    """Clean markdown code blocks, repair truncated or malformed LLM JSON, and parse."""
    cleaned = text.strip()
    if "```json" in cleaned:
        cleaned = cleaned.split("```json")[1].split("```")[0].strip()
    elif "```" in cleaned:
        cleaned = cleaned.split("```")[1].split("```")[0].strip()

    # 1. Try direct parse with strict=False (allows unescaped control chars/newlines in string literals)
    try:
        return json.loads(cleaned, strict=False)
    except Exception:
        pass

    # 2. Extract array [...] or object {...} bounds
    start_bracket = cleaned.find('[')
    start_brace = cleaned.find('{')

    if start_bracket != -1 and (start_brace == -1 or start_bracket < start_brace):
        start_idx = start_bracket
        is_array = True
    elif start_brace != -1:
        start_idx = start_brace
        is_array = False
    else:
        start_idx = 0
        is_array = True

    substring = cleaned[start_idx:].strip()

    try:
        return json.loads(substring, strict=False)
    except Exception:
        pass

    # 3. Handle truncated JSON (unterminated strings or unclosed brackets)
    repaired = substring
    quote_count = 0
    in_escape = False
    for char in repaired:
        if in_escape:
            in_escape = False
        elif char == '\\':
            in_escape = True
        elif char == '"':
            quote_count += 1

    if quote_count % 2 != 0:
        repaired += '"'

    open_brackets = []
    in_str = False
    in_esc = False
    for char in repaired:
        if in_esc:
            in_esc = False
        elif char == '\\':
            in_esc = True
        elif char == '"':
            in_str = not in_str
        elif not in_str:
            if char in ('[', '{'):
                open_brackets.append(char)
            elif char == ']' and open_brackets and open_brackets[-1] == '[':
                open_brackets.pop()
            elif char == '}' and open_brackets and open_brackets[-1] == '{':
                open_brackets.pop()

    for bracket in reversed(open_brackets):
        if bracket == '[':
            repaired += ']'
        elif bracket == '{':
            repaired += '}'

    try:
        return json.loads(repaired, strict=False)
    except Exception:
        pass

    # 4. Fallback: Regex extraction of complete items if it's an array
    if is_array:
        import re
        object_matches = re.findall(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', substring, re.DOTALL)
        parsed_items = []
        for obj_str in object_matches:
            try:
                parsed_items.append(json.loads(obj_str, strict=False))
            except Exception:
                continue
        if parsed_items:
            return parsed_items

    raise ValueError(f"Could not parse JSON response from AI: {text[:150]}...")

def detect_and_resolve_cycles(nodes_data: list) -> list:
    """
    Given a list of concepts with prerequisites, verify that the graph is a DAG.
    If any cycle is found, strip out the back-edge prerequisites to ensure no cycles exist.
    """
    # Build adjacency list: node_title -> list of prereq_titles
    adj = {}
    for node in nodes_data:
        adj[node["title"]] = list(node.get("prerequisites", []))

    visited = {}  # 0=unvisited, 1=visiting, 2=visited
    for title in adj:
        visited[title] = 0

    cycle_edges = set()

    def dfs(u):
        visited[u] = 1  # visiting
        for v in list(adj[u]):
            if v not in adj:
                # Prerequisite node doesn't exist in generated concepts, drop it
                adj[u].remove(v)
                continue
                
            if visited[v] == 1:
                # Cycle detected! Mark edge (u -> v) to be removed.
                # In prerequisite relationship: u depends on v, so the edge is v -> u.
                # To break the cycle, we drop v from u's prerequisites list.
                cycle_edges.add((u, v))
                adj[u].remove(v)
            elif visited[v] == 0:
                dfs(v)
        visited[u] = 2  # visited

    for title in list(adj.keys()):
        if visited[title] == 0:
            dfs(title)

    # Apply resolved prerequisites back to nodes_data
    for node in nodes_data:
        title = node["title"]
        if title in adj:
            node["prerequisites"] = adj[title]

    return nodes_data

ROMAN_TO_NUM = {"i": 1, "ii": 2, "iii": 3, "iv": 4, "v": 5, "vi": 6, "vii": 7, "viii": 8, "ix": 9, "x": 10}

def clean_unit_name(u_str: str | None) -> str:
    if not u_str:
        return "Unit 1"
    import re
    s = str(u_str).strip()

    # 1. Match Roman numerals with optional prefix/delimiters (e.g., UNIT-I, UNIT - II, Unit III, Module-IV, Unit-V)
    match_roman = re.search(r'(?:unit|module|chapter)?\s*[\:\-]?\s*\b([ivx]+)\b', s, re.IGNORECASE)
    if match_roman:
        val = ROMAN_TO_NUM.get(match_roman.group(1).lower())
        if val:
            return f"Unit {val}"

    # 2. Match numeric unit (e.g., Unit 1, Unit-1, Unit: 2, Module 3, Chapter 4)
    match_num = re.search(r'(?:unit|module|chapter)?\s*[\:\-]?\s*(\d+)', s, re.IGNORECASE)
    if match_num:
        return f"Unit {int(match_num.group(1))}"

    # 3. Standalone Roman numeral (e.g., "I", "II", "III", "IV", "V")
    if s.lower() in ROMAN_TO_NUM:
        return f"Unit {ROMAN_TO_NUM[s.lower()]}"

    # 4. Standalone number at start
    match_start = re.search(r'^(\d+)', s)
    if match_start:
        return f"Unit {int(match_start.group(1))}"

    cleaned = re.sub(r'[:\-].*$', '', s).strip()
    if not cleaned or cleaned.upper() in ("UNIT", "MODULE", "CHAPTER"):
        return "Unit 1"
    return cleaned

def cleanup_db_workspace_nodes(db: Session, workspace_id: UUID):
    """
    Clean up database concept nodes for a workspace:
    1. Normalize unit_ref strings in DB (e.g. 'Unit 1,3' -> 'Unit 1', 'Unit 2: Intro' -> 'Unit 2').
    2. Remove duplicate concept nodes with identical titles.
    """
    nodes = (
        db.query(ConceptNode)
        .filter(ConceptNode.workspace_id == workspace_id)
        .order_by(ConceptNode.order_hint.asc(), ConceptNode.created_at.asc())
        .all()
    )
    if not nodes:
        return

    seen_titles = set()
    nodes_to_delete = []
    modified = False

    for node in nodes:
        t_clean = node.title.strip().lower()
        if t_clean in seen_titles:
            nodes_to_delete.append(node)
            modified = True
            continue

        seen_titles.add(t_clean)

        c_unit = clean_unit_name(node.unit_ref)
        if node.unit_ref != c_unit:
            node.unit_ref = c_unit
            modified = True

    if nodes_to_delete:
        for dn in nodes_to_delete:
            db.delete(dn)
        modified = True

    if modified:
        db.commit()

def generate_concept_graph(
    db: Session,
    workspace: Workspace,
    document_id: UUID | None = None,
    answer_formats: list | None = None,
    custom_format: str | None = None,
    portion_text: str | None = None,
) -> dict:
    """
    Read workspace text, extract a Concept Graph using Gemini with format instructions,
    and save ConceptNodes, ConceptEdges, and sub_points per node.
    
    answer_formats: list of format keys e.g. ["meaning", "types", "application"]
    custom_format: free-text style instruction applied to every node answer.
    portion_text: user-pasted syllabus/portion text, prepended to document context.
    """
    # 1. Collect context directly from database records with fallbacks
    from app.models.document import Document
    from app.models.extracted_text import ExtractedText

    document_text = ""
    if document_id:
        ext = db.query(ExtractedText).filter(ExtractedText.document_id == document_id).first()
        if ext and ext.content and ext.content.strip():
            document_text = ext.content

    # If document_id text was empty or not specified, aggregate all extracted text in workspace
    if not document_text.strip():
        all_docs = db.query(Document).filter(Document.workspace_id == workspace.id).all()
        doc_ids = [d.id for d in all_docs]
        if doc_ids:
            exts = db.query(ExtractedText).filter(ExtractedText.document_id.in_(doc_ids)).all()
            for e in exts:
                if e.content and e.content.strip():
                    document_text += e.content + "\n"

    # Prepend user-pasted portion text if provided AND store it permanently as a Workspace Document
    if portion_text and portion_text.strip():
        import uuid
        from pathlib import Path

        upload_dir = Path("uploads")
        upload_dir.mkdir(parents=True, exist_ok=True)
        file_path_str = f"uploads/syllabus_portion_{uuid.uuid4().hex[:8]}.txt"
        with open(file_path_str, "w", encoding="utf-8") as f:
            f.write(portion_text.strip())

        existing_portion_docs = [
            d for d in workspace.documents if d.filename.startswith("Syllabus_Portion")
        ]
        doc_name = (
            f"Syllabus_Portion_{len(existing_portion_docs) + 1}.txt"
            if existing_portion_docs
            else "Syllabus_Portion.txt"
        )

        syllabus_doc = Document(
            workspace_id=workspace.id,
            filename=doc_name,
            file_type="txt",
            file_path=file_path_str,
            file_size=len(portion_text.strip().encode("utf-8")),
        )
        db.add(syllabus_doc)
        db.commit()
        db.refresh(syllabus_doc)

        extracted = ExtractedText(
            document_id=syllabus_doc.id,
            content=portion_text.strip(),
        )
        db.add(extracted)
        db.commit()
        db.refresh(workspace)

        document_text = f"[USER-DEFINED PORTION / SYLLABUS]\n{portion_text.strip()}\n\n[REFERENCE MATERIAL]\n{document_text}"

    if not document_text.strip():
        raise ValueError("No readable text found in your uploaded file or syllabus. Please ensure your file contains extractable text or paste your portion text directly.")

    # Collect existing workspace concepts to prevent duplicates
    existing_nodes = db.query(ConceptNode).filter(ConceptNode.workspace_id == workspace.id).all()
    existing_titles = [n.title for n in existing_nodes]
    existing_title_set = {n.title.lower().strip() for n in existing_nodes}

    existing_note = ""
    if existing_titles:
        existing_note = f"\nIMPORTANT DEDUPLICATION RULE: The workspace already contains these concepts: {json.dumps(existing_titles)}. DO NOT extract or duplicate any of these existing concepts. Extract ONLY NEW, additional unique concepts introduced in this portion."

    # Build format instruction block for the prompt
    FORMAT_LABELS = {
        "meaning": "Meaning / Definition",
        "types": "Types",
        "types_meaning": "Types + Meaning",
        "application": "Real-world Application",
        "working": "How it Works / Process",
        "comparison": "Comparison / Difference",
        "advantages": "Advantages & Disadvantages",
        "examples": "Examples",
    }
    format_note = ""
    if answer_formats:
        labels = [FORMAT_LABELS.get(f, f) for f in answer_formats]
        format_note = f"\nIMPORTANT: When generating sub_points and summaries, ensure each concept covers: {', '.join(labels)}."
    if custom_format:
        format_note += f"\nAdditional style instruction: {custom_format}"

    # 2. Check if unit headings are present in the text for multi-pass unit extraction
    import re
    pattern = r'\n(?=(?:UNIT|MODULE|CHAPTER)\s*[\:\-]?\s*[IVX0-9]+\b)'
    raw_chunks = re.split(pattern, document_text, flags=re.IGNORECASE)

    unit_chunks = []
    for chunk in raw_chunks:
        c_str = chunk.strip()
        if not c_str:
            continue
        match = re.search(r'((?:UNIT|MODULE|CHAPTER)\s*[\:\-]?\s*[IVX0-9]+\b)', c_str, re.IGNORECASE)
        if match:
            unit_name = clean_unit_name(match.group(1))
            unit_chunks.append((unit_name, c_str))
        elif len(c_str) > 200:
            unit_chunks.append(("Unit 1", c_str))

    raw_nodes = []
    if len(unit_chunks) > 1:
        # Multi-unit chunked extraction pass: guarantees EVERY unit gets 100% of its questions extracted
        for unit_name, chunk_text in unit_chunks:
            prompt = f"""
            Analyze the following text chunk for {unit_name}:

            {chunk_text}

            EXTRACT EVERY QUESTION / TOPIC: Extract EVERY SINGLE distinct question, numbered item, sub-question (e.g., Short Notes i, ii, iii, iv), and main topic from this text as an individual concept node. DO NOT skip or merge questions!

            For each item, provide:
            - title: The clear question title or topic name as stated in the context
            - summary: A 1-2 sentence core overview or answer summary for this specific question/topic
            - difficulty: "easy", "medium", or "hard"
            - prerequisites: list of concept titles in this unit or previous concepts that MUST be learned before this one
            - unit_ref: MUST be "{unit_name}"
            - sub_points: a list of 2 to 5 sub-topics or key bullet points about this concept.
              Each sub_point must have a "title" (short label) and a "description" (1-2 sentence explanation).
            {format_note}

            Return ONLY a valid JSON array of objects.
            """
            try:
                ai_resp = generate_content(prompt, expect_json=True)
                chunk_nodes = parse_json_from_ai(ai_resp)
                if isinstance(chunk_nodes, list):
                    for n in chunk_nodes:
                        if isinstance(n, dict) and "title" in n:
                            n["unit_ref"] = unit_name
                            raw_nodes.append(n)
            except Exception:
                continue
    else:
        # Single-pass fallback for non-unit-chunked documents
        prompt = f"""
        Analyze the following syllabus, course material, textbook, or Question Bank context:

        {document_text[:120000]}

        CRITICAL EXTRACTION & MULTI-UNIT RULES:
        1. SCAN ALL UNITS: Scan the ENTIRE text from beginning to end across ALL units, modules, or chapters present (e.g. Unit 1, Unit 2, Unit 3, Unit 4, Unit 5, etc.). DO NOT stop after Unit 1!
        2. EXTRACT EVERY QUESTION / TOPIC: Extract EVERY SINGLE distinct question, numbered item, sub-question (e.g., Short Notes i, ii, iii, iv), and main topic from the text as an individual concept node. DO NOT skip, condense, or merge multiple questions into one.
        3. DYNAMIC UNIT MAPPING (unit_ref): For each extracted item, set `unit_ref` to its corresponding unit string found in the text heading (e.g., "Unit 1", "Unit 2", "Unit 3", "Unit 4", "Unit 5", etc.).
        {existing_note}
        
        For each item, provide:
        - title: The clear question title or topic name as stated in the context
        - summary: A 1-2 sentence core overview or answer summary for this specific question/topic
        - difficulty: "easy", "medium", or "hard"
        - prerequisites: list of concept titles in this list that MUST be learned before this one
        - unit_ref: MUST be the clean unit string for the unit/chapter/module to which this item belongs (e.g., "Unit 1", "Unit 2", "Unit 3", "Unit 4", "Unit 5", etc.).
        - sub_points: a list of 2 to 5 sub-topics or key bullet points about this concept.
          Each sub_point must have a "title" (short label) and a "description" (1-2 sentence explanation).
        {format_note}
        Ensure prerequisites point ONLY to other concepts in this list or existing workspace concepts. Avoid circular dependencies.

        Return ONLY a valid JSON array of objects. No markdown, no extra text.
        """
        ai_response = generate_content(prompt, expect_json=True)
        parsed = parse_json_from_ai(ai_response)
        if isinstance(parsed, list):
            raw_nodes = [n for n in parsed if isinstance(n, dict) and "title" in n]

    # Cycle check and cleanup
    clean_nodes = detect_and_resolve_cycles(raw_nodes)

    # Filter out any duplicate nodes that match existing titles
    unique_new_nodes = []
    for node_data in clean_nodes:
        t_clean = node_data["title"].lower().strip()
        if t_clean not in existing_title_set:
            existing_title_set.add(t_clean)
            unique_new_nodes.append(node_data)

    # Save new unique nodes (preserving existing nodes)
    start_order = len(existing_nodes)
    db_nodes = []

    for idx, node_data in enumerate(unique_new_nodes):
        difficulty_val = node_data.get("difficulty", "medium")
        unit_val = clean_unit_name(node_data.get("unit_ref"))
        node = ConceptNode(
            workspace_id=workspace.id,
            title=node_data["title"],
            summary=node_data["summary"],
            difficulty=difficulty_val,
            unit_ref=unit_val,
            order_hint=start_order + idx,
            sub_points=node_data.get("sub_points", []),
            answer_cache=None,
        )
        db.add(node)
        db_nodes.append(node)

    db.commit()

    # Re-fetch all workspace nodes to generate edges
    all_workspace_nodes = db.query(ConceptNode).filter(ConceptNode.workspace_id == workspace.id).all()
    title_to_node_map = {n.title.lower().strip(): n for n in all_workspace_nodes}

    # Save edges for new nodes
    for node_data in unique_new_nodes:
        t_clean = node_data["title"].lower().strip()
        target_node = title_to_node_map.get(t_clean)
        if not target_node:
            continue
        prereqs = node_data.get("prerequisites", [])
        for prereq_title in prereqs:
            source_node = title_to_node_map.get(prereq_title.lower().strip())
            if source_node and source_node.id != target_node.id:
                # Check if edge already exists
                existing_edge = db.query(ConceptEdge).filter(
                    ConceptEdge.from_node_id == source_node.id,
                    ConceptEdge.to_node_id == target_node.id
                ).first()
                if not existing_edge:
                    edge = ConceptEdge(
                        from_node_id=source_node.id,
                        to_node_id=target_node.id
                    )
                    db.add(edge)

    db.commit()

    # Re-evaluate mastery states for the workspace owner
    evaluate_mastery_states(db, workspace.id, workspace.user_id)

    return get_graph_dict(db, workspace.id)


def get_graph_dict(db: Session, workspace_id: UUID) -> dict:
    """Retrieve all nodes, edges, and masteries for a workspace as a plain dict."""
    cleanup_db_workspace_nodes(db, workspace_id)
    nodes = (
        db.query(ConceptNode)
        .filter(ConceptNode.workspace_id == workspace_id)
        .order_by(ConceptNode.order_hint.asc())
        .all()
    )
    node_ids = [n.id for n in nodes]
    edges = db.query(ConceptEdge).filter(ConceptEdge.from_node_id.in_(node_ids)).all()
    masteries = db.query(NodeMastery).filter(NodeMastery.node_id.in_(node_ids)).all()
    mastery_map = {str(m.node_id): m for m in masteries}
    return {
        "nodes": nodes,
        "edges": edges,
        "masteries": mastery_map
    }

def evaluate_mastery_states(db: Session, workspace_id: UUID, user_id: UUID):
    """
    Computes LOCKED, UNLOCKED, or MASTERED statuses for each concept node based on prerequisites.
    Unlocked state is computed when all prereqs are mastered. Starting nodes are unlocked by default.
    """
    nodes = db.query(ConceptNode).filter(ConceptNode.workspace_id == workspace_id).all()
    node_ids = [n.id for n in nodes]

    edges = db.query(ConceptEdge).filter(ConceptEdge.to_node_id.in_(node_ids)).all()

    # Prereq map: to_node_id -> list of from_node_ids
    prereq_map = {node.id: [] for node in nodes}
    for edge in edges:
        prereq_map[edge.to_node_id].append(edge.from_node_id)

    masteries = db.query(NodeMastery).filter(
        NodeMastery.node_id.in_(node_ids),
        NodeMastery.user_id == user_id
    ).all()
    
    mastery_dict = {m.node_id: m for m in masteries}

    for node in nodes:
        mastery = mastery_dict.get(node.id)
        if not mastery:
            mastery = NodeMastery(
                user_id=user_id,
                node_id=node.id,
                status=MasteryStatus.LOCKED.value
            )
            db.add(mastery)
            mastery_dict[node.id] = mastery

        if mastery.status == MasteryStatus.MASTERED.value:
            continue

        required_ids = prereq_map[node.id]
        if not required_ids:
            # No prerequisites -> unlocked
            mastery.status = MasteryStatus.UNLOCKED.value
        else:
            all_prereqs_mastered = True
            for pid in required_ids:
                pm = mastery_dict.get(pid)
                if not pm or pm.status != MasteryStatus.MASTERED.value:
                    all_prereqs_mastered = False
                    break
            
            if all_prereqs_mastered:
                mastery.status = MasteryStatus.UNLOCKED.value
            else:
                mastery.status = MasteryStatus.LOCKED.value

    db.commit()

def grade_explanation(concept_title: str, concept_summary: str, student_explanation: str) -> dict:
    """
    Grade user explanation text against the target concept summary using Gemini.
    """
    prompt = f"""
    You are an expert academic coach grading a student's active-recall answer.
    
    Target Concept: "{concept_title}"
    Target Summary/Core Details: "{concept_summary}"
    
    Student's Explanation:
    "{student_explanation}"
    
    Grade this explanation on a scale of 0 to 100.
    To PASS (score >= 70), the student must accurately capture the main ideas in the concept summary.
    Provide constructive, structured feedback outlining:
    1. What details they got right.
    2. What important details were missing, inaccurate, or could be explained better.
    
    Return ONLY a valid JSON object.
    Do not add markdown code blocks or text outside the JSON.
    
    Format:
    {{
      "passed": true / false,
      "score": 85,
      "feedback": "Your structured coaching feedback here..."
    }}
    """
    
    response_text = generate_content(prompt, expect_json=True)
    return parse_json_from_ai(response_text)

def generate_node_quiz(db: Session, node: ConceptNode) -> list:
    """
    Generates 3 multiple choice questions for a specific concept node context.
    """
    prompt = f"""
    Create a mini-quiz of exactly 3 multiple choice questions based on the following concept summary:
    
    Concept: {node.title}
    Summary: {node.summary}
    
    Return ONLY a valid JSON array of objects.
    Do not add headings or extra text.
    
    Format:
    [
      {{
        "question": "...",
        "options": {{
          "A": "...",
          "B": "...",
          "C": "...",
          "D": "..."
        }},
        "answer": "A"
      }}
    ]
    """
    response_text = generate_content(prompt, expect_json=True)
    return parse_json_from_ai(response_text)


def generate_node_answer(db: Session, node: ConceptNode, workspace: Workspace) -> str:
    """
    Generate a rich Markdown reference answer for a concept node from the workspace source material.
    The result is cached in node.answer_cache so the expensive Gemini call only happens once.
    Returns the Markdown string.
    """
    # Return cached answer if available
    if node.answer_cache:
        return node.answer_cache

    # Collect workspace source text (up to 60k chars to keep prompt manageable)
    document_text = ""
    for doc in workspace.documents:
        if doc.extracted_text:
            document_text += doc.extracted_text.content + "\n"
    document_text = document_text[:60000]

    # Build sub-points context for the prompt
    sub_points_text = ""
    if node.sub_points:
        sub_points_text = "\n".join(
            f"- {sp['title']}: {sp['description']}" for sp in node.sub_points
        )
    else:
        sub_points_text = "(no sub-points available)"

    prompt = f"""
    You are an expert academic tutor. A student is studying the following concept from their reference material.

    Concept: {node.title}
    Summary: {node.summary}

    Key Sub-topics of this concept:
    {sub_points_text}

    Reference Material:
    {document_text}

    Generate a concise, direct, high-yield study reference answer for this concept.

    Structure the response using clean Markdown:
    1. **Core Definition & Overview** — 2-3 concise sentences explaining the concept directly.
    2. **Key Concepts & Working** — bullet points of the main sub-topics and mechanisms (short & focused).
    3. **Quick Exam Points** — 2-3 short bullet points on essential formulas, differences, or exam takeaways.

    IMPORTANT: Keep the response concise, clear, and direct. Avoid unnecessary fluff or overly long paragraphs.
    """

    answer = generate_content(prompt)

    # Cache the answer on the node so future clicks are instant
    node.answer_cache = answer
    db.commit()

    return answer


def generate_syllabus_pdf_bytes(db: Session, workspace: Workspace) -> bytes:
    """
    Generate an overall Concept Syllabus Report PDF bytes.
    Starts with:
    - Executive progress summary: learned vs left to do
    - List of concepts learned & left to do
    - Unit-wise Question & Reference Answer guide for all concepts.
    """
    import io
    import re
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
    )
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT

    # Fetch nodes, masteries
    nodes = (
        db.query(ConceptNode)
        .filter(ConceptNode.workspace_id == workspace.id)
        .order_by(ConceptNode.order_hint.asc())
        .all()
    )
    node_ids = [n.id for n in nodes]
    masteries = db.query(NodeMastery).filter(NodeMastery.node_id.in_(node_ids)).all()
    mastery_map = {m.node_id: m.status for m in masteries}

    total_count = len(nodes)
    mastered_nodes = [n for n in nodes if mastery_map.get(n.id) == "mastered"]
    unlocked_nodes = [n for n in nodes if mastery_map.get(n.id) == "unlocked"]
    locked_nodes = [n for n in nodes if mastery_map.get(n.id) not in ("mastered", "unlocked")]
    mastery_pct = round((len(mastered_nodes) / total_count * 100)) if total_count > 0 else 0

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'SyllabusTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#0f172a'),
        alignment=TA_CENTER,
        spaceAfter=4
    )

    subtitle_style = ParagraphStyle(
        'SyllabusSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10.5,
        leading=14,
        textColor=colors.HexColor('#6366f1'),
        alignment=TA_CENTER,
        spaceAfter=12
    )

    h1_style = ParagraphStyle(
        'SyllabusH1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        textColor=colors.HexColor('#1e293b'),
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'SyllabusBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#334155'),
        spaceAfter=4
    )

    q_title_style = ParagraphStyle(
        'SyllabusQTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#1e1b4b'),
        spaceBefore=8,
        spaceAfter=3,
        keepWithNext=True
    )

    answer_box_style = ParagraphStyle(
        'SyllabusAnswerBox',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor('#1e293b'),
        backColor=colors.HexColor('#f8fafc'),
        borderColor=colors.HexColor('#e2e8f0'),
        borderWidth=0.5,
        borderPadding=6,
        spaceBefore=4,
        spaceAfter=8,
        borderRadius=4
    )

    story = []

    # Title & Subtitle
    ws_title = workspace.name or "Course Workspace"
    story.append(Paragraph(f"{ws_title} — Concept Syllabus & Progress Report", title_style))
    story.append(Paragraph("Comprehensive Subject Knowledge Guide & Mastery Breakdown", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#6366f1'), spaceBefore=0, spaceAfter=10))

    # Executive Summary Stats Table
    summary_data = [
        [
            Paragraph(f"<b>Total Concepts:</b> {total_count}", body_style),
            Paragraph(f"<b>Mastered (Learned):</b> <font color='#10b981'><b>{len(mastered_nodes)} ({mastery_pct}%)</b></font>", body_style),
            Paragraph(f"<b>Unlocked:</b> {len(unlocked_nodes)}", body_style),
            Paragraph(f"<b>Left to Do (Locked):</b> <font color='#ef4444'><b>{len(locked_nodes)}</b></font>", body_style),
        ]
    ]
    t_summary = Table(summary_data, colWidths=[120, 150, 110, 140])
    t_summary.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f1f5f9')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(t_summary)
    story.append(Spacer(1, 8))

    # Learned vs Left to Do Breakdown
    story.append(Paragraph("1. Concepts Progress & Mastery Breakdown", h1_style))
    
    learned_text = "<b>Learned / Mastered Concepts:</b> " + (
        ", ".join([f"✅ {n.title}" for n in mastered_nodes]) if mastered_nodes else "None yet"
    )
    story.append(Paragraph(learned_text, body_style))

    unlocked_text = "<b>Unlocked Concepts (In Progress):</b> " + (
        ", ".join([f"⏳ {n.title}" for n in unlocked_nodes]) if unlocked_nodes else "None"
    )
    story.append(Paragraph(unlocked_text, body_style))

    left_text = "<b>Left to Do (Locked Concepts):</b> " + (
        ", ".join([f"🔒 {n.title}" for n in locked_nodes]) if locked_nodes else "All concepts completed! 🎉"
    )
    story.append(Paragraph(left_text, body_style))

    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#cbd5e1'), spaceBefore=2, spaceAfter=8))

    # Main Unit-Wise Q&A Reference Guide
    story.append(Paragraph("2. Unit-Wise Concept Questions & Reference Answers", h1_style))

    # Group nodes by Unit
    unit_map = {}
    for node in nodes:
        u_ref = clean_unit_name(node.unit_ref)
        if u_ref not in unit_map:
            unit_map[u_ref] = []
        unit_map[u_ref].append(node)

    def extract_unit_num(u_str):
        match = re.search(r'\d+', u_str)
        return int(match.group(0)) if match else 0

    sorted_units = sorted(unit_map.keys(), key=extract_unit_num)

    for unit_name in sorted_units:
        unit_nodes = unit_map[unit_name]
        story.append(Paragraph(f"<b>📁 {unit_name}</b> ({len(unit_nodes)} concepts)", h1_style))

        for idx, node in enumerate(unit_nodes):
            status = mastery_map.get(node.id, "locked")
            status_badge = "✅ Mastered" if status == "mastered" else "⏳ Unlocked" if status == "unlocked" else "🔒 Locked"
            
            # Fetch cached answer or generate reference answer
            ref_answer = generate_node_answer(db, node, workspace)

            # Convert markdown to ReportLab compatible HTML tags
            clean_ans = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', ref_answer)
            clean_ans = re.sub(r'#+\s*(.*?)\n', r'<b>\1</b><br/>', clean_ans)
            clean_ans = clean_ans.replace("`", "").replace("*", "")
            clean_ans_html = clean_ans.replace("\n", "<br/>")

            q_elements = [
                Paragraph(f"<b>Q{idx + 1}: {node.title}</b> &nbsp; <font color='#6366f1'>[{status_badge}]</font>", q_title_style),
                Paragraph(f"<b>Overview:</b> {node.summary}", body_style),
            ]

            if node.sub_points:
                sub_str = "<b>Key Sub-topics:</b> " + "; ".join([f"{sp['title']}: {sp['description']}" for sp in node.sub_points])
                q_elements.append(Paragraph(sub_str, body_style))

            q_elements.append(Paragraph(f"<b>Reference Answer:</b><br/>{clean_ans_html}", answer_box_style))
            story.append(KeepTogether(q_elements))
            story.append(Spacer(1, 4))

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
