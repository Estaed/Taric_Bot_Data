"""
Additional scenarios for Taric gameplay decision points.

This module provides comprehensive scenario definitions for critical
decision points in Taric gameplay, extending the base scenarios in
frame_analysis.py.
"""

# Define comprehensive scenario templates
# Each template will be used to generate multiple variations

ABILITY_SCENARIOS = {
    "Q_SCENARIOS": [
        {
            "name": "Low_Health_Ally_Priority",
            "description": "Multiple allies are low health, prioritize correct healing target",
            "game_time_range": (0.0, 1.0),  # Can occur throughout the game
            "ally_health_range": (0.1, 0.4),  # Low health allies
            "ally_count": (2, 4),            # Multiple allies
            "correct_action": "USE_Q"
        },
        {
            "name": "Auto_Attack_Reset",
            "description": "Use Q between auto-attacks to maximize DPS",
            "game_time_range": (0.0, 1.0),
            "enemy_health_range": (0.3, 0.7),
            "enemy_proximity": (100, 200),    # In auto attack range
            "correct_action": "AA_Q_AA"
        },
        {
            "name": "Multiple_Target_Healing",
            "description": "Position to heal multiple allies efficiently",
            "game_time_range": (0.3, 1.0),
            "ally_health_range": (0.2, 0.6),
            "ally_count": (2, 4),
            "ally_proximity": (100, 300),     # Close enough for Q
            "correct_action": "USE_Q"
        },
        {
            "name": "Mana_Conservation",
            "description": "Save mana instead of using Q when healing is not critical",
            "game_time_range": (0.0, 0.4),    # Early game mana management
            "ally_health_range": (0.6, 0.8),  # Allies not critically low
            "mana_percent": (0.1, 0.3),       # Low mana
            "correct_action": "HOLD_Q"
        },
        {
            "name": "Stack_Management",
            "description": "Hold Q stacks for upcoming fight",
            "game_time_range": (0.2, 0.8),
            "ally_health_range": (0.7, 0.9),  # Allies healthy
            "objective_spawning_soon": True,  # Objective coming up
            "correct_action": "HOLD_Q_STACKS"
        }
    ],
    
    "W_SCENARIOS": [
        {
            "name": "Carry_Protection",
            "description": "Link to ADC before team fight",
            "game_time_range": (0.3, 1.0),
            "ally_role": "ADC",
            "enemy_count": (3, 5),            # Team fight imminent
            "correct_action": "USE_W_ON_CARRY"
        },
        {
            "name": "Dive_Buddy",
            "description": "Link to assassin/diver before they engage",
            "game_time_range": (0.3, 0.9),
            "ally_role": "ASSASSIN",
            "ally_moving_forward": True,      # Ally moving toward enemies
            "correct_action": "USE_W_ON_DIVER"
        },
        {
            "name": "Defensive_Link_Swap",
            "description": "Change link target when original target is safe",
            "game_time_range": (0.2, 1.0),
            "current_linked_ally_health": (0.7, 1.0),  # Current link is healthy
            "other_ally_health": (0.1, 0.4),           # Other ally needs help
            "correct_action": "SWAP_W_TARGET"
        },
        {
            "name": "Pre_emptive_Shielding",
            "description": "Apply shield before predictable damage",
            "game_time_range": (0.0, 1.0),
            "enemy_casting_abilities": True,  # Enemy casting abilities
            "ally_health_range": (0.3, 0.7),
            "correct_action": "USE_W_SHIELD"
        },
        {
            "name": "Ability_Empowerment",
            "description": "Position so linked ally can extend E stun reach",
            "game_time_range": (0.2, 1.0),
            "enemies_near_linked_ally": True,
            "correct_action": "USE_E_THROUGH_W"
        },
        {
            "name": "Self_Cast_Decision",
            "description": "When to self-cast W instead of linking an ally",
            "game_time_range": (0.0, 0.3),    # Early laning phase
            "allies_in_range": False,         # No allies nearby
            "correct_action": "SELF_CAST_W"
        }
    ],
    
    "E_SCENARIOS": [
        {
            "name": "Multiple_Targets_Stun",
            "description": "Position to stun multiple enemies in a line",
            "game_time_range": (0.1, 1.0),
            "enemy_count": (2, 4),
            "enemy_alignment": "LINEAR",      # Enemies in a line
            "correct_action": "USE_E_LINE"
        },
        {
            "name": "Defensive_Peel",
            "description": "Stun enemies diving allies",
            "game_time_range": (0.2, 1.0),
            "ally_health_range": (0.1, 0.4),  # Ally in danger
            "enemy_proximity_to_ally": (100, 300),  # Enemy close to ally
            "correct_action": "USE_E_PEEL"
        },
        {
            "name": "Engage_Setup",
            "description": "Use stun to initiate fights",
            "game_time_range": (0.2, 0.9),
            "team_ready_to_fight": True,
            "enemy_count": (1, 3),
            "correct_action": "USE_E_ENGAGE"
        },
        {
            "name": "Chain_CC",
            "description": "Time stun to extend existing CC chain",
            "game_time_range": (0.1, 1.0),
            "enemy_cc_duration": (0.5, 1.5),  # Enemy currently CC'd
            "correct_action": "USE_E_CHAIN"
        },
        {
            "name": "Objective_Control",
            "description": "Use stun to secure objectives",
            "game_time_range": (0.3, 1.0),
            "near_objective": True,           # Near dragon/baron
            "enemy_jungler_proximity": (300, 600),  # Enemy jungler nearby
            "correct_action": "USE_E_OBJECTIVE"
        },
        {
            "name": "Flash_E_Combo",
            "description": "Flash positioning for optimal stun angle",
            "game_time_range": (0.3, 0.9),
            "flash_available": True,
            "enemy_key_target": True,         # High value target available
            "correct_action": "FLASH_E_COMBO"
        },
        {
            "name": "W_E_Extension",
            "description": "Use W on ally to extend stun range",
            "game_time_range": (0.2, 1.0),
            "ally_position_for_extension": True,
            "enemy_out_of_direct_range": True,
            "correct_action": "W_E_COMBO"
        }
    ],
    
    "R_SCENARIOS": [
        {
            "name": "Team_Fight_Initiation",
            "description": "Use ult as team engages",
            "game_time_range": (0.4, 1.0),
            "ally_count": (3, 5),             # Most of team present
            "allies_engaging": True,
            "correct_action": "USE_R_ENGAGE"
        },
        {
            "name": "Counter_Engage",
            "description": "Use ult after enemy engages",
            "game_time_range": (0.3, 1.0),
            "ally_health_range": (0.3, 0.7),
            "enemy_engage_abilities_used": True,
            "correct_action": "USE_R_COUNTER"
        },
        {
            "name": "Objective_Secure",
            "description": "Use ult during critical objective fights",
            "game_time_range": (0.5, 1.0),
            "at_major_objective": True,       # At Baron/Elder
            "objective_hp_percent": (0.0, 0.3), # Objective nearly dead
            "correct_action": "USE_R_OBJECTIVE"
        },
        {
            "name": "Dive_Protection",
            "description": "Use ult when allies are diving",
            "game_time_range": (0.4, 0.9),
            "allies_under_enemy_tower": True,
            "ally_health_range": (0.3, 0.6),
            "correct_action": "USE_R_DIVE"
        },
        {
            "name": "Desperate_Defense",
            "description": "Use ult to survive when multiple allies are low health",
            "game_time_range": (0.3, 1.0),
            "ally_count": (2, 5),
            "ally_health_range": (0.05, 0.3), # Very low health
            "correct_action": "USE_R_DESPERATION"
        },
        {
            "name": "False_Alarm",
            "description": "Recognize situations that look dangerous but don't require ultimate",
            "game_time_range": (0.2, 0.8),
            "ally_health_range": (0.3, 0.5),  # Medium-low health
            "enemy_count": (1, 2),            # Not enough enemies to warrant ult
            "correct_action": "HOLD_R"
        },
        {
            "name": "Last_Stand",
            "description": "Use ult for final base defense",
            "game_time_range": (0.8, 1.0),    # Late game
            "defending_nexus_turrets": True,
            "ally_count": (3, 5),
            "correct_action": "USE_R_LAST_STAND"
        }
    ]
}

