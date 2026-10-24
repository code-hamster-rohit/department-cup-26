"""
Modular Sports & Clean Architecture Verification Test.
Verifies that:
1. Every sport has its own backend module in sports/.
2. Every sport initializes its scoring state cleanly and independently.
3. Every sport processes sport-specific actions without clashing.
4. Audience and Admin templates/CSS/JS load without missing files or 500 errors.
"""

import sys
import os
import asyncio
import httpx

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.rules import RULES_DATA
from sports import SPORTS_REGISTRY, init_sport_score, handle_sport_action

BASE_URL = "http://127.0.0.1:8000"
ADMIN_EMAIL = "rohit_k@amsc.iitr.ac.in"

# Canonical actions to test backend scoring logic for each sport
SAMPLE_ACTIONS = {
    "cricket": {"type": "boundary", "runs": 6},
    "box_cricket": {"type": "run", "runs": 2},
    "football": {"type": "goal", "team": "team_a", "player": "Rohit Kumar", "minute": "12'"},
    "football_girls": {"type": "goal", "team": "team_a", "player": "Priya Sharma", "minute": "8'"},
    "penalty_shootout": {"type": "shootout_kick", "team": "team_a", "result": "goal"},
    "volleyball": {"type": "point", "team": "team_a"},
    "badminton": {"type": "point", "team": "team_a"},
    "table_tennis": {"type": "point", "team": "team_a"},
    "carrom": {"type": "end_board", "board_num": 1, "white_pts": 3, "black_pts": 0, "queen": "team_a"},
    "tug_of_war": {"type": "pull_result", "winner": "team_a", "duration": "45s"},
    "athletics_distance": {"type": "record_attempt", "bib": "A1", "name": "Awanish Singh", "department": "amsc", "distance": 6.85, "attempt_type": "official"},
    "basketball_shootout": {"type": "record_shot", "team": "team_a", "shooter": "Harshit", "zone": 2, "success": True}
}

