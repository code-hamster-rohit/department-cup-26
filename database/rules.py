"""
Official Rules & Regulations for Inter-Department Sports Meet (Department Cup 2026)
IIT Roorkee, Saharanpur Campus
Directly transcribed from the official tournament rulebook PDF.
"""

from typing import Any

RULES_DATA: dict[str, dict[str, Any]] = {
    "cricket_boys": {
        "id": "cricket_boys",
        "sport_type": "cricket",
        "name": "Cricket (boys)",
        "category": "Boys",
        "icon": "🏏",
        "squad": {
            "playing_count": 11,
            "max_substitutes": 4,
            "gender": "Boy",
            "notation": "11 Playing + up to 4 Substitutes (Bench)",
            "rules": [
                "Only registered 11 players can participate on the field during the match.",
                "Substitutes are allowed for fielding purposes only. They cannot bat, bowl, or act as captain or wicketkeeper.",
                "Concussion substitutes are not allowed."
            ]
        },
        "match_format": {
            "innings_overs": 10,
            "finals_overs": 15,
            "max_overs_per_bowler": 2,
            "powerplay_overs": 3,
            "powerplay_circle_limit": 2,
            "post_powerplay_circle_limit": 5,
            "tie_breaker": "Super Over (if time/ground permits, as decided by conducting team)"
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
                "desc": "2nd bouncer in an over is a No-ball + Free Hit. Ball bouncing twice or more before reaching batter is a No-ball + Free Hit. On a Free Hit, the batter can be dismissed ONLY by run out."
            },
            {
                "title": "Powerplay & Fielding",
                "badge": "⚡ PP: Overs 1-3",
                "desc": "First 3 overs: max 2 fielders outside 30-yard circle. After PP: max 5 outside. Violation results in a No-ball."
            },
            {
                "title": "Equipment Restriction",
                "badge": "🧤 NO KEEPING GLOVES",
                "desc": "Wicket keeping gloves are NOT allowed. Standard designated cricket bat and ball only."
            },
            {
                "title": "Late Arrival Penalty",
                "badge": "⏱️ LATE ARRIVAL",
                "desc": "If one team fails to report on time: opposing team receives 5 runs advantage. If both teams fail: 1 over deducted from each team's innings."
            }
        ]
    },

    "box_cricket_girls": {
        "id": "box_cricket_girls",
        "sport_type": "cricket",
        "name": "Box Cricket (girls)",
        "category": "Girls",
        "icon": "🏏",
        "squad": {
            "playing_count": 5,
            "max_substitutes": 3,
            "can_agree_6": True,
            "gender": "Girl",
            "notation": "5 (or 6 by mutual agreement) Playing + up to 3 Substitutes",
            "rules": [
                "Minimum 5 female players must participate in each match.",
                "If both captains mutually agree before the match, 6 female players may participate.",
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
            "all_out_wicket": 4  # 4th wicket falls when 5 players; 5th when 6 players
        },
        "specific_regulations": [
            {
                "title": "All-Out Condition",
                "badge": "⚠️ LAST BATTER RULE",
                "desc": "If 5 players participate, innings ends on the 4th wicket (last batter cannot continue without a partner). If 6 players, innings ends on 5th wicket."
            },
            {
                "title": "Bowling Restrictions",
                "badge": "🔄 MIN 3 BOWLERS",
                "desc": "A minimum of 3 different bowlers must be used. Bowler cannot bowl consecutive overs. Max 2 overs per bowler."
            },
            {
                "title": "No-ball & Free Hit",
                "badge": "🎯 FREE HIT ON NO-BALL",
                "desc": "2nd bouncer, waist-height full toss, overstepping, or first bounce outside pitch = No-ball + Free Hit. Batter can only be run out on Free Hit."
            },
            {
                "title": "Dead Ball Precedence",
                "badge": "🛑 DEAD BALL RULES",
                "desc": "Ball bouncing more than once before batting crease = Dead Ball. If multiple bounce + wide = Dead Ball. If overstep + multiple bounce = No-ball (overstep takes precedence)."
            },
            {
                "title": "Special Dead Ball Penalty",
                "badge": "🚨 6 RUNS + RE-BOWL",
                "desc": "If a bowler delivers a Dead ball and bowling team changes the bowler: over is cancelled, batting team awarded 6 runs, and entire over is re-bowled by a different bowler!"
            },
            {
                "title": "Late Arrival Penalty",
                "badge": "⏱️ LATE ARRIVAL",
                "desc": "5 runs advantage if one team late; 1 over deducted if both teams late."
            }
        ]
    },

    "football_boys": {
        "id": "football_boys",
        "sport_type": "football",
        "name": "Football (boys)",
        "category": "Boys",
        "icon": "⚽",
        "squad": {
            "playing_count": 7,
            "max_substitutes": 3,
            "gender": "Boy",
            "notation": "7 Playing + up to 3 Substitutes",
            "rules": [
                "Matches played with 7 players per team on half the football ground.",
                "Substitutions permitted with match official consent."
            ]
        },
        "match_format": {
            "half_duration_mins": 25,
            "half_time_break_mins": 5,
            "extra_time_mins": 10,  # 5 min + 2 min break + 5 min
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
            },
            {
                "title": "Late Arrival",
                "badge": "⏱️ 5 MIN REDUCTION",
                "desc": "If both teams fail to report on time, total match duration is reduced by 5 minutes."
            },
            {
                "title": "Language Conduct",
                "badge": "🟥 CONDUCT APOLOGY",
                "desc": "Foul or abusive language requires the player to apologize immediately on the spot, or face strict disciplinary action."
            }
        ]
    },

    "football_girls": {
        "id": "football_girls",
        "sport_type": "penalty_shootout",
        "name": "Football Penalty Shootout (girls)",
        "category": "Girls",
        "icon": "⚽",
        "squad": {
            "playing_count": 3,
            "max_substitutes": 2,
            "can_participate_all_5": True,
            "gender": "Girl",
            "notation": "3 (or all 5 if present) Playing + Substitutes",
            "rules": [
                "Each team registers 3 players + 2 subs.",
                "If all 5 registered players are present from both teams, teams participate with all 5 players."
            ]
        },
        "match_format": {
            "shots_per_player": 5,
            "total_shots_3_players": 15,
            "total_shots_5_players": 25,
            "tie_breaker": "Sudden-death penalty shootout (1 shot per round)"
        },
        "specific_regulations": [
            {
                "title": "Shot Allocation",
                "badge": "🎯 5 SHOTS / PLAYER",
                "desc": "Each participating player takes 5 penalty shots. (15 shots total if 3 players; 25 shots if 5 players)."
            },
            {
                "title": "Goalkeeper Rule",
                "badge": "🧤 GOAL LINE STANCE",
                "desc": "Designated GK from opposing team must remain on the goal line until the ball is kicked."
            },
            {
                "title": "Sudden Death",
                "badge": "⚡ SUDDEN DEATH",
                "desc": "If goals are tied after all scheduled shots, sudden death 1-shot rounds determine the winner."
            }
        ]
    },

    "volleyball_boys": {
        "id": "volleyball_boys",
        "sport_type": "volleyball",
        "name": "Volleyball (boys)",
        "category": "Boys",
        "icon": "🏐",
        "squad": {
            "playing_count": 6,
            "max_substitutes": 3,
            "gender": "Boy",
            "notation": "6 Playing + up to 3 Substitutes",
            "rules": ["Only 6 players per team on the court at any given time."]
        },
        "match_format": {
            "sets_format": "Best of 3 Sets",
            "target_sets": 2,
            "points_per_set": 25,
            "win_margin": 2,
            "deuce_threshold": 24,
            "scoring_system": "Rally-point scoring"
        },
        "specific_regulations": [
            {
                "title": "Sets Format",
                "badge": "🏆 BEST OF 3 SETS",
                "desc": "First team to win 2 sets wins match. Sets played to 25 points with minimum 2-point lead. At 24-24 deuce continues until 2-point lead."
            },
            {
                "title": "Late Arrival Penalty",
                "badge": "⚠️ 2-POINT ADJUSTMENT",
                "desc": "If one team is late, opponent receives 2-point advantage. If both late, 2-point disadvantage applied."
            }
        ]
    },

    "badminton_mix": {
        "id": "badminton_mix",
        "sport_type": "badminton",
        "name": "Badminton (mix)",
        "category": "Mixed",
        "icon": "🏸",
        "squad": {
            "composition": "2 Boys + 2 Girls + 2 Substitutes (1 Boy, 1 Girl)",
            "max_events_per_player": 2,
            "notation": "4 Playing (2B + 2G) + 2 Subs (1B + 1G)",
            "rules": [
                "Each player may participate in a maximum of 2 events out of the 5 events.",
                "Events: Boys' Singles, Girls' Singles, Mixed Doubles, Girls' Doubles, Boys' Doubles."
            ]
        },
        "match_format": {
            "events_count": 5,
            "events_to_win": 3,
            "events_list": [
                {"id": "bs", "name": "Boys' Singles", "type": "singles"},
                {"id": "gs", "name": "Girls' Singles", "type": "singles"},
                {"id": "xd", "name": "Mixed Doubles", "type": "doubles"},
                {"id": "gd", "name": "Girls' Doubles", "type": "doubles"},
                {"id": "bd", "name": "Boys' Doubles", "type": "doubles"}
            ],
            "sets_per_event": "Best of 3 Sets",
            "points_per_set": 15,
            "win_margin": 2,
            "golden_point_cap": 21
        },
        "specific_regulations": [
            {
                "title": "Team Victory Condition",
                "badge": "🥇 FIRST TO 3 EVENTS",
                "desc": "Team must win 3 of 5 events. Once 3 events are won, the match ends immediately."
            },
            {
                "title": "Set Scoring & Deuce",
                "badge": "🏸 15 PTS (CAP 21)",
                "desc": "Sets to 15 points. At 14-14, win by 2 points. If score reaches 20-20, first to 21 wins (golden point)!"
            },
            {
                "title": "Late Arrival",
                "badge": "⚠️ 2-POINT ADVANTAGE",
                "desc": "Late arrival awards 2 points to opponent in opening set."
            }
        ]
    },

    "tt_boys": {
        "id": "tt_boys",
        "sport_type": "table_tennis",
        "name": "TT (boys)",
        "category": "Boys",
        "icon": "🏓",
        "squad": {
            "playing_count": 3,
            "max_substitutes": 2,
            "gender": "Boy",
            "notation": "3 Playing + up to 2 Substitutes",
            "rules": [
                "Match consists of 3 events: Singles, Doubles, Reverse Singles.",
                "Reverse singles MUST feature the player who did not play in the first singles."
            ]
        },
        "match_format": {
            "events_count": 3,
            "events_to_win": 2,
            "events_list": [
                {"id": "singles", "name": "Singles", "type": "singles"},
                {"id": "doubles", "name": "Doubles", "type": "doubles"},
                {"id": "reverse_singles", "name": "Reverse Singles", "type": "singles"}
            ],
            "games_per_event": "Best of 3 Games",
            "points_per_game": 11,
            "win_margin": 2
        },
        "specific_regulations": [
            {
                "title": "Match Format",
                "badge": "🏓 BEST OF 3 EVENTS",
                "desc": "Team that wins 2 of 3 events wins match. Third event skipped if 2-0."
            },
            {
                "title": "Game Scoring",
                "badge": "11 PTS (WIN BY 2)",
                "desc": "11 points per game. At 10-10 deuce until 2-point lead. Service alternates every 2 points (every 1 point at deuce)."
            },
            {
                "title": "Late Arrival",
                "badge": "⚠️ 2-POINT ADVANTAGE",
                "desc": "2-point advantage to opponent in opening game."
            }
        ]
    },

    "carrom_mix": {
        "id": "carrom_mix",
        "sport_type": "carrom",
        "name": "Carrom (mix)",
        "category": "Mixed",
        "icon": "🎯",
        "squad": {
            "composition": "1 Boy + 1 Girl + 2 Substitutes (1 Boy, 1 Girl)",
            "notation": "2 Playing (1B + 1G) + 2 Subs (1B + 1G)",
            "rules": [
                "Events: Boys' Singles, Girls' Singles, Mixed Doubles, Boys' Doubles, Girls' Doubles.",
                "Team that wins at least 3 out of 5 events wins the match."
            ]
        },
        "match_format": {
            "events_count": 5,
            "events_to_win": 3,
            "events_list": [
                {"id": "bs", "name": "Boys' Singles"},
                {"id": "gs", "name": "Girls' Singles"},
                {"id": "xd", "name": "Mixed Doubles"},
                {"id": "bd", "name": "Boys' Doubles"},
                {"id": "gd", "name": "Girls' Doubles"}
            ]
        },
        "specific_regulations": [
            {
                "title": "Queen Cover Rule",
                "badge": "👑 QUEEN + COVER",
                "desc": "Queen must be pocketed and covered by pocketing own carrom man. Cannot cover with opponent carrom man."
            },
            {
                "title": "Striker Penalty",
                "badge": "⚠️ STRIKER FOUL",
                "desc": "Pocketing striker results in penalty of returning 1 previously pocketed carrom man to the board."
            },
            {
                "title": "Team Victory",
                "badge": "🏆 3 OUT OF 5 EVENTS",
                "desc": "First team to win 3 events wins overall match."
            }
        ]
    },

    "tow_boys": {
        "id": "tow_boys",
        "sport_type": "tug_of_war",
        "name": "Tug of War (boys)",
        "category": "Boys",
        "icon": "🪢",
        "squad": {
            "playing_count": 7,
            "max_substitutes": 2,
            "gender": "Boy",
            "notation": "7 Playing + up to 2 Substitutes"
        },
        "match_format": {
            "pulls_format": "Best of 3 Pulls",
            "pulls_to_win": 2
        },
        "specific_regulations": [
            {
                "title": "Pulls Format",
                "badge": "🪢 BEST OF 3 PULLS",
                "desc": "Team that wins 2 out of 3 pulls wins match. Pull won when centre marker crosses winning line."
            },
            {
                "title": "Safety Prohibition",
                "badge": "🚫 NO ROPE WRAPPING",
                "desc": "Wrapping rope around hands, wrists, arms, waist or any body part is strictly prohibited. Sitting or anchoring constitutes a foul."
            }
        ]
    },

    "tow_girls": {
        "id": "tow_girls",
        "sport_type": "tug_of_war",
        "name": "Tug of War (girls)",
        "category": "Girls",
        "icon": "🪢",
        "squad": {
            "playing_count": 5,
            "max_substitutes": 2,
            "gender": "Girl",
            "notation": "5 Playing + up to 2 Substitutes"
        },
        "match_format": {
            "pulls_format": "Best of 3 Pulls",
            "pulls_to_win": 2
        },
        "specific_regulations": [
            {
                "title": "Pulls Format",
                "badge": "🪢 BEST OF 3 PULLS",
                "desc": "Team that wins 2 out of 3 pulls wins match. Pull won when centre marker crosses winning line."
            },
            {
                "title": "Safety Rules",
                "badge": "🚫 NO LOCKING/SITTING",
                "desc": "No wrapping rope around body parts. Substitutions allowed only between pulls."
            }
        ]
    },

    "shotput_boys": {
        "id": "shotput_boys",
        "sport_type": "athletics_distance",
        "name": "Shot Put (boys)",
        "category": "Boys",
        "icon": "☄️",
        "squad": {
            "playing_count": 2,
            "max_substitutes": 1,
            "gender": "Boy",
            "notation": "2 Participating Players + 1 Substitute"
        },
        "match_format": {
            "trial_throws": 1,
            "official_attempts": 3,
            "ranking_basis": "Best valid official distance"
        },
        "specific_regulations": [
            {
                "title": "Attempts & Scoring",
                "badge": "📏 1 TRIAL + 3 OFFICIAL",
                "desc": "1 practice trial throw + 3 official measured attempts. Best valid distance determines ranking. Tie-breaker: next-best valid attempt."
            },
            {
                "title": "Foul Rules",
                "badge": "🚫 EXIT REAR HALF",
                "desc": "Must push from chin/neck with one hand. Stepping on/outside rim or exiting from front is a foul."
            }
        ]
    },

    "shotput_girls": {
        "id": "shotput_girls",
        "sport_type": "athletics_distance",
        "name": "Shot Put (girls)",
        "category": "Girls",
        "icon": "☄️",
        "squad": {
            "playing_count": 1,
            "max_substitutes": 1,
            "gender": "Girl",
            "notation": "1 Participating Player + 1 Substitute"
        },
        "match_format": {
            "trial_throws": 1,
            "official_attempts": 3,
            "ranking_basis": "Best valid official distance"
        },
        "specific_regulations": [
            {
                "title": "Attempts & Ranking",
                "badge": "📏 3 OFFICIAL THROWS",
                "desc": "1 trial throw + 3 official attempts. Best valid distance wins."
            }
        ]
    },

    "discus_boys": {
        "id": "discus_boys",
        "sport_type": "athletics_distance",
        "name": "Discus Throw (boys)",
        "category": "Boys",
        "icon": "🥏",
        "squad": {
            "playing_count": 2,
            "max_substitutes": 1,
            "gender": "Boy",
            "notation": "2 Participating Players + 1 Substitute"
        },
        "match_format": {
            "trial_throws": 1,
            "official_attempts": 3,
            "ranking_basis": "Best valid official distance"
        },
        "specific_regulations": [
            {
                "title": "Attempts & Ranking",
                "badge": "📏 1 TRIAL + 3 OFFICIAL",
                "desc": "1 practice throw + 3 official attempts. Best valid distance determines ranking. Tie-break: next-best valid attempt."
            }
        ]
    },

    "discus_girls": {
        "id": "discus_girls",
        "sport_type": "athletics_distance",
        "name": "Discus Throw (girls)",
        "category": "Girls",
        "icon": "🥏",
        "squad": {
            "playing_count": 1,
            "max_substitutes": 1,
            "gender": "Girl",
            "notation": "1 Participating Player + 1 Substitute"
        },
        "match_format": {
            "trial_throws": 1,
            "official_attempts": 3,
            "ranking_basis": "Best valid official distance"
        },
        "specific_regulations": [
            {
                "title": "Attempts & Ranking",
                "badge": "📏 3 OFFICIAL THROWS",
                "desc": "1 trial throw + 3 official attempts. Best valid distance wins."
            }
        ]
    },

    "long_jump_boys": {
        "id": "long_jump_boys",
        "sport_type": "athletics_distance",
        "name": "Long Jump (boys)",
        "category": "Boys",
        "icon": "🏃‍♂️",
        "squad": {
            "playing_count": 2,
            "max_substitutes": 1,
            "gender": "Boy",
            "notation": "2 Participating Players + 1 Substitute"
        },
        "match_format": {
            "trial_jumps": 1,
            "official_attempts": 3,
            "ranking_basis": "Longest valid jump"
        },
        "specific_regulations": [
            {
                "title": "Jumps Format",
                "badge": "🏃 1 TRIAL + 3 OFFICIAL",
                "desc": "1 practice jump + 3 official measured jumps. Longest valid jump determines winner. Tie-break: next-best jump."
            },
            {
                "title": "Foul Rules",
                "badge": "🚫 TAKE-OFF LINE",
                "desc": "Stepping beyond take-off line, somersaulting, or walking back through landing marks is a foul."
            }
        ]
    },

    "long_jump_girls": {
        "id": "long_jump_girls",
        "sport_type": "athletics_distance",
        "name": "Long Jump (girls)",
        "category": "Girls",
        "icon": "🏃‍♀️",
        "squad": {
            "playing_count": 1,
            "max_substitutes": 1,
            "gender": "Girl",
            "notation": "1 Participating Player + 1 Substitute"
        },
        "match_format": {
            "trial_jumps": 1,
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

    "basketball_shootout": {
        "id": "basketball_shootout",
        "sport_type": "basketball_shootout",
        "name": "Basketball Shootout",
        "category": "Mixed / Open",
        "icon": "🏀",
        "squad": {
            "boys_shots": 30,
            "boys_participants": "min 3, max 6 boys",
            "girls_shots": 15,
            "girls_participants": "min 3, max 5 girls",
            "max_shots_per_person": 5,
            "notation": "Boys: 30 shots (3-6 players) | Girls: 15 shots (3-5 players)",
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
                "desc": "Participants choose shooting spots: 3 pts (outside arc), 2 pts (mid-range), 1 pt (free throw / close). Successful shot scores points, miss scores 0."
            },
            {
                "title": "Cumulative Team Score",
                "badge": "📊 TOTAL POINTS",
                "desc": "All individual points are summed into the department's cumulative total score. Department with highest total wins!"
            }
        ]
    }
}


def get_all_sports() -> list[dict[str, Any]]:
    return list(RULES_DATA.values())


def get_sport_rule(sport_id: str) -> dict[str, Any] | None:
    return RULES_DATA.get(sport_id)
