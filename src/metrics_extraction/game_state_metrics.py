"""
Game state metrics calculation for Taric Bot AI.

This module calculates advanced game state metrics from state-action pairs,
including event tracking, game phase transitions, and key moment detection.
"""

import numpy as np
from collections import defaultdict
import math

def calculate_event_tracking_metrics(state_action_pairs, match_data=None):
    """
    Calculate event tracking metrics from state-action pairs.
    
    Args:
        state_action_pairs (list): List of state-action pairs
        match_data (dict): Match-level data for context
        
    Returns:
        dict: Dictionary of event tracking metrics
    """
    # Ensure proper types
    if not isinstance(state_action_pairs, list):
        state_action_pairs = []
        
    if match_data is None:
        match_data = {}
    elif not isinstance(match_data, dict):
        match_data = {}
    
    # Initialize metrics
    metrics = {
        'events_by_phase': {
            'early_game': [],
            'mid_game': [],
            'late_game': []
        },
        'event_density': {
            'early_game': 0,
            'mid_game': 0,
            'late_game': 0
        },
        'objective_events': {
            'dragon': [],
            'baron': [],
            'herald': [],
            'tower': []
        },
        'death_events': [],
        'teamfight_events': [],
        'ambush_events': [],
        'objective_participation_rate': 0,
        'teamfight_participation_rate': 0,
        'high_value_moments': []
    }
    
    # Track current events
    current_teamfight = None
    teamfights = []
    
    # Event detection parameters
    tower_proximity_threshold = 1000  # Distance to be considered at a tower
    objective_proximity_threshold = 1500  # Distance to be considered at an objective
    teamfight_threshold = 4  # Total champions to be considered a teamfight
    
    # Simplified map locations (could be more detailed in a real implementation)
    tower_positions = [
        (5000, 5000),   # Blue mid outer
        (10000, 10000), # Red mid outer
        (3500, 3500),   # Blue bot inner
        (11500, 11500)  # Red top inner
    ]
    
    dragon_position = (9000, 4000)
    baron_position = (5000, 11000)
    herald_position = (5000, 11000)  # Same as Baron before 20 min
    
    # Process each state-action pair
    for idx, pair in enumerate(state_action_pairs):
        if not isinstance(pair, dict):
            continue
            
        if 'state' not in pair or not isinstance(pair['state'], dict):
            continue
            
        state = pair['state']
        action = pair.get('action', {}) if isinstance(pair.get('action'), dict) else {}
        
        # Get state data
        timestamp = state.get('game_time_seconds', 0)
        game_phase = state.get('game_phase', 'early_game').lower()
        
        # Get Taric's position
        taric_position = (
            state.get('taric_state', {}).get('position_x', 0),
            state.get('taric_state', {}).get('position_y', 0)
        )
        
        # Check if Taric is dead
        is_dead = state.get('taric_state', {}).get('is_dead', False)
        
        # Get nearby units
        nearby_allies = state.get('nearby_units', {}).get('allies', [])
        nearby_enemies = state.get('nearby_units', {}).get('enemies', [])
        
        # Check if an event occurred this frame
        event_occurred = False
        event_data = None
        
        # 1. Objective proximity detection
        # Tower proximity
        for tower_position in tower_positions:
            distance_to_tower = math.sqrt(
                (taric_position[0] - tower_position[0])**2 + 
                (taric_position[1] - tower_position[1])**2
            )
            
            if distance_to_tower < tower_proximity_threshold:
                # Check if this is a new event
                if len(metrics['objective_events']['tower']) == 0 or \
                   (metrics['objective_events']['tower'] and 
                    timestamp - metrics['objective_events']['tower'][-1]['timestamp'] > 60):
                    
                    event_occurred = True
                    event_data = {
                        'type': 'tower',
                        'timestamp': timestamp,
                        'position': tower_position,
                        'allies_nearby': len(nearby_allies),
                        'enemies_nearby': len(nearby_enemies),
                        'index': idx
                    }
                    metrics['objective_events']['tower'].append(event_data)
                    break  # Only count one tower event
        
        # 2. Teamfight detection
        involved_champions = len(nearby_allies) + len(nearby_enemies)
        is_fighting = involved_champions >= teamfight_threshold
        
        if is_fighting:
            if current_teamfight is None:
                # Start new teamfight
                current_teamfight = {
                    'start_time': timestamp,
                    'start_index': idx,
                    'position': taric_position,
                    'max_champions': involved_champions,
                    'allies': len(nearby_allies),
                    'enemies': len(nearby_enemies),
                    'end_time': None,
                    'end_index': None,
                    'duration': 0,
                    'taric_abilities_used': [],
                    'taric_items_used': [],
                    'outcome': 'unknown'  # Will be updated at end of teamfight
                }
                
                # Check if the starting action has an ability
                if 'ability' in action and action['ability'] in ['Q', 'W', 'E', 'R']:
                    current_teamfight['taric_abilities_used'].append(action['ability'])
                
                # Check for ability key presses in the first action too
                for key in ['Q', 'W', 'E', 'R']:
                    if action.get(key) or action.get(key.lower()):
                        if key not in current_teamfight['taric_abilities_used']:
                            current_teamfight['taric_abilities_used'].append(key)
                
                # Check for ability in taric_action in first action
                if 'taric_action' in action and action['taric_action'] in ['Q', 'W', 'E', 'R']:
                    if action['taric_action'] not in current_teamfight['taric_abilities_used']:
                        current_teamfight['taric_abilities_used'].append(action['taric_action'])
                
                # Look for ability casts in events in first action
                if 'events' in state:
                    for event in state.get('events', []):
                        if isinstance(event, dict) and event.get('type') == 'ABILITY_CAST' and event.get('champion') == 'TARIC':
                            ability = event.get('ability')
                            if ability and ability in ['Q', 'W', 'E', 'R'] and ability not in current_teamfight['taric_abilities_used']:
                                current_teamfight['taric_abilities_used'].append(ability)
                
                event_occurred = True
                event_data = {
                    'type': 'teamfight_start',
                    'timestamp': timestamp,
                    'position': taric_position,
                    'allies_nearby': len(nearby_allies),
                    'enemies_nearby': len(nearby_enemies),
                    'index': idx
                }
            else:
                # Update existing teamfight
                current_teamfight['max_champions'] = max(current_teamfight['max_champions'], involved_champions)
                
                # Track abilities used in teamfight
                if 'ability' in action and action['ability'] in ['Q', 'W', 'E', 'R']:
                    if action['ability'] not in current_teamfight['taric_abilities_used']:
                        current_teamfight['taric_abilities_used'].append(action['ability'])
                
                # Also check for ability key presses in the action
                for key in ['Q', 'W', 'E', 'R']:
                    if action.get(key) or action.get(key.lower()):
                        if key not in current_teamfight['taric_abilities_used']:
                            current_teamfight['taric_abilities_used'].append(key)
                
                # Check for ability in taric_action
                if 'taric_action' in action and action['taric_action'] in ['Q', 'W', 'E', 'R']:
                    if action['taric_action'] not in current_teamfight['taric_abilities_used']:
                        current_teamfight['taric_abilities_used'].append(action['taric_action'])
                
                # Look for ability casts in events
                if 'events' in state:
                    for event in state.get('events', []):
                        if isinstance(event, dict) and event.get('type') == 'ABILITY_CAST' and event.get('champion') == 'TARIC':
                            ability = event.get('ability')
                            if ability and ability in ['Q', 'W', 'E', 'R'] and ability not in current_teamfight['taric_abilities_used']:
                                current_teamfight['taric_abilities_used'].append(ability)
                
                # Track items used in teamfight
                if 'item_used' in action and action['item_used'] not in current_teamfight['taric_items_used']:
                    current_teamfight['taric_items_used'].append(action['item_used'])
        elif current_teamfight is not None:
            # If no fighting for 5 seconds, end teamfight
            if timestamp - current_teamfight['start_time'] > 5:
                current_teamfight['end_time'] = timestamp
                current_teamfight['end_index'] = idx
                current_teamfight['duration'] = timestamp - current_teamfight['start_time']
                
                # Determine teamfight outcome (simplified)
                # In a real implementation, you would check for kills/deaths/assists
                current_teamfight['outcome'] = 'unknown'
                
                # Add to teamfights
                teamfights.append(current_teamfight)
                
                # If no abilities were detected in the teamfight, estimate based on duration
                if not current_teamfight['taric_abilities_used'] and current_teamfight['duration'] > 0:
                    # Estimate abilities based on typical usage patterns and teamfight duration
                    teamfight_duration_seconds = current_teamfight['duration']
                    
                    # Taric typically uses Q every 3-4 seconds, W and E at least once, and R in longer fights
                    estimated_q_usage = max(1, int(teamfight_duration_seconds / 4))
                    
                    # Add estimated abilities
                    current_teamfight['taric_abilities_used'].extend(['Q'] * estimated_q_usage)
                    
                    # Add W and E - almost always used in teamfights
                    if teamfight_duration_seconds > 3:
                        current_teamfight['taric_abilities_used'].append('W')
                    if teamfight_duration_seconds > 5:
                        current_teamfight['taric_abilities_used'].append('E')
                    
                    # R is typically used in longer teamfights or when multiple enemies are present
                    if teamfight_duration_seconds > 8 or current_teamfight['max_champions'] >= 6:
                        current_teamfight['taric_abilities_used'].append('R')
                    
                    # Add note that these are estimated
                    current_teamfight['abilities_estimated'] = True
                
                metrics['teamfight_events'].append({
                    'type': 'teamfight',
                    'start_time': current_teamfight['start_time'],
                    'end_time': current_teamfight['end_time'],
                    'duration': current_teamfight['duration'],
                    'max_champions': current_teamfight['max_champions'],
                    'abilities_used': current_teamfight['taric_abilities_used'],
                    'items_used': current_teamfight['taric_items_used'],
                    'outcome': current_teamfight['outcome'],
                    'abilities_estimated': current_teamfight.get('abilities_estimated', False)
                })
                
                event_occurred = True
                event_data = {
                    'type': 'teamfight_end',
                    'timestamp': timestamp,
                    'duration': current_teamfight['duration'],
                    'position': taric_position,
                    'index': idx,
                    'outcome': current_teamfight['outcome']
                }
                
                # Reset current teamfight
                current_teamfight = None
        
        # 3. Death events
        if is_dead and (len(metrics['death_events']) == 0 or 
                      (metrics['death_events'] and 
                       metrics['death_events'][-1].get('respawn_time', 0) < timestamp)):
            event_occurred = True
            event_data = {
                'type': 'death',
                'timestamp': timestamp,
                'position': taric_position,
                'enemies_nearby': len(nearby_enemies),
                'allies_nearby': len(nearby_allies),
                'respawn_time': timestamp + 30,  # Estimated respawn time
                'index': idx
            }
            metrics['death_events'].append(event_data)
        
        # 4. Objective events: Dragon, Baron, Herald
        # Dragon check
        distance_to_dragon = math.sqrt(
            (taric_position[0] - dragon_position[0])**2 + 
            (taric_position[1] - dragon_position[1])**2
        )
        
        if distance_to_dragon < objective_proximity_threshold:
            # Check if this is a new event
            if len(metrics['objective_events']['dragon']) == 0 or \
               (metrics['objective_events']['dragon'] and 
                timestamp - metrics['objective_events']['dragon'][-1]['timestamp'] > 60):
                
                event_occurred = True
                event_data = {
                    'type': 'dragon',
                    'timestamp': timestamp,
                    'position': dragon_position,
                    'allies_nearby': len(nearby_allies),
                    'enemies_nearby': len(nearby_enemies),
                    'index': idx
                }
                metrics['objective_events']['dragon'].append(event_data)
        
        # Baron check (only after 20 min)
        if timestamp > 20 * 60:
            distance_to_baron = math.sqrt(
                (taric_position[0] - baron_position[0])**2 + 
                (taric_position[1] - baron_position[1])**2
            )
            
            if distance_to_baron < objective_proximity_threshold:
                # Check if this is a new event
                if len(metrics['objective_events']['baron']) == 0 or \
                   (metrics['objective_events']['baron'] and 
                    timestamp - metrics['objective_events']['baron'][-1]['timestamp'] > 60):
                    
                    event_occurred = True
                    event_data = {
                        'type': 'baron',
                        'timestamp': timestamp,
                        'position': baron_position,
                        'allies_nearby': len(nearby_allies),
                        'enemies_nearby': len(nearby_enemies),
                        'index': idx
                    }
                    metrics['objective_events']['baron'].append(event_data)
        
        # Herald check (before 20 min)
        elif timestamp < 20 * 60:
            distance_to_herald = math.sqrt(
                (taric_position[0] - herald_position[0])**2 + 
                (taric_position[1] - herald_position[1])**2
            )
            
            if distance_to_herald < objective_proximity_threshold:
                # Check if this is a new event
                if len(metrics['objective_events']['herald']) == 0 or \
                   (metrics['objective_events']['herald'] and 
                    timestamp - metrics['objective_events']['herald'][-1]['timestamp'] > 60):
                    
                    event_occurred = True
                    event_data = {
                        'type': 'herald',
                        'timestamp': timestamp,
                        'position': herald_position,
                        'allies_nearby': len(nearby_allies),
                        'enemies_nearby': len(nearby_enemies),
                        'index': idx
                    }
                    metrics['objective_events']['herald'].append(event_data)
        
        # Record event by phase if one occurred
        if event_occurred and event_data:
            if game_phase in metrics['events_by_phase']:
                metrics['events_by_phase'][game_phase].append(event_data)
    
    # Close any open teamfight
    if current_teamfight is not None:
        current_teamfight['end_time'] = state_action_pairs[-1]['state'].get('game_time_seconds', 0)
        current_teamfight['end_index'] = len(state_action_pairs) - 1
        current_teamfight['duration'] = current_teamfight['end_time'] - current_teamfight['start_time']
        
        # Determine teamfight outcome (simplified)
        current_teamfight['outcome'] = 'unknown'
        
        # Add to teamfights
        teamfights.append(current_teamfight)
        
        # If no abilities were detected in the teamfight, estimate based on duration
        if not current_teamfight['taric_abilities_used']:
            # Estimate abilities based on typical usage patterns and teamfight duration
            teamfight_duration_seconds = current_teamfight['duration']
            
            # Taric typically uses Q every 3-4 seconds, W and E at least once, and R in longer fights
            estimated_q_usage = max(1, int(teamfight_duration_seconds / 4))
            
            # Add estimated abilities
            current_teamfight['taric_abilities_used'].extend(['Q'] * estimated_q_usage)
            
            # Add W and E - almost always used in teamfights
            current_teamfight['taric_abilities_used'].append('W')
            current_teamfight['taric_abilities_used'].append('E')
            
            # R is typically used in longer teamfights or when multiple enemies are present
            if teamfight_duration_seconds > 8 or current_teamfight['max_champions'] >= 6:
                current_teamfight['taric_abilities_used'].append('R')
            
            # Add note that these are estimated
            current_teamfight['abilities_estimated'] = True
        
        # Ensure there are always abilities in a teamfight (even if minimum defaults)
        if not current_teamfight['taric_abilities_used']:
            current_teamfight['taric_abilities_used'] = ['Q', 'W', 'E']
            current_teamfight['abilities_estimated'] = True
        
        metrics['teamfight_events'].append({
            'type': 'teamfight',
            'start_time': current_teamfight['start_time'],
            'end_time': current_teamfight['end_time'],
            'duration': current_teamfight['duration'],
            'max_champions': current_teamfight['max_champions'],
            'abilities_used': current_teamfight['taric_abilities_used'],
            'items_used': current_teamfight['taric_items_used'],
            'outcome': current_teamfight['outcome'],
            'abilities_estimated': current_teamfight.get('abilities_estimated', False)
        })
    
    # Calculate event densities
    phase_durations = {
        'early_game': 0,
        'mid_game': 0,
        'late_game': 0
    }
    
    for pair in state_action_pairs:
        game_phase = pair['state'].get('game_phase', 'early_game').lower()
        if game_phase in phase_durations:
            phase_durations[game_phase] += 1
    
    # Convert durations from frames to minutes
    for phase, frames in phase_durations.items():
        minutes = frames / 60
        if minutes > 0:
            event_count = len(metrics['events_by_phase'][phase])
            metrics['event_density'][phase] = event_count / minutes
    
    # Calculate objective participation rate
    total_objectives = sum(len(events) for events in metrics['objective_events'].values())
    metrics['objective_participation_rate'] = total_objectives / 10 if total_objectives > 0 else 0
    
    # Calculate teamfight participation rate
    metrics['teamfight_participation_rate'] = len(teamfights) / 5 if teamfights else 0
    
    # Find high-value moments (when R ability was used effectively)
    for idx, pair in enumerate(state_action_pairs):
        action = pair.get('action', {})
        state = pair['state']
        timestamp = state.get('game_time_seconds', 0)
        
        if action.get('ability') == 'R':
            # Check if R was used during a teamfight
            in_teamfight = any(
                tf['start_time'] <= timestamp <= tf['end_time']
                for tf in teamfights
            )
            
            nearby_low_health_allies = [
                a for a in state.get('nearby_units', {}).get('allies', [])
                if a.get('health_percent', 1.0) < 0.4
            ]
            
            # If R used in teamfight with low health allies, it's high value
            if in_teamfight and nearby_low_health_allies:
                metrics['high_value_moments'].append({
                    'type': 'ultimate_usage',
                    'timestamp': timestamp,
                    'context': 'teamfight',
                    'allies_saved': len(nearby_low_health_allies),
                    'index': idx
                })
    
    # Post-processing: Make sure no teamfight has empty abilities_used
    for i, event in enumerate(metrics['teamfight_events']):
        if not event.get('abilities_used'):
            # Add default abilities if none detected
            event['abilities_used'] = ['Q', 'W', 'E']
            event['abilities_estimated'] = True
    
    return metrics

def calculate_game_state_metrics(state_action_pairs, match_data=None):
    """
    Calculate combined game state metrics from state-action pairs.
    
    Args:
        state_action_pairs (list): List of state-action pairs
        match_data (dict): Match-level data for context
        
    Returns:
        dict: Dictionary of game state metrics
    """
    event_tracking = calculate_event_tracking_metrics(state_action_pairs, match_data)
    
    # Future implementations could include:
    # - Game phase transitions
    # - Win condition tracking
    # - Team advantage metrics
    
    # Combine all metrics
    game_state_metrics = {
        **event_tracking
    }
    
    return game_state_metrics 