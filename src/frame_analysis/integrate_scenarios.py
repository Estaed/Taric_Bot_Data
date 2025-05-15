"""
Integration script for the comprehensive Taric scenarios.

This script imports the scenarios from taric_scenarios.py and integrates them
with the frame_analysis.py module to provide a comprehensive set of training
scenarios for the Taric bot.
"""

import os
import sys
from pathlib import Path
import numpy as np
import json

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.append(project_root)

# Import from current package
from src.frame_analysis.frame_analysis import FrameAnalyzer
from src.frame_analysis.taric_scenarios import (
    ABILITY_SCENARIOS, 
    POSITIONING_SCENARIOS,
    COMBAT_SCENARIOS,
    ITEM_USAGE_SCENARIOS,
    WAVE_MANAGEMENT_SCENARIOS,
    VISION_CONTROL_SCENARIOS,
    MACRO_DECISION_SCENARIOS,
    TEAM_COORDINATION_SCENARIOS,
    GAME_PHASE_SCENARIOS,
    SPECIAL_MECHANICS_SCENARIOS
)
from src.config import RAW_DATA_DIR, CLEANED_DATA_DIR, FEATURES_DIR

def create_comprehensive_scenarios(analyzer):
    """
    Generate all scenario types from the comprehensive scenario templates.
    
    Args:
        analyzer (FrameAnalyzer): The frame analyzer instance
        
    Returns:
        list: All generated scenario instances
    """
    all_scenarios = []
    
    # Process Q scenarios
    for q_scenario_template in ABILITY_SCENARIOS["Q_SCENARIOS"]:
        # Generate 2-4 variations of each scenario
        for _ in range(np.random.randint(2, 5)):
            scenario = _generate_scenario_from_template(
                analyzer, q_scenario_template, "Q_ABILITY"
            )
            if scenario:
                all_scenarios.append(scenario)
    
    # Process W scenarios
    for w_scenario_template in ABILITY_SCENARIOS["W_SCENARIOS"]:
        for _ in range(np.random.randint(2, 5)):
            scenario = _generate_scenario_from_template(
                analyzer, w_scenario_template, "W_ABILITY"
            )
            if scenario:
                all_scenarios.append(scenario)
    
    # Process E scenarios
    for e_scenario_template in ABILITY_SCENARIOS["E_SCENARIOS"]:
        for _ in range(np.random.randint(2, 5)):
            scenario = _generate_scenario_from_template(
                analyzer, e_scenario_template, "E_ABILITY"
            )
            if scenario:
                all_scenarios.append(scenario)
    
    # Process R scenarios
    for r_scenario_template in ABILITY_SCENARIOS["R_SCENARIOS"]:
        for _ in range(np.random.randint(2, 5)):
            scenario = _generate_scenario_from_template(
                analyzer, r_scenario_template, "R_ABILITY"
            )
            if scenario:
                all_scenarios.append(scenario)
    
    # Process positioning scenarios
    for pos_template in POSITIONING_SCENARIOS:
        for _ in range(np.random.randint(2, 4)):
            scenario = _generate_scenario_from_template(
                analyzer, pos_template, "POSITIONING"
            )
            if scenario:
                all_scenarios.append(scenario)
    
    # Process combat scenarios
    for combat_template in COMBAT_SCENARIOS:
        for _ in range(np.random.randint(2, 4)):
            scenario = _generate_scenario_from_template(
                analyzer, combat_template, "COMBAT"
            )
            if scenario:
                all_scenarios.append(scenario)
    
    # Process the remaining scenario categories
    scenario_groups = [
        (ITEM_USAGE_SCENARIOS, "ITEM_USAGE", 2, 3),
        (WAVE_MANAGEMENT_SCENARIOS, "WAVE_MANAGEMENT", 1, 3),
        (VISION_CONTROL_SCENARIOS, "VISION_CONTROL", 2, 3),
        (MACRO_DECISION_SCENARIOS, "MACRO_DECISION", 2, 3),
        (TEAM_COORDINATION_SCENARIOS, "TEAM_COORDINATION", 2, 3),
        (SPECIAL_MECHANICS_SCENARIOS, "SPECIAL_MECHANICS", 2, 4)
    ]
    
    for scenarios, category, min_var, max_var in scenario_groups:
        for template in scenarios:
            for _ in range(np.random.randint(min_var, max_var + 1)):
                scenario = _generate_scenario_from_template(
                    analyzer, template, category
                )
                if scenario:
                    all_scenarios.append(scenario)
    
    # Process game phase scenarios
    for phase, templates in GAME_PHASE_SCENARIOS.items():
        for template in templates:
            for _ in range(np.random.randint(1, 4)):
                scenario = _generate_scenario_from_template(
                    analyzer, template, f"GAME_PHASE_{phase}"
                )
                if scenario:
                    all_scenarios.append(scenario)
    
    print(f"Generated {len(all_scenarios)} comprehensive scenarios")
    return all_scenarios

