"""
Positioning metrics calculation for Taric Bot AI.

This module calculates advanced positioning metrics from state-action pairs,
including lane proximity, positioning efficiency, and map presence.
"""

import numpy as np
import math
from collections import defaultdict

# Define map regions the same as in vision_metrics.py for consistency
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

# Objectives and key locations
KEY_LOCATIONS = {
    "BLUE_BUFF_BLUE": (4000, 8000),
    "RED_BUFF_BLUE": (6000, 4000),
    "BLUE_BUFF_RED": (10000, 6000),
    "RED_BUFF_RED": (8000, 10000),
    "BARON": (6500, 11000),
    "DRAGON": (10000, 4000),
    "HERALD": (6500, 11000),  # Same as Baron before 20min
    "BLUE_NEXUS": (1500, 1500),
    "RED_NEXUS": (12500, 12500)
}

# Lane waypoints for tracking lane proximity over time
LANE_WAYPOINTS = {
    "TOP_LANE": [
        (1800, 13200), (2500, 12500), (3300, 11700), (4000, 11000),
        (4700, 10300), (5500, 9500), (6300, 8700), (7100, 7900)
    ],
    "MID_LANE": [
        (3900, 3900), (4600, 4600), (5300, 5300), (6000, 6000),
        (6700, 6700), (7400, 7400), (8100, 8100), (8800, 8800),
        (9500, 9500), (10200, 10200)
    ],
    "BOT_LANE": [
        (8000, 1800), (8700, 2500), (9500, 3300), (10300, 4000),
        (11000, 4700), (11700, 5500), (12500, 6300), (13200, 7100)
    ]
}

def calculate_region_presence(state_action_pairs, match_data=None):
    """
    Calculate metrics for presence in different map regions.
    
    Args:
        state_action_pairs (list): List of state-action pairs
        match_data (dict): Match-level data for context
        
    Returns:
        dict: Dictionary of region presence metrics
    """
    # Initialize metrics
    metrics = {
        'region_presence': {region: 0 for region in MAP_REGIONS},
        'region_presence_percentage': {region: 0 for region in MAP_REGIONS},
        'lane_proximity': {
            'top_lane': 0,
            'mid_lane': 0,
            'bot_lane': 0
        },
        'objective_proximity': {
            'baron': 0,
            'dragon': 0,
            'herald': 0
        },
        'region_transitions': 0,
        'map_coverage': 0,
        'region_presence_by_phase': {
            'early_game': {region: 0 for region in MAP_REGIONS},
            'mid_game': {region: 0 for region in MAP_REGIONS},
            'late_game': {region: 0 for region in MAP_REGIONS}
        }
    }
    
    total_frames = len(state_action_pairs)
    if total_frames == 0:
        return metrics
    
    # Track current region and transitions
    current_region = None
    regions_visited = set()
    
    # Process each state-action pair
    for pair in state_action_pairs:
        state = pair['state']
        taric_state = state.get('taric_state', {})
        game_phase = state.get('game_phase', 'EARLY_GAME').lower()
        
        # Get Taric's position
        position_x = taric_state.get('position_x', 0)
        position_y = taric_state.get('position_y', 0)
        
        # Determine which region Taric is in
        region = "UNKNOWN"
        for region_name, region_bounds in MAP_REGIONS.items():
            (min_x, min_y), (max_x, max_y) = region_bounds
            if min_x <= position_x <= max_x and min_y <= position_y <= max_y:
                region = region_name
                break
        
        # Track region presence
        if region in metrics['region_presence']:
            metrics['region_presence'][region] += 1
            regions_visited.add(region)
        
        # Track region presence by game phase
        if game_phase in metrics['region_presence_by_phase']:
            if region in metrics['region_presence_by_phase'][game_phase]:
                metrics['region_presence_by_phase'][game_phase][region] += 1
        
        # Track region transitions
        if current_region is not None and current_region != region:
            metrics['region_transitions'] += 1
        
        current_region = region
        
        # Calculate proximity to lanes
        distance_to_top = min_distance_to_region(position_x, position_y, MAP_REGIONS["TOP_LANE"])
        distance_to_mid = min_distance_to_region(position_x, position_y, MAP_REGIONS["MID_LANE"])
        distance_to_bot = min_distance_to_region(position_x, position_y, MAP_REGIONS["BOT_LANE"])
        
        # Update lane proximity (inverse of distance, so closer = higher value)
        if distance_to_top > 0:
            metrics['lane_proximity']['top_lane'] += 1 / distance_to_top
        if distance_to_mid > 0:
            metrics['lane_proximity']['mid_lane'] += 1 / distance_to_mid
        if distance_to_bot > 0:
            metrics['lane_proximity']['bot_lane'] += 1 / distance_to_bot
        
        # Calculate proximity to objectives
        baron_pos = KEY_LOCATIONS.get("BARON", (0, 0))
        dragon_pos = KEY_LOCATIONS.get("DRAGON", (0, 0))
        herald_pos = KEY_LOCATIONS.get("HERALD", (0, 0))
        
        distance_to_baron = euclidean_distance(position_x, position_y, baron_pos[0], baron_pos[1])
        distance_to_dragon = euclidean_distance(position_x, position_y, dragon_pos[0], dragon_pos[1])
        distance_to_herald = euclidean_distance(position_x, position_y, herald_pos[0], herald_pos[1])
        
        # Update objective proximity (inverse of distance)
        if distance_to_baron > 0:
            metrics['objective_proximity']['baron'] += 1 / distance_to_baron
        if distance_to_dragon > 0:
            metrics['objective_proximity']['dragon'] += 1 / distance_to_dragon
        if distance_to_herald > 0:
            metrics['objective_proximity']['herald'] += 1 / distance_to_herald
    
    # Normalize metrics
    for region in metrics['region_presence']:
        metrics['region_presence_percentage'][region] = metrics['region_presence'][region] / total_frames
    
    # Calculate map coverage (percentage of regions visited)
    metrics['map_coverage'] = len(regions_visited) / len(MAP_REGIONS)
    
    # Normalize lane proximity and objective proximity
    for lane in metrics['lane_proximity']:
        metrics['lane_proximity'][lane] /= total_frames
    
    for objective in metrics['objective_proximity']:
        metrics['objective_proximity'][objective] /= total_frames
    
    # Normalize region presence by phase
    for phase in metrics['region_presence_by_phase']:
        phase_frames = sum(metrics['region_presence_by_phase'][phase].values())
        if phase_frames > 0:
            for region in metrics['region_presence_by_phase'][phase]:
                metrics['region_presence_by_phase'][phase][region] /= phase_frames
    
    return metrics


