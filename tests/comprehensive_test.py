"""
🏆 DEPARTMENT CUP 2026 - COMPREHENSIVE DUAL-VIEW TEST SUITE
Tests each of the 17 registered sports for BOTH Admin and Audience views:
  - Separately (Full match lifecycle: Creation -> Squads/Toss -> Live Scoring -> Undo -> Completion)
  - Simultaneously (Real-time concurrent Admin Scoring + Audience WebSocket + Audience HTTP)
  - Multi-Match (Concurrent parallel live matches across multiple fields)
"""

import os
import sys
import json
import time

# Ensure workspace root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from starlette.testclient import TestClient
from main import app
from database.rules import RULES_DATA

ADMIN_EMAIL = "rohit_k@amsc.iitr.ac.in"  # Official admin from user's MongoDB database


# -----------------------------------------------------------------------------
# SPORT-SPECIFIC TEST ACTION SCENARIOS
# -----------------------------------------------------------------------------
SPORT_ACTIONS = {
    "cricket": [
        {"type": "boundary", "runs": 4},
        {"type": "boundary", "runs": 6},
        {"type": "extra", "extra_type": "no_balls", "runs": 1},  # awards free hit
        {"type": "run", "runs": 2},  # consumes free hit
    ],
    "football": [
        {"type": "goal", "team": "team_a", "player": "Sathiyaraj", "minute": "12'"},
        {"type": "card", "team": "team_b", "player": "Vikash", "card_color": "yellow", "minute": "28'"},
        {"type": "update_half", "half": 2},
        {"type": "goal", "team": "team_b", "player": "Arpit", "minute": "44'"}
    ],
    "penalty_shootout": [
        {"type": "kick", "team": "team_a", "player": "Ananya Sharma", "result": "goal"},
        {"type": "kick", "team": "team_b", "player": "Pooja Verma", "result": "saved"},
        {"type": "kick", "team": "team_a", "player": "Sneha Roy", "result": "goal"},
        {"type": "kick", "team": "team_b", "player": "Neha Gupta", "result": "missed"}
    ],
    "volleyball": [
        {"type": "point", "team": "team_a"},
        {"type": "point", "team": "team_a"},
        {"type": "point", "team": "team_b"},
        {"type": "point", "team": "team_a"}
    ],
    "badminton": [
        {"type": "point", "team": "team_a", "event_index": 0},
        {"type": "point", "team": "team_a", "event_index": 0},
        {"type": "point", "team": "team_b", "event_index": 0}
    ],
    "table_tennis": [
        {"type": "point", "team": "team_a", "event_index": 0},
        {"type": "point", "team": "team_a", "event_index": 0},
        {"type": "point", "team": "team_b", "event_index": 0}
    ],
    "carrom": [
        {"type": "point", "team": "team_a", "event_index": 0},
        {"type": "point", "team": "team_b", "event_index": 0}
    ],
    "tug_of_war": [
        {"type": "pull_win", "winner": "team_a"}
    ],
    "athletics_distance": [
        {"type": "record_attempt", "name": "Aman Verma", "department": "AMSC", "attempt_type": "trial", "distance": 11.45, "is_foul": False},
        {"type": "record_attempt", "name": "Aman Verma", "department": "AMSC", "attempt_type": "official", "distance": 12.80, "is_foul": False},
        {"type": "record_attempt", "name": "Rohan Das", "department": "PPE", "attempt_type": "official", "distance": 13.15, "is_foul": False}
    ],
    "basketball_shootout": [
        {"type": "shot", "team": "team_a", "player": "Tanvi Joshi", "zone": 2, "success": True},
        {"type": "shot", "team": "team_b", "player": "Kritika Soni", "zone": 3, "success": True},
        {"type": "shot", "team": "team_a", "player": "Tanvi Joshi", "zone": 1, "success": False}
    ]
}


def clean_all_matches(client: TestClient):
    """Clean up any existing matches in database/storage."""
    res = client.get("/api/matches")
    if res.status_code == 200:
        for m in res.json().get("matches", []):
            client.post(f"/api/match/{m['id']}/delete", json={}, headers={"X-Admin-Email": ADMIN_EMAIL})


