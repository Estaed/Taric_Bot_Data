"""
Check the structure of state-action pairs file to verify our changes.
"""

import json
import sys
from pathlib import Path

def check_state_file(filepath):
    """Check the structure of a state-action pairs file."""
    try:
        print(f"Examining file: {filepath}")
        
        # Load the file
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Check top-level structure
        print("\nTop-level structure:")
        for key in data.keys():
            if key == 'state_action_pairs':
                print(f"- {key}: {len(data[key])} pairs")
            else:
                print(f"- {key}: {type(data[key]).__name__}")
        
        # Check if we have state-action pairs
        if len(data.get('state_action_pairs', [])) == 0:
            print("No state-action pairs found.")
            return
        
        # Check the first state-action pair
        first_pair = data['state_action_pairs'][0]
        print("\nFirst state-action pair keys:")
        print(list(first_pair.keys()))
        
        # Check enhanced data
        if 'enhanced_data' in first_pair.get('state', {}):
            enhanced_data = first_pair['state']['enhanced_data']
            print("\nEnhanced data components:")
            for key in enhanced_data.keys():
                print(f"- {key}")
            
            # Verify environmental_context is not present
            if 'environmental_context' in enhanced_data:
                print("\nWARNING: environmental_context is still present!")
            else:
                print("\nSuccess: environmental_context has been removed as expected.")
        else:
            print("\nNo enhanced data found in the first state-action pair.")
        
        # Check if we have team_composition at file level
        if 'team_composition' in data:
            print("\nTeam composition found at file level (optimized storage).")
            
            # Check how many champions in each team
            if isinstance(data['team_composition'], list):
                print(f"- Team composition has {len(data['team_composition'])} members")
        
        if 'enemy_composition' in data:
            if isinstance(data['enemy_composition'], list):
                print(f"- Enemy composition has {len(data['enemy_composition'])} members")
        
        # Estimate storage savings
        if 'team_composition' in data and 'state_action_pairs' in data:
            team_comp_size = len(json.dumps(data.get('team_composition', [])))
            enemy_comp_size = len(json.dumps(data.get('enemy_composition', [])))
            pairs_count = len(data['state_action_pairs'])
            
            estimated_saving = (team_comp_size + enemy_comp_size) * pairs_count
            print(f"\nEstimated storage saving: {estimated_saving/1024/1024:.2f} MB")
    
    except Exception as e:
        print(f"Error examining file: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
    else:
        # Use the test file
        filepath = "data/features/state_action_pairs/taric_sa_pairs_TEST_MATCH_20250515_193953.json"
    
    if not Path(filepath).exists():
        print(f"Error: File not found: {filepath}")
        sys.exit(1)
    
    check_state_file(filepath) 