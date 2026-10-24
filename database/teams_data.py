"""
Repository and loader for registered Department Cup teams and rosters.
Loads live roster data from departments JSON exports and provides defaults.
"""

import os
import json
from typing import Any

# Department specifications
DEPARTMENTS = {
    "amsc": {
        "code": "amsc",
        "abbr": "AMSC",
        "name": "Applied Mathematics & Scientific Computing",
        "color": "#3b82f6",
        "badge_bg": "rgba(59, 130, 246, 0.15)",
        "badge_border": "rgba(59, 130, 246, 0.4)",
        "icon": "📐"
    },
    "ppe": {
        "code": "ppe",
        "abbr": "PPE",
        "name": "Polymer & Process Engineering",
        "color": "#10b981",
        "badge_bg": "rgba(16, 185, 129, 0.15)",
        "badge_border": "rgba(16, 185, 129, 0.4)",
        "icon": "🧪"
    },
    "ppt": {
        "code": "ppt",
        "abbr": "PPT",
        "name": "Pulp & Paper Technology",
        "color": "#f59e0b",
        "badge_bg": "rgba(245, 158, 11, 0.15)",
        "badge_border": "rgba(245, 158, 11, 0.4)",
        "icon": "📜"
    }
}


def load_registered_department_rosters() -> dict[str, dict[str, Any]]:
    """
    Scans for departments.amsc.json, departments.ppe.json, departments.ppt.json
    and returns a structured map:
    {
       "amsc": { "shotput_girls": { "captain": ..., "main_players": [...], "substitutes": [...] }, ... },
       "ppe": { ... },
       "ppt": { ... }
    }
    """
    rosters: dict[str, dict[str, Any]] = {"amsc": {}, "ppe": {}, "ppt": {}}
    
    # Candidate search paths
    base_dirs = [
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),  # department-cup
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),  # e:\projects
        r"E:\projects"
    ]

    for dept_code in ["amsc", "ppe", "ppt"]:
        filename = f"departments.{dept_code}.json"
        found_path = None
        for b_dir in base_dirs:
            candidate = os.path.join(b_dir, filename)
            if os.path.isfile(candidate):
                found_path = candidate
                break

        if not found_path:
            continue

        try:
            with open(found_path, "r", encoding="utf-8") as f:
                docs = json.load(f)
                for doc in docs:
                    sport_id = doc.get("_id")
                    if not sport_id or sport_id == "events":
                        continue

                    # Each doc might have a teams array or direct sport key
                    team_info = None
                    if "teams" in doc and isinstance(doc["teams"], list) and len(doc["teams"]) > 0:
                        team_info = doc["teams"][0]
                    elif sport_id in doc and isinstance(doc[sport_id], list) and len(doc[sport_id]) > 0:
                        team_info = doc[sport_id][0]

                    if team_info:
                        captain = team_info.get("captain", {})
                        main_players = team_info.get("main_players", [])
                        subs = team_info.get("substitutes", [])
                        rosters[dept_code][sport_id] = {
                            "team_id": team_info.get("team_id"),
                            "department": dept_code.upper(),
                            "department_code": dept_code,
                            "captain": captain,
                            "main_players": main_players,
                            "substitutes": subs,
                            "total_playing": team_info.get("total_playing", len(main_players) + (1 if captain else 0)),
                            "total_substitutes": team_info.get("total_substitutes", len(subs))
                        }
        except Exception as e:
            print(f"Warning: Failed loading {found_path}: {e}")

    return rosters


