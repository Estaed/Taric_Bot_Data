"""
Process raw match data to extract Taric-specific information.
"""

import json
import pandas as pd
import os
import glob
from pathlib import Path
import sys

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import RAW_DATA_DIR, CLEANED_DATA_DIR

def extract_taric_data(match_data):
    """
    Extract Taric-specific data from a match.
    
    Args:
        match_data (dict): Raw match data
        
    Returns:
        dict: Extracted Taric data or None if Taric not in match
    """
    try:
        match_id = match_data['metadata']['matchId']
        
        # Find Taric in the match
        taric_participant = None
        for participant in match_data['info']['participants']:
            if participant['championName'].lower() == 'taric':
                taric_participant = participant
                break
        
        if not taric_participant:
            print(f"Taric not found in match {match_id}")
            return None
        
        # Extract basic match info
        match_info = {
            'match_id': match_id,
            'game_version': match_data['info']['gameVersion'],
            'game_duration': match_data['info']['gameDuration'],
            'game_mode': match_data['info']['gameMode'],
            'map_id': match_data['info']['mapId'],
            'queue_id': match_data['info']['queueId'],
            'timestamp': match_data['info'].get('gameStartTimestamp', 0),
        }
        
        # Extract Taric-specific data - basic info
        taric_data = {
            # Basic player info
            'player_team_id': taric_participant['teamId'],
            'player_win': taric_participant['win'],
            'player_position': taric_participant['teamPosition'],
            'player_lane': taric_participant['lane'],
            'individual_position': taric_participant.get('individualPosition', ''),
            'champion_level': taric_participant['champLevel'],
            'champion_transform': taric_participant.get('championTransform', 0),
            'champion_experience': taric_participant.get('champExperience', 0),
            
            # KDA and combat stats
            'kills': taric_participant['kills'],
            'deaths': taric_participant['deaths'],
            'assists': taric_participant['assists'],
            'kda': taric_participant.get('challenges', {}).get('kda', 0),
            'kill_participation': taric_participant.get('challenges', {}).get('killParticipation', 0),
            'multikills': taric_participant.get('challenges', {}).get('multikills', 0),
            'double_kills': taric_participant.get('doubleKills', 0),
            'triple_kills': taric_participant.get('tripleKills', 0),
            'quadra_kills': taric_participant.get('quadraKills', 0),
            'penta_kills': taric_participant.get('pentaKills', 0),
            'killing_sprees': taric_participant.get('killingSprees', 0),
            'largest_killing_spree': taric_participant.get('largestKillingSpree', 0),
            'largest_multi_kill': taric_participant.get('largestMultiKill', 0),
            
            # Damage metrics
            'damage_dealt_to_champions': taric_participant['totalDamageDealtToChampions'],
            'physical_damage_to_champions': taric_participant.get('physicalDamageDealtToChampions', 0),
            'magic_damage_to_champions': taric_participant.get('magicDamageDealtToChampions', 0),
            'true_damage_to_champions': taric_participant.get('trueDamageDealtToChampions', 0),
            'damage_taken': taric_participant['totalDamageTaken'],
            'physical_damage_taken': taric_participant.get('physicalDamageTaken', 0),
            'magic_damage_taken': taric_participant.get('magicDamageTaken', 0),
            'true_damage_taken': taric_participant.get('trueDamageTaken', 0),
            'damage_healed': taric_participant.get('totalHeal', 0) + taric_participant.get('totalHealsOnTeammates', 0),
            'damage_shielded': taric_participant.get('totalDamageShieldedOnTeammates', 0),
            'damage_self_mitigated': taric_participant.get('damageSelfMitigated', 0),
            'effective_heal_and_shielding': taric_participant.get('challenges', {}).get('effectiveHealAndShielding', 0),
            'team_damage_percentage': taric_participant.get('challenges', {}).get('teamDamagePercentage', 0),
            
            # Survival stats
            'time_CCing_others': taric_participant.get('timeCCingOthers', 0),
            'total_time_CC_dealt': taric_participant.get('totalTimeCCDealt', 0),
            'longest_time_spent_living': taric_participant.get('longestTimeSpentLiving', 0),
            'total_time_spent_dead': taric_participant.get('totalTimeSpentDead', 0),
            'save_ally_from_death': taric_participant.get('challenges', {}).get('saveAllyFromDeath', 0),
            'survived_three_immobilizes_in_fight': taric_participant.get('challenges', {}).get('survivedThreeImmobilizesInFight', 0),
            
            # Ability usage
            'spell1_casts': taric_participant.get('spell1Casts', 0),  # Q - Starlight's Touch
            'spell2_casts': taric_participant.get('spell2Casts', 0),  # W - Bastion
            'spell3_casts': taric_participant.get('spell3Casts', 0),  # E - Dazzle
            'spell4_casts': taric_participant.get('spell4Casts', 0),  # R - Cosmic Radiance
            'summoner1_casts': taric_participant.get('summoner1Casts', 0),
            'summoner2_casts': taric_participant.get('summoner2Casts', 0),
            'enemy_champion_immobilizations': taric_participant.get('challenges', {}).get('enemyChampionImmobilizations', 0),
            'immobilize_and_kill_with_ally': taric_participant.get('challenges', {}).get('immobilizeAndKillWithAlly', 0),
            'skillshots_dodged': taric_participant.get('challenges', {}).get('skillshotsDodged', 0),
            'skillshots_hit': taric_participant.get('challenges', {}).get('skillshotsHit', 0),
            
            # Vision
            'vision_score': taric_participant['visionScore'],
            'vision_score_per_minute': taric_participant.get('challenges', {}).get('visionScorePerMinute', 0),
            'vision_wards_bought': taric_participant['visionWardsBoughtInGame'],
            'detector_wards_placed': taric_participant.get('detectorWardsPlaced', 0),
            'stealth_wards_placed': taric_participant.get('challenges', {}).get('stealthWardsPlaced', 0),
            'wards_placed': taric_participant['wardsPlaced'],
            'wards_killed': taric_participant['wardsKilled'],
            'control_wards_placed': taric_participant.get('challenges', {}).get('controlWardsPlaced', 0),
            'ward_takedowns': taric_participant.get('challenges', {}).get('wardTakedowns', 0),
            'ward_takedowns_before_20m': taric_participant.get('challenges', {}).get('wardTakedownsBefore20M', 0),
            
            # Economy
            'gold_earned': taric_participant['goldEarned'],
            'gold_spent': taric_participant['goldSpent'],
            'gold_per_minute': taric_participant.get('challenges', {}).get('goldPerMinute', 0),
            'minions_killed': taric_participant['totalMinionsKilled'],
            'neutral_minions_killed': taric_participant.get('neutralMinionsKilled', 0),
            
            # Objective participation
            'objective_damage': taric_participant.get('damageDealtToObjectives', 0),
            'damage_dealt_to_buildings': taric_participant.get('damageDealtToBuildings', 0),
            'damage_dealt_to_turrets': taric_participant.get('damageDealtToTurrets', 0),
            'turret_kills': taric_participant.get('turretKills', 0),
            'turret_takedowns': taric_participant.get('turretTakedowns', 0),
            'inhibitor_kills': taric_participant.get('inhibitorKills', 0),
            'inhibitor_takedowns': taric_participant.get('inhibitorTakedowns', 0),
            'dragon_kills': taric_participant.get('dragonKills', 0),
            'dragon_takedowns': taric_participant.get('challenges', {}).get('dragonTakedowns', 0),
            'baron_kills': taric_participant.get('baronKills', 0),
            'baron_takedowns': taric_participant.get('challenges', {}).get('baronTakedowns', 0),
            'rift_herald_takedowns': taric_participant.get('challenges', {}).get('riftHeraldTakedowns', 0),
            
            # Items
            'item0': taric_participant['item0'],
            'item1': taric_participant['item1'],
            'item2': taric_participant['item2'],
            'item3': taric_participant['item3'],
            'item4': taric_participant['item4'],
            'item5': taric_participant['item5'],
            'item6': taric_participant['item6'],  # Trinket
            'items_purchased': taric_participant.get('itemsPurchased', 0),
            'consumables_purchased': taric_participant.get('consumablesPurchased', 0),
            
            # Communication
            'pings_total': sum([
                taric_participant.get('allInPings', 0),
                taric_participant.get('assistMePings', 0),
                taric_participant.get('basicPings', 0),
                taric_participant.get('commandPings', 0),
                taric_participant.get('dangerPings', 0),
                taric_participant.get('enemyMissingPings', 0),
                taric_participant.get('enemyVisionPings', 0),
                taric_participant.get('getBackPings', 0),
                taric_participant.get('holdPings', 0),
                taric_participant.get('needVisionPings', 0),
                taric_participant.get('onMyWayPings', 0),
                taric_participant.get('pushPings', 0),
                taric_participant.get('visionClearedPings', 0)
            ]),
            'all_in_pings': taric_participant.get('allInPings', 0),
            'assist_me_pings': taric_participant.get('assistMePings', 0),
            'basic_pings': taric_participant.get('basicPings', 0),
            'command_pings': taric_participant.get('commandPings', 0),
            'danger_pings': taric_participant.get('dangerPings', 0),
            'enemy_missing_pings': taric_participant.get('enemyMissingPings', 0),
            'enemy_vision_pings': taric_participant.get('enemyVisionPings', 0),
            'get_back_pings': taric_participant.get('getBackPings', 0),
            'hold_pings': taric_participant.get('holdPings', 0),
            'need_vision_pings': taric_participant.get('needVisionPings', 0),
            'on_my_way_pings': taric_participant.get('onMyWayPings', 0),
            'push_pings': taric_participant.get('pushPings', 0),
            'vision_cleared_pings': taric_participant.get('visionClearedPings', 0),
            
            # Runes and summoner spells
            'summoner1_id': taric_participant['summoner1Id'],
            'summoner2_id': taric_participant['summoner2Id'],
            'primary_rune_style': taric_participant.get('perks', {}).get('styles', [{}])[0].get('style', 0) if 'perks' in taric_participant else 0,
            'secondary_rune_style': taric_participant.get('perks', {}).get('styles', [{}, {}])[1].get('style', 0) if 'perks' in taric_participant else 0,
            
            # Game state
            'bounty_level': taric_participant.get('bountyLevel', 0),
            'time_played': taric_participant.get('timePlayed', 0)
        }
        
        # Combine match info and Taric data
        combined_data = {**match_info, **taric_data}
        
        return combined_data
    
    except Exception as e:
        print(f"Error processing match: {e}")
        return None

