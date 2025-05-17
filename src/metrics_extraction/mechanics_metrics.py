"""
Mechanical action metrics calculation for Taric Bot AI.

This module calculates metrics related to player mechanics and inputs,
including ability sequencing, targeting patterns, and action timing.
"""

import numpy as np
from collections import defaultdict
import math

def calculate_ability_sequence_metrics(state_action_pairs, match_data=None):
    """
    Calculate metrics related to ability sequencing and usage patterns.
    
    Args:
        state_action_pairs (list): List of state-action pairs
        match_data (dict): Match-level data for context
        
    Returns:
        dict: Dictionary of ability sequence metrics
    """
    # Ensure proper types
    if not isinstance(state_action_pairs, list):
        state_action_pairs = []
        
    if match_data is None:
        match_data = {}
    elif not isinstance(match_data, dict):
        match_data = {}
        
    metrics = {
        'ability_usage_count': {
            'Q': 0,
            'W': 0,
            'E': 0,
            'R': 0,
            'AUTO': 0
        },
        'ability_usage_percentage': {
            'Q': 0,
            'W': 0,
            'E': 0,
            'R': 0,
            'AUTO': 0
        },
        'common_ability_sequences': [],
        'ability_sequence_complexity': 0,
        'ability_combo_efficiency': 0,
        'ability_timing_consistency': 0,
        'ability_usage_by_phase': {
            'early_game': {
                'Q': 0,
                'W': 0,
                'E': 0,
                'R': 0,
                'AUTO': 0
            },
            'mid_game': {
                'Q': 0,
                'W': 0,
                'E': 0,
                'R': 0,
                'AUTO': 0
            },
            'late_game': {
                'Q': 0,
                'W': 0,
                'E': 0,
                'R': 0,
                'AUTO': 0
            }
        }
    }
    
    # Track action sequences
    ability_sequence = []
    ability_timing = []
    total_actions = 0
    
    # First pass: gather ability sequences and timing
    for pair in state_action_pairs:
        if not isinstance(pair, dict):
            continue
            
        if 'state' not in pair or not isinstance(pair['state'], dict):
            continue
            
        state = pair['state']
        action = pair.get('action', {}) if isinstance(pair.get('action'), dict) else {}
        game_phase = state.get('game_phase', 'EARLY_GAME').lower()
        timestamp = state.get('game_time_seconds', 0)
        
        ability = action.get('ability')
        
        if ability in ['Q', 'W', 'E', 'R', 'AUTO']:
            # Count ability usage
            metrics['ability_usage_count'][ability] += 1
            total_actions += 1
            
            # Count by game phase
            if game_phase in metrics['ability_usage_by_phase']:
                if ability in metrics['ability_usage_by_phase'][game_phase]:
                    metrics['ability_usage_by_phase'][game_phase][ability] += 1
            
            # Add to sequence
            ability_sequence.append(ability)
            ability_timing.append(timestamp)
    
    # Calculate ability usage percentage
    if total_actions > 0:
        for ability in metrics['ability_usage_percentage']:
            metrics['ability_usage_percentage'][ability] = (
                metrics['ability_usage_count'][ability] / total_actions
            )
    
    # Find common ability sequences (3-5 ability sequences)
    if len(ability_sequence) >= 3:
        sequence_counts = defaultdict(int)
        
        # Look for 3-ability sequences
        for i in range(len(ability_sequence) - 2):
            seq = tuple(ability_sequence[i:i+3])
            sequence_counts[seq] += 1
        
        # Get the most common sequences
        common_sequences = sorted(sequence_counts.items(), key=lambda x: x[1], reverse=True)
        metrics['common_ability_sequences'] = [
            {'sequence': list(seq), 'count': count}
            for seq, count in common_sequences[:5]  # Top 5 sequences
        ]
    
    # Calculate ability sequence complexity
    # Complexity is higher when more varied sequences are used
    if ability_sequence:
        unique_sequences = set()
        for i in range(len(ability_sequence) - 2):
            if i < 0 or i+2 >= len(ability_sequence):  # Ensure valid indices
                continue
            seq = tuple(ability_sequence[i:i+3])
            unique_sequences.add(seq)
        
        # Normalize by total possible sequences
        total_possible = max(1, len(ability_sequence) - 2)  # Avoid division by zero
        sequence_complexity = len(unique_sequences) / total_possible if total_possible > 0 else 0
        metrics['ability_sequence_complexity'] = sequence_complexity
    
    # Calculate timing consistency
    # Lower time gaps between abilities indicates better mechanics
    if len(ability_timing) >= 2:
        time_gaps = [ability_timing[i+1] - ability_timing[i] for i in range(len(ability_timing) - 1)]
        if time_gaps:  # Ensure we have gaps to calculate
            avg_gap = sum(time_gaps) / len(time_gaps)
            gap_variance = sum((gap - avg_gap) ** 2 for gap in time_gaps) / len(time_gaps)
            
            # Lower variance means more consistent timing
            # Add a small constant to avoid division by zero
            metrics['ability_timing_consistency'] = 1 / (1 + gap_variance)
    
    # Special sequences for Taric
    q_aa_combos = 0
    e_w_combos = 0
    
    # Count special Taric combos
    for i in range(len(ability_sequence) - 1):
        if i < 0 or i+1 >= len(ability_sequence):  # Ensure valid indices
            continue
            
        # Q -> AA combo (Q ability to reset auto attack)
        if ability_sequence[i] == 'Q' and ability_sequence[i+1] == 'AUTO':
            q_aa_combos += 1
        
        # E -> W combo (using W link to extend stun range)
        if ability_sequence[i] == 'W' and ability_sequence[i+1] == 'E':
            e_w_combos += 1
    
    # Calculate combo efficiency
    if total_actions > 0:
        # Higher values indicate better combo usage
        metrics['ability_combo_efficiency'] = (q_aa_combos + e_w_combos) / max(1, (total_actions / 2))
    
    return metrics


