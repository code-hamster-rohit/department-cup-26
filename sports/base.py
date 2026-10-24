"""
Base utilities and helpers for Department Cup sport scoring modules.
"""

from datetime import datetime
from typing import Any


def current_time_str() -> str:
    """Returns current UTC time in HH:MM format."""
    return datetime.utcnow().strftime("%H:%M")


def add_commentary(
    match: dict[str, Any],
    ball_or_tag: str,
    text: str,
    badge: str = "UPDATE",
    comment_type: str = "info"
) -> None:
    """Helper to uniformly append a commentary item to match state."""
    if "commentary" not in match:
        match["commentary"] = []
    match["commentary"].append({
        "time": current_time_str(),
        "ball": str(ball_or_tag),
        "text": text,
        "badge": badge,
        "type": comment_type
    })
