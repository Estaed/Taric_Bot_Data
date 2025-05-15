"""
Training Feature Extraction from Frame Analysis

This module directly extracts training features from game frames,
combining frame analysis and feature extraction in a single pipeline
for more efficient training data collection.

Usage:
    Import this module and use extract_training_features() to process frames.
"""

import time
import logging
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Import feature calculation modules
from src.features.combat_metrics import calculate_combat_metrics
from src.features.vision_metrics import calculate_vision_metrics
from src.features.positioning_metrics import calculate_positioning_metrics
from src.features.mechanics_metrics import calculate_mechanics_metrics
from src.features.game_state_metrics import calculate_game_state_metrics

# Import frame analysis modules - UPDATED
from src.frame_analysis.frame_analysis import FrameAnalyzer, TaricJSONEncoder

# Configure logging
logger = logging.getLogger(__name__)

class TrainingFeatureExtractor:
    """Extracts training features directly from game frames."""
    
    def __init__(self, buffer_size=100):
        """
        Initialize the training feature extractor.
        
        Args:
            buffer_size (int): Maximum number of frames to store in memory
        """
        self.frame_buffer = []
        self.buffer_size = buffer_size
        self.state_action_pairs = []
        self.feature_buffer = defaultdict(list)
        self.match_data = {}
        self.metadata = {}
        self.frame_analyzer = FrameAnalyzer()  # Initialize FrameAnalyzer
        
    def process_frame(self, frame_data):
        """
        Process a single game frame and extract features.
        
        Args:
            frame_data (dict): Raw frame data from the game
            
        Returns:
            dict: Extracted features
        """
        # Add frame to buffer
        self.frame_buffer.append(frame_data)
        
        # Keep buffer size under limit
        if len(self.frame_buffer) > self.buffer_size:
            self.frame_buffer.pop(0)
        
        # Extract metadata if this is the first frame
        if not self.metadata and 'gameData' in frame_data:
            self._extract_metadata(frame_data)
        
        # Process frame to get state-action pair - UPDATED
        # Instead of using non-existent functions, we use FrameAnalyzer
        if not self.frame_analyzer.match_data and self.match_data:
            self.frame_analyzer.match_data = self.match_data
            self.frame_analyzer._identify_taric_player()
            self.frame_analyzer._extract_team_compositions()
        
        # Create a game state from the frame
        try:
            timestamp = frame_data.get('gameData', {}).get('gameTime', 0)
            game_state = self.frame_analyzer._create_game_state(frame_data, timestamp)
            
            # Find any events that happened in this frame
            events = self.frame_analyzer.extract_taric_events()
            
            # If we have events, create actions
            if events:
                for event in events:
                    action = self.frame_analyzer._create_action(event)
                    if action:
                        # Create a state-action pair
                        state_action = {
                            'state': game_state,
                            'action': action,
                            'timestamp': timestamp
                        }
                        self.state_action_pairs.append(state_action)
            else:
                # No events, just add the game state
                state_action = {
                    'state': game_state,
                    'timestamp': timestamp
                }
                self.state_action_pairs.append(state_action)
            
            # Extract features if we have enough state-action pairs
            if len(self.state_action_pairs) >= 5:  # Need a small sequence for context
                features = self._extract_features_from_current_pairs()
                return features
                
        except Exception as e:
            logger.error(f"Error processing frame: {str(e)}")
            
        return None
    
    def _extract_metadata(self, frame_data):
        """Extract metadata from frame data."""
        game_data = frame_data.get('gameData', {})
        
        self.metadata = {
            'game_id': game_data.get('gameId', ''),
            'game_mode': game_data.get('gameMode', ''),
            'game_time': game_data.get('gameTime', 0),
            'taric_player': game_data.get('activePlayer', {}).get('summonerName', ''),
            'extraction_time': datetime.now().isoformat()
        }
        
        # Extract team data
        allies = []
        enemies = []
        
        for player in game_data.get('allPlayers', []):
            player_data = {
                'champion': player.get('championName', ''),
                'summoner_name': player.get('summonerName', ''),
                'team': player.get('team', ''),
                'position': player.get('position', '')
            }
            
            if player.get('team') == game_data.get('activePlayer', {}).get('team'):
                allies.append(player_data)
            else:
                enemies.append(player_data)
        
        self.metadata['allies'] = allies
        self.metadata['enemies'] = enemies
        
        # Add to match data
        self.match_data = {
            'gameId': game_data.get('gameId', ''),
            'gameMode': game_data.get('gameMode', ''),
            'teams': {
                'allies': allies,
                'enemies': enemies
            }
        }
    
    def _extract_features_from_current_pairs(self):
        """Extract features from current state-action pairs buffer."""
        # Only use the most recent state-action pairs for feature extraction
        recent_pairs = self.state_action_pairs[-10:]
        
        # Calculate features
        combat_metrics = calculate_combat_metrics(recent_pairs, self.match_data)
        vision_metrics = calculate_vision_metrics(recent_pairs, self.match_data)
        positioning_metrics = calculate_positioning_metrics(recent_pairs, self.match_data)
        mechanics_metrics = calculate_mechanics_metrics(recent_pairs, self.match_data)
        game_state_metrics = calculate_game_state_metrics(recent_pairs, self.match_data)
        
        # Add to feature buffer
        current_features = {
            'combat': combat_metrics,
            'vision': vision_metrics,
            'positioning': positioning_metrics,
            'mechanics': mechanics_metrics,
            'game_state': game_state_metrics,
            'timestamp': datetime.now().isoformat(),
            'game_time': recent_pairs[-1]['state'].get('game_time_seconds', 0)
        }
        
        # Add features to buffer
        for feature_type, metrics in current_features.items():
            if feature_type not in ['timestamp', 'game_time']:
                self.feature_buffer[feature_type].append(metrics)
        
        return current_features
    
    def get_training_data(self):
        """
        Get processed training data suitable for model training.
        
        Returns:
            dict: Training data with features and labels
        """
        if not self.feature_buffer:
            return None
        
        # Prepare features for training
        features = {}
        for feature_type, metrics_list in self.feature_buffer.items():
            if metrics_list:
                # Flatten and normalize features
                flattened = self._flatten_and_normalize_metrics(metrics_list)
                features[feature_type] = flattened
        
        # Get state-action pairs for labels
        labels = []
        for pair in self.state_action_pairs:
            if 'action' in pair:
                action = pair['action']
                # Extract relevant action information for training
                label = {
                    'ability': action.get('ability'),
                    'target_type': action.get('target_type'),
                    'target_position': action.get('target_position'),
                    'movement': action.get('movement'),
                    'item_used': action.get('item_used'),
                    'timestamp': pair['state'].get('game_time_seconds', 0)
                }
                labels.append(label)
        
        return {
            'features': features,
            'labels': labels,
            'metadata': self.metadata
        }
    
    def _flatten_and_normalize_metrics(self, metrics_list):
        """Flatten and normalize metrics for training."""
        flattened = {}
        # Simple flattening for demonstration - in practice this would be more sophisticated
        for metric_dict in metrics_list:
            for key, value in metric_dict.items():
                if isinstance(value, (int, float)):
                    if key not in flattened:
                        flattened[key] = []
                    flattened[key].append(value)
        
        # Calculate averages for numeric values
        averaged = {}
        for key, values in flattened.items():
            if values:
                averaged[key] = sum(values) / len(values)
        
        return averaged
    
    def save_training_data(self, output_dir):
        """
        Save training data to file.
        
        Args:
            output_dir (str): Directory to save training data
            
        Returns:
            str: Path to saved training data file
        """
        import json
        import os
        
        # Create output directory if it doesn't exist
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Get training data
        training_data = self.get_training_data()
        
        if not training_data:
            logger.warning("No training data to save")
            return None
        
        # Generate filename
        game_id = self.metadata.get('game_id', 'unknown')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"taric_training_data_{game_id}_{timestamp}.json"
        
        # Save to file
        output_file = output_path / filename
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(training_data, f, indent=2, cls=TaricJSONEncoder)  # Use the custom encoder
        
        logger.info(f"Saved training data to {output_file}")
        return str(output_file)
    
    def clear_buffers(self):
        """Clear all buffers."""
        self.frame_buffer = []
        self.state_action_pairs = []
        self.feature_buffer = defaultdict(list)


def extract_training_features(frame_data, extractor=None, output_dir=None):
    """
    Extract training features from a frame.
    
    Args:
        frame_data (dict): Frame data from the game
        extractor (TrainingFeatureExtractor): Existing extractor instance
        output_dir (str): Directory to save training data
        
    Returns:
        tuple: (features, extractor) - extracted features and extractor instance
    """
    # Create extractor if not provided
    if extractor is None:
        extractor = TrainingFeatureExtractor()
    
    # Process frame
    features = extractor.process_frame(frame_data)
    
    # Save training data if output directory is provided
    if output_dir and features:
        extractor.save_training_data(output_dir)
    
    return features, extractor 