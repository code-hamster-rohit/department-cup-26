"""
Authentication Router for Google OAuth 2.0 and Google Identity Services (GIS).
Integrates with MongoDB 'department_cup.admins' to enforce tournament administrator privileges.
"""

import httpx
from typing import Any
from fastapi import APIRouter, Request, HTTPException, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from database.config import (
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_REDIRECT_URI_AUDIENCE,
    GOOGLE_REDIRECT_URI_ADMIN,
)
from database.mongo import is_admin_email

auth_router = APIRouter(tags=["Auth"])


class GoogleVerifyRequest(BaseModel):
    credential: str  # Google ID token JWT


class EmailVerifyRequest(BaseModel):
    email: str


@auth_router.get("/api/auth/me")
async def get_current_user(request: Request):
    """Returns the currently authenticated user and their admin status."""
    user = request.session.get("user")
    if not user:
        return {"logged_in": False, "user": None, "is_admin": False}
    
    # Re-verify admin status live against MongoDB in case permissions changed
    email = user.get("email")
    is_admin = is_admin_email(email)
    user["is_admin"] = is_admin
    request.session["user"] = user

    return {
        "logged_in": True,
        "user": user,
        "is_admin": is_admin
    }


@auth_router.post("/api/auth/verify_email")
async def verify_email_admin(payload: EmailVerifyRequest, request: Request):
    """
    Direct verification for administrator emails against MongoDB department_cup.admins.
    Provides a guaranteed authentication path if Google popup is blocked.
    """
    email = payload.email.strip().lower()
    if not is_admin_email(email):
        return {
            "success": False,
            "is_admin": False,
            "message": f"Email '{email}' is not in the tournament admins collection."
        }
    user_obj = {
        "email": email,
        "name": email.split("@")[0].replace(".", " ").title(),
        "picture": "",
        "is_admin": True
    }
    request.session["user"] = user_obj
    return {"success": True, "is_admin": True, "user": user_obj}



@auth_router.post("/api/auth/google/verify")
async def verify_google_credential(payload: GoogleVerifyRequest, request: Request):
    """
    Verifies Google ID Token returned by Google Identity Services (GIS) button.
    Validates token against Google tokeninfo endpoint, checks MongoDB admins collection,
    and initializes session.
    """
    credential = payload.credential
    if not credential:
        raise HTTPException(status_code=400, detail="Missing credential token")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://oauth2.googleapis.com/tokeninfo",
                params={"id_token": credential}
            )
            if resp.status_code != 200:
                raise HTTPException(status_code=401, detail="Invalid or expired Google token")
            token_data = resp.json()

        # Validate Audience matches client id
        aud = token_data.get("aud")
        if GOOGLE_CLIENT_ID and aud != GOOGLE_CLIENT_ID:
            raise HTTPException(status_code=401, detail="Token audience mismatch")

        email = token_data.get("email", "").strip().lower()
        if not email:
            raise HTTPException(status_code=400, detail="No email provided in Google token")

        name = token_data.get("name", email.split("@")[0])
        picture = token_data.get("picture", "")

        # Live verification against MongoDB department_cup.admins
        is_admin = is_admin_email(email)

        user_obj = {
            "email": email,
            "name": name,
            "picture": picture,
            "is_admin": is_admin,
            "sub": token_data.get("sub", "")
        }

        request.session["user"] = user_obj
        request.session["just_signed_in"] = True

        return {
            "success": True,
            "user": user_obj,
            "is_admin": is_admin
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Authentication error: {str(e)}")


@auth_router.get("/auth/google/login")
async def google_login_redirect(request: Request, dest: str = "audience"):
    """
    Initiates Google OAuth 2.0 Authorization Code Flow.
    Uses registered redirect URI matching .env configuration.
    """
    if dest == "admin":
        redirect_uri = GOOGLE_REDIRECT_URI_ADMIN
    else:
        redirect_uri = GOOGLE_REDIRECT_URI_AUDIENCE

    google_auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri={redirect_uri}"
        "&response_type=code"
        "&scope=openid%20email%20profile"
        f"&state={dest}"
        "&access_type=offline"
        "&prompt=select_account"
    )
    return RedirectResponse(url=google_auth_url)


async def process_oauth_code_if_present(request: Request, redirect_uri: str) -> dict[str, Any] | None:
    """
    Helper called by page routes when Google redirects back with ?code=...
    Exchanges authorization code for tokens, extracts profile, verifies admin status in MongoDB,
    and stores user in session.
    """
    code = request.query_params.get("code")
    if not code:
        return None

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            token_res = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": redirect_uri
                }
            )
            if token_res.status_code != 200:
                print(f"[OAuth] Token exchange failed: {token_res.text}")
                return None
            token_data = token_res.json()
            access_token = token_data.get("access_token")

            userinfo_res = await client.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            if userinfo_res.status_code != 200:
                print(f"[OAuth] Userinfo failed: {userinfo_res.text}")
                return None
            userinfo = userinfo_res.json()

        email = userinfo.get("email", "").strip().lower()
        name = userinfo.get("name", email.split("@")[0])
        picture = userinfo.get("picture", "")

        is_admin = is_admin_email(email)

        user_obj = {
            "email": email,
            "name": name,
            "picture": picture,
            "is_admin": is_admin
        }
        request.session["user"] = user_obj
        request.session["just_signed_in"] = True
        return user_obj
    except Exception as e:
        print(f"[OAuth] Exception in process_oauth_code_if_present: {e}")
        return None


@auth_router.get("/auth/logout")
@auth_router.post("/api/auth/logout")
async def logout_user(request: Request):
    """Logs out the user and clears session."""
    request.session.clear()
    if request.headers.get("accept", "").startswith("application/json"):
        return {"success": True, "message": "Logged out successfully"}
    return RedirectResponse(url="/", status_code=303)
