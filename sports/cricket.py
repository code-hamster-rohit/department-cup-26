"""
Cricket and Box Cricket Scoring Engine for Department Cup 2026.
Supports full ball-by-ball scoring, partnerships, bowler economy, fall of wickets,
free hits on no-balls, powerplay status, and dead ball penalties.
"""

from typing import Any
from sports.base import add_commentary


def init_score(sport_rule: dict[str, Any], max_overs: int) -> dict[str, Any]:
    """Initializes score state for a new cricket match."""
    max_overs_per_bowler = sport_rule.get("match_format", {}).get("max_overs_per_bowler", 2)
    powerplay_overs = sport_rule.get("match_format", {}).get("powerplay_overs", 3 if max_overs >= 10 else 0)
    
    return {
        "innings": 1,
        "batting_team": "team_a",
        "bowling_team": "team_b",
        "max_overs": max_overs,
        "max_overs_per_bowler": max_overs_per_bowler,
        "powerplay_overs": powerplay_overs,
        "is_free_hit": False,
        "is_powerplay": True if powerplay_overs > 0 else False,
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


def handle_action(match: dict[str, Any], action: dict[str, Any]) -> None:
    """Processes ball-by-ball scoring actions for Cricket matches."""
    score = match["score"]
    act_type = action.get("type")  # run, boundary, wicket, extra, dead_ball, swap_strike, change_bowler, switch_innings

    if act_type == "switch_innings":
        score["innings"] = 2
        score["batting_team"], score["bowling_team"] = score["bowling_team"], score["batting_team"]
        score["innings_2"]["target"] = score["innings_1"]["runs"] + 1

        # Initialize default batters and bowler for 2nd innings from the new batting/bowling squads
        bat_playing = match.get("squads", {}).get(score["batting_team"], {}).get("playing", [])
        bowl_playing = match.get("squads", {}).get(score["bowling_team"], {}).get("playing", [])

        inn2 = score["innings_2"]
        p1 = bat_playing[0].get("name") if len(bat_playing) > 0 else "Striker"
        p2 = bat_playing[1].get("name") if len(bat_playing) > 1 else "Non-Striker"
        b1 = bowl_playing[0].get("name") if len(bowl_playing) > 0 else "Bowler"

        inn2["striker"] = p1
        inn2["non_striker"] = p2
        inn2["bowler"] = b1
        inn2.setdefault("batsmen", {})[p1] = {"runs": 0, "balls": 0, "fours": 0, "sixes": 0, "sr": "0.0", "status": "not out"}
        inn2.setdefault("batsmen", {})[p2] = {"runs": 0, "balls": 0, "fours": 0, "sixes": 0, "sr": "0.0", "status": "not out"}
        inn2.setdefault("bowlers", {})[b1] = {"overs": 0.0, "maidens": 0, "runs": 0, "wickets": 0, "legal_balls": 0, "econ": "0.0", "dots": 0, "fours": 0, "sixes": 0}

        target_team_abbr = match[score["batting_team"]]["abbr"] if score["batting_team"] in match else score["batting_team"].upper()
        add_commentary(
            match,
            ball_or_tag="0.0",
            text=f"Innings Break! Target for {target_team_abbr} is {score['innings_2']['target']} runs.",
            badge="INNINGS BREAK",
            comment_type="innings_break"
        )
        return

    inn_key = f"innings_{score['innings']}"
    inn = score[inn_key]

    # Squad defaults if not set
    bat_team_key = score.get("batting_team", "team_a")
    bowl_team_key = score.get("bowling_team", "team_b")
    bat_playing = match.get("squads", {}).get(bat_team_key, {}).get("playing", [])
    bowl_playing = match.get("squads", {}).get(bowl_team_key, {}).get("playing", [])

    default_striker = bat_playing[0].get("name") if len(bat_playing) > 0 else "Striker"
    default_non_striker = bat_playing[1].get("name") if len(bat_playing) > 1 else "Non-Striker"
    default_bowler = bowl_playing[0].get("name") if len(bowl_playing) > 0 else "Bowler"

    striker = action.get("striker") or inn.get("striker") or default_striker
    non_striker = action.get("non_striker") or inn.get("non_striker") or default_non_striker
    bowler = action.get("bowler") or inn.get("bowler") or default_bowler

    if act_type == "swap_strike":
        inn["striker"], inn["non_striker"] = non_striker, striker
        return

    if act_type == "change_bowler":
        new_b = action.get("bowler") or bowler
        inn["bowler"] = new_b
        if new_b not in inn["bowlers"]:
            inn["bowlers"][new_b] = {"overs": 0.0, "maidens": 0, "runs": 0, "wickets": 0, "legal_balls": 0, "dots": 0, "fours": 0, "sixes": 0, "econ": "0.0"}
        return

    inn["striker"] = striker
    inn["non_striker"] = non_striker
    inn["bowler"] = bowler

    # Ensure bowler record exists
    if bowler not in inn["bowlers"]:
        inn["bowlers"][bowler] = {"overs": 0.0, "maidens": 0, "runs": 0, "wickets": 0, "legal_balls": 0, "dots": 0, "fours": 0, "sixes": 0, "econ": "0.0"}
    b_stat = inn["bowlers"][bowler]

    # Ensure striker record exists
    if striker not in inn["batsmen"]:
        inn["batsmen"][striker] = {"runs": 0, "balls": 0, "fours": 0, "sixes": 0, "sr": "0.0", "status": "not out"}
    s_stat = inn["batsmen"][striker]

    # Calculate current ball notation
    cur_balls = inn["legal_balls"]
    over_num = cur_balls // 6
    ball_in_over = (cur_balls % 6) + 1
    ball_tag = f"{over_num}.{ball_in_over}"

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

        badge_txt = f"{runs} RUNS" if runs not in [4, 6] else ("FOUR" if runs == 4 else "SIX")
        add_commentary(
            match,
            ball_or_tag=ball_tag,
            text=comment_text,
            badge=badge_txt,
            comment_type="boundary" if runs in [4, 6] else "run"
        )

        # Odd runs change strike
        if runs % 2 != 0:
            inn["striker"], inn["non_striker"] = inn["non_striker"], inn["striker"]

        # Check end of over
        if inn["legal_balls"] % 6 == 0:
            inn["striker"], inn["non_striker"] = inn["non_striker"], inn["striker"]
            add_commentary(
                match,
                ball_or_tag=f"{over_num + 1}.0",
                text=f"End of over {over_num + 1}! Score: {inn['runs']}/{inn['wickets']}.",
                badge="END OF OVER",
                comment_type="over_end"
            )

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
                add_commentary(
                    match,
                    ball_or_tag=ball_tag,
                    text=f"NO-BALL called! {runs} run(s) added. FREE HIT awarded on next delivery!",
                    badge="🎯 FREE HIT",
                    comment_type="free_hit"
                )
            else:
                inn["timeline"].append(f"Wd+{runs-1}" if runs > 1 else "Wd")
                add_commentary(
                    match,
                    ball_or_tag=ball_tag,
                    text=f"Wide ball by {bowler}. {runs} extra run(s).",
                    badge="WIDE",
                    comment_type="wide"
                )
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

        add_commentary(
            match,
            ball_or_tag=ball_tag,
            text=f"WICKET! {striker} is out! ({dismissal}). Score: {inn['runs']}/{inn['wickets']}.",
            badge="WICKET",
            comment_type="wicket"
        )

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
            add_commentary(
                match,
                ball_or_tag=ball_tag,
                text="DEAD BALL PENALTY: 6 runs awarded to batting team and over must be re-bowled!",
                badge="🚨 6 RUNS DEAD BALL",
                comment_type="penalty"
            )
        else:
            inn["timeline"].append("DEAD")
            add_commentary(
                match,
                ball_or_tag=ball_tag,
                text="Dead ball signaled by umpire. Delivery will be re-bowled.",
                badge="DEAD BALL",
                comment_type="dead_ball"
            )

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

    # Check Powerplay status (overs 0 to powerplay_overs)
    if inn["overs"] < score.get("powerplay_overs", 0):
        score["is_powerplay"] = True
    else:
        score["is_powerplay"] = False
