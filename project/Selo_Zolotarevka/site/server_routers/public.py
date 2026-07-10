"""Public API — menu endpoints for the public site."""

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.menu import MenuItemTreeNode
from app.services.menu import get_active_menu_tree

router = APIRouter(prefix="/api", tags=["public"])


@router.get("/menu", response_model=List[MenuItemTreeNode])
def public_menu(db: Session = Depends(get_db)):
    """
    Return the active menu tree for the public site.
    Only items with is_active=True are included, nested as a tree.
    """
    return get_active_menu_tree(db)