POSITIONING_SCENARIOS = [
    {
        "name": "Frontline_Protection",
        "description": "Position between enemies and carries",
        "game_time_range": (0.3, 1.0),
        "ally_carries_present": True,
        "enemy_threats_present": True,
        "correct_action": "POSITION_FRONTLINE"
    },
    {
        "name": "Backline_Guardian",
        "description": "Stay near ADC/mage to peel",
        "game_time_range": (0.3, 1.0),
        "enemy_divers_present": True,
        "ally_carries_present": True,
        "correct_action": "POSITION_BACKLINE"
    },
    {
        "name": "Vision_Control",
        "description": "Position for safe warding",
        "game_time_range": (0.1, 0.9),
        "need_vision": True,
        "enemies_missing": True,
        "correct_action": "POSITION_FOR_VISION"
    },
    {
        "name": "Objective_Zoning",
        "description": "Position to zone enemies from objectives",
        "game_time_range": (0.3, 1.0),
        "at_major_objective": True,
        "enemy_approaching": True,
        "correct_action": "POSITION_ZONE_OBJECTIVE"
    },
    {
        "name": "Lane_Presence",
        "description": "Optimal positioning during laning phase",
        "game_time_range": (0.0, 0.3),
        "lane_phase": True,
        "ally_adc_present": True,
        "correct_action": "POSITION_LANE_OPTIMAL"
    },
    {
        "name": "Roaming_Routes",
        "description": "Path efficiently when roaming",
        "game_time_range": (0.1, 0.4),
        "roaming_opportunity": True,
        "target_lane_pressure": True,
        "correct_action": "POSITION_ROAM_PATH"
    },
    {
        "name": "Teamfight_Formation",
        "description": "Position to maximize ability impact",
        "game_time_range": (0.3, 1.0),
        "team_fight_imminent": True,
        "ally_count": (3, 5),
        "correct_action": "POSITION_TEAMFIGHT_OPTIMAL"
    }
]

