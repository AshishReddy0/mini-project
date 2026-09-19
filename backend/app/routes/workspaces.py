# Workspace CRUD API routes.

from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.workspace import WorkspaceCreate, WorkspaceResponse, WorkspaceUpdate
from app.services import workspace_service
from app.utils.security import get_current_user

# Initializes APIRouter for workspace operations under /workspaces prefix
router = APIRouter(prefix="/workspaces", tags=["Workspaces"])

# Endpoint for listing all workspaces belonging to the authenticated user
@router.get("", response_model=list[WorkspaceResponse])
def list_workspaces(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return workspace_service.list_workspaces(db, current_user)

# Endpoint for creating a new subject workspace
@router.post("", response_model=WorkspaceResponse, status_code=201)
def create_workspace(
    data: WorkspaceCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return workspace_service.create_workspace(db, current_user, data)

# Endpoint for retrieving details of a single workspace by ID
@router.get("/{workspace_id}", response_model=WorkspaceResponse)
def get_workspace(
    workspace_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return workspace_service.get_workspace_for_user(db, workspace_id, current_user)

# Endpoint for updating workspace metadata (name, description)
@router.put("/{workspace_id}", response_model=WorkspaceResponse)
def update_workspace(
    workspace_id: UUID,
    data: WorkspaceUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    workspace = workspace_service.get_workspace_for_user(db, workspace_id, current_user)
    return workspace_service.update_workspace(db, workspace, data)

# Endpoint for permanently deleting a workspace and associated files
@router.delete("/{workspace_id}", status_code=204)
def delete_workspace(
    workspace_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    workspace = workspace_service.get_workspace_for_user(db, workspace_id, current_user)
    workspace_service.delete_workspace(db, workspace)

