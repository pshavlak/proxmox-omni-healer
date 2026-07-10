"""Admin authentication router — login, logout, and login page."""

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

from app.services.auth import verify_credentials

router = APIRouter(prefix="/admin", tags=["admin_auth"])

_templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))


@router.get("/login", response_class=HTMLResponse, include_in_schema=False)
def login_page(request: Request):
    """Render the admin login page."""
    # Already logged in — bounce to admin dashboard
    if request.session.get("admin_authenticated"):
        return RedirectResponse(url="/admin/menu", status_code=302)

    return _templates.TemplateResponse(
        request=request,
        name="admin/login.html",
    )


@router.post("/login", include_in_schema=False)
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    """Authenticate admin credentials and set session cookie."""
    if verify_credentials(username, password):
        request.session["admin_authenticated"] = True
        # Redirect to the page the user was trying to reach, default to /admin/menu
        next_url = request.query_params.get("next", "/admin/menu")
        return RedirectResponse(url=next_url, status_code=302)

    return _templates.TemplateResponse(
        request=request,
        name="admin/login.html",
        context={"error": "Неверное имя пользователя или пароль"},
        status_code=401,
    )


@router.get("/logout", include_in_schema=False)
def logout(request: Request):
    """Clear the admin session and redirect to login."""
    request.session.clear()
    return RedirectResponse(url="/admin/login", status_code=302)
