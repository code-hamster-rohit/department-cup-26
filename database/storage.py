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


def get_match(match_id: str) -> dict[str, Any] | None:
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


def list_matches(limit: int = 50) -> list[dict[str, Any]]:
    # In serverless environment, if cache is empty, load from MongoDB
    if not _matches_cache:
        try:
            from database.mongo import load_matches_from_mongo
            mongo_matches = load_matches_from_mongo()
            if mongo_matches:
                _matches_cache.update(mongo_matches)
        except Exception:
            pass
    matches = [_normalize_match_squad_and_sport(m) for m in _matches_cache.values() if m]
    # Sort by created_at descending
    matches.sort(key=lambda m: m.get("created_at", ""), reverse=True)
    return matches[:limit]


def get_active_matches() -> list[dict[str, Any]]:
    if not _matches_cache:
        try:
            from database.mongo import load_matches_from_mongo
            mongo_matches = load_matches_from_mongo()
            if mongo_matches:
                _matches_cache.update(mongo_matches)
        except Exception:
            pass
    return [_normalize_match_squad_and_sport(m) for m in _matches_cache.values() if m and m.get("status") in ["upcoming", "squads_announced", "live"]]



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
            "score": _init_sport_score(sport_rule, max_overs),
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


def _init_sport_score(sport_rule: dict[str, Any], max_overs: int) -> dict[str, Any]:
    stype = sport_rule.get("sport_type")
    
    if stype == "cricket":
        return {
            "innings": 1,
            "batting_team": "team_a",
            "bowling_team": "team_b",
            "max_overs": max_overs,
            "max_overs_per_bowler": sport_rule.get("match_format", {}).get("max_overs_per_bowler", 2),
            "powerplay_overs": sport_rule.get("match_format", {}).get("powerplay_overs", 3 if max_overs >= 10 else 0),
            "is_free_hit": False,
            "is_powerplay": True if (sport_rule.get("match_format", {}).get("powerplay_overs", 0) > 0) else False,
            "innings_1": {
                "team": "team_a",
                "runs": 0,
                "wickets": 0,
                "overs": 0.0,
                "legal_balls": 0,
                "crr": "0.00",
                "extras": {"wides": 0, "no_balls": 0, "byes": 0, "leg_byes": 0, "penalty": 0},
                "striker": None,
                "non_striker": None,
                "bowler": None,
                "batsmen": {},  # name: {runs, balls, fours, sixes, sr, status}
                "bowlers": {},  # name: {overs, maidens, runs, wickets, legal_balls, econ, dots, fours, sixes}
                "fow": [],      # Fall of Wickets: [{wicket, runs, over, player}]
                "partnerships": [],  # Completed partnerships: [{wicket, runs, balls, player_1, player_2}]
                "current_partnership": {"runs": 0, "balls": 0},
                "dnb": [],      # Did Not Bat list
                "timeline": []  # recent deliveries
            },
            "innings_2": {
                "team": "team_b",
                "runs": 0,
                "wickets": 0,
                "overs": 0.0,
                "legal_balls": 0,
                "crr": "0.00",
                "target": None,
                "extras": {"wides": 0, "no_balls": 0, "byes": 0, "leg_byes": 0, "penalty": 0},
                "striker": None,
                "non_striker": None,
                "bowler": None,
                "batsmen": {},
                "bowlers": {},
                "fow": [],
                "partnerships": [],
                "current_partnership": {"runs": 0, "balls": 0},
                "dnb": [],
                "timeline": []
            }
        }
    
    elif stype == "football":
        return {
            "team_a_score": 0,
            "team_b_score": 0,
            "half": 1,
            "period_label": "1st Half",
            "time_display": "00:00",
            "events": [],  # [{type: goal/yellow_card/red_card, team, player, assist, minute}]
            "stats": {
                "team_a": {"shots": 0, "shots_on_target": 0, "corners": 0, "fouls": 0, "yellow_cards": 0, "red_cards": 0, "offsides": 0},
                "team_b": {"shots": 0, "shots_on_target": 0, "corners": 0, "fouls": 0, "yellow_cards": 0, "red_cards": 0, "offsides": 0}
            },
            "extra_time": False,
            "shootout": {"active": False, "team_a_kicks": [], "team_b_kicks": []}
        }

    elif stype == "penalty_shootout":
        return {
            "team_a_score": 0,
            "team_b_score": 0,
            "shots_per_player": 5,
            "team_a_kicks": [],
            "team_b_kicks": [],
            "current_shooter_index": 0,
            "sudden_death": False
        }

    elif stype in ["volleyball", "badminton", "table_tennis"]:
        pts = 21 if stype == "badminton" else (11 if stype == "table_tennis" else 25)
        return {
            "sets_team_a": 0,
            "sets_team_b": 0,
            "current_set": 1,
            "points_to_win_set": pts,
            "set_scores": [{"set": 1, "team_a": 0, "team_b": 0, "winner": None}],
            "server": "team_a",
            "in_deuce": False,
            "total_points_a": 0,
            "total_points_b": 0,
            "players_a": "",
            "players_b": ""
        }

    elif stype == "carrom":
        return {
            "score_team_a": 0,
            "score_team_b": 0,
            "current_board": 1,
            "boards": [],
            "players_a": "",
            "players_b": ""
        }

    elif stype == "tug_of_war":
        return {
            "pulls_team_a": 0,
            "pulls_team_b": 0,
            "current_pull": 1,
            "pulls_to_win": 2,
            "pull_history": []
        }

    elif stype == "athletics_distance":
        return {
            "athletes": []  # List of {name, department, bib, trial, attempts: [a1, a2, a3], best, rank}
        }

    elif stype == "basketball_shootout":
        return {
            "score_team_a": 0,
            "score_team_b": 0,
            "shots_team_a": [],
            "shots_team_b": [],
            "shooters_a": {},  # name: {1pt_made, 1pt_att, 2pt_made, 2pt_att, 3pt_made, 3pt_att, total_pts, pct}
            "shooters_b": {},
            "remaining_shots_a": 30,
            "remaining_shots_b": 30
        }

    return {}


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
    Executes a sport-specific score update action.
    """
    async with _lock:
        match = get_match(match_id)
        if not match:
            raise ValueError(f"Match {match_id} not found")

        # Snapshot for undo
        prev_snapshot = json.loads(json.dumps(match["score"]))
        match["history"].append(prev_snapshot)
        if len(match["history"]) > 20:
            match["history"].pop(0)

        stype = match["sport_type"]
        action_type = action.get("type")

        if stype == "cricket":
            _handle_cricket_action(match, action)
        elif stype == "football":
            _handle_football_action(match, action)
        elif stype == "penalty_shootout":
            _handle_shootout_action(match, action)
        elif stype in ["volleyball", "badminton", "table_tennis"]:
            _handle_set_sport_action(match, action)
        elif stype == "carrom":
            _handle_carrom_action(match, action)
        elif stype == "tug_of_war":
            _handle_tow_action(match, action)
        elif stype == "athletics_distance":
            _handle_athletics_action(match, action)
        elif stype == "basketball_shootout":
            _handle_basketball_action(match, action)

        match["updated_at"] = datetime.utcnow().isoformat()
        _save_matches_to_disk(match)
        return match


def _handle_cricket_action(match: dict[str, Any], action: dict[str, Any]):
    score = match["score"]
    inn_key = f"innings_{score['innings']}"
    inn = score[inn_key]
    act_type = action.get("type")  # run, boundary, wicket, extra, dead_ball, swap_strike, change_bowler, switch_innings

    striker = action.get("striker") or inn.get("striker") or "Striker"
    non_striker = action.get("non_striker") or inn.get("non_striker") or "Non-Striker"
    bowler = action.get("bowler") or inn.get("bowler") or "Bowler"
    inn["striker"] = striker
    inn["non_striker"] = non_striker
    inn["bowler"] = bowler

    # Ensure bowler record
    if bowler not in inn["bowlers"]:
        inn["bowlers"][bowler] = {"overs": 0.0, "maidens": 0, "runs": 0, "wickets": 0, "legal_balls": 0, "dots": 0, "fours": 0, "sixes": 0}
    b_stat = inn["bowlers"][bowler]

    # Ensure striker record
    if striker not in inn["batsmen"]:
        inn["batsmen"][striker] = {"runs": 0, "balls": 0, "fours": 0, "sixes": 0, "sr": "0.0", "status": "not out"}
    s_stat = inn["batsmen"][striker]

    # Calculate current ball notation
    cur_balls = inn["legal_balls"]
    over_num = cur_balls // 6
    ball_in_over = (cur_balls % 6) + 1
    ball_tag = f"{over_num}.{ball_in_over}"

    is_free_hit = score.get("is_free_hit", False)
    cp = inn.setdefault("current_partnership", {"runs": 0, "balls": 0})

    if act_type in ["run", "boundary"]:
        runs = int(action.get("runs", 0))
        
        inn["runs"] += runs
        inn["legal_balls"] += 1
        s_stat["runs"] += runs
        s_stat["balls"] += 1
        cp["runs"] = cp.get("runs", 0) + runs
        cp["balls"] = cp.get("balls", 0) + 1

        if runs == 0:
            b_stat["dots"] = b_stat.get("dots", 0) + 1
        elif runs == 4:
            s_stat["fours"] += 1
            b_stat["fours"] = b_stat.get("fours", 0) + 1
        elif runs == 6:
            s_stat["sixes"] += 1
            b_stat["sixes"] = b_stat.get("sixes", 0) + 1

        b_stat["runs"] += runs
        b_stat["legal_balls"] += 1
        b_stat["overs"] = round((b_stat["legal_balls"] // 6) + (b_stat["legal_balls"] % 6) / 10, 1)

        # Free hit is consumed on a legal delivery
        score["is_free_hit"] = False

        timeline_tag = str(runs) if runs > 0 else "."
        inn["timeline"].append(timeline_tag)

        # Commentary
        comment_text = action.get("commentary") or f"{bowler} to {striker}, {runs} run(s)!"
        if runs == 4:
            comment_text = f"FOUR! {striker} pierces the field with impeccable timing."
        elif runs == 6:
            comment_text = f"SIX! Massive hit by {striker} high into the stands!"
        
        match["commentary"].append({
            "time": datetime.utcnow().strftime("%H:%M"),
            "ball": ball_tag,
            "text": comment_text,
            "badge": f"{runs} RUNS" if runs not in [4, 6] else ("FOUR" if runs == 4 else "SIX"),
            "type": "boundary" if runs in [4, 6] else "run"
        })

        # Odd runs change strike
        if runs % 2 != 0:
            inn["striker"], inn["non_striker"] = inn["non_striker"], inn["striker"]

        # Check end of over
        if inn["legal_balls"] % 6 == 0:
            inn["striker"], inn["non_striker"] = inn["non_striker"], inn["striker"]
            match["commentary"].append({
                "time": datetime.utcnow().strftime("%H:%M"),
                "ball": f"{over_num + 1}.0",
                "text": f"End of over {over_num + 1}! Score: {inn['runs']}/{inn['wickets']}.",
                "badge": "END OF OVER",
                "type": "over_end"
            })

    elif act_type == "extra":
        raw_extra = (action.get("extra_type") or "wide").lower()
        extra_type = raw_extra[:-1] if raw_extra.endswith("s") and raw_extra not in ["byes"] else raw_extra
        if extra_type in ["no_balls", "noball", "noballs"]:
            extra_type = "no_ball"
        elif extra_type in ["wides", "wideball"]:
            extra_type = "wide"
        elif extra_type in ["byes"]:
            extra_type = "bye"
        elif extra_type in ["leg_byes"]:
            extra_type = "leg_bye"
        elif extra_type in ["penalties"]:
            extra_type = "penalty"

        runs = int(action.get("runs", 1))
        cp["runs"] = cp.get("runs", 0) + runs

        if extra_type in ["wide", "no_ball"]:
            inn["runs"] += runs
            b_stat["runs"] += runs
            inn["extras"][f"{extra_type}s"] += runs
            
            if extra_type == "no_ball":
                score["is_free_hit"] = True
                inn["timeline"].append(f"NB+{runs-1}" if runs > 1 else "NB")
                match["commentary"].append({
                    "time": datetime.utcnow().strftime("%H:%M"),
                    "ball": ball_tag,
                    "text": f"NO-BALL called! {runs} run(s) added. FREE HIT awarded on next delivery!",
                    "badge": "🎯 FREE HIT",
                    "type": "free_hit"
                })
            else:
                inn["timeline"].append(f"Wd+{runs-1}" if runs > 1 else "Wd")
                match["commentary"].append({
                    "time": datetime.utcnow().strftime("%H:%M"),
                    "ball": ball_tag,
                    "text": f"Wide ball by {bowler}. {runs} extra run(s).",
                    "badge": "WIDE",
                    "type": "wide"
                })
        elif extra_type in ["bye", "leg_bye"]:
            inn["runs"] += runs
            inn["legal_balls"] += 1
            s_stat["balls"] += 1
            cp["balls"] = cp.get("balls", 0) + 1
            b_stat["legal_balls"] += 1
            b_stat["overs"] = round((b_stat["legal_balls"] // 6) + (b_stat["legal_balls"] % 6) / 10, 1)
            inn["extras"][f"{extra_type}s"] += runs
            inn["timeline"].append(f"{extra_type[0].upper()}B{runs}")
            score["is_free_hit"] = False

    elif act_type == "wicket":
        dismissal = action.get("dismissal", "bowled")

        inn["wickets"] += 1
        inn["legal_balls"] += 1
        s_stat["balls"] += 1
        s_stat["status"] = f"out ({dismissal} b {bowler})"
        
        if dismissal != "run_out":
            b_stat["wickets"] += 1
        b_stat["legal_balls"] += 1
        b_stat["overs"] = round((b_stat["legal_balls"] // 6) + (b_stat["legal_balls"] % 6) / 10, 1)

        # Record Fall of Wicket (FOW)
        inn.setdefault("fow", []).append({
            "wicket": inn["wickets"],
            "runs": inn["runs"],
            "over": ball_tag,
            "player": striker
        })

        # Record Completed Partnership
        inn.setdefault("partnerships", []).append({
            "wicket": inn["wickets"],
            "runs": cp.get("runs", 0),
            "balls": cp.get("balls", 0),
            "player_1": striker,
            "player_2": non_striker
        })
        inn["current_partnership"] = {"runs": 0, "balls": 0}

        score["is_free_hit"] = False
        inn["timeline"].append("W")

        match["commentary"].append({
            "time": datetime.utcnow().strftime("%H:%M"),
            "ball": ball_tag,
            "text": f"WICKET! {striker} is out! ({dismissal}). Score: {inn['runs']}/{inn['wickets']}.",
            "badge": "WICKET",
            "type": "wicket"
        })

        # Assign new batter if provided
        new_batsman = action.get("new_batsman")
        if new_batsman:
            inn["striker"] = new_batsman
            if new_batsman not in inn["batsmen"]:
                inn["batsmen"][new_batsman] = {"runs": 0, "balls": 0, "fours": 0, "sixes": 0, "sr": "0.0", "status": "not out"}

    elif act_type == "dead_ball":
        special_penalty = action.get("is_special_dead_ball_penalty", False)
        if special_penalty:
            inn["runs"] += 6
            inn["timeline"].append("DEAD+6")
            match["commentary"].append({
                "time": datetime.utcnow().strftime("%H:%M"),
                "ball": ball_tag,
                "text": "DEAD BALL PENALTY: 6 runs awarded to batting team and over must be re-bowled!",
                "badge": "🚨 6 RUNS DEAD BALL",
                "type": "penalty"
            })
        else:
            inn["timeline"].append("DEAD")
            match["commentary"].append({
                "time": datetime.utcnow().strftime("%H:%M"),
                "ball": ball_tag,
                "text": "Dead ball signaled by umpire. Delivery will be re-bowled.",
                "badge": "DEAD BALL",
                "type": "dead_ball"
            })

    elif act_type == "switch_innings":
        score["innings"] = 2
        score["batting_team"], score["bowling_team"] = score["bowling_team"], score["batting_team"]
        score["innings_2"]["target"] = score["innings_1"]["runs"] + 1
        match["commentary"].append({
            "time": datetime.utcnow().strftime("%H:%M"),
            "ball": "0.0",
            "text": f"Innings Break! Target for {match[score['batting_team']]['abbr']} is {score['innings_2']['target']} runs.",
            "badge": "INNINGS BREAK",
            "type": "innings_break"
        })

    # Update overall overs and CRR
    inn["overs"] = round((inn["legal_balls"] // 6) + (inn["legal_balls"] % 6) / 10, 1)
    overs_dec = (inn["legal_balls"] // 6) + (inn["legal_balls"] % 6) / 6.0
    inn["crr"] = f"{(inn['runs'] / overs_dec):.2f}" if overs_dec > 0 else "0.00"

    # Update striker strike rate
    if s_stat.get("balls", 0) > 0:
        s_stat["sr"] = f"{(s_stat['runs'] / s_stat['balls'] * 100):.1f}"
    else:
        s_stat["sr"] = "0.0"

    # Update bowler economy
    b_overs_dec = (b_stat["legal_balls"] // 6) + (b_stat["legal_balls"] % 6) / 6.0
    if b_overs_dec > 0:
        b_stat["econ"] = f"{(b_stat['runs'] / b_overs_dec):.1f}"
    else:
        b_stat["econ"] = "0.0"

    # Dynamic DNB (Did Not Bat) calculation
    bat_team_code = score.get("batting_team", "team_a")
    bat_squad = match.get("squads", {}).get(bat_team_code, {}).get("playing", [])
    batted_names = set(inn.get("batsmen", {}).keys())
    inn["dnb"] = [p.get("name") for p in bat_squad if p.get("name") and p.get("name") not in batted_names]

    # Check Powerplay status (overs 0 to 3)
    if inn["overs"] < score.get("powerplay_overs", 0):
        score["is_powerplay"] = True
    else:
        score["is_powerplay"] = False


def _handle_football_action(match: dict[str, Any], action: dict[str, Any]):
    score = match["score"]
    act = action.get("type")  # goal, card, stat, update_half, shootout_kick
    team = action.get("team", "team_a")
    player = action.get("player", "Player")

    score.setdefault("stats", {
        "team_a": {"shots": 0, "shots_on_target": 0, "corners": 0, "fouls": 0, "yellow_cards": 0, "red_cards": 0, "offsides": 0},
        "team_b": {"shots": 0, "shots_on_target": 0, "corners": 0, "fouls": 0, "yellow_cards": 0, "red_cards": 0, "offsides": 0}
    })

    if act == "goal":
        if team == "team_a":
            score["team_a_score"] += 1
        else:
            score["team_b_score"] += 1
        
        minute = action.get("minute", "25'")
        assist = action.get("assist", "")
        
        score["stats"][team]["shots"] = score["stats"][team].get("shots", 0) + 1
        score["stats"][team]["shots_on_target"] = score["stats"][team].get("shots_on_target", 0) + 1
        score["events"].append({
            "type": "goal",
            "team": team,
            "player": player,
            "assist": assist,
            "minute": minute
        })
        team_abbr = match[team]["abbr"]
        assist_str = f" (Assist: {assist})" if assist else ""
        match["commentary"].append({
            "time": datetime.utcnow().strftime("%H:%M"),
            "ball": f"{minute}",
            "text": f"GOAL! {player} scores for {team_abbr}!{assist_str} Current: {score['team_a_score']} - {score['team_b_score']}",
            "badge": "⚽ GOAL",
            "type": "goal"
        })

    elif act == "card":
        color = action.get("card_color", "yellow")
        minute = action.get("minute", "30'")
        score["stats"][team][f"{color}_cards"] = score["stats"][team].get(f"{color}_cards", 0) + 1
        score["events"].append({"type": f"{color}_card", "team": team, "player": player, "minute": minute})
        badge = "🟨 YELLOW CARD" if color == "yellow" else "🟥 RED CARD"
        match["commentary"].append({
            "time": datetime.utcnow().strftime("%H:%M"),
            "ball": minute,
            "text": f"{badge} shown to {player} ({match[team]['abbr']}).",
            "badge": badge,
            "type": "card"
        })

    elif act == "stat":
        stat_key = action.get("stat_key", "shots")
        delta = int(action.get("delta", 1))
        curr = score["stats"][team].get(stat_key, 0)
        score["stats"][team][stat_key] = max(0, curr + delta)

    elif act == "update_half":
        new_half = int(action.get("half", 2))
        score["half"] = new_half
        period_names = {1: "1st Half", 2: "2nd Half", 3: "Extra Time", 4: "Penalty Shootout"}
        period_label = period_names.get(new_half, f"Period {new_half}")
        score["period_label"] = period_label
        match["commentary"].append({
            "time": datetime.utcnow().strftime("%H:%M"),
            "ball": period_label,
            "text": f"Match Period updated to: {period_label}",
            "badge": "PERIOD",
            "type": "period"
        })

    elif act == "shootout_kick":
        _handle_shootout_action(match, action)


def _handle_shootout_action(match: dict[str, Any], action: dict[str, Any]):
    score = match["score"]
    team = action.get("team", "team_a")
    player = action.get("player", "Shooter")
    result = action.get("result", "goal")  # goal, saved, missed
    
    kick_data = {"player": player, "result": result, "time": datetime.utcnow().strftime("%H:%M")}
    score.setdefault("shootout", {"active": True, "team_a_kicks": [], "team_b_kicks": []})
    
    if team == "team_a":
        score["shootout"].setdefault("team_a_kicks", []).append(kick_data)
        if result == "goal":
            score["team_a_score"] += 1
    else:
        score["shootout"].setdefault("team_b_kicks", []).append(kick_data)
        if result == "goal":
            score["team_b_score"] += 1

    symbol = "⚽ GOAL" if result == "goal" else ("🧤 SAVED" if result == "saved" else "❌ MISSED")
    total_kicks = len(score["shootout"].get("team_a_kicks", [])) + len(score["shootout"].get("team_b_kicks", []))
    match["commentary"].append({
        "time": datetime.utcnow().strftime("%H:%M"),
        "ball": f"P-{total_kicks}",
        "text": f"Penalty kick by {player} ({match[team]['abbr']}): {symbol}! Score: {score['team_a_score']} - {score['team_b_score']}",
        "badge": symbol,
        "type": "penalty"
    })


def _handle_set_sport_action(match: dict[str, Any], action: dict[str, Any]):
    score = match["score"]
    team = action.get("team", "team_a")
    act = action.get("type")
    stype = match.get("sport_type", "badminton")

    # Match target points per set
    if stype == "badminton":
        target = score.get("points_to_win_set") or 21
        cap = 30
    elif stype == "table_tennis":
        target = score.get("points_to_win_set") or 11
        cap = 15
    else:  # volleyball
        target = 15 if score.get("current_set", 1) >= 3 else (score.get("points_to_win_set") or 25)
        cap = 30

    cur_set_idx = max(0, score.get("current_set", 1) - 1)
    if "set_scores" not in score or not score["set_scores"]:
        score["set_scores"] = [{"set": 1, "team_a": 0, "team_b": 0, "winner": None}]
    while cur_set_idx >= len(score["set_scores"]):
        score["set_scores"].append({"set": len(score["set_scores"]) + 1, "team_a": 0, "team_b": 0, "winner": None})
    set_obj = score["set_scores"][cur_set_idx]

    if act == "point":
        delta = int(action.get("delta", 1))
        if delta < 0:
            set_obj[team] = max(0, set_obj.get(team, 0) - 1)
            pts_a = set_obj["team_a"]
            pts_b = set_obj["team_b"]
            match["commentary"].append({
                "time": datetime.utcnow().strftime("%H:%M"),
                "ball": f"S{score['current_set']}",
                "text": f"Point deducted (-1) from {match[team]['abbr']}. Score: {pts_a} - {pts_b}.",
                "badge": "CORRECTION",
                "type": "point_deduct"
            })
        else:
            set_obj[team] = set_obj.get(team, 0) + delta
            score["server"] = team
            pts_a = set_obj["team_a"]
            pts_b = set_obj["team_b"]

            # Deuce check
            if pts_a >= (target - 1) and pts_b >= (target - 1):
                score["in_deuce"] = True
            else:
                score["in_deuce"] = False

            # Check set victory
            if ((pts_a >= target or pts_b >= target) and abs(pts_a - pts_b) >= 2) or (pts_a >= cap or pts_b >= cap):
                winner = "team_a" if pts_a > pts_b else "team_b"
                set_obj["winner"] = winner
                if winner == "team_a":
                    score["sets_team_a"] = score.get("sets_team_a", 0) + 1
                else:
                    score["sets_team_b"] = score.get("sets_team_b", 0) + 1

                w_name = match[winner]["abbr"] if winner in match else winner
                match["commentary"].append({
                    "time": datetime.utcnow().strftime("%H:%M"),
                    "ball": f"Set {score['current_set']}",
                    "text": f"SET {score['current_set']} WON! {w_name} wins Set {score['current_set']} ({pts_a} - {pts_b})!",
                    "badge": "🏆 SET WON",
                    "type": "set_won"
                })

                # Check match completion (first to 2 sets in best of 3)
                if score.get("sets_team_a", 0) >= 2 or score.get("sets_team_b", 0) >= 2:
                    m_win = "team_a" if score.get("sets_team_a", 0) >= 2 else "team_b"
                    match["status"] = "completed"
                    match["winner"] = m_win
                    match["winner_code"] = match[m_win]["code"]
                    match["winner_name"] = match[m_win]["abbr"]
                    match["result"] = f"{match[m_win]['abbr']} won {score['sets_team_a']} - {score['sets_team_b']} sets"
                    match["completed_at"] = datetime.utcnow().isoformat()
                    match["commentary"].append({
                        "time": datetime.utcnow().strftime("%H:%M"),
                        "ball": "FINAL",
                        "text": f"MATCH FINISHED! {match['result']}!",
                        "badge": "🏆 MATCH WON",
                        "type": "match_won"
                    })
                else:
                    score["current_set"] = score.get("current_set", 1) + 1
                    score["set_scores"].append({"set": score["current_set"], "team_a": 0, "team_b": 0, "winner": None})
                    score["in_deuce"] = False
            else:
                match["commentary"].append({
                    "time": datetime.utcnow().strftime("%H:%M"),
                    "ball": f"S{score['current_set']}",
                    "text": f"Point to {match[team]['abbr']}! Current Set: {pts_a} - {pts_b}" + (" (DEUCE)" if score["in_deuce"] else ""),
                    "badge": "POINT",
                    "type": "point"
                })

    elif act == "end_set":
        pts_a = set_obj["team_a"]
        pts_b = set_obj["team_b"]
        winner = action.get("winner")
        if not winner:
            winner = "team_a" if pts_a >= pts_b else "team_b"
        set_obj["winner"] = winner
        if winner == "team_a":
            score["sets_team_a"] = score.get("sets_team_a", 0) + 1
        else:
            score["sets_team_b"] = score.get("sets_team_b", 0) + 1

        w_name = match[winner]["abbr"] if winner in match else winner
        match["commentary"].append({
            "time": datetime.utcnow().strftime("%H:%M"),
            "ball": f"Set {score['current_set']}",
            "text": f"SET FINISHED: {w_name} wins Set {score['current_set']} ({pts_a} - {pts_b})!",
            "badge": "SET WON",
            "type": "set_won"
        })

        if score.get("sets_team_a", 0) >= 2 or score.get("sets_team_b", 0) >= 2:
            m_win = "team_a" if score.get("sets_team_a", 0) >= 2 else "team_b"
            match["status"] = "completed"
            match["winner"] = m_win
            match["winner_code"] = match[m_win]["code"]
            match["winner_name"] = match[m_win]["abbr"]
            match["result"] = f"{match[m_win]['abbr']} won {score['sets_team_a']} - {score['sets_team_b']} sets"
            match["completed_at"] = datetime.utcnow().isoformat()
        else:
            score["current_set"] = score.get("current_set", 1) + 1
            score["set_scores"].append({"set": score["current_set"], "team_a": 0, "team_b": 0, "winner": None})
            score["in_deuce"] = False

    elif act == "swap_server":
        score["server"] = "team_b" if score.get("server") == "team_a" else "team_a"
        match["commentary"].append({
            "time": datetime.utcnow().strftime("%H:%M"),
            "ball": "SERVE",
            "text": f"Server switched: {match[score['server']]['abbr']} now serving.",
            "badge": "SERVICE",
            "type": "serve"
        })

    elif act == "update_players":
        if "players_a" in action:
            score["players_a"] = action["players_a"]
        if "players_b" in action:
            score["players_b"] = action["players_b"]

    elif act == "timeout":
        t_key = f"timeouts_{team[-1]}"
        set_obj[t_key] = set_obj.get(t_key, 0) + 1
        match["commentary"].append({
            "time": datetime.utcnow().strftime("%H:%M"),
            "ball": f"Set {score['current_set']}",
            "text": f"Timeout called by {match[team]['abbr']}.",
            "badge": "⏱️ TIMEOUT",
            "type": "timeout"
        })


def _handle_carrom_action(match: dict[str, Any], action: dict[str, Any]):
    score = match["score"]
    act = action.get("type")
    team = action.get("team", "team_a")

    if act == "points":
        delta = int(action.get("delta", 1))
        target_key = f"score_{team}"
        curr = score.get(target_key, 0)
        score[target_key] = max(0, curr + delta)
        pa = score.get("score_team_a", 0)
        pb = score.get("score_team_b", 0)
        t_name = match[team]["abbr"] if team in match else team

        match["commentary"].append({
            "time": datetime.utcnow().strftime("%H:%M"),
            "ball": f"B{score.get('current_board', 1)}",
            "text": f"{'+' if delta > 0 else ''}{delta} pts to {t_name}! Total: {pa} - {pb}.",
            "badge": "🎯 POINTS",
            "type": "carrom_pts"
        })

        if score.get("score_team_a", 0) >= 29 or score.get("score_team_b", 0) >= 29:
            winner = "team_a" if score.get("score_team_a", 0) >= 29 else "team_b"
            match["status"] = "completed"
            match["winner"] = winner
            match["winner_code"] = match[winner]["code"]
            match["winner_name"] = match[winner]["abbr"]
            match["result"] = f"{match[winner]['abbr']} won the Carrom Match ({score.get('score_team_a')} - {score.get('score_team_b')})!"
            match["completed_at"] = datetime.utcnow().isoformat()

    elif act == "end_board":
        b_num = score.get("current_board", 1)
        score.setdefault("boards", []).append({
            "board": b_num,
            "score_a": score.get("score_team_a", 0),
            "score_b": score.get("score_team_b", 0)
        })
        if b_num >= 8:
            pa = score.get("score_team_a", 0)
            pb = score.get("score_team_b", 0)
            winner = "team_a" if pa > pb else ("team_b" if pb > pa else "draw")
            match["status"] = "completed"
            match["winner"] = winner
            if winner != "draw":
                match["winner_code"] = match[winner]["code"]
                match["winner_name"] = match[winner]["abbr"]
                match["result"] = f"{match[winner]['abbr']} won on 8 boards ({pa} - {pb})!"
            else:
                match["winner_code"] = "draw"
                match["winner_name"] = "Draw"
                match["result"] = f"Match drawn after 8 boards ({pa} - {pb})!"
            match["completed_at"] = datetime.utcnow().isoformat()
        else:
            score["current_board"] = b_num + 1
            match["commentary"].append({
                "time": datetime.utcnow().strftime("%H:%M"),
                "ball": f"Board {b_num}",
                "text": f"Board {b_num} completed. Moving to Board {b_num + 1}.",
                "badge": "NEXT BOARD",
                "type": "board_next"
            })


def _handle_racquet_action(match: dict[str, Any], action: dict[str, Any]):
    _handle_set_sport_action(match, action)


def _handle_tow_action(match: dict[str, Any], action: dict[str, Any]):
    score = match["score"]
    winner = action.get("winner", "team_a")
    pull_num = score["current_pull"]
    duration = action.get("duration", "1m 15s")
    lane_a = action.get("lane_a", "North")
    lane_b = action.get("lane_b", "South")
    cautions_a = int(action.get("cautions_a", 0))
    cautions_b = int(action.get("cautions_b", 0))
    
    if winner == "team_a":
        score["pulls_team_a"] += 1
    else:
        score["pulls_team_b"] += 1

    score.setdefault("pull_history", []).append({
        "pull": pull_num,
        "winner": winner,
        "team_name": match[winner]["abbr"],
        "duration": duration,
        "lane_a": lane_a,
        "lane_b": lane_b,
        "cautions_a": cautions_a,
        "cautions_b": cautions_b
    })

    match["commentary"].append({
        "time": datetime.utcnow().strftime("%H:%M"),
        "ball": f"Pull {pull_num}",
        "text": f"PULL {pull_num} WON! {match[winner]['abbr']} wins in {duration}!",
        "badge": "🪢 PULL WON",
        "type": "pull_won"
    })

    if score["pulls_team_a"] >= 2 or score["pulls_team_b"] >= 2:
        m_winner = "team_a" if score["pulls_team_a"] >= 2 else "team_b"
        match["status"] = "completed"
        match["winner"] = m_winner
        match["winner_code"] = match[m_winner]["code"]
        match["winner_name"] = match[m_winner]["abbr"]
        match["result"] = f"{match[m_winner]['abbr']} won the Tug of War {max(score['pulls_team_a'], score['pulls_team_b'])} - {min(score['pulls_team_a'], score['pulls_team_b'])}!"
        match["completed_at"] = datetime.utcnow().isoformat()
    else:
        score["current_pull"] += 1


def _handle_athletics_action(match: dict[str, Any], action: dict[str, Any]):
    score = match["score"]
    athlete_name = action.get("name") or action.get("player", "Athlete")
    dept = action.get("department") or action.get("team", "AMSC")
    bib = action.get("bib", "")
    attempt_type = action.get("attempt_type", "official")  # trial or official
    dist = float(action.get("distance", 0.0))
    is_foul = bool(action.get("is_foul") or action.get("foul", False))

    # Find or create athlete entry
    score.setdefault("athletes", [])
    ath = next((a for a in score["athletes"] if a["name"] == athlete_name), None)
    if not ath:
        ath = {
            "name": athlete_name,
            "department": dept,
            "bib": bib,
            "trial": None,
            "attempts": [],
            "best": 0.0
        }
        score["athletes"].append(ath)

    if bib and not ath.get("bib"):
        ath["bib"] = bib

    if attempt_type == "trial":
        ath["trial"] = "X" if is_foul else dist
    else:
        val = "X" if is_foul else dist
        ath["attempts"].append(val)
        valid_attempts = [a for a in ath["attempts"] if isinstance(a, (int, float))]
        if valid_attempts:
            ath["best"] = max(valid_attempts)

    # Sort leaderboard by best descending
    score["athletes"].sort(key=lambda x: x.get("best", 0.0), reverse=True)
    for idx, a in enumerate(score["athletes"]):
        a["rank"] = idx + 1

    mark_str = "FOUL (X)" if is_foul else f"{dist}m"
    match["commentary"].append({
        "time": datetime.utcnow().strftime("%H:%M"),
        "ball": f"Attempt {len(ath['attempts'])}",
        "text": f"{athlete_name} ({dept}) marks {mark_str}. Current Best: {ath['best']}m.",
        "badge": "📏 ATTEMPT",
        "type": "attempt"
    })


def _handle_basketball_action(match: dict[str, Any], action: dict[str, Any]):
    score = match["score"]
    team = action.get("team", "team_a")
    player = action.get("player", "Shooter")
    zone = int(action.get("zone", 1))  # 1, 2, or 3 points
    success = bool(action.get("success", False))
    points = zone if success else 0

    shot_entry = {"player": player, "zone": zone, "success": success, "points": points}
    score.setdefault("shots_team_a", [])
    score.setdefault("shots_team_b", [])
    
    # Update individual shooter box score
    sh_dict = score.setdefault(f"shooters_{team[-1]}", {})
    sh = sh_dict.setdefault(player, {
        "1pt_made": 0, "1pt_att": 0,
        "2pt_made": 0, "2pt_att": 0,
        "3pt_made": 0, "3pt_att": 0,
        "total_pts": 0, "pct": "0.0%"
    })
    z_key = f"{zone}pt"
    sh[f"{z_key}_att"] = sh.get(f"{z_key}_att", 0) + 1
    if success:
        sh[f"{z_key}_made"] = sh.get(f"{z_key}_made", 0) + 1
        sh["total_pts"] = sh.get("total_pts", 0) + zone
    tot_att = sh.get("1pt_att", 0) + sh.get("2pt_att", 0) + sh.get("3pt_att", 0)
    tot_made = sh.get("1pt_made", 0) + sh.get("2pt_made", 0) + sh.get("3pt_made", 0)
    sh["pct"] = f"{(tot_made / tot_att * 100):.1f}%" if tot_att > 0 else "0.0%"

    if team == "team_a":
        score["shots_team_a"].append(shot_entry)
        score["score_team_a"] += points
        score["remaining_shots_a"] = max(0, score.get("remaining_shots_a", 30) - 1)
    else:
        score["shots_team_b"].append(shot_entry)
        score["score_team_b"] += points
        score["remaining_shots_b"] = max(0, score.get("remaining_shots_b", 30) - 1)

    result_text = f"+{points} PTS ({zone}-Pt Zone)" if success else "MISSED (0 pts)"
    match["commentary"].append({
        "time": datetime.utcnow().strftime("%H:%M"),
        "ball": f"Shot",
        "text": f"{player} ({match[team]['abbr']}) from {zone}-Point area: {result_text}! Total: {score['score_team_a']} - {score['score_team_b']}",
        "badge": f"{points} PTS" if success else "MISS",
        "type": "basketball_shot"
    })


async def undo_last_action(match_id: str) -> dict[str, Any]:
    async with _lock:
        match = get_match(match_id)
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
        match = get_match(match_id)
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


async def delete_match(match_id: str):
    async with _lock:
        match = _matches_cache.get(match_id)
        sport_id = match.get("sport_id") if match else None
        if match_id in _matches_cache:
            del _matches_cache[match_id]
            _save_matches_to_disk()
            try:
                from database.mongo import delete_match_from_mongo
                delete_match_from_mongo(match_id, sport_id)
            except Exception as e:
                print(f"[Storage] MongoDB match delete error: {e}")


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

