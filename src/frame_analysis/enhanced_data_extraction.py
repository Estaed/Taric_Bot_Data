"""
Enhanced data extraction for Taric game analysis.

This module provides functionality to extract additional detailed data from game states,
including positional data, combat metrics, decision context, player input patterns,
and environmental context.
"""

import numpy as np
from pathlib import Path
import math

# Map regions definition (rough approximation of League map regions)
MAP_REGIONS = {
    "TOP_LANE": [(0, 7000), (7000, 14000)],
    "MID_LANE": [(3500, 10500), (10500, 3500)],
    "BOT_LANE": [(7000, 0), (14000, 7000)],
    "TOP_JUNGLE_BLUE": [(2000, 7000), (7000, 12000)],
    "BOT_JUNGLE_BLUE": [(2000, 2000), (7000, 7000)],
    "TOP_JUNGLE_RED": [(7000, 7000), (12000, 12000)],
    "BOT_JUNGLE_RED": [(7000, 2000), (12000, 7000)],
    "BARON_PIT": [(5500, 10000), (7500, 12000)],
    "DRAGON_PIT": [(9000, 3000), (11000, 5000)],
    "BLUE_BASE": [(0, 0), (2000, 2000)],
    "RED_BASE": [(12000, 12000), (14000, 14000)]
}

# Objective locations (approximate)
OBJECTIVE_LOCATIONS = {
    "BARON": (6500, 11000),
    "DRAGON": (10000, 4000),
    "BLUE_BUFF_BLUE": (4000, 8000),
    "BLUE_BUFF_RED": (10000, 6000),
    "RED_BUFF_BLUE": (6000, 4000), 
    "RED_BUFF_RED": (8000, 10000),
    "TOP_TOWER_T1_BLUE": (5000, 13000),
    "TOP_TOWER_T1_RED": (9000, 9000),
    "MID_TOWER_T1_BLUE": (5500, 6500),
    "MID_TOWER_T1_RED": (8500, 8500),
    "BOT_TOWER_T1_BLUE": (2000, 8000),
    "BOT_TOWER_T1_RED": (13000, 6000)
}

