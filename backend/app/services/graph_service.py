import json
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.workspace import Workspace
from app.models.concept_graph import ConceptNode, ConceptEdge, NodeMastery, MasteryStatus
from app.services.gemini_service import generate_content

def parse_json_from_ai(text: str):
    """Clean markdown code blocks and parse JSON output from LLM."""
    cleaned = text.strip()
    if "```json" in cleaned:
        cleaned = cleaned.split("```json")[1].split("```")[0].strip()
    elif "```" in cleaned:
        cleaned = cleaned.split("```")[1].split("```")[0].strip()
    return json.loads(cleaned)

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

def clean_unit_name(u_str: str | None) -> str:
    if not u_str:
        return "Unit 1"
    import re
    match = re.search(r'unit\s*(\d+)', u_str, re.IGNORECASE)
    if match:
        return f"Unit {match.group(1)}"
    cleaned = re.sub(r'[:\-].*$', '', u_str).strip()
    return cleaned if cleaned else "Unit 1"

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

    # 2. Call Gemini — request nodes WITH sub_points and format instruction
    prompt = f"""
    Analyze the following syllabus, course material, or Q-bank context:

    {document_text[:120000]}

    Extract a comprehensive list of 5 to 15 key concepts/questions for studying this subject.
    {existing_note}
    
    For each item, provide:
    - title: The concept name or question title
    - summary: A 1-2 sentence overview or answer summary
    - category: "LAQ" (Long Answer Question / 10 Marks), "SAQ" (Short Answer Question / 2-5 Marks), or "Concept" (Core Concept)
    - difficulty: "easy", "medium", or "hard"
    - prerequisites: list of concept titles that MUST be learned before this one
    - unit_ref: MUST be a single clean unit string for ONE unit only (e.g. "Unit 1" or "Unit 2"). DO NOT join multiple units like "Unit 1,3" or "Unit 1 and 2". If a concept spans multiple units, assign it to the primary unit.
    - sub_points: a list of 3 to 6 sub-topics or key bullet points about this concept.
      Each sub_point must have a "title" (short label) and a "description" (1-2 sentence explanation).
    {format_note}
    Ensure prerequisites point ONLY to other concepts in this list or existing workspace concepts. Avoid circular dependencies.

    Return ONLY a valid JSON array of objects. No markdown, no extra text.

    Format:
    [
      {{
        "title": "Concept Title or Question",
        "summary": "1-2 sentence overview.",
        "category": "LAQ",
        "difficulty": "medium",
        "prerequisites": ["Prerequisite Title A"],
        "unit_ref": "Unit 1",
        "sub_points": [
          {{"title": "Sub-topic Name", "description": "Explanation."}}
        ]
      }}
    ]
    """

    ai_response = generate_content(prompt, expect_json=True)
    raw_nodes = parse_json_from_ai(ai_response)

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
        # Store category in difficulty or sub_points metadata if needed
        difficulty_val = node_data.get("category") or node_data.get("difficulty", "medium")
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