COMBAT_SCENARIOS = [
    {
        "name": "Early_Game_Trades",
        "description": "Trading patterns in lane",
        "game_time_range": (0.0, 0.2),
        "lane_phase": True,
        "enemy_cooldowns_used": True,
        "correct_action": "TRADE_PATTERN"
    },
    {
        "name": "All_in_Engagement",
        "description": "Full combat sequence execution",
        "game_time_range": (0.1, 0.5),
        "all_abilities_available": True,
        "target_vulnerable": True,
        "correct_action": "ALL_IN_COMBO"
    },
    {
        "name": "Peeling_Multiple_Divers",
        "description": "Handle multiple enemies attacking carries",
        "game_time_range": (0.3, 1.0),
        "ally_carries_under_attack": True,
        "enemy_count": (2, 3),
        "correct_action": "PEEL_COMBO"
    },
    {
        "name": "Kiting_Mechanics",
        "description": "Move between abilities when retreating",
        "game_time_range": (0.1, 1.0),
        "outnumbered": True,
        "ally_health_range": (0.2, 0.5),
        "correct_action": "KITE_RETREAT"
    },
    {
        "name": "Focus_Target_Selection",
        "description": "Identify highest priority target",
        "game_time_range": (0.3, 1.0),
        "multiple_targets_available": True,
        "key_target_present": True,
        "correct_action": "TARGET_PRIORITY"
    },
    {
        "name": "Wombo_Combo_Setup",
        "description": "Coordinate abilities with team",
        "game_time_range": (0.3, 1.0),
        "ally_has_aoe_abilities": True,
        "enemies_grouped": True,
        "correct_action": "WOMBO_SETUP"
    },
    {
        "name": "Pick_Potential",
        "description": "Execute picks on isolated enemies",
        "game_time_range": (0.2, 0.9),
        "enemy_isolated": True,
        "team_nearby": True,
        "correct_action": "EXECUTE_PICK"
    }
]