def process_all_matches():
    """
    Process all raw match data files and extract Taric information.
    
    Returns:
        pandas.DataFrame: DataFrame with processed Taric data
    """
    # Create cleaned data directory if it doesn't exist
    CLEANED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # Get all match files
    match_files = list(RAW_DATA_DIR.glob('*.json'))
    
    if not match_files:
        print(f"No match files found in {RAW_DATA_DIR}")
        return None
    
    print(f"Processing {len(match_files)} match files...")
    
    # Process each file
    taric_data_list = []
    for match_file in match_files:
        try:
            with open(match_file, 'r', encoding='utf-8') as f:
                match_data = json.load(f)
            
            taric_data = extract_taric_data(match_data)
            if taric_data:
                taric_data_list.append(taric_data)
        
        except Exception as e:
            print(f"Error loading {match_file}: {e}")
    
    if not taric_data_list:
        print("No Taric data extracted from matches")
        return None
    
    # Convert to DataFrame
    df = pd.DataFrame(taric_data_list)
    
    # Save to CSV
    output_file = CLEANED_DATA_DIR / 'taric_matches.csv'
    df.to_csv(output_file, index=False)
    
    print(f"Processed data saved to {output_file}")
    
    return df

def main():
    """Main function to process match data."""
    print("Processing Taric match data...")
    taric_df = process_all_matches()
    
    if taric_df is not None:
        print(f"Successfully processed {len(taric_df)} Taric matches")
        
        # Print basic statistics
        print("\nBasic Statistics:")
        print(f"Win Rate: {taric_df['player_win'].mean():.2%}")
        print(f"Average KDA: {taric_df['kda'].mean():.2f}")
        print(f"Average Vision Score: {taric_df['vision_score'].mean():.2f}")
        print(f"Most Common Position: {taric_df['player_position'].value_counts().index[0]}")
    else:
        print("No data was processed")

if __name__ == "__main__":
    main() 