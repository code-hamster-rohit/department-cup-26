"""
REST API endpoints for Department Cup Scoreboard.
Every state mutation triggers instantaneous WebSocket broadcasting.
"""

import time
from typing import Any
from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel

from database.rules import get_all_sports, get_sport_rule
from database.teams_data import DEPARTMENTS, load_registered_department_rosters
from database.mongo import is_admin_email, get_all_admin_emails, add_admin_email
from database.storage import (
    create_match,
    get_match,
    list_matches,
    update_squads_and_toss,
    update_players_and_toss,
    start_match,
    update_score_action,
    undo_last_action,
    end_match,
    delete_match,
    restore_match_to_screen,
)
from routes.ws import manager

api_router = APIRouter(prefix="/api", tags=["API"])


def verify_admin_access(request: Request) -> str:
    """Verifies that the caller has an active admin email in MongoDB department_cup.admins."""
    user = request.session.get("user")
    email = user.get("email") if (user and isinstance(user, dict)) else None
    if not email:
        email = request.headers.get("X-Admin-Email")
    
    if not email:
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Please sign in with an authorized Google administrator account."
        )

    if not is_admin_email(email):
        raise HTTPException(
            status_code=403,
            detail=f"Access Denied: Email '{email}' is not registered as an administrator in the MongoDB department_cup.admins collection."
        )
    return email


class CreateMatchRequest(BaseModel):
    sport_id: str
    team_a: str
    team_b: str
    venue: str = "Main Sports Ground"
    stage: str = "League Match"
    custom_overs: int | None = None
    day_label: str = "Day 1"
    scheduled_date: str = ""
    category: str | None = None


class SquadsTossRequest(BaseModel):
    squad_a: dict[str, Any] | None = None
    squad_b: dict[str, Any] | None = None
    players_a: str | None = None
    players_b: str | None = None
    toss_winner: str | None = None
    toss_decision: str | None = None


class PlayersTossRequest(BaseModel):
    players_a: str = ""
    players_b: str = ""
    toss_winner: str | None = None
    toss_decision: str | None = None


class ScoreActionRequest(BaseModel):
    type: str  # run, boundary, wicket, extra, dead_ball, goal, point, attempt, activate_event, update_event_meta, record_event_result, pause_tie, etc.
    runs: int | None = 0
    extra_type: str | None = None
    dismissal: str | None = None
    striker: str | None = None
    non_striker: str | None = None
    bowler: str | None = None
    new_batsman: str | None = None
    commentary: str | None = None
    is_special_dead_ball_penalty: bool | None = False
    # Football / Shootout / Volleyball / Racquets / Others / Athletics
    name: str | None = None
    department: str | None = None
    team: str | None = None
    player: str | None = None
    assist: str | None = None
    minute: str | None = None
    card_color: str | None = None
    stat_key: str | None = None
    delta: int | None = 1
    half: int | None = None
    result: str | None = None
    event_index: int | None = None
    winner: str | None = None
    distance: float | None = None
    is_foul: bool | None = False
    attempt_type: str | None = "official"
    bib: str | None = None
    zone: int | None = 1
    success: bool | None = False
    # Multi-event sub-event scheduling and result recording
    day_label: str | None = None
    scheduled_date: str | None = None
    players_a: str | None = None
    players_b: str | None = None
    status: str | None = None
    sets_a: int | None = None
    sets_b: int | None = None
    set_history: list[dict[str, Any]] | None = None
    note: str | None = None
    # Tug of War and Carrom specific fields
    duration: str | None = None
    lane_a: str | None = None
    lane_b: str | None = None
    cautions_a: int | None = None
    cautions_b: int | None = None
    board_num: int | None = None
    white_pts: int | None = None
    black_pts: int | None = None
    queen: str | None = None
    net_points: int | None = None


class EndMatchRequest(BaseModel):
    winner: str
    result_summary: str
    player_of_the_match: str = ""


@api_router.get("/debug/db")
async def debug_db():
    from database.mongo import MONGO_URI, DATABASE_NAME, get_db, get_mongo_client
    import traceback
    
    uri_set = bool(MONGO_URI)
    uri_preview = (MONGO_URI[:12] + "..." + MONGO_URI[-10:]) if len(MONGO_URI) > 25 else ("Set" if uri_set else "NOT SET")
    
    status = {
        "mongo_uri_set": uri_set,
        "mongo_uri_preview": uri_preview,
        "database_name": DATABASE_NAME,
        "connected": False,
        "error": None,
        "matches_count": 0,
        "matches_ids": []
    }
    
    try:
        db = get_db()
        if db is not None:
            client = get_mongo_client()
            if client:
                client.admin.command("ping")
                status["connected"] = True
                status["matches_count"] = db["matches"].count_documents({})
                status["matches_ids"] = [d.get("id") for d in db["matches"].find({}, {"id": 1}).limit(10)]
            else:
                status["error"] = "get_mongo_client() returned None"
        else:
            status["error"] = "get_db() returned None (MONGO_URI may be empty or connection failed)"
    except Exception as e:
        status["error"] = f"{type(e).__name__}: {str(e)}"
        status["traceback"] = traceback.format_exc()
        
    return status


