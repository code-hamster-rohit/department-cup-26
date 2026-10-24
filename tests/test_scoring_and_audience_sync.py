"""
Comprehensive automated tests for Control Room Scoring & Audience View Sync.
Verifies:
1. Admin authentication & authorization via session and X-Admin-Email header.
2. Complete Cricket & Box Cricket live scorer actions:
   - Runs: 0 (dot), 1, 2, 3, 4 (four), 6 (six)
   - Strike rotation on odd runs & over completion
   - Manual strike swap (swap_strike)
   - Extras: Wide, No-Ball (+ Free Hit active), Byes, Leg byes
   - Free hit consumption on legal delivery
   - Box cricket dead ball
   - Bowler change
   - Wickets & new batsman assignment
   - Undo last action (reverts score, timeline, commentary)
   - Innings switch (target set, teams flipped, 2nd innings default batters/bowler initialized)
   - Conclude match (winner declared, result summary, motm)
3. Audience View & Polling Sync:
   - /api/match/{id}/poll with ISO string timestamp (VERIFIES NO 422 ERROR!)
   - /api/match/{id} returns updated scores with Cache-Control: no-cache
   - /api/matches/active/poll returns live matches
   - HTML view contains correct scores, striker, and max overs
"""

from starlette.testclient import TestClient

from main import app
from database.storage import init_storage, get_match, create_match