def calculate_target_selection_metrics(state_action_pairs, match_data=None):
    """
    Calculate metrics related to target selection patterns.
    
    Args:
        state_action_pairs (list): List of state-action pairs
        match_data (dict): Match-level data for context
        
    Returns:
        dict: Dictionary of target selection metrics
    """
    # Ensure proper types
    if not isinstance(state_action_pairs, list):
        state_action_pairs = []
        
    if match_data is None:
        match_data = {}
    elif not isinstance(match_data, dict):
        match_data = {}
        
    metrics = {
        'target_selection_distribution': {},
        'priority_target_focus': 0,
        'target_switching_frequency': 0,
        'defensive_targeting_percentage': 0,
        'offensive_targeting_percentage': 0,
        'target_selection_by_ability': {
            'Q': {},
            'W': {},
            'E': {},
            'R': {}
        }
    }
    
    # Track targets
    all_targets = []
    defensive_targets = 0
    offensive_targets = 0
    ability_targets = {
        'Q': [],
        'W': [],
        'E': [],
        'R': []
    }
    
    for pair in state_action_pairs:
        if not isinstance(pair, dict):
            continue
            
        if 'state' not in pair or not isinstance(pair['state'], dict):
            continue
            
        state = pair['state']
        action = pair.get('action', {}) if isinstance(pair.get('action'), dict) else {}
        
        # Skip if no action or no targets
        if not action:
            continue
            
        # Get ability and targets
        ability = action.get('ability')
        targets = action.get('targets', [])
        
        # Skip if not a valid ability or no targets
        if not ability or not isinstance(targets, list) or not targets:
            continue
            
        for target in targets:
            if not isinstance(target, dict):
                continue
                
            target_type = target.get('type', 'unknown')
            target_champion = target.get('champion', 'unknown')
            
            # Add to distribution
            target_key = f"{target_type}:{target_champion}"
            if target_key not in metrics['target_selection_distribution']:
                metrics['target_selection_distribution'][target_key] = 0
            metrics['target_selection_distribution'][target_key] += 1
            
            # Track targets by ability
            if ability in ability_targets and ability in metrics['target_selection_by_ability']:
                if target_key not in metrics['target_selection_by_ability'][ability]:
                    metrics['target_selection_by_ability'][ability][target_key] = 0
                metrics['target_selection_by_ability'][ability][target_key] += 1
            
            # Add to all targets
            all_targets.append(target_key)
            
            # Count offensive vs defensive targeting
            if target_type == 'ally':
                defensive_targets += 1
            elif target_type == 'enemy':
                offensive_targets += 1
    
    # Calculate target switching frequency
    if len(all_targets) > 1:
        switches = sum(1 for i in range(1, len(all_targets)) if all_targets[i] != all_targets[i-1])
        metrics['target_switching_frequency'] = switches / (len(all_targets) - 1)
    
    # Calculate offensive vs defensive targeting percentages
    total_targets = defensive_targets + offensive_targets
    if total_targets > 0:
        metrics['defensive_targeting_percentage'] = defensive_targets / total_targets
        metrics['offensive_targeting_percentage'] = offensive_targets / total_targets
    
    # Calculate priority target focus
    # In this simplified version, we'll assume ADC and APC champions are priority targets
    priority_champion_types = ['adc', 'apc', 'mage', 'marksman']
    priority_targets = sum(
        metrics['target_selection_distribution'].get(key, 0)
        for key in metrics['target_selection_distribution']
        if 'enemy' in key.lower() and any(pt in key.lower() for pt in priority_champion_types)
    )
    
    total_enemy_targets = sum(
        metrics['target_selection_distribution'].get(key, 0)
        for key in metrics['target_selection_distribution']
        if 'enemy' in key.lower()
    )
    
    if total_enemy_targets > 0:
        metrics['priority_target_focus'] = priority_targets / total_enemy_targets
    
    return metrics


def calculate_apm_metrics(state_action_pairs, match_data=None):
    """
    Calculate metrics related to actions per minute and input speed.
    
    Args:
        state_action_pairs (list): List of state-action pairs
        match_data (dict): Match-level data for context
        
    Returns:
        dict: Dictionary of APM metrics
    """
    # Ensure proper types
    if not isinstance(state_action_pairs, list):
        state_action_pairs = []
        
    if match_data is None:
        match_data = {}
    elif not isinstance(match_data, dict):
        match_data = {}
    
    metrics = {
        'actions_per_minute': 0,
        'ability_casts_per_minute': 0,
        'movement_commands_per_minute': 0,
        'target_selection_per_minute': 0,
        'peak_apm': 0,
        'apm_by_phase': {
            'early_game': 0,
            'mid_game': 0,
            'late_game': 0
        },
        'apm_consistency': 0,
        'input_sequence_efficiency': 0
    }
    
    # Track action counts and timestamps
    all_actions = []
    ability_casts = []
    movement_commands = []
    target_selections = []
    
    # First pass: gather action data
    for pair in state_action_pairs:
        if not isinstance(pair, dict):
            continue
            
        if 'state' not in pair or not isinstance(pair['state'], dict):
            continue
            
        state = pair['state']
        action = pair.get('action', {}) if isinstance(pair.get('action'), dict) else {}
        timestamp = state.get('game_time_seconds', 0)
        game_phase = state.get('game_phase', 'early_game').lower()
        
        # Count different action types
        if action:
            all_actions.append({
                'timestamp': timestamp,
                'phase': game_phase,
                'type': action.get('type', 'unknown')
            })
            
            # Count ability casts
            if action.get('ability') in ['Q', 'W', 'E', 'R']:
                ability_casts.append({
                    'timestamp': timestamp,
                    'phase': game_phase,
                    'ability': action.get('ability')
                })
            
            # Count movement commands
            if action.get('type') == 'movement' or action.get('movement'):
                movement_commands.append({
                    'timestamp': timestamp,
                    'phase': game_phase
                })
            
            # Count target selections
            if action.get('targets') or action.get('target'):
                target_selections.append({
                    'timestamp': timestamp,
                    'phase': game_phase
                })
    
    # Calculate APM metrics
    if state_action_pairs:
        # Get total game time from last state-action pair
        total_game_time = 0
        for pair in reversed(state_action_pairs):
            if isinstance(pair, dict) and 'state' in pair and isinstance(pair['state'], dict):
                total_game_time = pair['state'].get('game_time_seconds', 0)
                break
        
        if total_game_time > 0:
            # Convert to minutes
            total_minutes = total_game_time / 60
            
            # Calculate overall APM
            metrics['actions_per_minute'] = len(all_actions) / total_minutes if total_minutes > 0 else 0
            metrics['ability_casts_per_minute'] = len(ability_casts) / total_minutes if total_minutes > 0 else 0
            metrics['movement_commands_per_minute'] = len(movement_commands) / total_minutes if total_minutes > 0 else 0
            metrics['target_selection_per_minute'] = len(target_selections) / total_minutes if total_minutes > 0 else 0
            
            # Calculate APM by phase
            phase_durations = {'early_game': 0, 'mid_game': 0, 'late_game': 0}
            phase_action_counts = {'early_game': 0, 'mid_game': 0, 'late_game': 0}
            
            # Count actions per phase
            for action in all_actions:
                phase = action.get('phase', 'early_game')
                if phase in phase_action_counts:
                    phase_action_counts[phase] += 1
            
            # Estimate phase durations 
            # (This is a simplification - in real data you'd know precise phase times)
            if total_game_time < 900:  # < 15 minutes
                # Short game, early and mid only
                phase_durations['early_game'] = min(600, total_game_time)  # First 10 minutes
                phase_durations['mid_game'] = max(0, total_game_time - 600)  # Remainder
            else:
                # Normal game with all phases
                phase_durations['early_game'] = 600  # First 10 minutes
                phase_durations['mid_game'] = 900  # Next 15 minutes
                phase_durations['late_game'] = max(0, total_game_time - 1500)  # Remainder
            
            # Calculate APM for each phase
            for phase in phase_action_counts:
                phase_minutes = phase_durations[phase] / 60
                if phase_minutes > 0:
                    metrics['apm_by_phase'][phase] = phase_action_counts[phase] / phase_minutes
            
            # Calculate peak APM (highest APM in any 1-minute window)
            if len(all_actions) > 0:
                # Group actions into 1-minute windows
                window_actions = {}
                for action in all_actions:
                    minute = int(action['timestamp'] / 60)
                    if minute not in window_actions:
                        window_actions[minute] = 0
                    window_actions[minute] += 1
                
                # Find peak
                if window_actions:
                    metrics['peak_apm'] = max(window_actions.values())
            
            # Calculate APM consistency (standard deviation of APM across 1-minute windows)
            if window_actions:
                window_apms = list(window_actions.values())
                if window_apms:
                    mean_apm = sum(window_apms) / len(window_apms)
                    variance = sum((apm - mean_apm) ** 2 for apm in window_apms) / len(window_apms)
                    std_dev = variance ** 0.5
                    
                    # Convert to a 0-1 score (lower std dev = higher consistency)
                    metrics['apm_consistency'] = 1 / (1 + std_dev) if std_dev > 0 else 1
    
    # Calculate input sequence efficiency
    # (Measures how well inputs are chained together without unnecessary actions)
    # Simplified version: lower time between intentional actions = higher efficiency
    if len(ability_casts) > 1:
        ability_gaps = [ability_casts[i+1]['timestamp'] - ability_casts[i]['timestamp'] 
                        for i in range(len(ability_casts) - 1)]
        avg_gap = sum(ability_gaps) / len(ability_gaps) if ability_gaps else 0
        
        # Normalize: 0 = poor, 1 = excellent
        # Assuming gaps of ~1-2 seconds are good, >5 seconds is suboptimal
        if avg_gap > 0:
            metrics['input_sequence_efficiency'] = min(1.0, 3.0 / avg_gap)
    
    return metrics


