"""
Combat metrics calculation for Taric Bot AI.

This module calculates advanced combat metrics from state-action pairs,
including healing efficiency, shielding effectiveness, and stun success rate.
"""

import numpy as np
from collections import defaultdict


def calculate_healing_metrics(state_action_pairs, match_data=None):
    """
    Calculate advanced healing metrics from state-action pairs.
    
    Args:
        state_action_pairs (list): List of state-action pairs
        match_data (dict): Match-level data for context
        
    Returns:
        dict: Dictionary of healing metrics
    """
    total_game_time = 0
    if state_action_pairs:
        # Get game time from the last state-action pair
        total_game_time = state_action_pairs[-1]['state']['game_time_seconds']
    
    # Initialize metrics
    metrics = {
        'total_healing': 0,
        'healing_per_minute': 0,
        'heal_uptime': 0,
        'max_multi_target_healing': 0,
        'healing_efficiency': 0,
        'healing_by_phase': {
            'early_game': 0,
            'mid_game': 0,
            'late_game': 0
        },
        'healing_by_target_priority': {
            'high_priority': 0,  # ADC, APC
            'medium_priority': 0,  # Jungle, Support
            'low_priority': 0  # Tank, Bruiser
        },
        'healing_to_priority_targets': 0,
        'total_healing_opportunities': 0,
        'healing_opportunities_taken': 0,
        'optimal_heal_timing_percent': 0,
        'heal_distribution_score': 0
    }
    
    q_cast_timestamps = []
    healing_events = []
    q_cooldown = 15  # Base Q cooldown in seconds
    
    # Role priority mapping (simplified)
    role_priority = {
        'ADC': 'high_priority',
        'APC': 'high_priority',
        'MID': 'high_priority',
        'JUNGLE': 'medium_priority',
        'SUPPORT': 'medium_priority',
        'TOP': 'low_priority'
    }
    
    # Champion class mapping (example mapping)
    champion_class = {}
    if match_data and 'teams' in match_data:
        for team in match_data.get('teams', []):
            for participant in team.get('participants', []):
                champion = participant.get('champion_name', '').lower()
                role = participant.get('role', '').upper()
                # Map the champion to its priority based on role
                champion_class[champion] = role_priority.get(role, 'medium_priority')
    
    # First pass: collect healing events and cooldowns
    for pair in state_action_pairs:
        state = pair['state']
        action = pair.get('action', {})
        
        # Track Q casts
        if action.get('ability') == 'Q':
            timestamp = state['game_time_seconds']
            q_cast_timestamps.append(timestamp)
            
            # Get number of targets healed
            targets = action.get('targets', [])
            heal_amount = action.get('heal_amount', 0)
            num_targets = len(targets) if isinstance(targets, list) else 1
            
            # Track target priority for this heal
            priority_healing = 0
            for target in targets:
                target_champion = target.get('champion', '').lower()
                target_priority = champion_class.get(target_champion, 'medium_priority')
                
                # Track healing by target priority
                if target_priority in metrics['healing_by_target_priority']:
                    target_heal = heal_amount / num_targets if num_targets > 0 else 0
                    metrics['healing_by_target_priority'][target_priority] += target_heal
                
                # Count as priority healing if high priority target
                if target_priority == 'high_priority':
                    priority_healing += heal_amount / num_targets if num_targets > 0 else 0
            
            healing_events.append({
                'timestamp': timestamp,
                'amount': heal_amount,
                'num_targets': num_targets,
                'game_phase': state['game_phase'],
                'targets': targets,
                'priority_healing': priority_healing
            })
            
            metrics['total_healing'] += heal_amount
            metrics['max_multi_target_healing'] = max(
                metrics['max_multi_target_healing'], 
                num_targets
            )
            
            # Track healing by game phase
            game_phase = state['game_phase'].lower()
            if game_phase in metrics['healing_by_phase']:
                metrics['healing_by_phase'][game_phase] += heal_amount
            
            # Add priority healing
            metrics['healing_to_priority_targets'] += priority_healing
        
        # Track healing opportunities (when allies are low health)
        nearby_allies = state.get('nearby_units', {}).get('allies', [])
        low_health_allies = []
        for ally in nearby_allies:
            if ally.get('health_percent', 1.0) < 0.6 and ally.get('is_in_q_range', False):
                low_health_allies.append({
                    'champion': ally.get('champion', ''),
                    'health_percent': ally.get('health_percent', 1.0),
                    'priority': champion_class.get(ally.get('champion', '').lower(), 'medium_priority')
                })
        
        # If there are low health allies, count as a healing opportunity
        if low_health_allies:
            metrics['total_healing_opportunities'] += 1
            
            # Check if Q was used in this opportunity
            current_time = state['game_time_seconds']
            recent_cast = any(abs(current_time - t) < 2.0 for t in q_cast_timestamps)
            
            # Check if this was a high value opportunity (low health high priority target)
            high_value_opportunity = any(
                ally['health_percent'] < 0.4 and ally['priority'] == 'high_priority' 
                for ally in low_health_allies
            )
            
            if recent_cast:
                metrics['healing_opportunities_taken'] += 1
                
                # If this was a high value opportunity and we took it, count as optimal timing
                if high_value_opportunity:
                    metrics['optimal_heal_timing_percent'] += 1
    
    # Calculate heal uptime (improved version)
    if total_game_time > 0:
        # Calculate active healing windows based on Q cooldown
        active_healing_windows = []
        
        # Calculate ability haste from item build if available
        ability_haste = 0
        if match_data and 'player_stats' in match_data:
            ability_haste = match_data.get('player_stats', {}).get('ability_haste', 0)
        
        # Adjust Q cooldown based on ability haste if available
        if ability_haste > 0:
            q_cooldown = q_cooldown * (100 / (100 + ability_haste))
        
        for timestamp in q_cast_timestamps:
            # Q healing lasts ~3 seconds
            healing_window = (timestamp, timestamp + 3)
            active_healing_windows.append(healing_window)
        
        # Merge overlapping windows
        if active_healing_windows:
            active_healing_windows.sort()
            merged_windows = [active_healing_windows[0]]
            
            for window in active_healing_windows[1:]:
                prev_start, prev_end = merged_windows[-1]
                curr_start, curr_end = window
                
                if curr_start <= prev_end:
                    # Windows overlap, merge them
                    merged_windows[-1] = (prev_start, max(prev_end, curr_end))
                else:
                    # No overlap, add new window
                    merged_windows.append(window)
            
            # Calculate total active healing time
            active_healing_time = sum(end - start for start, end in merged_windows)
            metrics['heal_uptime'] = min(1.0, active_healing_time / total_game_time)
        
        # Calculate healing per minute
        metrics['healing_per_minute'] = metrics['total_healing'] / (total_game_time / 60)
    
    # Calculate healing efficiency
    if metrics['total_healing_opportunities'] > 0:
        metrics['healing_efficiency'] = metrics['healing_opportunities_taken'] / metrics['total_healing_opportunities']
        
        # Normalize optimal timing percentage
        if metrics['healing_opportunities_taken'] > 0:
            metrics['optimal_heal_timing_percent'] = metrics['optimal_heal_timing_percent'] / metrics['healing_opportunities_taken']
    
    # Calculate heal distribution score (how well healing is distributed across priorities)
    total_priority_healing = sum(metrics['healing_by_target_priority'].values())
    if total_priority_healing > 0:
        # Ideal distribution might be 60% high, 30% medium, 10% low priority
        ideal_distribution = {'high_priority': 0.6, 'medium_priority': 0.3, 'low_priority': 0.1}
        actual_distribution = {
            k: v / total_priority_healing 
            for k, v in metrics['healing_by_target_priority'].items()
        }
        
        # Calculate distribution score (1.0 = perfect match to ideal distribution)
        distribution_diff = sum(
            abs(ideal_distribution.get(k, 0) - actual_distribution.get(k, 0))
            for k in set(ideal_distribution) | set(actual_distribution)
        )
        
        # Convert to a 0-1 score (lower difference = higher score)
        metrics['heal_distribution_score'] = max(0, 1 - (distribution_diff / 2))
    
    return metrics