@api_router.get("/sports")
async def get_sports():
    return {"sports": get_all_sports()}


@api_router.get("/departments")
async def get_departments_data():
    rosters = load_registered_department_rosters()
    return {
        "departments": DEPARTMENTS,
        "registered_rosters": rosters
    }


@api_router.get("/matches")
async def get_all_matches():
    return {"matches": list_matches()}


@api_router.get("/match/{match_id}")
async def get_match_detail(match_id: str, response: Response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    m = get_match(match_id, force_mongo=True)
    if not m:
        raise HTTPException(status_code=404, detail="Match not found")
    return {"match": m}


@api_router.post("/match/create")
async def api_create_match(payload: CreateMatchRequest, request: Request):
    verify_admin_access(request)
    
    # Verify MongoDB connectivity before creating match in serverless environment
    from database.mongo import get_db, MONGO_URI
    if not MONGO_URI or "<cluster>" in MONGO_URI or "<username>" in MONGO_URI or "<password>" in MONGO_URI:
        raise HTTPException(
            status_code=500,
            detail="MONGO_URI in Vercel contains placeholder text ('<cluster>'). Please update MONGO_URI in Vercel Project Settings with your actual MongoDB connection string."
        )
    db = get_db()
    if db is None:
        raise HTTPException(
            status_code=500,
            detail="Database connection to MongoDB Atlas failed. Please check MONGO_URI in Vercel Environment Variables and verify that MongoDB Atlas Network Access allows 0.0.0.0/0."
        )

    try:
        match = await create_match(
            sport_id=payload.sport_id,
            team_a_code=payload.team_a,
            team_b_code=payload.team_b,
            venue=payload.venue,
            stage=payload.stage,
            custom_overs=payload.custom_overs,
            day_label=payload.day_label,
            scheduled_date=payload.scheduled_date,
            category=payload.category
        )
        await manager.broadcast_match(match["id"], "MATCH_CREATED", match)
        return {"success": True, "match": match}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@api_router.post("/match/{match_id}/squads")
async def api_update_squads(match_id: str, payload: SquadsTossRequest, request: Request):
    verify_admin_access(request)
    try:
        if payload.players_a or payload.players_b:
            match = await update_players_and_toss(
                match_id=match_id,
                players_a=payload.players_a or "",
                players_b=payload.players_b or "",
                toss_winner=payload.toss_winner,
                toss_decision=payload.toss_decision
            )
        else:
            match = await update_squads_and_toss(
                match_id=match_id,
                squad_a=payload.squad_a or {},
                squad_b=payload.squad_b or {},
                toss_winner=payload.toss_winner,
                toss_decision=payload.toss_decision
            )
        await manager.broadcast_match(match_id, "SQUADS_ANNOUNCED", match)
        return {"success": True, "match": match}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@api_router.post("/match/{match_id}/players")
async def api_update_players(match_id: str, payload: PlayersTossRequest, request: Request):
    verify_admin_access(request)
    try:
        match = await update_players_and_toss(
            match_id=match_id,
            players_a=payload.players_a,
            players_b=payload.players_b,
            toss_winner=payload.toss_winner,
            toss_decision=payload.toss_decision
        )
        await manager.broadcast_match(match_id, "PLAYERS_UPDATED", match)
        return {"success": True, "match": match}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@api_router.post("/match/{match_id}/start")
async def api_start_match(match_id: str, request: Request):
    verify_admin_access(request)
    try:
        match = await start_match(match_id)
        await manager.broadcast_match(match_id, "MATCH_STARTED", match)
        return {"success": True, "match": match}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@api_router.post("/match/{match_id}/score")
async def api_score_action(match_id: str, payload: ScoreActionRequest, request: Request):
    verify_admin_access(request)
    try:
        action_dict = payload.model_dump(exclude_none=True)
        match = await update_score_action(match_id, action_dict)
        await manager.broadcast_match(match_id, "SCORE_UPDATED", {
            "score": match["score"],
            "commentary": match["commentary"][-1] if match["commentary"] else None,
            "status": match["status"],
            "result": match.get("result")
        })
        return {"success": True, "match": match}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@api_router.post("/match/{match_id}/undo")
async def api_undo_action(match_id: str, request: Request):
    verify_admin_access(request)
    try:
        match = await undo_last_action(match_id)
        await manager.broadcast_match(match_id, "SCORE_UPDATED", {
            "score": match["score"],
            "commentary": match["commentary"][-1] if match["commentary"] else None,
            "status": match["status"],
            "result": match.get("result")
        })
        return {"success": True, "match": match}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@api_router.post("/match/{match_id}/end")
async def api_end_match(match_id: str, payload: EndMatchRequest, request: Request):
    verify_admin_access(request)
    try:
        match = await end_match(
            match_id=match_id,
            winner=payload.winner,
            result_summary=payload.result_summary,
            motm=payload.player_of_the_match
        )
        await manager.broadcast_match(match_id, "MATCH_COMPLETED", match)
        return {"success": True, "match": match}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@api_router.post("/match/{match_id}/delete")
@api_router.delete("/match/{match_id}")
async def api_delete_match(match_id: str, request: Request):
    verify_admin_access(request)
    try:
        result = await delete_match(match_id)
        if result.get("deleted_from_db"):
            await manager.broadcast_match(match_id, "MATCH_DELETED", {"match_id": match_id, "action": "deleted"})
        else:
            await manager.broadcast_match(match_id, "MATCH_CLEARED_SCREEN", {"match_id": match_id, "action": "cleared_from_screen"})
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@api_router.post("/match/{match_id}/restore")
async def api_restore_match(match_id: str, request: Request):
    verify_admin_access(request)
    try:
        match = await restore_match_to_screen(match_id)
        await manager.broadcast_match(match_id, "MATCH_RESTORED", {"match_id": match_id})
        return {"success": True, "match": match}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class AddAdminRequest(BaseModel):
    email: str
    name: str = ""


@api_router.get("/admins")
async def api_list_admins(request: Request):
    verify_admin_access(request)
    return {"admins": get_all_admin_emails()}


@api_router.post("/admins/add")
async def api_add_admin(payload: AddAdminRequest, request: Request):
    current_admin = verify_admin_access(request)
    success = add_admin_email(payload.email, payload.name, added_by=current_admin)
    return {"success": success, "admins": get_all_admin_emails()}


class ReactionRequest(BaseModel):
    content: str
    sender: str | None = "Audience"


@api_router.post("/match/{match_id}/react")
async def api_send_reaction(match_id: str, payload: ReactionRequest):
    """
    Broadcasts ephemeral fading reaction (emojis or crowd chant text)
    to all active live viewers of the match. No persistent storage.
    """
    content = payload.content.strip()[:60]
    if not content:
        raise HTTPException(status_code=400, detail="Empty reaction content")

    m = get_match(match_id)
    if not m:
        raise HTTPException(status_code=404, detail="Match not found")

    await manager.broadcast_match(match_id, "LIVE_REACTION", {
        "content": content,
        "sender": payload.sender or "Audience",
        "time": time.time()
    })
    return {"success": True, "content": content}


@api_router.get("/match/{match_id}/poll")
async def api_poll_match(match_id: str, response: Response, since: str | float | None = None):
    """
    HTTP polling fallback for serverless environments (Vercel) where
    WebSockets are not available. Returns current match state so the
    frontend can diff and update the DOM.
    """
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    m = get_match(match_id, force_mongo=True)
    if not m:
        raise HTTPException(status_code=404, detail="Match not found")

    # Return lightweight payload with score, status, and recent commentary
    recent_commentary = m.get("commentary", [])[-5:] if m.get("commentary") else []
    return {
        "match_id": match_id,
        "status": m.get("status"),
        "score": m.get("score"),
        "result": m.get("result"),
        "commentary": recent_commentary,
        "updated_at": m.get("updated_at", ""),
        "server_time": time.time()
    }


@api_router.get("/matches/active/poll")
async def api_poll_active_matches(response: Response):
    """
    HTTP polling fallback that returns a summary of all active (live) matches.
    Used by the audience arena when WebSockets are unavailable.
    """
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    from database.storage import get_active_matches
    active = get_active_matches(force_mongo=True)
    summaries = []
    for m in active:
        summaries.append({
            "id": m["id"],
            "sport_name": m.get("sport_name"),
            "sport_type": m.get("sport_type"),
            "team_a": m.get("team_a", {}).get("abbr"),
            "team_b": m.get("team_b", {}).get("abbr"),
            "status": m.get("status"),
            "score": m.get("score"),
            "result": m.get("result"),
            "updated_at": m.get("updated_at", "")
        })
    return {"matches": summaries, "server_time": time.time()}
