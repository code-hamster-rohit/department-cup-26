"""
Official Rules & Regulations for Inter-Department Sports Meet (Department Cup 2026)
IIT Roorkee, Saharanpur Campus.

Matches the 12 primary tournament sports mapped directly to MongoDB collections:
  - cricket
  - box_cricket
  - football
  - volleyball
  - badminton
  - table_tennis
  - carrom
  - tug_of_war
  - shotput
  - discuss_throw
  - long_jump
  - basketball
"""

from typing import Any

# Primary 12 Sports Configuration & Limits
SPORTS_CONFIG: dict[str, dict[str, Any]] = {
    "badminton": {
        "id": "badminton",
        "collection_name": "badminton",
        "name": "Badminton",
        "category": "Racquet",
        "icon": "🏸",
        "main_count": 2,
        "sub_max": 2,
        "formula": "1-2 Players",
        "squad_notation": "Singles (1) or Doubles (2)",
        "squad_badge": "Singles / Doubles",
        "gender_badge": "🏸 Badminton Match",
        "gender_rule_desc": "Admin enters playing athletes on the spot (Singles: 1 player, Doubles: 2 players).",
        "description": "Best of 3 sets to 21 points (or 15 points per agreement). First to win 2 sets wins the match.",
        "default_gender": "Open",
    },
    "basketball": {
        "id": "basketball",
        "collection_name": "basketball",
        "name": "Basketball",
        "category": "Court",
        "icon": "🏀",
        "main_count": 6,
        "sub_max": 2,
        "formula": "6 + 2",
        "squad_notation": "Team Shooters (up to 8 participants)",
        "squad_badge": "Team Shooters",
        "gender_badge": "🏀 Team Shootout",
        "gender_rule_desc": "Participants take designated shots from 3-point, 2-point, and 1-point zones.",
        "description": "Department shootout challenge. Cumulative total score determines the winning department.",
        "default_gender": "Open",
    },
    "box_cricket": {
        "id": "box_cricket",
        "collection_name": "box_cricket",
        "name": "Box Cricket",
        "category": "Cricket",
        "icon": "🏏",
        "main_count": 5,
        "sub_max": 3,
        "formula": "5 + 3",
        "squad_notation": "5 Playing + up to 3 Substitutes",
        "squad_badge": "5 Playing + up to 3 Subs",
        "gender_badge": "🏏 Fast-Paced Box Match",
        "gender_rule_desc": "5 Playing players (or 6 by mutual agreement) + up to 3 bench substitutes.",
        "description": "6-over match, min 3 bowlers. Last batter cannot bat alone (all out on 4th wicket).",
        "default_gender": "Open",
    },
    "carrom": {
        "id": "carrom",
        "collection_name": "carrom",
        "name": "Carrom",
        "category": "Board",
        "icon": "🎯",
        "main_count": 2,
        "sub_max": 2,
        "formula": "1-2 Players",
        "squad_notation": "Singles (1) or Doubles (2)",
        "squad_badge": "Singles / Doubles",
        "gender_badge": "🎯 Carrom Match",
        "gender_rule_desc": "Admin enters playing athletes on the spot (Singles: 1 player, Doubles: 2 players).",
        "description": "Single match played up to 29 points or 8 boards. First side to 29 points wins.",
        "default_gender": "Open",
    },
    "cricket": {
        "id": "cricket",
        "collection_name": "cricket",
        "name": "Cricket",
        "category": "Cricket",
        "icon": "🏏",
        "main_count": 11,
        "sub_max": 4,
        "formula": "11 + 4",
        "squad_notation": "11 Playing + up to 4 Substitutes (Bench)",
        "squad_badge": "11 Playing + up to 4 Subs",
        "gender_badge": "🏏 10-Over Limited Overs",
        "gender_rule_desc": "11 Playing Players + up to 4 Substitutes on bench.",
        "description": "10-over limited overs format (15 overs for finals). Max 2 overs per bowler, powerplay overs 1-3. No LBW. Free hits on no-balls.",
        "default_gender": "Open",
    },
    "discuss_throw": {
        "id": "discuss_throw",
        "collection_name": "discuss_throw",
        "name": "Discuss Throw",
        "category": "Athletics",
        "icon": "🥏",
        "main_count": 2,
        "sub_max": 1,
        "formula": "2 + 1",
        "squad_notation": "2 Athletes + 1 Substitute",
        "squad_badge": "2 Athletes + 1 Sub",
        "gender_badge": "🥏 Athletics Field",
        "gender_rule_desc": "2 Registered Throwers + 1 Substitute.",
        "description": "1 trial throw + 3 official attempts per athlete. Best valid distance in meters determines winner.",
        "default_gender": "Open",
    },
    "football": {
        "id": "football",
        "collection_name": "football",
        "name": "Football",
        "category": "Field",
        "icon": "⚽",
        "main_count": 7,
        "sub_max": 3,
        "formula": "7 + 3",
        "squad_notation": "7 Playing + up to 3 Substitutes",
        "squad_badge": "7 Playing + up to 3 Subs",
        "gender_badge": "⚽ Half-Ground 7v7",
        "gender_rule_desc": "7 Playing Players on pitch + up to 3 bench substitutes.",
        "description": "Two halves of 25 minutes. Extra time (10m) and penalty shootout (5 kicks + sudden death) to resolve draws.",
        "default_gender": "Open",
    },
    "long_jump": {
        "id": "long_jump",
        "collection_name": "long_jump",
        "name": "Long Jump",
        "category": "Athletics",
        "icon": "🏃",
        "main_count": 2,
        "sub_max": 1,
        "formula": "2 + 1",
        "squad_notation": "2 Athletes + 1 Substitute",
        "squad_badge": "2 Athletes + 1 Sub",
        "gender_badge": "🏃 Athletics Jump",
        "gender_rule_desc": "2 Registered Jumpers + 1 Substitute.",
        "description": "1 trial jump + 3 official attempts. Longest valid jump in meters wins.",
        "default_gender": "Open",
    },
    "shotput": {
        "id": "shotput",
        "collection_name": "shotput",
        "name": "Shotput",
        "category": "Athletics",
        "icon": "☄️",
        "main_count": 2,
        "sub_max": 1,
        "formula": "2 + 1",
        "squad_notation": "2 Athletes + 1 Substitute",
        "squad_badge": "2 Athletes + 1 Sub",
        "gender_badge": "☄️ Athletics Field",
        "gender_rule_desc": "2 Registered Throwers + 1 Substitute.",
        "description": "1 trial throw + 3 official attempts per athlete. Best distance in meters determines winner.",
        "default_gender": "Open",
    },
    "table_tennis": {
        "id": "table_tennis",
        "collection_name": "table_tennis",
        "name": "Table Tennis",
        "category": "Racquet",
        "icon": "🏓",
        "main_count": 2,
        "sub_max": 2,
        "formula": "1-2 Players",
        "squad_notation": "Singles (1) or Doubles (2)",
        "squad_badge": "Singles / Doubles",
        "gender_badge": "🏓 Table Tennis Match",
        "gender_rule_desc": "Admin enters playing athletes on the spot (Singles: 1 player, Doubles: 2 players).",
        "description": "Best of 3 sets to 11 points (2-point lead required at deuce). First to win 2 sets wins the match.",
        "default_gender": "Open",
    },
    "tug_of_war": {
        "id": "tug_of_war",
        "collection_name": "tug_of_war",
        "name": "Tug of War",
        "category": "Field",
        "icon": "🪢",
        "main_count": 7,
        "sub_max": 2,
        "formula": "7 + 2",
        "squad_notation": "7 Pullers + up to 2 Substitutes",
        "squad_badge": "7 Pullers + up to 2 Subs",
        "gender_badge": "🪢 Best of 3 Pulls",
        "gender_rule_desc": "7 active pullers + up to 2 substitutes.",
        "description": "Best of 3 pulls. Tape mark must cross the department boundary line for victory.",
        "default_gender": "Open",
    },
    "volleyball": {
        "id": "volleyball",
        "collection_name": "volleyball",
        "name": "Volleyball",
        "category": "Court",
        "icon": "🏐",
        "main_count": 6,
        "sub_max": 2,
        "formula": "6 + 2",
        "squad_notation": "6 Playing + up to 2 Substitutes",
        "squad_badge": "6 Playing + up to 2 Subs",
        "gender_badge": "🏐 Best of 3 Sets",
        "gender_rule_desc": "6 Playing Players on court + up to 2 substitutes.",
        "description": "Best of 3 sets. First two sets to 25 points (2-point lead required, cap at 30). Deciding set to 15 points.",
        "default_gender": "Open",
    },
}

