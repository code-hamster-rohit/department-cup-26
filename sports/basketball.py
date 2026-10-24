"""
Basketball Shootout Scoring Engine for Department Cup 2026.
Supports department shootout challenges with 1pt, 2pt, and 3pt zones,
individual shooter box scores, shooting percentages, and cumulative team scores.
"""

from typing import Any
from sports.base import add_commentary


def init_score(sport_rule: dict[str, Any] = None, max_overs: int = 0) -> dict[str, Any]:
    """Initializes score state for a Basketball Shootout match."""
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


def handle_action(match: dict[str, Any], action: dict[str, Any]) -> None:
    """Processes shots taken from 1pt, 2pt, and 3pt zones for Basketball."""
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
    team_abbr = match[team]["abbr"] if team in match else team.upper()
    add_commentary(
        match,
        ball_or_tag="Shot",
        text=f"{player} ({team_abbr}) from {zone}-Point area: {result_text}! Total: {score['score_team_a']} - {score['score_team_b']}",
        badge=f"{points} PTS" if success else "MISS",
        comment_type="basketball_shot"
    )