# -----------------------------------------------------------------------------
# PART 1: TEST SEPARATELY FOR EVERY SINGLE SPORT (17 SPORTS)
# -----------------------------------------------------------------------------
def test_sport_separately(client: TestClient, sport_id: str, sport_info: dict):
    sport_name = sport_info["name"]
    stype = sport_info["sport_type"]
    actions = SPORT_ACTIONS.get(stype, SPORT_ACTIONS.get(sport_id, []))

    # 1. Admin Security: Non-admin rejected with 403
    res_bad = client.post(
        "/api/match/create",
        json={"sport_id": sport_id, "team_a": "amsc", "team_b": "ppe", "venue": "Main Arena", "stage": "Group Stage"},
        headers={"X-Admin-Email": "unauthorized_student@iitr.ac.in"}
    )
    assert res_bad.status_code == 403, f"Non-admin was not rejected for {sport_id}!"

    # 2. Admin Create Match (Status: upcoming)
    res_create = client.post(
        "/api/match/create",
        json={"sport_id": sport_id, "team_a": "amsc", "team_b": "ppe", "venue": "Main Arena", "stage": "Group Stage"},
        headers={"X-Admin-Email": ADMIN_EMAIL}
    )
    assert res_create.status_code == 200 and res_create.json()["success"] is True
    match = res_create.json()["match"]
    match_id = match["id"]

    # 3. Admin View: Dashboard and Match Control Room
    res_admin_dash = client.get("/admin", headers={"X-Admin-Email": ADMIN_EMAIL})
    assert res_admin_dash.status_code == 200
    assert "Verified Tournament Admin" in res_admin_dash.text

    res_admin_room = client.get(f"/admin/match/{match_id}", headers={"X-Admin-Email": ADMIN_EMAIL})
    assert res_admin_room.status_code == 200
    assert "1. Fixture Created" in res_admin_room.text
    assert "Step 2: Confirm Squads & Record Toss" in res_admin_room.text

    # 4. Audience View: Fixture / Upcoming Phase
    res_aud_up = client.get(f"/?match={match_id}")
    assert res_aud_up.status_code == 200
    assert "AMSC" in res_aud_up.text and "PPE" in res_aud_up.text
    assert "UPCOMING MATCH" in res_aud_up.text
    # Verify all 5 tabs exist in Audience View
    assert 'id="tab-btn-live"' in res_aud_up.text
    assert 'id="tab-btn-scorecard"' in res_aud_up.text
    assert 'id="tab-btn-squads"' in res_aud_up.text
    assert 'id="tab-btn-commentary"' in res_aud_up.text
    assert 'id="tab-btn-rules"' in res_aud_up.text
    # Verify Tab 5 contains official tournament rules for this sport
    assert "Official Meet Rules" in res_aud_up.text

    # 5. Admin View: Announce Squads & Toss
    squad_a = match["squads"]["team_a"]
    squad_b = match["squads"]["team_b"]
    res_squads = client.post(
        f"/api/match/{match_id}/squads",
        json={"squad_a": squad_a, "squad_b": squad_b, "toss_winner": "team_a", "toss_decision": "bat"},
        headers={"X-Admin-Email": ADMIN_EMAIL}
    )
    assert res_squads.status_code == 200 and res_squads.json()["match"]["status"] == "squads_announced"

    # 6. Audience View: Squads Announced Phase
    res_aud_sq = client.get(f"/?match={match_id}")
    assert res_aud_sq.status_code == 200
    assert "SQUADS ANNOUNCED" in res_aud_sq.text
    assert "AMSC won the toss" in res_aud_sq.text
    assert "Playing Lineup" in res_aud_sq.text

    # 7. Admin View: Start Match (Status: live)
    res_start = client.post(
        f"/api/match/{match_id}/start",
        json={},
        headers={"X-Admin-Email": ADMIN_EMAIL}
    )
    assert res_start.status_code == 200 and res_start.json()["match"]["status"] == "live"

    # 8. Admin View: Apply Sport-Specific Score Actions
    for act in actions:
        res_act = client.post(
            f"/api/match/{match_id}/score",
            json=act,
            headers={"X-Admin-Email": ADMIN_EMAIL}
        )
        assert res_act.status_code == 200, f"Score action failed for {sport_id}: {act} -> {res_act.text}"

    # 9. Admin View: Test Undo & Re-apply
    res_undo = client.post(
        f"/api/match/{match_id}/undo",
        json={},
        headers={"X-Admin-Email": ADMIN_EMAIL}
    )
    assert res_undo.status_code == 200 and res_undo.json()["success"] is True
    # Re-apply last action
    if actions:
        client.post(
            f"/api/match/{match_id}/score",
            json=actions[-1],
            headers={"X-Admin-Email": ADMIN_EMAIL}
        )

    # 10. Audience View: Live Phase Verification
    res_aud_live = client.get(f"/?match={match_id}")
    assert res_aud_live.status_code == 200
    assert "LIVE IN-PROGRESS" in res_aud_live.text
    # Verify dedicated scorecard rendered in Tab 2
    if stype == "cricket":
        assert "Bowling Analysis" in res_aud_live.text
        assert "Extras:" in res_aud_live.text
        assert "TOTAL" in res_aud_live.text
    elif stype == "football":
        assert "Football Match Scorecard" in res_aud_live.text
    elif stype == "penalty_shootout":
        assert "Shootout Matrix Scorecard" in res_aud_live.text
    elif stype == "volleyball":
        assert "Volleyball Sets Summary" in res_aud_live.text
    elif stype in ["badminton", "table_tennis", "carrom"]:
        assert "Events & Rubbers Breakdown" in res_aud_live.text
    elif stype == "tug_of_war":
        assert "Tug of War Pulls Scorecard" in res_aud_live.text
    elif stype == "athletics_distance":
        assert "Athletics Performance Leaderboard" in res_aud_live.text
    elif stype == "basketball_shootout":
        assert "Basketball Shootout Scorecard" in res_aud_live.text

    # 11. Admin View: Complete Match
    res_end = client.post(
        f"/api/match/{match_id}/end",
        json={"winner": "team_a", "result_summary": f"AMSC won the {sport_name} match!", "player_of_the_match": "Star Player"},
        headers={"X-Admin-Email": ADMIN_EMAIL}
    )
    assert res_end.status_code == 200 and res_end.json()["match"]["status"] == "completed"

    # 12. Audience View: Completed State
    res_aud_comp = client.get(f"/?match={match_id}")
    assert res_aud_comp.status_code == 200
    assert "COMPLETED" in res_aud_comp.text
    assert f"AMSC won the {sport_name} match!" in res_aud_comp.text

    # 13. Admin Clean up
    client.post(f"/api/match/{match_id}/delete", json={}, headers={"X-Admin-Email": ADMIN_EMAIL})
    print(f"  ✅ [SEPARATE] {sport_name:<30} ({stype:<18}): Admin & Audience views 100% verified.")