# Detailed Tournament Rules & Match Engine Formats
RULES_DATA: dict[str, dict[str, Any]] = {
    "badminton": {
        "id": "badminton",
        "collection_name": "badminton",
        "sport_type": "badminton",
        "name": "Badminton",
        "category": "Racquet",
        "icon": "🏸",
        "squad": {
            "playing_count": 2,
            "max_substitutes": 2,
            "notation": "1-2 Players (Singles or Doubles)",
            "rules": [
                "Singles: 1 player per side. Doubles: 2 players per side.",
                "Admin enters player names during match setup."
            ]
        },
        "match_format": {
            "sets_to_win": 2,
            "max_sets": 3,
            "points_per_set": 21,
            "cap_points": 30
        },
        "specific_regulations": [
            {
                "title": "Match Format",
                "badge": "🏸 BEST OF 3 SETS",
                "desc": "Single match: Best of 3 sets to 21 points (or 15 points by agreement). First to win 2 sets wins the match."
            },
            {
                "title": "Scoring & Deuce",
                "badge": "21 PTS (DEUCE +2)",
                "desc": "At 20-all, side leading by 2 wins; golden point cap at 30."
            }
        ]
    },

    "basketball": {
        "id": "basketball",
        "collection_name": "basketball",
        "sport_type": "basketball_shootout",
        "name": "Basketball",
        "category": "Court",
        "icon": "🏀",
        "squad": {
            "playing_count": 6,
            "max_substitutes": 2,
            "notation": "Team Shooters (up to 8 participants)",
            "rules": [
                "Each participant may take at most 5 shots.",
                "Each participant may take shots only once."
            ]
        },
        "match_format": {
            "zones": [
                {"points": 3, "name": "3-Point Line", "desc": "Designated 3-point line"},
                {"points": 2, "name": "2-Point Area", "desc": "Designated 2-point area"},
                {"points": 1, "name": "1-Point Area", "desc": "Designated 1-point area"}
            ],
            "ranking_basis": "Highest cumulative department score"
        },
        "specific_regulations": [
            {
                "title": "Scoring Zones",
                "badge": "🏀 3-PT / 2-PT / 1-PT",
                "desc": "Shooters choose zones: 3 pts (outside arc), 2 pts (mid-range), 1 pt (free throw). Successful shot awards points."
            },
            {
                "title": "Department Winner",
                "badge": "📊 TOTAL POINTS",
                "desc": "All individual scores sum into the department's cumulative total score. Department with highest points wins."
            }
        ]
    },

    "box_cricket": {
        "id": "box_cricket",
        "collection_name": "box_cricket",
        "sport_type": "cricket",
        "name": "Box Cricket",
        "category": "Cricket",
        "icon": "🏏",
        "squad": {
            "playing_count": 5,
            "max_substitutes": 3,
            "can_agree_6": True,
            "notation": "5 (or 6 by mutual agreement) Playing + up to 3 Substitutes",
            "rules": [
                "Minimum 5 players must participate in each match.",
                "If both captains mutually agree before the match, 6 players may participate.",
                "The agreed number of players must remain unchanged throughout the match."
            ]
        },
        "match_format": {
            "innings_overs": 6,
            "min_bowlers": 3,
            "max_overs_per_bowler": 2,
            "pitch_distance_meters": 17,
            "no_powerplay": True,
            "fielding_restrictions": False,
            "all_out_wicket": 4
        },
        "specific_regulations": [
            {
                "title": "All-Out Condition",
                "badge": "⚠️ LAST BATTER RULE",
                "desc": "Innings ends on the 4th wicket (or 5th wicket if 6 players). Last batter cannot bat alone."
            },
            {
                "title": "Bowling Restrictions",
                "badge": "🔄 MIN 3 BOWLERS",
                "desc": "Minimum 3 different bowlers must be used. Bowlers cannot bowl consecutive overs. Max 2 overs per bowler."
            },
            {
                "title": "No-ball & Free Hit",
                "badge": "🎯 FREE HIT",
                "desc": "2nd bouncer, waist-height full toss, or overstepping is a No-ball + Free Hit."
            }
        ]
    },

    "carrom": {
        "id": "carrom",
        "collection_name": "carrom",
        "sport_type": "carrom",
        "name": "Carrom",
        "category": "Board",
        "icon": "🎯",
        "squad": {
            "playing_count": 2,
            "max_substitutes": 1,
            "notation": "1-2 Players (Singles or Doubles)",
            "rules": [
                "Singles: 1 player per side. Doubles: 2 players per side.",
                "Admin enters player names during match setup."
            ]
        },
        "match_format": {
            "points_target": 29,
            "max_boards": 8
        },
        "specific_regulations": [
            {
                "title": "Match Format",
                "badge": "🎯 29 PTS / 8 BOARDS",
                "desc": "Single match played up to 29 points or a maximum of 8 boards. First side to 29 points wins."
            },
            {
                "title": "Board Scoring",
                "badge": "QUEEN +3",
                "desc": "1 pt per opponent carrom piece left on board + 3 bonus pts for queen if covered."
            }
        ]
    },

    "cricket": {
        "id": "cricket",
        "collection_name": "cricket",
        "sport_type": "cricket",
        "name": "Cricket",
        "category": "Cricket",
        "icon": "🏏",
        "squad": {
            "playing_count": 11,
            "max_substitutes": 4,
            "notation": "11 Playing + up to 4 Substitutes (Bench)",
            "rules": [
                "Only registered 11 players can participate on the field during the match.",
                "Substitutes are allowed for fielding purposes only. They cannot bat, bowl, or act as captain or wicketkeeper."
            ]
        },
        "match_format": {
            "innings_overs": 10,
            "finals_overs": 15,
            "max_overs_per_bowler": 2,
            "powerplay_overs": 3,
            "powerplay_circle_limit": 2,
            "post_powerplay_circle_limit": 5,
            "tie_breaker": "Super Over"
        },
        "specific_regulations": [
            {
                "title": "LBW Rule",
                "badge": "🚫 NO LBW",
                "desc": "LBW (Leg Before Wicket) will NOT be applicable."
            },
            {
                "title": "Free Hit on No-ball",
                "badge": "🎯 FREE HIT",
                "desc": "2nd bouncer in an over is a No-ball + Free Hit. Batter can be dismissed ONLY by run out on Free Hit."
            },
            {
                "title": "Powerplay & Fielding",
                "badge": "⚡ PP: Overs 1-3",
                "desc": "First 3 overs: max 2 fielders outside 30-yard circle. After PP: max 5 outside."
            }
        ]
    },

    "discuss_throw": {
        "id": "discuss_throw",
        "collection_name": "discuss_throw",
        "sport_type": "athletics_distance",
        "name": "Discuss Throw",
        "category": "Athletics",
        "icon": "🥏",
        "squad": {
            "playing_count": 2,
            "max_substitutes": 1,
            "notation": "2 Athletes + 1 Substitute",
            "rules": [
                "Each department fields 2 athletes + up to 1 substitute.",
                "Substitutions must be announced before trials begin."
            ]
        },
        "match_format": {
            "unit": "meters",
            "trial_attempts": 1,
            "official_attempts": 3,
            "ranking_basis": "Best valid distance"
        },
        "specific_regulations": [
            {
                "title": "Throws Format",
                "badge": "🥏 3 OFFICIAL THROWS",
                "desc": "1 trial throw + 3 official attempts. Best valid distance in meters determines athlete rank."
            }
        ]
    },

    "football": {
        "id": "football",
        "collection_name": "football",
        "sport_type": "football",
        "name": "Football",
        "category": "Field",
        "icon": "⚽",
        "squad": {
            "playing_count": 7,
            "max_substitutes": 3,
            "notation": "7 Playing + up to 3 Substitutes",
            "rules": [
                "Matches played with 7 players per team on half the football ground.",
                "Substitutions permitted with match official consent."
            ]
        },
        "match_format": {
            "half_duration_mins": 25,
            "half_time_break_mins": 5,
            "extra_time_mins": 10,
            "penalty_shootout_kicks": 5,
            "sudden_death": True
        },
        "specific_regulations": [
            {
                "title": "Pitch & Halves",
                "badge": "⏱️ 2 x 25 MINS",
                "desc": "Two halves of 25 minutes each on half of the football ground. 5-minute halftime break."
            },
            {
                "title": "Draw Resolution",
                "badge": "🥅 EXTRA TIME & PENALTIES",
                "desc": "If tied: 10 minutes extra time (5m + 2m break + 5m). Still tied: 5 penalty kicks per team, then sudden death."
            }
        ]
    },

    "long_jump": {
        "id": "long_jump",
        "collection_name": "long_jump",
        "sport_type": "athletics_distance",
        "name": "Long Jump",
        "category": "Athletics",
        "icon": "🏃",
        "squad": {
            "playing_count": 2,
            "max_substitutes": 1,
            "notation": "2 Athletes + 1 Substitute",
            "rules": [
                "Each department fields 2 athletes + up to 1 substitute.",
                "Take-off must occur before or on the foul board."
            ]
        },
        "match_format": {
            "unit": "meters",
            "trial_attempts": 1,
            "official_attempts": 3,
            "ranking_basis": "Longest valid jump"
        },
        "specific_regulations": [
            {
                "title": "Jumps Format",
                "badge": "🏃 3 OFFICIAL JUMPS",
                "desc": "1 trial jump + 3 official attempts. Longest valid jump wins."
            }
        ]
    },

    "shotput": {
        "id": "shotput",
        "collection_name": "shotput",
        "sport_type": "athletics_distance",
        "name": "Shotput",
        "category": "Athletics",
        "icon": "☄️",
        "squad": {
            "playing_count": 2,
            "max_substitutes": 1,
            "notation": "2 Athletes + 1 Substitute",
            "rules": [
                "Each department fields 2 athletes + up to 1 substitute.",
                "Shot must be pushed from the shoulder with one hand only."
            ]
        },
        "match_format": {
            "unit": "meters",
            "trial_attempts": 1,
            "official_attempts": 3,
            "ranking_basis": "Best valid distance"
        },
        "specific_regulations": [
            {
                "title": "Attempts Format",
                "badge": "☄️ 3 OFFICIAL THROWS",
                "desc": "1 trial throw + 3 official attempts. Longest valid throw in meters wins."
            }
        ]
    },

    "table_tennis": {
        "id": "table_tennis",
        "collection_name": "table_tennis",
        "sport_type": "table_tennis",
        "name": "Table Tennis",
        "category": "Racquet",
        "icon": "🏓",
        "squad": {
            "playing_count": 2,
            "max_substitutes": 2,
            "notation": "1-2 Players (Singles or Doubles)",
            "rules": [
                "Singles: 1 player per side. Doubles: 2 players per side.",
                "Admin enters player names during match setup."
            ]
        },
        "match_format": {
            "sets_to_win": 2,
            "max_sets": 3,
            "points_per_set": 11,
            "cap_points": 15
        },
        "specific_regulations": [
            {
                "title": "Match Format",
                "badge": "🏓 BEST OF 3 SETS",
                "desc": "Single match: Best of 3 sets to 11 points. First to win 2 sets wins the match."
            },
            {
                "title": "Set Rules",
                "badge": "11 POINTS (DEUCE +2)",
                "desc": "Each set to 11 points. 2 points clear needed at 10-all."
            }
        ]
    },

    "tug_of_war": {
        "id": "tug_of_war",
        "collection_name": "tug_of_war",
        "sport_type": "tug_of_war",
        "name": "Tug of War",
        "category": "Field",
        "icon": "🪢",
        "squad": {
            "playing_count": 7,
            "max_substitutes": 2,
            "notation": "7 Pullers + up to 2 Substitutes",
            "rules": [
                "7 active pullers + up to 2 substitutes.",
                "Spikes, cleats, or footwear with protrusions are strictly prohibited."
            ]
        },
        "match_format": {
            "pulls_to_win": 2,
            "max_pulls": 3
        },
        "specific_regulations": [
            {
                "title": "Match Format",
                "badge": "🪢 BEST OF 3 PULLS",
                "desc": "Best of 3 pulls. First department to win 2 pulls wins the match."
            },
            {
                "title": "Win Condition",
                "badge": "🏁 BOUNDARY MARK",
                "desc": "Tape mark on rope must cross the winning boundary line completely."
            }
        ]
    },

    "volleyball": {
        "id": "volleyball",
        "collection_name": "volleyball",
        "sport_type": "volleyball",
        "name": "Volleyball",
        "category": "Court",
        "icon": "🏐",
        "squad": {
            "playing_count": 6,
            "max_substitutes": 2,
            "notation": "6 Playing + up to 2 Substitutes",
            "rules": [
                "6 players on court + up to 2 substitutes.",
                "Rotations and standard volleyball regulations apply."
            ]
        },
        "match_format": {
            "sets_to_win": 2,
            "max_sets": 3,
            "set_1_2_points": 25,
            "decider_points": 15,
            "cap_points": 30
        },
        "specific_regulations": [
            {
                "title": "Set Points",
                "badge": "🏐 25 PTS (CAP 30)",
                "desc": "First 2 sets played to 25 points (must lead by 2, capped at 30). Deciding 3rd set to 15 points."
            },
            {
                "title": "Victory",
                "badge": "🏆 BEST OF 3 SETS",
                "desc": "First department to win 2 sets wins the volleyball match."
            }
        ]
    }
}

