"""
Table Tennis Scoring Engine for Department Cup 2026.
Supports Best of 3 sets (11 points, win by 2, cap 15 points),
server switches, athlete tracking, deuce, and match conclusion.
"""

from datetime import datetime
from typing import Any
from sports.base import add_commentary


def init_score(sport_rule: dict[str, Any] = None, max_overs: int = 0) -> dict[str, Any]:
    """Initializes score state for a Table Tennis match."""
    return {
        "sets_team_a": 0,
        "sets_team_b": 0,
        "current_set": 1,
        "points_to_win_set": 11,
        "set_scores": [{"set": 1, "team_a": 0, "team_b": 0, "winner": None}],
        "server": "team_a",
        "in_deuce": False,
        "total_points_a": 0,
        "total_points_b": 0,
        "players_a": "",
        "players_b": ""
    }


def handle_action(match: dict[str, Any], action: dict[str, Any]) -> None:
    """Processes point scoring, server rotation, and sets for Table Tennis."""
    score = match["score"]
    team = action.get("team", "team_a")
    act = action.get("type")

    target = score.get("points_to_win_set") or 11
    cap = 15

    cur_set_idx = max(0, score.get("current_set", 1) - 1)
    if "set_scores" not in score or not score["set_scores"]:
        score["set_scores"] = [{"set": 1, "team_a": 0, "team_b": 0, "winner": None}]
    while cur_set_idx >= len(score["set_scores"]):
        score["set_scores"].append({"set": len(score["set_scores"]) + 1, "team_a": 0, "team_b": 0, "winner": None})
    set_obj = score["set_scores"][cur_set_idx]

    team_abbr = match[team]["abbr"] if team in match else team.upper()

    if act == "point":
        delta = int(action.get("delta", 1))
        if delta < 0:
            set_obj[team] = max(0, set_obj.get(team, 0) - 1)
            pts_a = set_obj["team_a"]
            pts_b = set_obj["team_b"]
            add_commentary(
                match,
                ball_or_tag=f"S{score['current_set']}",
                text=f"Point corrected (-1) for {team_abbr}. Score: {pts_a} - {pts_b}.",
                badge="CORRECTION",
                comment_type="point_deduct"
            )
        else:
            set_obj[team] = set_obj.get(team, 0) + delta
            pts_a = set_obj["team_a"]
            pts_b = set_obj["team_b"]

            # Table tennis server rotation (every 2 points, or every 1 point on deuce)
            total_pts = pts_a + pts_b
            if pts_a >= 10 and pts_b >= 10:
                score["in_deuce"] = True
                score["server"] = "team_b" if score.get("server") == "team_a" else "team_a"
            else:
                score["in_deuce"] = False
                if total_pts % 2 == 0:
                    score["server"] = "team_b" if score.get("server") == "team_a" else "team_a"

            # Check set victory
            if ((pts_a >= target or pts_b >= target) and abs(pts_a - pts_b) >= 2) or (pts_a >= cap or pts_b >= cap):
                winner = "team_a" if pts_a > pts_b else "team_b"
                set_obj["winner"] = winner
                if winner == "team_a":
                    score["sets_team_a"] = score.get("sets_team_a", 0) + 1
                else:
                    score["sets_team_b"] = score.get("sets_team_b", 0) + 1

                w_name = match[winner]["abbr"] if winner in match else winner.upper()
                add_commentary(
                    match,
                    ball_or_tag=f"Set {score['current_set']}",
                    text=f"SET {score['current_set']} WON! {w_name} wins Set {score['current_set']} ({pts_a} - {pts_b})!",
                    badge="🏆 SET WON",
                    comment_type="set_won"
                )

                if score.get("sets_team_a", 0) >= 2 or score.get("sets_team_b", 0) >= 2:
                    m_win = "team_a" if score.get("sets_team_a", 0) >= 2 else "team_b"
                    match["status"] = "completed"
                    match["winner"] = m_win
                    match["winner_code"] = match[m_win]["code"]
                    match["winner_name"] = match[m_win]["abbr"]
                    match["result"] = f"{match[m_win]['abbr']} won {score['sets_team_a']} - {score['sets_team_b']} sets"
                    match["completed_at"] = datetime.utcnow().isoformat()
                    add_commentary(
                        match,
                        ball_or_tag="FINAL",
                        text=f"MATCH FINISHED! {match['result']}!",
                        badge="🏆 MATCH WON",
                        comment_type="match_won"
                    )
                else:
                    score["current_set"] = score.get("current_set", 1) + 1
                    score["set_scores"].append({"set": score["current_set"], "team_a": 0, "team_b": 0, "winner": None})
                    score["in_deuce"] = False
            else:
                add_commentary(
                    match,
                    ball_or_tag=f"S{score['current_set']}",
                    text=f"Point to {team_abbr}! Set {score['current_set']}: {pts_a} - {pts_b}" + (" (DEUCE)" if score["in_deuce"] else ""),
                    badge="POINT",
                    comment_type="point"
                )

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

        w_name = match[winner]["abbr"] if winner in match else winner.upper()
        add_commentary(
            match,
            ball_or_tag=f"Set {score['current_set']}",
            text=f"SET FINISHED: {w_name} wins Set {score['current_set']} ({pts_a} - {pts_b})!",
            badge="SET WON",
            comment_type="set_won"
        )

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
        server_abbr = match[score["server"]]["abbr"] if score["server"] in match else score["server"].upper()
        add_commentary(
            match,
            ball_or_tag="SERVE",
            text=f"Server switched: {server_abbr} now serving.",
            badge="SERVICE",
            comment_type="serve"
        )

    elif act == "update_players":
        if "players_a" in action:
            score["players_a"] = action["players_a"]
        if "players_b" in action:
            score["players_b"] = action["players_b"]