def _generate_scenario_from_template(analyzer, template, category):
    """
    Generate a concrete scenario instance from a template.
    
    Args:
        analyzer (FrameAnalyzer): The frame analyzer instance
        template (dict): The scenario template
        category (str): The scenario category
        
    Returns:
        dict: A concrete scenario instance or None if generation failed
    """
    try:
        # Get game data
        game_duration = analyzer.match_data['info']['gameDuration']
        
        # Calculate timestamp within the game time range
        min_time, max_time = template.get("game_time_range", (0.0, 1.0))
        scenario_time_percent = min_time + np.random.random() * (max_time - min_time)
        timestamp = int(game_duration * 1000 * scenario_time_percent)
        
        # Find nearest frame
        nearest_frame = None
        min_time_diff = float('inf')
        
        for frame in analyzer.frames:
            time_diff = abs(frame.get('timestamp', 0) - timestamp)
            if time_diff < min_time_diff:
                min_time_diff = time_diff
                nearest_frame = frame
        
        if not nearest_frame:
            return None
        
        # Create base game state
        game_state = analyzer._create_game_state(nearest_frame, timestamp)
        if not game_state:
            return None
        
        # Modify game state to match scenario requirements
        _modify_game_state_for_scenario(game_state, template)
        
        # Create action
        action = {
            "type": "CRITICAL_DECISION",
            "name": template["name"],
            "description": template["description"],
            "timestamp": timestamp,
            "correct_action": template["correct_action"],
            "scenario_category": category
        }
        
        # Add ability-specific action data
        if category == "Q_ABILITY" and template["correct_action"] == "USE_Q":
            action["ability"] = "Q"
            action["targets"] = [analyzer.taric_participant_id]  # Self
            # Add random allies as targets
            if "ally_count" in template:
                min_allies, max_allies = template["ally_count"]
                num_allies = min(max_allies, np.random.randint(min_allies, max_allies + 1))
                for _ in range(num_allies):
                    action["targets"].append(np.random.randint(1, 5))  # Random ally IDs
        
        elif category == "W_ABILITY" and "USE_W" in template["correct_action"]:
            action["ability"] = "W"
            if "ally_role" in template:
                action["target_role"] = template["ally_role"]
                action["target_id"] = np.random.randint(1, 5)  # Random ally ID
        
        elif category == "E_ABILITY" and "USE_E" in template["correct_action"]:
            action["ability"] = "E"
            # Add stun direction
            action["stun_direction_x"] = np.random.random() * 2 - 1
            action["stun_direction_y"] = np.random.random() * 2 - 1
            # Normalize
            magnitude = np.sqrt(action["stun_direction_x"]**2 + action["stun_direction_y"]**2)
            if magnitude > 0:
                action["stun_direction_x"] /= magnitude
                action["stun_direction_y"] /= magnitude
            
            # Add targets that would be hit
            if "enemy_count" in template:
                min_enemies, max_enemies = template["enemy_count"]
                num_enemies = min(max_enemies, np.random.randint(min_enemies, max_enemies + 1))
                action["stunned_targets"] = [np.random.randint(6, 11) for _ in range(num_enemies)]
        
        elif category == "R_ABILITY" and "USE_R" in template["correct_action"]:
            action["ability"] = "R"
            # Include allies affected by ultimate
            action["affected_allies"] = [analyzer.taric_participant_id]  # Taric always affected
            if "ally_count" in template:
                min_allies, max_allies = template["ally_count"]
                num_allies = min(max_allies, np.random.randint(min_allies, max_allies + 1))
                for _ in range(num_allies):
                    action["affected_allies"].append(np.random.randint(1, 5))  # Random ally ID
        
        # Return the scenario
        return {
            "state": game_state,
            "action": action,
            "timestamp": timestamp,
            "event_type": "CRITICAL_DECISION",
            "scenario_type": category
        }
        
    except Exception as e:
        print(f"Error generating scenario from template: {e}")
        return None