def extract_positional_data(game_state, timestamp):
    """
    Extract detailed positional data for Taric and nearby units.
    
    Args:
        game_state (dict): The current game state
        timestamp (int): Current timestamp in milliseconds
        
    Returns:
        dict: Detailed positional data
    """
    taric_state = game_state.get('taric_state', {})
    nearby_units = game_state.get('nearby_units', {})
    
    # Get Taric's position
    taric_x = taric_state.get('position_x', 0)
    taric_y = taric_state.get('position_y', 0)
    
    # Determine which map region Taric is in
    current_region = "UNKNOWN"
    for region_name, region_bounds in MAP_REGIONS.items():
        (min_x, min_y), (max_x, max_y) = region_bounds
        if min_x <= taric_x <= max_x and min_y <= taric_y <= max_y:
            current_region = region_name
            break
    
    # Calculate proximity to objectives
    objective_distances = {}
    for obj_name, (obj_x, obj_y) in OBJECTIVE_LOCATIONS.items():
        distance = math.sqrt((taric_x - obj_x)**2 + (taric_y - obj_y)**2)
        objective_distances[f"distance_to_{obj_name.lower()}"] = distance
    
    # Calculate average position of allies and enemies
    ally_positions = []
    for ally in nearby_units.get('allies', []):
        if 'position_x' in ally and 'position_y' in ally:
            ally_positions.append((ally['position_x'], ally['position_y']))
    
    enemy_positions = []
    for enemy in nearby_units.get('enemies', []):
        if 'position_x' in enemy and 'position_y' in enemy:
            enemy_positions.append((enemy['position_x'], enemy['position_y']))
    
    # Calculate team centroid positions
    ally_centroid_x, ally_centroid_y = 0, 0
    if ally_positions:
        ally_centroid_x = sum(pos[0] for pos in ally_positions) / len(ally_positions)
        ally_centroid_y = sum(pos[1] for pos in ally_positions) / len(ally_positions)
    
    enemy_centroid_x, enemy_centroid_y = 0, 0
    if enemy_positions:
        enemy_centroid_x = sum(pos[0] for pos in enemy_positions) / len(enemy_positions)
        enemy_centroid_y = sum(pos[1] for pos in enemy_positions) / len(enemy_positions)
    
    # Calculate team spread (variance in positions)
    ally_spread = 0
    if ally_positions:
        ally_spread = sum(math.sqrt((pos[0] - ally_centroid_x)**2 + (pos[1] - ally_centroid_y)**2) 
                         for pos in ally_positions) / len(ally_positions)
    
    enemy_spread = 0
    if enemy_positions:
        enemy_spread = sum(math.sqrt((pos[0] - enemy_centroid_x)**2 + (pos[1] - enemy_centroid_y)**2)
                          for pos in enemy_positions) / len(enemy_positions)
    
    # Calculate distance to safe position (e.g., closest ally tower)
    # For simplicity, we'll use base locations as safe positions
    blue_base_x, blue_base_y = 1000, 1000  # Approximate blue base center
    red_base_x, red_base_y = 13000, 13000  # Approximate red base center
    
    # Determine team side based on team_id (assuming blue side is 100, red side is 200)
    team_id = game_state.get('team_id', 100)
    if team_id == 100:  # Blue side
        safe_position = (blue_base_x, blue_base_y)
    else:  # Red side
        safe_position = (red_base_x, red_base_y)
    
    distance_to_safe_position = math.sqrt((taric_x - safe_position[0])**2 + (taric_y - safe_position[1])**2)
    
    # Create positioning features
    positional_data = {
        'current_region': current_region,
        'objective_distances': objective_distances,
        'ally_centroid': {
            'x': ally_centroid_x,
            'y': ally_centroid_y
        },
        'enemy_centroid': {
            'x': enemy_centroid_x,
            'y': enemy_centroid_y
        },
        'ally_spread': ally_spread,
        'enemy_spread': enemy_spread,
        'distance_to_safe_position': distance_to_safe_position,
        'distance_to_ally_centroid': math.sqrt((taric_x - ally_centroid_x)**2 + (taric_y - ally_centroid_y)**2) if ally_positions else 0,
        'distance_to_enemy_centroid': math.sqrt((taric_x - enemy_centroid_x)**2 + (taric_y - enemy_centroid_y)**2) if enemy_positions else 0,
        'is_in_fog_of_war': False,  # Placeholder - would be determined from vision data
        'is_in_danger_zone': nearby_units.get('enemy_count', 0) > nearby_units.get('ally_count', 0)
    }
    
    return positional_data

