"""
Department Cup 2026 - Central Sports Registry.
Decouples each sport's scoring rules and score initialization into its own clean module.
"""

from typing import Any, Callable

from sports import (
    cricket,
    football,
    volleyball,
    badminton,
    table_tennis,
    carrom,
    tug_of_war,
    athletics,
    basketball,
)

# Registry mapping normalized sport_type/sport_id to module handlers
SPORTS_REGISTRY: dict[str, Any] = {
    "cricket": cricket,
    "box_cricket": cricket,
    "cricket_boys": cricket,
    "box_cricket_girls": cricket,

    "football": football,
    "football_boys": football,
    "football_girls": football,
    "penalty_shootout": football,

    "volleyball": volleyball,
    "volleyball_boys": volleyball,

    "badminton": badminton,
    "badminton_mix": badminton,

    "table_tennis": table_tennis,
    "tt_boys": table_tennis,

    "carrom": carrom,
    "carrom_mix": carrom,

    "tug_of_war": tug_of_war,
    "tow_boys": tug_of_war,
    "tow_girls": tug_of_war,

    "athletics_distance": athletics,
    "shotput": athletics,
    "shotput_boys": athletics,
    "shotput_girls": athletics,
    "discus_boys": athletics,
    "discus_girls": athletics,
    "discuss_throw": athletics,
    "long_jump": athletics,
    "long_jump_boys": athletics,
    "long_jump_girls": athletics,

    "basketball": basketball,
    "basketball_shootout": basketball,
}


def get_sport_module(sport_type_or_id: str | None) -> Any:
    """Returns the dedicated scoring module for a given sport type or id."""
    if not sport_type_or_id:
        return cricket
    key = str(sport_type_or_id).lower().strip()
    return SPORTS_REGISTRY.get(key, cricket)


def init_sport_score(sport_rule: dict[str, Any], max_overs: int) -> dict[str, Any]:
    """Initializes the empty score document for a newly created match."""
    stype = sport_rule.get("sport_type") or sport_rule.get("id")
    mod = get_sport_module(stype)
    if hasattr(mod, "init_score"):
        return mod.init_score(sport_rule, max_overs)
    return {}


def handle_sport_action(match: dict[str, Any], action: dict[str, Any]) -> None:
    """Dispatches a score update action to the sport's dedicated module."""
    stype = match.get("sport_type") or match.get("sport_id")
    mod = get_sport_module(stype)
    if hasattr(mod, "handle_action"):
        mod.handle_action(match, action)
    else:
        raise ValueError(f"No scoring handler found for sport type: {stype}")


__all__ = [
    "SPORTS_REGISTRY",
    "get_sport_module",
    "init_sport_score",
    "handle_sport_action",
    "cricket",
    "football",
    "volleyball",
    "badminton",
    "table_tennis",
    "carrom",
    "tug_of_war",
    "athletics",
    "basketball",
]
