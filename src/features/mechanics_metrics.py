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
        state = pair['state']
        action = pair.get('action', {})
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
            seq = tuple(ability_sequence[i:i+3])
            unique_sequences.add(seq)
        
        # Normalize by total possible sequences
        sequence_complexity = len(unique_sequences) / (len(ability_sequence) - 2) if len(ability_sequence) > 2 else 0
        metrics['ability_sequence_complexity'] = sequence_complexity
    
    # Calculate timing consistency
    # Lower time gaps between abilities indicates better mechanics
    if len(ability_timing) >= 2:
        time_gaps = [ability_timing[i+1] - ability_timing[i] for i in range(len(ability_timing) - 1)]
        avg_gap = sum(time_gaps) / len(time_gaps)
        gap_variance = sum((gap - avg_gap) ** 2 for gap in time_gaps) / len(time_gaps)
        
        # Lower variance means more consistent timing
        metrics['ability_timing_consistency'] = 1 / (1 + gap_variance)
    
    # Special sequences for Taric
    q_aa_combos = 0
    e_w_combos = 0
    
    # Count special Taric combos
    for i in range(len(ability_sequence) - 1):
        # Q -> AA combo (Q ability to reset auto attack)
        if ability_sequence[i] == 'Q' and ability_sequence[i+1] == 'AUTO':
            q_aa_combos += 1
        
        # E -> W combo (using W link to extend stun range)
        if ability_sequence[i] == 'W' and ability_sequence[i+1] == 'E':
            e_w_combos += 1
    
    # Calculate combo efficiency
    if total_actions > 0:
        # Higher values indicate better combo usage
        metrics['ability_combo_efficiency'] = (q_aa_combos + e_w_combos) / (total_actions / 2)
    
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
        state = pair['state']
        action = pair.get('action', {})
        ability = action.get('ability')
        
        # Process targeting information
        target = action.get('target')
        targets = action.get('targets', [])
        
        # Single target abilities (W)
        if target and ability in ['W']:
            target_id = target.get('id', 'unknown')
            
            # Add to overall targets
            all_targets.append(target_id)
            
            # Add to ability-specific targets
            ability_targets[ability].append(target_id)
            
            # Count as defensive targeting (W is always on allies)
            defensive_targets += 1
            
            # Update target distribution
            if target_id not in metrics['target_selection_distribution']:
                metrics['target_selection_distribution'][target_id] = 0
            metrics['target_selection_distribution'][target_id] += 1
            
            # Update ability-specific distribution
            if target_id not in metrics['target_selection_by_ability'][ability]:
                metrics['target_selection_by_ability'][ability][target_id] = 0
            metrics['target_selection_by_ability'][ability][target_id] += 1
        
        # Multi-target abilities (Q, E, R)
        elif targets and ability in ['Q', 'E', 'R']:
            for target in targets:
                target_id = target.get('id', 'unknown')
                
                # Add to overall targets
                all_targets.append(target_id)
                
                # Add to ability-specific targets
                ability_targets[ability].append(target_id)
                
                # Count as defensive or offensive
                if ability == 'Q' or ability == 'R':
                    defensive_targets += 1
                elif ability == 'E':
                    offensive_targets += 1
                
                # Update target distribution
                if target_id not in metrics['target_selection_distribution']:
                    metrics['target_selection_distribution'][target_id] = 0
                metrics['target_selection_distribution'][target_id] += 1
                
                # Update ability-specific distribution
                if target_id not in metrics['target_selection_by_ability'][ability]:
                    metrics['target_selection_by_ability'][ability][target_id] = 0
                metrics['target_selection_by_ability'][ability][target_id] += 1
    
    # Calculate target switching frequency
    if len(all_targets) >= 2:
        switches = sum(1 for i in range(len(all_targets) - 1) if all_targets[i] != all_targets[i+1])
        metrics['target_switching_frequency'] = switches / (len(all_targets) - 1)
    
    # Calculate offensive/defensive targeting percentages
    total_targeted_actions = defensive_targets + offensive_targets
    if total_targeted_actions > 0:
        metrics['defensive_targeting_percentage'] = defensive_targets / total_targeted_actions
        metrics['offensive_targeting_percentage'] = offensive_targets / total_targeted_actions
    
    # Calculate priority target focus
    # (how consistently high-value targets are focused)
    if metrics['target_selection_distribution']:
        # Get most targeted entities
        sorted_targets = sorted(metrics['target_selection_distribution'].items(), key=lambda x: x[1], reverse=True)
        if sorted_targets:
            # What percentage of actions were on the top 2 targets?
            top_targets_count = sum(count for _, count in sorted_targets[:2])
            top_targets_percentage = top_targets_count / len(all_targets) if all_targets else 0
            metrics['priority_target_focus'] = top_targets_percentage
    
    return metrics