ITEM_USAGE_SCENARIOS = [
    {
        "name": "Locket_Timing",
        "description": "Use Locket shield at optimal moment",
        "game_time_range": (0.3, 1.0),
        "has_locket": True,
        "team_taking_damage": True,
        "correct_action": "USE_LOCKET"
    },
    {
        "name": "Redemption_Placement",
        "description": "Place Redemption in optimal location",
        "game_time_range": (0.3, 1.0),
        "has_redemption": True,
        "team_fight_active": True,
        "correct_action": "USE_REDEMPTION"
    },
    {
        "name": "Knights_Vow_Partner",
        "description": "Select best ally for Knight's Vow",
        "game_time_range": (0.2, 1.0),
        "has_knights_vow": True,
        "carries_present": True,
        "correct_action": "USE_KNIGHTS_VOW"
    },
    {
        "name": "Zekes_Timing",
        "description": "Activate with ally's damage window",
        "game_time_range": (0.3, 1.0),
        "has_zekes": True,
        "ally_adc_in_range": True,
        "correct_action": "USE_ZEKES"
    },
    {
        "name": "Chemtech_Application",
        "description": "Apply healing reduction efficiently",
        "game_time_range": (0.2, 1.0),
        "has_chemtech": True,
        "enemy_healing_champion": True,
        "correct_action": "USE_CHEMTECH"
    },
    {
        "name": "Mobility_Items",
        "description": "Use movement items for engage/disengage",
        "game_time_range": (0.2, 1.0),
        "has_shurelyas": True,
        "team_needs_mobility": True,
        "correct_action": "USE_SHURELYAS"
    },
    {
        "name": "Wardstone_Management",
        "description": "Optimal ward placement with Vigilant Wardstone",
        "game_time_range": (0.5, 1.0),
        "has_wardstone": True,
        "vision_control_needed": True,
        "correct_action": "USE_WARDSTONE"
    }
]

WAVE_MANAGEMENT_SCENARIOS = [
    {
        "name": "Freeze_Setup",
        "description": "Creating a freeze when ADC is away",
        "game_time_range": (0.0, 0.3),
        "ally_adc_absent": True,
        "minion_setup_favorable": True,
        "correct_action": "SETUP_FREEZE"
    },
    {
        "name": "Slow_Push_Construction",
        "description": "Building a slow push before objective",
        "game_time_range": (0.2, 0.7),
        "objective_spawning_soon": True,
        "lane_position_neutral": True,
        "correct_action": "BUILD_SLOW_PUSH"
    },
    {
        "name": "Fast_Push_Execution",
        "description": "Quick pushing to recall or roam",
        "game_time_range": (0.1, 0.6),
        "need_to_recall": True,
        "minions_available": True,
        "correct_action": "EXECUTE_FAST_PUSH"
    },
    {
        "name": "Last_Hit_Under_Tower",
        "description": "Help ADC secure CS under tower",
        "game_time_range": (0.0, 0.3),
        "pushing_to_tower": True,
        "ally_adc_present": True,
        "correct_action": "HELP_LAST_HIT"
    },
    {
        "name": "Reset_Timing",
        "description": "Optimal backing timing",
        "game_time_range": (0.0, 0.8),
        "wave_cleared": True,
        "gold_for_items": True,
        "correct_action": "EXECUTE_RESET"
    }
]

VISION_CONTROL_SCENARIOS = [
    {
        "name": "Defensive_Warding",
        "description": "Ward placement when behind",
        "game_time_range": (0.1, 1.0),
        "team_gold_deficit": True,
        "losing_map_control": True,
        "correct_action": "WARD_DEFENSIVE"
    },
    {
        "name": "Offensive_Warding",
        "description": "Deep wards when ahead",
        "game_time_range": (0.2, 1.0),
        "team_gold_advantage": True,
        "enemy_jungle_accessible": True,
        "correct_action": "WARD_OFFENSIVE"
    },
    {
        "name": "Objective_Setup",
        "description": "Vision control before objectives",
        "game_time_range": (0.2, 1.0),
        "objective_spawning_soon": True,
        "controlling_objective_area": True,
        "correct_action": "WARD_OBJECTIVE"
    },
    {
        "name": "Sweeping_Patterns",
        "description": "Efficient sweeping routes",
        "game_time_range": (0.2, 1.0),
        "likely_enemy_wards": True,
        "objective_contest_soon": True,
        "correct_action": "SWEEP_PATTERN"
    },
    {
        "name": "Vision_Denial",
        "description": "Clear enemy vision before plays",
        "game_time_range": (0.3, 1.0),
        "planning_objective": True,
        "enemy_wards_spotted": True,
        "correct_action": "DENY_VISION"
    },
    {
        "name": "Baron_Dragon_Control",
        "description": "Optimal vision for major objectives",
        "game_time_range": (0.4, 1.0),
        "major_objective_available": True,
        "team_preparing_for_objective": True,
        "correct_action": "WARD_MAJOR_OBJECTIVE"
    }
]

