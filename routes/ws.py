"""
WebSocket Connection Manager for zero-latency live score streaming.
Supports global live overview channel and per-match channels.
"""

import json
import time
from typing import Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

ws_router = APIRouter()


class ConnectionManager:
    def __init__(self):
        # Global listeners: receive match creation, end, and summary updates
        self.global_connections: list[WebSocket] = []
        # Per-match listeners: match_id -> list[WebSocket]
        self.match_connections: dict[str, list[WebSocket]] = {}

    async def connect_global(self, websocket: WebSocket):
        await websocket.accept()
        self.global_connections.append(websocket)

    def disconnect_global(self, websocket: WebSocket):
        if websocket in self.global_connections:
            self.global_connections.remove(websocket)

    async def connect_match(self, match_id: str, websocket: WebSocket):
        await websocket.accept()
        if match_id not in self.match_connections:
            self.match_connections[match_id] = []
        self.match_connections[match_id].append(websocket)

    def disconnect_match(self, match_id: str, websocket: WebSocket):
        if match_id in self.match_connections:
            if websocket in self.match_connections[match_id]:
                self.match_connections[match_id].remove(websocket)
            if len(self.match_connections[match_id]) == 0:
                del self.match_connections[match_id]

    async def broadcast_match(self, match_id: str, event_type: str, data: dict[str, Any]):
        message = json.dumps({"event": event_type, "match_id": match_id, "data": data}, default=str)
        
        # 1. Broadcast to clients watching this match specifically
        if match_id in self.match_connections:
            dead_sockets = []
            for ws in self.match_connections[match_id]:
                try:
                    await ws.send_text(message)
                except Exception:
                    dead_sockets.append(ws)
            for ds in dead_sockets:
                self.disconnect_match(match_id, ds)

        # 2. Also send summary to global live listeners
        dead_globals = []
        for ws in self.global_connections:
            try:
                await ws.send_text(message)
            except Exception:
                dead_globals.append(ws)
        for ds in dead_globals:
            self.disconnect_global(ds)


manager = ConnectionManager()


@ws_router.websocket("/ws/live")
async def websocket_global_endpoint(websocket: WebSocket):
    await manager.connect_global(websocket)
    try:
        while True:
            # Keep connection alive with heartbeat / client ping or handle live reaction
            msg = await websocket.receive_text()
            if msg == "ping":
                await websocket.send_text("pong")
            else:
                try:
                    payload = json.loads(msg)
                    if payload.get("type") == "REACTION":
                        content = str(payload.get("content", "")).strip()[:60]
                        mid = payload.get("match_id")
                        if content and mid:
                            await manager.broadcast_match(mid, "LIVE_REACTION", {
                                "content": content,
                                "sender": payload.get("sender", "Audience"),
                                "time": time.time()
                            })
                except Exception:
                    pass
    except WebSocketDisconnect:
        manager.disconnect_global(websocket)
    except Exception:
        manager.disconnect_global(websocket)


@ws_router.websocket("/ws/match/{match_id}")
async def websocket_match_endpoint(websocket: WebSocket, match_id: str):
    await manager.connect_match(match_id, websocket)
    try:
        while True:
            msg = await websocket.receive_text()
            if msg == "ping":
                await websocket.send_text("pong")
            else:
                try:
                    payload = json.loads(msg)
                    if payload.get("type") == "REACTION":
                        content = str(payload.get("content", "")).strip()[:60]
                        mid = payload.get("match_id", match_id)
                        if content and mid:
                            await manager.broadcast_match(mid, "LIVE_REACTION", {
                                "content": content,
                                "sender": payload.get("sender", "Audience"),
                                "time": time.time()
                            })
                except Exception:
                    pass
    except WebSocketDisconnect:
        manager.disconnect_match(match_id, websocket)
    except Exception:
        manager.disconnect_match(match_id, websocket)