def calculate_interaction_timing_metrics(state_action_pairs, match_data=None):
    """
    Calculate detailed interaction timing metrics, analyzing the precise timing
    between different actions and game events.
    
    Args:
        state_action_pairs (list): List of state-action pairs
        match_data (dict): Match-level data for context
        
    Returns:
        dict: Dictionary of interaction timing metrics
    """
    metrics = {
        'reaction_times': {
            'enemy_aggression': [],
            'ally_health_drop': [],
            'objective_spawn': [],
            'team_fight_start': []
        },
        'average_reaction_time': {
            'enemy_aggression': 0,
            'ally_health_drop': 0,
            'objective_spawn': 0,
            'team_fight_start': 0
        },
        'ability_timing_patterns': {
            'combat_start': {
                'Q': 0,
                'W': 0,
                'E': 0,
                'R': 0
            },
            'combat_middle': {
                'Q': 0,
                'W': 0,
                'E': 0,
                'R': 0
            },
            'combat_end': {
                'Q': 0,
                'W': 0,
                'E': 0,
                'R': 0
            }
        },
        'action_interval_distribution': {},
        'sequence_timing_variance': 0,
        'combo_execution_speed': {
            'W_E_combo': [],
            'Q_AUTO_combo': [],
            'multi_stun_combo': [],
            'R_timing': []
        },
        'average_combo_speed': {
            'W_E_combo': 0,
            'Q_AUTO_combo': 0,
            'multi_stun_combo': 0,
            'R_timing': 0
        },
        'ability_timing_by_game_state': {
            'under_pressure': {
                'Q': 0,
                'W': 0,
                'E': 0,
                'R': 0
            },
            'favorable_state': {
                'Q': 0,
                'W': 0,
                'E': 0,
                'R': 0
            },
            'neutral_state': {
                'Q': 0,
                'W': 0,
                'E': 0,
                'R': 0
            }
        },
        'input_precision': 0
    }
    
    # Track game events and player actions
    events = []
    actions = []
    combat_segments = []
    current_combat = None
    
    # Collect all game events and actions with timestamps
    for i, pair in enumerate(state_action_pairs):
        state = pair['state']
        action = pair.get('action', {})
        timestamp = state.get('game_time_seconds', 0)
        
        # Record action if it exists
        if action and 'ability' in action:
            actions.append({
                'type': 'action',
                'ability': action.get('ability'),
                'timestamp': timestamp,
                'targets': action.get('targets', []),
                'target': action.get('target'),
                'index': i
            })
        
        # Detect and record game events
        # Enemy aggression detection (enemy champion getting close with low health)
        nearby_enemies = state.get('nearby_units', {}).get('enemies', [])
        taric_health = state.get('taric_state', {}).get('health_percent', 1.0)
        nearby_allies = state.get('nearby_units', {}).get('allies', [])
        
        # Enemy aggression event
        close_enemies = [e for e in nearby_enemies if e.get('distance', 1000) < 500]
        if close_enemies and len(close_enemies) >= 2:
            events.append({
                'type': 'enemy_aggression',
                'timestamp': timestamp,
                'enemies': close_enemies,
                'index': i
            })
        
        # Ally health drop event
        low_allies = [a for a in nearby_allies if a.get('health_percent', 1.0) < 0.4]
        if low_allies:
            events.append({
                'type': 'ally_health_drop',
                'timestamp': timestamp,
                'allies': low_allies,
                'index': i
            })
        
        # Objective spawn event (simplified, assuming events at specific times)
        if abs(timestamp - 5*60) < 5:  # First dragon around 5 min
            events.append({
                'type': 'objective_spawn',
                'timestamp': timestamp,
                'objective': 'dragon',
                'index': i
            })
        elif abs(timestamp - 8*60) < 5:  # Rift Herald around 8 min
            events.append({
                'type': 'objective_spawn',
                'timestamp': timestamp,
                'objective': 'herald',
                'index': i
            })
        elif abs(timestamp - 20*60) < 5:  # Baron around 20 min
            events.append({
                'type': 'objective_spawn',
                'timestamp': timestamp,
                'objective': 'baron',
                'index': i
            })
        
        # Team fight detection (when there are multiple allies and enemies nearby)
        if len(nearby_allies) >= 2 and len(nearby_enemies) >= 2:
            if current_combat is None:
                current_combat = {
                    'start_time': timestamp,
                    'start_index': i,
                    'actions': [],
                    'end_time': None,
                    'end_index': None
                }
                events.append({
                    'type': 'team_fight_start',
                    'timestamp': timestamp,
                    'allies': nearby_allies,
                    'enemies': nearby_enemies,
                    'index': i
                })
        elif current_combat is not None:
            # Combat ended if no enemies or allies nearby for 5 seconds
            if timestamp - current_combat['start_time'] > 5:
                current_combat['end_time'] = timestamp
                current_combat['end_index'] = i
                combat_segments.append(current_combat)
                current_combat = None
    
    # Close any open combat segments
    if current_combat is not None and current_combat['end_time'] is None:
        current_combat['end_time'] = state_action_pairs[-1]['state'].get('game_time_seconds', 0)
        current_combat['end_index'] = len(state_action_pairs) - 1
        combat_segments.append(current_combat)
    
    # Calculate reaction times to events
    for event in events:
        event_time = event['timestamp']
        event_type = event['type']
        
        # Find the next action after this event
        next_actions = [a for a in actions if a['timestamp'] > event_time]
        if next_actions:
            next_action = min(next_actions, key=lambda a: a['timestamp'])
            reaction_time = next_action['timestamp'] - event_time
            
            # Only count reasonable reaction times (less than 5 seconds)
            if reaction_time <= 5:
                metrics['reaction_times'][event_type].append(reaction_time)
    
    # Calculate average reaction times
    for event_type, times in metrics['reaction_times'].items():
        if times:
            metrics['average_reaction_time'][event_type] = sum(times) / len(times)
    
    # Analyze ability timings in combat scenarios
    for combat in combat_segments:
        start_time = combat['start_time']
        end_time = combat['end_time']
        duration = end_time - start_time
        
        if duration <= 0:
            continue  # Skip invalid combats
        
        # Get actions during this combat
        combat_actions = [a for a in actions if start_time <= a['timestamp'] <= end_time]
        
        # Divide combat into three phases
        early_threshold = start_time + duration * 0.33
        late_threshold = start_time + duration * 0.66
        
        for action in combat_actions:
            action_time = action['timestamp']
            ability = action.get('ability')
            
            if ability in ['Q', 'W', 'E', 'R']:
                # Determine which phase of combat
                if action_time <= early_threshold:
                    metrics['ability_timing_patterns']['combat_start'][ability] += 1
                elif action_time <= late_threshold:
                    metrics['ability_timing_patterns']['combat_middle'][ability] += 1
                else:
                    metrics['ability_timing_patterns']['combat_end'][ability] += 1
    
    # Calculate action interval distribution
    action_intervals = []
    for i in range(1, len(actions)):
        interval = actions[i]['timestamp'] - actions[i-1]['timestamp']
        # Group intervals into 0.5 second buckets
        bucket = round(interval * 2) / 2
        if bucket not in metrics['action_interval_distribution']:
            metrics['action_interval_distribution'][bucket] = 0
        metrics['action_interval_distribution'][bucket] += 1
        action_intervals.append(interval)
    
    # Calculate variance in sequence timing
    if action_intervals:
        avg_interval = sum(action_intervals) / len(action_intervals)
        variance = sum((interval - avg_interval) ** 2 for interval in action_intervals) / len(action_intervals)
        metrics['sequence_timing_variance'] = variance
    
    # Analyze combo execution speed
    for i in range(len(actions) - 1):
        current = actions[i]
        next_action = actions[i+1]
        combo_time = next_action['timestamp'] - current['timestamp']
        
        # W-E combo (Bastion to extended stun)
        if current['ability'] == 'W' and next_action['ability'] == 'E' and combo_time <= 2:
            metrics['combo_execution_speed']['W_E_combo'].append(combo_time)
        
        # Q-AUTO combo (healing to auto-attack reset)
        if current['ability'] == 'Q' and next_action['ability'] == 'AUTO' and combo_time <= 1:
            metrics['combo_execution_speed']['Q_AUTO_combo'].append(combo_time)
    
    # Analyze multi-stun combos (E targeting multiple enemies)
    for action in actions:
        if action['ability'] == 'E':
            targets = action.get('targets', [])
            if len(targets) >= 2:  # Multi-target stun
                # Calculate "setup time" - time since last ability
                prev_actions = [a for a in actions if a['timestamp'] < action['timestamp']]
                if prev_actions:
                    last_action = max(prev_actions, key=lambda a: a['timestamp'])
                    setup_time = action['timestamp'] - last_action['timestamp']
                    metrics['combo_execution_speed']['multi_stun_combo'].append(setup_time)
        
        # Analyze R timing relative to combat start
        if action['ability'] == 'R':
            # Find the closest combat start before this R
            combat_starts = [e for e in events 
                            if e['type'] == 'team_fight_start' and e['timestamp'] <= action['timestamp']]
            if combat_starts:
                latest_start = max(combat_starts, key=lambda e: e['timestamp'])
                r_timing = action['timestamp'] - latest_start['timestamp']
                metrics['combo_execution_speed']['R_timing'].append(r_timing)
    
    # Calculate average combo speeds
    for combo_type, times in metrics['combo_execution_speed'].items():
        if times:
            metrics['average_combo_speed'][combo_type] = sum(times) / len(times)
    
    # Analyze ability timing by game state
    for i, pair in enumerate(state_action_pairs):
        state = pair['state']
        action = pair.get('action', {})
        
        if 'ability' not in action:
            continue
            
        ability = action['ability']
        if ability not in ['Q', 'W', 'E', 'R']:
            continue
            
        # Determine game state based on health, nearby units, etc.
        taric_health = state.get('taric_state', {}).get('health_percent', 1.0)
        nearby_enemies = len(state.get('nearby_units', {}).get('enemies', []))
        nearby_allies = len(state.get('nearby_units', {}).get('allies', []))
        
        # Under pressure: low health or outnumbered
        if taric_health < 0.4 or nearby_enemies > nearby_allies + 1:
            metrics['ability_timing_by_game_state']['under_pressure'][ability] += 1
        # Favorable: healthy and numerical advantage
        elif taric_health > 0.7 and nearby_allies > nearby_enemies:
            metrics['ability_timing_by_game_state']['favorable_state'][ability] += 1
        # Neutral: otherwise
        else:
            metrics['ability_timing_by_game_state']['neutral_state'][ability] += 1
    
    # Calculate input precision (based on optimal combo timing)
    precision_scores = []
    
    # Optimal W-E combo is about 0.5 seconds
    if metrics['combo_execution_speed']['W_E_combo']:
        w_e_precision = [max(0, 1 - abs(t - 0.5) / 0.5) for t in metrics['combo_execution_speed']['W_E_combo']]
        precision_scores.extend(w_e_precision)
    
    # Optimal Q-AUTO combo is about 0.2 seconds
    if metrics['combo_execution_speed']['Q_AUTO_combo']:
        q_auto_precision = [max(0, 1 - abs(t - 0.2) / 0.2) for t in metrics['combo_execution_speed']['Q_AUTO_combo']]
        precision_scores.extend(q_auto_precision)
    
    # Overall input precision score
    if precision_scores:
        metrics['input_precision'] = sum(precision_scores) / len(precision_scores)
    
    return metrics

