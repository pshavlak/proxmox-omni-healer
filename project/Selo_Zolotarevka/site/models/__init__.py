"""
Pydantic модели для сайта Золотаревка.
"""
from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime


class PageBase(BaseModel):
    id: str
    name: str
    icon: str = "📄"
    parent: Optional[str] = None
    sort_order: int = 99
    status: str = "draft"


class Page(PageBase):
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class PageCreate(BaseModel):
    id: str
    name: str
    icon: str = "📄"
    parent: Optional[str] = None
    sort_order: int = 99


class PageUpdate(BaseModel):
    name: Optional[str] = None
    icon: Optional[str] = None
    parent: Optional[str] = None
    sort_order: Optional[int] = None
    status: Optional[str] = None


class BlockBase(BaseModel):
    id: str
    page_id: str
    type: str
    name: str = "Блок"
    sort_order: int = 0
    config: Any = {}


class Block(BlockBase):
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class BlockCreate(BaseModel):
    id: Optional[str] = None
    type: str
    name: str = "Блок"
    sort_order: int = 0
    config: Any = {}


class BlockUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    config: Optional[Any] = None


class RoleBase(BaseModel):
    id: str
    name: str
    icon: str = "🛡️"
    sections: Any = []
    caps: Any = {}


class Role(RoleBase):
    created_at: Optional[str] = None


class RoleCreate(BaseModel):
    id: Optional[str] = None
    name: str
    icon: str = "🛡️"
    sections: Any = []
    caps: Any = {}


class MediaItem(BaseModel):
    id: int
    filename: str
    original_name: str
    mime_type: str
    size: int
    alt_text: str = ""
    url: str = ""
    created_at: Optional[str] = None


class SuggestionCreate(BaseModel):
    name: str
    email: str
    category: str = "Новость"
    text: str


class ReorderItem(BaseModel):
    id: str
    sort_order: int


class ReorderRequest(BaseModel):
    items: list[ReorderItem]