MACRO_DECISION_SCENARIOS = [
    {
        "name": "Lane_Assignment",
        "description": "Where to be on map in mid/late game",
        "game_time_range": (0.4, 1.0),
        "lane_phase_over": True,
        "team_composition_needs": "PROTECT",
        "correct_action": "ASSIGN_WITH_CARRY"
    },
    {
        "name": "Roaming_Windows",
        "description": "When to roam from lane",
        "game_time_range": (0.1, 0.4),
        "adc_safe": True,
        "other_lane_gankable": True,
        "correct_action": "EXECUTE_ROAM"
    },
    {
        "name": "Recall_Timing",
        "description": "Optimal back timing",
        "game_time_range": (0.0, 0.9),
        "low_resources": True,
        "wave_state_favorable": True,
        "correct_action": "EXECUTE_RECALL"
    },
    {
        "name": "Objective_Priority",
        "description": "Choose between competing objectives",
        "game_time_range": (0.3, 1.0),
        "multiple_objectives_available": True,
        "team_position_favorable": True,
        "correct_action": "PRIORITIZE_OBJECTIVE"
    },
    {
        "name": "Split_Push_Support",
        "description": "When to support split pusher vs group",
        "game_time_range": (0.5, 1.0),
        "ally_splitting": True,
        "team_4v4_capable": True,
        "correct_action": "SUPPORT_GROUP"
    },
    {
        "name": "Base_Defense",
        "description": "Managing defense when inhibs are down",
        "game_time_range": (0.7, 1.0),
        "inhibs_down": True,
        "super_minions_present": True,
        "correct_action": "DEFEND_BASE"
    },
    {
        "name": "Elder_Baron_Setup",
        "description": "Preparation for game-deciding objectives",
        "game_time_range": (0.7, 1.0),
        "game_deciding_objective_up": True,
        "team_in_position": True,
        "correct_action": "SETUP_ELDER_BARON"
    }
]

TEAM_COORDINATION_SCENARIOS = [
    {
        "name": "Engage_Communication",
        "description": "Signal readiness for team engage",
        "game_time_range": (0.3, 1.0),
        "team_in_position": True,
        "abilities_ready": True,
        "correct_action": "SIGNAL_ENGAGE"
    },
    {
        "name": "Peel_Assignment",
        "description": "Coordinate who peels which threats",
        "game_time_range": (0.3, 1.0),
        "multiple_threats_present": True,
        "carries_need_protection": True,
        "correct_action": "ASSIGN_PEEL"
    },
    {
        "name": "Focus_Target_Calling",
        "description": "Identify priority targets",
        "game_time_range": (0.3, 1.0),
        "multiple_enemies_present": True,
        "key_target_killable": True,
        "correct_action": "CALL_FOCUS_TARGET"
    },
    {
        "name": "Objective_Securing",
        "description": "Coordinate securing major objectives",
        "game_time_range": (0.4, 1.0),
        "at_major_objective": True,
        "objective_contestable": True,
        "correct_action": "SECURE_OBJECTIVE"
    },
    {
        "name": "Vision_Control_Coordination",
        "description": "Team sweeping patterns",
        "game_time_range": (0.3, 1.0),
        "objective_coming_up": True,
        "team_has_sweepers": True,
        "correct_action": "COORDINATE_SWEEPING"
    },
    {
        "name": "Bait_Setups",
        "description": "Using Taric as bait with ult available",
        "game_time_range": (0.4, 0.9),
        "ultimate_available": True,
        "team_in_position": True,
        "correct_action": "EXECUTE_BAIT"
    }
]