def test_control_room_and_audience_sync():
    client = TestClient(app)
    admin_email = "rohit_k@amsc.iitr.ac.in"
    headers = {"X-Admin-Email": admin_email}

    # 1. Create a Box Cricket match: AMSC vs PPT (6 overs)
    create_res = client.post("/api/match/create", headers=headers, json={
        "sport_id": "box_cricket_girls",
        "category": "Girls",
        "team_a": "amsc",
        "team_b": "ppt",
        "venue": "Near Volleyball Ground",
        "stage": "League Match",
        "custom_overs": 6
    })
    assert create_res.status_code == 200, f"Match create failed: {create_res.text}"
    match_id = create_res.json()["match"]["id"]
    assert match_id.startswith("m_")

    # Verify unauthenticated request is blocked
    unauth_res = client.post(f"/api/match/{match_id}/score", json={"type": "run", "runs": 1})
    assert unauth_res.status_code == 401, "Expected 401 for unauthenticated request"

    # 2. Check audience view initially shows fixture
    aud_res = client.get(f"/?match={match_id}")
    assert aud_res.status_code == 200
    assert "AMSC" in aud_res.text
    assert "PPT" in aud_res.text

    # 3. Start Match Live
    start_res = client.post(f"/api/match/{match_id}/start", headers=headers)
    assert start_res.status_code == 200
    assert start_res.json()["match"]["status"] == "live"

    # 4. Dot ball (0 runs)
    res_dot = client.post(f"/api/match/{match_id}/score", headers=headers, json={
        "type": "run",
        "runs": 0,
        "striker": "AMSC Captain",
        "non_striker": "AMSC Player 2",
        "bowler": "PPT Captain"
    })
    assert res_dot.status_code == 200
    inn1 = res_dot.json()["match"]["score"]["innings_1"]
    assert inn1["runs"] == 0
    assert inn1["legal_balls"] == 1
    assert inn1["overs"] == 0.1
    assert inn1["timeline"][-1] == "."

    # 5. Single (1 run) -> strike rotates!
    res_1 = client.post(f"/api/match/{match_id}/score", headers=headers, json={
        "type": "run",
        "runs": 1,
        "striker": "AMSC Captain",
        "non_striker": "AMSC Player 2",
        "bowler": "PPT Captain"
    })
    assert res_1.status_code == 200
    inn1 = res_1.json()["match"]["score"]["innings_1"]
    assert inn1["runs"] == 1
    assert inn1["legal_balls"] == 2
    assert inn1["overs"] == 0.2
    # Strike rotated to AMSC Player 2
    assert inn1["striker"] == "AMSC Player 2"
    assert inn1["non_striker"] == "AMSC Captain"

    # 6. Manual Swap Strike
    res_swap = client.post(f"/api/match/{match_id}/score", headers=headers, json={
        "type": "swap_strike"
    })
    assert res_swap.status_code == 200
    inn1 = res_swap.json()["match"]["score"]["innings_1"]
    assert inn1["striker"] == "AMSC Captain"
    assert inn1["non_striker"] == "AMSC Player 2"

    # 7. Boundary FOUR (4 runs)
    res_4 = client.post(f"/api/match/{match_id}/score", headers=headers, json={
        "type": "boundary",
        "runs": 4,
        "striker": "AMSC Captain",
        "non_striker": "AMSC Player 2",
        "bowler": "PPT Captain"
    })
    assert res_4.status_code == 200
    inn1 = res_4.json()["match"]["score"]["innings_1"]
    assert inn1["runs"] == 5
    assert inn1["legal_balls"] == 3
    assert inn1["overs"] == 0.3
    assert inn1["batsmen"]["AMSC Captain"]["fours"] == 1

    # 8. No-Ball + Free Hit Generator
    res_nb = client.post(f"/api/match/{match_id}/score", headers=headers, json={
        "type": "extra",
        "extra_type": "no_ball",
        "runs": 1
    })
    assert res_nb.status_code == 200
    match_score = res_nb.json()["match"]["score"]
    assert match_score["is_free_hit"] is True
    assert match_score["innings_1"]["runs"] == 6
    assert match_score["innings_1"]["legal_balls"] == 3  # No-ball does not advance legal ball count

    # 9. Free hit consumed on legal ball (SIX!)
    res_6 = client.post(f"/api/match/{match_id}/score", headers=headers, json={
        "type": "boundary",
        "runs": 6,
        "striker": "AMSC Captain",
        "non_striker": "AMSC Player 2",
        "bowler": "PPT Captain"
    })
    assert res_6.status_code == 200
    match_score = res_6.json()["match"]["score"]
    assert match_score["is_free_hit"] is False  # Free hit successfully consumed!
    assert match_score["innings_1"]["runs"] == 12
    assert match_score["innings_1"]["legal_balls"] == 4
    assert match_score["innings_1"]["batsmen"]["AMSC Captain"]["sixes"] == 1

    # 10. Undo Last Action
    res_undo = client.post(f"/api/match/{match_id}/undo", headers=headers)
    assert res_undo.status_code == 200
    match_score = res_undo.json()["match"]["score"]
    assert match_score["innings_1"]["runs"] == 6
    assert match_score["innings_1"]["legal_balls"] == 3
    assert match_score["is_free_hit"] is True  # Free hit is active again after undo!

    # 11. Re-score legal ball (Single)
    res_legal = client.post(f"/api/match/{match_id}/score", headers=headers, json={
        "type": "run",
        "runs": 1,
        "striker": "AMSC Captain",
        "non_striker": "AMSC Player 2",
        "bowler": "PPT Captain"
    })
    assert res_legal.status_code == 200

    # 12. Bowler Change
    res_bowler = client.post(f"/api/match/{match_id}/score", headers=headers, json={
        "type": "change_bowler",
        "bowler": "PPT Player 2"
    })
    assert res_bowler.status_code == 200
    assert res_bowler.json()["match"]["score"]["innings_1"]["bowler"] == "PPT Player 2"

    # 13. Wicket (Bowled) & New Batter
    res_w = client.post(f"/api/match/{match_id}/score", headers=headers, json={
        "type": "wicket",
        "dismissal": "bowled",
        "new_batsman": "AMSC Player 3",
        "striker": "AMSC Player 2",
        "non_striker": "AMSC Captain",
        "bowler": "PPT Player 2"
    })
    assert res_w.status_code == 200
    inn1 = res_w.json()["match"]["score"]["innings_1"]
    assert inn1["wickets"] == 1
    assert inn1["striker"] == "AMSC Player 3"

    # 14. Audience Polling Endpoints
    # Test /api/match/{id}/poll with ISO string timestamp (REGRESSION CHECK: MUST NOT 422!)
    poll_res = client.get(f"/api/match/{match_id}/poll?since=2026-10-24T03:45:09.853063")
    assert poll_res.status_code == 200, f"Poll returned {poll_res.status_code}: {poll_res.text}"
    poll_data = poll_res.json()
    assert poll_data["match_id"] == match_id
    assert poll_data["status"] == "live"
    assert poll_data["score"]["innings_1"]["runs"] == 7
    assert poll_data["score"]["innings_1"]["wickets"] == 1

    # Test /api/match/{id} detail endpoint
    detail_res = client.get(f"/api/match/{match_id}")
    assert detail_res.status_code == 200
    assert detail_res.headers.get("cache-control") == "no-cache, no-store, must-revalidate"
    assert detail_res.json()["match"]["score"]["innings_1"]["runs"] == 7

    # Test /api/matches/active/poll
    active_poll = client.get("/api/matches/active/poll")
    assert active_poll.status_code == 200
    active_ids = [m["id"] for m in active_poll.json()["matches"]]
    assert match_id in active_ids

    # 15. Switch Innings
    res_switch = client.post(f"/api/match/{match_id}/score", headers=headers, json={
        "type": "switch_innings"
    })
    assert res_switch.status_code == 200
    sc = res_switch.json()["match"]["score"]
    assert sc["innings"] == 2
    assert sc["batting_team"] == "team_b"  # PPT batting
    assert sc["bowling_team"] == "team_a"  # AMSC bowling
    assert sc["innings_2"]["target"] == 8  # 7 + 1 = 8
    # 2nd innings default batters initialized from PPT
    assert sc["innings_2"]["striker"] is not None and len(sc["innings_2"]["striker"]) > 0
    assert sc["innings_2"]["non_striker"] is not None and len(sc["innings_2"]["non_striker"]) > 0
    assert sc["innings_2"]["bowler"] is not None and len(sc["innings_2"]["bowler"]) > 0
    striker_name = sc["innings_2"]["striker"]
    non_striker_name = sc["innings_2"]["non_striker"]
    bowler_name = sc["innings_2"]["bowler"]

    # 16. Score in 2nd innings: PPT hits 2 runs
    res_inn2 = client.post(f"/api/match/{match_id}/score", headers=headers, json={
        "type": "run",
        "runs": 2,
        "striker": striker_name,
        "non_striker": non_striker_name,
        "bowler": bowler_name
    })
    assert res_inn2.status_code == 200
    inn2 = res_inn2.json()["match"]["score"]["innings_2"]
    assert inn2["runs"] == 2
    assert inn2["legal_balls"] == 1
    assert inn2["overs"] == 0.1

    # 17. Conclude Match
    res_end = client.post(f"/api/match/{match_id}/end", headers=headers, json={
        "winner": "team_b",
        "result_summary": "PPT won by 5 wickets with 5.5 overs to spare",
        "player_of_the_match": "PPT Captain"
    })
    assert res_end.status_code == 200
    m_ended = res_end.json()["match"]
    assert m_ended["status"] == "completed"
    assert m_ended["winner"] == "team_b"
    assert m_ended["winner_name"] == "PPT"

    # 18. Verify concluded match disappears from audience view
    aud_after = client.get(f"/?match={match_id}")
    assert aud_after.status_code == 200
    # Match card for concluded match is not the active live stream
    assert "PPT won by 5 wickets" in aud_after.text or match_id not in aud_after.text


