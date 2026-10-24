"""
Storage and Match State Management Engine for Department Cup.
Supports persistent JSON file storage with thread-safe writes,
sub-millisecond reads, and optional MongoDB synchronization.
"""

import os
import json
import uuid
import asyncio
from datetime import datetime
from typing import Any

from database.rules import RULES_DATA, get_sport_rule, is_team_sport, is_single_double_sport
from database.teams_data import DEPARTMENTS, get_default_squad
from sports import init_sport_score, handle_sport_action

VALID_DEPARTMENTS = {"amsc", "ppe", "ppt"}

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
MATCHES_FILE = os.path.join(DATA_DIR, "matches.json")

_lock = asyncio.Lock()
_matches_cache: dict[str, dict[str, Any]] = {}


def _load_matches_from_disk() -> dict[str, dict[str, Any]]:
    # 1. Check primary persistent file
    target_file = MATCHES_FILE
    if not os.path.exists(target_file):
        # 2. Check /tmp fallback in serverless (e.g., Vercel Lambda container reuse)
        tmp_target = os.path.join("/tmp", "department_cup_data", "matches.json")
        if os.path.exists(tmp_target):
            target_file = tmp_target
        else:
            return {}
    try:
        with open(target_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except Exception as e:
        print(f"Error loading matches from disk: {e}")
        return {}


def _save_matches_to_disk(match_to_sync: dict[str, Any] | None = None):
    # 1. Live MongoDB synchronization FIRST (critical for serverless like Vercel)
    try:
        from database.mongo import sync_match_to_mongo
        if match_to_sync:
            sync_match_to_mongo(match_to_sync)
        else:
            for m in list(_matches_cache.values()):
                sync_match_to_mongo(m)
    except Exception as e:
        print(f"[Storage] MongoDB sync error: {e}")

    # 2. File cache writing (works locally, falls back gracefully on read-only serverless)
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        temp_file = f"{MATCHES_FILE}.tmp"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(_matches_cache, f, indent=2, default=str)
        # Atomic file replacement
        os.replace(temp_file, MATCHES_FILE)
    except OSError:
        # In read-only serverless environments (e.g., Vercel Lambda), write to /tmp
        try:
            tmp_data_dir = os.path.join("/tmp", "department_cup_data")
            os.makedirs(tmp_data_dir, exist_ok=True)
            tmp_file = os.path.join(tmp_data_dir, "matches.json")
            with open(tmp_file, "w", encoding="utf-8") as f:
                json.dump(_matches_cache, f, indent=2, default=str)
        except Exception:
            pass


def init_storage():
    """Initializes storage cache from persistent file, synced with MongoDB Atlas."""
    global _matches_cache
    _matches_cache = _load_matches_from_disk()
    try:
        from database.mongo import load_matches_from_mongo
        mongo_matches = load_matches_from_mongo()
        if mongo_matches:
            for m_id, m_doc in mongo_matches.items():
                _matches_cache[m_id] = m_doc
    except Exception as e:
        print(f"[Storage] Initial Mongo sync skipped: {e}")
    # Strictly filter out any matches not exclusively between AMSC, PPE, PPT
    _matches_cache = {
        m_id: m for m_id, m in _matches_cache.items()
        if m.get("team_a", {}).get("code", "").lower() in VALID_DEPARTMENTS
        and m.get("team_b", {}).get("code", "").lower() in VALID_DEPARTMENTS
    }
    print(f"Storage initialized with {len(_matches_cache)} matches.")


def _normalize_match_squad_and_sport(match: dict[str, Any] | None) -> dict[str, Any] | None:
    if not match or not isinstance(match, dict):
        return match
    is_team = is_team_sport(match.get("sport_id") or match.get("sport_type"))
    match["is_team_sport"] = is_team
    if is_team:
        # For team sports (cricket, football, volleyball, box cricket, TOW, etc.):
        # ensure whole squad info is present
        squads = match.get("squads")
        if not squads or not isinstance(squads, dict) or not squads.get("team_a") or not squads.get("team_b"):
            team_a_code = match.get("team_a", {}).get("code", "amsc") if isinstance(match.get("team_a"), dict) else str(match.get("team_a", "amsc")).lower()
            team_b_code = match.get("team_b", {}).get("code", "ppe") if isinstance(match.get("team_b"), dict) else str(match.get("team_b", "ppe")).lower()
            sport_rule = get_sport_rule(match.get("sport_id", match.get("sport_type"))) or {}
            match["squads"] = {
                "team_a": get_default_squad(team_a_code, match.get("sport_id", match.get("sport_type")), sport_rule, category=match.get("category")),
                "team_b": get_default_squad(team_b_code, match.get("sport_id", match.get("sport_type")), sport_rule, category=match.get("category")),
            }
    else:
        # For single/doubles sports (badminton, TT, carrom, athletics):
        # do NOT take a whole squad.
        match["squads"] = {}
    return match


def get_match(match_id: str, force_mongo: bool = False) -> dict[str, Any] | None:
    if force_mongo:
        try:
            from database.mongo import get_db, SPORT_COLLECTIONS
            db = get_db()
            if db is not None:
                for col in SPORT_COLLECTIONS:
                    doc = db[col].find_one({"id": match_id})
                    if doc:
                        doc.pop("_id", None)
                        _matches_cache[match_id] = doc
                        return _normalize_match_squad_and_sport(doc)
                existing_cols = db.list_collection_names()
                if "matches" in existing_cols:
                    doc = db["matches"].find_one({"id": match_id})
                    if doc:
                        doc.pop("_id", None)
                        _matches_cache[match_id] = doc
                        return _normalize_match_squad_and_sport(doc)
        except Exception:
            pass

    m = _matches_cache.get(match_id)
    if m:
        return _normalize_match_squad_and_sport(m)
    # Fallback to MongoDB sport collections if not in memory
    try:
        from database.mongo import get_db, SPORT_COLLECTIONS
        db = get_db()
        if db is not None:
            for col in SPORT_COLLECTIONS:
                doc = db[col].find_one({"id": match_id})
                if doc:
                    doc.pop("_id", None)
                    _matches_cache[match_id] = doc
                    return _normalize_match_squad_and_sport(doc)
            existing_cols = db.list_collection_names()
            if "matches" in existing_cols:
                doc = db["matches"].find_one({"id": match_id})
                if doc:
                    doc.pop("_id", None)
                    _matches_cache[match_id] = doc
                    return _normalize_match_squad_and_sport(doc)
    except Exception:
        pass
    return None


def list_matches(limit: int = 50, include_hidden: bool = False) -> list[dict[str, Any]]:
    # In serverless environment, if cache is empty, load from MongoDB
    if not _matches_cache:
        try:
            from database.mongo import load_matches_from_mongo
            mongo_matches = load_matches_from_mongo()
            if mongo_matches:
                _matches_cache.update(mongo_matches)
        except Exception:
            pass
    matches = [
        _normalize_match_squad_and_sport(m)
        for m in _matches_cache.values()
        if m and (include_hidden or not m.get("hidden_from_screen", False))
    ]
    # Sort by created_at descending
    matches.sort(key=lambda m: m.get("created_at", ""), reverse=True)
    return matches[:limit]


def get_active_matches(force_mongo: bool = False) -> list[dict[str, Any]]:
    if force_mongo or not _matches_cache:
        try:
            from database.mongo import load_matches_from_mongo
            mongo_matches = load_matches_from_mongo()
            if mongo_matches:
                _matches_cache.update(mongo_matches)
        except Exception:
            pass
    return [
        _normalize_match_squad_and_sport(m)
        for m in _matches_cache.values()
        if m and not m.get("hidden_from_screen", False) and m.get("status") in ["upcoming", "squads_announced", "live"]
    ]



async def create_match(
    sport_id: str,
    team_a_code: str,
    team_b_code: str,
    venue: str = "Main Sports Ground",
    stage: str = "Tournament Match",
    custom_overs: int | None = None,
    day_label: str = "Day 1",
    scheduled_date: str = "",
    category: str | None = None
) -> dict[str, Any]:
    async with _lock:
        sport_rule = get_sport_rule(sport_id)
        if not sport_rule:
            raise ValueError(f"Unknown sport ID: {sport_id}")

        match_id = f"m_{uuid.uuid4().hex[:8]}"

        team_a_key = (team_a_code or "").lower().strip()
        team_b_key = (team_b_code or "").lower().strip()

        if team_a_key not in VALID_DEPARTMENTS or team_b_key not in VALID_DEPARTMENTS:
            raise ValueError(
                f"Invalid department. Department Cup only has 3 departments: AMSC, PPE, and PPT. "
                f"Received '{team_a_code}' vs '{team_b_code}'."
            )
        if team_a_key == team_b_key:
            raise ValueError("A department cannot play against itself. Please select two different departments.")

        team_a_info = DEPARTMENTS[team_a_key]
        team_b_info = DEPARTMENTS[team_b_key]

        # Gender category normalization (Boys, Girls, Mixed, Open)
        norm_cat = (category or "").strip()
        if not norm_cat:
            norm_cat = sport_rule.get("default_gender") or sport_rule.get("category", "Boys")
        # Capitalize nicely
        if norm_cat.lower() in ["boy", "boys"]:
            norm_cat = "Boys"
            g_badge = "👦 Boys"
        elif norm_cat.lower() in ["girl", "girls"]:
            norm_cat = "Girls"
            g_badge = "👧 Girls"
        elif norm_cat.lower() in ["mix", "mixed"]:
            norm_cat = "Mixed"
            g_badge = "👫 Mixed"
        else:
            norm_cat = "Open"
            g_badge = "⚡ Open"

        max_overs = custom_overs or sport_rule.get("match_format", {}).get("innings_overs", 10)
        is_team = is_team_sport(sport_rule["id"]) or is_team_sport(sport_rule.get("sport_type"))
        squads = {}
        if is_team:
            squads = {
                "team_a": get_default_squad(team_a_key, sport_rule["id"], sport_rule, category=norm_cat),
                "team_b": get_default_squad(team_b_key, sport_rule["id"], sport_rule, category=norm_cat)
            }

        match_obj: dict[str, Any] = {
            "id": match_id,
            "sport_id": sport_rule["id"],
            "sport_name": sport_rule["name"],
            "collection_name": sport_rule.get("collection_name", sport_rule["id"]),
            "sport_type": sport_rule["sport_type"],
            "category": norm_cat,
            "gender_category": norm_cat,
            "gender_badge": g_badge,
            "sport_category": sport_rule.get("category", "Sports"),
            "sport_icon": sport_rule["icon"],
            "venue": venue,
            "stage": stage,
            "day_label": day_label or "",
            "scheduled_date": scheduled_date or "",
            "status": "upcoming",  # upcoming -> squads_announced -> live -> completed
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "completed_at": None,
            "is_team_sport": is_team,
            "players_a": "",
            "players_b": "",
            "team_a": {
                "code": team_a_code.lower(),
                "abbr": team_a_info.get("abbr", team_a_code.upper()),
                "name": team_a_info.get("name", team_a_code.upper()),
                "color": team_a_info.get("color", "#3b82f6")
            },
            "team_b": {
                "code": team_b_code.lower(),
                "abbr": team_b_info.get("abbr", team_b_code.upper()),
                "name": team_b_info.get("name", team_b_code.upper()),
                "color": team_b_info.get("color", "#10b981")
            },
            "squads": squads,
            "toss": {
                "conducted": False,
                "winner": None,
                "decision": None,
                "summary": "Toss yet to take place"
            },
            "rulebook_highlights": sport_rule.get("specific_regulations", []),
            "score": init_sport_score(sport_rule, max_overs),
            "commentary": [
                {
                    "time": datetime.utcnow().strftime("%H:%M"),
                    "ball": "-",
                    "text": f"Match created: {team_a_info.get('abbr')} vs {team_b_info.get('abbr')} in {sport_rule['name']}.",
                    "badge": "FIXTURE",
                    "type": "info"
                }
            ],
            "history": [],  # undo stack
            "winner": None,
            "winner_code": None,
            "winner_name": None,
            "result": None
        }

        _matches_cache[match_id] = match_obj
        _save_matches_to_disk(match_obj)
        return match_obj


async def update_squads_and_toss(
    match_id: str,
    squad_a: dict[str, Any],
    squad_b: dict[str, Any],
    toss_winner: str | None = None,
    toss_decision: str | None = None
) -> dict[str, Any]:
    async with _lock:
        match = get_match(match_id)
        if not match:
            raise ValueError(f"Match {match_id} not found")

        if not match.get("squads") or not isinstance(match["squads"], dict):
            match["squads"] = {}

        if squad_a and isinstance(squad_a, dict) and squad_a.get("playing") and len(squad_a["playing"]) > 0:
            if "team_a" not in match["squads"]:
                match["squads"]["team_a"] = {}
            match["squads"]["team_a"]["playing"] = squad_a["playing"]
            cap = next((p["name"] for p in squad_a["playing"] if p.get("is_captain") or p.get("role") == "Captain"), None)
            if cap:
                match["squads"]["team_a"]["captain"] = cap
        elif "team_a" not in match.get("squads", {}):
            sport_rule = get_sport_rule(match.get("sport_id", match.get("sport_type"))) or {}
            match["squads"]["team_a"] = get_default_squad(match["team_a"]["code"], match.get("sport_id", match.get("sport_type")), sport_rule, category=match.get("category"))

        if squad_b and isinstance(squad_b, dict) and squad_b.get("playing") and len(squad_b["playing"]) > 0:
            if "team_b" not in match["squads"]:
                match["squads"]["team_b"] = {}
            match["squads"]["team_b"]["playing"] = squad_b["playing"]
            cap = next((p["name"] for p in squad_b["playing"] if p.get("is_captain") or p.get("role") == "Captain"), None)
            if cap:
                match["squads"]["team_b"]["captain"] = cap
        elif "team_b" not in match.get("squads", {}):
            sport_rule = get_sport_rule(match.get("sport_id", match.get("sport_type"))) or {}
            match["squads"]["team_b"] = get_default_squad(match["team_b"]["code"], match.get("sport_id", match.get("sport_type")), sport_rule, category=match.get("category"))

        match["squads"]["squads_confirmed"] = True

        # Auto-extract athlete names for single-match sports (Badminton, Table Tennis, Carrom, Volleyball)
        if match.get("sport_type") in ["badminton", "table_tennis", "volleyball", "carrom"]:
            p_a = [p.get("name") for p in match.get("squads", {}).get("team_a", {}).get("playing", []) if p.get("name")]
            p_b = [p.get("name") for p in match.get("squads", {}).get("team_b", {}).get("playing", []) if p.get("name")]
            if p_a:
                match["players_a"] = " / ".join(p_a)
                match["score"]["players_a"] = match["players_a"]
            if p_b:
                match["players_b"] = " / ".join(p_b)
                match["score"]["players_b"] = match["players_b"]

        if toss_winner and toss_decision:
            toss_team_name = match["team_a"]["abbr"] if toss_winner == "team_a" else match["team_b"]["abbr"]
            summary = f"{toss_team_name} won the toss and elected to {toss_decision} first."
            match["toss"] = {
                "conducted": True,
                "winner": toss_winner,
                "decision": toss_decision,
                "summary": summary
            }
            if match.get("sport_type") in ["volleyball", "badminton", "table_tennis"]:
                if (toss_winner == "team_a" and toss_decision == "serve") or (toss_winner == "team_b" and toss_decision == "receive"):
                    match["score"]["server"] = "team_a"
                else:
                    match["score"]["server"] = "team_b"
            # Set batting team for cricket based on toss
            if match["sport_type"] == "cricket":
                if (toss_winner == "team_a" and toss_decision == "bat") or (toss_winner == "team_b" and toss_decision == "bowl"):
                    match["score"]["batting_team"] = "team_a"
                    match["score"]["bowling_team"] = "team_b"
                else:
                    match["score"]["batting_team"] = "team_b"
                    match["score"]["bowling_team"] = "team_a"
                match["score"]["innings_1"]["team"] = match["score"]["batting_team"]
                match["score"]["innings_2"]["team"] = match["score"]["bowling_team"]

        match["status"] = "squads_announced"
        match["updated_at"] = datetime.utcnow().isoformat()
        _save_matches_to_disk(match)
        return match


async def update_players_and_toss(
    match_id: str,
    players_a: str = "",
    players_b: str = "",
    toss_winner: str | None = None,
    toss_decision: str | None = None
) -> dict[str, Any]:
    async with _lock:
        match = get_match(match_id)
        if not match:
            raise ValueError(f"Match {match_id} not found")

        if players_a:
            match["players_a"] = players_a
            if "score" in match and isinstance(match["score"], dict):
                match["score"]["players_a"] = players_a
        if players_b:
            match["players_b"] = players_b
            if "score" in match and isinstance(match["score"], dict):
                match["score"]["players_b"] = players_b

        if toss_winner and toss_decision:
            toss_team_name = match["team_a"]["abbr"] if toss_winner == "team_a" else match["team_b"]["abbr"]
            summary = f"{toss_team_name} won the toss and elected to {toss_decision} first."
            match["toss"] = {
                "conducted": True,
                "winner": toss_winner,
                "decision": toss_decision,
                "summary": summary
            }
            if match.get("sport_type") in ["volleyball", "badminton", "table_tennis"]:
                if (toss_winner == "team_a" and toss_decision == "serve") or (toss_winner == "team_b" and toss_decision == "receive"):
                    match["score"]["server"] = "team_a"
                else:
                    match["score"]["server"] = "team_b"

        match["status"] = "squads_announced"
        match["updated_at"] = datetime.utcnow().isoformat()
        _save_matches_to_disk(match)
        return match


async def start_match(match_id: str) -> dict[str, Any]:
    async with _lock:
        match = get_match(match_id)
        if not match:
            raise ValueError(f"Match {match_id} not found")

        match["status"] = "live"
        match["updated_at"] = datetime.utcnow().isoformat()
        
        # Initialize default batsmen/bowler for cricket if not set
        if match["sport_type"] == "cricket":
            inn_key = f"innings_{match['score']['innings']}"
            inn = match["score"][inn_key]
            bat_team_key = match["score"]["batting_team"]
            bowl_team_key = match["score"]["bowling_team"]
            
            bat_playing = match.get("squads", {}).get(bat_team_key, {}).get("playing", [])
            bowl_playing = match.get("squads", {}).get(bowl_team_key, {}).get("playing", [])
            
            if not inn.get("striker") and len(bat_playing) > 0:
                inn["striker"] = bat_playing[0].get("name", "Striker")
                inn["batsmen"][inn["striker"]] = {"runs": 0, "balls": 0, "fours": 0, "sixes": 0, "status": "not out"}
            if not inn.get("non_striker") and len(bat_playing) > 1:
                inn["non_striker"] = bat_playing[1].get("name", "Non-Striker")
                inn["batsmen"][inn["non_striker"]] = {"runs": 0, "balls": 0, "fours": 0, "sixes": 0, "status": "not out"}
            if not inn.get("bowler") and len(bowl_playing) > 0:
                inn["bowler"] = bowl_playing[0].get("name", "Bowler")
                inn["bowlers"][inn["bowler"]] = {"overs": 0.0, "maidens": 0, "runs": 0, "wickets": 0, "legal_balls": 0}
                inn["bowlers"][inn["bowler"]] = {"overs": 0.0, "maidens": 0, "runs": 0, "wickets": 0, "legal_balls": 0}

        _save_matches_to_disk(match)
        return match


async def update_score_action(match_id: str, action: dict[str, Any]) -> dict[str, Any]:
    """
    Executes a sport-specific score update action using dedicated sport modules.
    """
    async with _lock:
        match = get_match(match_id, force_mongo=True)
        if not match:
            raise ValueError(f"Match {match_id} not found")

        # Automatically transition match to live if it was upcoming or squads_announced
        if match.get("status") in ["upcoming", "squads_announced"]:
            match["status"] = "live"

        # Snapshot for undo
        prev_snapshot = json.loads(json.dumps(match["score"]))
        match["history"].append(prev_snapshot)
        if len(match["history"]) > 20:
            match["history"].pop(0)

        # Delegate scoring logic to dedicated sports module
        handle_sport_action(match, action)

        match["updated_at"] = datetime.utcnow().isoformat()
        _save_matches_to_disk(match)
        return match


async def undo_last_action(match_id: str) -> dict[str, Any]:
    async with _lock:
        match = get_match(match_id, force_mongo=True)
        if not match:
            raise ValueError(f"Match {match_id} not found")
        if not match.get("history"):
            raise ValueError("No actions to undo")

        prev_score = match["history"].pop()
        match["score"] = prev_score
        if match["commentary"]:
            match["commentary"].pop()

        match["updated_at"] = datetime.utcnow().isoformat()
        _save_matches_to_disk(match)
        return match


async def end_match(match_id: str, winner: str, result_summary: str, motm: str = "") -> dict[str, Any]:
    async with _lock:
        match = get_match(match_id, force_mongo=True)
        if not match:
            raise ValueError(f"Match {match_id} not found")

        match["status"] = "completed"
        match["result"] = result_summary
        match["winner"] = winner

        if winner == "team_a":
            match["winner_code"] = match["team_a"]["code"]
            match["winner_name"] = match["team_a"]["abbr"]
        elif winner == "team_b":
            match["winner_code"] = match["team_b"]["code"]
            match["winner_name"] = match["team_b"]["abbr"]
        elif winner in ["draw", "tied"]:
            match["winner_code"] = "draw"
            match["winner_name"] = "Draw / Tied"
        else:
            match["winner_code"] = winner.lower()
            match["winner_name"] = winner.upper()

        match["player_of_the_match"] = motm
        match["completed_at"] = datetime.utcnow().isoformat()
        match["updated_at"] = datetime.utcnow().isoformat()

        match["commentary"].append({
            "time": datetime.utcnow().strftime("%H:%M"),
            "ball": "END",
            "text": f"MATCH CONCLUDED! {result_summary}" + (f" Player of the Match: {motm}." if motm else ""),
            "badge": "🏆 WINNER DECLARED",
            "type": "concluded"
        })

        _save_matches_to_disk(match)
        return match


async def delete_match(match_id: str) -> dict[str, Any]:
    """
    Deletes or clears a match based on conclusion status:
    - If match is NOT concluded: Clears from BOTH screen AND database (permanently erased).
    - If match IS concluded: Clears ONLY from screen (marked hidden_from_screen), preserving historical records in database.
    """
    async with _lock:
        # 1. Fetch match from memory cache or MongoDB
        match = _matches_cache.get(match_id) or get_match(match_id)
        if not match:
            # If match not found, ensure any lingering references are purged
            _matches_cache.pop(match_id, None)
            _save_matches_to_disk()
            try:
                from database.mongo import delete_match_from_mongo
                delete_match_from_mongo(match_id)
            except Exception as e:
                print(f"[Storage] MongoDB delete error: {e}")
            return {
                "success": True,
                "status": "not_found_purged",
                "concluded": False,
                "deleted_from_db": True,
                "message": "Match removed from screen and database."
            }

        sport_id = match.get("sport_id") or match.get("sport_type")
        status = match.get("status")
        is_concluded = (status in ["completed", "archived_completed"])

        if not is_concluded:
            # ---------------------------------------------------------
            # 1. UNCONCLUDED MATCH:
            # Delete from BOTH user's screen AND database
            # ---------------------------------------------------------
            _matches_cache.pop(match_id, None)
            _save_matches_to_disk()
            try:
                from database.mongo import delete_match_from_mongo
                delete_match_from_mongo(match_id, sport_id)
            except Exception as e:
                print(f"[Storage] MongoDB match delete error: {e}")

            return {
                "success": True,
                "status": "deleted_everywhere",
                "concluded": False,
                "deleted_from_db": True,
                "message": "Unconcluded match permanently deleted from screen and database."
            }
        else:
            # ---------------------------------------------------------
            # 2. CONCLUDED MATCH:
            # Clear ONLY from screen, and KEEP in database
            # ---------------------------------------------------------
            match["hidden_from_screen"] = True
            _matches_cache[match_id] = match
            _save_matches_to_disk(match)

            return {
                "success": True,
                "status": "cleared_from_screen",
                "concluded": True,
                "deleted_from_db": False,
                "message": "Concluded match cleared from screen. Historical data preserved in database."
            }


async def restore_match_to_screen(match_id: str) -> dict[str, Any]:
    """Restores a concluded match back to active screen display."""
    async with _lock:
        match = _matches_cache.get(match_id) or get_match(match_id)
        if not match:
            raise ValueError(f"Match {match_id} not found")
        match["hidden_from_screen"] = False
        _matches_cache[match_id] = match
        _save_matches_to_disk(match)
        return match


def calculate_department_standings() -> dict[str, Any]:
    """
    Computes tournament standings and live department leads across AMSC, PPE, PPT.
    Tracks total points, matches played/won/lost/drawn, sub-events (rubbers) won,
    and in-progress tie leads across all days of the tournament.
    """
    dept_stats: dict[str, dict[str, Any]] = {}
    for code, info in DEPARTMENTS.items():
        dept_stats[code] = {
            "code": code,
            "abbr": info["abbr"],
            "name": info["name"],
            "color": info["color"],
            "badge_bg": info.get("badge_bg", "rgba(59, 130, 246, 0.15)"),
            "badge_border": info.get("badge_border", "rgba(59, 130, 246, 0.4)"),
            "icon": info.get("icon", "🏅"),
            "points": 0,
            "matches_played": 0,
            "matches_won": 0,
            "matches_lost": 0,
            "matches_drawn": 0,
            "matches_in_progress": 0,
            "sub_events_won": 0,
            "sub_events_played": 0,
            "leading_in_active": 0,
            "active_leads": []
        }

    all_matches = list(_matches_cache.values())
    active_ties_leads = []

    for m in all_matches:
        team_a_code = m.get("team_a", {}).get("code", "").lower()
        team_b_code = m.get("team_b", {}).get("code", "").lower()
        status = m.get("status", "upcoming")
        winner = m.get("winner")
        score = m.get("score", {})
        sport_type = m.get("sport_type")
        sport_name = m.get("sport_name", "Sport")
        sport_icon = m.get("sport_icon", "🏅")
        
        # 1. In-progress lead tracking for set-based sports
        if sport_type in ["badminton", "table_tennis", "volleyball"]:
            wa = score.get("sets_team_a", 0)
            wb = score.get("sets_team_b", 0)
            if status in ["live", "squads_announced", "upcoming"] and (wa > 0 or wb > 0):
                if wa > wb and team_a_code in dept_stats:
                    dept_stats[team_a_code]["leading_in_active"] += 1
                    lead_desc = f"{m['team_a']['abbr']} leads {wa} - {wb} in sets vs {m['team_b']['abbr']}"
                    dept_stats[team_a_code]["active_leads"].append({
                        "match_id": m["id"], "sport_name": sport_name, "sport_icon": sport_icon, "desc": lead_desc
                    })
                    active_ties_leads.append({
                        "match_id": m["id"], "sport_name": sport_name, "sport_icon": sport_icon,
                        "leader": m['team_a']['abbr'], "leader_code": team_a_code,
                        "lead_text": lead_desc, "summary": lead_desc
                    })
                elif wb > wa and team_b_code in dept_stats:
                    dept_stats[team_b_code]["leading_in_active"] += 1
                    lead_desc = f"{m['team_b']['abbr']} leads {wb} - {wa} in sets vs {m['team_a']['abbr']}"
                    dept_stats[team_b_code]["active_leads"].append({
                        "match_id": m["id"], "sport_name": sport_name, "sport_icon": sport_icon, "desc": lead_desc
                    })
                    active_ties_leads.append({
                        "match_id": m["id"], "sport_name": sport_name, "sport_icon": sport_icon,
                        "leader": m['team_b']['abbr'], "leader_code": team_b_code,
                        "lead_text": lead_desc, "summary": lead_desc
                    })

        # 2. Overall Match Status & Points
        if status == "completed":
            if team_a_code in dept_stats:
                dept_stats[team_a_code]["matches_played"] += 1
            if team_b_code in dept_stats:
                dept_stats[team_b_code]["matches_played"] += 1

            if winner in ["team_a", team_a_code]:
                if team_a_code in dept_stats:
                    dept_stats[team_a_code]["matches_won"] += 1
                    dept_stats[team_a_code]["points"] += 3  # 3 points for winning match
                if team_b_code in dept_stats:
                    dept_stats[team_b_code]["matches_lost"] += 1
            elif winner in ["team_b", team_b_code]:
                if team_b_code in dept_stats:
                    dept_stats[team_b_code]["matches_won"] += 1
                    dept_stats[team_b_code]["points"] += 3
                if team_a_code in dept_stats:
                    dept_stats[team_a_code]["matches_lost"] += 1
            elif winner in ["draw", "tied"]:
                if team_a_code in dept_stats:
                    dept_stats[team_a_code]["matches_drawn"] += 1
                    dept_stats[team_a_code]["points"] += 1
                if team_b_code in dept_stats:
                    dept_stats[team_b_code]["matches_drawn"] += 1
                    dept_stats[team_b_code]["points"] += 1
        elif status == "live":
            if team_a_code in dept_stats:
                dept_stats[team_a_code]["matches_in_progress"] += 1
            if team_b_code in dept_stats:
                dept_stats[team_b_code]["matches_in_progress"] += 1

    # Sort leaderboard
    sorted_standings = sorted(
        dept_stats.values(),
        key=lambda x: (x["points"], x["leading_in_active"], x["matches_won"], x["sub_events_won"]),
        reverse=True
    )
    
    for idx, d in enumerate(sorted_standings):
        d["rank"] = idx + 1

    leader = sorted_standings[0] if sorted_standings else None
    
    return {
        "leader": leader["abbr"] if leader else "AMSC",
        "leader_code": leader["code"] if leader else "amsc",
        "leader_points": leader["points"] if leader else 0,
        "standings": sorted_standings,
        "active_leads": active_ties_leads,
        "total_matches": len(all_matches)
    }

