"""Admin API router for media, settings, and suggestions."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.auth import require_admin_api
from app.schemas.media import (
    MediaItemResponse,
    MediaItemUpdate,
    SettingResponse,
    SettingUpdate,
    SuggestionResponse,
    SuggestionCreate,
)
from app.services.media import (
    get_media_items,
    get_media_item,
    upload_media,
    update_media,
    delete_media,
    get_settings,
    get_setting,
    upsert_setting,
    delete_setting,
    get_suggestions,
    create_suggestion,
    mark_suggestion_read,
)

router = APIRouter(prefix="/api", tags=["admin_tools"])


# ── Media endpoints (admin only) ──────────────────────────────────────────

@router.get("/media", response_model=List[MediaItemResponse], dependencies=[Depends(require_admin_api)])
def api_list_media(db: Session = Depends(get_db)):
    """List all uploaded media items."""
    return get_media_items(db)


@router.post("/media/upload", response_model=MediaItemResponse, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_admin_api)])
def api_upload_media(
    file: UploadFile = File(...),
    alt_text: str = Form(""),
    db: Session = Depends(get_db),
):
    """Upload a media file."""
    return upload_media(db, file, alt_text)


@router.get("/media/{item_id}", response_model=MediaItemResponse, dependencies=[Depends(require_admin_api)])
def api_get_media(item_id: int, db: Session = Depends(get_db)):
    """Get a single media item by id."""
    item = get_media_item(db, item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"MediaItem {item_id} not found")
    return item


@router.put("/media/{item_id}", response_model=MediaItemResponse, dependencies=[Depends(require_admin_api)])
def api_update_media(item_id: int, body: MediaItemUpdate, db: Session = Depends(get_db)):
    """Update media item metadata (alt text)."""
    item = update_media(db, item_id, body.alt_text or "")
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"MediaItem {item_id} not found")
    return item


@router.delete("/media/{item_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_admin_api)])
def api_delete_media(item_id: int, db: Session = Depends(get_db)):
    """Delete a media item and its file."""
    if not delete_media(db, item_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"MediaItem {item_id} not found")


# ── Settings endpoints (admin only) ───────────────────────────────────────

@router.get("/settings", response_model=List[SettingResponse], dependencies=[Depends(require_admin_api)])
def api_list_settings(db: Session = Depends(get_db)):
    """List all settings."""
    return get_settings(db)


@router.get("/settings/{key}", response_model=SettingResponse, dependencies=[Depends(require_admin_api)])
def api_get_setting(key: str, db: Session = Depends(get_db)):
    """Get a single setting by key."""
    setting = get_setting(db, key)
    if not setting:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Setting '{key}' not found")
    return setting


@router.put("/settings/{key}", response_model=SettingResponse, dependencies=[Depends(require_admin_api)])
def api_upsert_setting(key: str, body: SettingUpdate, db: Session = Depends(get_db)):
    """Create or update a setting."""
    return upsert_setting(db, key, body.value)


@router.delete("/settings/{key}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_admin_api)])
def api_delete_setting(key: str, db: Session = Depends(get_db)):
    """Delete a setting by key."""
    if not delete_setting(db, key):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Setting '{key}' not found")


# ── Suggestions endpoints (admin: list+mark, public: create) ──────────────

@router.get("/suggest", response_model=List[SuggestionResponse], dependencies=[Depends(require_admin_api)])
def api_list_suggestions(db: Session = Depends(get_db)):
    """List all suggestions (admin only)."""
    return get_suggestions(db)


@router.post("/suggest", response_model=SuggestionResponse, status_code=status.HTTP_201_CREATED)
def api_create_suggestion(body: SuggestionCreate, db: Session = Depends(get_db)):
    """Submit a suggestion (public — no auth required)."""
    return create_suggestion(db, body.content, body.author_name, body.author_contact)


@router.put("/suggest/{sug_id}/read", response_model=SuggestionResponse, dependencies=[Depends(require_admin_api)])
def api_mark_suggestion_read(sug_id: int, db: Session = Depends(get_db)):
    """Mark a suggestion as read (admin only)."""
    sug = mark_suggestion_read(db, sug_id)
    if not sug:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Suggestion {sug_id} not found")
    return sug
