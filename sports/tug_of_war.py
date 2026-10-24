"""
Tug of War Scoring Engine for Department Cup 2026.
Supports Best of 3 pulls, duration, lane tracking, cautions, and match conclusion.
"""

from datetime import datetime
from typing import Any
from sports.base import add_commentary


def init_score(sport_rule: dict[str, Any] = None, max_overs: int = 0) -> dict[str, Any]:
    """Initializes score state for a Tug of War match."""
    return {
        "pulls_team_a": 0,
        "pulls_team_b": 0,
        "current_pull": 1,
        "pulls_to_win": 2,
        "pull_history": []
    }


def handle_action(match: dict[str, Any], action: dict[str, Any]) -> None:
    """Processes pull outcomes, lane choices, cautions, and conclusions for Tug of War."""
    score = match["score"]
    winner = action.get("winner") or action.get("team", "team_a")
    pull_num = score.get("current_pull", 1)
    duration = action.get("duration", "1m 15s")
    lane_a = action.get("lane_a", "North")
    lane_b = action.get("lane_b", "South")
    cautions_a = int(action.get("cautions_a", 0))
    cautions_b = int(action.get("cautions_b", 0))

    if winner == "team_a":
        score["pulls_team_a"] += 1
    else:
        score["pulls_team_b"] += 1

    winner_abbr = match[winner]["abbr"] if winner in match else winner.upper()

    score.setdefault("pull_history", []).append({
        "pull": pull_num,
        "winner": winner,
        "team_name": winner_abbr,
        "duration": duration,
        "lane_a": lane_a,
        "lane_b": lane_b,
        "cautions_a": cautions_a,
        "cautions_b": cautions_b
    })

    add_commentary(
        match,
        ball_or_tag=f"Pull {pull_num}",
        text=f"PULL {pull_num} WON! {winner_abbr} wins in {duration}!",
        badge="🪢 PULL WON",
        comment_type="pull_won"
    )

    if score["pulls_team_a"] >= 2 or score["pulls_team_b"] >= 2:
        m_winner = "team_a" if score["pulls_team_a"] >= 2 else "team_b"
        match["status"] = "completed"
        match["winner"] = m_winner
        match["winner_code"] = match[m_winner]["code"]
        match["winner_name"] = match[m_winner]["abbr"]
        p_max = max(score["pulls_team_a"], score["pulls_team_b"])
        p_min = min(score["pulls_team_a"], score["pulls_team_b"])
        match["result"] = f"{match[m_winner]['abbr']} won the Tug of War {p_max} - {p_min}!"
        match["completed_at"] = datetime.utcnow().isoformat()
        add_commentary(
            match,
            ball_or_tag="FINAL",
            text=f"MATCH COMPLETED! {match['result']}",
            badge="🏆 MATCH WON",
            comment_type="match_won"
        )
    else:
        score["current_pull"] += 1