def get_default_squad(dept_code: str, sport_id: str, sport_cfg: dict[str, Any], category: str | None = None) -> dict[str, Any]:
    """
    Returns the real registered squad if available from json,
    matching the sport and gender category (Boys, Girls, Mixed).
    """
    all_rosters = load_registered_department_rosters()
    dept_rosters = all_rosters.get(dept_code.lower(), {})
    
    cat_lower = (category or "").lower().strip()
    sid_lower = sport_id.lower().strip()
    
    candidates = []
    
    # 1. Target gender-specific keys first if category is provided
    if "girl" in cat_lower or cat_lower == "girls":
        gender_keys = {
            "shotput": ["shotput_girls"],
            "discuss_throw": ["discus_girls"],
            "long_jump": ["long_jump_girls"],
            "tug_of_war": ["tow_girls"],
            "box_cricket": ["box_cricket_girls"],
            "football": ["football_girls"],
            "cricket": ["cricket_girls", "box_cricket_girls"],
        }
        candidates.extend(gender_keys.get(sid_lower, [f"{sid_lower}_girls"]))
    elif "boy" in cat_lower or cat_lower == "boys":
        gender_keys = {
            "cricket": ["cricket_boys"],
            "football": ["football_boys"],
            "volleyball": ["volleyball_boys"],
            "table_tennis": ["tt_boys"],
            "tug_of_war": ["tow_boys"],
            "shotput": ["shotput_boys"],
            "discuss_throw": ["discus_boys"],
            "long_jump": ["long_jump_boys"],
        }
        candidates.extend(gender_keys.get(sid_lower, [f"{sid_lower}_boys"]))
    elif "mix" in cat_lower or cat_lower == "mixed":
        mixed_keys = {
            "badminton": ["badminton_mix"],
            "carrom": ["carrom_mix"],
            "basketball": ["basketball_shootout"],
        }
        candidates.extend(mixed_keys.get(sid_lower, [f"{sid_lower}_mix"]))

    # 2. General aliases
    candidates.append(sid_lower)
    alias_map = {
        "badminton": ["badminton_mix"],
        "cricket": ["cricket_boys", "box_cricket_girls"],
        "box_cricket": ["box_cricket_girls"],
        "football": ["football_boys", "football_girls"],
        "volleyball": ["volleyball_boys"],
        "table_tennis": ["tt_boys"],
        "carrom": ["carrom_mix"],
        "tug_of_war": ["tow_boys", "tow_girls"],
        "shotput": ["shotput_boys", "shotput_girls"],
        "discuss_throw": ["discus_boys", "discus_girls", "discus_throw"],
        "long_jump": ["long_jump_boys", "long_jump_girls"],
        "basketball": ["basketball_shootout"]
    }
    for a in alias_map.get(sid_lower, []):
        if a not in candidates:
            candidates.append(a)

    matched_key = next((c for c in candidates if c in dept_rosters), None)
    
    if matched_key:
        saved = dept_rosters[matched_key]
        playing_list = []
        if saved.get("captain"):
            cap = dict(saved["captain"])
            cap["is_captain"] = True
            playing_list.append(cap)
        for p in saved.get("main_players", []):
            p_dict = dict(p)
            p_dict["is_captain"] = False
            playing_list.append(p_dict)
            
        return {
            "department": dept_code.upper(),
            "department_code": dept_code.lower(),
            "captain": saved.get("captain", {}).get("name", "Captain"),
            "playing": playing_list,
            "substitutes": saved.get("substitutes", [])
        }

    # Generate standard template for that sport rule
    squad_cfg = sport_cfg.get("squad", {})
    playing_count = squad_cfg.get("playing_count", 11)
    max_subs = squad_cfg.get("max_substitutes", 4)
    dept_name = DEPARTMENTS.get(dept_code.lower(), {}).get("abbr", dept_code.upper())
    
    playing = []
    for i in range(1, playing_count + 1):
        is_cap = (i == 1)
        role = "Captain" if is_cap else f"Player {i}"
        playing.append({
            "name": f"{dept_name} {role}",
            "student_id": f"2692{i:04d}",
            "role": role,
            "is_captain": is_cap
        })
        
    subs = []
    for j in range(1, min(max_subs + 1, 4)):
        subs.append({
            "name": f"{dept_name} Sub {j}",
            "student_id": f"2693{j:04d}",
            "role": f"Substitute {j}",
            "is_captain": False
        })

    return {
        "department": dept_name,
        "department_code": dept_code.lower(),
        "captain": f"{dept_name} Captain",
        "playing": playing,
        "substitutes": subs
    }