def calculate_lane_proximity_over_time(state_action_pairs, match_data=None):
    """
    Calculate lane proximity metrics over time.
    
    Args:
        state_action_pairs (list): List of state-action pairs
        match_data (dict): Match-level data for context
        
    Returns:
        dict: Dictionary of lane proximity over time metrics
    """
    # Initialize metrics
    metrics = {
        'lane_proximity_timeline': {
            'top_lane': [],
            'mid_lane': [],
            'bot_lane': []
        },
        'primary_lane': 'unknown',
        'lane_adherence': 0,
        'lane_rotation_count': 0,
        'lane_presence_by_phase': {
            'early_game': {
                'top_lane': 0,
                'mid_lane': 0,
                'bot_lane': 0
            },
            'mid_game': {
                'top_lane': 0,
                'mid_lane': 0,
                'bot_lane': 0
            },
            'late_game': {
                'top_lane': 0,
                'mid_lane': 0,
                'bot_lane': 0
            }
        }
    }
    
    if not state_action_pairs:
        return metrics
    
    # Track lane proximity over time
    lane_proximity_windows = {
        'top_lane': [],
        'mid_lane': [],
        'bot_lane': []
    }
    
    window_size = 60  # 1-minute windows
    current_primary_lane = None
    lane_switches = 0
    
    # Process each state-action pair
    for idx, pair in enumerate(state_action_pairs):
        state = pair['state']
        taric_state = state.get('taric_state', {})
        game_phase = state.get('game_phase', 'EARLY_GAME').lower()
        timestamp = state.get('game_time_seconds', 0)
        
        # Get Taric's position
        position_x = taric_state.get('position_x', 0)
        position_y = taric_state.get('position_y', 0)
        
        # Calculate proximity to each lane using waypoints
        lane_proximities = {}
        for lane_name, waypoints in LANE_WAYPOINTS.items():
            # Find minimum distance to any waypoint in the lane
            min_dist = float('inf')
            for waypoint in waypoints:
                dist = euclidean_distance(position_x, position_y, waypoint[0], waypoint[1])
                min_dist = min(min_dist, dist)
            
            # Convert to proximity (inverse distance)
            lane_proximities[lane_name.lower()] = 1 / (min_dist + 1)  # +1 to avoid division by zero
            
            # Add to timeline
            if timestamp % 10 == 0:  # Record every 10 seconds to reduce data size
                lane_key = lane_name.lower()
                metrics['lane_proximity_timeline'][lane_key].append({
                    'time': timestamp,
                    'proximity': lane_proximities[lane_key]
                })
        
        # Track lane presence by phase
        closest_lane = max(lane_proximities.items(), key=lambda x: x[1])[0]
        phase_key = game_phase
        if phase_key in metrics['lane_presence_by_phase']:
            if closest_lane in metrics['lane_presence_by_phase'][phase_key]:
                metrics['lane_presence_by_phase'][phase_key][closest_lane] += 1
        
        # Track primary lane switches
        if current_primary_lane is None:
            current_primary_lane = closest_lane
        elif closest_lane != current_primary_lane:
            # Only count as a lane switch if the proximity to the new lane is significant
            if lane_proximities[closest_lane] > 0.5:  # Threshold for significant lane presence
                lane_switches += 1
                current_primary_lane = closest_lane
        
        # Add to sliding window for each lane
        for lane, proximity in lane_proximities.items():
            lane_proximity_windows[lane].append(proximity)
            # Keep window at specified size
            if len(lane_proximity_windows[lane]) > window_size:
                lane_proximity_windows[lane].pop(0)
    
    # Calculate primary lane based on overall presence
    lane_presence = {}
    for phase_data in metrics['lane_presence_by_phase'].values():
        for lane, count in phase_data.items():
            if lane not in lane_presence:
                lane_presence[lane] = 0
            lane_presence[lane] += count
    
    if lane_presence:
        metrics['primary_lane'] = max(lane_presence.items(), key=lambda x: x[1])[0]
    
    # Calculate lane adherence (how consistently the champion stays in their primary lane)
    total_frames = len(state_action_pairs)
    if total_frames > 0 and metrics['primary_lane'] in lane_presence:
        metrics['lane_adherence'] = lane_presence[metrics['primary_lane']] / total_frames
    
    # Record lane rotation count
    metrics['lane_rotation_count'] = lane_switches
    
    # Normalize lane presence by phase
    for phase in metrics['lane_presence_by_phase']:
        phase_total = sum(metrics['lane_presence_by_phase'][phase].values())
        if phase_total > 0:
            for lane in metrics['lane_presence_by_phase'][phase]:
                metrics['lane_presence_by_phase'][phase][lane] /= phase_total
    
    return metrics


