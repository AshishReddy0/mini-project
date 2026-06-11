# Authentication API routes: register, login, and current user profile.

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.auth import TokenResponse, UserLogin, UserRegister, UserResponse
from app.services import auth_service
from app.utils.security import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=201)
def register(data: UserRegister, db: Annotated[Session, Depends(get_db)]):
    """Create a new student account."""
    return auth_service.register_user(db, data)


@router.post("/login", response_model=TokenResponse)
def login(data: UserLogin, db: Annotated[Session, Depends(get_db)]):
    """Log in and receive a JWT access token."""
    _, token = auth_service.login_user(db, data)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
def get_me(current_user: Annotated[User, Depends(get_current_user)]):
    """Return the currently authenticated user's profile."""
    return current_user