def calculate_item_ability_metrics(state_action_pairs, match_data=None):
    """
    Calculate metrics related to item active usage in relation to ability casts.
    
    Args:
        state_action_pairs (list): List of state-action pairs
        match_data (dict): Match-level data for context
        
    Returns:
        dict: Dictionary of item-ability interaction metrics
    """
    metrics = {
        'item_usage_count': defaultdict(int),
        'item_usage_by_phase': {
            'early_game': defaultdict(int),
            'mid_game': defaultdict(int),
            'late_game': defaultdict(int)
        },
        'item_ability_combinations': defaultdict(int),
        'item_ability_timing': {},  # Timing between item use and related ability
        'item_efficiency_score': {},  # How effectively items are used
        'common_item_ability_sequences': [],
        'item_usage_in_combat': defaultdict(int),
        'item_usage_out_of_combat': defaultdict(int),
        'ward_usage_count': 0,
        'ward_usage_by_phase': {
            'early_game': 0,
            'mid_game': 0,
            'late_game': 0
        },
        'ward_types': {}
    }
    
    # Define relevant active items for Taric
    support_active_items = [
        'LOCKET_OF_THE_IRON_SOLARI',  # AOE shield
        'REDEMPTION',                 # AOE heal
        'KNIGHTS_VOW',                # Damage redirection
        'ZEKES_CONVERGENCE',          # Empowers ally
        'SHURELYAS_BATTLESONG',       # Movement speed
        'CHEMTECH_PUTRIFIER',         # Anti-heal
        'MIKAEL_CRUCIBLE',            # Cleanse
        'ARDENT_CENSER',              # Attack speed buff 
        'STAFF_OF_FLOWING_WATER',     # AP buff
        'THORNMAIL',                  # Anti-heal
        'CONTROL_WARD',               # Vision
        'STEALTH_WARD',               # Vision
        'BLUE_TRINKET',               # Vision
        'HEALTH_POTION',              # Healing
        'CORRUPTING_POTION',          # Healing + damage
        # Add common ward variants
        'WARD',                       # Common ward name
        'TRINKET_WARD',               # Trinket ward
        'YELLOW_TRINKET',             # Yellow trinket ward
        'SIGHT_WARD',                 # Sight ward
        'VISION_WARD',                # Vision ward
        'FARSIGHT_ALTERATION',        # Blue trinket official name
        'ORACLE_LENS',                # Red trinket
        'SWEEPING_LENS',              # Red trinket variant
        'ZOMBIE_WARD',                # Rune ward
        'GHOST_PORO',                 # Rune vision
        'WARD_TOTEM',                 # Ward totem
    ]
    
    # Add a dedicated ward detection variable
    ward_items = [
        'CONTROL_WARD', 'STEALTH_WARD', 'WARD', 'TRINKET_WARD', 
        'YELLOW_TRINKET', 'SIGHT_WARD', 'VISION_WARD', 'BLUE_TRINKET',
        'FARSIGHT_ALTERATION', 'ORACLE_LENS', 'SWEEPING_LENS', 
        'ZOMBIE_WARD', 'GHOST_PORO', 'WARD_TOTEM'
    ]
    
    # Track item usage and ability casts with timestamps
    item_usages = []
    ability_casts = []
    
    # First pass: collect all item usages and ability casts
    for idx, pair in enumerate(state_action_pairs):
        state = pair['state']
        action = pair.get('action', {})
        game_phase = state.get('game_phase', 'EARLY_GAME').lower()
        timestamp = state.get('game_time_seconds', 0)
        
        # Track item usage
        if 'item_used' in action:
            item_name = action['item_used']
            
            # Only track relevant active items
            if item_name in support_active_items:
                # Record item usage
                metrics['item_usage_count'][item_name] += 1
                
                # Record by phase
                if game_phase in metrics['item_usage_by_phase']:
                    metrics['item_usage_by_phase'][game_phase][item_name] += 1
                
                # Record item usage with context
                nearby_enemies = state.get('nearby_units', {}).get('enemies', [])
                in_combat = len(nearby_enemies) > 0
                
                if in_combat:
                    metrics['item_usage_in_combat'][item_name] += 1
                else:
                    metrics['item_usage_out_of_combat'][item_name] += 1
                
                # Add to item usages list
                item_usages.append({
                    'item': item_name,
                    'timestamp': timestamp,
                    'in_combat': in_combat,
                    'target': action.get('target'),
                    'targets': action.get('targets', []),
                    'index': idx
                })
                
                # Specifically track ward placements
                if item_name in ward_items or any(ward_term in str(item_name).upper() for ward_term in ['WARD', 'TRINKET', 'VISION']):
                    # Create a ward-specific entry in metrics
                    if 'ward_usage_count' not in metrics:
                        metrics['ward_usage_count'] = 0
                        metrics['ward_usage_by_phase'] = {
                            'early_game': 0,
                            'mid_game': 0,
                            'late_game': 0
                        }
                        metrics['ward_types'] = {}
                    
                    # Increment ward counters
                    metrics['ward_usage_count'] += 1
                    if game_phase in metrics['ward_usage_by_phase']:
                        metrics['ward_usage_by_phase'][game_phase] += 1
                    
                    # Track ward type
                    if item_name not in metrics['ward_types']:
                        metrics['ward_types'][item_name] = 0
                    metrics['ward_types'][item_name] += 1
        
        # Also check for ward placement actions (might be recorded differently than item usage)
        ward_action = False
        if action.get('ability') == 'WARD' or action.get('action_type') == 'WARD_PLACEMENT':
            ward_action = True
        elif action.get('ability') in ['TRINKET', 'ITEM1', 'ITEM2', 'ITEM3', 'ITEM4', 'ITEM5', 'ITEM6'] and any(ward_term in str(action.get('item', '')).upper() for ward_term in ['WARD', 'TRINKET', 'VISION']):
            ward_action = True
        elif 'ward_placed' in action or 'place_ward' in action:
            ward_action = True
        elif action.get('type') == 'WARD_PLACED' or action.get('taric_action') == 'WARD_PLACED':
            ward_action = True
        # Also check the events array for ward placements
        elif 'events' in pair:
            events = pair.get('events', [])
            for event in events:
                if isinstance(event, dict) and (event.get('type') == 'WARD_PLACED' or event.get('taric_action') == 'WARD_PLACED'):
                    ward_action = True
                    break
        
        if ward_action:
            # Initialize ward metrics if not already done
            if 'ward_usage_count' not in metrics:
                metrics['ward_usage_count'] = 0
                metrics['ward_usage_by_phase'] = {
                    'early_game': 0,
                    'mid_game': 0,
                    'late_game': 0
                }
                metrics['ward_types'] = {}
            
            # Get ward type (or use a default if unknown)
            ward_type = action.get('item', 'UNKNOWN_WARD')
            
            # Increment ward counters
            metrics['ward_usage_count'] += 1
            if game_phase in metrics['ward_usage_by_phase']:
                metrics['ward_usage_by_phase'][game_phase] += 1
            
            # Track ward type
            if ward_type not in metrics['ward_types']:
                metrics['ward_types'][ward_type] = 0
            metrics['ward_types'][ward_type] += 1
                
        # Track ability casts
        if 'ability' in action:
            ability = action.get('ability')
            if ability in ['Q', 'W', 'E', 'R']:
                ability_casts.append({
                    'ability': ability,
                    'timestamp': timestamp,
                    'target': action.get('target'),
                    'targets': action.get('targets', []),
                    'index': idx
                })
    
    # Calculate item-ability combinations and timing
    for item_usage in item_usages:
        item_time = item_usage['timestamp']
        item_name = item_usage['item']
        
        # Look for abilities used within 3 seconds before or after item usage
        related_abilities = [
            ability for ability in ability_casts
            if abs(ability['timestamp'] - item_time) <= 3
        ]
        
        # Record item-ability combinations
        for ability in related_abilities:
            combo_key = f"{item_name}_{ability['ability']}"
            metrics['item_ability_combinations'][combo_key] += 1
            
            # Record timing (how many seconds between item and ability)
            if combo_key not in metrics['item_ability_timing']:
                metrics['item_ability_timing'][combo_key] = []
            
            timing = abs(ability['timestamp'] - item_time)
            metrics['item_ability_timing'][combo_key].append(timing)
    
    # Calculate average timing for each item-ability combination
    for combo, timings in metrics['item_ability_timing'].items():
        if timings:
            metrics['item_ability_timing'][combo] = sum(timings) / len(timings)
    
    # Calculate efficiency scores for specific item-ability combinations
    efficiency_ratings = {}
    
    # Locket + R (Cosmic Radiance) - good combo for team fights
    locket_r_combo = metrics['item_ability_combinations'].get('LOCKET_OF_THE_IRON_SOLARI_R', 0)
    total_locket = metrics['item_usage_count'].get('LOCKET_OF_THE_IRON_SOLARI', 0)
    if total_locket > 0:
        efficiency_ratings['LOCKET_OF_THE_IRON_SOLARI'] = locket_r_combo / total_locket
    
    # Redemption + R - another good team fight combo
    redemption_r_combo = metrics['item_ability_combinations'].get('REDEMPTION_R', 0)
    total_redemption = metrics['item_usage_count'].get('REDEMPTION', 0)
    if total_redemption > 0:
        efficiency_ratings['REDEMPTION'] = redemption_r_combo / total_redemption
    
    # Knights Vow + W (linking carry)
    knights_w_combo = metrics['item_ability_combinations'].get('KNIGHTS_VOW_W', 0)
    total_knights = metrics['item_usage_count'].get('KNIGHTS_VOW', 0)
    if total_knights > 0:
        efficiency_ratings['KNIGHTS_VOW'] = knights_w_combo / total_knights
    
    # Mikael's Crucible timing efficiency (should be used reactively)
    if 'MIKAEL_CRUCIBLE' in metrics['item_usage_in_combat']:
        combat_usage = metrics['item_usage_in_combat']['MIKAEL_CRUCIBLE']
        total_usage = metrics['item_usage_count']['MIKAEL_CRUCIBLE']
        if total_usage > 0:
            efficiency_ratings['MIKAEL_CRUCIBLE'] = combat_usage / total_usage
    
    # Add efficiency ratings to metrics
    metrics['item_efficiency_score'] = efficiency_ratings
    
    # Find common item-ability sequences
    all_actions = []
    
    # Combine item usages and ability casts into a single chronological list
    for item in item_usages:
        all_actions.append(('item', item['item'], item['timestamp']))
    
    for ability in ability_casts:
        all_actions.append(('ability', ability['ability'], ability['timestamp']))
    
    # Sort by timestamp
    all_actions.sort(key=lambda x: x[2])
    
    # Extract action sequences (look at 3-action windows)
    if len(all_actions) >= 3:
        sequence_counts = defaultdict(int)
        
        for i in range(len(all_actions) - 2):
            seq = (
                f"{all_actions[i][0]}_{all_actions[i][1]}",
                f"{all_actions[i+1][0]}_{all_actions[i+1][1]}",
                f"{all_actions[i+2][0]}_{all_actions[i+2][1]}"
            )
            sequence_counts[seq] += 1
        
        # Get most common sequences
        common_sequences = sorted(sequence_counts.items(), key=lambda x: x[1], reverse=True)
        metrics['common_item_ability_sequences'] = [
            {'sequence': list(seq), 'count': count}
            for seq, count in common_sequences[:5]  # Top 5 sequences
        ]
    
    return metrics

