"""
Athletics Distance Scoring Engine for Department Cup 2026.
Supports Shot Put, Discus Throw, and Long Jump events for Boys and Girls.
Features trial attempts, official attempts, foul tracking, best mark calculation,
and live leaderboard rank sorting.
"""

from typing import Any
from sports.base import add_commentary


def init_score(sport_rule: dict[str, Any] = None, max_overs: int = 0) -> dict[str, Any]:
    """Initializes score state for an Athletics Distance event."""
    return {
        "athletes": []  # List of {name, department, bib, trial, attempts: [a1, a2, a3], best, rank}
    }


def handle_action(match: dict[str, Any], action: dict[str, Any]) -> None:
    """Processes trial and official distance attempts for Athletics."""
    score = match["score"]
    athlete_name = action.get("name") or action.get("player", "Athlete")
    dept = action.get("department") or action.get("team", "AMSC")
    bib = action.get("bib", "")
    attempt_type = action.get("attempt_type", "official")  # trial or official
    dist = float(action.get("distance", 0.0))
    is_foul = bool(action.get("is_foul") or action.get("foul", False))

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
    add_commentary(
        match,
        ball_or_tag=f"Attempt {len(ath['attempts'])}",
        text=f"{athlete_name} ({dept}) marks {mark_str}. Current Best: {ath['best']}m.",
        badge="📏 ATTEMPT",
        comment_type="attempt"
    )
