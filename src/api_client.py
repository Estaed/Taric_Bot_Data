"""
API client for interacting with the Riot Games API.
Handles authentication, rate limiting, and data fetching for League of Legends data.
"""

import os
import time
import json
import requests
from pathlib import Path
from datetime import datetime

from src.config import RIOT_API_KEY, RAW_DATA_DIR

# Constants
REGIONS = ["na1", "euw1", "eun1", "kr", "br1", "jp1", "ru", "oc1", "tr1", "la1", "la2"]
ROUTE_REGIONS = {
    "na1": "americas",
    "br1": "americas",
    "la1": "americas",
    "la2": "americas",
    "euw1": "europe",
    "eun1": "europe",
    "tr1": "europe",
    "ru": "europe",
    "kr": "asia",
    "jp1": "asia",
    "oc1": "sea"
}

# Tier values for rank comparison
TIER_VALUES = {
    "IRON": 0,
    "BRONZE": 1,
    "SILVER": 2,
    "GOLD": 3,
    "PLATINUM": 4,
    "DIAMOND": 5,
    "MASTER": 6,
    "GRANDMASTER": 7,
    "CHALLENGER": 8
}

# Constants for Taric
TARIC_CHAMPION_ID = 44

class RiotApiClient:
    """Client for interacting with the Riot Games API."""
    
    def __init__(self, api_key=None):
        """
        Initialize the Riot API client.
        
        Args:
            api_key (str, optional): Riot API key. Defaults to environment variable.
        """
        if api_key is None:
            api_key = RIOT_API_KEY
        
        if not api_key:
            raise ValueError("API key is required. Please set RIOT_API_KEY environment variable.")
        
        self.api_key = api_key
        self.headers = {"X-Riot-Token": self.api_key}
        self.request_count = 0
        self.last_request_time = 0
        
        # Ensure data directory exists
        RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    def _handle_rate_limiting(self):
        """Handle rate limiting for API requests."""
        # Basic rate limiting
        # Riot API has different rate limits, but we'll use a simple approach
        self.request_count += 1
        
        # If it's been more than 2 minutes since our last request, reset the counter
        current_time = time.time()
        if current_time - self.last_request_time > 120:
            self.request_count = 1
        
        # If we've made 20 requests in the last 2 minutes, wait before making more
        if self.request_count >= 20:
            sleep_time = 120 - (current_time - self.last_request_time)
            if sleep_time > 0:
                print(f"Rate limit approaching. Sleeping for {sleep_time:.2f} seconds...")
                time.sleep(sleep_time)
                self.request_count = 1
        
        # If it's been less than 1.5 seconds since our last request, wait
        # This ensures we don't exceed the 20 requests per second limit
        if current_time - self.last_request_time < 1.5:
            time.sleep(1.5 - (current_time - self.last_request_time))
        
        self.last_request_time = time.time()
    
    def _make_request(self, endpoint, params=None):
        """
        Make a request to the Riot API with rate limiting.
        
        Args:
            endpoint (str): API endpoint to request
            params (dict, optional): Query parameters. Defaults to None.
            
        Returns:
            dict: JSON response from the API
        """
        self._handle_rate_limiting()
        
        response = requests.get(endpoint, headers=self.headers, params=params)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:
            # Rate limited, wait and retry
            retry_after = int(response.headers.get('Retry-After', 10))
            print(f"Rate limited. Retrying after {retry_after} seconds...")
            time.sleep(retry_after + 1)  # Add 1 second buffer
            return self._make_request(endpoint, params)
        elif response.status_code == 404:
            # Resource not found
            return None
        else:
            # Other errors
            print(f"Error: {response.status_code} - {response.text}")
            return None
    
    def get_summoner_by_riot_id(self, game_name, tag_line, region="na1"):
        """
        Get summoner data by Riot ID.
        
        Args:
            game_name (str): Game name part of Riot ID
            tag_line (str): Tag line part of Riot ID
            region (str, optional): Region to query. Defaults to "na1".
            
        Returns:
            dict: Summoner data or None if not found
        """
        endpoint = f"https://{region}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}"
        account_data = self._make_request(endpoint)
        
        if not account_data:
            return None
        
        # Get the summoner data using the puuid
        puuid = account_data.get("puuid")
        if not puuid:
            return None
        
        endpoint = f"https://{region}.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{puuid}"
        return self._make_request(endpoint)
    
    def get_matches_by_puuid(self, puuid, region="na1", count=20, queue_type=None, start_time=None, end_time=None):
        """
        Get match IDs for a player by PUUID.
        
        Args:
            puuid (str): Player's PUUID
            region (str, optional): Region to query. Defaults to "na1".
            count (int, optional): Number of matches to fetch. Defaults to 20.
            queue_type (int, optional): Queue type filter. Defaults to None.
            start_time (int, optional): Start time in epoch seconds. Defaults to None.
            end_time (int, optional): End time in epoch seconds. Defaults to None.
            
        Returns:
            list: List of match IDs
        """
        route_region = ROUTE_REGIONS.get(region, "americas")
        endpoint = f"https://{route_region}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids"
        
        params = {
            "count": count
        }
        
        if queue_type:
            params["queue"] = queue_type
        
        if start_time:
            params["startTime"] = start_time
        
        if end_time:
            params["endTime"] = end_time
        
        return self._make_request(endpoint, params)
    
    def get_match_by_id(self, match_id, region="americas"):
        """
        Get match data by match ID.
        
        Args:
            match_id (str): Match ID to fetch
            region (str, optional): Routing region to query. Defaults to "americas".
            
        Returns:
            dict: Match data or None if not found
        """
        endpoint = f"https://{region}.api.riotgames.com/lol/match/v5/matches/{match_id}"
        return self._make_request(endpoint)
    
    def get_summoner_ranked_info(self, summoner_id, region="na1"):
        """
        Get ranked information for a summoner.
        
        Args:
            summoner_id (str): Summoner ID
            region (str, optional): Region to query. Defaults to "na1".
            
        Returns:
            list: List of ranked queue data
        """
        endpoint = f"https://{region}.api.riotgames.com/lol/league/v4/entries/by-summoner/{summoner_id}"
        return self._make_request(endpoint)
    
    def get_champion_id(self, champion_name):
        """
        Get champion ID by name.
        For now, we'll just hardcode a few common ones.
        
        Args:
            champion_name (str): Champion name
            
        Returns:
            int: Champion ID or None if not found
        """
        # This is a hardcoded mapping for now
        # In a real implementation, you'd use the Data Dragon API
        champion_map = {
            "Taric": 44,
            "Ashe": 22,
            "Garen": 86,
            "Lux": 99,
            "Jinx": 222,
            "Yasuo": 157,
            "Yone": 777,
            "Master Yi": 11,
            "Yi": 11
        }
        
        return champion_map.get(champion_name)
    
    def _has_taric_in_match(self, match_data):
        """
        Check if Taric is in a match.
        
        Args:
            match_data (dict): Match data from Riot API
            
        Returns:
            bool: True if Taric is in the match, False otherwise
        """
        if not match_data or not match_data.get("info", {}).get("participants"):
            return False
        
        for participant in match_data["info"]["participants"]:
            if participant.get("championId") == TARIC_CHAMPION_ID:
                return True
        
        return False
    
    def _is_high_enough_tier(self, summoner_id, region="na1", min_tier="DIAMOND"):
        """
        Check if a summoner is at or above a specified tier.
        
        Args:
            summoner_id (str): Summoner ID
            region (str, optional): Region to query. Defaults to "na1".
            min_tier (str, optional): Minimum tier to check. Defaults to "DIAMOND".
            
        Returns:
            bool: True if the summoner is at or above the tier, False otherwise
        """
        if not min_tier or min_tier not in TIER_VALUES:
            return True  # No tier filter
            
        ranked_info = self.get_summoner_ranked_info(summoner_id, region)
        
        if not ranked_info:
            return False
        
        # Check all ranked queues
        for queue_data in ranked_info:
            tier = queue_data.get("tier", "")
            if TIER_VALUES.get(tier, -1) >= TIER_VALUES.get(min_tier, 0):
                return True
        
        return False
    
    def collect_taric_data_for_player(self, game_name, tag_line, region="na1", count=20, queue_type=None, min_tier=None, save_to_file=True):
        """
        Collect Taric match data for a specific player.
        
        Args:
            game_name (str): Game name part of Riot ID
            tag_line (str): Tag line part of Riot ID
            region (str, optional): Region to query. Defaults to "na1".
            count (int, optional): Number of matches to fetch. Defaults to 20.
            queue_type (int, optional): Queue type filter. Defaults to None.
            min_tier (str, optional): Minimum tier to collect. Defaults to None.
            save_to_file (bool, optional): Whether to save match data to file. Defaults to True.
            
        Returns:
            list: List of Taric match data
        """
        # Get summoner data
        summoner = self.get_summoner_by_riot_id(game_name, tag_line, region)
        
        if not summoner:
            print(f"Summoner {game_name}#{tag_line} not found in region {region}")
            return []
        
        # Check if summoner is high enough tier
        if min_tier and not self._is_high_enough_tier(summoner["id"], region, min_tier):
            print(f"Summoner {game_name}#{tag_line} is not {min_tier}+ tier")
            return []
        
        print(f"Found player {game_name}#{tag_line} with PUUID: {summoner['puuid']}")
        
        # Get match IDs
        match_ids = self.get_matches_by_puuid(
            summoner["puuid"], 
            region=region, 
            count=100,  # Get more matches to filter for Taric
            queue_type=queue_type
        )
        
        if not match_ids:
            print(f"No matches found for {game_name}#{tag_line}")
            return []
        
        # Filter for Taric matches
        taric_matches = []
        route_region = ROUTE_REGIONS.get(region, "americas")
        
        for match_id in match_ids:
            # Check if we already have enough Taric matches
            if len(taric_matches) >= count:
                break
                
            # Get match data
            match_data = self.get_match_by_id(match_id, route_region)
            
            # Check if match has Taric
            if not match_data or not self._has_taric_in_match(match_data):
                continue
                
            # Add match data to list
            taric_matches.append(match_data)
            print(f"Found Taric in match {match_id}")
            
            # Save match data to file
            if save_to_file:
                self._save_match_data_to_file(match_data)
        
        print(f"Found {len(taric_matches)} Taric matches for {game_name}#{tag_line}")
        
        return taric_matches
    
    def fetch_high_elo_taric_matches(self, queue=420, tier="DIAMOND", count=20, save_to_file=True):
        """
        Collect high ELO Taric games directly.
        
        Args:
            queue (int, optional): Queue type filter. Defaults to 420 (ranked solo/duo).
            tier (str, optional): Minimum tier to collect. Defaults to "DIAMOND".
            count (int, optional): Number of matches to fetch. Defaults to 20.
            save_to_file (bool, optional): Whether to save data to files. Defaults to True.
            
        Returns:
            list: List of match data
        """
        # Implementation would fetch matches from ranked leaderboards
        print(f"This method would ideally fetch {count} Taric matches from {tier}+ ranked games")
        print("For now, returning an empty list as this requires additional API endpoints")
        return []
        
    def fetch_top_taric_players(self, region="na1", min_tier="DIAMOND", count=10):
        """
        Find the top Taric players in a region with a minimum tier.
        
        Args:
            region (str): Region to query
            min_tier (str): Minimum tier to include ("DIAMOND", "MASTER", etc.)
            count (int): Maximum number of players to return
            
        Returns:
            list: List of player dictionaries with game_name and tag_line
        """
        players = []
        
        # Method 1: Check challenger/grandmaster/master leagues
        if min_tier in ["CHALLENGER", "GRANDMASTER", "MASTER"]:
            tiers_to_check = []
            
            if TIER_VALUES[min_tier] <= TIER_VALUES["CHALLENGER"]:
                tiers_to_check.append("challenger")
            if TIER_VALUES[min_tier] <= TIER_VALUES["GRANDMASTER"]:
                tiers_to_check.append("grandmaster")
            if TIER_VALUES[min_tier] <= TIER_VALUES["MASTER"]:
                tiers_to_check.append("master")
                
            for tier in tiers_to_check:
                if len(players) >= count:
                    break
                    
                endpoint = f"https://{region}.api.riotgames.com/lol/league/v4/{tier}leagues/by-queue/RANKED_SOLO_5x5"
                league_data = self._make_request(endpoint)
                
                if not league_data or "entries" not in league_data:
                    continue
                
                # Process each entry in the league
                for entry in league_data.get("entries", []):
                    if len(players) >= count:
                        break
                        
                    summoner_id = entry.get("summonerId")
                    if not summoner_id:
                        continue
                    
                    # Get summoner data
                    endpoint = f"https://{region}.api.riotgames.com/lol/summoner/v4/summoners/{summoner_id}"
                    summoner = self._make_request(endpoint)
                    
                    if not summoner or "puuid" not in summoner:
                        continue
                    
                    puuid = summoner.get("puuid")
                    
                    # Check if player plays Taric
                    route_region = ROUTE_REGIONS.get(region, "americas")
                    matches_endpoint = f"https://{route_region}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids"
                    matches = self._make_request(matches_endpoint, {"count": 20})
                    
                    if not matches:
                        continue
                    
                    # Check if any matches have Taric
                    is_taric_player = False
                    
                    for match_id in matches[:5]:  # Just check the first 5 matches
                        match_data = self.get_match_by_id(match_id, route_region)
                        
                        if not match_data or "info" not in match_data:
                            continue
                            
                        participants = match_data.get("info", {}).get("participants", [])
                        
                        for participant in participants:
                            if participant.get("puuid") == puuid and participant.get("championId") == TARIC_CHAMPION_ID:
                                is_taric_player = True
                                break
                                
                        if is_taric_player:
                            break
                    
                    if is_taric_player:
                        # Get Riot ID
                        account_endpoint = f"https://{region}.api.riotgames.com/riot/account/v1/accounts/by-puuid/{puuid}"
                        account_data = self._make_request(account_endpoint)
                        
                        if account_data and "gameName" in account_data and "tagLine" in account_data:
                            players.append({
                                "game_name": account_data.get("gameName"),
                                "tag_line": account_data.get("tagLine"),
                                "tier": tier.upper()
                            })
                            print(f"Found Taric player: {account_data.get('gameName')}#{account_data.get('tagLine')} ({tier.upper()})")
        
        # Method 2: If we need more players, check Diamond tier
        if len(players) < count and TIER_VALUES[min_tier] <= TIER_VALUES["DIAMOND"]:
            # Diamond has 4 divisions
            for division in ["I", "II", "III", "IV"]:
                if len(players) >= count:
                    break
                    
                endpoint = f"https://{region}.api.riotgames.com/lol/league/v4/entries/RANKED_SOLO_5x5/DIAMOND/{division}"
                entries = self._make_request(endpoint)
                
                if not entries:
                    continue
                
                for entry in entries:
                    if len(players) >= count:
                        break
                        
                    summoner_id = entry.get("summonerId")
                    if not summoner_id:
                        continue
                    
                    # Get summoner data
                    endpoint = f"https://{region}.api.riotgames.com/lol/summoner/v4/summoners/{summoner_id}"
                    summoner = self._make_request(endpoint)
                    
                    if not summoner or "puuid" not in summoner:
                        continue
                    
                    puuid = summoner.get("puuid")
                    
                    # Check if player plays Taric
                    route_region = ROUTE_REGIONS.get(region, "americas")
                    matches_endpoint = f"https://{route_region}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids"
                    matches = self._make_request(matches_endpoint, {"count": 20})
                    
                    if not matches:
                        continue
                    
                    # Check if any matches have Taric
                    is_taric_player = False
                    
                    for match_id in matches[:5]:  # Just check the first 5 matches
                        match_data = self.get_match_by_id(match_id, route_region)
                        
                        if not match_data or "info" not in match_data:
                            continue
                            
                        participants = match_data.get("info", {}).get("participants", [])
                        
                        for participant in participants:
                            if participant.get("puuid") == puuid and participant.get("championId") == TARIC_CHAMPION_ID:
                                is_taric_player = True
                                break
                                
                        if is_taric_player:
                            break
                    
                    if is_taric_player:
                        # Get Riot ID
                        account_endpoint = f"https://{region}.api.riotgames.com/riot/account/v1/accounts/by-puuid/{puuid}"
                        account_data = self._make_request(account_endpoint)
                        
                        if account_data and "gameName" in account_data and "tagLine" in account_data:
                            players.append({
                                "game_name": account_data.get("gameName"),
                                "tag_line": account_data.get("tagLine"),
                                "tier": "DIAMOND",
                                "division": division
                            })
                            print(f"Found Taric player: {account_data.get('gameName')}#{account_data.get('tagLine')} (DIAMOND {division})")
        
        return players[:count]
    
    def download_multiple_matches(self, match_ids, region="americas", save_to_file=True, taric_only=True):
        """
        Download multiple matches by ID.
        
        Args:
            match_ids (list): List of match IDs to download
            region (str, optional): Routing region. Defaults to "americas".
            save_to_file (bool, optional): Whether to save match data to files. Defaults to True.
            taric_only (bool, optional): Whether to only download matches with Taric. Defaults to True.
            
        Returns:
            list: List of match data
        """
        matches = []
        
        for match_id in match_ids:
            if not match_id:
                continue
                
            match_data = self.get_match_by_id(match_id, region)
            
            if not match_data:
                print(f"Match {match_id} not found")
                continue
                
            if taric_only and not self._has_taric_in_match(match_data):
                print(f"Taric not found in match {match_id}")
                continue
                
            matches.append(match_data)
            
            if save_to_file:
                self._save_match_data_to_file(match_data)
                
            # Print progress
            if len(matches) % 5 == 0:
                print(f"Downloaded {len(matches)} matches...")
        
        return matches
    
    def _save_match_data_to_file(self, match_data):
        """
        Save match data to a file.
        
        Args:
            match_data (dict): Match data to save
        """
        if not match_data or not match_data.get("metadata", {}).get("matchId"):
            return
            
        match_id = match_data["metadata"]["matchId"]
        file_path = RAW_DATA_DIR / f"{match_id}.json"
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(match_data, f, indent=2)