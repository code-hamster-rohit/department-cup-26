"""
Volleyball Scoring Engine for Department Cup 2026.
Supports Best of 3 sets (25 pts for sets 1-2, 15 pts for set 3, win by 2, cap 30),
timeouts, serving team tracking, and match conclusion.
"""

from datetime import datetime
from typing import Any
from sports.base import add_commentary


def init_score(sport_rule: dict[str, Any] = None, max_overs: int = 0) -> dict[str, Any]:
    """Initializes score state for a Volleyball match."""
    return {
        "sets_team_a": 0,
        "sets_team_b": 0,
        "current_set": 1,
        "points_to_win_set": 25,
        "set_scores": [{"set": 1, "team_a": 0, "team_b": 0, "winner": None}],
        "server": "team_a",
        "in_deuce": False,
        "total_points_a": 0,
        "total_points_b": 0,
        "players_a": "",
        "players_b": ""
    }


def handle_action(match: dict[str, Any], action: dict[str, Any]) -> None:
    """Processes point scoring, timeouts, server swaps, and sets for Volleyball."""
    score = match["score"]
    team = action.get("team", "team_a")
    act = action.get("type")

    # Set targets: 25 for sets 1 and 2, 15 for deciding 3rd set
    target = 15 if score.get("current_set", 1) >= 3 else 25
    cap = 30

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
                text=f"Point deducted (-1) from {team_abbr}. Score: {pts_a} - {pts_b}.",
                badge="CORRECTION",
                comment_type="point_deduct"
            )
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

                w_name = match[winner]["abbr"] if winner in match else winner.upper()
                add_commentary(
                    match,
                    ball_or_tag=f"Set {score['current_set']}",
                    text=f"SET {score['current_set']} WON! {w_name} wins Set {score['current_set']} ({pts_a} - {pts_b})!",
                    badge="🏆 SET WON",
                    comment_type="set_won"
                )

                # Check match completion (first to 2 sets in best of 3)
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
                    target_next = 15 if score["current_set"] >= 3 else 25
                    score["points_to_win_set"] = target_next
                    score["set_scores"].append({"set": score["current_set"], "team_a": 0, "team_b": 0, "winner": None})
                    score["in_deuce"] = False
            else:
                add_commentary(
                    match,
                    ball_or_tag=f"S{score['current_set']}",
                    text=f"Point to {team_abbr}! Current Set: {pts_a} - {pts_b}" + (" (DEUCE)" if score["in_deuce"] else ""),
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
            target_next = 15 if score["current_set"] >= 3 else 25
            score["points_to_win_set"] = target_next
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

    elif act == "timeout":
        t_key = f"timeouts_{team[-1]}"
        set_obj[t_key] = set_obj.get(t_key, 0) + 1
        add_commentary(
            match,
            ball_or_tag=f"Set {score['current_set']}",
            text=f"Timeout called by {team_abbr}.",
            badge="⏱️ TIMEOUT",
            comment_type="timeout"
        )
