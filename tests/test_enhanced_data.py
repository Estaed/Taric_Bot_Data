"""
Test the enhanced data extraction to verify changes.
"""

import json
from src.frame_analysis.enhanced_data_extraction import extract_enhanced_data

# Create a minimal game state for testing
test_game_state = {
    'taric_state': {
        'position_x': 1000,
        'position_y': 1000,
        'level': 5,
        'current_health': 800,
        'max_health': 1000,
    },
    'nearby_units': {
        'allies': [
            {
                'distance': 400,
                'health_percent': 0.7
            }
        ],
        'enemies': [
            {
                'distance': 600,
                'health_percent': 0.8
            }
        ],
        'ally_count': 1,
        'enemy_count': 1
    }
}

# Test the extract_enhanced_data function
enhanced_data = extract_enhanced_data(
    test_game_state,
    timestamp=60000,  # 1 minute into the game
    action=None,
    previous_states=None,
    previous_actions=None,
    analyzer=None
)

# Print the keys to verify environmental_context is removed
print("Enhanced data keys:", enhanced_data.keys())

# Pretty print the enhanced data
print("\nEnhanced data content:")
print(json.dumps(enhanced_data, indent=2))

# Verify environmental_context is not in the keys
assert 'environmental_context' not in enhanced_data, "Environmental context should be removed!"
print("\nTest passed: Environmental context has been successfully removed.") 