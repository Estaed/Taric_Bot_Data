"""
Frame-by-frame analysis for Taric match data.

This module processes match data to extract detailed timeline events,
analyze game state at different timestamps, and create state-action pairs
suitable for training a reinforcement learning model.
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
import os
import glob
from datetime import datetime, timedelta
import sys

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.append(project_root)

from src.config import RAW_DATA_DIR, CLEANED_DATA_DIR, STATE_ACTION_DIR

# Import enhanced data extraction capabilities
from src.frame_analysis.enhanced_data_extraction import extract_enhanced_data

# Import scenario templates 
try:
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
    USING_COMPREHENSIVE_SCENARIOS = True
except ImportError:
    USING_COMPREHENSIVE_SCENARIOS = False

# Custom JSON encoder to handle special values
class TaricJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for Taric data that handles special values like infinity and NaN."""
    def default(self, obj):
        if isinstance(obj, float):
            if np.isnan(obj):
                return 0.0
            elif np.isinf(obj) and obj > 0:
                return 9999999.0
            elif np.isinf(obj) and obj < 0:
                return -9999999.0
        
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        
        if isinstance(obj, (np.int64, np.int32, np.int16, np.int8)):
            return int(obj)
        
        if isinstance(obj, (np.float64, np.float32, np.float16)):
            if np.isnan(obj):
                return 0.0
            elif np.isinf(obj) and obj > 0:
                return 9999999.0
            elif np.isinf(obj) and obj < 0:
                return -9999999.0
            return float(obj)
        
        return super().default(obj)

# Constants for Taric
TARIC_CHAMPION_ID = 44
TARIC_ABILITIES = {
    "Q": "StarliGHTstouch",  # Heal
    "W": "Bastion",          # Shield and link
    "E": "Dazzle",           # Stun
    "R": "CosmicRadiance"    # Invulnerability
}

# Add ability cooldown constants (in seconds)
TARIC_COOLDOWNS = {
    "Q": 15,    # Starlight's Touch base cooldown
    "W": 15,    # Bastion base cooldown
    "E": 17,    # Dazzle base cooldown
    "R": 160,   # Cosmic Radiance base cooldown
    "SUMMONER1": 300,  # Default for Flash
    "SUMMONER2": 210   # Default for other summoners
}

# Add estimated range constants
TARIC_RANGES = {
    "Q": 350,     # Starlight's Touch healing range
    "W": 800,     # Bastion cast range
    "W_LINK": 1400, # Bastion link range
    "E": 575,     # Dazzle stun range
    "R": 400,     # Cosmic Radiance radius
    "BASIC_ATTACK": 150  # Basic attack range
}

# Ability Haste values for common Taric items
ITEM_ABILITY_HASTE = {
    # Support Mythics
    3190: 20,    # Locket of the Iron Solari
    6617: 20,    # Moonstone Renewer
    6632: 20,    # Divine Sunderer
    6620: 15,    # Shurelya's Battlesong
    2065: 10,    # Shard of True Ice
    3050: 10,    # Zeke's Convergence
    3107: 10,    # Redemption
    3222: 10,    # Mikael's Blessing
    3504: 10,    # Ardent Censer
    3011: 10,    # Chemtech Putrifier
    4401: 15,    # Knight's Vow
    6665: 10,    # Vigilant Wardstone
    # Other items with AH
    3065: 10,    # Spirit Visage
    3071: 10,    # Black Cleaver
    3083: 10,    # Warmog's Armor
    3102: 15,    # Banshee's Veil
    3110: 10,    # Frozen Heart
    3157: 15,    # Zhonya's Hourglass
    # Default for unknown items
    0: 0         # No ability haste
}