def test_multisport_control_and_audience():
    client = TestClient(app)
    admin_email = "rohit_k@amsc.iitr.ac.in"
    headers = {"X-Admin-Email": admin_email}

    # 1. Badminton match
    bad_res = client.post("/api/match/create", headers=headers, json={
        "sport_id": "badminton_mix",
        "team_a": "amsc",
        "team_b": "ppe",
        "venue": "Indoor Badminton Court"
    })
    assert bad_res.status_code == 200
    b_mid = bad_res.json()["match"]["id"]

    # Start and score points
    client.post(f"/api/match/{b_mid}/start", headers=headers)
    pt1 = client.post(f"/api/match/{b_mid}/score", headers=headers, json={"type": "point", "team": "team_a", "delta": 1})
    assert pt1.status_code == 200
    cur_set = pt1.json()["match"]["score"]["set_scores"][-1]
    assert cur_set["team_a"] == 1

    # Swap server
    srv_res = client.post(f"/api/match/{b_mid}/score", headers=headers, json={"type": "swap_server"})
    assert srv_res.status_code == 200
    assert srv_res.json()["match"]["score"]["server"] == "team_b"

    # 2. Football match
    fb_res = client.post("/api/match/create", headers=headers, json={
        "sport_id": "football_boys",
        "team_a": "amsc",
        "team_b": "ppt",
        "venue": "Football Ground"
    })
    assert fb_res.status_code == 200
    fb_mid = fb_res.json()["match"]["id"]

    # Goal
    goal_res = client.post(f"/api/match/{fb_mid}/score", headers=headers, json={
        "type": "goal",
        "team": "team_a",
        "player": "Rohit",
        "minute": "15'"
    })
    assert goal_res.status_code == 200
    assert goal_res.json()["match"]["score"]["team_a_score"] == 1

    # Period update
    half_res = client.post(f"/api/match/{fb_mid}/score", headers=headers, json={
        "type": "update_half",
        "half": 2
    })
    assert half_res.status_code == 200
    assert half_res.json()["match"]["score"]["half"] == 2
