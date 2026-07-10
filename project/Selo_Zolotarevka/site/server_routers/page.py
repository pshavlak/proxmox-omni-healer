"""Admin API router for pages CRUD — uses the service layer."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.page import (
    PageCreate,
    PageResponse,
    PageUpdate,
    ReorderPage,
)
from app.services.auth import require_admin_api
from app.services.page import (
    create_page,
    delete_page,
    get_page,
    get_pages,
    reorder_pages,
    update_page,
)

router = APIRouter(prefix="/pages", tags=["pages"], dependencies=[Depends(require_admin_api)])


# ── GET /pages ────────────────────────────────────────────────────────────

@router.get("", response_model=List[PageResponse])
def api_list_pages(db: Session = Depends(get_db)):
    """Return all pages as a flat list, ordered by order then title."""
    return get_pages(db)


# ── GET /pages/{page_id} ─────────────────────────────────────────────────

@router.get("/{page_id}", response_model=PageResponse)
def api_get_page(page_id: int, db: Session = Depends(get_db)):
    """Return a single page by id."""
    page = get_page(db, page_id)
    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Page {page_id} not found",
        )
    return page


# ── POST /pages ───────────────────────────────────────────────────────────

@router.post("", response_model=PageResponse, status_code=status.HTTP_201_CREATED)
def api_create_page(body: PageCreate, db: Session = Depends(get_db)):
    """Create a new page."""
    return create_page(db, body)


# ── PUT /pages/{page_id} ─────────────────────────────────────────────────

@router.put("/{page_id}", response_model=PageResponse)
def api_update_page(page_id: int, body: PageUpdate, db: Session = Depends(get_db)):
    """Update an existing page (partial update)."""
    page = update_page(db, page_id, body)
    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Page {page_id} not found",
        )
    return page


# ── DELETE /pages/{page_id} ───────────────────────────────────────────────

@router.delete("/{page_id}", status_code=status.HTTP_204_NO_CONTENT)
def api_delete_page(page_id: int, db: Session = Depends(get_db)):
    """Delete a page."""
    if not delete_page(db, page_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Page {page_id} not found",
        )


# ── POST /pages/reorder ────────────────────────────────────────────────────

@router.post("/reorder", response_model=List[PageResponse])
def api_reorder_pages(body: List[ReorderPage], db: Session = Depends(get_db)):
    """Batch-update order for multiple pages."""
    return reorder_pages(db, body)
