"""Pydantic-модели для API сайта села Золотаревка."""
from pydantic import BaseModel, Field
from typing import Optional


class PageCreate(BaseModel):
    id: str = Field(..., description="URL-идентификатор (slug)")
    name: str = Field(..., description="Название страницы")
    icon: str = Field(default="📄", description="Иконка emoji")
    parent: Optional[str] = Field(default=None, description="ID родительской страницы")
    sort_order: int = Field(default=99, description="Порядок сортировки")


class PageUpdate(BaseModel):
    name: Optional[str] = Field(default=None)
    icon: Optional[str] = Field(default=None)
    parent: Optional[str] = Field(default=None)
    sort_order: Optional[int] = Field(default=None)
    status: Optional[str] = Field(default=None)


class BlockCreate(BaseModel):
    id: str = Field(..., description="ID блока")
    page_id: str = Field(..., description="ID страницы")
    type: str = Field(..., description="Тип блока")
    name: str = Field(default="Блок")
    sort_order: int = Field(default=0)
    config: dict = Field(default_factory=dict)


class RoleCreate(BaseModel):
    id: str = Field(..., description="ID роли")
    name: str = Field(..., description="Название роли")
    icon: str = Field(default="🛡️")
    sections: list = Field(default_factory=list)
    caps: dict = Field(default_factory=dict)


class SuggestionCreate(BaseModel):
    name: str = Field(..., description="Имя отправителя")
    email: str = Field(..., description="Email")
    category: str = Field(default="news", description="Категория")
    text: str = Field(..., description="Текст новости")


class ReorderItem(BaseModel):
    id: str
    sort_order: int


class ReorderRequest(BaseModel):
    items: list[ReorderItem]