def calculate_champion_pathing(state_action_pairs, match_data=None):
    """
    Calculate champion pathing and movement efficiency metrics.
    
    Args:
        state_action_pairs (list): List of state-action pairs
        match_data (dict): Match-level data for context
        
    Returns:
        dict: Dictionary of champion pathing metrics
    """
    # Initialize metrics
    metrics = {
        'total_distance_traveled': 0,
        'distance_traveled_by_phase': {
            'early_game': 0,
            'mid_game': 0,
            'late_game': 0
        },
        'movement_speed': 0,
        'path_efficiency': 0,
        'path_directness': 0,
        'frequent_paths': [],
        'backtrack_percentage': 0,
        'objectives_approached': {
            'dragon': 0,
            'baron': 0,
            'herald': 0
        }
    }
    
    if not state_action_pairs:
        return metrics
    
    # Track movement data
    path_segments = []  # List of (start_pos, end_pos, distance) tuples
    previous_position = None
    positions = []
    backtrack_count = 0
    total_segments = 0
    
    # Track objective approaches
    last_objective_distance = {
        'dragon': float('inf'),
        'baron': float('inf'),
        'herald': float('inf')
    }
    
    # Process each state-action pair
    for idx, pair in enumerate(state_action_pairs):
        state = pair['state']
        taric_state = state.get('taric_state', {})
        game_phase = state.get('game_phase', 'EARLY_GAME').lower()
        
        # Get Taric's position
        position_x = taric_state.get('position_x', 0)
        position_y = taric_state.get('position_y', 0)
        current_position = (position_x, position_y)
        positions.append(current_position)
        
        # Calculate distance traveled from previous position
        if previous_position:
            distance = euclidean_distance(
                previous_position[0], previous_position[1],
                current_position[0], current_position[1]
            )
            
            if distance > 0:  # Only count actual movement
                # Add to total distance
                metrics['total_distance_traveled'] += distance
                
                # Add to phase-specific distance
                if game_phase in metrics['distance_traveled_by_phase']:
                    metrics['distance_traveled_by_phase'][game_phase] += distance
                
                # Add path segment
                path_segments.append((previous_position, current_position, distance))
                total_segments += 1
                
                # Check for backtracking
                if len(positions) >= 3:
                    # If we're closer to a position from 2 steps ago than the last position
                    # This might indicate backtracking
                    prev_prev_position = positions[-3]
                    dist_to_prev_prev = euclidean_distance(
                        current_position[0], current_position[1],
                        prev_prev_position[0], prev_prev_position[1]
                    )
                    if dist_to_prev_prev < distance:
                        backtrack_count += 1
        
        # Update previous position
        previous_position = current_position
        
        # Check distance to objectives
        for objective, position in {
            'dragon': KEY_LOCATIONS.get("DRAGON", (0, 0)),
            'baron': KEY_LOCATIONS.get("BARON", (0, 0)),
            'herald': KEY_LOCATIONS.get("HERALD", (0, 0))
        }.items():
            curr_dist = euclidean_distance(position_x, position_y, position[0], position[1])
            
            # Check if getting closer to the objective
            if curr_dist < last_objective_distance[objective] - 500:  # Significant approach
                metrics['objectives_approached'][objective] += 1
            
            last_objective_distance[objective] = curr_dist
    
    # Calculate movement speed (units per second)
    total_time = len(state_action_pairs)
    if total_time > 0:
        metrics['movement_speed'] = metrics['total_distance_traveled'] / total_time
    
    # Calculate path efficiency
    if len(positions) >= 2:
        # Direct distance from start to end
        start_position = positions[0]
        end_position = positions[-1]
        direct_distance = euclidean_distance(
            start_position[0], start_position[1],
            end_position[0], end_position[1]
        )
        
        # Path efficiency = direct distance / total distance traveled
        if metrics['total_distance_traveled'] > 0:
            metrics['path_efficiency'] = direct_distance / metrics['total_distance_traveled']
    
    # Calculate path directness (how consistently the champion moves in the same direction)
    if len(path_segments) >= 2:
        direction_changes = 0
        for i in range(len(path_segments) - 1):
            _, curr_end, _ = path_segments[i]
            curr_start, _, _ = path_segments[i + 1]
            
            # If end of current segment is start of next segment, the path is continuous
            if curr_end == curr_start:
                # Calculate angle between segments
                prev_direction = (
                    path_segments[i][1][0] - path_segments[i][0][0],
                    path_segments[i][1][1] - path_segments[i][0][1]
                )
                next_direction = (
                    path_segments[i+1][1][0] - path_segments[i+1][0][0],
                    path_segments[i+1][1][1] - path_segments[i+1][0][1]
                )
                
                # Normalize directions
                prev_mag = math.sqrt(prev_direction[0]**2 + prev_direction[1]**2)
                next_mag = math.sqrt(next_direction[0]**2 + next_direction[1]**2)
                
                if prev_mag > 0 and next_mag > 0:
                    prev_direction = (prev_direction[0] / prev_mag, prev_direction[1] / prev_mag)
                    next_direction = (next_direction[0] / next_mag, next_direction[1] / next_mag)
                    
                    # Calculate dot product
                    dot_product = prev_direction[0] * next_direction[0] + prev_direction[1] * next_direction[1]
                    
                    # If dot product is less than 0, direction changed by more than 90 degrees
                    if dot_product < 0:
                        direction_changes += 1
        
        # Path directness = 1 - (direction changes / total segments)
        if total_segments > 0:
            metrics['path_directness'] = 1 - (direction_changes / total_segments)
    
    # Calculate backtrack percentage
    if total_segments > 0:
        metrics['backtrack_percentage'] = backtrack_count / total_segments
    
    # Calculate frequent paths (simplified)
    # In a full implementation, this would cluster path segments to find common routes
    metrics['frequent_paths'] = []
    
    return metrics