def calculate_shield_metrics(state_action_pairs, match_data=None):
    """
    Calculate advanced shielding metrics from state-action pairs.
    
    Args:
        state_action_pairs (list): List of state-action pairs
        match_data (dict): Match-level data for context
        
    Returns:
        dict: Dictionary of shielding metrics
    """
    total_game_time = 0
    if state_action_pairs:
        # Get game time from the last state-action pair
        total_game_time = state_action_pairs[-1]['state']['game_time_seconds']
    
    # Initialize metrics
    metrics = {
        'total_shielding': 0,
        'shield_uptime': 0,
        'shield_damage_prevented': 0,
        'shield_efficiency': 0,
        'shield_target_distribution': {},
        'w_link_uptime': 0,
        'optimal_w_timing': 0,
        'w_link_efficiency': 0,
        'w_link_target_switching': 0,
        'w_empowerment_usage': 0
    }
    
    # Initialize r_shields list
    r_shields = []
    
    # Track W casts and active periods
    w_cast_timestamps = []
    w_active_periods = []
    w_cooldown = 15  # Base W cooldown in seconds
    linked_ally_id = None
    link_start_time = None
    total_link_time = 0
    link_switches = 0
    previous_linked_ally = None
    w_e_combo_count = 0
    
    # Role priority mapping (simplified)
    role_priority = {
        'ADC': 'high_priority',
        'APC': 'high_priority',
        'MID': 'high_priority',
        'JUNGLE': 'medium_priority',
        'SUPPORT': 'medium_priority',
        'TOP': 'low_priority'
    }
    
    # Champion class mapping
    champion_class = {}
    if match_data and 'teams' in match_data:
        for team in match_data.get('teams', []):
            for participant in team.get('participants', []):
                champion = participant.get('champion_name', '').lower()
                role = participant.get('role', '').upper()
                # Map the champion to its priority based on role
                champion_class[champion] = role_priority.get(role, 'medium_priority')
    
    # First pass: gather attack data to determine high threat periods
    threat_periods = []
    for pair in state_action_pairs:
        state = pair['state']
        timestamp = state['game_time_seconds']
        
        # Check for enemy attacks
        nearby_enemies = state.get('nearby_units', {}).get('enemies', [])
        attacking_enemies = sum(1 for enemy in nearby_enemies if enemy.get('is_attacking', False))
        
        if attacking_enemies >= 2:
            # Consider this a high threat period
            threat_periods.append((timestamp, timestamp + 3))  # 3-second threat window
    
    # Merge overlapping threat periods
    if threat_periods:
        threat_periods.sort()
        merged_threats = [threat_periods[0]]
        
        for period in threat_periods[1:]:
            prev_start, prev_end = merged_threats[-1]
            curr_start, curr_end = period
            
            if curr_start <= prev_end:
                # Periods overlap, merge them
                merged_threats[-1] = (prev_start, max(prev_end, curr_end))
            else:
                # No overlap, add new period
                merged_threats.append(period)
        
        threat_periods = merged_threats
    
    # Second pass: process shield data and link information
    for i, pair in enumerate(state_action_pairs):
        state = pair['state']
        action = pair.get('action', {})
        timestamp = state['game_time_seconds']
        
        # Track W casts
        if action.get('ability') == 'W':
            w_cast_timestamps.append(timestamp)
            shield_amount = action.get('shield_amount', 0)
            metrics['total_shielding'] += shield_amount
            
            # Get target info
            target = action.get('target', None)
            if target:
                target_id = target.get('id', 'unknown')
                if target_id not in metrics['shield_target_distribution']:
                    metrics['shield_target_distribution'][target_id] = 0
                metrics['shield_target_distribution'][target_id] += 1
                
                # Track link changes
                new_linked_ally = target_id
                if linked_ally_id is None:
                    # First link
                    linked_ally_id = new_linked_ally
                    link_start_time = timestamp
                elif linked_ally_id != new_linked_ally:
                    # Link target changed - track switching
                    link_switches += 1
                    
                    if link_start_time is not None:
                        total_link_time += (timestamp - link_start_time)
                    linked_ally_id = new_linked_ally
                    link_start_time = timestamp
                
                # Check if this was during a high threat period (optimal timing)
                is_during_threat = any(start <= timestamp <= end for start, end in threat_periods)
                if is_during_threat:
                    metrics['optimal_w_timing'] += 1
        
        # Track R casts
        if action.get('ability') == 'R':
            targets = action.get('targets', [])
            
            # Cosmic Radiance lasts 2.5 seconds and has a brief delay
            ult_start = timestamp + 2.5  # Accounting for the delay
            ult_end = ult_start + 2.5
            
            r_shields.append({
                'start_time': ult_start,
                'end_time': ult_end,
                'targets': targets
            })
        
        # Check for W-E combo
        if action.get('ability') == 'E' and action.get('used_w_link', False):
            w_e_combo_count += 1
        
        # Check if link is active
        taric_state = state.get('taric_state', {})
        has_link = taric_state.get('has_link', False)
        if not has_link and linked_ally_id is not None:
            # Link ended
            if link_start_time is not None:
                total_link_time += (timestamp - link_start_time)
            linked_ally_id = None
            link_start_time = None
    
    # Calculate final link time if still active at end
    if linked_ally_id is not None and link_start_time is not None and total_game_time > 0:
        total_link_time += (total_game_time - link_start_time)
    
    # Calculate shield uptime and W efficiency
    if total_game_time > 0:
        # Calculate shield uptime based on W duration
        # W shield lasts ~2.5 seconds
        active_shield_time = len(w_cast_timestamps) * 2.5
        metrics['shield_uptime'] = min(1.0, active_shield_time / total_game_time)
        
        # Calculate W link uptime
        metrics['w_link_uptime'] = min(1.0, total_link_time / total_game_time)
        
        # Calculate W link efficiency (how often it was used for an ability)
        if w_e_combo_count > 0 and len(w_cast_timestamps) > 0:
            metrics['w_empowerment_usage'] = w_e_combo_count / len(w_cast_timestamps)
        
        # Calculate W link target switching (normalized)
        if len(w_cast_timestamps) > 1:
            metrics['w_link_target_switching'] = link_switches / (len(w_cast_timestamps) - 1)
    
    # Calculate optimal W timing percentage
    if len(w_cast_timestamps) > 0:
        metrics['optimal_w_timing'] = metrics['optimal_w_timing'] / len(w_cast_timestamps)
    
    return metrics


