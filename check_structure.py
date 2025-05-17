import json
import sys

def check_file_structure(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"File: {file_path}")
    print(f"Type of root object: {type(data)}")
    
    if 'state_action_pairs' in data:
        sa_pairs = data['state_action_pairs']
        print(f"Type of state_action_pairs: {type(sa_pairs)}")
        print(f"Number of state_action_pairs: {len(sa_pairs)}")
        
        if len(sa_pairs) > 0:
            first_pair = sa_pairs[0]
            print(f"Type of first pair: {type(first_pair)}")
            
            if isinstance(first_pair, dict):
                print("Keys in first pair:", list(first_pair.keys()))
                
                if 'state' in first_pair:
                    state = first_pair['state']
                    print(f"Type of state: {type(state)}")
                    if isinstance(state, dict):
                        print("Keys in state:", list(state.keys()))
                    
                if 'action' in first_pair:
                    action = first_pair['action']
                    print(f"Type of action: {type(action)}")
                    if isinstance(action, dict):
                        print("Keys in action:", list(action.keys()))

if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = "data/state_action_pairs/taric_sa_pairs_OC1_666495933_20250517_144355.json"
    
    check_file_structure(file_path) 