def extract_combat_metrics(game_state, timestamp, previous_states=None):
    """
    Extract enhanced combat metrics.
    
    Args:
        game_state (dict): Current game state
        timestamp (int): Current timestamp in milliseconds
        previous_states (list, optional): Previous game states for comparison
        
    Returns:
        dict: Enhanced combat metrics
    """
    taric_state = game_state.get('taric_state', {})
    nearby_units = game_state.get('nearby_units', {})
    
    # Calculate health changes if we have previous states
    health_restored = 0
    damage_taken = 0
    
    if previous_states and len(previous_states) > 0:
        prev_state = previous_states[-1]
        prev_taric_state = prev_state.get('taric_state', {})
        
        # Calculate health delta
        prev_health = prev_taric_state.get('current_health', 0)
        current_health = taric_state.get('current_health', 0)
        health_delta = current_health - prev_health
        
        if health_delta > 0:
            health_restored = health_delta
        elif health_delta < 0:
            damage_taken = -health_delta
    
    # Calculate potential healing targets
    potential_heal_targets = []
    total_ally_health_deficit = 0
    
    for i, ally in enumerate(nearby_units.get('allies', [])):
        current_health = ally.get('current_health', 0)
        max_health = ally.get('max_health', 0)
        
        if max_health > 0:
            health_deficit = max_health - current_health
            health_percent = current_health / max_health
            
            if health_percent < 0.7:  # Consider allies below 70% health as potential heal targets
                potential_heal_targets.append({
                    'ally_index': i,
                    'health_deficit': health_deficit,
                    'health_percent': health_percent,
                    'priority': (1 - health_percent) * (1 + (0.2 if ally.get('is_in_danger', False) else 0))
                })
            
            total_ally_health_deficit += health_deficit
    
    # Sort potential heal targets by priority
    potential_heal_targets.sort(key=lambda x: x['priority'], reverse=True)
    
    # Calculate stun opportunities
    stun_opportunities = []
    for i, enemy in enumerate(nearby_units.get('enemies', [])):
        if enemy.get('is_in_e_range', False):
            stun_opportunities.append({
                'enemy_index': i,
                'health_percent': enemy.get('health_percent', 1.0),
                'is_killable': enemy.get('is_killable', False),
                'priority': (1 if enemy.get('is_killable', False) else 0.5)
            })
    
    # Sort stun opportunities by priority
    stun_opportunities.sort(key=lambda x: x['priority'], reverse=True)
    
    # Calculate combat metrics
    combat_metrics = {
        'in_combat': nearby_units.get('enemy_count', 0) > 0,
        'health_restored': health_restored,
        'damage_taken': damage_taken,
        'potential_heal_targets': potential_heal_targets[:3],  # Top 3 targets
        'stun_opportunities': stun_opportunities[:3],  # Top 3 opportunities
        'total_ally_health_deficit': total_ally_health_deficit,
        'combat_advantage': nearby_units.get('ally_count', 0) - nearby_units.get('enemy_count', 0),
        'combat_intensity': nearby_units.get('ally_count', 0) + nearby_units.get('enemy_count', 0),
        'ally_health_average': nearby_units.get('average_ally_health_percent', 1.0),
        'enemy_health_average': nearby_units.get('average_enemy_health_percent', 1.0),
        'health_advantage': nearby_units.get('average_ally_health_percent', 1.0) - nearby_units.get('average_enemy_health_percent', 1.0)
    }
    
    return combat_metrics

def extract_decision_context(game_state, timestamp, analyzer=None):
    """
    Extract decision context data for the current state.
    
    Args:
        game_state (dict): Current game state
        timestamp (int): Current timestamp in milliseconds
        analyzer (FrameAnalyzer, optional): The frame analyzer with access to static match data
        
    Returns:
        dict: Decision context variables
    """
    # Game time in minutes for easier phase determination
    game_time_minutes = timestamp / 60000
    
    # Determine game phase more precisely
    game_phase = "EARLY_GAME"
    if game_time_minutes >= 25:
        game_phase = "LATE_GAME"
    elif game_time_minutes >= 14:
        game_phase = "MID_GAME"
    elif game_time_minutes >= 8:
        game_phase = "EARLY_MID_GAME"
    
    # Determine lane phase
    is_lane_phase = game_time_minutes < 14
    
    # Get team compositions - try to get from analyzer first (new structure)
    # Fall back to game_state for backward compatibility
    team_composition = []
    enemy_composition = []
    
    if analyzer:
        team_composition = analyzer.team_composition
        enemy_composition = analyzer.enemy_composition
    else:
        # Legacy support for old format
        team_composition = game_state.get('team_composition', [])
        enemy_composition = game_state.get('enemy_composition', [])
    
    # Calculate gold difference (approximate based on available data)
    team_gold = sum(member.get('total_gold', 0) for member in team_composition)
    enemy_gold = sum(member.get('total_gold', 0) for member in enemy_composition)
    gold_diff = team_gold - enemy_gold
    
    # Approximate team level average
    team_levels = [member.get('level', 1) for member in team_composition]
    enemy_levels = [member.get('level', 1) for member in enemy_composition]
    
    team_level_avg = sum(team_levels) / max(1, len(team_levels))
    enemy_level_avg = sum(enemy_levels) / max(1, len(enemy_levels))
    level_diff = team_level_avg - enemy_level_avg
    
    # Decision context for objectives based on game time
    baron_active = game_time_minutes >= 20
    elder_active = game_time_minutes >= 35
    
    # Dragon spawn times (approximately every 5 minutes after 5 minutes)
    time_since_first_dragon = max(0, game_time_minutes - 5)
    dragon_timer = time_since_first_dragon % 5
    dragon_spawning_soon = dragon_timer > 4  # Within 1 minute of spawn
    
    # Herald timing (approximately 8-19 minutes)
    herald_available = 8 <= game_time_minutes <= 19
    
    decision_context = {
        'game_phase': game_phase,
        'is_lane_phase': is_lane_phase,
        'gold_diff': gold_diff,
        'level_diff': level_diff,
        'objective_control': {
            'baron_active': baron_active,
            'elder_active': elder_active,
            'dragon_spawning_soon': dragon_spawning_soon,
            'herald_available': herald_available
        },
        'team_strength': {
            'stronger_early': np.random.random() > 0.5,  # Placeholder - would be determined from team comps
            'stronger_late': np.random.random() > 0.5,  # Placeholder - would be determined from team comps
            'better_teamfight': np.random.random() > 0.5,  # Placeholder - would be determined from team comps
            'better_pick_potential': np.random.random() > 0.5  # Placeholder - would be determined from team comps
        }
    }
    
    return decision_context