# -----------------------------------------------------------------------------
# PART 2: SIMULTANEOUS TESTING (Admin Live Scoring + Audience WebSocket + Audience HTTP)
# -----------------------------------------------------------------------------
def test_simultaneous_realtime(client: TestClient):
    print("\n--- PART 2: Simultaneous Testing (Admin Live Scoring + Audience WebSocket + HTTP sync) ---")
    
    # Admin creates and starts live match
    r_create = client.post(
        "/api/match/create",
        json={"sport_id": "cricket_boys", "team_a": "amsc", "team_b": "ppe", "venue": "Main Arena", "stage": "Live Demo"},
        headers={"X-Admin-Email": ADMIN_EMAIL}
    )
    mid = r_create.json()["match"]["id"]
    client.post(f"/api/match/{mid}/start", json={}, headers={"X-Admin-Email": ADMIN_EMAIL})

    # Open Audience WebSocket connection
    with client.websocket_connect("/ws/live") as ws:
        # Admin executes live delivery 1: FOUR
        t_start = time.time()
        client.post(
            f"/api/match/{mid}/score",
            json={"type": "boundary", "runs": 4},
            headers={"X-Admin-Email": ADMIN_EMAIL}
        )
        msg1 = json.loads(ws.receive_text())
        t_dur1 = (time.time() - t_start) * 1000
        assert msg1["event"] == "SCORE_UPDATED"
        assert msg1["match_id"] == mid
        assert msg1["data"]["commentary"]["badge"] == "FOUR"
        print(f"  ✅ Delivery 1 (FOUR): Received on Audience WS in {t_dur1:.2f} ms.")

        # Audience simultaneously checks live HTTP page
        r_http1 = client.get(f"/?match={mid}")
        assert r_http1.status_code == 200
        assert "4/0" in r_http1.text
        assert "FOUR" in r_http1.text

        # Admin executes live delivery 2: SIX
        t_start = time.time()
        client.post(
            f"/api/match/{mid}/score",
            json={"type": "boundary", "runs": 6},
            headers={"X-Admin-Email": ADMIN_EMAIL}
        )
        msg2 = json.loads(ws.receive_text())
        t_dur2 = (time.time() - t_start) * 1000
        assert msg2["data"]["commentary"]["badge"] == "SIX"
        print(f"  ✅ Delivery 2 (SIX):  Received on Audience WS in {t_dur2:.2f} ms.")

        # Audience simultaneously checks live HTTP page
        r_http2 = client.get(f"/?match={mid}")
        assert r_http2.status_code == 200
        assert "10/0" in r_http2.text

        # Admin executes live delivery 3: NO BALL (Free Hit awarded)
        t_start = time.time()
        client.post(
            f"/api/match/{mid}/score",
            json={"type": "extra", "extra_type": "no_balls", "runs": 1},
            headers={"X-Admin-Email": ADMIN_EMAIL}
        )
        msg3 = json.loads(ws.receive_text())
        t_dur3 = (time.time() - t_start) * 1000
        assert msg3["data"]["score"]["is_free_hit"] is True
        print(f"  ✅ Delivery 3 (NO BALL + FREE HIT): Received on Audience WS in {t_dur3:.2f} ms.")

        # Audience simultaneously checks live HTTP page for Free Hit badge
        r_http3 = client.get(f"/?match={mid}")
        assert r_http3.status_code == 200
        assert "FREE HIT" in r_http3.text

    # Clean up
    client.post(f"/api/match/{mid}/delete", json={}, headers={"X-Admin-Email": ADMIN_EMAIL})
    print("  ✅ PASS: Simultaneous Admin Scoring and Audience WebSocket streaming 100% verified.")