def _modify_game_state_for_scenario(game_state, template):
    """
    Modify a game state to match the scenario requirements.
    
    Args:
        game_state (dict): The game state to modify
        template (dict): The scenario template
    """
    # Modify ally health if specified
    if "ally_health_range" in template:
        min_health, max_health = template["ally_health_range"]
        allies = game_state["nearby_units"]["allies"]
        for ally in allies:
            ally["health_percent"] = min_health + np.random.random() * (max_health - min_health)
            ally["is_in_danger"] = ally["health_percent"] < 0.4
    
    # Modify enemy health if specified
    if "enemy_health_range" in template:
        min_health, max_health = template["enemy_health_range"]
        enemies = game_state["nearby_units"]["enemies"]
        for enemy in enemies:
            enemy["health_percent"] = min_health + np.random.random() * (max_health - min_health)
            enemy["is_killable"] = enemy["health_percent"] < 0.2
    
    # Modify ally count if specified
    if "ally_count" in template:
        min_allies, max_allies = template["ally_count"]
        ally_count = np.random.randint(min_allies, max_allies + 1)
        allies = game_state["nearby_units"]["allies"]
        
        # Adjust ally list size
        while len(allies) > ally_count and allies:
            allies.pop()
        
        # Add allies if needed
        while len(allies) < ally_count:
            allies.append({
                "distance": np.random.randint(200, 800),
                "health_percent": np.random.random(),
                "is_in_q_range": np.random.random() > 0.3,
                "is_in_w_range": np.random.random() > 0.4,
                "is_in_e_range": np.random.random() > 0.5,
                "is_in_r_range": np.random.random() > 0.3,
                "is_in_danger": np.random.random() < 0.3
            })
        
        game_state["nearby_units"]["ally_count"] = len(allies)
    
    # Modify enemy count if specified
    if "enemy_count" in template:
        min_enemies, max_enemies = template["enemy_count"]
        enemy_count = np.random.randint(min_enemies, max_enemies + 1)
        enemies = game_state["nearby_units"]["enemies"]
        
        # Adjust enemy list size
        while len(enemies) > enemy_count and enemies:
            enemies.pop()
        
        # Add enemies if needed
        while len(enemies) < enemy_count:
            enemies.append({
                "distance": np.random.randint(300, 1000),
                "health_percent": np.random.random(),
                "is_in_basic_attack_range": np.random.random() > 0.7,
                "is_in_e_range": np.random.random() > 0.5,
                "is_stunnable": np.random.random() > 0.3,
                "is_killable": np.random.random() < 0.2
            })
        
        game_state["nearby_units"]["enemy_count"] = len(enemies)
    
    # Add any other template-specific modifications
    if "mana_percent" in template:
        min_mana, max_mana = template["mana_percent"]
        game_state["taric_state"]["mana_percent"] = min_mana + np.random.random() * (max_mana - min_mana)
    
    if "flash_available" in template:
        game_state["taric_state"]["cooldowns"]["SUMMONER1"] = 0 if template["flash_available"] else 300
    
    # Flag-based properties
    for flag_prop in [
        "team_invading", "enemy_cc_duration", "at_major_objective", 
        "objective_spawning_soon", "team_ready_to_fight", "allies_engaging",
        "ultimate_available", "passive_charged", "team_fight_imminent",
        "at_major_objective", "need_vision", "lane_phase"
    ]:
        if flag_prop in template:
            game_state.setdefault("scenario_flags", {})[flag_prop] = template[flag_prop]

def integrate_with_frame_analyzer():
    """
    Patch the FrameAnalyzer class to include the comprehensive scenarios.
    """
    # Store original method
    original_method = FrameAnalyzer.create_critical_decision_scenarios
    
    # Define extended method
    def extended_create_critical_decision_scenarios(self):
        """
        Create a comprehensive set of scenarios for critical decision points.
        
        This extended method calls the original implementation and then adds
        all the additional scenarios defined in taric_scenarios.py.
        
        Returns:
            list: All scenario instances
        """
        # Call original method to get base scenarios
        base_scenarios = original_method(self)
        
        # Generate comprehensive scenarios
        comprehensive_scenarios = create_comprehensive_scenarios(self)
        
        # Combine scenarios
        all_scenarios = base_scenarios + comprehensive_scenarios
        print(f"Total scenarios: {len(all_scenarios)} ({len(base_scenarios)} base + {len(comprehensive_scenarios)} comprehensive)")
        
        return all_scenarios
    
    # Replace the method
    FrameAnalyzer.create_critical_decision_scenarios = extended_create_critical_decision_scenarios
    
    print("Successfully integrated comprehensive scenarios with FrameAnalyzer")
    return True

def main():
    """Main function to integrate scenarios and test generation."""
    # Integrate with frame analyzer
    integrate_with_frame_analyzer()
    
    # Test on one match file
    match_files = list(RAW_DATA_DIR.glob('*.json'))
    
    if not match_files:
        print(f"No match files found in {RAW_DATA_DIR}")
        return False
    
    try:
        # Load first match
        with open(match_files[0], 'r', encoding='utf-8') as f:
            match_data = json.load(f)
        
        # Create analyzer
        analyzer = FrameAnalyzer(match_data=match_data)
        
        # Create scenarios
        scenarios = analyzer.create_critical_decision_scenarios()
        
        print(f"Successfully generated {len(scenarios)} scenarios")
        print(f"Scenario types: {set(s.get('scenario_type', 'UNKNOWN') for s in scenarios)}")
        
        return True
    
    except Exception as e:
        print(f"Error testing scenario integration: {e}")
        return False

if __name__ == "__main__":
    main() 