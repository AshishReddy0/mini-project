from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.concept_graph import ConceptNode, ConceptEdge, NodeMastery, MasteryStatus
from app.schemas.concept_graph import (
    GraphGenerateRequest,
    NodeAttemptRequest,
    ConceptGraphResponse,
)
from app.services import workspace_service, graph_service
from app.utils.security import get_current_user

router = APIRouter(prefix="/workspaces", tags=["Concept Graph"])


@router.post("/{workspace_id}/graph/generate")
def generate_graph(
    workspace_id: UUID,
    data: GraphGenerateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Analyze workspace documents and generate a concept dependency graph with sub_points."""
    workspace = workspace_service.get_workspace_for_user(db, workspace_id, current_user)
    try:
        res = graph_service.generate_concept_graph(
            db,
            workspace,
            data.document_id,
            answer_formats=data.answer_formats,
            custom_format=data.custom_format,
            portion_text=data.portion_text,
        )
        return res
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate graph: {str(e)}",
        )


@router.get("/{workspace_id}/graph", response_model=ConceptGraphResponse)
def get_graph(
    workspace_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Retrieve the concept graph nodes, edges, and user mastery statuses."""
    workspace = workspace_service.get_workspace_for_user(db, workspace_id, current_user)
    # Clean up duplicate nodes or legacy multi-unit strings in the database
    graph_service.cleanup_db_workspace_nodes(db, workspace.id)

    nodes = (
        db.query(ConceptNode)
        .filter(ConceptNode.workspace_id == workspace.id)
        .order_by(ConceptNode.order_hint.asc())
        .all()
    )

    node_ids = [n.id for n in nodes]

    edges = db.query(ConceptEdge).filter(ConceptEdge.from_node_id.in_(node_ids)).all()

    # Re-evaluate mastery states so they're always accurate
    graph_service.evaluate_mastery_states(db, workspace.id, current_user.id)

    masteries = db.query(NodeMastery).filter(
        NodeMastery.node_id.in_(node_ids),
        NodeMastery.user_id == current_user.id
    ).all()

    mastery_map = {str(m.node_id): m for m in masteries}

    return {
        "nodes": nodes,
        "edges": edges,
        "masteries": mastery_map
    }


@router.delete("/{workspace_id}/graph", status_code=status.HTTP_200_OK)
def clear_graph(
    workspace_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Clear all concept nodes and graph data for a workspace."""
    workspace = workspace_service.get_workspace_for_user(db, workspace_id, current_user)
    graph_service.clear_workspace_graph(db, workspace.id)
    return {"message": "Concept syllabus cleared successfully"}


@router.get("/{workspace_id}/graph/export-pdf")
def export_graph_pdf(
    workspace_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Generate and download a comprehensive Concept Syllabus PDF report."""
    workspace = workspace_service.get_workspace_for_user(db, workspace_id, current_user)
    try:
        pdf_bytes = graph_service.generate_syllabus_pdf_bytes(db, workspace)
        safe_title = "".join(c for c in workspace.name if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
        filename = f"{safe_title or 'Workspace'}_Concept_Syllabus.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate PDF: {str(e)}"
        )


@router.get("/{workspace_id}/node/{node_id}/answer")
def get_node_answer(
    workspace_id: UUID,
    node_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Get or generate the rich Markdown reference answer for a specific concept node.
    Uses cached answer_cache if available, otherwise generates via Gemini and caches it.
    """
    workspace = workspace_service.get_workspace_for_user(db, workspace_id, current_user)
    node = db.query(ConceptNode).filter(
        ConceptNode.id == node_id,
        ConceptNode.workspace_id == workspace.id
    ).first()
    if not node:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Concept node not found")

    try:
        answer = graph_service.generate_node_answer(db, node, workspace)
        return {
            "node_id": str(node.id),
            "title": node.title,
            "summary": node.summary,
            "difficulty": node.difficulty,
            "sub_points": node.sub_points or [],
            "answer": answer,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate answer: {str(e)}"
        )


@router.post("/{workspace_id}/node/{node_id}/master")
def mark_node_mastered(
    workspace_id: UUID,
    node_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Directly mark a concept node as mastered (after user confirms they understand it)."""
    workspace = workspace_service.get_workspace_for_user(db, workspace_id, current_user)
    node = db.query(ConceptNode).filter(
        ConceptNode.id == node_id,
        ConceptNode.workspace_id == workspace.id
    ).first()
    if not node:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Concept node not found")

    mastery = db.query(NodeMastery).filter(
        NodeMastery.node_id == node_id,
        NodeMastery.user_id == current_user.id
    ).first()

    if not mastery:
        mastery = NodeMastery(
            user_id=current_user.id,
            node_id=node_id,
            status=MasteryStatus.UNLOCKED.value
        )
        db.add(mastery)

    mastery.status = MasteryStatus.MASTERED.value
    mastery.attempts = (mastery.attempts or 0) + 1
    db.commit()

    # Re-evaluate to propagate unlocks to dependent nodes
    graph_service.evaluate_mastery_states(db, workspace.id, current_user.id)

    return {"status": "mastered", "node_id": str(node_id)}


@router.post("/{workspace_id}/node/{node_id}/attempt")
def attempt_node(
    workspace_id: UUID,
    node_id: UUID,
    data: NodeAttemptRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Submit a mastery check attempt for a node via explain-back mode."""
    workspace = workspace_service.get_workspace_for_user(db, workspace_id, current_user)
    node = db.query(ConceptNode).filter(
        ConceptNode.id == node_id,
        ConceptNode.workspace_id == workspace.id
    ).first()
    if not node:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Concept node not found")

    mastery = db.query(NodeMastery).filter(
        NodeMastery.node_id == node_id,
        NodeMastery.user_id == current_user.id
    ).first()

    if not mastery:
        mastery = NodeMastery(
            user_id=current_user.id,
            node_id=node_id,
            status=MasteryStatus.UNLOCKED.value
        )
        db.add(mastery)

    mastery.attempts = (mastery.attempts or 0) + 1

    if data.explain_mode:
        if not data.explanation or len(data.explanation.strip()) < 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Explanation must be at least 10 characters long."
            )
        try:
            grade_res = graph_service.grade_explanation(node.title, node.summary, data.explanation)
            mastery.last_score = grade_res.get("score", 0)
            mastery.feedback = grade_res.get("feedback", "")

            if grade_res.get("passed", False):
                mastery.status = MasteryStatus.MASTERED.value

            db.commit()
            graph_service.evaluate_mastery_states(db, workspace.id, current_user.id)

            return {
                "passed": grade_res.get("passed", False),
                "score": grade_res.get("score", 0),
                "feedback": grade_res.get("feedback", "")
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to grade explanation: {str(e)}"
            )
    else:
        # Direct score submission
        if data.score is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Score is required.")

        mastery.last_score = int(data.score * 33.3)
        passed = data.score >= 2

        if passed:
            mastery.status = MasteryStatus.MASTERED.value
            mastery.feedback = "Quiz passed successfully!"
        else:
            mastery.feedback = "Did not meet the passing score."

        db.commit()
        graph_service.evaluate_mastery_states(db, workspace.id, current_user.id)

        return {"passed": passed, "score": data.score, "feedback": mastery.feedback}