def extract_player_input_patterns(game_state, timestamp, action, previous_actions=None):
    """
    Extract patterns in player inputs and decision making.
    
    Args:
        game_state (dict): Current game state
        timestamp (int): Current timestamp in milliseconds
        action (dict): Current action
        previous_actions (list, optional): Previous actions for sequence detection
        
    Returns:
        dict: Input pattern metrics
    """
    # Default values
    input_patterns = {
        'ability_sequence': [],
        'target_selection_pattern': 'NONE',
        'reaction_time_ms': 0,
        'combat_style': 'NEUTRAL'
    }
    
    # If we have previous actions, analyze sequences
    if previous_actions and len(previous_actions) > 0:
        # Extract last 5 ability usages (if available)
        ability_sequence = []
        for i in range(min(5, len(previous_actions))):
            if previous_actions[-(i+1)].get('type') == 'TARIC_ABILITY_CAST':
                ability_sequence.append(previous_actions[-(i+1)].get('ability', 'X'))
        input_patterns['ability_sequence'] = ability_sequence
        
        # Analyze reaction time from stimuli to response (e.g., enemy appearing to ability cast)
        # This would need more detailed event tracking in a real implementation
        # Here we'll use a placeholder value
        input_patterns['reaction_time_ms'] = np.random.randint(200, 800)
        
        # Analyze target selection patterns
        target_counts = {}
        for prev_action in previous_actions[-10:]:  # Look at last 10 actions
            target_id = prev_action.get('target_id')
            if target_id:
                target_counts[target_id] = target_counts.get(target_id, 0) + 1
        
        # Determine most frequent target
        most_frequent_target = None
        most_frequent_count = 0
        for target_id, count in target_counts.items():
            if count > most_frequent_count:
                most_frequent_target = target_id
                most_frequent_count = count
        
        # Categorize target selection pattern
        if most_frequent_count >= 3:
            input_patterns['target_selection_pattern'] = 'FOCUSED'
        elif len(target_counts) >= 3:
            input_patterns['target_selection_pattern'] = 'DISTRIBUTED'
        else:
            input_patterns['target_selection_pattern'] = 'BALANCED'
        
        # Analyze combat style based on positioning and ability usage
        aggressive_actions = 0
        defensive_actions = 0
        for prev_action in previous_actions[-10:]:
            if prev_action.get('type') == 'TARIC_ABILITY_CAST':
                ability = prev_action.get('ability')
                if ability == 'E':  # Stun is generally aggressive
                    aggressive_actions += 1
                elif ability in ['W', 'R']:  # Shield and ult are generally defensive
                    defensive_actions += 1
                elif ability == 'Q':  # Heal depends on target
                    if prev_action.get('target_id') == game_state.get('taric_participant_id'):
                        defensive_actions += 1
                    else:
                        # Supporting an ally could be either
                        aggressive_actions += 0.5
                        defensive_actions += 0.5
        
        # Determine overall combat style
        if aggressive_actions > defensive_actions * 1.5:
            input_patterns['combat_style'] = 'AGGRESSIVE'
        elif defensive_actions > aggressive_actions * 1.5:
            input_patterns['combat_style'] = 'DEFENSIVE'
        else:
            input_patterns['combat_style'] = 'BALANCED'
    
    return input_patterns

