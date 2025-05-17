"""
Inspect enhanced data from state-action pairs.
"""

import json
import sys
from pathlib import Path

def inspect_enhanced_data(filepath):
    """
    Inspect enhanced data in a state-action pairs file.
    
    Args:
        filepath (str): Path to the state-action pairs file
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        state_action_pairs = data.get('state_action_pairs', [])
        
        # Count and find enhanced data pairs
        enhanced_pairs = [p for p in state_action_pairs if 'enhanced_data' in p.get('state', {})]
        enhanced_count = len(enhanced_pairs)
        total_count = len(state_action_pairs)
        
        print(f"Enhanced Data Inspection for {filepath}")
        print(f"Total state-action pairs: {total_count}")
        print(f"Pairs with enhanced data: {enhanced_count} ({enhanced_count/total_count*100:.1f}%)")
        
        if enhanced_count > 0:
            # Get the first sample with enhanced data
            sample = enhanced_pairs[0]['state']['enhanced_data']
            
            # Show top-level structure
            print("\nEnhanced Data Structure:")
            for key in sample.keys():
                print(f"- {key}")
            
            # Display sample data for each category
            print("\nSample Data (first 3 categories):")
            
            for i, (key, value) in enumerate(sample.items()):
                if i >= 3:
                    break
                    
                print(f"\n{key.upper()}")
                print("-" * 40)
                
                if isinstance(value, dict):
                    for subkey, subvalue in value.items():
                        # Format based on data type
                        if isinstance(subvalue, dict):
                            print(f"  {subkey}: {type(subvalue).__name__} with {len(subvalue)} items")
                        elif isinstance(subvalue, (list, tuple)):
                            print(f"  {subkey}: {type(subvalue).__name__} with {len(subvalue)} items")
                        else:
                            print(f"  {subkey}: {subvalue}")
                else:
                    print(f"  {value}")
                    
            # Sample specific areas
            print("\nPositional Data Sample:")
            if 'positional_data' in sample:
                pos_data = sample['positional_data']
                print(f"  Current Region: {pos_data.get('current_region', 'Unknown')}")
                print(f"  Distance to Dragon: {pos_data.get('objective_distances', {}).get('distance_to_dragon', 'N/A')}")
                print(f"  Is in Danger Zone: {pos_data.get('is_in_danger_zone', False)}")
            
            print("\nCombat Metrics Sample:")
            if 'combat_metrics' in sample:
                combat_data = sample['combat_metrics']
                print(f"  In Combat: {combat_data.get('in_combat', False)}")
                print(f"  Combat Advantage: {combat_data.get('combat_advantage', 0)}")
                print(f"  Ally Health Average: {combat_data.get('ally_health_average', 0)}")
                
                # Potential heal targets
                heal_targets = combat_data.get('potential_heal_targets', [])
                if heal_targets:
                    print(f"  Top Heal Target: Priority {heal_targets[0].get('priority', 0):.2f}, Health {heal_targets[0].get('health_percent', 0)*100:.1f}%")
                else:
                    print("  No Potential Heal Targets")
            
            print("\nInput Patterns Sample:")
            if 'input_patterns' in sample:
                pattern_data = sample['input_patterns']
                print(f"  Combat Style: {pattern_data.get('combat_style', 'Unknown')}")
                print(f"  Target Selection: {pattern_data.get('target_selection_pattern', 'Unknown')}")
                print(f"  Recent Ability Sequence: {pattern_data.get('ability_sequence', [])}")
            
        else:
            print("No enhanced data found in the state-action pairs.")
        
    except Exception as e:
        print(f"Error inspecting enhanced data: {e}")

if __name__ == "__main__":
    # Use the latest processed file if not specified
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
    else:
        # Find the most recent state-action pairs file
        sa_pairs_dir = Path('data/state_action_pairs')
        files = list(sa_pairs_dir.glob('*.json'))
        if files:
            # Sort by modification time, newest first
            files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            filepath = str(files[0])
            print(f"Using most recent file: {filepath}")
        else:
            print("No state-action pairs files found.")
            sys.exit(1)
    
    inspect_enhanced_data(filepath) 