def calculate_apm_metrics(state_action_pairs, match_data=None):
    """
    Calculate metrics related to Actions Per Minute (APM) and input patterns.
    
    Args:
        state_action_pairs (list): List of state-action pairs
        match_data (dict): Match-level data for context
        
    Returns:
        dict: Dictionary of APM metrics
    """
    metrics = {
        'actions_per_minute': 0,
        'apm_by_phase': {
            'early_game': 0,
            'mid_game': 0,
            'late_game': 0
        },
        'apm_variance': 0,
        'combat_apm': 0,
        'non_combat_apm': 0,
        'peak_apm': 0,
        'mouse_movement_efficiency': 0
    }
    
    # Cannot directly measure mouse movements from state-action pairs
    # but we can approximate APM and other metrics
    
    total_game_time = 0
    if state_action_pairs:
        total_game_time = state_action_pairs[-1]['state']['game_time_seconds']
    
    # Count actions by phase and by minute
    action_count = 0
    actions_by_phase = {
        'early_game': 0,
        'mid_game': 0,
        'late_game': 0
    }
    actions_by_minute = defaultdict(int)
    combat_actions = 0
    non_combat_actions = 0
    
    for pair in state_action_pairs:
        state = pair['state']
        action = pair.get('action', {})
        game_phase = state.get('game_phase', 'EARLY_GAME').lower()
        timestamp = state.get('game_time_seconds', 0)
        minute = int(timestamp / 60)
        
        if action.get('ability') or action.get('item_used') or action.get('movement'):
            action_count += 1
            
            # Count by phase
            if game_phase in actions_by_phase:
                actions_by_phase[game_phase] += 1
            
            # Count by minute
            actions_by_minute[minute] += 1
            
            # Count combat vs non-combat
            is_combat = False
            if action.get('ability') in ['Q', 'W', 'E', 'R', 'AUTO']:
                nearby_enemies = len(state.get('nearby_units', {}).get('enemies', []))
                if nearby_enemies > 0:
                    is_combat = True
            
            if is_combat:
                combat_actions += 1
            else:
                non_combat_actions += 1
    
    # Calculate overall APM
    if total_game_time > 0:
        total_minutes = total_game_time / 60
        metrics['actions_per_minute'] = action_count / total_minutes if total_minutes > 0 else 0
    
    # Calculate APM by phase
    phase_durations = {
        'early_game': 0,
        'mid_game': 0,
        'late_game': 0
    }
    
    for pair in state_action_pairs:
        state = pair['state']
        game_phase = state.get('game_phase', 'EARLY_GAME').lower()
        if game_phase in phase_durations:
            phase_durations[game_phase] += 1
    
    for phase in metrics['apm_by_phase']:
        if phase_durations[phase] > 0:
            phase_minutes = phase_durations[phase] / 60  # Convert from seconds to minutes
            metrics['apm_by_phase'][phase] = actions_by_phase[phase] / phase_minutes if phase_minutes > 0 else 0
    
    # Calculate APM variance
    if actions_by_minute:
        apm_values = list(actions_by_minute.values())
        avg_apm = sum(apm_values) / len(apm_values)
        apm_variance = sum((apm - avg_apm) ** 2 for apm in apm_values) / len(apm_values)
        metrics['apm_variance'] = apm_variance
        metrics['peak_apm'] = max(apm_values)
    
    # Calculate combat vs non-combat APM
    if total_game_time > 0:
        total_minutes = total_game_time / 60
        metrics['combat_apm'] = combat_actions / total_minutes if total_minutes > 0 else 0
        metrics['non_combat_apm'] = non_combat_actions / total_minutes if total_minutes > 0 else 0
    
    # Mouse movement efficiency can't be directly calculated without more detailed data
    # This is a placeholder for future implementation when more data is available
    metrics['mouse_movement_efficiency'] = 0.75  # Placeholder value
    
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
        'item_usage_out_of_combat': defaultdict(int)
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
        'CORRUPTING_POTION'           # Healing + damage
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
        
        # Track ability casts
        if 'ability' in action:
            ability = action['ability']
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
    Calculate metrics related to mouse click patterns (right-click vs left-click)
    and click position analysis.
    
    Args:
        state_action_pairs (list): List of state-action pairs
        match_data (dict): Match-level data for context
        
    Returns:
        dict: Dictionary of mouse click pattern metrics
    """
    metrics = {
        'click_counts': {
            'right_click': 0,
            'left_click': 0,
            'ability_click': 0,
            'item_click': 0
        },
        'click_ratios': {
            'right_to_left_ratio': 0,
            'ability_to_movement_ratio': 0
        },
        'click_patterns_by_phase': {
            'early_game': {
                'right_click': 0,
                'left_click': 0,
                'ability_click': 0,
                'item_click': 0
            },
            'mid_game': {
                'right_click': 0,
                'left_click': 0,
                'ability_click': 0,
                'item_click': 0
            },
            'late_game': {
                'right_click': 0,
                'left_click': 0,
                'ability_click': 0,
                'item_click': 0
            }
        },
        'click_patterns_by_context': {
            'in_combat': {
                'right_click': 0,
                'left_click': 0,
                'ability_click': 0,
                'item_click': 0
            },
            'out_of_combat': {
                'right_click': 0,
                'left_click': 0,
                'ability_click': 0,
                'item_click': 0
            },
            'near_objective': {
                'right_click': 0,
                'left_click': 0,
                'ability_click': 0,
                'item_click': 0
            }
        },
        'click_sequence_patterns': [],
        'click_frequency': {
            'clicks_per_minute': 0,
            'right_clicks_per_minute': 0,
            'left_clicks_per_minute': 0
        },
        'click_spatial_distribution': {
            'self_centered': 0,
            'target_centered': 0,
            'exploratory': 0
        },
        'click_timing_metrics': {
            'average_time_between_clicks': 0,
            'click_burst_frequency': 0
        },
        'click_efficiency': 0,
        # New positional metrics
        'click_positions': {
            'right_click_positions': [],  # List of (x,y) coordinates
            'left_click_positions': [],   # List of (x,y) coordinates
            'ability_click_positions': [], # List of (x,y) coordinates
            'item_click_positions': []    # List of (x,y) coordinates
        },
        'click_position_metrics': {
            'position_variance_x': 0,      # How spread out clicks are horizontally
            'position_variance_y': 0,      # How spread out clicks are vertically
            'click_position_entropy': 0,   # Measure of randomness in click positions
            'consecutive_click_distance_avg': 0, # Average distance between consecutive clicks
            'click_clusters': [],          # Centers of click clusters
            'distance_from_champion_avg': 0, # Average distance from champion
            'map_coverage_percentage': 0,   # Percentage of map covered by clicks
            'position_heatmap': {}         # Grid-based heatmap of click density
        }
    }
    
    # Counters for click analysis
    click_timestamps = []
    click_types = []
    right_clicks = 0
    left_clicks = 0
    ability_clicks = 0
    item_clicks = 0
    
    # New position tracking
    all_click_positions = []
    right_click_positions = []
    left_click_positions = []
    ability_click_positions = []
    item_click_positions = []
    
    # Phase-specific counters
    phase_clicks = {
        'early_game': {'right_click': 0, 'left_click': 0, 'ability_click': 0, 'item_click': 0},
        'mid_game': {'right_click': 0, 'left_click': 0, 'ability_click': 0, 'item_click': 0},
        'late_game': {'right_click': 0, 'left_click': 0, 'ability_click': 0, 'item_click': 0}
    }
    
    # Context-specific counters
    context_clicks = {
        'in_combat': {'right_click': 0, 'left_click': 0, 'ability_click': 0, 'item_click': 0},
        'out_of_combat': {'right_click': 0, 'left_click': 0, 'ability_click': 0, 'item_click': 0},
        'near_objective': {'right_click': 0, 'left_click': 0, 'ability_click': 0, 'item_click': 0}
    }
    
    total_game_time = 0
    if state_action_pairs:
        total_game_time = state_action_pairs[-1]['state']['game_time_seconds']
    
    # Process all state-action pairs
    for pair in state_action_pairs:
        state = pair['state']
        action = pair.get('action', {})
        game_phase = state.get('game_phase', 'early_game').lower()
        timestamp = state.get('game_time_seconds', 0)
        
        # Determine context
        nearby_enemies = state.get('nearby_units', {}).get('enemies', [])
        in_combat = len(nearby_enemies) > 0
        context = 'in_combat' if in_combat else 'out_of_combat'
        
        # Get Taric's position
        taric_position = (
            state.get('taric_state', {}).get('position_x', 0),
            state.get('taric_state', {}).get('position_y', 0)
        )
        
        # Check for objective proximity (simplified approach)
        near_objective = False
        objective_positions = [
            (9500, 4000),  # Dragon position
            (5500, 10000)  # Baron position
        ]
        
        for obj_pos in objective_positions:
            distance = math.sqrt(
                (taric_position[0] - obj_pos[0])**2 + 
                (taric_position[1] - obj_pos[1])**2
            )
            if distance < 2000:  # If within 2000 units of an objective
                near_objective = True
                break
        
        if near_objective:
            context = 'near_objective'
        
        # Track different click types
        
        # Movement actions (right clicks)
        if action.get('movement'):
            # Get click position for movement
            click_position = None
            if 'target_position' in action:
                click_position = (
                    action['target_position'].get('x', 0),
                    action['target_position'].get('y', 0)
                )
            elif 'destination' in action:
                click_position = (
                    action['destination'].get('x', 0),
                    action['destination'].get('y', 0)
                )
            
            if click_position:
                all_click_positions.append({
                    'position': click_position,
                    'type': 'right_click',
                    'timestamp': timestamp,
                    'distance_from_champion': math.sqrt(
                        (click_position[0] - taric_position[0])**2 +
                        (click_position[1] - taric_position[1])**2
                    )
                })
                
                right_click_positions.append(click_position)
            
            right_clicks += 1
            click_timestamps.append(timestamp)
            click_types.append('right_click')
            
            # Update phase metrics
            if game_phase in phase_clicks:
                phase_clicks[game_phase]['right_click'] += 1
            
            # Update context metrics
            context_clicks[context]['right_click'] += 1
        
        # Ability usage (typically associated with left clicks/keyboard)
        if action.get('ability'):
            # Get click position for ability
            click_position = None
            
            if 'target_position' in action:
                click_position = (
                    action['target_position'].get('x', 0),
                    action['target_position'].get('y', 0)
                )
            elif action.get('targets'):
                # Use first target's position
                if action['targets'] and 'position' in action['targets'][0]:
                    click_position = (
                        action['targets'][0]['position'].get('x', 0),
                        action['targets'][0]['position'].get('y', 0)
                    )
            elif action.get('target') and 'position' in action.get('target', {}):
                click_position = (
                    action['target']['position'].get('x', 0),
                    action['target']['position'].get('y', 0)
                )
            
            if click_position:
                all_click_positions.append({
                    'position': click_position,
                    'type': 'ability_click',
                    'ability': action.get('ability'),
                    'timestamp': timestamp,
                    'distance_from_champion': math.sqrt(
                        (click_position[0] - taric_position[0])**2 +
                        (click_position[1] - taric_position[1])**2
                    )
                })
                
                ability_click_positions.append(click_position)
            
            ability_clicks += 1
            click_timestamps.append(timestamp)
            click_types.append('ability_click')
            
            # Update phase metrics
            if game_phase in phase_clicks:
                phase_clicks[game_phase]['ability_click'] += 1
            
            # Update context metrics
            context_clicks[context]['ability_click'] += 1
            
            # Targeting enemies with abilities typically requires left-clicks
            if action.get('targets') or action.get('target'):
                left_clicks += 1
                
                # Update phase metrics
                if game_phase in phase_clicks:
                    phase_clicks[game_phase]['left_click'] += 1
                
                # Update context metrics
                context_clicks[context]['left_click'] += 1
                
                if click_position:
                    left_click_positions.append(click_position)
        
        # Item usage (typically associated with left clicks)
        if action.get('item_used'):
            # Get click position for item
            click_position = None
            
            if 'target_position' in action:
                click_position = (
                    action['target_position'].get('x', 0),
                    action['target_position'].get('y', 0)
                )
            elif action.get('target') and 'position' in action.get('target', {}):
                click_position = (
                    action['target']['position'].get('x', 0),
                    action['target']['position'].get('y', 0)
                )
            
            if click_position:
                all_click_positions.append({
                    'position': click_position,
                    'type': 'item_click',
                    'item': action.get('item_used'),
                    'timestamp': timestamp,
                    'distance_from_champion': math.sqrt(
                        (click_position[0] - taric_position[0])**2 +
                        (click_position[1] - taric_position[1])**2
                    )
                })
                
                item_click_positions.append(click_position)
            
            item_clicks += 1
            click_timestamps.append(timestamp)
            click_types.append('item_click')
            
            # Update phase metrics
            if game_phase in phase_clicks:
                phase_clicks[game_phase]['item_click'] += 1
            
            # Update context metrics
            context_clicks[context]['item_click'] += 1
            
            # Items with active effects typically require left-clicks
            left_clicks += 1
            
            # Update phase metrics
            if game_phase in phase_clicks:
                phase_clicks[game_phase]['left_click'] += 1
            
            # Update context metrics
            context_clicks[context]['left_click'] += 1
            
            if click_position and click_position not in left_click_positions:
                left_click_positions.append(click_position)
    
    # Update click counts
    metrics['click_counts']['right_click'] = right_clicks
    metrics['click_counts']['left_click'] = left_clicks
    metrics['click_counts']['ability_click'] = ability_clicks
    metrics['click_counts']['item_click'] = item_clicks
    
    # Update click ratios
    total_clicks = right_clicks + left_clicks
    if total_clicks > 0:
        metrics['click_ratios']['right_to_left_ratio'] = right_clicks / total_clicks
    
    total_action_clicks = ability_clicks + right_clicks
    if total_action_clicks > 0:
        metrics['click_ratios']['ability_to_movement_ratio'] = ability_clicks / total_action_clicks
    
    # Update phase-specific patterns
    for phase in phase_clicks:
        for click_type, count in phase_clicks[phase].items():
            metrics['click_patterns_by_phase'][phase][click_type] = count
    
    # Update context-specific patterns
    for context in context_clicks:
        for click_type, count in context_clicks[context].items():
            metrics['click_patterns_by_context'][context][click_type] = count
    
    # Calculate click frequency
    total_minutes = total_game_time / 60 if total_game_time > 0 else 1
    
    metrics['click_frequency']['clicks_per_minute'] = total_clicks / total_minutes
    metrics['click_frequency']['right_clicks_per_minute'] = right_clicks / total_minutes
    metrics['click_frequency']['left_clicks_per_minute'] = left_clicks / total_minutes
    
    # Calculate timing metrics
    if len(click_timestamps) >= 2:
        time_between_clicks = [
            click_timestamps[i+1] - click_timestamps[i]
            for i in range(len(click_timestamps) - 1)
        ]
        avg_time = sum(time_between_clicks) / len(time_between_clicks)
        metrics['click_timing_metrics']['average_time_between_clicks'] = avg_time
        
        # Count click bursts (clicks within 0.5 seconds of each other)
        burst_count = sum(1 for time in time_between_clicks if time < 0.5)
        metrics['click_timing_metrics']['click_burst_frequency'] = burst_count / len(time_between_clicks)
    
    # Calculate click sequence patterns
    if len(click_types) >= 3:
        sequence_counts = defaultdict(int)
        
        for i in range(len(click_types) - 2):
            seq = (click_types[i], click_types[i+1], click_types[i+2])
            sequence_counts[seq] += 1
        
        # Get most common sequences
        common_sequences = sorted(sequence_counts.items(), key=lambda x: x[1], reverse=True)
        metrics['click_sequence_patterns'] = [
            {'sequence': seq, 'count': count}
            for seq, count in common_sequences[:5]  # Top 5 sequences
        ]
    
    # Estimate spatial distribution (based on context)
    if total_clicks > 0:
        # Self-centered: clicks during abilities targeting self
        self_targeting = metrics['click_patterns_by_context']['out_of_combat']['ability_click']
        # Target-centered: clicks during combat
        target_targeting = metrics['click_patterns_by_context']['in_combat']['ability_click'] + metrics['click_patterns_by_context']['in_combat']['left_click']
        # Exploratory: movement clicks not in combat
        exploratory = metrics['click_patterns_by_context']['out_of_combat']['right_click']
        
        metrics['click_spatial_distribution']['self_centered'] = self_targeting / total_clicks
        metrics['click_spatial_distribution']['target_centered'] = target_targeting / total_clicks
        metrics['click_spatial_distribution']['exploratory'] = exploratory / total_clicks
    
    # Calculate click efficiency (ratio of effective actions to total clicks)
    effective_actions = ability_clicks + item_clicks
    if total_clicks > 0:
        metrics['click_efficiency'] = effective_actions / total_clicks
    
    # Store click positions in metrics
    metrics['click_positions']['right_click_positions'] = right_click_positions
    metrics['click_positions']['left_click_positions'] = left_click_positions
    metrics['click_positions']['ability_click_positions'] = ability_click_positions
    metrics['click_positions']['item_click_positions'] = item_click_positions
    
    # Calculate position-based metrics
    if all_click_positions:
        # Extract x and y coordinates for variance calculation
        x_coords = [pos['position'][0] for pos in all_click_positions]
        y_coords = [pos['position'][1] for pos in all_click_positions]
        
        # Calculate variance in x and y coordinates
        if x_coords:
            avg_x = sum(x_coords) / len(x_coords)
            metrics['click_position_metrics']['position_variance_x'] = sum((x - avg_x) ** 2 for x in x_coords) / len(x_coords)
        
        if y_coords:
            avg_y = sum(y_coords) / len(y_coords)
            metrics['click_position_metrics']['position_variance_y'] = sum((y - avg_y) ** 2 for y in y_coords) / len(y_coords)
        
        # Calculate average distance from champion
        champion_distances = [pos['distance_from_champion'] for pos in all_click_positions]
        metrics['click_position_metrics']['distance_from_champion_avg'] = sum(champion_distances) / len(champion_distances) if champion_distances else 0
        
        # Calculate consecutive click distances
        if len(all_click_positions) >= 2:
            consecutive_distances = []
            for i in range(len(all_click_positions) - 1):
                pos1 = all_click_positions[i]['position']
                pos2 = all_click_positions[i+1]['position']
                distance = math.sqrt((pos2[0] - pos1[0])**2 + (pos2[1] - pos1[1])**2)
                consecutive_distances.append(distance)
            
            if consecutive_distances:
                metrics['click_position_metrics']['consecutive_click_distance_avg'] = sum(consecutive_distances) / len(consecutive_distances)
        
        # Create a simplified heatmap using a grid
        # Divide the map into a 10x10 grid for analysis
        heatmap = defaultdict(int)
        map_width = 15000  # Approximate Summoner's Rift width
        map_height = 15000  # Approximate Summoner's Rift height
        grid_size = 10
        cell_width = map_width / grid_size
        cell_height = map_height / grid_size
        
        for pos in all_click_positions:
            x, y = pos['position']
            grid_x = min(grid_size - 1, max(0, int(x / cell_width)))
            grid_y = min(grid_size - 1, max(0, int(y / cell_height)))
            grid_key = f"{grid_x},{grid_y}"
            heatmap[grid_key] += 1
        
        metrics['click_position_metrics']['position_heatmap'] = dict(heatmap)
        
        # Calculate map coverage (percentage of grid cells with clicks)
        total_cells = grid_size * grid_size
        cells_with_clicks = len(heatmap)
        metrics['click_position_metrics']['map_coverage_percentage'] = cells_with_clicks / total_cells if total_cells > 0 else 0
        
        # Basic clustering to find hotspots
        # (In a real implementation, this would use K-means or DBSCAN for better clustering)
        if heatmap:
            # Find top 3 hotspots in the heatmap
            top_clusters = sorted(heatmap.items(), key=lambda x: x[1], reverse=True)[:3]
            for grid_key, count in top_clusters:
                grid_x, grid_y = map(int, grid_key.split(','))
                center_x = (grid_x + 0.5) * cell_width
                center_y = (grid_y + 0.5) * cell_height
                metrics['click_position_metrics']['click_clusters'].append({
                    'center': (center_x, center_y),
                    'count': count,
                    'percentage': count / len(all_click_positions) if all_click_positions else 0
                })
        
        # Calculate click position entropy (simplified version)
        # Higher entropy means more randomness/spread out clicks
        if heatmap:
            total_clicks = sum(heatmap.values())
            if total_clicks > 0:
                probabilities = [count / total_clicks for count in heatmap.values()]
                entropy = -sum(p * math.log(p) for p in probabilities if p > 0)
                metrics['click_position_metrics']['click_position_entropy'] = entropy
    
    return metrics

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
    ability_sequence = calculate_ability_sequence_metrics(state_action_pairs, match_data)
    target_selection = calculate_target_selection_metrics(state_action_pairs, match_data)
    apm = calculate_apm_metrics(state_action_pairs, match_data)
    interaction_timing = calculate_interaction_timing_metrics(state_action_pairs, match_data)
    item_ability = calculate_item_ability_metrics(state_action_pairs, match_data)
    mouse_click_patterns = calculate_mouse_click_metrics(state_action_pairs, match_data)
    auto_attack_reset = calculate_auto_attack_reset_metrics(state_action_pairs, match_data)
    camera_control = calculate_camera_control_metrics(state_action_pairs, match_data)
    
    # Combine all metrics
    mechanics_metrics = {
        **ability_sequence,
        **target_selection,
        **apm,
        **interaction_timing,
        **item_ability,
        **mouse_click_patterns,
        **auto_attack_reset,
        **camera_control
    }
    
    return mechanics_metrics 