"""
Carrom Scoring Engine for Department Cup 2026.
Supports boards 1 to 8, points scoring, queen cover, target of 29 points,
and board breakdown history.
"""

from datetime import datetime
from typing import Any
from sports.base import add_commentary


def init_score(sport_rule: dict[str, Any] = None, max_overs: int = 0) -> dict[str, Any]:
    """Initializes score state for a Carrom match."""
    return {
        "score_team_a": 0,
        "score_team_b": 0,
        "current_board": 1,
        "boards": [],
        "players_a": "",
        "players_b": ""
    }


def handle_action(match: dict[str, Any], action: dict[str, Any]) -> None:
    """Processes board points and end of board for Carrom."""
    score = match["score"]
    act = action.get("type")
    team = action.get("team", "team_a")

    if act in ["point", "points"]:
        delta = int(action.get("delta", 1))
        target_key = f"score_{team}"
        curr = score.get(target_key, 0)
        score[target_key] = max(0, curr + delta)

        pa = score.get("score_team_a", 0)
        pb = score.get("score_team_b", 0)
        t_name = match[team]["abbr"] if team in match else team.upper()

        add_commentary(
            match,
            ball_or_tag=f"B{score.get('current_board', 1)}",
            text=f"{'+' if delta > 0 else ''}{delta} pts to {t_name}! Total: {pa} - {pb}.",
            badge="🎯 POINTS",
            comment_type="carrom_pts"
        )

        if score.get("score_team_a", 0) >= 29 or score.get("score_team_b", 0) >= 29:
            winner = "team_a" if score.get("score_team_a", 0) >= 29 else "team_b"
            match["status"] = "completed"
            match["winner"] = winner
            match["winner_code"] = match[winner]["code"]
            match["winner_name"] = match[winner]["abbr"]
            match["result"] = f"{match[winner]['abbr']} won the Carrom Match ({score.get('score_team_a')} - {score.get('score_team_b')})!"
            match["completed_at"] = datetime.utcnow().isoformat()
            add_commentary(
                match,
                ball_or_tag="FINAL",
                text=f"MATCH COMPLETED! {match['result']}",
                badge="🏆 MATCH WON",
                comment_type="match_won"
            )

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
            add_commentary(
                match,
                ball_or_tag="FINAL",
                text=f"MATCH CONCLUDED! {match['result']}",
                badge="🏆 FINAL",
                comment_type="match_won"
            )
        else:
            score["current_board"] = b_num + 1
            add_commentary(
                match,
                ball_or_tag=f"Board {b_num}",
                text=f"Board {b_num} completed. Moving to Board {b_num + 1}.",
                badge="NEXT BOARD",
                comment_type="board_next"
            )

    elif act == "update_players":
        if "players_a" in action:
            score["players_a"] = action["players_a"]
        if "players_b" in action:
            score["players_b"] = action["players_b"]
