"""
Analyze the distribution of action types from frame analysis
"""

from src.frame_analysis import FrameAnalyzer, TaricJSONEncoder
import collections
import json
from pathlib import Path

def analyze_match(match_id):
    """
    Analyze action distribution for a specific match
    """
    analyzer = FrameAnalyzer()
    success = analyzer.load_match_by_id(match_id)
    
    if not success:
        print(f"Failed to load match {match_id}")
        return
    
    pairs = analyzer.create_state_action_pairs()
    
    # Count action types
    action_types = collections.Counter([p['action']['type'] for p in pairs])
    
    print(f"Match ID: {match_id}")
    print(f"Total state-action pairs: {len(pairs)}")
    print("\nAction types:")
    for action_type, count in action_types.most_common():
        print(f"  {action_type}: {count} ({count/len(pairs)*100:.1f}%)")
    
    # Count by event type
    event_types = collections.Counter([p.get('event_type', 'UNKNOWN') for p in pairs])
    
    print("\nEvent types:")
    for event_type, count in event_types.most_common():
        print(f"  {event_type}: {count} ({count/len(pairs)*100:.1f}%)")
    
    # Save processed pairs
    output_dir = Path("data/features/state_action_pairs")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / f"taric_sa_pairs_per_second_{match_id}.json"
    
    # Create metadata and save
    output_data = {
        'metadata': {
            'match_id': match_id,
            'pairs_count': len(pairs),
            'action_types': {k: v for k, v in action_types.items()},
            'event_types': {k: v for k, v in event_types.items()}
        },
        'state_action_pairs': pairs
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, cls=TaricJSONEncoder)
    
    print(f"\nSaved detailed analysis to {output_file}")

if __name__ == "__main__":
    # Analyze a specific match
    analyze_match("663516245") 