def calculate_positioning_efficiency(state_action_pairs, match_data=None):
    """
    Calculate metrics for positioning efficiency.
    
    Args:
        state_action_pairs (list): List of state-action pairs
        match_data (dict): Match-level data for context
        
    Returns:
        dict: Dictionary of positioning efficiency metrics
    """
    # Initialize metrics
    metrics = {
        'average_distance_to_allies': 0,
        'average_distance_to_enemies': 0,
        'ideal_positioning_percentage': 0,
        'distance_traveled': 0,
        'movement_efficiency': 0,
        'team_spread': 0,
        'position_relative_to_team': 'unknown'  # frontline, backline, etc.
    }
    
    total_frames = len(state_action_pairs)
    if total_frames == 0:
        return metrics
    
    # Track distances and positions
    ally_distances = []
    enemy_distances = []
    ideal_positioning_frames = 0
    total_distance_traveled = 0
    previous_position = None
    team_spread_values = []
    
    # Process each state-action pair
    for pair in state_action_pairs:
        state = pair['state']
        taric_state = state.get('taric_state', {})
        nearby_units = state.get('nearby_units', {})
        
        # Get Taric's position
        position_x = taric_state.get('position_x', 0)
        position_y = taric_state.get('position_y', 0)
        current_position = (position_x, position_y)
        
        # Calculate distance traveled
        if previous_position:
            distance = euclidean_distance(
                previous_position[0], previous_position[1],
                current_position[0], current_position[1]
            )
            total_distance_traveled += distance
        
        previous_position = current_position
        
        # Calculate distance to allies and enemies
        frame_ally_distances = []
        for ally in nearby_units.get('allies', []):
            if 'distance' in ally:
                frame_ally_distances.append(ally['distance'])
        
        frame_enemy_distances = []
        for enemy in nearby_units.get('enemies', []):
            if 'distance' in enemy:
                frame_enemy_distances.append(enemy['distance'])
        
        if frame_ally_distances:
            ally_distances.append(sum(frame_ally_distances) / len(frame_ally_distances))
        
        if frame_enemy_distances:
            enemy_distances.append(sum(frame_enemy_distances) / len(frame_enemy_distances))
        
        # Calculate team spread
        if frame_ally_distances:
            team_spread = np.std(frame_ally_distances) if len(frame_ally_distances) > 1 else 0
            team_spread_values.append(team_spread)
        
        # Determine if Taric is in ideal positioning
        # For Taric, ideal positioning is being close to allies but not too close to enemies
        # This is a simplification and can be refined with more specific rules
        if frame_ally_distances and frame_enemy_distances:
            avg_ally_distance = sum(frame_ally_distances) / len(frame_ally_distances)
            avg_enemy_distance = sum(frame_enemy_distances) / len(frame_enemy_distances)
            
            # Ideal: Taric is close to allies (< 500 units) but not too close to enemies (> 700 units)
            # Frontline: Close to allies and enemies
            # Backline: Far from allies and enemies
            
            if avg_ally_distance < 500:
                if avg_enemy_distance > 700:
                    # Ideal positioning
                    ideal_positioning_frames += 1
                    metrics['position_relative_to_team'] = 'optimal'
                elif avg_enemy_distance < 500:
                    metrics['position_relative_to_team'] = 'frontline'
                else:
                    metrics['position_relative_to_team'] = 'midline'
            else:
                metrics['position_relative_to_team'] = 'backline'
    
    # Calculate average distances
    if ally_distances:
        metrics['average_distance_to_allies'] = sum(ally_distances) / len(ally_distances)
    
    if enemy_distances:
        metrics['average_distance_to_enemies'] = sum(enemy_distances) / len(enemy_distances)
    
    # Calculate ideal positioning percentage
    if total_frames > 0:
        metrics['ideal_positioning_percentage'] = ideal_positioning_frames / total_frames
    
    # Set total distance traveled
    metrics['distance_traveled'] = total_distance_traveled
    
    # Calculate movement efficiency
    # This is a simplified metric that compares distance traveled to objectives/allies
    # A more sophisticated metric would consider whether movement achieved game objectives
    if total_distance_traveled > 0:
        # Placeholder for a more sophisticated calculation
        metrics['movement_efficiency'] = 0.7  # default placeholder
    
    # Calculate average team spread
    if team_spread_values:
        metrics['team_spread'] = sum(team_spread_values) / len(team_spread_values)
    
    return metrics


