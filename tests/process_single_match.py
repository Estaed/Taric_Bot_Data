"""
Process a single match and output state-action pairs for testing.
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from src.frame_analysis import FrameAnalyzer

def process_single_match(match_id=None):
    """
    Process a single match for testing.
    
    Args:
        match_id (str, optional): Match ID to process. If None, will create simulated data.
    """
    print(f"Processing match: {match_id if match_id else 'simulated data'}")
    
    # Create analyzer
    analyzer = FrameAnalyzer(match_id=match_id)
    
    # If no match_id provided, just create simulated timeline data
    if not match_id:
        # Initialize with minimum required data for simulation
        analyzer.match_data = {
            'metadata': {'matchId': 'TEST_MATCH'},
            'info': {
                'gameDuration': 1800,  # 30 minutes
                'gameVersion': 'TEST_VERSION',
                'participants': [
                    {
                        'participantId': 10, 
                        'championId': 44, 
                        'championName': 'Taric', 
                        'teamId': 200,
                        'teamPosition': 'UTILITY',
                        'lane': 'BOTTOM',
                        'role': 'SUPPORT',
                        'summoner1Id': 14,  # Flash
                        'summoner2Id': 4,   # Ignite
                        'goldEarned': 10000,
                        'champLevel': 10,
                        'totalMinionsKilled': 25,
                        'neutralMinionsKilled': 0,
                        'champExperience': 8000,
                        'item0': 3050,  # Zeke's Convergence
                        'item1': 3107,  # Redemption
                        'item2': 3190,  # Locket of the Iron Solari
                        'item3': 2065,  # Shard of True Ice
                        'item4': 0,
                        'item5': 0,
                        'item6': 0
                    },
                    {
                        'participantId': 9, 
                        'championId': 67, 
                        'championName': 'Vayne', 
                        'teamId': 200,
                        'teamPosition': 'BOTTOM',
                        'lane': 'BOTTOM',
                        'role': 'CARRY',
                        'summoner1Id': 4,   # Flash
                        'summoner2Id': 21,  # Heal
                        'goldEarned': 12000,
                        'champLevel': 11,
                        'totalMinionsKilled': 150,
                        'neutralMinionsKilled': 10,
                        'champExperience': 9000
                    },
                    {
                        'participantId': 8, 
                        'championId': 99, 
                        'championName': 'Lux', 
                        'teamId': 200,
                        'teamPosition': 'MIDDLE',
                        'lane': 'MIDDLE',
                        'role': 'SOLO',
                        'summoner1Id': 4,   # Flash
                        'summoner2Id': 12,  # Teleport
                        'goldEarned': 11000,
                        'champLevel': 12,
                        'totalMinionsKilled': 140,
                        'neutralMinionsKilled': 5,
                        'champExperience': 10000
                    },
                    {
                        'participantId': 7, 
                        'championId': 19, 
                        'championName': 'Warwick', 
                        'teamId': 200,
                        'teamPosition': 'JUNGLE',
                        'lane': 'JUNGLE',
                        'role': 'NONE',
                        'summoner1Id': 11,  # Smite
                        'summoner2Id': 4,   # Flash
                        'goldEarned': 10500,
                        'champLevel': 10,
                        'totalMinionsKilled': 40,
                        'neutralMinionsKilled': 100,
                        'champExperience': 8500
                    },
                    {
                        'participantId': 6, 
                        'championId': 92, 
                        'championName': 'Riven', 
                        'teamId': 200,
                        'teamPosition': 'TOP',
                        'lane': 'TOP',
                        'role': 'SOLO',
                        'summoner1Id': 4,   # Flash
                        'summoner2Id': 14,  # Ignite
                        'goldEarned': 10800,
                        'champLevel': 11,
                        'totalMinionsKilled': 130,
                        'neutralMinionsKilled': 15,
                        'champExperience': 9500
                    },
                    # Enemy team
                    {
                        'participantId': 1, 
                        'championId': 27, 
                        'championName': 'Singed', 
                        'teamId': 100,
                        'teamPosition': 'TOP',
                        'lane': 'TOP',
                        'role': 'SOLO',
                        'summoner1Id': 4,   # Flash
                        'summoner2Id': 12,  # Teleport
                        'goldEarned': 10000,
                        'champLevel': 10,
                        'totalMinionsKilled': 120,
                        'neutralMinionsKilled': 10,
                        'champExperience': 8000
                    },
                    {
                        'participantId': 2, 
                        'championId': 64, 
                        'championName': 'LeeSin', 
                        'teamId': 100,
                        'teamPosition': 'JUNGLE',
                        'lane': 'JUNGLE',
                        'role': 'NONE',
                        'summoner1Id': 11,  # Smite
                        'summoner2Id': 4,   # Flash
                        'goldEarned': 10200,
                        'champLevel': 9,
                        'totalMinionsKilled': 30,
                        'neutralMinionsKilled': 95,
                        'champExperience': 7500
                    },
                    {
                        'participantId': 3, 
                        'championId': 74, 
                        'championName': 'Heimerdinger', 
                        'teamId': 100,
                        'teamPosition': 'MIDDLE',
                        'lane': 'MIDDLE',
                        'role': 'SOLO',
                        'summoner1Id': 4,   # Flash
                        'summoner2Id': 14,  # Ignite
                        'goldEarned': 11500,
                        'champLevel': 11,
                        'totalMinionsKilled': 145,
                        'neutralMinionsKilled': 8,
                        'champExperience': 9000
                    },
                    {
                        'participantId': 4, 
                        'championId': 18, 
                        'championName': 'Tristana', 
                        'teamId': 100,
                        'teamPosition': 'BOTTOM',
                        'lane': 'BOTTOM',
                        'role': 'CARRY',
                        'summoner1Id': 4,   # Flash
                        'summoner2Id': 21,  # Heal
                        'goldEarned': 12500,
                        'champLevel': 10,
                        'totalMinionsKilled': 155,
                        'neutralMinionsKilled': 5,
                        'champExperience': 8200
                    },
                    {
                        'participantId': 5, 
                        'championId': 53, 
                        'championName': 'Blitzcrank', 
                        'teamId': 100,
                        'teamPosition': 'UTILITY',
                        'lane': 'BOTTOM',
                        'role': 'SUPPORT',
                        'summoner1Id': 4,   # Flash
                        'summoner2Id': 14,  # Ignite
                        'goldEarned': 9000,
                        'champLevel': 9,
                        'totalMinionsKilled': 30,
                        'neutralMinionsKilled': 0,
                        'champExperience': 7000
                    }
                ],
                'gameMode': 'CLASSIC',
                'gameType': 'MATCHED_GAME',
                'mapId': 11,
                'queueId': 420,
                'platformId': 'TEST',
            }
        }
        analyzer.taric_participant_id = 10
        analyzer.taric_team_id = 200
        analyzer._extract_team_compositions()
        analyzer._extract_game_context()
    
    # Create state-action pairs
    if not analyzer.fetch_timeline():
        print("Error: Could not fetch timeline data")
        return False
    
    pairs = analyzer.create_state_action_pairs()
    print(f"Created {len(pairs)} state-action pairs")
    
    # Save the file with a timestamp
    output_file = analyzer.save_state_action_pairs()
    
    if output_file:
        print(f"Successfully saved state-action pairs to {output_file}")
        
        # Verify that environmental context is not in the output
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if len(data['state_action_pairs']) > 0:
                enhanced_data = data['state_action_pairs'][0]['state'].get('enhanced_data', {})
                if 'environmental_context' in enhanced_data:
                    print("WARNING: environmental_context is still present in the output!")
                else:
                    print("Success: environmental_context has been removed from the output.")
            
            return True
        except Exception as e:
            print(f"Error verifying output file: {e}")
            return False
    else:
        print("Error: Failed to save state-action pairs")
        return False

if __name__ == "__main__":
    # If match ID is provided as command line argument, use it
    match_id = sys.argv[1] if len(sys.argv) > 1 else None
    process_single_match(match_id) 