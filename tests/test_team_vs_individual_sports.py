import asyncio
from database.rules import is_team_sport, is_single_double_sport, TOURNAMENT_SPORTS_CONFIG_16
from database.storage import create_match, get_match, update_squads_and_toss, update_players_and_toss, start_match

async def run():
    print("1. Testing is_team_sport classification:")
    assert is_team_sport("cricket") is True, "cricket should be team"
    assert is_team_sport("cricket_boys") is True, "cricket_boys should be team"
    assert is_team_sport("football_boys") is True, "football_boys should be team"
    assert is_team_sport("volleyball") is True, "volleyball should be team"
    assert is_team_sport("tow_boys") is True, "tow_boys should be team"
    assert is_team_sport("box_cricket_girls") is True, "box_cricket_girls should be team"
    assert is_team_sport("badminton") is False, "badminton should NOT be team"
    assert is_team_sport("badminton_mix") is False, "badminton_mix should NOT be team"
    assert is_team_sport("tt_boys") is False, "tt_boys should NOT be team"
    assert is_team_sport("carrom_mix") is False, "carrom_mix should NOT be team"
    assert is_team_sport("shotput_boys") is False, "shotput_boys should NOT be team"
    print("PASS: All sport classification assertions passed!")

    print("\n2. Testing match creation for Single/Doubles sport (Badminton):")
    m_badminton = await create_match("badminton", "amsc", "ppe")
    assert m_badminton["is_team_sport"] is False
    assert m_badminton["squads"] == {}
    print("PASS: Badminton match has is_team_sport=False and no squads!")

    print("\n3. Testing update_players_and_toss for Badminton:")
    m_badminton = await update_players_and_toss(m_badminton["id"], "Rohit / Sam", "Alex / Rahul", "team_a", "serve")
    assert m_badminton["players_a"] == "Rohit / Sam"
    assert m_badminton["players_b"] == "Alex / Rahul"
    m_badminton = await start_match(m_badminton["id"])
    assert m_badminton["status"] == "live"
    print("PASS: Badminton live start succeeded!")

    print("\n4. Testing match creation for Team sport (Cricket):")
    m_cricket = await create_match("cricket", "amsc", "ppe")
    assert m_cricket["is_team_sport"] is True
    assert "team_a" in m_cricket["squads"] and len(m_cricket["squads"]["team_a"]["playing"]) == 11
    assert "team_b" in m_cricket["squads"] and len(m_cricket["squads"]["team_b"]["playing"]) == 11
    print("PASS: Cricket match has is_team_sport=True and 11 playing players pre-loaded!")

    print("\n5. Testing update_squads_and_toss and start_match for Cricket:")
    m_cricket = await update_squads_and_toss(m_cricket["id"], {}, {}, "team_a", "bat")
    assert m_cricket["score"]["batting_team"] == "team_a"
    m_cricket = await start_match(m_cricket["id"])
    assert m_cricket["status"] == "live"
    inn = m_cricket["score"]["innings_1"]
    assert inn["striker"] is not None
    assert inn["non_striker"] is not None
    assert inn["bowler"] is not None
    print(f"PASS: Cricket live start succeeded! Striker: {inn['striker']}, Non-striker: {inn['non_striker']}, Bowler: {inn['bowler']}")

if __name__ == "__main__":
    asyncio.run(run())
