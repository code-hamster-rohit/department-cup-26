"""
Simulation Script: 2 Full Overs on Box Cricket and Cricket
Simulates ball-by-ball live action through the actual Department Cup match engine:
Runs, Boundaries, Wickets, Extras (Wide & No-Ball with Free Hit), Over completion,
Strike rotation, Partnership tracking, and Bowler economics.
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.storage import (
    create_match,
    start_match,
    update_squads_and_toss,
    update_score_action,
    get_match,
    delete_match
)


def print_scorecard_summary(match: dict, title: str):
    score = match["score"]
    inn = score[f"innings_{score['innings']}"]
    balls = inn["legal_balls"]
    ov_str = f"{balls // 6}.{balls % 6}"

    print(f"\n{'='*65}")
    print(f"📊 {title.upper()}")
    print(f"🏆 {match['sport_name']} ({match['gender_badge']}) | {match['team_a']['abbr']} vs {match['team_b']['abbr']}")
    print(f"{'='*65}")
    print(f"⭐ SCORE: {inn['runs']}/{inn['wickets']} in {ov_str} overs (CRR: {inn['crr']})")
    print(f"🎯 Striker: {inn['striker']} | Non-Striker: {inn['non_striker']} | Bowler: {inn['bowler']}")
    print(f"📈 Delivery Timeline: {' '.join(inn['timeline'][-14:])}")

    print("\n🏏 BATTING SCORECARD:")
    print(f"{'Batter':<20} {'Runs':<6} {'Balls':<6} {'4s':<5} {'6s':<5} {'SR':<8} {'Status'}")
    print("-" * 60)
    for b_name, b_data in inn["batsmen"].items():
        print(f"{b_name:<20} {b_data['runs']:<6} {b_data['balls']:<6} {b_data['fours']:<5} {b_data['sixes']:<5} {b_data['sr']:<8} {b_data['status']}")

    print("\n🎯 BOWLING FIGURES:")
    print(f"{'Bowler':<20} {'Overs':<7} {'Maidens':<8} {'Runs':<6} {'Wickets':<8} {'Econ'}")
    print("-" * 60)
    for bw_name, bw_data in inn["bowlers"].items():
        econ = round(bw_data['runs'] / max(bw_data['legal_balls'] / 6, 0.166), 2)
        print(f"{bw_name:<20} {bw_data['overs']:<7} {bw_data['maidens']:<8} {bw_data['runs']:<6} {bw_data['wickets']:<8} {econ}")
    print(f"{'='*65}\n")


async def run_two_overs_simulation(sport_id: str, sport_label: str, team_a: str, team_b: str, batters: list, bowlers: list, cleanup: bool = False):
    print(f"\n\n{'#'*70}")
    print(f"🚀 INITIATING 2-OVER FULL SIMULATION: {sport_label.upper()}")
    print(f"{'#'*70}")

    # 1. Create Match
    match = await create_match(
        sport_id=sport_id,
        team_a_code=team_a,
        team_b_code=team_b,
        venue="Main Sports Ground, IITR SRE",
        stage="Tournament Clash"
    )
    mid = match["id"]
    print(f"✓ Created match: {mid} ({match['sport_name']})")

    # 2. Setup Toss & Squads
    await update_squads_and_toss(
        match_id=mid,
        squad_a={"playing": [{"name": b} for b in batters[:5]], "substitutes": []},
        squad_b={"playing": [{"name": b} for b in bowlers[:5]], "substitutes": []},
        toss_winner="team_a",
        toss_decision="bat"
    )
    print("✓ Toss conducted: Team A won and elected to bat first.")

    # 3. Start Live
    await start_match(mid)
    print("✓ Match started LIVE!")

    striker = batters[0]
    non_striker = batters[1]
    bowler_1 = bowlers[0]
    bowler_2 = bowlers[1]

    # =========================================================================
    # OVER 1: Bowled by bowler_1
    # =========================================================================
    print(f"\n--- 🏏 COMMENCING OVER 1 (Bowler: {bowler_1}) ---")
    
    # Ball 0.1: Dot ball (0 runs)
    print("Ball 0.1: Good length delivery outside off, left alone.")
    match = await update_score_action(mid, {
        "type": "run",
        "runs": 0,
        "striker": striker,
        "non_striker": non_striker,
        "bowler": bowler_1,
        "commentary": f"{bowler_1} to {striker}, dot ball. Tight line!"
    })

    # Ball 0.2: FOUR!
    print("Ball 0.2: CRACKED! Beautiful cover drive for FOUR!")
    match = await update_score_action(mid, {
        "type": "boundary",
        "runs": 4,
        "striker": striker,
        "non_striker": non_striker,
        "bowler": bowler_1,
        "commentary": f"FOUR! {striker} leans into a glorious cover drive to the fence."
    })

    # Ball 0.3: 1 Run (strike rotated)
    print("Ball 0.3: Tucked to mid-wicket for a sharp single. Strike rotates.")
    match = await update_score_action(mid, {
        "type": "run",
        "runs": 1,
        "striker": striker,
        "non_striker": non_striker,
        "bowler": bowler_1,
        "commentary": f"{striker} rotates the strike with a neat nudge to mid-wicket."
    })
    # Since 1 run was taken, the active striker in score is now non_striker
    cur_striker = match["score"]["innings_1"]["striker"]
    cur_non_striker = match["score"]["innings_1"]["non_striker"]

    # Ball 0.4 (Wide): Extra run awarded
    print("Ball 0.4: WIDE! Bowled down the leg side, umpire signals wide.")
    match = await update_score_action(mid, {
        "type": "extra",
        "extra_type": "wide",
        "runs": 1,
        "striker": cur_striker,
        "non_striker": cur_non_striker,
        "bowler": bowler_1,
        "commentary": f"Wide called against {bowler_1}. +1 extra run."
    })

    # Ball 0.4 Re-bowl: 2 Runs
    print("Ball 0.4 (Re-bowl): Driven into the deep extra cover gap, batters run 2!")
    match = await update_score_action(mid, {
        "type": "run",
        "runs": 2,
        "striker": cur_striker,
        "non_striker": cur_non_striker,
        "bowler": bowler_1,
        "commentary": f"{cur_striker} pushes hard into the deep and scampers back for two."
    })

    # Ball 0.5: WICKET! Caught at mid-on
    new_batter = batters[2]
    print(f"Ball 0.5: OUT! {cur_striker} goes for a lofted shot and is caught! Wicket falls.")
    match = await update_score_action(mid, {
        "type": "wicket",
        "dismissal_type": "caught",
        "striker": cur_striker,
        "non_striker": cur_non_striker,
        "bowler": bowler_1,
        "new_batsman": new_batter,
        "commentary": f"OUT! {cur_striker} mistimes the drive and is comfortably caught at mid-on!"
    })
    cur_striker = match["score"]["innings_1"]["striker"]
    cur_non_striker = match["score"]["innings_1"]["non_striker"]

    # Ball 0.6: SIX! Massive maximum on the final ball of over 1!
    print(f"Ball 0.6: SIX! New batter {cur_striker} dispatches it over long-on for SIX!")
    match = await update_score_action(mid, {
        "type": "boundary",
        "runs": 6,
        "striker": cur_striker,
        "non_striker": cur_non_striker,
        "bowler": bowler_1,
        "commentary": f"SIX! Massive blow by {cur_striker}! Sail over the boundary ropes."
    })

    print_scorecard_summary(match, f"{sport_label} - Scorecard at End of Over 1")

    # =========================================================================
    # OVER 2: Bowled by bowler_2
    # Strike automatically rotated at the end of Over 1
    # =========================================================================
    cur_striker = match["score"]["innings_1"]["striker"]
    cur_non_striker = match["score"]["innings_1"]["non_striker"]
    print(f"\n--- 🏏 COMMENCING OVER 2 (Bowler: {bowler_2}) ---")

    # Ball 1.1: 1 run
    print(f"Ball 1.1: {bowler_2} starts, {cur_striker} works it fine for a single.")
    match = await update_score_action(mid, {
        "type": "run",
        "runs": 1,
        "striker": cur_striker,
        "non_striker": cur_non_striker,
        "bowler": bowler_2,
        "commentary": f"{bowler_2} starts Over 2, single taken by {cur_striker}."
    })
    cur_striker = match["score"]["innings_1"]["striker"]
    cur_non_striker = match["score"]["innings_1"]["non_striker"]

    # Ball 1.2: 2 runs
    print("Ball 1.2: Clipped off the pads through square leg for two runs.")
    match = await update_score_action(mid, {
        "type": "run",
        "runs": 2,
        "striker": cur_striker,
        "non_striker": cur_non_striker,
        "bowler": bowler_2,
        "commentary": f"Good running between the wickets, 2 runs added."
    })

    # Ball 1.3: NO-BALL (+1 run, Free Hit awarded)
    print("Ball 1.3: NO-BALL called for overstepping! Free Hit awarded on next ball.")
    match = await update_score_action(mid, {
        "type": "extra",
        "extra_type": "no_ball",
        "runs": 1,
        "striker": cur_striker,
        "non_striker": cur_non_striker,
        "bowler": bowler_2,
        "commentary": f"Front-foot no-ball by {bowler_2}. FREE HIT on the next delivery!"
    })

    # Ball 1.3 Re-bowl (FREE HIT): FOUR!
    print("Ball 1.3 (FREE HIT): SMASHED! Batter capitalizes on the free hit for FOUR!")
    match = await update_score_action(mid, {
        "type": "boundary",
        "runs": 4,
        "striker": cur_striker,
        "non_striker": cur_non_striker,
        "bowler": bowler_2,
        "commentary": f"FREE HIT DISPATCHED! {cur_striker} slashes hard over point for FOUR!"
    })

    # Ball 1.4: Dot ball
    print("Ball 1.4: Slower ball deception, beaten outside off stump. Dot ball.")
    match = await update_score_action(mid, {
        "type": "run",
        "runs": 0,
        "striker": cur_striker,
        "non_striker": cur_non_striker,
        "bowler": bowler_2,
        "commentary": f"Clever change of pace by {bowler_2}, no run."
    })

    # Ball 1.5: 1 run
    print("Ball 1.5: Pushed down the ground to long-off for 1 run.")
    match = await update_score_action(mid, {
        "type": "run",
        "runs": 1,
        "striker": cur_striker,
        "non_striker": cur_non_striker,
        "bowler": bowler_2,
        "commentary": f"Long-off collects, 1 run to {cur_striker}."
    })
    cur_striker = match["score"]["innings_1"]["striker"]
    cur_non_striker = match["score"]["innings_1"]["non_striker"]

    # Ball 2.0: FOUR! Over 2 finishes in style!
    print(f"Ball 2.0: CRACKING SHOT! {cur_striker} pulls hard through mid-wicket for FOUR to finish Over 2!")
    match = await update_score_action(mid, {
        "type": "boundary",
        "runs": 4,
        "striker": cur_striker,
        "non_striker": cur_non_striker,
        "bowler": bowler_2,
        "commentary": f"FOUR! End of Over 2! Superb pull shot by {cur_striker} to close out the 2nd over."
    })

    print_scorecard_summary(match, f"{sport_label} - FINAL SCORECARD AFTER EXACTLY 2 FULL OVERS")

    # Assertions to guarantee correctness
    score = match["score"]["innings_1"]
    assert score["legal_balls"] == 12, f"Expected 12 legal balls for 2 overs, got {score['legal_balls']}"
    assert score["overs"] == 2.0, f"Expected 2.0 overs, got {score['overs']}"
    assert score["wickets"] == 1, f"Expected 1 wicket, got {score['wickets']}"
    print(f"✅ VERIFICATION PASSED: Exactly 2.0 overs (12 legal deliveries) completed with 1 wicket!")

    # Optionally cleanup simulation match
    if cleanup:
        await delete_match(mid)
        print(f"✓ Cleaned up test simulation match {mid}.")
    else:
        print(f"💾 MATCH PRESERVED IN DATABASE: {mid}")
        print(f"   MongoDB Collection: '{match.get('collection_name', sport_id)}'")
        print(f"   Control Room URL:   /admin/match/{mid}")
        print(f"   Audience View URL:  /?match={mid}")

    return mid, match


async def main():
    print("=" * 70)
    print("🏆 RUNNING COMPLETE 2-OVER SIMULATION ON CRICKET & BOX CRICKET")
    print("=" * 70)

    # SIMULATION 1: CRICKET (BOYS)
    await run_two_overs_simulation(
        sport_id="cricket",
        sport_label="Cricket (Boys - 11 A-Side)",
        team_a="amsc",
        team_b="ppe",
        batters=["Rohit (AMSC)", "Aman (AMSC)", "Vikas (AMSC)", "Sanjay (AMSC)", "Deepak (AMSC)"],
        bowlers=["Vikram (PPE)", "Suresh (PPE)", "Rajesh (PPE)", "Karan (PPE)", "Manish (PPE)"]
    )

    # SIMULATION 2: BOX CRICKET
    await run_two_overs_simulation(
        sport_id="box_cricket",
        sport_label="Box Cricket (5 A-Side)",
        team_a="ppe",
        team_b="ppt",
        batters=["Pooja (PPE)", "Neha (PPE)", "Kiran (PPE)", "Sneha (PPE)", "Ananya (PPE)"],
        bowlers=["Ritu (PPT)", "Kavya (PPT)", "Meera (PPT)", "Divya (PPT)", "Sunita (PPT)"]
    )

    print("\n" + "=" * 70)
    print("🎉 BOTH 2-OVER SIMULATIONS (CRICKET & BOX CRICKET) COMPLETED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
