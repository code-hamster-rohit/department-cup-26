import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from httpx import AsyncClient, ASGITransport
from main import app

async def test_full_lifecycle():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Check audience view with no match
        r = await client.get("/")
        assert r.status_code == 200
        assert "NO MATCH CURRENTLY IN PROGRESS" in r.text
        assert "OPTION 1" in r.text
        assert "OPTION 2" in r.text
        print("[Test 1 Passed] Audience view loads with 2 options and empty stadium.")

        # 2. Check admin verify email
        r = await client.post("/api/auth/verify_email", json={"email": "rohit_k@amsc.iitr.ac.in"})
        assert r.status_code == 200
        data = r.json()
        assert data["success"] is True
        assert data["is_admin"] is True
        print("[Test 2 Passed] Admin email verification succeeds.")

        # 3. Create a Match
        r = await client.post("/api/match/create", json={
            "sport_id": "cricket",
            "team_a": "amsc",
            "team_b": "ppe",
            "category": "Boys",
            "stage": "League Match",
            "venue": "Main Sports Ground",
            "custom_overs": 10
        })
        assert r.status_code == 200
        match_data = r.json()["match"]
        match_id = match_data["id"]
        print(f"[Test 3 Passed] Match created: {match_id} (AMSC vs PPE Cricket)")

        # 4. Check audience view now has active match
        r = await client.get("/")
        assert r.status_code == 200
        assert match_id in r.text
        assert "AMSC" in r.text
        assert "PPE" in r.text
        print("[Test 4 Passed] Audience view now displays the newly created match.")

        # 5. Announce Toss and Squads
        r = await client.post(f"/api/match/{match_id}/squads", json={
            "squad_a": match_data["squads"]["team_a"],
            "squad_b": match_data["squads"]["team_b"],
            "toss_winner": "amsc",
            "toss_decision": "bat"
        })
        assert r.status_code == 200
        print("[Test 5 Passed] Toss and squads announced.")

        # 6. Start Match
        r = await client.post(f"/api/match/{match_id}/start")
        assert r.status_code == 200
        print("[Test 6 Passed] Match started (status = live).")

        # 7. Update Score (Runs & Boundaries)
        r = await client.post(f"/api/match/{match_id}/score", json={"type": "boundary", "runs": 4, "striker": "Riya"})
        assert r.status_code == 200
        cur_score = r.json()["match"]["score"]["innings_1"]
        assert cur_score["runs"] == 4
        print(f"[Test 7 Passed] Score updated: {cur_score['runs']}/{cur_score['wickets']}")

        # 8. Conclude Match & Declare Winner
        r = await client.post(f"/api/match/{match_id}/end", json={
            "winner": "team_a",
            "result_summary": "AMSC won by 14 runs",
            "player_of_the_match": "Riya"
        })
        assert r.status_code == 200
        print("[Test 8 Passed] Match ended and winner declared.")

        # 9. Check Audience view - match must DISAPPEAR!
        r = await client.get("/")
        assert r.status_code == 200
        assert "NO MATCH CURRENTLY IN PROGRESS" in r.text
        print("[Test 9 Passed] Match has disappeared from live audience view as required!")

        # 10. Clean up / delete test match from storage
        r = await client.post(f"/api/match/{match_id}/delete")
        assert r.status_code == 200
        print("[Test 10 Passed] Cleaned up test fixture.")

if __name__ == "__main__":
    asyncio.run(test_full_lifecycle())