# Legacy and category aliases redirecting to the 12 primary sport collections
SPORT_ALIASES: dict[str, str] = {
    "cricket_boys": "cricket",
    "box_cricket_girls": "box_cricket",
    "football_boys": "football",
    "football_girls": "football",
    "volleyball_boys": "volleyball",
    "badminton_mix": "badminton",
    "tt_boys": "table_tennis",
    "carrom_mix": "carrom",
    "tow_boys": "tug_of_war",
    "tow_girls": "tug_of_war",
    "shotput_boys": "shotput",
    "shotput_girls": "shotput",
    "discus_boys": "discuss_throw",
    "discus_girls": "discuss_throw",
    "discus_throw": "discuss_throw",
    "long_jump_boys": "long_jump",
    "long_jump_girls": "long_jump",
    "basketball_shootout": "basketball",
}


def get_all_sports() -> list[dict[str, Any]]:
    """Returns the 12 primary tournament sports for match creation and display."""
    return list(RULES_DATA.values())


def get_sport_rule(sport_id: str) -> dict[str, Any] | None:
    """Returns the sport rule, resolving aliases if needed."""
    if not sport_id:
        return None
    sid = sport_id.lower().strip()
    if sid in RULES_DATA:
        return RULES_DATA[sid]
    target_id = SPORT_ALIASES.get(sid)
    if target_id and target_id in RULES_DATA:
        return RULES_DATA[target_id]
    return None


def get_sports_config() -> dict[str, dict[str, Any]]:
    """Returns the 12 primary sports configuration map."""
    return SPORTS_CONFIG
