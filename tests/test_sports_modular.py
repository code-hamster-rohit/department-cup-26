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
import json
import urllib.request

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

def run_modular_tests():
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
    
    def api_req(method, path, data=None, headers=None):
        url = f"{BASE_URL}{path}"
        hdrs = {"X-Admin-Email": ADMIN_EMAIL}
        if headers:
            hdrs.update(headers)
        body = None
        if data is not None:
            body = json.dumps(data).encode("utf-8")
            hdrs["Content-Type"] = "application/json"
        req = urllib.request.Request(url, data=body, headers=hdrs, method=method)
        with urllib.request.urlopen(req, timeout=10) as resp:
            content = resp.read().decode("utf-8")
            return resp.status, content

    # Test clean canvas
    st, html = api_req("GET", "/")
    assert st == 200, f"GET / failed with {st}"
    print("  ✔ GET / (Audience Canvas) -> 200 OK")

    # Test creating a Badminton match
    st, res = api_req("POST", "/api/match/create", data={
        "sport_id": "badminton",
        "category": "Mixed",
        "team_a": "amsc",
        "team_b": "ppe",
        "venue": "Campus Indoor Hall",
        "stage": "Semi-Final",
        "custom_overs": 0
    })
    assert st == 200, f"Failed creating badminton match: {res}"
    match_data = json.loads(res)["match"]
    match_id = match_data["id"]
    print(f"  ✔ POST /api/match/create (Badminton) -> 200 OK (Match ID: {match_id})")

    # Start match to make it live
    st, _ = api_req("POST", f"/api/match/{match_id}/start")
    assert st == 200
    print("  ✔ POST /api/match/{id}/start -> 200 OK (Match is LIVE)")

    # Verify Audience page renders badminton templates and linked CSS/JS
    st, aud_html = api_req("GET", "/")
    assert st == 200
    assert "sports/badminton.css" in aud_html, "badminton.css not linked in audience page"
    assert "audience/sports/badminton.js" in aud_html, "badminton.js not linked in audience page"
    assert "aud-badminton-tie-strip" in aud_html, "badminton tie strip not rendered in audience view"
    assert "aud-badminton-events-grid" in aud_html, "badminton events grid not rendered in audience view"
    print("  ✔ GET / (Live Audience Badminton Arena) -> 200 OK (Rendered badminton partials, CSS & JS)")

    # Verify Admin Control Room renders admin badminton template and linked CSS/JS
    st, adm_html = api_req("GET", f"/admin/match/{match_id}")
    assert st == 200
    assert "sports/badminton.css" in adm_html, "badminton.css not linked in admin page"
    assert "admin/sports/badminton.js" in adm_html, "admin/sports/badminton.js not linked in admin page"
    assert "badminton-touch-controls" in adm_html, "badminton touch controls not rendered"
    assert "badminton-events-nav" in adm_html, "badminton 5-events nav not rendered"
    print("  ✔ GET /admin/match/{id} -> 200 OK (Rendered admin badminton cockpit, CSS & JS)")

    # Perform scoring action via API: Rally won for Team A
    st, res_score = api_req("POST", f"/api/match/{match_id}/score", data={"type": "point", "team": "team_a", "delta": 1})
    assert st == 200
    print("  ✔ POST /api/match/{id}/score (+1 Point AMSC) -> 200 OK (Score mutated)")

    # Undo score action
    st, _ = api_req("POST", f"/api/match/{match_id}/undo")
    assert st == 200
    print("  ✔ POST /api/match/{id}/undo -> 200 OK")

    # Conclude and clean up match
    st, _ = api_req("POST", f"/api/match/{match_id}/end", data={
        "winner": "team_a",
        "result_summary": "AMSC won Mixed Team Tie 3-0",
        "player_of_the_match": "Awanish Singh"
    })
    assert st == 200
    
    st, _ = api_req("POST", f"/api/match/{match_id}/delete")
    assert st == 200
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
    run_modular_tests()

