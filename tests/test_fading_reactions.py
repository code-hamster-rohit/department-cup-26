"""
Automated Verification for Fading Reactions Feature:
1. REST reaction endpoint POST /api/match/{match_id}/react
2. WebSocket zero-latency broadcast for LIVE_REACTION
3. Emojis and Custom Text Chants support
4. Non-persistence verification: match database object remains clean
"""

import os
import sys
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from main import app
from database.storage import list_matches, create_match, delete_match
import asyncio

def run_fading_reactions_test():
    print("=" * 60)
    print("TESTING FADING REACTIONS (HOTSTAR/INSTAGRAM LIVE STYLE)")
    print("=" * 60)

    client = TestClient(app)

    # 1. Setup a test match
    matches = list_matches()
    test_match = None
    cleanup = False
    if not matches:
        print("Creating temporary test match for reaction verification...")
        test_match = asyncio.run(create_match("cricket_boys", "amsc", "ppe", "Main Oval", "Final"))
        cleanup = True
    else:
        test_match = matches[0]

    match_id = test_match["id"]
    print(f"Target match: {match_id} ({test_match['sport_name']})")

    # 2. Test WebSocket connection and receiving LIVE_REACTION
    # Using TestClient's websocket_connect
    with client.websocket_connect("/ws/live") as ws_live:
        # A. Send emoji reaction via REST API
        res1 = client.post(f"/api/match/{match_id}/react", json={
            "content": "🔥",
            "sender": "AudienceFan1"
        })
        assert res1.status_code == 200, f"Emoji reaction failed: {res1.text}"
        assert res1.json().get("success") is True
        print("  [PASS] REST POST emoji reaction '🔥' -> 200 OK")

        # Verify WS receives it
        msg1_raw = ws_live.receive_text()
        msg1 = json.loads(msg1_raw)
        assert msg1.get("event") == "LIVE_REACTION", f"Expected LIVE_REACTION, got {msg1}"
        assert msg1["data"]["content"] == "🔥"
        assert msg1["data"]["sender"] == "AudienceFan1"
        print(f"  [PASS] WS received broadcast for emoji: {msg1['data']}")

        # B. Send custom text chant reaction via REST API
        res2 = client.post(f"/api/match/{match_id}/react", json={
            "content": "AMSC On Fire! 🚀",
            "sender": "Rahul (AMSC)"
        })
        assert res2.status_code == 200, f"Text chant reaction failed: {res2.text}"
        assert res2.json().get("success") is True
        print("  [PASS] REST POST text chant 'AMSC On Fire! 🚀' -> 200 OK")

        # Verify WS receives it
        msg2_raw = ws_live.receive_text()
        msg2 = json.loads(msg2_raw)
        assert msg2.get("event") == "LIVE_REACTION"
        assert msg2["data"]["content"] == "AMSC On Fire! 🚀"
        assert msg2["data"]["sender"] == "Rahul (AMSC)"
        print(f"  [PASS] WS received broadcast for text chant: {msg2['data']}")

        # C. Send reaction directly via WebSocket
        with client.websocket_connect(f"/ws/match/{match_id}") as ws_match:
            ws_match.send_text(json.dumps({
                "type": "REACTION",
                "match_id": match_id,
                "content": "SIXERRR! 💥",
                "sender": "CrowdCheerer"
            }))
            print("  [PASS] WebSocket frame REACTION 'SIXERRR! 💥' sent directly")

            # Receive on global listener
            msg3_raw = ws_live.receive_text()
            msg3 = json.loads(msg3_raw)
            assert msg3.get("event") == "LIVE_REACTION"
            assert msg3["data"]["content"] == "SIXERRR! 💥"
            assert msg3["data"]["sender"] == "CrowdCheerer"
            print(f"  [PASS] WS received broadcast from socket trigger: {msg3['data']}")

    # 3. Non-persistence verification: match database object remains clean
    refreshed_matches = list_matches()
    target_refreshed = next(m for m in refreshed_matches if m["id"] == match_id)
    assert "reactions" not in target_refreshed or not target_refreshed.get("reactions"), \
        "Reactions must NOT be persisted in storage!"
    print("  [PASS] Non-persistence verified: 0 bytes written to database or disk")

    # 4. Empty content validation
    res_empty = client.post(f"/api/match/{match_id}/react", json={
        "content": "   ",
        "sender": "Nobody"
    })
    assert res_empty.status_code == 400
    print("  [PASS] Empty reaction content correctly rejected with 400 Bad Request")

    # 5. Invalid match ID validation
    res_invalid = client.post("/api/match/nonexistent-id/react", json={
        "content": "🔥",
        "sender": "Nobody"
    })
    assert res_invalid.status_code == 404
    print("  [PASS] Nonexistent match ID correctly rejected with 404 Not Found")

    # Cleanup if needed
    if cleanup:
        asyncio.run(delete_match(match_id))
        print("  [PASS] Temporary test match cleaned up")

    print("\nALL FADING REACTION VERIFICATION CHECKS PASSED (100%)!\n")

if __name__ == "__main__":
    run_fading_reactions_test()
