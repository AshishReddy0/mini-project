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
    # 1. Collect context
    document_text = ""
    if document_id:
        selected_doc = None
        for doc in workspace.documents:
            if doc.id == document_id:
                selected_doc = doc
                break
        if selected_doc and selected_doc.extracted_text:
            document_text = selected_doc.extracted_text.content
    else:
        for doc in workspace.documents:
            if doc.extracted_text:
                document_text += doc.extracted_text.content + "\n"

    # Prepend user-pasted portion text if provided
    if portion_text and portion_text.strip():
        document_text = f"[USER-DEFINED PORTION / SYLLABUS]\n{portion_text.strip()}\n\n[REFERENCE MATERIAL]\n{document_text}"

    if not document_text.strip():
        raise ValueError("Please upload some study materials or paste your portion text first.")

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

    # 2. Call Gemini — request nodes WITH sub_points and format instructions
    prompt = f"""
    Analyze the following syllabus or textbook context:

    {document_text[:120000]}

    Create a structured Concept Dependency Graph (DAG) for studying this subject.
    Extract a comprehensive list of 8 to 20 key concepts/topics.
    For each concept, provide:
    - title: The concept name
    - summary: A 1-2 sentence overview of the concept
    - difficulty: "easy", "medium", or "hard"
    - prerequisites: list of concept titles that MUST be learned before this one
    - unit_ref: the unit or chapter this concept belongs to (if apparent)
    - sub_points: a list of 3 to 6 sub-topics or key bullet points about this concept.
      Each sub_point must have a "title" (short label, e.g. "Types of Scheduling") and a
      "description" (1-2 sentence explanation of that sub-topic, referenced from the source material).
    {format_note}
    Ensure prerequisites point ONLY to other concepts in this list. Avoid circular dependencies.
    Make sub_points specific, accurate, and directly derived from the provided material.

    Return ONLY a valid JSON array of objects. No markdown, no extra text.

    Format:
    [
      {{
        "title": "Concept Title",
        "summary": "1-2 sentence overview.",
        "difficulty": "medium",
        "prerequisites": ["Prerequisite Title A"],
        "unit_ref": "Unit 1: Introduction",
        "sub_points": [
          {{"title": "Sub-topic Name", "description": "Explanation of this sub-topic from the material."}},
          {{"title": "Another Sub-topic", "description": "Explanation."}}
        ]
      }}
    ]
    """

    ai_response = generate_content(prompt)
    raw_nodes = parse_json_from_ai(ai_response)

    # Cycle check and cleanup
    clean_nodes = detect_and_resolve_cycles(raw_nodes)

    # Delete existing nodes and edges in the workspace
    existing_nodes = db.query(ConceptNode).filter(ConceptNode.workspace_id == workspace.id).all()
    for n in existing_nodes:
        db.delete(n)
    db.commit()

    # Save new nodes (including sub_points)
    db_nodes = []
    title_to_node_map = {}

    for idx, node_data in enumerate(clean_nodes):
        node = ConceptNode(
            workspace_id=workspace.id,
            title=node_data["title"],
            summary=node_data["summary"],
            difficulty=node_data.get("difficulty", "medium"),
            unit_ref=node_data.get("unit_ref"),
            order_hint=idx,
            sub_points=node_data.get("sub_points", []),
            # answer_cache starts as None — generated on first click
            answer_cache=None,
        )
        db.add(node)
        db_nodes.append(node)

    db.commit()

    # Map title to node for creating edges
    for node in db_nodes:
        title_to_node_map[node.title.lower().strip()] = node

    # Save edges
    for idx, node_data in enumerate(clean_nodes):
        target_node = db_nodes[idx]
        prereqs = node_data.get("prerequisites", [])
        for prereq_title in prereqs:
            source_node = title_to_node_map.get(prereq_title.lower().strip())
            if source_node and source_node.id != target_node.id:
                edge = ConceptEdge(
                    from_node_id=source_node.id,
                    to_node_id=target_node.id,
                    relation="prerequisite"
                )
                db.add(edge)

    db.commit()

    # Re-evaluate mastery states for the workspace owner
    evaluate_mastery_states(db, workspace.id, workspace.user_id)

    return {"status": "success", "nodes_count": len(db_nodes)}

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
    
    response_text = generate_content(prompt)
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
    response_text = generate_content(prompt)
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

    Generate a comprehensive, well-structured study reference answer for this concept.
    The answer should be deeply rooted in the reference material provided.

    Structure the response using clean Markdown:
    1. **Overview** — expand the summary into 2-3 sentences giving full context
    2. **Key Sub-topics** — for each sub-point, a paragraph with explanation and any relevant details, formulas, or examples from the source
    3. **How It Works / Process** — explain mechanisms, algorithms, or workflows if applicable
    4. **Key Terms** — a small table or bullet list of important vocabulary with definitions
    5. **Common Exam Points** — 2-3 bullet points on what examiners typically ask about this concept

    Write clearly and precisely. Use tables where helpful. Use code blocks for any algorithms or pseudocode.
    """

    answer = generate_content(prompt)

    # Cache the answer on the node so future clicks are instant
    node.answer_cache = answer
    db.commit()

    return answer