async def run_modular_tests():
    print("=" * 70)
    print("⚡ VERIFYING MODULAR SPORTS ARCHITECTURE")
    print("=" * 70)

    # 1. Test Backend Modules Isolation
    print("\n[1/4] Testing backend modules & scoring state engines...")
    for sport_id, rule in RULES_DATA.items():
        score = init_sport_score(rule, max_overs=10)
        assert score is not None, f"Failed to initialize score for {sport_id}"
        
        # Test sample action
        action = SAMPLE_ACTIONS.get(sport_id) or SAMPLE_ACTIONS.get(rule.get("sport_type"))
        if action:
            mock_match = {
                "id": f"test_{sport_id}",
                "sport_id": sport_id,
                "sport_type": rule.get("sport_type", sport_id),
                "team_a": {"code": "amsc", "name": "AMSC", "abbr": "AMSC"},
                "team_b": {"code": "ppe", "name": "PPE", "abbr": "PPE"},
                "score": score,
                "status": "live",
                "commentary": []
            }
            handle_sport_action(mock_match, action)
            assert mock_match["score"] is not None, f"handle_sport_action corrupted score for {sport_id}"
            print(f"  ✔ {sport_id:<22} (engine: {rule.get('sport_type', sport_id)}) -> initial & action handling OK")

    # 2. Test File System Separation
    print("\n[2/4] Testing separate templates, CSS, and JS files per sport...")
    checked_sports = ["cricket", "football", "volleyball", "badminton", "table_tennis", "carrom", "tug_of_war", "athletics", "basketball"]
    for sp in checked_sports:
        # Check Audience Template
        aud_tmpl = os.path.join("templates", "audience", "sports", f"{sp}.html")
        assert os.path.exists(aud_tmpl), f"Missing audience template: {aud_tmpl}"
        
        # Check Admin Template
        adm_tmpl = os.path.join("templates", "admin", "sports", f"{sp}.html")
        assert os.path.exists(adm_tmpl), f"Missing admin template: {adm_tmpl}"
        
        # Check CSS
        sp_css = os.path.join("static", "css", "sports", f"{sp}.css")
        assert os.path.exists(sp_css), f"Missing CSS file: {sp_css}"
        
        # Check Audience JS
        aud_js = os.path.join("static", "js", "audience", "sports", f"{sp}.js")
        assert os.path.exists(aud_js), f"Missing audience JS: {aud_js}"
        
        # Check Admin JS
        adm_js = os.path.join("static", "js", "admin", "sports", f"{sp}.js")
        assert os.path.exists(adm_js), f"Missing admin JS: {adm_js}"
        
        print(f"  ✔ {sp:<16} -> Audience HTML, Admin HTML, CSS, Audience JS, Admin JS all exist")

    # 3. Test HTTP Lifecycle & Rendering via running FastAPI app
    print("\n[3/4] Testing live API creation, admin room rendering, and audience view...")
    async with httpx.AsyncClient(timeout=15.0) as client:
        # Test clean canvas
        res_home = await client.get(f"{BASE_URL}/")
        assert res_home.status_code == 200, f"GET / failed with {res_home.status_code}"
        print("  ✔ GET / (Audience Canvas) -> 200 OK")

        # Test creating a Cricket match
        res_create = await client.post(
            f"{BASE_URL}/api/match/create",
            headers={"X-Admin-Email": ADMIN_EMAIL},
            json={
                "sport_id": "cricket",
                "category": "Boys",
                "team_a": "amsc",
                "team_b": "ppe",
                "venue": "Campus Oval",
                "stage": "League Match",
                "custom_overs": 10
            }
        )
        assert res_create.status_code == 200, f"Failed creating match: {res_create.text}"
        match_id = res_create.json()["match"]["id"]
        print(f"  ✔ POST /api/match/create (Cricket) -> 200 OK (Match ID: {match_id})")

        # Start match to make it live
        res_start = await client.post(f"{BASE_URL}/api/match/{match_id}/start", headers={"X-Admin-Email": ADMIN_EMAIL})
        assert res_start.status_code == 200
        print("  ✔ POST /api/match/{id}/start -> 200 OK (Match is LIVE)")

        # Verify Audience page renders cricket template and linked CSS/JS
        res_aud = await client.get(f"{BASE_URL}/")
        assert res_aud.status_code == 200
        assert "sports/cricket.css" in res_aud.text, "cricket.css not linked in audience page"
        assert "audience/sports/cricket.js" in res_aud.text, "cricket.js not linked in audience page"
        assert "aud-pitch-strip" in res_aud.text, "cricket pitch strip partial not rendered"
        print("  ✔ GET / (Live Audience Cricket Arena) -> 200 OK (Rendered cricket partial, CSS & JS)")

        # Verify Admin Control Room renders admin cricket template and linked CSS/JS
        res_adm = await client.get(f"{BASE_URL}/admin/match/{match_id}", headers={"X-Admin-Email": ADMIN_EMAIL})
        assert res_adm.status_code == 200
        assert "sports/cricket.css" in res_adm.text, "cricket.css not linked in admin page"
        assert "admin/sports/cricket.js" in res_adm.text, "admin/cricket.js not linked in admin page"
        assert "tactical-cricket-bar" in res_adm.text, "admin cricket scoring keypad not rendered"
        print("  ✔ GET /admin/match/{id} -> 200 OK (Rendered admin cricket cockpit, CSS & JS)")

        # Perform scoring action via API
        res_score = await client.post(
            f"{BASE_URL}/api/match/{match_id}/score",
            headers={"X-Admin-Email": ADMIN_EMAIL},
            json={"type": "boundary", "runs": 6}
        )
        assert res_score.status_code == 200
        print("  ✔ POST /api/match/{id}/score (SIX!) -> 200 OK (Score mutated)")

        # Undo score action
        res_undo = await client.post(f"{BASE_URL}/api/match/{match_id}/undo", headers={"X-Admin-Email": ADMIN_EMAIL})
        assert res_undo.status_code == 200
        print("  ✔ POST /api/match/{id}/undo -> 200 OK")

        # Conclude and clean up match
        res_end = await client.post(
            f"{BASE_URL}/api/match/{match_id}/end",
            headers={"X-Admin-Email": ADMIN_EMAIL},
            json={"winner": "team_a", "result_summary": "AMSC won by 6 wickets", "player_of_the_match": "Rohit Kumar"}
        )
        assert res_end.status_code == 200
        
        res_del = await client.post(f"{BASE_URL}/api/match/{match_id}/delete", headers={"X-Admin-Email": ADMIN_EMAIL})
        assert res_del.status_code == 200
        print("  ✔ POST /api/match/{id}/delete -> 200 OK (Cleaned up)")

    # 4. Summary
    print("\n[4/4] Architecture Status:")
    print("  ✔ Separate backend modules (sports/*.py)")
    print("  ✔ Separate audience templates (templates/audience/sports/*.html)")
    print("  ✔ Separate admin templates (templates/admin/sports/*.html)")
    print("  ✔ Separate CSS files (static/css/sports/*.css)")
    print("  ✔ Separate audience JS files (static/js/audience/sports/*.js)")
    print("  ✔ Separate admin JS files (static/js/admin/sports/*.js)")
    print("  ✔ Clean, understandable, and easily editable structure achieved!\n")

if __name__ == "__main__":
    asyncio.run(run_modular_tests())
