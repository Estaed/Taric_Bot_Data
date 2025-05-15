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
    Track and analyze key game events and moments from state-action pairs.
    
    Args:
        state_action_pairs (list): List of state-action pairs
        match_data (dict): Match-level data for context
        
    Returns:
        dict: Dictionary of event tracking metrics
    """
    metrics = {
        'key_events': [],
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
            'herald': [],
            'baron': [],
            'tower': []
        },
        'teamfight_events': [],
        'death_events': [],
        'kill_participation_events': [],
        'objective_participation_rate': 0,
        'teamfight_participation_rate': 0,
        'death_timing_correlation': 0,
        'event_reaction_metrics': {
            'response_time': {},
            'action_taken': {}
        },
        'high_value_moments': [],
        'missed_opportunities': []
    }
    
    # Track game events
    events = []
    teamfights = []
    current_teamfight = None
    teamfight_threshold = 3  # Minimum champions involved in teamfight
    
    # Event detection thresholds
    dragon_proximity_threshold = 2000  # Units from dragon
    baron_proximity_threshold = 2000   # Units from baron
    herald_proximity_threshold = 2000  # Units from herald
    tower_proximity_threshold = 1500   # Units from tower
    
    # First pass: Identify events
    for idx, pair in enumerate(state_action_pairs):
        state = pair['state']
        action = pair.get('action', {})
        timestamp = state.get('game_time_seconds', 0)
        game_phase = state.get('game_phase', 'early_game').lower()
        
        # Extract relevant state information
        taric_position = (
            state.get('taric_state', {}).get('position_x', 0),
            state.get('taric_state', {}).get('position_y', 0)
        )
        
        nearby_allies = state.get('nearby_units', {}).get('allies', [])
        nearby_enemies = state.get('nearby_units', {}).get('enemies', [])
        
        # Check for deaths
        is_dead = state.get('taric_state', {}).get('is_dead', False)
        
        # Game events to track
        event_occurred = False
        event_data = {}
        
        # 1. Objective-related events detection
        # Dragon event (proximity based approach)
        dragon_position = (9500, 4000)  # Approximate dragon position
        distance_to_dragon = math.sqrt(
            (taric_position[0] - dragon_position[0])**2 + 
            (taric_position[1] - dragon_position[1])**2
        )
        
        if distance_to_dragon < dragon_proximity_threshold:
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
        
        # Baron event
        baron_position = (5500, 10000)  # Approximate baron position
        distance_to_baron = math.sqrt(
            (taric_position[0] - baron_position[0])**2 + 
            (taric_position[1] - baron_position[1])**2
        )
        
        if distance_to_baron < baron_proximity_threshold and timestamp > 20*60:  # Baron after 20 min
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
        
        # Herald event (same position as Baron, but before 20 min)
        if distance_to_baron < herald_proximity_threshold and timestamp < 20*60:
            # Check if this is a new event
            if len(metrics['objective_events']['herald']) == 0 or \
               (metrics['objective_events']['herald'] and 
                timestamp - metrics['objective_events']['herald'][-1]['timestamp'] > 60):
                
                event_occurred = True
                event_data = {
                    'type': 'herald',
                    'timestamp': timestamp,
                    'position': baron_position,  # Same position as Baron
                    'allies_nearby': len(nearby_allies),
                    'enemies_nearby': len(nearby_enemies),
                    'index': idx
                }
                metrics['objective_events']['herald'].append(event_data)
        
        # Tower event (would need actual tower positions, using placeholder approach)
        # In a real implementation, you would check distance to all tower positions
        tower_positions = [
            (5000, 5000),  # Placeholder tower position
            (9000, 9000)   # Placeholder tower position
        ]
        
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
                if 'ability' in action:
                    current_teamfight['taric_abilities_used'].append(action['ability'])
                
                # Track items used in teamfight
                if 'item_used' in action:
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
                metrics['teamfight_events'].append({
                    'type': 'teamfight',
                    'start_time': current_teamfight['start_time'],
                    'end_time': current_teamfight['end_time'],
                    'duration': current_teamfight['duration'],
                    'max_champions': current_teamfight['max_champions'],
                    'abilities_used': current_teamfight['taric_abilities_used'],
                    'items_used': current_teamfight['taric_items_used'],
                    'outcome': current_teamfight['outcome']
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
        
        # 4. Kill participation events
        # In a real implementation, you would check for actual kills
        # Here we estimate based on combat context and enemy health
        low_health_enemies = [
            e for e in nearby_enemies 
            if e.get('health_percent', 1.0) < 0.2
        ]
        
        if low_health_enemies and 'ability' in action and (
                len(metrics['kill_participation_events']) == 0 or
                (metrics['kill_participation_events'] and 
                 timestamp - metrics['kill_participation_events'][-1]['timestamp'] > 10)):
            event_occurred = True
            event_data = {
                'type': 'kill_participation',
                'timestamp': timestamp,
                'position': taric_position,
                'ability_used': action.get('ability'),
                'num_low_health_enemies': len(low_health_enemies),
                'index': idx
            }
            metrics['kill_participation_events'].append(event_data)
        
        # Add to general event list if an event occurred
        if event_occurred and event_data:
            events.append(event_data)
            
            # Add to events by phase
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
        metrics['teamfight_events'].append({
            'type': 'teamfight',
            'start_time': current_teamfight['start_time'],
            'end_time': current_teamfight['end_time'],
            'duration': current_teamfight['duration'],
            'max_champions': current_teamfight['max_champions'],
            'abilities_used': current_teamfight['taric_abilities_used'],
            'items_used': current_teamfight['taric_items_used'],
            'outcome': current_teamfight['outcome']
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
    
    # Identify missed opportunities
    # Example: When teammates died shortly after Taric's R was available
    for idx, pair in enumerate(state_action_pairs):
        state = pair['state']
        timestamp = state.get('game_time_seconds', 0)
        
        # Check if R is available
        r_cooldown = state.get('taric_state', {}).get('cooldowns', {}).get('R', 0)
        
        if r_cooldown <= 0:
            # Look for nearby dying allies
            nearby_allies = state.get('nearby_units', {}).get('allies', [])
            dying_allies = [
                a for a in nearby_allies
                if a.get('health_percent', 1.0) < 0.2
            ]
            
            # If Taric's R is available and allies are dying, it's a missed opportunity
            if dying_allies:
                # Check if R was used in the next 5 seconds
                r_used = False
                for i in range(idx, min(idx + 5, len(state_action_pairs))):
                    if state_action_pairs[i].get('action', {}).get('ability') == 'R':
                        r_used = True
                        break
                
                if not r_used:
                    metrics['missed_opportunities'].append({
                        'type': 'ult_opportunity',
                        'timestamp': timestamp,
                        'dying_allies': len(dying_allies),
                        'index': idx
                    })
    
    # Aggregate all key events for easy access
    metrics['key_events'] = events
    
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