# Estimate ability haste from runes and levels
def estimate_additional_ability_haste(level, has_transcendence=False, has_cosmic_insight=False):
    """
    Estimate ability haste from level, runes, and other sources.
    
    Args:
        level (int): Champion level
        has_transcendence (bool): Whether the champion has the Transcendence rune
        has_cosmic_insight (bool): Whether the champion has the Cosmic Insight rune
        
    Returns:
        int: Estimated ability haste
    """
    # Base ability haste from levels and potential mythic passive
    base_ah = min(10, level // 5 * 5)  # Scales with level (0, 5, 10)
    
    # Rune-based ability haste
    rune_ah = 0
    if has_transcendence:
        # Transcendence gives 5/8/11 AH at levels 5/8/11
        if level >= 11:
            rune_ah += 11
        elif level >= 8:
            rune_ah += 8
        elif level >= 5:
            rune_ah += 5
    
    if has_cosmic_insight:
        rune_ah += 10  # Cosmic Insight gives 10 AH
    
    # Estimated mythic bonus (if any)
    mythic_passive_ah = 0
    if level >= 9:  # Assume mythic completion around level 9
        mythic_passive_ah = 5
    
    return base_ah + rune_ah + mythic_passive_ah

# Function to calculate cooldown reduction from ability haste
def calculate_cdr_from_ah(ability_haste):
    """
    Calculate cooldown reduction percentage from ability haste.
    
    Args:
        ability_haste (float): Ability haste value
        
    Returns:
        float: Cooldown reduction factor (e.g., 0.2 for 20% CDR)
    """
    return ability_haste / (100 + ability_haste)

class FrameAnalyzer:
    """
    Analyzes match data frame-by-frame to extract temporal events and state-action pairs.
    """
    
    def __init__(self, match_data=None, match_id=None):
        """
        Initialize the frame analyzer with match data.
        
        Args:
            match_data (dict, optional): Raw match data. Defaults to None.
            match_id (str, optional): Match ID to load from file. Defaults to None.
        """
        self.match_data = None
        self.timeline_data = None
        self.taric_participant_id = None
        self.taric_team_id = None
        self.frames = None
        self.state_action_pairs = []
        self.team_composition = None
        self.enemy_composition = None
        self.lane_matchup = None
        self.game_context = None
        
        if match_data:
            self.match_data = match_data
            self._identify_taric_player()
            self._extract_team_compositions()
            self._extract_game_context()
        elif match_id:
            self.load_match_by_id(match_id)
    
    def load_match_by_id(self, match_id):
        """
        Load match data from file by match ID.
        
        Args:
            match_id (str): Match ID to load
            
        Returns:
            bool: True if successful, False otherwise
        """
        match_files = list(RAW_DATA_DIR.glob(f"*{match_id}*.json"))
        
        if not match_files:
            print(f"No match file found for match ID: {match_id}")
            return False
        
        try:
            with open(match_files[0], 'r', encoding='utf-8') as f:
                self.match_data = json.load(f)
            
            self._identify_taric_player()
            self._extract_team_compositions()
            self._extract_game_context()
            return True
            
        except Exception as e:
            print(f"Error loading match file: {e}")
            return False
    
    def _identify_taric_player(self):
        """
        Identify the Taric player in the match.
        
        Returns:
            int: Participant ID for Taric or None if not found
        """
        if not self.match_data:
            return None
        
        for participant in self.match_data['info']['participants']:
            if participant['championId'] == TARIC_CHAMPION_ID or participant['championName'].lower() == 'taric':
                self.taric_participant_id = participant['participantId']
                self.taric_team_id = participant['teamId']
                return self.taric_participant_id
        
        return None
    
    def _extract_team_compositions(self):
        """
        Extract team compositions from the match data.
        
        This includes champion names, roles, and other relevant information
        about team composition for context-aware decision making.
        """
        if not self.match_data or not self.taric_participant_id:
            return
        
        # Initialize team compositions
        self.team_composition = []
        self.enemy_composition = []
        
        # Get Taric's team ID
        taric_team_id = None
        for participant in self.match_data['info']['participants']:
            if participant['participantId'] == self.taric_participant_id:
                taric_team_id = participant['teamId']
                break
        
        if not taric_team_id:
            return
        
        # Extract team compositions
        for participant in self.match_data['info']['participants']:
            champion_info = {
                'participantId': participant['participantId'],
                'championId': participant['championId'],
                'championName': participant['championName'],
                'position': participant['teamPosition'],
                'lane': participant['lane'],
                'role': participant.get('role', ''),
                'summoner1Id': participant['summoner1Id'],
                'summoner2Id': participant['summoner2Id']
            }
            
            # Add to appropriate team
            if participant['teamId'] == taric_team_id:
                self.team_composition.append(champion_info)
            else:
                self.enemy_composition.append(champion_info)
        
        # Extract Taric's lane matchup
        taric_position = None
        for ally in self.team_composition:
            if ally['participantId'] == self.taric_participant_id:
                taric_position = ally['position']
                taric_lane = ally['lane']
                break
        
        if taric_position:
            # Find opponent in same position/lane
            for enemy in self.enemy_composition:
                if enemy['position'] == taric_position or enemy['lane'] == taric_lane:
                    self.lane_matchup = {
                        'ally': next((a for a in self.team_composition if a['participantId'] == self.taric_participant_id), None),
                        'enemy': enemy
                    }
                    break
    
    def _extract_game_context(self):
        """
        Extract game context information that affects decision making.
        
        This includes game mode, map, queue type, patch version, and other
        relevant game settings that might affect the agent's behavior.
        """
        if not self.match_data:
            return
        
        info = self.match_data.get('info', {})
        
        self.game_context = {
            'gameMode': info.get('gameMode', ''),
            'gameType': info.get('gameType', ''),
            'mapId': info.get('mapId', 0),
            'queueId': info.get('queueId', 0),
            'gameVersion': info.get('gameVersion', ''),
            'platformId': info.get('platformId', ''),
            'gameDuration': info.get('gameDuration', 0),
            'patch': info.get('gameVersion', '').split('.')[0:2] if 'gameVersion' in info else ['', '']
        }
    
    def fetch_timeline(self):
        """
        Simulates timeline data focused on Taric's actions and events.
        Now generates data at 1-second intervals for more detailed analysis.
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.match_data or not self.taric_participant_id:
            print("Match data or Taric player not found")
            return False
        
        try:
            # Create simulated timeline frames with high temporal resolution (1 second)
            game_duration = self.match_data['info']['gameDuration']
            frame_count = max(60, game_duration)  # One frame every second, with minimum of 60 frames
            
            # Get Taric data from match
            taric_participant = None
            for participant in self.match_data['info']['participants']:
                if participant['championId'] == TARIC_CHAMPION_ID or participant['championName'].lower() == 'taric':
                    taric_participant = participant
                    break
            
            if not taric_participant:
                print("Taric not found in match participants")
                return False
            
            # Get team information
            taric_team_id = taric_participant['teamId']
            allies = [p for p in self.match_data['info']['participants'] if p['teamId'] == taric_team_id and p['championId'] != TARIC_CHAMPION_ID]
            enemies = [p for p in self.match_data['info']['participants'] if p['teamId'] != taric_team_id]
            
            frames = []
            for frame_idx in range(frame_count + 1):
                # Calculate timestamp (1 second in milliseconds)
                timestamp = frame_idx * 1000  # 1 second in milliseconds
                
                # Create frame data
                frame = {
                    'timestamp': timestamp,
                    'participantFrames': {},
                    'events': []
                }
                
                # Add Taric's frame data only - focus on the protagonist
                scale_factor = min(1.0, timestamp / (game_duration * 1000))
                
                # Generate health values based on level and time
                current_level = max(1, int(taric_participant['champLevel'] * scale_factor))
                base_health = 600 + (current_level - 1) * 90  # Approximate Taric health scaling
                max_health = base_health * (1 + 0.02 * (timestamp / 60000))  # Simulate item health bonuses over time
                current_health = max_health * (0.4 + 0.6 * np.random.random())  # Random health between 40-100%
                
                frame['participantFrames'][str(self.taric_participant_id)] = {
                    'participantId': self.taric_participant_id,
                    'position': {
                        'x': np.random.randint(0, 14000),  # Random position on map
                        'y': np.random.randint(0, 14000)
                    },
                    'currentGold': int(taric_participant['goldEarned'] * scale_factor),
                    'totalGold': int(taric_participant['goldEarned'] * scale_factor),
                    'level': current_level,
                    'xp': int(taric_participant.get('champExperience', 0) * scale_factor),
                    'minionsKilled': int(taric_participant['totalMinionsKilled'] * scale_factor),
                    'jungleMinionsKilled': int(taric_participant.get('neutralMinionsKilled', 0) * scale_factor),
                    'currentHealth': int(current_health),
                    'maxHealth': int(max_health)
                }
                
                # Now also generate data for allies and enemies to provide team context
                for ally in allies:
                    ally_scale_factor = min(1.0, scale_factor * (0.9 + 0.2 * np.random.random()))
                    ally_level = max(1, int(ally['champLevel'] * ally_scale_factor))
                    
                    # Base health depends on champion type
                    ally_health_base = 500 + (ally_level - 1) * 80  # Generic health scaling
                    if ally['championName'].lower() in ['leona', 'nautilus', 'alistar', 'braum']:
                        # Tanky supports
                        ally_health_base = 600 + (ally_level - 1) * 95
                    elif ally['championName'].lower() in ['ezreal', 'jinx', 'caitlyn', 'jhin']:
                        # ADCs
                        ally_health_base = 550 + (ally_level - 1) * 85
                    
                    ally_max_health = ally_health_base * (1 + 0.02 * (timestamp / 60000))
                    ally_current_health = ally_max_health * (0.3 + 0.7 * np.random.random())
                    
                    frame['participantFrames'][str(ally['participantId'])] = {
                        'participantId': ally['participantId'],
                        'position': {
                            'x': np.random.randint(0, 14000),
                            'y': np.random.randint(0, 14000)
                        },
                        'currentGold': int(ally['goldEarned'] * ally_scale_factor),
                        'totalGold': int(ally['goldEarned'] * ally_scale_factor),
                        'level': ally_level,
                        'currentHealth': int(ally_current_health),
                        'maxHealth': int(ally_max_health),
                        'championName': ally['championName']
                    }
                
                for enemy in enemies:
                    enemy_scale_factor = min(1.0, scale_factor * (0.9 + 0.2 * np.random.random()))
                    enemy_level = max(1, int(enemy['champLevel'] * enemy_scale_factor))
                    
                    # Base health depends on champion type
                    enemy_health_base = 500 + (enemy_level - 1) * 80  # Generic health scaling
                    enemy_max_health = enemy_health_base * (1 + 0.02 * (timestamp / 60000))
                    enemy_current_health = enemy_max_health * (0.3 + 0.7 * np.random.random())
                    
                    frame['participantFrames'][str(enemy['participantId'])] = {
                        'participantId': enemy['participantId'],
                        'position': {
                            'x': np.random.randint(0, 14000),
                            'y': np.random.randint(0, 14000)
                        },
                        'currentGold': int(enemy['goldEarned'] * enemy_scale_factor),
                        'totalGold': int(enemy['goldEarned'] * enemy_scale_factor),
                        'level': enemy_level,
                        'currentHealth': int(enemy_current_health),
                        'maxHealth': int(enemy_max_health),
                        'championName': enemy['championName']
                    }
                
                # Generate Taric-focused events for this frame
                # Only add events in certain frames to simulate realistic gameplay
                if frame_idx > 0:
                    # Adjust event density based on game phase
                    game_minute = timestamp / 60000
                    
                    # Calculate event probability based on game phase
                    # Early game: fewer events
                    # Mid/late game: more events during intense moments
                    if game_minute < 10:
                        # Early game: ~5-10% chance of event per second
                        event_probability = 0.05 + (game_minute / 10) * 0.05
                    elif game_minute < 25:
                        # Mid game: ~10-20% chance of event per second
                        event_probability = 0.10 + ((game_minute - 10) / 15) * 0.10
                    else:
                        # Late game: ~20-30% chance of event per second
                        event_probability = 0.20 + min(0.10, ((game_minute - 25) / 15) * 0.10)
                        
                    # During high-intensity moments, increase probability
                    # We'll approximate this by adding random spikes
                    if np.random.random() < 0.05:  # 5% chance of high-intensity moment
                        event_probability *= 2
                        
                    # Decide if we should generate an event for this frame
                    if np.random.random() < event_probability:
                        # Random timestamp within this 1-second window
                        event_timestamp = timestamp - np.random.randint(0, 1000)  # Up to 1 second back
                        
                        # Determine event type with weighted probabilities based on game phase
                        event_types = []
                        probabilities = []
                        
                        # Add ability usage events with their probabilities
                        q_chance = 0.6  # High chance to use Q (heal)
                        w_chance = 0.2 + (game_minute / (game_duration/60)) * 0.3  # W usage increases over time
                        e_chance = 0.3 + (game_minute / (game_duration/60)) * 0.4  # E usage increases over time
                        r_chance = 0.05 + (game_minute / (game_duration/60)) * 0.15  # R usage increases late game
                        
                        if np.random.random() < q_chance:
                            event_types.append('TARIC_Q')
                            probabilities.append(q_chance)
                        
                        if np.random.random() < w_chance:
                            event_types.append('TARIC_W')
                            probabilities.append(w_chance)
                        
                        if np.random.random() < e_chance:
                            event_types.append('TARIC_E')
                            probabilities.append(e_chance)
                        
                        if np.random.random() < r_chance:
                            event_types.append('TARIC_R')
                            probabilities.append(r_chance)
                        
                        # Combat events more likely in mid/late game
                        combat_chance = 0.1 + (game_minute / (game_duration/60)) * 0.3
                        if np.random.random() < combat_chance:
                            event_types.extend(['CHAMPION_KILL', 'ASSIST'])
                            probabilities.extend([0.1, 0.2])
                        
                        # Other event types
                        event_types.extend(['WARD_PLACED', 'ELITE_MONSTER_KILL', 'RECALL'])
                        probabilities.extend([0.15, 0.1, 0.15])
                        
                        # Add team fight events in mid/late game
                        if game_minute > 15:
                            event_types.append('TEAM_FIGHT')
                            probabilities.append(0.2)
                        
                        # Normalize probabilities
                        total_prob = sum(probabilities)
                        if total_prob > 0:
                            probabilities = [p/total_prob for p in probabilities]
                        else:
                            probabilities = [1/len(probabilities)] * len(probabilities)
                        
                        # Choose event type
                        event_type = np.random.choice(event_types, p=probabilities)
                        
                        # Create event with detailed Taric information
                        event = {
                            'timestamp': event_timestamp,
                            'participantId': self.taric_participant_id
                        }
                        
                        # Handle different event types
                        if event_type == 'TARIC_Q':
                            # Q ability (Heal)
                            event['type'] = 'TARIC_ABILITY_CAST'
                            event['ability'] = 'Q'
                            
                            # Simulate casting Q on low health allies
                            targets = []
                            heal_amount = 60 + 40 * current_level  # Base heal scaling with level
                            
                            # Sometimes heal self
                            if np.random.random() < 0.4:
                                targets.append(self.taric_participant_id)
                            
                            # Add random allies as heal targets
                            num_allies = min(3, len(allies))
                            for _ in range(np.random.randint(0, num_allies + 1)):
                                if allies:
                                    targets.append(allies[np.random.randint(0, len(allies))]['participantId'])
                            
                            event['affectedIds'] = list(set(targets))  # Remove duplicates
                            event['healAmount'] = heal_amount
                        
                        elif event_type == 'TARIC_W':
                            # W ability (Bastion shield)
                            event['type'] = 'TARIC_ABILITY_CAST'
                            event['ability'] = 'W'
                            
                            # Choose an ally to link with
                            if allies:
                                target_id = allies[np.random.randint(0, len(allies))]['participantId']
                                event['targetId'] = target_id
                                event['shieldAmount'] = 80 + 50 * current_level  # Shield value scaling with level
                        
                        elif event_type == 'TARIC_E':
                            # E ability (Stun)
                            event['type'] = 'TARIC_ABILITY_CAST'
                            event['ability'] = 'E'
                            
                            # Direction of stun
                            dir_x = np.random.random() * 2 - 1  # Random direction vector
                            dir_y = np.random.random() * 2 - 1
                            # Normalize
                            magnitude = max(0.001, np.sqrt(dir_x**2 + dir_y**2))
                            dir_x /= magnitude
                            dir_y /= magnitude
                            
                            event['directionX'] = dir_x
                            event['directionY'] = dir_y
                            
                            # Simulate enemies hit by stun
                            stunned_targets = []
                            num_enemies = min(2, len(enemies))  # At most 2 enemies stunned
                            for _ in range(np.random.randint(0, num_enemies + 1)):
                                if enemies:
                                    stunned_targets.append(enemies[np.random.randint(0, len(enemies))]['participantId'])
                            
                            event['affectedIds'] = list(set(stunned_targets))  # Remove duplicates
                        
                        elif event_type == 'TARIC_R':
                            # R ability (Cosmic Radiance)
                            event['type'] = 'TARIC_ABILITY_CAST'
                            event['ability'] = 'R'
                            
                            # Allies affected by ult
                            affected_allies = [self.taric_participant_id]  # Always includes self
                            
                            # Add random allies as affected by ult
                            num_allies = min(4, len(allies))
                            for _ in range(np.random.randint(1, num_allies + 1)):
                                if allies:
                                    affected_allies.append(allies[np.random.randint(0, len(allies))]['participantId'])
                            
                            event['affectedIds'] = list(set(affected_allies))  # Remove duplicates
                        
                        elif event_type == 'CHAMPION_KILL':
                            # Taric kills are rare, but possible
                            event['type'] = 'CHAMPION_KILL'
                            event['killerId'] = self.taric_participant_id
                            
                            # Random enemy as victim
                            if enemies:
                                event['victimId'] = enemies[np.random.randint(0, len(enemies))]['participantId']
                            else:
                                event['victimId'] = np.random.randint(6, 11)  # Fallback random enemy ID
                            
                            event['taric_action'] = 'KILL'
                            
                        elif event_type == 'ASSIST':
                            # Taric getting an assist
                            event['type'] = 'ASSIST'
                            
                            # Random ally as killer
                            if allies:
                                event['killerId'] = allies[np.random.randint(0, len(allies))]['participantId']
                            else:
                                event['killerId'] = np.random.randint(1, 11)
                            
                            # Random enemy as victim
                            if enemies:
                                event['victimId'] = enemies[np.random.randint(0, len(enemies))]['participantId']
                            else:
                                event['victimId'] = np.random.randint(6, 11)
                            
                            event['assistingParticipantIds'] = [self.taric_participant_id]
                            event['taric_action'] = 'ASSIST'
                            
                        elif event_type == 'WARD_PLACED':
                            # Taric placing a ward
                            event['type'] = 'WARD_PLACED'
                            event['creatorId'] = self.taric_participant_id
                            
                            # Random position for ward
                            event['position'] = {
                                'x': np.random.randint(0, 14000),
                                'y': np.random.randint(0, 14000)
                            }
                            
                            event['taric_action'] = 'WARD_PLACED'
                            
                        elif event_type == 'ELITE_MONSTER_KILL':
                            # Team killing elite monster with Taric assisting
                            event['type'] = 'ELITE_MONSTER_KILL'
                            
                            # Random ally as killer or jungler
                            if allies:
                                event['killerId'] = allies[np.random.randint(0, len(allies))]['participantId']
                            else:
                                event['killerId'] = np.random.randint(1, 11)
                            
                            event['monsterType'] = np.random.choice(['DRAGON', 'BARON_NASHOR', 'RIFTHERALD'])
                            event['assistingParticipantIds'] = [self.taric_participant_id]
                            
                        elif event_type == 'RECALL':
                            # Taric recalling
                            event['type'] = 'RECALL'
                            event['recallStatus'] = 'FINISHED'  # Assume recall completes
                            
                        # Add the event to the frame
                        frame['events'].append(event)
                
                frames.append(frame)
            
            # Create timeline data structure
            self.timeline_data = {
                'metadata': self.match_data['metadata'],
                'info': {
                    'frameInterval': 1000,  # 1 second in milliseconds
                    'frames': frames
                }
            }
            
            self.frames = frames
            return True
            
        except Exception as e:
            print(f"Error creating timeline data: {e}")
            return False
    
    def extract_taric_events(self):
        """
        Extract all events related to Taric from the timeline.
        
        Returns:
            list: List of Taric-related events
        """
        if not self.timeline_data or not self.frames:
            if not self.fetch_timeline():
                return []
        
        taric_events = []
        
        for frame in self.frames:
            for event in frame.get('events', []):
                # Check if Taric is involved in the event
                is_taric_event = False
                
                # Check various event types
                if event.get('type') == 'CHAMPION_KILL':
                    if event.get('killerId') == self.taric_participant_id:
                        is_taric_event = True
                        event['taric_action'] = 'KILL'
                
                elif event.get('type') == 'ASSIST':
                    if self.taric_participant_id in event.get('assistingParticipantIds', []):
                        is_taric_event = True
                        event['taric_action'] = 'ASSIST'
                
                elif event.get('type') == 'WARD_PLACED':
                    if event.get('creatorId') == self.taric_participant_id:
                        is_taric_event = True
                        event['taric_action'] = 'WARD_PLACED'
                
                elif event.get('type') == 'WARD_KILL':
                    if event.get('killerId') == self.taric_participant_id:
                        is_taric_event = True
                        event['taric_action'] = 'WARD_KILL'
                
                elif event.get('type') == 'SKILL_LEVEL_UP':
                    if event.get('participantId') == self.taric_participant_id:
                        is_taric_event = True
                        skill_slot = event.get('skillSlot')
                        if skill_slot == 1:
                            event['taric_action'] = 'LEVEL_Q'
                        elif skill_slot == 2:
                            event['taric_action'] = 'LEVEL_W'
                        elif skill_slot == 3:
                            event['taric_action'] = 'LEVEL_E'
                        elif skill_slot == 4:
                            event['taric_action'] = 'LEVEL_R'
                
                elif event.get('type') in ['ITEM_PURCHASED', 'ITEM_SOLD', 'ITEM_DESTROYED']:
                    if event.get('participantId') == self.taric_participant_id:
                        is_taric_event = True
                        event['taric_action'] = event.get('type')
                
                # Add event if it's related to Taric
                if is_taric_event:
                    taric_events.append(event)
        
        return taric_events
    
    def create_state_action_pairs(self):
        """
        Create state-action pairs for reinforcement learning.
        
        Returns:
            list: List of state-action pairs
        """
        if not self.timeline_data or not self.frames:
            if not self.fetch_timeline():
                return []
        
        state_action_pairs = []
        
        # Get all Taric-related events
        taric_events = self.extract_taric_events()
        
        # Create a dictionary to track which frames have explicit actions
        frames_with_actions = {}
        
        # Keep track of previous states and actions for context
        previous_states = []
        previous_actions = []
        
        # First pass - create state-action pairs for explicit actions
        for event in taric_events:
            # Get the frame closest to this event
            event_time = event.get('timestamp', 0)
            closest_frame = None
            min_time_diff = float('inf')
            closest_frame_idx = -1
            
            for i, frame in enumerate(self.frames):
                time_diff = abs(frame.get('timestamp', 0) - event_time)
                if time_diff < min_time_diff:
                    min_time_diff = time_diff
                    closest_frame = frame
                    closest_frame_idx = i
            
            if not closest_frame:
                continue
            
            # Mark this frame as having an action
            frames_with_actions[closest_frame_idx] = True
            
            # Create game state at this moment
            game_state = self._create_game_state(closest_frame, event_time)
            
            # Get the action from the event
            action = self._create_action(event)
            
            # Add enhanced data extraction
            if game_state and action:
                # Add enhanced data to the game state
                enhanced_data = extract_enhanced_data(
                    game_state, 
                    event_time, 
                    action, 
                    previous_states, 
                    previous_actions,
                    self  # Pass self as analyzer
                )
                
                game_state['enhanced_data'] = enhanced_data
                
                # Create state-action pair
                state_action_pair = {
                    'state': game_state,
                    'action': action,
                    'timestamp': event_time,
                    'event_type': event.get('type')
                }
                
                # Add to lists
                state_action_pairs.append(state_action_pair)
                previous_states.append(game_state)
                previous_actions.append(action)
        
        # Second pass - add NO_ACTION for frames without explicit actions
        for i, frame in enumerate(self.frames):
            # Skip frames that already have actions
            if i in frames_with_actions:
                continue
                
            timestamp = frame.get('timestamp', 0)
            
            # Create game state
            game_state = self._create_game_state(frame, timestamp)
            
            # Create a NO_ACTION action
            action = {
                'type': 'NO_ACTION',
                'timestamp': timestamp,
                'description': 'No explicit action detected in this frame'
            }
            
            # Add to state-action pairs
            if game_state:
                # Add enhanced data to the game state
                enhanced_data = extract_enhanced_data(
                    game_state, 
                    timestamp, 
                    action, 
                    previous_states, 
                    previous_actions,
                    self  # Pass self as analyzer
                )
                
                game_state['enhanced_data'] = enhanced_data
                
                state_action_pair = {
                    'state': game_state,
                    'action': action,
                    'timestamp': timestamp,
                    'event_type': 'NO_ACTION'
                }
                
                state_action_pairs.append(state_action_pair)
                previous_states.append(game_state)
                previous_actions.append(action)
        
        # Sort state-action pairs by timestamp
        state_action_pairs.sort(key=lambda x: x['timestamp'])
        
        self.state_action_pairs = state_action_pairs
        return state_action_pairs
    
    def _create_game_state(self, frame, timestamp):
        """
        Create a game state representation at a specific moment, focused only on Taric.
        
        Args:
            frame (dict): Frame data
            timestamp (int): Timestamp in milliseconds
            
        Returns:
            dict: Game state representation with Taric-centric focus
        """
        if not frame:
            return None
        
        try:
            # Get Taric's state in this frame
            taric_frame = frame.get('participantFrames', {}).get(str(self.taric_participant_id))
            if not taric_frame:
                return None
            
            # Calculate cooldowns
            cooldowns = self._calculate_cooldowns(frame, timestamp)
            
            # Get nearby allies and enemies (simplified representations)
            nearby_units = self._get_nearby_units(frame, taric_frame)
            
            # Get targeting info - who Taric is targeting with abilities
            targeting = self._get_targeting_info(frame, timestamp)
            
            # Calculate game phase
            game_time_minutes = timestamp / 60000
            if game_time_minutes < 14:
                game_phase = "EARLY_GAME"
            elif game_time_minutes < 25:
                game_phase = "MID_GAME"
            else:
                game_phase = "LATE_GAME"
            
            # Create overall game state focused on Taric with enhanced information
            # Removed static match data (team_composition, enemy_composition, lane_matchup, game_context)
            game_state = {
                'timestamp': timestamp,
                'game_time_seconds': timestamp / 1000,  # seconds
                'game_phase': game_phase,
                'taric_state': {
                    'position_x': taric_frame.get('position', {}).get('x'),
                    'position_y': taric_frame.get('position', {}).get('y'),
                    'level': taric_frame.get('level'),
                    'current_gold': taric_frame.get('currentGold'),
                    'total_gold': taric_frame.get('totalGold'),
                    'minions_killed': taric_frame.get('minionsKilled'),
                    'jungle_minions_killed': taric_frame.get('jungleMinionsKilled'),
                    'current_health': taric_frame.get('currentHealth', 1000),
                    'max_health': taric_frame.get('maxHealth', 1500),
                    'health_percent': taric_frame.get('currentHealth', 1000) / max(taric_frame.get('maxHealth', 1500), 1),
                    'cooldowns': cooldowns,
                    'is_recalling': self._is_recalling(frame, timestamp),
                    'has_link': targeting.get('linked_ally_id') is not None
                },
                'nearby_units': nearby_units,
                'targeting': targeting,
                # Only include Taric's relevant events
                'game_events': [
                    e for e in frame.get('events', []) 
                    if e.get('timestamp') <= timestamp and (
                        e.get('killerId') == self.taric_participant_id or
                        e.get('victimId') == self.taric_participant_id or
                        e.get('creatorId') == self.taric_participant_id or
                        e.get('participantId') == self.taric_participant_id or
                        self.taric_participant_id in e.get('assistingParticipantIds', [])
                    )
                ],
                'reward_signals': self._calculate_rewards(frame, timestamp)
            }
            
            return game_state
            
        except Exception as e:
            print(f"Error creating game state: {e}")
            return None
    
    def _calculate_cooldowns(self, frame, timestamp):
        """
        Calculate the cooldown state of Taric's abilities, accounting for ability haste.
        
        Args:
            frame (dict): Frame data
            timestamp (int): Current timestamp
            
        Returns:
            dict: Cooldown states for abilities
        """
        cooldowns = {
            "Q": 0,
            "W": 0,
            "E": 0, 
            "R": 0,
            "SUMMONER1": 0,
            "SUMMONER2": 0
        }
        
        # Get Taric's frame data
        taric_frame = frame.get('participantFrames', {}).get(str(self.taric_participant_id))
        if not taric_frame:
            return cooldowns
        
        # Get Taric's current level
        current_level = taric_frame.get('level', 1)
        
        # Calculate total ability haste from items
        total_ability_haste = 0
        
        # If we have access to the match data, get Taric's items and check for ability haste
        if self.match_data:
            taric_participant = None
            for participant in self.match_data['info']['participants']:
                if participant['participantId'] == self.taric_participant_id:
                    taric_participant = participant
                    break
            
            if taric_participant:
                # Add up ability haste from items
                for item_slot in range(7):  # Items 0-6
                    item_id = taric_participant.get(f'item{item_slot}', 0)
                    total_ability_haste += ITEM_ABILITY_HASTE.get(item_id, 0)
                
                # Check for runes that provide ability haste
                has_transcendence = False
                has_cosmic_insight = False
                
                # Check for Transcendence (Sorcery) and Cosmic Insight (Inspiration)
                if 'perks' in taric_participant:
                    for style in taric_participant['perks'].get('styles', []):
                        if style.get('style') == 8200:  # Sorcery
                            for selection in style.get('selections', []):
                                if selection.get('perk') == 8210:  # Transcendence
                                    has_transcendence = True
                        elif style.get('style') == 8300:  # Inspiration
                            for selection in style.get('selections', []):
                                if selection.get('perk') == 8347:  # Cosmic Insight
                                    has_cosmic_insight = True
                
                # Add ability haste from runes and level
                total_ability_haste += estimate_additional_ability_haste(
                    current_level,
                    has_transcendence,
                    has_cosmic_insight
                )
        else:
            # If we don't have match data, estimate based on level
            # Use a conservative estimate of ability haste scaling with level
            # At level 1: ~0 AH, level 6: ~10 AH, level 11: ~20 AH, level 16: ~40 AH
            estimated_game_progress = min(1.0, current_level / 18)
            total_ability_haste = int(estimated_game_progress * 50)  # Maximum of ~50 AH at level 18
        
        # Calculate cooldown reduction factor
        cdr_factor = calculate_cdr_from_ah(total_ability_haste)
        
        # If we have previous events, check for ability usage and apply CDR
        for event in frame.get('events', []):
            if event.get('timestamp') > timestamp:
                continue
                
            if event.get('type') == 'SKILL_LEVEL_UP' and event.get('participantId') == self.taric_participant_id:
                # When an ability is leveled up, there's a good chance it was just used
                skill_slot = event.get('skillSlot')
                if skill_slot == 1:
                    # This only applies if skill was used, so we set a partial cooldown
                    base_cooldown = TARIC_COOLDOWNS["Q"] * 0.3  # Partial cooldown for skill level up
                    reduced_cooldown = base_cooldown * (1 - cdr_factor)
                    cooldowns["Q"] = max(0, reduced_cooldown - (timestamp - event.get('timestamp')) / 1000)
                elif skill_slot == 2:
                    base_cooldown = TARIC_COOLDOWNS["W"] * 0.3
                    reduced_cooldown = base_cooldown * (1 - cdr_factor)
                    cooldowns["W"] = max(0, reduced_cooldown - (timestamp - event.get('timestamp')) / 1000)
                elif skill_slot == 3:
                    base_cooldown = TARIC_COOLDOWNS["E"] * 0.3
                    reduced_cooldown = base_cooldown * (1 - cdr_factor)
                    cooldowns["E"] = max(0, reduced_cooldown - (timestamp - event.get('timestamp')) / 1000)
                elif skill_slot == 4:
                    base_cooldown = TARIC_COOLDOWNS["R"] * 0.3
                    reduced_cooldown = base_cooldown * (1 - cdr_factor)
                    cooldowns["R"] = max(0, reduced_cooldown - (timestamp - event.get('timestamp')) / 1000)
            
            # Check for Taric ability usage events we created in the simulation
            if event.get('type') == 'TARIC_ABILITY_CAST' and event.get('participantId') == self.taric_participant_id:
                ability = event.get('ability')
                if ability in cooldowns:
                    base_cooldown = TARIC_COOLDOWNS[ability]
                    reduced_cooldown = base_cooldown * (1 - cdr_factor)
                    cooldowns[ability] = max(0, reduced_cooldown - (timestamp - event.get('timestamp')) / 1000)
            
            # Check for summoner spell usage
            if event.get('type') == 'SUMMONER_SPELL_USED' and event.get('participantId') == self.taric_participant_id:
                spell_id = event.get('summonerSpellId')
                if spell_id == 1:  # First summoner spell
                    base_cooldown = TARIC_COOLDOWNS["SUMMONER1"]
                    reduced_cooldown = base_cooldown * (1 - cdr_factor)
                    cooldowns["SUMMONER1"] = max(0, reduced_cooldown - (timestamp - event.get('timestamp')) / 1000)
                elif spell_id == 2:  # Second summoner spell
                    base_cooldown = TARIC_COOLDOWNS["SUMMONER2"]
                    reduced_cooldown = base_cooldown * (1 - cdr_factor)
                    cooldowns["SUMMONER2"] = max(0, reduced_cooldown - (timestamp - event.get('timestamp')) / 1000)
        
        return cooldowns
    
    def _get_nearby_units(self, frame, taric_frame):
        """
        Get simplified information about nearby allies and enemies.
        
        Args:
            frame (dict): Frame data
            taric_frame (dict): Taric's frame data
            
        Returns:
            dict: Information about nearby units
        """
        nearby = {
            'allies': [],
            'enemies': [],
            'ally_count': 0,
            'enemy_count': 0,
            'closest_ally_distance': 9999999,  # Use a large number instead of infinity for JSON compatibility
            'closest_enemy_distance': 9999999,  # Use a large number instead of infinity for JSON compatibility
            'average_ally_health_percent': 1.0,
            'average_enemy_health_percent': 1.0
        }
        
        # Get Taric's position
        taric_x = taric_frame.get('position', {}).get('x', 0)
        taric_y = taric_frame.get('position', {}).get('y', 0)
        
        # For nearby units, we'll just create simulated data for the RL model
        # In a real scenario, we'd extract this from participant frames
        
        # Simulate 0-4 allies nearby
        ally_count = min(4, np.random.randint(0, 5))
        nearby['ally_count'] = ally_count
        
        ally_health_total = 0
        
        for i in range(ally_count):
            # Random distance from Taric (300-1200 units)
            distance = np.random.randint(300, 1200)
            if distance < nearby['closest_ally_distance']:
                nearby['closest_ally_distance'] = distance
                
            # Random health percentage (0.1-1.0)
            health_percent = max(0.1, min(1.0, np.random.random()))
            ally_health_total += health_percent
            
            # Create simplified ally representation
            ally = {
                'distance': distance,
                'health_percent': health_percent,
                'is_in_q_range': distance <= TARIC_RANGES["Q"],
                'is_in_w_range': distance <= TARIC_RANGES["W"],
                'is_in_e_range': distance <= TARIC_RANGES["E"],
                'is_in_r_range': distance <= TARIC_RANGES["R"],
                'is_in_danger': health_percent < 0.3  # Low health
            }
            nearby['allies'].append(ally)
        
        if ally_count > 0:
            nearby['average_ally_health_percent'] = ally_health_total / ally_count
        
        # Simulate 0-5 enemies nearby
        enemy_count = min(5, np.random.randint(0, 6))
        nearby['enemy_count'] = enemy_count
        
        enemy_health_total = 0
        
        for i in range(enemy_count):
            # Random distance from Taric (300-1500 units)
            distance = np.random.randint(300, 1500)
            if distance < nearby['closest_enemy_distance']:
                nearby['closest_enemy_distance'] = distance
                
            # Random health percentage (0.1-1.0)
            health_percent = max(0.1, min(1.0, np.random.random()))
            enemy_health_total += health_percent
            
            # Create simplified enemy representation
            enemy = {
                'distance': distance,
                'health_percent': health_percent,
                'is_in_basic_attack_range': distance <= TARIC_RANGES["BASIC_ATTACK"],
                'is_in_e_range': distance <= TARIC_RANGES["E"],
                'is_stunnable': distance <= TARIC_RANGES["E"],
                'is_killable': health_percent < 0.2  # Very low health
            }
            nearby['enemies'].append(enemy)
        
        if enemy_count > 0:
            nearby['average_enemy_health_percent'] = enemy_health_total / enemy_count
            
        # Keep default distances if no units found
        if ally_count == 0:
            nearby['closest_ally_distance'] = -1  # -1 indicates no allies nearby
        if enemy_count == 0:
            nearby['closest_enemy_distance'] = -1  # -1 indicates no enemies nearby
            
        return nearby
    
    def _is_recalling(self, frame, timestamp):
        """Check if Taric is currently recalling"""
        # Check for recall events
        for event in frame.get('events', []):
            if (event.get('type') == 'RECALL' and 
                event.get('participantId') == self.taric_participant_id and
                event.get('timestamp') <= timestamp and
                event.get('timestamp') + 8000 >= timestamp):  # Recall takes 8 seconds
                return True
        return False
    
    def _get_targeting_info(self, frame, timestamp):
        """
        Extract information about who Taric is targeting with abilities.
        
        Args:
            frame (dict): Frame data
            timestamp (int): Current timestamp
            
        Returns:
            dict: Targeting information
        """
        targeting = {
            'linked_ally_id': None,
            'last_heal_target_id': None,
            'last_stun_target_id': None,
            'ulted_allies': []
        }
        
        # Look for recent W castings to determine linked ally
        for event in frame.get('events', []):
            if event.get('timestamp') > timestamp:
                continue
                
            # W ability usage (Bastion)
            if (event.get('type') == 'TARIC_ABILITY_CAST' and 
                event.get('ability') == 'W' and 
                event.get('participantId') == self.taric_participant_id):
                targeting['linked_ally_id'] = event.get('targetId')
            
            # Q ability usage (Heal)
            elif (event.get('type') == 'TARIC_ABILITY_CAST' and 
                  event.get('ability') == 'Q' and 
                  event.get('participantId') == self.taric_participant_id):
                targeting['last_heal_target_id'] = event.get('targetId')
            
            # E ability usage (Stun)
            elif (event.get('type') == 'TARIC_ABILITY_CAST' and 
                  event.get('ability') == 'E' and 
                  event.get('participantId') == self.taric_participant_id):
                targeting['last_stun_target_id'] = event.get('targetId')
            
            # R ability usage (Ultimate)
            elif (event.get('type') == 'TARIC_ABILITY_CAST' and 
                  event.get('ability') == 'R' and 
                  event.get('participantId') == self.taric_participant_id):
                targeting['ulted_allies'] = event.get('affectedIds', [])
        
        return targeting
    
    def _calculate_rewards(self, frame, timestamp):
        """
        Calculate various reward signals for reinforcement learning.
        
        Args:
            frame (dict): Frame data
            timestamp (int): Current timestamp
            
        Returns:
            dict: Reward signals
        """
        rewards = {
            'kill_reward': 0,
            'assist_reward': 0,
            'death_penalty': 0,
            'heal_reward': 0,
            'stun_reward': 0,
            'ultimate_reward': 0,
            'objective_reward': 0,
            'warding_reward': 0,
            'survival_reward': 0
        }
        
        # Look at recent events to calculate rewards
        for event in frame.get('events', []):
            if event.get('timestamp') > timestamp or event.get('timestamp') < timestamp - 10000:  # Last 10 seconds
                continue
            
            # Kills
            if event.get('type') == 'CHAMPION_KILL' and event.get('killerId') == self.taric_participant_id:
                rewards['kill_reward'] += 1.0
            
            # Assists
            elif event.get('type') == 'ASSIST' and self.taric_participant_id in event.get('assistingParticipantIds', []):
                rewards['assist_reward'] += 0.5
            
            # Deaths
            elif event.get('type') == 'CHAMPION_KILL' and event.get('victimId') == self.taric_participant_id:
                rewards['death_penalty'] -= 1.0
            
            # Healing allies
            elif event.get('type') == 'TARIC_ABILITY_CAST' and event.get('ability') == 'Q' and event.get('participantId') == self.taric_participant_id:
                rewards['heal_reward'] += 0.2
            
            # Stunning enemies
            elif event.get('type') == 'TARIC_ABILITY_CAST' and event.get('ability') == 'E' and event.get('participantId') == self.taric_participant_id:
                rewards['stun_reward'] += 0.3
            
            # Using ultimate to save allies
            elif event.get('type') == 'TARIC_ABILITY_CAST' and event.get('ability') == 'R' and event.get('participantId') == self.taric_participant_id:
                rewards['ultimate_reward'] += 0.5
            
            # Participating in objectives
            elif event.get('type') == 'ELITE_MONSTER_KILL' and self.taric_participant_id in event.get('assistingParticipantIds', []):
                rewards['objective_reward'] += 0.4
            
            # Warding
            elif event.get('type') == 'WARD_PLACED' and event.get('creatorId') == self.taric_participant_id:
                rewards['warding_reward'] += 0.1
        
        # Survival reward (small reward for staying alive)
        rewards['survival_reward'] = 0.01
        
        # Calculate total reward
        rewards['total_reward'] = sum(rewards.values())
        
        return rewards
    
    def _create_action(self, event):
        """
        Create an action representation from an event with enhanced targeting information.
        
        Args:
            event (dict): Event data
            
        Returns:
            dict: Action representation
        """
        if not event:
            return None
        
        try:
            action_type = event.get('taric_action', event.get('type'))
            
            # Create action based on event type with enhanced information
            action = {
                'type': action_type,
                'timestamp': event.get('timestamp')
            }
            
            # Add action-specific data
            if action_type in ['KILL', 'ASSIST']:
                action['target_id'] = event.get('victimId')
                
            elif action_type in ['WARD_PLACED', 'WARD_KILL']:
                action['position'] = event.get('position')
                
            elif action_type in ['LEVEL_Q', 'LEVEL_W', 'LEVEL_E', 'LEVEL_R']:
                action['skill'] = action_type[-1]  # Extract Q, W, E, or R
                
            elif action_type in ['ITEM_PURCHASED', 'ITEM_SOLD', 'ITEM_DESTROYED']:
                action['item_id'] = event.get('itemId')
            
            # Add targeting information for specific abilities
            if action_type == 'TARIC_ABILITY_CAST':
                action['ability'] = event.get('ability')
                action['target_id'] = event.get('targetId')
                
                if event.get('ability') == 'Q':  # Heal
                    action['healing_amount'] = event.get('healAmount', 100)
                    action['targets'] = event.get('affectedIds', [])
                    
                elif event.get('ability') == 'W':  # Shield
                    action['target_id'] = event.get('targetId')
                    action['shield_amount'] = event.get('shieldAmount', 100)
                    
                elif event.get('ability') == 'E':  # Stun
                    action['stun_direction_x'] = event.get('directionX', 0)
                    action['stun_direction_y'] = event.get('directionY', 0)
                    action['stunned_targets'] = event.get('affectedIds', [])
                    
                elif event.get('ability') == 'R':  # Ultimate
                    action['affected_allies'] = event.get('affectedIds', [])
            
            return action
            
        except Exception as e:
            print(f"Error creating action: {e}")
            return None
    
    def save_state_action_pairs(self, output_file=None):
        """
        Save state-action pairs to a file.
        
        Args:
            output_file (str or Path, optional): Output file path. Defaults to None.
            
        Returns:
            str: Output file path
        """
        if not self.state_action_pairs:
            self.create_state_action_pairs()
        
        if not self.state_action_pairs:
            print("No state-action pairs to save")
            return None
        
        try:
            # Create output directory if needed
            output_dir = STATE_ACTION_DIR
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Default output file
            if not output_file:
                match_id = self.match_data['metadata']['matchId']
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = output_dir / f"taric_sa_pairs_{match_id}_{timestamp}.json"
            
            # Create a custom JSON serializable data structure with static match data separated
            output_data = {
                'metadata': {
                    'match_id': self.match_data['metadata']['matchId'],
                    'game_version': self.match_data['info']['gameVersion'],
                    'taric_participant_id': self.taric_participant_id,
                    'pairs_count': len(self.state_action_pairs)
                },
                # Add static match data at the top level - only stored once
                'match_data': {
                    'team_composition': self.team_composition,
                    'enemy_composition': self.enemy_composition,
                    'lane_matchup': self.lane_matchup,
                    'game_context': self.game_context
                },
                'state_action_pairs': self._prepare_json_serializable(self.state_action_pairs)
            }
            
            # Save to file using a custom encoder to handle NaN and Infinity
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, cls=TaricJSONEncoder)
            
            print(f"Saved {len(self.state_action_pairs)} state-action pairs to {output_file}")
            return output_file
            
        except Exception as e:
            print(f"Error saving state-action pairs: {e}")
            return None
            
    def _prepare_json_serializable(self, data):
        """
        Prepare data to be JSON serializable by handling special values.
        
        Args:
            data: Any Python data structure
            
        Returns:
            object: JSON-serializable structure
        """
        if isinstance(data, dict):
            return {k: self._prepare_json_serializable(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._prepare_json_serializable(item) for item in data]
        elif isinstance(data, (int, str, bool, type(None))):
            return data
        elif isinstance(data, float):
            if np.isnan(data):
                return 0.0
            elif np.isinf(data) and data > 0:
                return 9999999.0
            elif np.isinf(data) and data < 0:
                return -9999999.0
            else:
                return data
        elif isinstance(data, np.ndarray):
            return self._prepare_json_serializable(data.tolist())
        elif isinstance(data, (np.int64, np.int32, np.int16, np.int8)):
            return int(data)
        elif isinstance(data, (np.float64, np.float32, np.float16)):
            if np.isnan(data):
                return 0.0
            elif np.isinf(data) and data > 0:
                return 9999999.0
            elif np.isinf(data) and data < 0:
                return -9999999.0
            else:
                return float(data)
        else:
            return str(data)  # Convert any other types to string

    def create_critical_decision_scenarios(self):
        """
        Create specific scenarios for critical decision points, especially for Taric's ultimate.
        
        This method generates additional state-action pairs that focus on high-impact 
        decision moments, such as when to use Cosmic Radiance, optimal target selection
        for abilities, and positioning during team fights.
        
        Returns:
            list: Additional state-action pairs focusing on critical decision points
        """
        if not self.match_data or not self.frames:
            if not self.fetch_timeline():
                return []
        
        critical_scenarios = []
        game_duration = self.match_data['info']['gameDuration']
        
        # 1. Ultimate Usage Scenarios
        # Create scenarios where Taric needs to decide whether to use ultimate
        ult_scenarios = []
        
        # Define critical moments for ultimate usage
        ult_decision_points = [
            {
                "name": "Team_Fight_Imminent",
                "description": "Team fight about to begin, multiple enemies approaching",
                "game_time_range": (0.4, 0.8),  # 40-80% through the game
                "ally_health_range": (0.3, 0.7), # Allies with 30-70% health
                "enemy_count": (3, 5),           # 3-5 enemies nearby
                "correct_action": "USE_ULT"      # Should use ultimate
            },
            {
                "name": "Objective_Contest",
                "description": "Contesting Baron/Dragon with enemy team",
                "game_time_range": (0.5, 0.9),   # Mid to late game
                "ally_health_range": (0.4, 0.8),
                "enemy_count": (3, 5),
                "correct_action": "USE_ULT"
            },
            {
                "name": "Allied_Carry_Diving",
                "description": "Allied carry diving enemy team, needs protection",
                "game_time_range": (0.3, 0.9),
                "ally_health_range": (0.3, 0.6),
                "enemy_count": (2, 4),
                "correct_action": "USE_ULT"
            },
            {
                "name": "False_Alarm",
                "description": "Situation looks threatening but doesn't require ultimate",
                "game_time_range": (0.2, 0.8),
                "ally_health_range": (0.6, 0.9),  # Allies quite healthy
                "enemy_count": (1, 2),            # Only a couple enemies
                "correct_action": "HOLD_ULT"      # Should NOT use ultimate
            }
        ]
        
        # Generate scenarios for each decision point
        for decision in ult_decision_points:
            # Create 2-3 variations of each scenario
            for _ in range(np.random.randint(2, 4)):
                # Calculate timestamp within the game time range
                min_time, max_time = decision["game_time_range"]
                scenario_time_percent = min_time + np.random.random() * (max_time - min_time)
                timestamp = int(game_duration * 1000 * scenario_time_percent)
                
                # Find nearest frame
                nearest_frame = None
                min_time_diff = float('inf')
                for frame in self.frames:
                    time_diff = abs(frame.get('timestamp', 0) - timestamp)
                    if time_diff < min_time_diff:
                        min_time_diff = time_diff
                        nearest_frame = frame
                
                if not nearest_frame:
                    continue
                
                # Create base game state
                game_state = self._create_game_state(nearest_frame, timestamp)
                if not game_state:
                    continue
                
                # Modify game state to match scenario requirements
                # Set ally health values
                min_health, max_health = decision["ally_health_range"]
                allies = game_state["nearby_units"]["allies"]
                for ally in allies:
                    ally["health_percent"] = min_health + np.random.random() * (max_health - min_health)
                    ally["is_in_danger"] = ally["health_percent"] < 0.4
                
                # Set enemy count and proximity
                min_enemies, max_enemies = decision["enemy_count"]
                enemy_count = np.random.randint(min_enemies, max_enemies + 1)
                
                # Adjust enemy list
                enemies = game_state["nearby_units"]["enemies"]
                while len(enemies) > enemy_count and enemies:
                    enemies.pop()
                
                # Add enemies if needed
                while len(enemies) < enemy_count:
                    enemies.append({
                        "distance": np.random.randint(400, 1200),  # Enemies at engagement range
                        "health_percent": 0.5 + np.random.random() * 0.5,  # Healthy enemies
                        "is_in_basic_attack_range": False,
                        "is_in_e_range": np.random.random() > 0.5,
                        "is_stunnable": np.random.random() > 0.5,
                        "is_killable": False
                    })
                
                # Update unit counts
                game_state["nearby_units"]["ally_count"] = len(allies)
                game_state["nearby_units"]["enemy_count"] = len(enemies)
                
                # Create action for this scenario
                action = {
                    "type": "CRITICAL_DECISION",
                    "name": decision["name"],
                    "description": decision["description"],
                    "timestamp": timestamp,
                    "correct_action": decision["correct_action"]
                }
                
                if decision["correct_action"] == "USE_ULT":
                    action["ability"] = "R"
                    # Include allies who would be affected by ultimate
                    action["affected_allies"] = [self.taric_participant_id]  # Taric always affected
                    for ally in allies:
                        if np.random.random() > 0.2:  # 80% chance to include each ally
                            action["affected_allies"].append(np.random.randint(1, 5))  # Random ally ID
                
                # Add this scenario
                ult_scenarios.append({
                    "state": game_state,
                    "action": action,
                    "timestamp": timestamp,
                    "event_type": "CRITICAL_DECISION",
                    "scenario_type": "ULTIMATE_DECISION"
                })
        
        critical_scenarios.extend(ult_scenarios)
        
        # 2. Stun Chain Scenarios (E ability usage)
        stun_scenarios = []
        
        # Similar structure to ultimate scenarios
        stun_decision_points = [
            {
                "name": "Multiple_Targets_Stun",
                "description": "Multiple enemies in stun range",
                "game_time_range": (0.2, 0.9),
                "enemy_count": (2, 4),
                "enemy_proximity": (300, 570),  # Within stun range (575)
                "correct_action": "USE_E"
            },
            {
                "name": "Defensive_Peel",
                "description": "Enemy diving ally, need to peel with stun",
                "game_time_range": (0.1, 0.9),
                "enemy_count": (1, 2),
                "enemy_proximity": (200, 400),
                "ally_health_range": (0.1, 0.4),  # Low health ally
                "correct_action": "USE_E"
            }
        ]
        
        # Generate stun scenarios
        for decision in stun_decision_points:
            for _ in range(np.random.randint(2, 4)):
                # Calculate timestamp
                min_time, max_time = decision["game_time_range"]
                scenario_time_percent = min_time + np.random.random() * (max_time - min_time)
                timestamp = int(game_duration * 1000 * scenario_time_percent)
                
                # Find nearest frame and create game state (similar to above)
                nearest_frame = None
                min_time_diff = float('inf')
                for frame in self.frames:
                    time_diff = abs(frame.get('timestamp', 0) - timestamp)
                    if time_diff < min_time_diff:
                        min_time_diff = time_diff
                        nearest_frame = frame
                
                if not nearest_frame:
                    continue
                
                game_state = self._create_game_state(nearest_frame, timestamp)
                if not game_state:
                    continue
                
                # Modify game state for stun scenario
                # Set enemy count and proximity
                min_enemies, max_enemies = decision["enemy_count"]
                enemy_count = np.random.randint(min_enemies, max_enemies + 1)
                
                # Adjust enemy list and set proximity
                enemies = game_state["nearby_units"]["enemies"]
                while len(enemies) > enemy_count and enemies:
                    enemies.pop()
                
                # Add enemies if needed
                min_proximity, max_proximity = decision["enemy_proximity"]
                while len(enemies) < enemy_count:
                    distance = min_proximity + np.random.random() * (max_proximity - min_proximity)
                    enemies.append({
                        "distance": distance,
                        "health_percent": 0.4 + np.random.random() * 0.6,
                        "is_in_basic_attack_range": distance <= TARIC_RANGES["BASIC_ATTACK"],
                        "is_in_e_range": distance <= TARIC_RANGES["E"],
                        "is_stunnable": distance <= TARIC_RANGES["E"],
                        "is_killable": np.random.random() > 0.8
                    })
                
                # Handle ally health for defensive scenarios
                if "ally_health_range" in decision:
                    min_health, max_health = decision["ally_health_range"]
                    allies = game_state["nearby_units"]["allies"]
                    for ally in allies:
                        ally["health_percent"] = min_health + np.random.random() * (max_health - min_health)
                        ally["is_in_danger"] = ally["health_percent"] < 0.3
                
                # Update unit counts
                game_state["nearby_units"]["ally_count"] = len(game_state["nearby_units"]["allies"])
                game_state["nearby_units"]["enemy_count"] = len(enemies)
                
                # Create action
                action = {
                    "type": "CRITICAL_DECISION",
                    "name": decision["name"],
                    "description": decision["description"],
                    "timestamp": timestamp,
                    "correct_action": decision["correct_action"]
                }
                
                if decision["correct_action"] == "USE_E":
                    action["ability"] = "E"
                    # Add stun direction
                    action["stun_direction_x"] = np.random.random() * 2 - 1
                    action["stun_direction_y"] = np.random.random() * 2 - 1
                    # Normalize direction vector
                    magnitude = np.sqrt(action["stun_direction_x"]**2 + action["stun_direction_y"]**2)
                    if magnitude > 0:
                        action["stun_direction_x"] /= magnitude
                        action["stun_direction_y"] /= magnitude
                    
                    # Add targets that would be hit
                    action["stunned_targets"] = []
                    for i, enemy in enumerate(enemies):
                        if enemy["is_in_e_range"] and np.random.random() > 0.3:
                            action["stunned_targets"].append(i + 6)  # Assuming enemies start at ID 6
                
                # Add scenario
                stun_scenarios.append({
                    "state": game_state,
                    "action": action,
                    "timestamp": timestamp,
                    "event_type": "CRITICAL_DECISION",
                    "scenario_type": "STUN_DECISION"
                })
        
        critical_scenarios.extend(stun_scenarios)
        
        # 3. Add comprehensive scenarios from taric_scenarios.py if available
        if USING_COMPREHENSIVE_SCENARIOS:
            comprehensive_scenarios = self._create_comprehensive_scenarios()
            if comprehensive_scenarios:
                critical_scenarios.extend(comprehensive_scenarios)
                print(f"  Added {len(comprehensive_scenarios)} comprehensive scenarios")
        
        return critical_scenarios

    def _create_comprehensive_scenarios(self):
        """
        Generate all scenario types from the comprehensive scenario templates.
        
        Returns:
            list: All generated scenario instances
        """
        if not USING_COMPREHENSIVE_SCENARIOS:
            return []
            
        all_scenarios = []
        
        # Process Q scenarios
        for q_scenario_template in ABILITY_SCENARIOS["Q_SCENARIOS"]:
            # Generate 2-4 variations of each scenario
            for _ in range(np.random.randint(2, 5)):
                scenario = self._generate_scenario_from_template(
                    q_scenario_template, "Q_ABILITY"
                )
                if scenario:
                    all_scenarios.append(scenario)
        
        # Process W scenarios
        for w_scenario_template in ABILITY_SCENARIOS["W_SCENARIOS"]:
            for _ in range(np.random.randint(2, 5)):
                scenario = self._generate_scenario_from_template(
                    w_scenario_template, "W_ABILITY"
                )
                if scenario:
                    all_scenarios.append(scenario)
        
        # Process E scenarios
        for e_scenario_template in ABILITY_SCENARIOS["E_SCENARIOS"]:
            for _ in range(np.random.randint(2, 5)):
                scenario = self._generate_scenario_from_template(
                    e_scenario_template, "E_ABILITY"
                )
                if scenario:
                    all_scenarios.append(scenario)
        
        # Process R scenarios
        for r_scenario_template in ABILITY_SCENARIOS["R_SCENARIOS"]:
            for _ in range(np.random.randint(2, 5)):
                scenario = self._generate_scenario_from_template(
                    r_scenario_template, "R_ABILITY"
                )
                if scenario:
                    all_scenarios.append(scenario)
        
        # Process positioning scenarios
        for pos_template in POSITIONING_SCENARIOS:
            for _ in range(np.random.randint(2, 4)):
                scenario = self._generate_scenario_from_template(
                    pos_template, "POSITIONING"
                )
                if scenario:
                    all_scenarios.append(scenario)
        
        # Process combat scenarios
        for combat_template in COMBAT_SCENARIOS:
            for _ in range(np.random.randint(2, 4)):
                scenario = self._generate_scenario_from_template(
                    combat_template, "COMBAT"
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
                    scenario = self._generate_scenario_from_template(
                        template, category
                    )
                    if scenario:
                        all_scenarios.append(scenario)
        
        # Process game phase scenarios
        for phase, templates in GAME_PHASE_SCENARIOS.items():
            for template in templates:
                for _ in range(np.random.randint(1, 4)):
                    scenario = self._generate_scenario_from_template(
                        template, f"GAME_PHASE_{phase}"
                    )
                    if scenario:
                        all_scenarios.append(scenario)
        
        return all_scenarios
        
    def _generate_scenario_from_template(self, template, category):
        """
        Generate a concrete scenario instance from a template.
        
        Args:
            template (dict): The scenario template
            category (str): The scenario category
            
        Returns:
            dict: A concrete scenario instance or None if generation failed
        """
        try:
            # Get game data
            game_duration = self.match_data['info']['gameDuration']
            
            # Calculate timestamp within the game time range
            min_time, max_time = template.get("game_time_range", (0.0, 1.0))
            scenario_time_percent = min_time + np.random.random() * (max_time - min_time)
            timestamp = int(game_duration * 1000 * scenario_time_percent)
            
            # Find nearest frame
            nearest_frame = None
            min_time_diff = float('inf')
            
            for frame in self.frames:
                time_diff = abs(frame.get('timestamp', 0) - timestamp)
                if time_diff < min_time_diff:
                    min_time_diff = time_diff
                    nearest_frame = frame
            
            if not nearest_frame:
                return None
            
            # Create base game state
            game_state = self._create_game_state(nearest_frame, timestamp)
            if not game_state:
                return None
            
            # Modify game state to match scenario requirements
            self._modify_game_state_for_scenario(game_state, template)
            
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
                action["targets"] = [self.taric_participant_id]  # Self
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
                action["affected_allies"] = [self.taric_participant_id]  # Taric always affected
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
    
    def _modify_game_state_for_scenario(self, game_state, template):
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
                
        return game_state

def process_all_matches():
    """
    Process all match files to create state-action pairs.
    
    Returns:
        list: List of output files
    """
    # Get all match files
    match_files = list(RAW_DATA_DIR.glob('*.json'))
    
    if not match_files:
        print(f"No match files found in {RAW_DATA_DIR}")
        return []
    
    print(f"Processing {len(match_files)} match files for frame analysis...")
    
    output_files = []
    for match_file in match_files:
        try:
            print(f"Processing {match_file}...")
            
            # Load match data
            with open(match_file, 'r', encoding='utf-8') as f:
                match_data = json.load(f)
            
            # Create frame analyzer
            analyzer = FrameAnalyzer(match_data=match_data)
            
            # Create standard state-action pairs
            standard_pairs = analyzer.create_state_action_pairs()
            
            # Generate critical decision scenarios
            try:
                critical_scenarios = analyzer.create_critical_decision_scenarios()
                if critical_scenarios:
                    print(f"  Added {len(critical_scenarios)} critical decision scenarios")
                    analyzer.state_action_pairs.extend(critical_scenarios)
            except Exception as e:
                print(f"  Warning: Could not create critical scenarios: {e}")
            
            # Save combined state-action pairs
            output_file = analyzer.save_state_action_pairs()
            
            if output_file:
                output_files.append(output_file)
            
        except Exception as e:
            print(f"Error processing {match_file}: {e}")
    
    print(f"Processed {len(output_files)} match files successfully")
    return output_files

def main():
    """Main function to perform frame analysis on match data."""
    print("Performing frame-by-frame analysis on Taric match data...")
    output_files = process_all_matches()
    
    if output_files:
        print(f"Successfully created state-action pairs for {len(output_files)} matches")
    else:
        print("No state-action pairs were created")

if __name__ == "__main__":
    main() 