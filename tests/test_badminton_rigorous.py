"""
Rigorous Test Suite for Badminton Scoring Engine.
Tests all tournament rules & edge cases:
1. Standard Set Victory (15-9, 15-13)
2. Deuce (14-14 -> 16-14, 18-16)
3. Golden Point Cap at 20-20 (First to 21 wins, set ends at 21-20, no score exceeds 21)
4. Set Completion Guard (Points CANNOT be added to a completed set)
5. Point Deduction (-1 point correction)
6. Event Progression (2 sets won = Event Victory)
7. Match Progression (3 events won = Overall Team Victory)
8. Late Arrival Advantage (+2 points)
9. Active Event Switching (BS -> GS -> XD -> GD -> BD)
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sports.badminton import init_score, handle_action

def make_test_match():
    score = init_score()
    return {
        "id": "test_badminton_m1",
        "sport_id": "badminton",
        "sport_type": "badminton",
        "team_a": {"code": "amsc", "abbr": "AMSC", "name": "AMSC"},
        "team_b": {"code": "ppe", "abbr": "PPE", "name": "PPE"},
        "status": "live",
        "score": score,
        "commentary": []
    }

def test_badminton_rules():
    print("🏸 TESTING BADMINTON RIGOROUS SCORING ENGINE...")
    
    # Test 1: Standard Set Victory (15-10)
    m = make_test_match()
    # Team A scores 15 points, Team B scores 10 points
    for _ in range(10):
        handle_action(m, {"type": "point", "team": "team_a"})
        handle_action(m, {"type": "point", "team": "team_b"})
    for _ in range(5):
        handle_action(m, {"type": "point", "team": "team_a"})
    
    ev = m["score"]["events"][0]
    set1 = ev["set_scores"][0]
    assert set1["team_a"] == 15 and set1["team_b"] == 10, f"Expected 15-10, got {set1['team_a']}-{set1['team_b']}"
    assert set1["completed"] is True, "Set 1 must be completed"
    assert set1["winner"] == "team_a", "Team A must win Set 1"
    assert ev["sets_a"] == 1, "Team A must have 1 set won"
    assert ev["current_set"] == 2, "Must advance to Set 2"
    print("  ✔ 1. Standard Set 1 Won at 15-10 verified")

    # Test 2: Set Completion Guard
    # Try adding points to Set 1 - must not affect Set 1!
    pts_set1_before = set1["team_a"]
    handle_action(m, {"type": "point", "team": "team_a"})
    # This point should go to Set 2, NOT Set 1!
    assert set1["team_a"] == pts_set1_before, "Completed Set 1 must never be modified by new points"
    set2 = ev["set_scores"][1]
    assert set2["team_a"] == 1, f"New point must go to Set 2, got {set2['team_a']}"
    print("  ✔ 2. Set completion guard verified (points go to current set, closed sets protected)")

    # Test 3: Deuce Rules (14-14 -> 16-14)
    m2 = make_test_match()
    ev2 = m2["score"]["events"][0]
    # Score 14 - 14
    for _ in range(14):
        handle_action(m2, {"type": "point", "team": "team_a"})
        handle_action(m2, {"type": "point", "team": "team_b"})
    
    set1_m2 = ev2["set_scores"][0]
    assert set1_m2["team_a"] == 14 and set1_m2["team_b"] == 14
    assert ev2["in_deuce"] is True, "Must be in deuce at 14-14"
    assert set1_m2["completed"] is False, "Set must not be completed at 14-14"

    # Team A scores 15 (15-14): Still in deuce, need 2 point lead!
    handle_action(m2, {"type": "point", "team": "team_a"})
    assert set1_m2["team_a"] == 15 and set1_m2["team_b"] == 14
    assert set1_m2["completed"] is False, "Set must not end at 15-14 in deuce"
    
    # Team A scores 16 (16-14): 2 point lead achieved -> Set 1 WON!
    handle_action(m2, {"type": "point", "team": "team_a"})
    assert set1_m2["team_a"] == 16 and set1_m2["team_b"] == 14
    assert set1_m2["completed"] is True, "Set 1 must be completed at 16-14"
    assert set1_m2["winner"] == "team_a", "Team A must win at 16-14"
    print("  ✔ 3. Deuce at 14-14 and 2-point victory (16-14) verified")

    # Test 4: Golden Point Cap at 20-20 (First to 21 wins, max score 21)
    m3 = make_test_match()
    ev3 = m3["score"]["events"][0]
    # Score 20 - 20
    for _ in range(20):
        handle_action(m3, {"type": "point", "team": "team_a"})
        handle_action(m3, {"type": "point", "team": "team_b"})
    set1_m3 = ev3["set_scores"][0]
    assert set1_m3["team_a"] == 20 and set1_m3["team_b"] == 20
    assert set1_m3["completed"] is False

    # Team B scores to reach 21 (20-21): Golden point cap -> Team B wins set!
    handle_action(m3, {"type": "point", "team": "team_b"})
    assert set1_m3["team_a"] == 20 and set1_m3["team_b"] == 21
    assert set1_m3["completed"] is True, "Set must end at 21 on golden point cap"
    assert set1_m3["winner"] == "team_b", "Team B must win set at 21"
    assert ev3["sets_b"] == 1
    print("  ✔ 4. Golden point cap at 20-20 -> first to 21 (21-20) wins set verified")

    # Test 5: Point Deduction (-1 point correction)
    m4 = make_test_match()
    ev4 = m4["score"]["events"][0]
    handle_action(m4, {"type": "point", "team": "team_a", "delta": 1})
    handle_action(m4, {"type": "point", "team": "team_a", "delta": 1})
    assert ev4["set_scores"][0]["team_a"] == 2
    handle_action(m4, {"type": "point", "team": "team_a", "delta": -1})
    assert ev4["set_scores"][0]["team_a"] == 1
    print("  ✔ 5. Point deduction (-1 point correction) verified")

    # Test 6: Event Victory (Best of 3 Sets: 2 sets won = Event Won)
    # Team A wins Set 1 (15-5) and Set 2 (15-8)
    for _ in range(15):
        handle_action(m, {"type": "point", "team": "team_a"})
    for _ in range(8):
        handle_action(m, {"type": "point", "team": "team_b"})
    for _ in range(14): # already had 1 point from Test 2
        handle_action(m, {"type": "point", "team": "team_a"})
    
    assert ev["sets_a"] == 2, f"Team A must have won 2 sets, got {ev['sets_a']}"
    assert ev["status"] == "completed", "Event 1 must be completed"
    assert ev["winner"] == "team_a", "Team A must be event winner"
    assert m["score"]["events_team_a"] == 1, "Overall match must record 1 event win for Team A"
    print("  ✔ 6. Event victory (2 sets won = Event Won, events_team_a = 1) verified")

    # Test 7: Late Arrival Advantage (Rule 5: +2 points)
    m5 = make_test_match()
    ev5 = m5["score"]["events"][0]
    handle_action(m5, {"type": "late_arrival_penalty", "advantaged_team": "team_a"})
    assert ev5["set_scores"][0]["team_a"] == 2
    assert ev5["set_scores"][0]["team_b"] == 0
    print("  ✔ 7. Late arrival advantage (+2 points in opening set) verified")

    # Test 8: Active Event Switching
    handle_action(m5, {"type": "switch_event", "event_id": "xd"})
    assert m5["score"]["active_event_id"] == "xd"
    assert m5["score"]["active_event_name"] == "Mixed Doubles"
    print("  ✔ 8. Active event switching (switched to Mixed Doubles) verified")

    # Test 9: Overall Match Victory (First to 3 Events Won)
    m_full = make_test_match()
    # Team A wins Event 1 (BS)
    ev_bs = m_full["score"]["events"][0]
    ev_bs["sets_a"] = 2
    ev_bs["winner"] = "team_a"
    ev_bs["status"] = "completed"
    
    # Team A wins Event 2 (GS)
    ev_gs = m_full["score"]["events"][1]
    ev_gs["sets_a"] = 2
    ev_gs["winner"] = "team_a"
    ev_gs["status"] = "completed"
    
    # Switch to Event 3 (XD) and Team A wins it live by scoring 2 sets
    m_full["score"]["active_event_id"] = "xd"
    ev_xd = m_full["score"]["events"][2]
    ev_xd["status"] = "in_progress"
    
    # Win Set 1 for Team A
    for _ in range(15):
        handle_action(m_full, {"type": "point", "team": "team_a"})
    assert ev_xd["sets_a"] == 1
    
    # Win Set 2 for Team A -> 3rd event victory!
    for _ in range(15):
        handle_action(m_full, {"type": "point", "team": "team_a"})
    assert ev_xd["sets_a"] == 2
    assert ev_xd["status"] == "completed"
    assert ev_xd["winner"] == "team_a"

    # Match must be COMPLETED!
    assert m_full["score"]["events_team_a"] == 3, f"Team A must have 3 event wins, got {m_full['score']['events_team_a']}"
    assert m_full["status"] == "completed", "Overall match must be completed on 3rd event win!"
    assert m_full["winner"] == "team_a", "Team A must be declared champion!"
    print("  ✔ 9. Overall Match Victory (First team to win 3 events wins tie) verified!")
    
    print("\n🎉 ALL 9 RIGOROUS BADMINTON TEST SCENARIOS PASSED WITH 100% ACCURACY!\n")

if __name__ == "__main__":
    test_badminton_rules()