def extract_environmental_context(game_state, timestamp):
    """
    Extract environmental context data.
    
    Args:
        game_state (dict): Current game state
        timestamp (int): Current timestamp in milliseconds
        
    Returns:
        dict: Environmental context data
    """
    # Game time in minutes
    game_time_minutes = timestamp / 60000
    
    # Day/night cycle (game time based approximation)
    # In League, this would be for special champions or map effects
    is_night = (game_time_minutes % 8) >= 4  # Simulate day/night cycle every 8 minutes
    
    # Nearby terrain features (would come from detailed map data)
    # Here we'll approximate with random values
    nearby_terrain = []
    if np.random.random() > 0.7:
        nearby_terrain.append('BRUSH')
    if np.random.random() > 0.8:
        nearby_terrain.append('WALL')
    if np.random.random() > 0.9:
        nearby_terrain.append('RIVER')
    
    # Vision control state - in a real implementation would be extracted from ward data
    vision_control = {
        'team_wards_nearby': np.random.randint(0, 3),
        'enemy_wards_nearby': np.random.randint(0, 2),
        'vision_advantage': np.random.random() > 0.5,
        'area_revealed_percent': np.random.random()
    }
    
    # Weather effects (cosmetic in League but could be used for visual feature extraction)
    weather_effects = np.random.choice(['CLEAR', 'CLOUDY', 'RAINY'], p=[0.7, 0.2, 0.1])
    
    # Minion wave state (approximated)
    minion_state = {
        'allied_minions_nearby': np.random.randint(0, 7),
        'enemy_minions_nearby': np.random.randint(0, 7),
        'wave_pushing_towards_enemy': np.random.random() > 0.5
    }
    
    # Team composition synergy ratings (would be calculated from actual compositions)
    team_comp_synergy = {
        'engage_potential': np.random.random(),
        'peel_potential': np.random.random(),
        'poke_potential': np.random.random(),
        'teamfight_strength': np.random.random(),
        'synergy_with_taric': np.random.random()
    }
    
    # Create environmental context
    environmental_context = {
        'is_night': is_night,
        'nearby_terrain': nearby_terrain,
        'vision_control': vision_control,
        'weather_effects': weather_effects,
        'minion_state': minion_state,
        'team_comp_synergy': team_comp_synergy
    }
    
    return environmental_context

def extract_enhanced_data(game_state, timestamp, action=None, previous_states=None, previous_actions=None, analyzer=None):
    """
    Extract all enhanced data metrics in one call.
    
    Args:
        game_state (dict): Current game state
        timestamp (int): Current timestamp in milliseconds
        action (dict, optional): Current action
        previous_states (list, optional): Previous game states
        previous_actions (list, optional): Previous actions
        analyzer (FrameAnalyzer, optional): The frame analyzer with access to static match data
        
    Returns:
        dict: Complete enhanced data metrics
    """
    enhanced_data = {
        'positional_data': extract_positional_data(game_state, timestamp),
        'combat_metrics': extract_combat_metrics(game_state, timestamp, previous_states),
        'decision_context': extract_decision_context(game_state, timestamp, analyzer),
        'input_patterns': extract_player_input_patterns(game_state, timestamp, action, previous_actions)
        # Removed environmental_context as it uses synthetic data
    }
    
    return enhanced_data 