GAME_PHASE_SCENARIOS = {
    "EARLY_GAME": [
        {
            "name": "Level_1_Invade",
            "description": "Support team during invades",
            "game_time_range": (0.0, 0.03),
            "team_invading": True,
            "early_game": True,
            "correct_action": "SUPPORT_INVADE"
        },
        {
            "name": "Level_2_Power_Spike",
            "description": "Leverage level 2 advantage in lane",
            "game_time_range": (0.02, 0.1),
            "just_reached_level_2": True,
            "enemy_still_level_1": True,
            "correct_action": "PRESS_LEVEL_ADVANTAGE"
        },
        {
            "name": "Early_Gank_Setup",
            "description": "Create opportunities for jungle ganks",
            "game_time_range": (0.05, 0.2),
            "ally_jungler_nearby": True,
            "lane_gankable": True,
            "correct_action": "SETUP_GANK"
        },
        {
            "name": "River_Control",
            "description": "Contest scuttle and river vision",
            "game_time_range": (0.05, 0.2),
            "scuttle_spawning": True,
            "jungler_contest_possible": True,
            "correct_action": "CONTROL_RIVER"
        }
    ],
    
    "MID_GAME": [
        {
            "name": "First_Tower_Rotation",
            "description": "Where to go after first tower falls",
            "game_time_range": (0.2, 0.4),
            "first_tower_fallen": True,
            "mid_game_begun": True,
            "correct_action": "ROTATE_MID"
        },
        {
            "name": "Drake_Setup",
            "description": "Prepare vision and position for dragon",
            "game_time_range": (0.2, 0.5),
            "dragon_spawning_soon": True,
            "team_in_position": True,
            "correct_action": "SETUP_DRAGON"
        },
        {
            "name": "Herald_Teamfight",
            "description": "Position for Herald contests",
            "game_time_range": (0.2, 0.4),
            "herald_active": True,
            "teams_contesting": True,
            "correct_action": "CONTEST_HERALD"
        },
        {
            "name": "Mid_Lane_ARAM",
            "description": "Handle frequent mid skirmishes",
            "game_time_range": (0.3, 0.6),
            "teams_grouped_mid": True,
            "skirmishing_frequent": True,
            "correct_action": "POSITION_MID_SKIRMISH"
        }
    ],
    
    "LATE_GAME": [
        {
            "name": "Baron_Dance",
            "description": "Position and vision control around Baron",
            "game_time_range": (0.6, 1.0),
            "baron_up": True,
            "teams_posturing": True,
            "correct_action": "CONTROL_BARON_AREA"
        },
        {
            "name": "Elder_Execution",
            "description": "Secure Elder with team",
            "game_time_range": (0.7, 1.0),
            "elder_dragon_up": True,
            "game_deciding_fight": True,
            "correct_action": "SECURE_ELDER"
        },
        {
            "name": "Base_Siege",
            "description": "Support team during siege",
            "game_time_range": (0.7, 1.0),
            "sieging_enemy_base": True,
            "inhibs_exposed": True,
            "correct_action": "SUPPORT_SIEGE"
        },
        {
            "name": "Base_Defense",
            "description": "Hold base against siege",
            "game_time_range": (0.7, 1.0),
            "defending_base": True,
            "inhibs_threatened": True,
            "correct_action": "DEFEND_INHIBS"
        }
    ]
}

SPECIAL_MECHANICS_SCENARIOS = [
    {
        "name": "Flash_E_W_Combo",
        "description": "Quick execution of mobility into stun extension",
        "game_time_range": (0.3, 1.0),
        "flash_available": True,
        "key_target_in_extended_range": True,
        "correct_action": "EXECUTE_FLASH_E_W"
    },
    {
        "name": "W_Partner_Switching",
        "description": "Rapidly change W target for different situations",
        "game_time_range": (0.3, 1.0),
        "w_on_cooldown": False,
        "multiple_allies_needing_protection": True,
        "correct_action": "EXECUTE_W_SWITCHING"
    },
    {
        "name": "Animation_Cancelling",
        "description": "Cancel ability animations properly",
        "game_time_range": (0.1, 1.0),
        "in_combat": True,
        "dps_maximization_needed": True,
        "correct_action": "CANCEL_ANIMATIONS"
    },
    {
        "name": "Ability_Sequencing",
        "description": "Optimal order of ability usage in different situations",
        "game_time_range": (0.2, 1.0),
        "all_abilities_available": True,
        "full_combo_needed": True,
        "correct_action": "OPTIMAL_SEQUENCE"
    },
    {
        "name": "Passive_Double_Hit",
        "description": "Maximize passive damage with auto resets",
        "game_time_range": (0.1, 1.0),
        "passive_charged": True,
        "enemy_in_range": True,
        "correct_action": "MAXIMIZE_PASSIVE"
    }
] 