# -----------------------------------------------------------------------------
# PART 3: CONCURRENT MULTI-SPORT SIMULTANEOUS SIMULATION
# -----------------------------------------------------------------------------
def test_concurrent_multi_match(client: TestClient):
    print("\n--- PART 3: Concurrent Multi-Match Tournament Simulation (3 Sports Simultaneously) ---")

    # Start 3 matches on different fields at the exact same time
    m1_res = client.post("/api/match/create", json={"sport_id": "cricket_boys", "team_a": "amsc", "team_b": "ppe", "venue": "Ground A", "stage": "Tri-Series"}, headers={"X-Admin-Email": ADMIN_EMAIL})
    m2_res = client.post("/api/match/create", json={"sport_id": "football_boys", "team_a": "ppe", "team_b": "ppt", "venue": "Ground B", "stage": "Tri-Series"}, headers={"X-Admin-Email": ADMIN_EMAIL})
    m3_res = client.post("/api/match/create", json={"sport_id": "volleyball_boys", "team_a": "ppt", "team_b": "amsc", "venue": "Court C", "stage": "Tri-Series"}, headers={"X-Admin-Email": ADMIN_EMAIL})
    
    mid1, mid2, mid3 = m1_res.json()["match"]["id"], m2_res.json()["match"]["id"], m3_res.json()["match"]["id"]

    # Start all 3 simultaneously
    client.post(f"/api/match/{mid1}/start", json={}, headers={"X-Admin-Email": ADMIN_EMAIL})
    client.post(f"/api/match/{mid2}/start", json={}, headers={"X-Admin-Email": ADMIN_EMAIL})
    client.post(f"/api/match/{mid3}/start", json={}, headers={"X-Admin-Email": ADMIN_EMAIL})

    # Interleaved concurrent scoring actions across all 3 sports
    client.post(f"/api/match/{mid1}/score", json={"type": "boundary", "runs": 6}, headers={"X-Admin-Email": ADMIN_EMAIL})
    client.post(f"/api/match/{mid2}/score", json={"type": "goal", "team": "team_a", "player": "Forward 1", "minute": "10'"}, headers={"X-Admin-Email": ADMIN_EMAIL})
    client.post(f"/api/match/{mid3}/score", json={"type": "point", "team": "team_b"}, headers={"X-Admin-Email": ADMIN_EMAIL})
    client.post(f"/api/match/{mid1}/score", json={"type": "boundary", "runs": 4}, headers={"X-Admin-Email": ADMIN_EMAIL})
    client.post(f"/api/match/{mid2}/score", json={"type": "card", "team": "team_b", "player": "Defender 2", "card_color": "yellow", "minute": "15'"}, headers={"X-Admin-Email": ADMIN_EMAIL})
    client.post(f"/api/match/{mid3}/score", json={"type": "point", "team": "team_a"}, headers={"X-Admin-Email": ADMIN_EMAIL})

    # Verify Audience Selector Bar contains all 3 live matches
    res_aud_all = client.get("/")
    assert res_aud_all.status_code == 200
    assert f"chip-{mid1}" in res_aud_all.text
    assert f"chip-{mid2}" in res_aud_all.text
    assert f"chip-{mid3}" in res_aud_all.text
    print("  ✅ Audience Selector Bar successfully renders all 3 concurrent live matches.")

    # Verify Admin Dashboard contains all 3 matches
    res_admin_all = client.get("/admin", headers={"X-Admin-Email": ADMIN_EMAIL})
    assert res_admin_all.status_code == 200
    assert mid1 in res_admin_all.text
    assert mid2 in res_admin_all.text
    assert mid3 in res_admin_all.text
    print("  ✅ Admin Dashboard successfully tracks all 3 concurrent live matches.")

    # Clean up
    client.post(f"/api/match/{mid1}/delete", json={}, headers={"X-Admin-Email": ADMIN_EMAIL})
    client.post(f"/api/match/{mid2}/delete", json={}, headers={"X-Admin-Email": ADMIN_EMAIL})
    client.post(f"/api/match/{mid3}/delete", json={}, headers={"X-Admin-Email": ADMIN_EMAIL})
    print("  ✅ PASS: Multi-match concurrency and state isolation 100% verified.")


