"""Admin API router for menu CRUD — uses the service layer."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.menu import (
    MenuItemCreate,
    MenuItemResponse,
    MenuItemTreeNode,
    MenuItemUpdate,
    ReorderItem,
)
from app.services import (
    create_menu_item,
    delete_menu_item,
    get_menu_item,
    get_menu_items,
    get_menu_tree,
    reorder_menu_items,
    update_menu_item,
)
from app.services.auth import require_admin_api

router = APIRouter(prefix="/menu", tags=["menu"])


# ── POST /menu/items ──────────────────────────────────────────────────────

@router.post("/items", response_model=MenuItemResponse, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_admin_api)])
def api_create_item(body: MenuItemCreate, db: Session = Depends(get_db)):
    """Create a new menu item."""
    return create_menu_item(db, body)


# ── GET /menu/items ───────────────────────────────────────────────────────

@router.get("/items", response_model=List[MenuItemResponse], dependencies=[Depends(require_admin_api)])
def api_list_items(db: Session = Depends(get_db)):
    """Return all menu items as a flat list."""
    return get_menu_items(db)


# ── GET /menu/items/{item_id} ─────────────────────────────────────────────

@router.get("/items/{item_id}", response_model=MenuItemResponse, dependencies=[Depends(require_admin_api)])
def api_get_item(item_id: int, db: Session = Depends(get_db)):
    """Return a single menu item by id."""
    item = get_menu_item(db, item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MenuItem {item_id} not found",
        )
    return item


# ── PUT /menu/items/{item_id} ─────────────────────────────────────────────

@router.put("/items/{item_id}", response_model=MenuItemResponse, dependencies=[Depends(require_admin_api)])
def api_update_item(item_id: int, body: MenuItemUpdate, db: Session = Depends(get_db)):
    """Update an existing menu item (partial update)."""
    item = update_menu_item(db, item_id, body)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MenuItem {item_id} not found",
        )
    return item


# ── DELETE /menu/items/{item_id} ──────────────────────────────────────────

@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require_admin_api)])
def api_delete_item(item_id: int, db: Session = Depends(get_db)):
    """Delete a menu item (cascades to children via DB)."""
    if not delete_menu_item(db, item_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MenuItem {item_id} not found",
        )


# ── PUT /menu/reorder ─────────────────────────────────────────────────────

@router.put("/reorder", response_model=List[MenuItemResponse], dependencies=[Depends(require_admin_api)])
def api_reorder(body: List[ReorderItem], db: Session = Depends(get_db)):
    """Batch-update order and/or parent_id for multiple items."""
    return reorder_menu_items(db, body)


# ── GET /menu (public) ─────────────────────────────────────────────────────
# Returns the active-only tree — the public site menu. NO auth required.

@router.get("", response_model=List[MenuItemTreeNode])
def api_public_menu(
    db: Session = Depends(get_db),
):
    """Return the public site menu (active items only, nested tree)."""
    return get_menu_tree(db, active_only=True)


# ── GET /menu/tree ────────────────────────────────────────────────────────

@router.get("/tree", response_model=List[MenuItemTreeNode], dependencies=[Depends(require_admin_api)])
def api_get_tree(
    active_only: bool = Query(False),
    db: Session = Depends(get_db),
):
    """Return the menu as a nested tree (optionally only active items)."""
    return get_menu_tree(db, active_only=active_only)
