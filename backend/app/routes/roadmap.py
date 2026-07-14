import json
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.roadmap import RoadmapGenerateRequest
from app.services import workspace_service
from app.services.gemini_service import generate_content
from app.utils.security import get_current_user

router = APIRouter(prefix="/workspaces", tags=["Study Roadmap"])


def parse_json_from_ai(text: str):
    """Clean markdown code blocks and parse JSON output from LLM."""
    cleaned = text.strip()
    # Remove code blocks if present
    if "```json" in cleaned:
        cleaned = cleaned.split("```json")[1].split("```")[0].strip()
    elif "```" in cleaned:
        cleaned = cleaned.split("```")[1].split("```")[0].strip()
    return json.loads(cleaned)


@router.get("/{workspace_id}/roadmap")
def get_roadmap(
    workspace_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Retrieve the active learning roadmap for the workspace."""
    workspace = workspace_service.get_workspace_for_user(db, workspace_id, current_user)
    return workspace.roadmap_json or {"units": []}


@router.post("/{workspace_id}/roadmap/generate")
def generate_roadmap(
    workspace_id: UUID,
    data: RoadmapGenerateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Analyze syllabus or workspace documents and create a structured learning roadmap."""
    workspace = workspace_service.get_workspace_for_user(db, workspace_id, current_user)

    selected_doc = None
    if data.document_id:
        for doc in workspace.documents:
            if doc.id == data.document_id:
                selected_doc = doc
                break
        if not selected_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Selected syllabus document not found",
            )
    elif workspace.documents:
        # Default to first document uploaded as the syllabus context
        selected_doc = workspace.documents[0]
    
    if not selected_doc or not selected_doc.extracted_text or not selected_doc.extracted_text.content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please upload a syllabus or study document to the workspace first.",
        )

    syllabus_text = selected_doc.extracted_text.content

    prompt = f"""
    Analyze the following syllabus, course outline, or study material:

    {syllabus_text}

    Create a structured, logical, unit-wise learning roadmap to prepare for this subject.
    Divide the material into 4 to 8 sequential study units.
    
    Return ONLY a valid JSON array of objects.
    Do not add extra explanation, headings, markdown code blocks, or text.
    
    Format:
    [
      {{
        "id": 1,
        "title": "Unit Name/Title",
        "topics": ["Topic A", "Topic B", "Topic C"],
        "unlocked": true,
        "completed": false
      }},
      {{
        "id": 2,
        "title": "Unit Name/Title",
        "topics": ["Topic D", "Topic E"],
        "unlocked": false,
        "completed": false
      }}
    ]
    """

    try:
        response_text = generate_content(prompt)
        units = parse_json_from_ai(response_text)
        
        # Ensure the first unit is always unlocked by default
        if units:
            units[0]["unlocked"] = True

        roadmap_data = {"units": units}
        workspace.roadmap_json = roadmap_data
        db.commit()
        db.refresh(workspace)
        return workspace.roadmap_json
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate roadmap from AI: {str(e)}",
        )


@router.post("/{workspace_id}/roadmap/step/{step_id}/complete")
def complete_step(
    workspace_id: UUID,
    step_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Mark a unit step as completed and unlock the next unit step."""
    workspace = workspace_service.get_workspace_for_user(db, workspace_id, current_user)
    if not workspace.roadmap_json or "units" not in workspace.roadmap_json:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Roadmap is not generated yet.",
        )

    units = list(workspace.roadmap_json["units"])
    step_found = False

    for idx, unit in enumerate(units):
        if unit["id"] == step_id:
            unit["completed"] = True
            step_found = True
            # Unlock next unit if exists
            if idx + 1 < len(units):
                units[idx + 1]["unlocked"] = True
            break

    if not step_found:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unit with ID {step_id} not found in roadmap.",
        )

    # Re-save JSON to trigger SQLAlchemy mutation tracking
    workspace.roadmap_json = {"units": units}
    db.commit()
    db.refresh(workspace)
    return workspace.roadmap_json


@router.post("/{workspace_id}/roadmap/step/{step_id}/learn")
def learn_step(
    workspace_id: UUID,
    step_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Generate study content and practice questions for a specific unit using the workspace context."""
    workspace = workspace_service.get_workspace_for_user(db, workspace_id, current_user)
    if not workspace.roadmap_json or "units" not in workspace.roadmap_json:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Roadmap is not generated yet.",
        )

    active_unit = None
    for unit in workspace.roadmap_json["units"]:
        if unit["id"] == step_id:
            active_unit = unit
            break

    if not active_unit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unit not found.",
        )

    if not active_unit["unlocked"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This unit is locked. Please complete the previous units first.",
        )

    # Collect workspace context (excluding syllabus if we want, but simple merge of all texts is fine)
    workspace_context = ""
    for doc in workspace.documents:
        if doc.extracted_text:
            workspace_context += doc.extracted_text.content + "\n"

    if not workspace_context:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No study material documents found in workspace.",
        )

    prompt = f"""
    You are a study assistant helping a student prepare for: {workspace.name}
    Active Unit: {active_unit['title']}
    Specific Topics: {", ".join(active_unit['topics'])}

    Using this study material:
    {workspace_context}

    Please provide:
    1. A detailed study explanation of the topics in clean Markdown. Use headings, lists, bold text, and code snippets where appropriate. Keep it concise but comprehensive.
    2. Exactly 3 practice multiple-choice questions (MCQs) to verify their understanding.

    Return ONLY a valid JSON object.
    Do not add extra explanation outside the JSON. Do not return markdown code block markers.

    Format:
    {{
      "material": "detailed markdown explanations here...",
      "quiz": [
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
    }}
    """

    try:
        response_text = generate_content(prompt)
        data = parse_json_from_ai(response_text)
        return data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate study materials: {str(e)}",
        )


@router.post("/{workspace_id}/roadmap/reset")
def reset_roadmap(
    workspace_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Delete the generated roadmap for the workspace."""
    workspace = workspace_service.get_workspace_for_user(db, workspace_id, current_user)
    workspace.roadmap_json = None
    db.commit()
    db.refresh(workspace)
    return {"status": "reset"}
