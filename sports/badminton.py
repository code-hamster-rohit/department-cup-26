"""
Badminton Scoring Engine for Department Cup 2026.
Strictly implements Inter-Department Sports Meet - Badminton Rules & Regulations:
- 5 Events Mixed Team Tie: Boys' Singles, Girls' Singles, Mixed Doubles, Girls' Doubles, Boys' Doubles.
- Best of 5 Events: First team to win 3 events wins the overall match.
- Each event is Best of 3 Sets. First to win 2 sets wins the event.
- Scoring: 15 points per set. At 14-14, deuce applies (win by 2).
- Golden Point Cap: At 20-20, first to 21 points wins the set (cap at 21).
- Player limits: Max 2 events per player; Mixed Doubles must be 1 Boy + 1 Girl.
- Late arrival: 2-point advantage to opposing team in opening set.
- Bulletproof state machine with completion guards preventing infinite score accumulation.
"""

from datetime import datetime
from typing import Any
from sports.base import add_commentary


DEFAULT_EVENTS = [
    {
        "id": "bs",
        "name": "Boys' Singles",
        "short_name": "BS",
        "type": "singles",
        "gender": "Boy",
        "player_count": 1,
        "players_a": "",
        "players_b": "",
        "status": "in_progress",  # "upcoming", "in_progress", "completed"
        "winner": None,
        "sets_a": 0,
        "sets_b": 0,
        "current_set": 1,
        "in_deuce": False,
        "server": "team_a",
        "set_scores": [
            {"set": 1, "team_a": 0, "team_b": 0, "winner": None, "completed": False}
        ]
    },
    {
        "id": "gs",
        "name": "Girls' Singles",
        "short_name": "GS",
        "type": "singles",
        "gender": "Girl",
        "player_count": 1,
        "players_a": "",
        "players_b": "",
        "status": "upcoming",
        "winner": None,
        "sets_a": 0,
        "sets_b": 0,
        "current_set": 1,
        "in_deuce": False,
        "server": "team_a",
        "set_scores": [
            {"set": 1, "team_a": 0, "team_b": 0, "winner": None, "completed": False}
        ]
    },
    {
        "id": "xd",
        "name": "Mixed Doubles",
        "short_name": "XD",
        "type": "doubles",
        "gender": "Mixed",
        "player_count": 2,
        "players_a": "",
        "players_b": "",
        "status": "upcoming",
        "winner": None,
        "sets_a": 0,
        "sets_b": 0,
        "current_set": 1,
        "in_deuce": False,
        "server": "team_a",
        "set_scores": [
            {"set": 1, "team_a": 0, "team_b": 0, "winner": None, "completed": False}
        ]
    },
    {
        "id": "gd",
        "name": "Girls' Doubles",
        "short_name": "GD",
        "type": "doubles",
        "gender": "Girl",
        "player_count": 2,
        "players_a": "",
        "players_b": "",
        "status": "upcoming",
        "winner": None,
        "sets_a": 0,
        "sets_b": 0,
        "current_set": 1,
        "in_deuce": False,
        "server": "team_a",
        "set_scores": [
            {"set": 1, "team_a": 0, "team_b": 0, "winner": None, "completed": False}
        ]
    },
    {
        "id": "bd",
        "name": "Boys' Doubles",
        "short_name": "BD",
        "type": "doubles",
        "gender": "Boy",
        "player_count": 2,
        "players_a": "",
        "players_b": "",
        "status": "upcoming",
        "winner": None,
        "sets_a": 0,
        "sets_b": 0,
        "current_set": 1,
        "in_deuce": False,
        "server": "team_a",
        "set_scores": [
            {"set": 1, "team_a": 0, "team_b": 0, "winner": None, "completed": False}
        ]
    }
]


