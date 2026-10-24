"""
Football and Penalty Shootout Scoring Engine for Department Cup 2026.
Supports goals with assist tracking, cards, in-depth match stats, periods, and shootout kicks.
"""

from typing import Any
from sports.base import add_commentary


def init_score(sport_rule: dict[str, Any], max_overs: int = 0) -> dict[str, Any]:
    """Initializes score state for Football and Penalty Shootout matches."""
    stype = sport_rule.get("sport_type")
    if stype == "penalty_shootout":
        return {
            "team_a_score": 0,
            "team_b_score": 0,
            "shots_per_player": 5,
            "team_a_kicks": [],
            "team_b_kicks": [],
            "current_shooter_index": 0,
            "sudden_death": False
        }

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


def handle_action(match: dict[str, Any], action: dict[str, Any]) -> None:
    """Processes scoring, disciplinary, and stats events for Football matches."""
    score = match["score"]
    act = action.get("type")  # goal, card, stat, update_half, shootout_kick, kick
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
        score.setdefault("events", []).append({
            "type": "goal",
            "team": team,
            "player": player,
            "assist": assist,
            "minute": minute
        })
        team_abbr = match[team]["abbr"] if team in match else team.upper()
        assist_str = f" (Assist: {assist})" if assist else ""
        add_commentary(
            match,
            ball_or_tag=str(minute),
            text=f"GOAL! {player} scores for {team_abbr}!{assist_str} Current: {score['team_a_score']} - {score['team_b_score']}",
            badge="⚽ GOAL",
            comment_type="goal"
        )

    elif act == "card":
        color = action.get("card_color", "yellow")
        minute = action.get("minute", "30'")
        score["stats"][team][f"{color}_cards"] = score["stats"][team].get(f"{color}_cards", 0) + 1
        score.setdefault("events", []).append({"type": f"{color}_card", "team": team, "player": player, "minute": minute})
        badge = "🟨 YELLOW CARD" if color == "yellow" else "🟥 RED CARD"
        team_abbr = match[team]["abbr"] if team in match else team.upper()
        add_commentary(
            match,
            ball_or_tag=str(minute),
            text=f"{badge} shown to {player} ({team_abbr}).",
            badge=badge,
            comment_type="card"
        )

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
        add_commentary(
            match,
            ball_or_tag=period_label,
            text=f"Match Period updated to: {period_label}",
            badge="PERIOD",
            comment_type="period"
        )

    elif act in ["shootout_kick", "kick"]:
        handle_shootout_kick(match, action)


def handle_shootout_kick(match: dict[str, Any], action: dict[str, Any]) -> None:
    """Handles penalty shootout kicks for tie-breaks or Girls shootout matches."""
    score = match["score"]
    team = action.get("team", "team_a")
    player = action.get("player", "Shooter")
    result = action.get("result", "goal")  # goal, saved, missed

    from sports.base import current_time_str
    kick_data = {"player": player, "result": result, "time": current_time_str()}

    if "shootout" in score:
        so = score["shootout"]
    else:
        so = score

    so.setdefault("team_a_kicks", [])
    so.setdefault("team_b_kicks", [])

    if team == "team_a":
        so["team_a_kicks"].append(kick_data)
        if result == "goal":
            score["team_a_score"] += 1
    else:
        so["team_b_kicks"].append(kick_data)
        if result == "goal":
            score["team_b_score"] += 1

    symbol = "⚽ GOAL" if result == "goal" else ("🧤 SAVED" if result == "saved" else "❌ MISSED")
    total_kicks = len(so["team_a_kicks"]) + len(so["team_b_kicks"])
    team_abbr = match[team]["abbr"] if team in match else team.upper()

    add_commentary(
        match,
        ball_or_tag=f"P-{total_kicks}",
        text=f"Penalty kick by {player} ({team_abbr}): {symbol}! Score: {score['team_a_score']} - {score['team_b_score']}",
        badge=symbol,
        comment_type="penalty"
    )