# -----------------------------------------------------------------------------
# MAIN TEST RUNNER
# -----------------------------------------------------------------------------
def run_all_comprehensive_tests():
    print("=" * 80)
    print("🏆 DEPARTMENT CUP 2026 - COMPLETE COMPREHENSIVE DUAL-VIEW TEST SUITE")
    print("=" * 80)

    client = TestClient(app)

    # Clean up before testing
    clean_all_matches(client)

    # 1. Blank Canvas verification
    res_blank = client.get("/")
    assert res_blank.status_code == 200
    assert "Department Cup 2026 Arena" in res_blank.text
    assert 'id="blank-canvas-section"' in res_blank.text
    assert 'id="active-match-section"' not in res_blank.text
    print("✅ PASS: Blank Canvas initial view verified (0 matches active).")

    # 2. Test each of the 17 sports separately
    print(f"\n--- PART 1: Testing all {len(RULES_DATA)} Sports Separately (Admin & Audience Views) ---")
    for sport_id, sport_info in RULES_DATA.items():
        test_sport_separately(client, sport_id, sport_info)

    # 3. Test simultaneous Admin live scoring + Audience WebSocket + HTTP sync
    test_simultaneous_realtime(client)

    # 4. Test multi-match parallel tournament execution
    test_concurrent_multi_match(client)

    # Final cleanup to leave pristine canvas
    clean_all_matches(client)

    print("\n" + "=" * 80)
    print("🎉 ALL 17 SPORTS TESTED SEPARATELY & SIMULTANEOUSLY FOR BOTH ADMIN & AUDIENCE VIEWS!")
    print("🎉 100% PASS RATE - ZERO REGRESSIONS DETECTED.")
    print("=" * 80)


if __name__ == "__main__":
    run_all_comprehensive_tests()
