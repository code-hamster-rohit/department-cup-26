"""
Department Cup 2026 - Main FastAPI Application
Live Sports Scoreboard & Administration System
IIT Roorkee, Saharanpur Campus
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from database.config import (
    setup_database,
    SECRET_KEY,
    GOOGLE_CLIENT_ID,
    GOOGLE_REDIRECT_URI_AUDIENCE,
    GOOGLE_REDIRECT_URI_ADMIN,
)
from database.mongo import is_admin_email
from database.rules import get_all_sports, get_sport_rule
from database.storage import list_matches, get_match, get_active_matches
from routes.api import api_router
from routes.ws import ws_router
from routes.auth import auth_router, process_oauth_code_if_present

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(BASE_DIR, "static")
templates_dir = os.path.join(BASE_DIR, "templates")

templates = Jinja2Templates(directory=templates_dir)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize persistent storage and print status
    setup_database()
    yield


class VercelPathNormalizerMiddleware:
    """
    Normalizes request paths when deployed as a serverless function on Vercel.
    When Vercel rewrites routes to api/index.py, it passes the original client path
    in the `x-matched-path` header while setting `scope['path']` to `/api/index.py`.
    This middleware restores `scope['path']` to the true user path before routing.
    """
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] in ("http", "websocket"):
            headers = dict(scope.get("headers", []))
            matched = (
                headers.get(b"x-matched-path")
                or headers.get(b"x-original-url")
                or headers.get(b"x-forwarded-uri")
            )
            if matched:
                path = matched.decode("utf-8").split("?")[0]
                scope["path"] = path
                scope["raw_path"] = path.encode("utf-8")
            else:
                raw_path = scope.get("path", "")
                if raw_path in ("/api/index.py", "/api/index", "/api", "/api/"):
                    scope["path"] = "/"
                    scope["raw_path"] = b"/"
                elif raw_path.startswith("/api/index.py/"):
                    p = raw_path[len("/api/index.py"):]
                    scope["path"] = p
                    scope["raw_path"] = p.encode("utf-8")
                elif raw_path.startswith("/api/index/"):
                    p = raw_path[len("/api/index"):]
                    scope["path"] = p
                    scope["raw_path"] = p.encode("utf-8")
        await self.app(scope, receive, send)


app = FastAPI(
    title="Department Cup 2026 · Live Scoreboard",
    description="Real-Time Sports Scoreboard & Administration System with zero-latency WebSockets",
    version="1.0.0",
    lifespan=lifespan
)

# Enable signed session cookies for authentication
app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    max_age=86400 * 7,  # 7 days
    same_site="lax"
)

# Outermost middleware: normalizes Vercel rewrites and x-matched-path
app.add_middleware(VercelPathNormalizerMiddleware)

# Mount static assets
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Mount API, WebSocket, and Auth routers
app.include_router(auth_router)
app.include_router(api_router)
app.include_router(ws_router)


def get_session_user_context(request: Request) -> tuple[dict | None, bool]:
    """Helper to extract user and live verify admin status against MongoDB."""
    user = request.session.get("user")
    header_email = request.headers.get("X-Admin-Email")
    if not user and header_email:
        is_adm = is_admin_email(header_email)
        user = {"email": header_email, "name": header_email.split("@")[0], "is_admin": is_adm}
        return user, is_adm

    if not user:
        return None, False
    email = user.get("email")
    is_admin = is_admin_email(email)
    user["is_admin"] = is_admin
    request.session["user"] = user
    return user, is_admin


# -----------------------------------------------------------------------------
# AUDIENCE ARENA ROUTES
# -----------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
@app.get("/api/index.py", response_class=HTMLResponse)
@app.get("/api/index", response_class=HTMLResponse)
async def audience_view(request: Request, match: str | None = None):
    # Handle incoming OAuth code redirect if present
    if request.query_params.get("code"):
        await process_oauth_code_if_present(request, GOOGLE_REDIRECT_URI_AUDIENCE)
        return RedirectResponse(url="/", status_code=303)

    user, is_admin = get_session_user_context(request)
    show_dest_modal = bool(request.session.pop("just_signed_in", False) and is_admin)

    all_m = list_matches()
    active_m = None

    if match:
        active_m = get_match(match)

    # If no match query specified, pick the currently live or first match if any
    if not active_m and all_m:
        # Prioritize live match, then squads_announced, then upcoming
        live_matches = [m for m in all_m if m.get("status") == "live"]
        if live_matches:
            active_m = live_matches[0]
        else:
            active_m = all_m[0]

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "active_nav": "audience",
            "active_match": active_m,
            "all_matches": all_m,
            "current_user": user,
            "is_admin": is_admin,
            "show_dest_modal": show_dest_modal,
            "google_client_id": GOOGLE_CLIENT_ID
        }
    )


@app.get("/match/{match_id}")
async def match_direct_link(match_id: str):
    return RedirectResponse(url=f"/?match={match_id}", status_code=303)


# -----------------------------------------------------------------------------
# ADMINISTRATOR CENTER ROUTES
# -----------------------------------------------------------------------------

@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    # Handle incoming OAuth code redirect if present
    if request.query_params.get("code"):
        await process_oauth_code_if_present(request, GOOGLE_REDIRECT_URI_ADMIN)
        return RedirectResponse(url="/admin", status_code=303)

    user, is_admin = get_session_user_context(request)
    show_dest_modal = bool(request.session.pop("just_signed_in", False) and is_admin)

    matches = list_matches()
    sports = get_all_sports()

    return templates.TemplateResponse(
        request=request,
        name="admin.html",
        context={
            "active_nav": "admin",
            "matches": matches,
            "sports": sports,
            "current_user": user,
            "is_admin": is_admin,
            "show_dest_modal": show_dest_modal,
            "google_client_id": GOOGLE_CLIENT_ID
        }
    )


@app.get("/admin/match/{match_id}", response_class=HTMLResponse)
async def admin_control_room(request: Request, match_id: str):
    user, is_admin = get_session_user_context(request)

    m = get_match(match_id)
    if not m:
        raise HTTPException(status_code=404, detail="Match not found")

    sport_rule = get_sport_rule(m["sport_id"]) or {}

    return templates.TemplateResponse(
        request=request,
        name="admin_match.html",
        context={
            "active_nav": "admin",
            "match": m,
            "sport_rule": sport_rule,
            "current_user": user,
            "is_admin": is_admin,
            "google_client_id": GOOGLE_CLIENT_ID
        }
    )


# -----------------------------------------------------------------------------
# OFFICIAL RULEBOOK BROWSER
# -----------------------------------------------------------------------------

@app.get("/rules", response_class=HTMLResponse)
async def rulebook_view(request: Request):
    user, is_admin = get_session_user_context(request)
    sports = get_all_sports()
    return templates.TemplateResponse(
        request=request,
        name="rules.html",
        context={
            "active_nav": "rules",
            "sports": sports,
            "current_user": user,
            "is_admin": is_admin,
            "google_client_id": GOOGLE_CLIENT_ID
        }
    )


@app.get("/health")
async def health():
    return {"status": "ok", "app": "Department Cup 2026 Scoreboard"}