def calculate_stun_metrics(state_action_pairs, match_data=None):
    """
    Calculate stun-related metrics from state-action pairs.
    
    Args:
        state_action_pairs (list): List of state-action pairs
        match_data (dict): Match-level data for context
        
    Returns:
        dict: Dictionary of stun metrics
    """
    # Initialize metrics
    metrics = {
        'total_stun_attempts': 0,
        'successful_stuns': 0,
        'stun_rate': 0,
        'multi_target_stuns': 0,
        'stun_target_distribution': {},
        'flash_e_combos': 0,
        'w_e_combos': 0,
        'longest_stun_chain': 0,
        'stun_uptime': 0
    }
    
    total_game_time = 0
    if state_action_pairs:
        total_game_time = state_action_pairs[-1]['state']['game_time_seconds']
    
    e_cast_timestamps = []
    stun_durations = []  # Track duration of each stun
    current_stun_chain = 0
    prev_stun_end = 0
    
    # Track flash-E combos
    last_flash_time = None
    
    for pair in state_action_pairs:
        state = pair['state']
        action = pair.get('action', {})
        timestamp = state['game_time_seconds']
        
        # Track Flash usage
        if action.get('ability') == 'SUMMONER1' and action.get('summoner_spell') == 'FLASH':
            last_flash_time = timestamp
        
        # Track E casts
        if action.get('ability') == 'E':
            e_cast_timestamps.append(timestamp)
            metrics['total_stun_attempts'] += 1
            
            # Check if this is a Flash-E combo
            if last_flash_time and (timestamp - last_flash_time) < 1.0:
                metrics['flash_e_combos'] += 1
                last_flash_time = None
            
            # Check if this is a W-E combo
            if action.get('used_w_link', False):
                metrics['w_e_combos'] += 1
            
            # Get stun targets
            targets = action.get('targets', [])
            num_targets = len(targets) if isinstance(targets, list) else (1 if targets else 0)
            
            # Count successful stuns
            stun_landed = action.get('stun_landed', False)
            if stun_landed:
                metrics['successful_stuns'] += 1
                
                # Track multi-target stuns
                if num_targets > 1:
                    metrics['multi_target_stuns'] += 1
                
                # Track stun duration (Taric's E stun is 1.6s at all ranks)
                stun_duration = 1.6
                stun_start = timestamp
                stun_end = timestamp + stun_duration
                stun_durations.append((stun_start, stun_end))
                
                # Track stun chains
                if stun_start <= prev_stun_end + 1:  # Allow 1s gap for chain
                    current_stun_chain += 1
                else:
                    current_stun_chain = 1
                
                metrics['longest_stun_chain'] = max(metrics['longest_stun_chain'], current_stun_chain)
                prev_stun_end = stun_end
                
                # Track stun target distribution
                for target in targets:
                    target_id = target.get('id', 'unknown')
                    if target_id not in metrics['stun_target_distribution']:
                        metrics['stun_target_distribution'][target_id] = 0
                    metrics['stun_target_distribution'][target_id] += 1
    
    # Calculate stun rate
    if metrics['total_stun_attempts'] > 0:
        metrics['stun_rate'] = metrics['successful_stuns'] / metrics['total_stun_attempts']
    
    # Calculate stun uptime
    if total_game_time > 0:
        # Calculate total time enemies were stunned
        stunned_time = sum(end - start for start, end in stun_durations)
        metrics['stun_uptime'] = stunned_time / total_game_time
    
    return metrics