def calculate_mouse_click_metrics(state_action_pairs, match_data=None):
    """
    Calculate metrics related to mouse clicks from state-action pairs.
    
    Args:
        state_action_pairs (list): List of state-action pairs
        match_data (dict): Match-level data for context
        
    Returns:
        dict: Dictionary of mouse click metrics
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
        'clicks_per_minute': 0,
        'clicks_per_action': 0,
        'click_accuracy': 0,
        'click_distribution': {},
        'avg_click_distance': 0,
        'click_frequency_in_combat': 0,
        'misclick_rate': 0
    }
    
    # Count total clicks
    total_clicks = 0
    total_actions = 0
    click_positions = []
    click_targets = []
    accurate_clicks = 0
    combat_clicks = 0
    combat_duration = 0
    is_in_combat = False
    
    # For the click distribution map
    map_regions = {
        'ally_base': 0,
        'enemy_base': 0,
        'top_lane': 0,
        'mid_lane': 0,
        'bottom_lane': 0,
        'ally_jungle': 0,
        'enemy_jungle': 0,
        'river': 0,
        'other': 0
    }
    
    # Collect game time
    game_time_seconds = 0
    if state_action_pairs:
        last_pair = state_action_pairs[-1]
        if isinstance(last_pair, dict) and 'state' in last_pair and isinstance(last_pair['state'], dict):
            game_time_seconds = last_pair['state'].get('game_time_seconds', 0)
    
    # Process all clicks in state-action pairs
    previous_position = None
    
    for pair in state_action_pairs:
        if not isinstance(pair, dict):
            continue
            
        # Check validity of state and action
        if 'state' not in pair or not isinstance(pair['state'], dict):
            continue
            
        state = pair.get('state', {})
        action = pair.get('action', {})
        if not isinstance(action, dict):
            action = {}
        
        # Track if in combat
        in_combat_now = state.get('in_combat', False)
        if in_combat_now and not is_in_combat:
            is_in_combat = True
            combat_start_time = state.get('game_time_seconds', 0)
        elif not in_combat_now and is_in_combat:
            is_in_combat = False
            combat_end_time = state.get('game_time_seconds', 0)
            combat_duration += combat_end_time - combat_start_time
        
        # Count actions
        if action:
            total_actions += 1
        
        # Get click data
        clicks = action.get('clicks', [])
        
        # Handle the case where clicks is an integer instead of a list
        if isinstance(clicks, int):
            # If clicks is just a count, we can't get detailed metrics
            total_clicks += clicks
            if is_in_combat:
                combat_clicks += clicks
            continue
            
        # Normal case where clicks is a list
        if not isinstance(clicks, list):
            clicks = []
        
        # Process each click
        for click in clicks:
            total_clicks += 1
            
            if is_in_combat:
                combat_clicks += 1
            
            # Get click position
            if isinstance(click, dict):
                position = click.get('position')
                target = click.get('target')
                
                if position:
                    click_positions.append(position)
                    
                    # Calculate map region
                    region = get_map_region(position)
                    if region in map_regions:
                        map_regions[region] += 1
                
                if target:
                    click_targets.append(target)
                    accurate_clicks += 1
                
                # Check if we have a previous position to calculate distance
                if previous_position and position:
                    try:
                        # Calculate Euclidean distance between clicks
                        dx = position[0] - previous_position[0]
                        dy = position[1] - previous_position[1]
                        distance = (dx**2 + dy**2)**0.5
                        metrics['avg_click_distance'] += distance
                    except (IndexError, TypeError):
                        pass
                
                previous_position = position
    
    # Calculate metrics
    if game_time_seconds > 0:
        # Convert to minutes
        game_time_minutes = game_time_seconds / 60
        if game_time_minutes > 0:
            metrics['clicks_per_minute'] = total_clicks / game_time_minutes
    
    if total_actions > 0:
        metrics['clicks_per_action'] = total_clicks / total_actions
    
    if total_clicks > 0:
        metrics['click_accuracy'] = accurate_clicks / total_clicks
        
        # Normalize click distribution
        total_region_clicks = sum(map_regions.values())
        if total_region_clicks > 0:
            metrics['click_distribution'] = {
                region: count / total_region_clicks 
                for region, count in map_regions.items()
            }
        
        # Calculate average click distance
        if len(click_positions) > 1:
            metrics['avg_click_distance'] = metrics['avg_click_distance'] / (len(click_positions) - 1)
    
    # Calculate combat click frequency
    if combat_duration > 0:
        metrics['click_frequency_in_combat'] = combat_clicks / (combat_duration / 60)  # per minute
    
    # Calculate misclick rate (clicks without targets)
    if total_clicks > 0:
        metrics['misclick_rate'] = 1 - (len(click_targets) / total_clicks)
    
    return metrics
    
def get_map_region(position):
    """
    Determine the map region from a position.
    
    Args:
        position (list): [x, y] coordinates
        
    Returns:
        str: Map region
    """
    # Simple map region check based on position
    # This is just a placeholder - a real implementation would use actual map regions
    try:
        x, y = position
        
        # Basic region mapping (assumes standard map coordinates)
        # Coordinate assumptions: [0,0] is bottom-left, [15000,15000] is top-right
        if x < 3000 and y < 3000:
            return 'ally_base'
        elif x > 12000 and y > 12000:
            return 'enemy_base'
        elif x < 5000 and y > 10000:
            return 'top_lane'
        elif 5000 <= x <= 10000 and 5000 <= y <= 10000:
            return 'mid_lane'
        elif x > 10000 and y < 5000:
            return 'bottom_lane'
        elif x < 7500 and y < 7500:
            return 'ally_jungle'
        elif x > 7500 and y > 7500:
            return 'enemy_jungle'
        elif (5000 <= x <= 10000 and (y < 5000 or y > 10000)) or ((x < 5000 or x > 10000) and 5000 <= y <= 10000):
            return 'river'
        else:
            return 'other'
    except (TypeError, IndexError):
        return 'other'

def calculate_auto_attack_reset_metrics(state_action_pairs, match_data=None):
    """
    Calculate metrics related to auto-attack reset timing using abilities.
    
    Args:
        state_action_pairs (list): List of state-action pairs
        match_data (dict): Match-level data for context
        
    Returns:
        dict: Dictionary of auto-attack reset metrics
    """
    metrics = {
        'total_auto_attacks': 0,
        'auto_attack_resets_total': 0,
        'auto_attack_resets_by_ability': {
            'Q': 0,  # Taric Q can reset auto attack
            'W': 0,
            'E': 0
        },
        'reset_timing_consistency': 0,
        'reset_timing_average': 0,
        'reset_success_rate': 0,
        'auto_attack_dps': 0,
        'auto_attack_frequency': {
            'early_game': 0,
            'mid_game': 0,
            'late_game': 0
        },
        'aa_reset_by_phase': {
            'early_game': 0,
            'mid_game': 0,
            'late_game': 0
        },
        'aa_reset_in_combat': 0,
        'aa_reset_in_trades': 0,
        'optimal_reset_percentage': 0
    }
    
    # Extract auto attacks and abilities
    auto_attacks = []
    ability_usages = []
    
    # First pass: collect all auto attacks and ability usages
    for idx, pair in enumerate(state_action_pairs):
        state = pair['state']
        action = pair.get('action', {})
        timestamp = state.get('game_time_seconds', 0)
        game_phase = state.get('game_phase', 'early_game').lower()
        
        if action.get('ability') == 'AUTO':
            # Record auto attack
            auto_attacks.append({
                'timestamp': timestamp,
                'index': idx,
                'phase': game_phase,
                'in_combat': len(state.get('nearby_units', {}).get('enemies', [])) > 0
            })
            metrics['total_auto_attacks'] += 1
        
        elif action.get('ability') in ['Q', 'W', 'E']:
            # Record ability usage
            ability_usages.append({
                'ability': action.get('ability'),
                'timestamp': timestamp,
                'index': idx,
                'phase': game_phase,
                'in_combat': len(state.get('nearby_units', {}).get('enemies', [])) > 0
            })
    
    # Calculate auto attack resets (when an auto attack follows an ability within 0.5 seconds)
    reset_timings = []
    
    for i, aa in enumerate(auto_attacks):
        if i == 0:
            continue  # Skip first auto attack
        
        # Look for abilities used just before this auto attack
        prev_timestamp = aa['timestamp']
        
        for ability in ability_usages:
            # Check if ability was used 0.1-0.5 seconds before auto attack
            time_diff = prev_timestamp - ability['timestamp']
            if 0.1 <= time_diff <= 0.5:
                # This could be an auto attack reset
                metrics['auto_attack_resets_total'] += 1
                metrics['auto_attack_resets_by_ability'][ability['ability']] += 1
                
                # Record timing
                reset_timings.append(time_diff)
                
                # Record phase information
                if aa['phase'] in metrics['aa_reset_by_phase']:
                    metrics['aa_reset_by_phase'][aa['phase']] += 1
                
                # Record combat status
                if aa['in_combat']:
                    metrics['aa_reset_in_combat'] += 1
                
                # Assuming a trade is when there are 1-2 enemies nearby
                if aa['in_combat'] and len([e for e in state_action_pairs[aa['index']]['state'].get('nearby_units', {}).get('enemies', []) if e.get('distance', 0) < 700]) <= 2:
                    metrics['aa_reset_in_trades'] += 1
                
                break  # Only count one reset per auto attack
    
    # Calculate reset timing consistency
    if reset_timings:
        avg_timing = sum(reset_timings) / len(reset_timings)
        metrics['reset_timing_average'] = avg_timing
        
        # Calculate timing variance (lower is better)
        variance = sum((t - avg_timing) ** 2 for t in reset_timings) / len(reset_timings)
        metrics['reset_timing_consistency'] = 1 / (1 + variance)  # Transform to a 0-1 score
        
        # Optimal resets are those that happen very quickly after the ability
        optimal_resets = sum(1 for t in reset_timings if t <= 0.3)
        metrics['optimal_reset_percentage'] = optimal_resets / len(reset_timings)
    
    # Calculate reset success rate (resets divided by potential reset opportunities)
    potential_resets = len([a for a in ability_usages if a['ability'] == 'Q'])  # Q is main reset ability
    if potential_resets > 0:
        q_resets = metrics['auto_attack_resets_by_ability']['Q']
        metrics['reset_success_rate'] = q_resets / potential_resets
    
    # Calculate auto attack frequency by game phase
    phase_durations = {
        'early_game': 0,
        'mid_game': 0,
        'late_game': 0
    }
    
    phase_aas = {
        'early_game': 0,
        'mid_game': 0,
        'late_game': 0
    }
    
    for aa in auto_attacks:
        if aa['phase'] in phase_aas:
            phase_aas[aa['phase']] += 1
    
    for pair in state_action_pairs:
        phase = pair['state'].get('game_phase', 'early_game').lower()
        if phase in phase_durations:
            phase_durations[phase] += 1
    
    # Convert durations from frames to minutes
    for phase, frames in phase_durations.items():
        minutes = frames / 60
        if minutes > 0:
            metrics['auto_attack_frequency'][phase] = phase_aas[phase] / minutes
    
    # Calculate estimated DPS from auto attacks
    total_game_time = state_action_pairs[-1]['state'].get('game_time_seconds', 0) if state_action_pairs else 0
    if total_game_time > 0:
        # Simple approximation, would be more accurate with actual damage values
        metrics['auto_attack_dps'] = metrics['total_auto_attacks'] / (total_game_time / 60)
    
    return metrics

def calculate_camera_control_metrics(state_action_pairs, match_data=None):
    """
    Calculate metrics related to camera control patterns.
    
    Args:
        state_action_pairs (list): List of state-action pairs
        match_data (dict): Match-level data for context
        
    Returns:
        dict: Dictionary of camera control pattern metrics
    """
    metrics = {
        'camera_movement_frequency': 0,
        'camera_position_changes': 0,
        'camera_patterns': {
            'locked': 0,       # Camera follows champion
            'unlocked': 0,     # Free camera
            'mixed': 0         # Combination
        },
        'camera_movement_by_phase': {
            'early_game': 0,
            'mid_game': 0,
            'late_game': 0
        },
        'camera_focus_areas': {
            'self_centered': 0,
            'lane_centered': 0,
            'map_awareness': 0
        },
        'camera_control_during_combat': 0,
        'camera_control_during_movement': 0,
        'minimap_view_frequency': 0,
        'camera_movement_before_objectives': 0,
        'camera_efficiency': 0,
        'camera_hotkey_usage': 0,
        'camera_control_smoothness': 0
    }
    
    # Note: In practice, this would use actual camera position data
    # Since we don't have real camera data in the current dataset,
    # we'll implement an approximation and placeholders
    
    # Camera position and movement tracking
    camera_positions = []
    map_view_events = []
    smooth_movements = 0
    jerky_movements = 0
    
    # Track position of champions that might indicate camera movement
    for idx, pair in enumerate(state_action_pairs):
        state = pair['state']
        action = pair.get('action', {})
        timestamp = state.get('game_time_seconds', 0)
        game_phase = state.get('game_phase', 'early_game').lower()
        
        # Extract position data
        taric_position = (
            state.get('taric_state', {}).get('position_x', 0),
            state.get('taric_state', {}).get('position_y', 0)
        )
        
        # In a real implementation, we would have camera position
        # Here we use champion position as a proxy
        camera_positions.append({
            'position': taric_position,
            'timestamp': timestamp,
            'phase': game_phase,
            'in_combat': len(state.get('nearby_units', {}).get('enemies', [])) > 0,
            'is_moving': bool(action.get('movement'))
        })
        
        # Detect potential map view events (simplified)
        if idx > 0:
            prev_pos = camera_positions[idx-1]['position']
            curr_pos = taric_position
            
            # Calculate distance moved
            distance = math.sqrt(
                (curr_pos[0] - prev_pos[0])**2 + 
                (curr_pos[1] - prev_pos[1])**2
            )
            
            # Large, sudden jumps might indicate minimap usage or camera hotkeys
            if distance > 2000 and not camera_positions[idx-1]['in_combat']:
                map_view_events.append({
                    'timestamp': timestamp,
                    'from_position': prev_pos,
                    'to_position': curr_pos,
                    'distance': distance
                })
                
                # Track camera hotkey usage (F-keys or minimap clicks)
                metrics['camera_hotkey_usage'] += 1
            
            # Track camera movement smoothness
            if idx > 1:
                prev_distance = math.sqrt(
                    (prev_pos[0] - camera_positions[idx-2]['position'][0])**2 + 
                    (prev_pos[1] - camera_positions[idx-2]['position'][1])**2
                )
                
                # Analyze movement pattern
                if abs(distance - prev_distance) < 100:
                    smooth_movements += 1
                else:
                    jerky_movements += 1
    
    # Calculate camera movement frequency
    if len(camera_positions) > 1:
        total_game_time = camera_positions[-1]['timestamp']
        position_changes = sum(
            1 for i in range(1, len(camera_positions))
            if camera_positions[i]['position'] != camera_positions[i-1]['position']
        )
        
        if total_game_time > 0:
            metrics['camera_movement_frequency'] = position_changes / (total_game_time / 60)
            metrics['camera_position_changes'] = position_changes
    
    # Estimate camera pattern (locked/unlocked)
    total_positions = len(camera_positions)
    if total_positions > 0:
        # Count how often position changes during movement
        positions_while_moving = sum(1 for pos in camera_positions if pos['is_moving'])
        position_changes_while_moving = sum(
            1 for i in range(1, len(camera_positions))
            if camera_positions[i]['is_moving'] and 
            camera_positions[i]['position'] != camera_positions[i-1]['position']
        )
        
        if positions_while_moving > 0:
            change_ratio = position_changes_while_moving / positions_while_moving
            
            # Determine camera mode based on change ratio
            if change_ratio > 0.9:
                metrics['camera_patterns']['unlocked'] = 1
            elif change_ratio < 0.3:
                metrics['camera_patterns']['locked'] = 1
            else:
                metrics['camera_patterns']['mixed'] = 1
    
    # Calculate camera movement by phase
    phase_movements = {'early_game': 0, 'mid_game': 0, 'late_game': 0}
    phase_counts = {'early_game': 0, 'mid_game': 0, 'late_game': 0}
    
    for i in range(1, len(camera_positions)):
        phase = camera_positions[i]['phase']
        if camera_positions[i]['position'] != camera_positions[i-1]['position']:
            if phase in phase_movements:
                phase_movements[phase] += 1
        if phase in phase_counts:
            phase_counts[phase] += 1
    
    # Calculate camera movement rate by phase
    for phase in phase_movements:
        if phase_counts[phase] > 0:
            metrics['camera_movement_by_phase'][phase] = phase_movements[phase] / phase_counts[phase]
    
    # Calculate camera control during combat
    combat_camera_moves = sum(
        1 for i in range(1, len(camera_positions))
        if camera_positions[i]['in_combat'] and 
        camera_positions[i]['position'] != camera_positions[i-1]['position']
    )
    combat_frames = sum(1 for pos in camera_positions if pos['in_combat'])
    
    if combat_frames > 0:
        metrics['camera_control_during_combat'] = combat_camera_moves / combat_frames
    
    # Calculate camera control during movement
    if positions_while_moving > 0:
        metrics['camera_control_during_movement'] = position_changes_while_moving / positions_while_moving
    
    # Calculate minimap view frequency
    if total_game_time > 0:
        metrics['minimap_view_frequency'] = len(map_view_events) / (total_game_time / 60)
    
    # Calculate camera movement before objectives
    # (Would need to correlate with objective spawn times)
    metrics['camera_movement_before_objectives'] = 0.5  # Placeholder
    
    # Calculate camera efficiency
    # (How well camera movements cover important areas)
    metrics['camera_efficiency'] = 0.7  # Placeholder
    
    # Calculate camera control smoothness
    if smooth_movements + jerky_movements > 0:
        metrics['camera_control_smoothness'] = smooth_movements / (smooth_movements + jerky_movements)
    
    # Calculate focus areas
    # Simple approximation based on positions
    metrics['camera_focus_areas']['self_centered'] = 0.6  # Most players focus on themselves
    metrics['camera_focus_areas']['lane_centered'] = 0.3  # Some focus on lane
    metrics['camera_focus_areas']['map_awareness'] = 0.1  # Small portion on map awareness
    
    return metrics

def calculate_mechanics_metrics(state_action_pairs, match_data=None):
    """
    Calculate combined mechanical metrics from state-action pairs.
    
    Args:
        state_action_pairs (list): List of state-action pairs
        match_data (dict): Match-level data for context
        
    Returns:
        dict: Dictionary of mechanics metrics
    """
    # Ensure proper types
    if not isinstance(state_action_pairs, list):
        state_action_pairs = []
        
    if match_data is None:
        match_data = {}
    elif not isinstance(match_data, dict):
        match_data = {}
    
    # Calculate individual metrics with proper error handling
    try:
        ability_sequence = calculate_ability_sequence_metrics(state_action_pairs, match_data)
    except Exception as e:
        print(f"Error calculating ability sequence metrics: {str(e)}")
        ability_sequence = {}
        
    try:
        target_selection = calculate_target_selection_metrics(state_action_pairs, match_data)
    except Exception as e:
        print(f"Error calculating target selection metrics: {str(e)}")
        target_selection = {}
        
    try:
        apm = calculate_apm_metrics(state_action_pairs, match_data)
    except Exception as e:
        print(f"Error calculating APM metrics: {str(e)}")
        apm = {}
        
    try:
        interaction_timing = calculate_interaction_timing_metrics(state_action_pairs, match_data)
    except Exception as e:
        print(f"Error calculating interaction timing metrics: {str(e)}")
        interaction_timing = {}
        
    try:
        item_ability = calculate_item_ability_metrics(state_action_pairs, match_data)
    except Exception as e:
        print(f"Error calculating item ability metrics: {str(e)}")
        item_ability = {}
        
    try:
        mouse_click_patterns = calculate_mouse_click_metrics(state_action_pairs, match_data)
    except Exception as e:
        print(f"Error calculating mouse click metrics: {str(e)}")
        mouse_click_patterns = {}
        
    try:
        auto_attack_reset = calculate_auto_attack_reset_metrics(state_action_pairs, match_data)
    except Exception as e:
        print(f"Error calculating auto attack reset metrics: {str(e)}")
        auto_attack_reset = {}
        
    try:
        camera_control = calculate_camera_control_metrics(state_action_pairs, match_data)
    except Exception as e:
        print(f"Error calculating camera control metrics: {str(e)}")
        camera_control = {}
    
    # Combine all metrics
    mechanics_metrics = {}
    
    # Add metrics from each category, ensuring they're dictionaries
    if isinstance(ability_sequence, dict):
        mechanics_metrics.update(ability_sequence)
    
    if isinstance(target_selection, dict):
        mechanics_metrics.update(target_selection)
    
    if isinstance(apm, dict):
        mechanics_metrics.update(apm)
    
    if isinstance(interaction_timing, dict):
        mechanics_metrics.update(interaction_timing)
    
    if isinstance(item_ability, dict):
        mechanics_metrics.update(item_ability)
    
    if isinstance(mouse_click_patterns, dict):
        mechanics_metrics.update(mouse_click_patterns)
    
    if isinstance(auto_attack_reset, dict):
        mechanics_metrics.update(auto_attack_reset)
    
    if isinstance(camera_control, dict):
        mechanics_metrics.update(camera_control)
    
    return mechanics_metrics 