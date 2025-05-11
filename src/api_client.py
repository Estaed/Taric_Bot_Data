"""
Riot API client for fetching League of Legends match data.
"""

from riotwatcher import LolWatcher
import pandas as pd
import time
import json
from pathlib import Path
from datetime import datetime

from src.config import RIOT_API_KEY, RAW_DATA_DIR

class RiotApiClient:
    """Client for interacting with Riot Games API to fetch Taric data."""
    
    def __init__(self, api_key=None, region="na1"):
        """
        Initialize the API client.
        
        Args:
            api_key (str, optional): Riot API key. Defaults to the one in environment variables.
            region (str, optional): Server region. Defaults to "na1".
        """
        self.api_key = api_key or RIOT_API_KEY
        if not self.api_key:
            raise ValueError("Riot API key is required. Set it in .env file or pass to constructor.")
        
        self.region = region
        self.watcher = LolWatcher(self.api_key)
        self.taric_id = None  # Will be fetched when needed
    
    def get_champion_id(self, champion_name="Taric"):
        """Get the champion ID for a given champion name."""
        if self.taric_id is not None and champion_name.lower() == "taric":
            return self.taric_id
            
        # Get latest version
        versions = self.watcher.data_dragon.versions_for_region(self.region)
        champions_version = versions['n']['champion']
        
        # Get champion data
        champions = self.watcher.data_dragon.champions(champions_version)
        
        # Find champion by name
        for key, champion in champions['data'].items():
            if champion['name'].lower() == champion_name.lower():
                if champion_name.lower() == "taric":
                    self.taric_id = int(champion['key'])
                return int(champion['key'])
        
        raise ValueError(f"Champion {champion_name} not found!")
    
    def fetch_high_elo_taric_matches(self, queue=420, tier="DIAMOND", division="I", count=10):
        """
        Fetch high ELO matches with Taric.
        
        Args:
            queue (int, optional): Queue ID (e.g., 420 for ranked solo/duo). Defaults to 420.
            tier (str, optional): Tier to search. Defaults to "DIAMOND".
            division (str, optional): Division within tier. Defaults to "I".
            count (int, optional): Number of matches to fetch. Defaults to 10.
        
        Returns:
            list: List of match IDs with Taric
        """
        # Implementation will be completed in Phase 1
        # This is just a placeholder for the structure
        pass
    
    def download_match_data(self, match_id, save_to_file=True):
        """
        Download detailed match data.
        
        Args:
            match_id (str): Match ID to fetch
            save_to_file (bool, optional): Whether to save data to file. Defaults to True.
            
        Returns:
            dict: Match data
        """
        # Implementation will be completed in Phase 1
        # This is just a placeholder for the structure
        pass
    
    def save_match_data(self, match_data, file_name=None):
        """
        Save match data to a JSON file.
        
        Args:
            match_data (dict): Match data to save
            file_name (str, optional): File name. Defaults to match ID with timestamp.
            
        Returns:
            Path: Path to saved file
        """
        if file_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            match_id = match_data.get('metadata', {}).get('matchId', 'unknown')
            file_name = f"match_{match_id}_{timestamp}.json"
        
        file_path = RAW_DATA_DIR / file_name
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(match_data, f, ensure_ascii=False, indent=4)
        
        return file_path