def calculate_positioning_metrics(state_action_pairs, match_data=None):
    """
    Calculate combined positioning metrics from state-action pairs.
    
    Args:
        state_action_pairs (list): List of state-action pairs
        match_data (dict): Match-level data for context
        
    Returns:
        dict: Dictionary of positioning metrics
    """
    region_presence = calculate_region_presence(state_action_pairs, match_data)
    lane_proximity = calculate_lane_proximity_over_time(state_action_pairs, match_data)
    champion_pathing = calculate_champion_pathing(state_action_pairs, match_data)
    positioning_efficiency = calculate_positioning_efficiency(state_action_pairs, match_data)
    
    # Combine all metrics
    positioning_metrics = {
        **region_presence,
        **lane_proximity,
        **champion_pathing,
        **positioning_efficiency
    }
    
    return positioning_metrics


# Helper functions

def euclidean_distance(x1, y1, x2, y2):
    """Calculate Euclidean distance between two points."""
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)


def min_distance_to_region(x, y, region_bounds):
    """Calculate minimum distance from a point to a rectangular region."""
    (min_x, min_y), (max_x, max_y) = region_bounds
    
    # Check if point is inside the region
    if min_x <= x <= max_x and min_y <= y <= max_y:
        return 0
    
    # Calculate distance to nearest edge
    dx = max(min_x - x, 0, x - max_x)
    dy = max(min_y - y, 0, y - max_y)
    
    return math.sqrt(dx*dx + dy*dy) 