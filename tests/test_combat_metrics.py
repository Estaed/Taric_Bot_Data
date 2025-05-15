#!/usr/bin/env python
"""
Test script for combat_metrics.py
"""

from src.features.combat_metrics import calculate_combat_metrics

def main():
    # Create a more complete test state-action pair
    test_state_action_pairs = [{
        'state': {
            'game_time_seconds': 300,
            'game_phase': 'mid_game',  # Add game phase
            'nearby_units': {
                'allies': [
                    {
                        'id': 'ally1',
                        'champion': 'ashe',
                        'health_percent': 0.7,
                        'is_in_q_range': True,
                        'damage_taken_last_second': 50
                    }
                ],
                'enemies': [
                    {
                        'id': 'enemy1',
                        'champion': 'darius',
                        'is_attacking': True
                    }
                ]
            },
            'taric_state': {
                'has_link': True
            }
        },
        'action': {
            'ability': 'Q',
            'targets': [{'id': 'ally1', 'champion': 'ashe'}],
            'heal_amount': 120
        },
        'timestamp': 300
    }]
    
    # Add match data for context
    match_data = {
        'teams': {
            'allies': [
                {'champion_name': 'ashe', 'role': 'ADC'},
                {'champion_name': 'taric', 'role': 'SUPPORT'}
            ],
            'enemies': [
                {'champion_name': 'darius', 'role': 'TOP'}
            ]
        },
        'player_stats': {
            'ability_haste': 20
        }
    }
    
    # Test the combat metrics function
    try:
        print("Testing calculate_combat_metrics function...")
        metrics = calculate_combat_metrics(test_state_action_pairs, match_data)
        print("Combat metrics calculated successfully!")
        print(f"Number of metrics: {len(metrics)}")
        
        # Print some key metrics
        print("\nSample metrics:")
        for key, value in list(metrics.items())[:5]:
            print(f"  {key}: {value}")
            
        return True
    except Exception as e:
        print(f"Error testing combat_metrics: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    main() 