def calculate_damage_prevention_metrics(state_action_pairs, match_data=None):
    """
    Calculate damage prevention metrics from state-action pairs.
    
    Args:
        state_action_pairs (list): List of state-action pairs
        match_data (dict): Match-level data for context
        
    Returns:
        dict: Dictionary of damage prevention metrics
    """
    metrics = {
        'total_damage_prevented': 0,
        'damage_prevented_by_w': 0,
        'damage_prevented_by_r': 0,
        'prevention_efficiency': 0,
        'ult_timing_score': 0,
        'damage_prevented_per_minute': 0
    }
    
    total_game_time = 0
    if state_action_pairs:
        total_game_time = state_action_pairs[-1]['state']['game_time_seconds']
    
    # Track W and R casts
    w_shields = []  # List of (start_time, end_time, target, amount)
    r_shields = []  # List of (start_time, end_time, targets)
    
    # Process each state-action pair
    for pair in state_action_pairs:
        state = pair['state']
        action = pair.get('action', {})
        timestamp = state['game_time_seconds']
        
        # Track W casts
        if action.get('ability') == 'W':
            target = action.get('target', {})
            shield_amount = action.get('shield_amount', 0)
            
            # W shield typically lasts 2.5 seconds
            shield_start = timestamp
            shield_end = timestamp + 2.5
            
            w_shields.append({
                'start_time': shield_start,
                'end_time': shield_end,
                'target': target,
                'amount': shield_amount
            })
        
        # Track R casts
        if action.get('ability') == 'R':
            targets = action.get('targets', [])
            
            # Cosmic Radiance lasts 2.5 seconds and has a brief delay
            ult_start = timestamp + 2.5  # Accounting for the delay
            ult_end = ult_start + 2.5
            
            r_shields.append({
                'start_time': ult_start,
                'end_time': ult_end,
                'targets': targets
            })
        
        # Check for incoming damage events
        for w_shield in w_shields:
            if w_shield['start_time'] <= timestamp <= w_shield['end_time']:
                # Check if the shielded target took damage
                incoming_damage = 0
                
                nearby_units = state.get('nearby_units', {})
                for ally in nearby_units.get('allies', []):
                    if ally.get('id') == w_shield['target'].get('id'):
                        # This is our shielded ally
                        incoming_damage = ally.get('damage_taken_last_second', 0)
                        break
                
                # Estimate damage prevented (up to shield amount)
                damage_prevented = min(incoming_damage, w_shield['amount'])
                metrics['damage_prevented_by_w'] += damage_prevented
                metrics['total_damage_prevented'] += damage_prevented
        
        # Check for R protection
        for r_shield in r_shields:
            if r_shield['start_time'] <= timestamp <= r_shield['end_time']:
                # During ult invulnerability period
                incoming_damage = 0
                
                # Estimate damage that would have been taken by all allies
                nearby_units = state.get('nearby_units', {})
                for ally in nearby_units.get('allies', []):
                    # Check if this ally is in the ult targets
                    ally_id = ally.get('id')
                    is_protected = any(target.get('id') == ally_id for target in r_shield['targets'])
                    
                    if is_protected:
                        incoming_damage += ally.get('damage_taken_last_second', 0)
                
                # All damage is prevented during ult
                metrics['damage_prevented_by_r'] += incoming_damage
                metrics['total_damage_prevented'] += incoming_damage
    
    # Calculate ult timing score
    # Higher score if ult prevented more damage
    if r_shields:
        avg_damage_prevented = metrics['damage_prevented_by_r'] / len(r_shields) if metrics['damage_prevented_by_r'] > 0 else 0
        
        # Scale to a 0-1 score
        # Assuming 1000 damage prevented per ult is very good
        metrics['ult_timing_score'] = min(1.0, avg_damage_prevented / 1000)
    
    # Calculate damage prevented per minute
    if total_game_time > 0:
        metrics['damage_prevented_per_minute'] = metrics['total_damage_prevented'] / (total_game_time / 60)
    
    # Calculate prevention efficiency (percent of estimated incoming damage that was prevented)
    # This is a placeholder since we can't precisely know all incoming damage
    metrics['prevention_efficiency'] = 0.5  # Default placeholder
    
    return metrics


def calculate_combat_metrics(state_action_pairs, match_data=None):
    """
    Calculate combined combat metrics from state-action pairs.
    
    Args:
        state_action_pairs (list): List of state-action pairs
        match_data (dict): Match-level data for context
        
    Returns:
        dict: Dictionary of combat metrics
    """
    healing_metrics = calculate_healing_metrics(state_action_pairs, match_data)
    shield_metrics = calculate_shield_metrics(state_action_pairs, match_data)
    stun_metrics = calculate_stun_metrics(state_action_pairs, match_data)
    damage_prevention_metrics = calculate_damage_prevention_metrics(state_action_pairs, match_data)
    
    # Combine all metrics
    combat_metrics = {
        **healing_metrics,
        **shield_metrics,
        **stun_metrics,
        **damage_prevention_metrics
    }
    
    return combat_metrics 