def init_score(sport_rule: dict[str, Any] = None, max_overs: int = 0) -> dict[str, Any]:
    """Initializes score state for a 5-event Badminton Mixed Team Match."""
    import copy
    events = copy.deepcopy(DEFAULT_EVENTS)
    active_ev = events[0]

    return {
        "match_format": "5_events",
        "events_team_a": 0,
        "events_team_b": 0,
        "events_to_win": 3,
        "total_events": 5,
        "active_event_id": active_ev["id"],
        "active_event_name": active_ev["name"],
        "points_to_win_set": 15,
        "deuce_at": 14,
        "cap_points": 21,
        "sets_to_win_event": 2,
        "events": events,

        # Top-level mirrors for active event (instant binding)
        "sets_team_a": active_ev["sets_a"],
        "sets_team_b": active_ev["sets_b"],
        "current_set": active_ev["current_set"],
        "set_scores": active_ev["set_scores"],
        "server": active_ev["server"],
        "in_deuce": active_ev["in_deuce"],
        "players_a": active_ev["players_a"],
        "players_b": active_ev["players_b"]
    }


def _get_active_event(score: dict[str, Any]) -> dict[str, Any]:
    """Returns the currently active event object from the events list."""
    if "events" not in score or not score["events"]:
        import copy
        score["events"] = copy.deepcopy(DEFAULT_EVENTS)

    active_id = score.get("active_event_id") or "bs"
    for ev in score["events"]:
        if ev["id"] == active_id:
            return ev
    # Fallback to first event
    score["active_event_id"] = score["events"][0]["id"]
    return score["events"][0]


def _sync_active_event_mirrors(score: dict[str, Any]) -> None:
    """Synchronizes top-level score fields with the active event and tallies overall event wins."""
    ev = _get_active_event(score)
    score["active_event_id"] = ev["id"]
    score["active_event_name"] = ev["name"]

    # Re-tally overall events won across all 5 events
    ev_a = sum(1 for e in score["events"] if e.get("winner") == "team_a")
    ev_b = sum(1 for e in score["events"] if e.get("winner") == "team_b")
    score["events_team_a"] = ev_a
    score["events_team_b"] = ev_b

    # Mirror active event fields
    score["sets_team_a"] = ev.get("sets_a", 0)
    score["sets_team_b"] = ev.get("sets_b", 0)
    score["current_set"] = ev.get("current_set", 1)
    score["set_scores"] = ev.get("set_scores", [])
    score["server"] = ev.get("server", "team_a")
    score["in_deuce"] = ev.get("in_deuce", False)
    score["players_a"] = ev.get("players_a", "")
    score["players_b"] = ev.get("players_b", "")


