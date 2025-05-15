#!/usr/bin/env python
"""
Test script for feature extraction functionality.

This script tests the new click position tracking in mechanics_metrics.py

Usage:
    python test_feature_extraction.py
"""

import os
import sys
import json
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import feature extraction modules
from src.features.mechanics_metrics import calculate_mouse_click_metrics

def create_sample_state_action_pair():
    """Create a sample state-action pair with click positions for testing."""
    return {
        'state': {
            'game_time_seconds': 120,
            'game_phase': 'early_game',
            'taric_state': {
                'position_x': 1000,
                'position_y': 1000,
                'health_percent': 0.8,
                'is_dead': False
            },
            'nearby_units': {
                'allies': [
                    {'id': 'ally1', 'distance': 300}
                ],
                'enemies': [
                    {'id': 'enemy1', 'distance': 800}
                ]
            }
        },
        'action': {
            'ability': 'Q',
            'target_position': {
                'x': 1200,
                'y': 900
            },
            'targets': [
                {'id': 'ally1', 'position': {'x': 1200, 'y': 900}}
            ]
        }
    }

def create_sample_right_click_pair():
    """Create a sample state-action pair with right-click movement."""
    return {
        'state': {
            'game_time_seconds': 125,
            'game_phase': 'early_game',
            'taric_state': {
                'position_x': 1050,
                'position_y': 1050,
                'health_percent': 0.8,
                'is_dead': False
            },
            'nearby_units': {
                'allies': [
                    {'id': 'ally1', 'distance': 350}
                ],
                'enemies': []
            }
        },
        'action': {
            'movement': True,
            'target_position': {
                'x': 1500,
                'y': 1500
            }
        }
    }

def create_sample_item_click_pair():
    """Create a sample state-action pair with item usage."""
    return {
        'state': {
            'game_time_seconds': 130,
            'game_phase': 'early_game',
            'taric_state': {
                'position_x': 1100,
                'position_y': 1100,
                'health_percent': 0.7,
                'is_dead': False
            },
            'nearby_units': {
                'allies': [
                    {'id': 'ally1', 'distance': 400}
                ],
                'enemies': [
                    {'id': 'enemy1', 'distance': 700}
                ]
            }
        },
        'action': {
            'item_used': 'HEALTH_POTION',
            'target': {
                'id': 'self',
                'position': {'x': 1100, 'y': 1100}
            }
        }
    }

def test_mouse_click_metrics():
    """Test the mouse click metrics with position tracking."""
    logger.info("Testing mouse click position tracking...")
    
    # Create sample state-action pairs
    state_action_pairs = [
        create_sample_state_action_pair(),
        create_sample_right_click_pair(),
        create_sample_item_click_pair()
    ]
    
    # Calculate mouse click metrics
    metrics = calculate_mouse_click_metrics(state_action_pairs)
    
    # Verify metrics
    logger.info(f"Click counts: {metrics['click_counts']}")
    logger.info(f"Click positions tracked: {len(metrics['click_positions']['right_click_positions'])} right clicks, "
                f"{len(metrics['click_positions']['ability_click_positions'])} ability clicks, "
                f"{len(metrics['click_positions']['item_click_positions'])} item clicks")
    
    # Print detailed position metrics
    logger.info(f"Position variance X: {metrics['click_position_metrics']['position_variance_x']:.2f}")
    logger.info(f"Position variance Y: {metrics['click_position_metrics']['position_variance_y']:.2f}")
    logger.info(f"Average distance from champion: {metrics['click_position_metrics']['distance_from_champion_avg']:.2f}")
    
    # Show heatmap
    logger.info(f"Position heatmap: {metrics['click_position_metrics']['position_heatmap']}")
    logger.info(f"Map coverage: {metrics['click_position_metrics']['map_coverage_percentage']*100:.1f}%")
    
    # Check click clusters
    if metrics['click_position_metrics']['click_clusters']:
        logger.info("Detected click clusters:")
        for i, cluster in enumerate(metrics['click_position_metrics']['click_clusters']):
            logger.info(f"  Cluster {i+1}: center={cluster['center']}, count={cluster['count']}, percentage={cluster['percentage']*100:.1f}%")
    
    return metrics

def main():
    """Run all tests."""
    logger.info("=== Starting Feature Extraction Tests ===")
    
    # Test mouse click metrics
    mouse_metrics = test_mouse_click_metrics()
    
    logger.info("\n=== All Tests Completed ===")
    
    # Return results for verification
    return {
        'mouse_metrics': mouse_metrics
    }

if __name__ == "__main__":
    main() 