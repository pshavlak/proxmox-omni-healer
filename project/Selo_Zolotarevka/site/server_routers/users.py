"""Admin API router for users and roles management."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.auth import require_admin_api
from app.schemas.users import RoleResponse, RoleCreate, UserResponse, UserCreate
from app.services.users import get_roles, create_role, delete_role, get_users, create_user, delete_user

router = APIRouter(prefix="/api", tags=["admin_users"], dependencies=[Depends(require_admin_api)])


# ── Roles ─────────────────────────────────────────────────────────────────

@router.get("/roles", response_model=List[RoleResponse])
def api_list_roles(db: Session = Depends(get_db)):
    return get_roles(db)


@router.post("/roles", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
def api_create_role(body: RoleCreate, db: Session = Depends(get_db)):
    return create_role(db, body.name, body.description)


@router.delete("/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
def api_delete_role(role_id: int, db: Session = Depends(get_db)):
    if not delete_role(db, role_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Role {role_id} not found")


# ── Users ─────────────────────────────────────────────────────────────────

@router.get("/users", response_model=List[UserResponse])
def api_list_users(db: Session = Depends(get_db)):
    return get_users(db)


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def api_create_user(body: UserCreate, db: Session = Depends(get_db)):
    return create_user(db, body.username, body.role_id)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def api_delete_user(user_id: int, db: Session = Depends(get_db)):
    if not delete_user(db, user_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User {user_id} not found")
