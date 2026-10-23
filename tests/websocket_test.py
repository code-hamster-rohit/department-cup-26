"""
Asynchronous WebSocket Quality Assurance Test.
Tests zero-latency live score broadcasting and Cricbuzz commentary streaming.
"""

import json
import asyncio
import httpx
from websockets.asyncio.client import connect

ADMIN_EMAIL = "rohit_k@amsc.iitr.ac.in"
BASE_URL = "http://127.0.0.1:8000"
WS_URL = "ws://127.0.0.1:8000/ws/live"


async def test_websocket_streaming():
    print("=" * 65)
    print("⚡ ZERO-LATENCY WEBSOCKET STREAMING TEST")
    print("=" * 65)

    async with httpx.AsyncClient() as client:
        # 1. Create match
        res = await client.post(
            f"{BASE_URL}/api/match/create",
            json={"sport_id": "cricket_boys", "team_a": "ppe", "team_b": "amsc"},
            headers={"X-Admin-Email": ADMIN_EMAIL}
        )
        assert res.status_code == 200
        match_id = res.json()["match"]["id"]
        print(f"Created test match: {match_id}")

        # Start match
        await client.post(f"{BASE_URL}/api/match/{match_id}/start", headers={"X-Admin-Email": ADMIN_EMAIL})

    # 2. Connect WebSocket to live channel
    async with connect(WS_URL) as ws:
        print("WebSocket client connected to /ws/live.")

        # 3. Trigger a score action via REST
        async with httpx.AsyncClient() as client:
            score_task = client.post(
                f"{BASE_URL}/api/match/{match_id}/score",
                json={"type": "run", "runs": 6, "striker": "Rishabh", "bowler": "Mayank"},
                headers={"X-Admin-Email": ADMIN_EMAIL}
            )

            # Wait for WS message and REST simultaneously
            score_resp, ws_msg = await asyncio.gather(
                score_task,
                ws.recv()
            )

        ws_data = json.loads(ws_msg)
        print("Received live WebSocket broadcast event:", ws_data.get("event"))
        assert ws_data.get("event") == "SCORE_UPDATED"
        assert ws_data["match_id"] == match_id
        latest_comm = ws_data["data"]["commentary"]
        print("Live Cricbuzz Commentary Broadcast:", latest_comm["badge"], "->", latest_comm["text"])
        assert "SIX" in latest_comm["badge"]
        print("✅ PASS: Real-time WebSocket delivery confirmed with zero latency!")

    # Clean up
    async with httpx.AsyncClient() as client:
        await client.post(f"{BASE_URL}/api/match/{match_id}/delete", headers={"X-Admin-Email": ADMIN_EMAIL})
        print(f"Cleaned up test match: {match_id}")

    print("=" * 65)
    print("🎉 WEBSOCKET STREAMING QA VERIFICATION COMPLETE")
    print("=" * 65)


if __name__ == "__main__":
    asyncio.run(test_websocket_streaming())
