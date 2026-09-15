# Workspace business logic — subject-specific study areas.

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.workspace import Workspace
from app.models.concept_graph import ConceptNode, NodeMastery
from app.schemas.workspace import WorkspaceCreate, WorkspaceUpdate


def populate_workspace_stats(db: Session, workspace: Workspace, user: User) -> Workspace:
    """Attach concept stats to a workspace instance."""
    total_concepts = (
        db.query(ConceptNode)
        .filter(ConceptNode.workspace_id == workspace.id)
        .count()
    )
    mastered_concepts = (
        db.query(NodeMastery)
        .join(ConceptNode, NodeMastery.node_id == ConceptNode.id)
        .filter(
            ConceptNode.workspace_id == workspace.id,
            NodeMastery.user_id == user.id,
            NodeMastery.status == "mastered"
        )
        .count()
    )
    workspace.total_concepts = total_concepts
    workspace.mastered_concepts = mastered_concepts
    return workspace


def get_workspace_for_user(db: Session, workspace_id: UUID, user: User) -> Workspace:
    """
    Fetch a workspace and ensure it belongs to the current user.
    Prevents users from accessing another student's workspaces.
    """
    workspace = (
        db.query(Workspace)
        .filter(Workspace.id == workspace_id, Workspace.user_id == user.id)
        .first()
    )
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found",
        )
    return populate_workspace_stats(db, workspace, user)


def list_workspaces(db: Session, user: User) -> list[Workspace]:
    """Return all workspaces owned by the user with concept progress stats."""
    workspaces = db.query(Workspace).filter(Workspace.user_id == user.id).all()
    for ws in workspaces:
        populate_workspace_stats(db, ws, user)
    return workspaces



def create_workspace(db: Session, user: User, data: WorkspaceCreate) -> Workspace:
    """Create a new subject workspace for the current user."""
    workspace = Workspace(
        user_id=user.id,
        name=data.name,
        description=data.description,
    )
    db.add(workspace)
    db.commit()
    db.refresh(workspace)
    return workspace


def update_workspace(
    db: Session, workspace: Workspace, data: WorkspaceUpdate
) -> Workspace:
    """Update workspace name and/or description."""
    if data.name is not None:
        workspace.name = data.name
    if data.description is not None:
        workspace.description = data.description

    db.commit()
    db.refresh(workspace)
    return workspace


def delete_workspace(db: Session, workspace: Workspace) -> None:
    """Delete a workspace and all related documents, content, and chat."""
    db.delete(workspace)
    db.commit()