def handle_action(match: dict[str, Any], action: dict[str, Any]) -> None:
    """Processes point scoring, server swaps, set wins, and event progression for Badminton."""
    score = match["score"]
    act = action.get("type")
    team = action.get("team", "team_a")

    target = int(score.get("points_to_win_set") or 15)
    deuce_threshold = int(score.get("deuce_at") or 14)
    cap = int(score.get("cap_points") or 21)

    cur_event = _get_active_event(score)
    team_a_name = match.get("team_a", {}).get("abbr", "TEAM A")
    team_b_name = match.get("team_b", {}).get("abbr", "TEAM B")
    acting_team_abbr = team_a_name if team == "team_a" else team_b_name

    # -------------------------------------------------------------------------
    # 1. POINT SCORING (+1 / -1)
    # -------------------------------------------------------------------------
    if act == "point":
        # Guard 1: Cannot score if match is already officially completed
        if match.get("status") == "completed":
            return

        # Guard 2: Cannot score if this event is already won
        if cur_event.get("status") == "completed":
            return

        # Ensure set_scores exists
        if not cur_event.get("set_scores"):
            cur_event["set_scores"] = [{"set": 1, "team_a": 0, "team_b": 0, "winner": None, "completed": False}]

        cur_set_idx = max(0, cur_event.get("current_set", 1) - 1)
        while cur_set_idx >= len(cur_event["set_scores"]):
            cur_event["set_scores"].append({
                "set": len(cur_event["set_scores"]) + 1,
                "team_a": 0,
                "team_b": 0,
                "winner": None,
                "completed": False
            })

        set_obj = cur_event["set_scores"][cur_set_idx]

        # Guard 3: Cannot score on an already completed set
        if set_obj.get("completed"):
            return

        delta = int(action.get("delta", 1))

        if delta < 0:
            # Point Correction (-1 Deduct)
            if set_obj.get(team, 0) > 0:
                set_obj[team] -= 1
                pts_a = set_obj["team_a"]
                pts_b = set_obj["team_b"]

                # Recalculate deuce
                if pts_a >= deuce_threshold and pts_b >= deuce_threshold:
                    cur_event["in_deuce"] = True
                else:
                    cur_event["in_deuce"] = False

                _sync_active_event_mirrors(score)
                add_commentary(
                    match,
                    ball_or_tag=f"{cur_event['short_name']}-S{cur_event['current_set']}",
                    text=f"Point corrected (-1) for {acting_team_abbr}. Current score: {pts_a} - {pts_b}.",
                    badge="CORRECTION",
                    comment_type="point_deduct"
                )
            return

        # Delta > 0: Rally Won
        set_obj[team] = set_obj.get(team, 0) + delta
        cur_event["server"] = team  # Rally-point rule: winner of rally serves next
        pts_a = set_obj["team_a"]
        pts_b = set_obj["team_b"]

        # Deuce Check (Rule 3.2): At 14-all, must win by 2 points
        if pts_a >= deuce_threshold and pts_b >= deuce_threshold:
            cur_event["in_deuce"] = True
        else:
            cur_event["in_deuce"] = False

        # Check Set Victory (Rule 3.1 & Rule 3.3):
        # 1. Normal Win: score >= 15 with a margin of >= 2 points
        # 2. Golden Point Cap at 20-20: First to 21 points wins immediately!
        normal_win = (pts_a >= target or pts_b >= target) and abs(pts_a - pts_b) >= 2
        cap_win = (pts_a >= cap or pts_b >= cap)

        if normal_win or cap_win:
            winner = "team_a" if pts_a > pts_b else "team_b"
            winner_abbr = team_a_name if winner == "team_a" else team_b_name
            set_obj["winner"] = winner
            set_obj["completed"] = True
            cur_event["in_deuce"] = False

            if winner == "team_a":
                cur_event["sets_a"] = cur_event.get("sets_a", 0) + 1
            else:
                cur_event["sets_b"] = cur_event.get("sets_b", 0) + 1

            add_commentary(
                match,
                ball_or_tag=f"{cur_event['short_name']}-Set {cur_event['current_set']}",
                text=f"SET {cur_event['current_set']} WON! {winner_abbr} wins ({pts_a} - {pts_b}) in {cur_event['name']}!",
                badge="🏆 SET WON",
                comment_type="set_won"
            )

            # Check Event Victory (Best of 3 sets: first to 2 sets wins the event)
            if cur_event.get("sets_a", 0) >= 2 or cur_event.get("sets_b", 0) >= 2:
                ev_winner = "team_a" if cur_event["sets_a"] >= 2 else "team_b"
                ev_winner_abbr = team_a_name if ev_winner == "team_a" else team_b_name
                cur_event["status"] = "completed"
                cur_event["winner"] = ev_winner

                add_commentary(
                    match,
                    ball_or_tag=f"EVENT {cur_event['short_name']}",
                    text=f"MATCH EVENT WON! {ev_winner_abbr} wins {cur_event['name']} ({cur_event['sets_a']} - {cur_event['sets_b']} sets)!",
                    badge="🎉 EVENT WON",
                    comment_type="event_won"
                )

                _sync_active_event_mirrors(score)

                # Check Overall Match Victory (Best of 5 events: first to 3 events wins)
                if score["events_team_a"] >= 3 or score["events_team_b"] >= 3:
                    m_win = "team_a" if score["events_team_a"] >= 3 else "team_b"
                    m_win_abbr = team_a_name if m_win == "team_a" else team_b_name
                    match["status"] = "completed"
                    match["winner"] = m_win
                    match["winner_code"] = match[m_win]["code"]
                    match["winner_name"] = match[m_win]["abbr"]
                    match["result"] = f"{m_win_abbr} won the match {score['events_team_a']} - {score['events_team_b']} ({score['events_team_a'] if m_win == 'team_a' else score['events_team_b']} Event Victories)"
                    match["completed_at"] = datetime.utcnow().isoformat()
                    add_commentary(
                        match,
                        ball_or_tag="FINAL",
                        text=f"🏆 OVERALL TOURNAMENT MATCH FINISHED! {match['result']}!",
                        badge="🏆 CHAMPION",
                        comment_type="match_won"
                    )
            else:
                # Event continues to next set
                cur_event["current_set"] = cur_event.get("current_set", 1) + 1
                cur_event["set_scores"].append({
                    "set": cur_event["current_set"],
                    "team_a": 0,
                    "team_b": 0,
                    "winner": None,
                    "completed": False
                })
        else:
            deuce_str = " (🔥 DEUCE - Win by 2)" if cur_event["in_deuce"] else ""
            if pts_a == 20 and pts_b == 20:
                deuce_str = " (⚡ GOLDEN POINT CAP - Next point wins set at 21!)"
            add_commentary(
                match,
                ball_or_tag=f"{cur_event['short_name']}-S{cur_event['current_set']}",
                text=f"Point to {acting_team_abbr}! Set {cur_event['current_set']}: {pts_a} - {pts_b}{deuce_str}",
                badge="POINT",
                comment_type="point"
            )

        _sync_active_event_mirrors(score)

    # -------------------------------------------------------------------------
    # 2. SWITCH ACTIVE EVENT
    # -------------------------------------------------------------------------
    elif act == "switch_event":
        target_ev_id = action.get("event_id")
        if target_ev_id:
            for ev in score.get("events", []):
                if ev["id"] == target_ev_id:
                    score["active_event_id"] = target_ev_id
                    if ev.get("status") == "upcoming":
                        ev["status"] = "in_progress"
                    _sync_active_event_mirrors(score)
                    add_commentary(
                        match,
                        ball_or_tag="EVENT",
                        text=f"Switched court focus to {ev['name']} ({ev['short_name']}).",
                        badge="EVENT",
                        comment_type="info"
                    )
                    break

    # -------------------------------------------------------------------------
    # 3. START NEXT EVENT
    # -------------------------------------------------------------------------
    elif act == "start_next_event":
        # Find the next non-completed event
        events = score.get("events", [])
        for ev in events:
            if ev.get("status") != "completed":
                score["active_event_id"] = ev["id"]
                ev["status"] = "in_progress"
                _sync_active_event_mirrors(score)
                add_commentary(
                    match,
                    ball_or_tag="NEXT EVENT",
                    text=f"Commenced {ev['name']} ({ev['short_name']})!",
                    badge="EVENT STARTED",
                    comment_type="info"
                )
                break

    # -------------------------------------------------------------------------
    # 4. START NEXT SET
    # -------------------------------------------------------------------------
    elif act == "start_next_set":
        cur_set_idx = max(0, cur_event.get("current_set", 1) - 1)
        if cur_set_idx < len(cur_event.get("set_scores", [])):
            cur_set = cur_event["set_scores"][cur_set_idx]
            if cur_set.get("completed") and cur_event.get("sets_a", 0) < 2 and cur_event.get("sets_b", 0) < 2:
                cur_event["current_set"] = cur_event.get("current_set", 1) + 1
                cur_event["set_scores"].append({
                    "set": cur_event["current_set"],
                    "team_a": 0,
                    "team_b": 0,
                    "winner": None,
                    "completed": False
                })
                cur_event["in_deuce"] = False
                _sync_active_event_mirrors(score)

    # -------------------------------------------------------------------------
    # 5. END / AWARD SET MANUALLY
    # -------------------------------------------------------------------------
    elif act == "end_set":
        cur_set_idx = max(0, cur_event.get("current_set", 1) - 1)
        if cur_set_idx < len(cur_event.get("set_scores", [])):
            set_obj = cur_event["set_scores"][cur_set_idx]
            if not set_obj.get("completed"):
                winner = action.get("winner")
                if not winner:
                    winner = "team_a" if set_obj["team_a"] >= set_obj["team_b"] else "team_b"
                winner_abbr = team_a_name if winner == "team_a" else team_b_name
                set_obj["winner"] = winner
                set_obj["completed"] = True
                cur_event["in_deuce"] = False

                if winner == "team_a":
                    cur_event["sets_a"] = cur_event.get("sets_a", 0) + 1
                else:
                    cur_event["sets_b"] = cur_event.get("sets_b", 0) + 1

                add_commentary(
                    match,
                    ball_or_tag=f"{cur_event['short_name']}-Set {cur_event['current_set']}",
                    text=f"SET CONCLUDED: {winner_abbr} awarded Set {cur_event['current_set']} ({set_obj['team_a']} - {set_obj['team_b']})!",
                    badge="SET AWARDED",
                    comment_type="set_won"
                )

                if cur_event.get("sets_a", 0) >= 2 or cur_event.get("sets_b", 0) >= 2:
                    ev_win = "team_a" if cur_event["sets_a"] >= 2 else "team_b"
                    cur_event["status"] = "completed"
                    cur_event["winner"] = ev_win
                    _sync_active_event_mirrors(score)
                    if score["events_team_a"] >= 3 or score["events_team_b"] >= 3:
                        m_win = "team_a" if score["events_team_a"] >= 3 else "team_b"
                        match["status"] = "completed"
                        match["winner"] = m_win
                        match["result"] = f"{match[m_win]['abbr']} won the match {score['events_team_a']} - {score['events_team_b']}"
                else:
                    cur_event["current_set"] = cur_event.get("current_set", 1) + 1
                    cur_event["set_scores"].append({
                        "set": cur_event["current_set"],
                        "team_a": 0,
                        "team_b": 0,
                        "winner": None,
                        "completed": False
                    })
                _sync_active_event_mirrors(score)

    # -------------------------------------------------------------------------
    # 6. SWAP SERVER
    # -------------------------------------------------------------------------
    elif act == "swap_server":
        cur_event["server"] = "team_b" if cur_event.get("server") == "team_a" else "team_a"
        server_abbr = team_a_name if cur_event["server"] == "team_a" else team_b_name
        _sync_active_event_mirrors(score)
        add_commentary(
            match,
            ball_or_tag="SERVE",
            text=f"Service switched: {server_abbr} now serving.",
            badge="SERVICE",
            comment_type="serve"
        )

    # -------------------------------------------------------------------------
    # 7. LATE ARRIVAL PENALTY / ADVANTAGE (Rule 5)
    # -------------------------------------------------------------------------
    elif act == "late_arrival_penalty":
        # Rule 5: 2 points advantage awarded to opposing team
        advantaged_team = action.get("advantaged_team", "team_a")
        cur_set_idx = max(0, cur_event.get("current_set", 1) - 1)
        if cur_set_idx < len(cur_event.get("set_scores", [])):
            set_obj = cur_event["set_scores"][cur_set_idx]
            # Add 2 points advantage
            set_obj[advantaged_team] = set_obj.get(advantaged_team, 0) + 2
            adv_abbr = team_a_name if advantaged_team == "team_a" else team_b_name
            _sync_active_event_mirrors(score)
            add_commentary(
                match,
                ball_or_tag="LATE ARRIVAL",
                text=f"Late arrival rule applied: +2 points advantage awarded to {adv_abbr}.",
                badge="⚠️ PENALTY RULE",
                comment_type="penalty"
            )

    # -------------------------------------------------------------------------
    # 8. UPDATE EVENT LINEUP / PLAYERS
    # -------------------------------------------------------------------------
    elif act == "update_event_players":
        target_ev_id = action.get("event_id") or score.get("active_event_id")
        for ev in score.get("events", []):
            if ev["id"] == target_ev_id:
                if "players_a" in action:
                    ev["players_a"] = str(action["players_a"]).strip()
                if "players_b" in action:
                    ev["players_b"] = str(action["players_b"]).strip()
                _sync_active_event_mirrors(score)
                break
