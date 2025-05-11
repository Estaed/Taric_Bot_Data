#!/usr/bin/env python
"""
Script to collect 100 Taric games from Estaed accounts.
"""

import os
import sys
import json
import requests
import urllib.parse
import time
from pathlib import Path
from datetime import datetime

# Create data directories if they don't exist
data_dir = Path("data/raw")
estaed_games_dir = data_dir / "Estaed games"

data_dir.mkdir(parents=True, exist_ok=True)
estaed_games_dir.mkdir(parents=True, exist_ok=True)

# Define game modes to include: Ranked Solo/Duo, Ranked Flex, Draft Pick, Swift Play
# Queue IDs: https://static.developer.riotgames.com/docs/lol/queues.json
VALID_QUEUE_IDS = [
    400,  # 5v5 Draft Pick
    420,  # 5v5 Ranked Solo/Duo
    440,  # 5v5 Ranked Flex
    940,  # Swift Play
    700   # Clash
]

# Taric's champion ID
TARIC_CHAMPION_ID = 44

# Rate limiting settings
RATE_LIMIT_WINDOW = 120  # 2 minutes to wait after hitting rate limit
MAX_RETRIES = 5

class RateLimiter:
    """Track and limit API requests based on Riot's rate limits."""
    def __init__(self):
        self.request_times = []
        self.retries = 0
        self.last_retry_time = datetime.now()
    
    def wait_if_needed(self):
        """Wait if we've hit rate limits recently."""
        # If we've recently hit a rate limit, ensure we wait
        now = datetime.now()
        if self.retries > 0:
            seconds_since_retry = (now - self.last_retry_time).total_seconds()
            if seconds_since_retry < RATE_LIMIT_WINDOW:
                wait_time = RATE_LIMIT_WINDOW - seconds_since_retry
                print(f"Waiting {wait_time:.1f} seconds due to recent rate limit...")
                time.sleep(wait_time)
                self.retries = 0
        
        # Always add a small delay between requests
        time.sleep(1.2)  # More conservative delay
    
    def handle_429(self):
        """Handle rate limit exceeded errors."""
        self.retries += 1
        wait_time = RATE_LIMIT_WINDOW * (2 ** min(self.retries, 3))  # Exponential backoff
        print(f"Rate limit exceeded! Waiting {wait_time:.1f} seconds before retrying...")
        self.last_retry_time = datetime.now()
        time.sleep(wait_time)

def make_api_request(url, headers, rate_limiter, max_retries=MAX_RETRIES):
    """Make API request with rate limiting and retry logic."""
    retry_count = 0
    
    while retry_count < max_retries:
        rate_limiter.wait_if_needed()
        
        try:
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                print(f"Rate limit exceeded (429) for URL: {url}")
                rate_limiter.handle_429()
                retry_count += 1
            elif response.status_code == 403:
                print(f"Forbidden (403) for URL: {url}")
                retry_count += 1
                time.sleep(5)
            elif response.status_code == 404:
                print(f"Not found (404) for URL: {url}")
                return None
            else:
                print(f"Error {response.status_code} for URL: {url}")
                retry_count += 1
                time.sleep(5)
        
        except requests.exceptions.RequestException as e:
            print(f"Request exception: {e}")
            retry_count += 1
            time.sleep(5)
    
    print(f"Failed after {max_retries} retries for URL: {url}")
    return None

def get_existing_games():
    """Get list of existing games and count them."""
    existing_match_ids = set()
    for file_path in estaed_games_dir.glob("*.json"):
        try:
            match_id = file_path.stem.split("_")[-1]
            existing_match_ids.add(match_id)
        except:
            continue
    
    return existing_match_ids

def is_taric_game(match_data, puuid):
    """Check if the match has Taric and he was played by the given account."""
    # Get match info
    info = match_data.get("info", {})
    
    # Check participants for Taric
    for participant in info.get("participants", []):
        if participant.get("puuid") == puuid and participant.get("championId") == TARIC_CHAMPION_ID:
            return True
    
    return False

def collect_estaed_data():
    """Collect 100 Taric games from Estaed accounts."""
    # Ask for API key
    print("\nIMPORTANT: You need a valid Development or Personal Riot API key (not Production).")
    print("Get your API key from: https://developer.riotgames.com/")
    print("NOTE: Development API keys expire in 24 hours.")
    api_key = input("Enter your Riot API key: ")
    
    if not api_key:
        print("No API key provided. Cannot collect data.")
        return
    
    # Set up headers
    headers = {"X-Riot-Token": api_key}
    
    # Initialize rate limiter
    rate_limiter = RateLimiter()
    
    # Define Estaed accounts with their target game counts
    accounts = [
        {"game_name": "Estaed", "tag_line": "TAR", "target_games": 50},
        {"game_name": "EstaedOCE", "tag_line": "9591", "target_games": 50}
    ]
    
    # Store Estaed PUUIDs and their target game counts
    estaed_puuids = []
    estaed_account_names = []
    estaed_target_games = []
    
    # Step 1: Look up all Estaed accounts
    print("\nStep 1: Looking up Estaed accounts...")
    
    # Prioritize regions
    regions = ["sea", "asia", "europe", "americas"]
    
    for account in accounts:
        game_name = urllib.parse.quote(account["game_name"])
        tag_line = urllib.parse.quote(account["tag_line"])
        
        found = False
        print(f"\nLooking for account: {account['game_name']}#{account['tag_line']}")
        
        for region in regions:
            # Using the recommended endpoint for getting PUUID from Riot ID
            account_url = f"https://{region}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}"
            print(f"Trying endpoint: {account_url}")
            
            account_data = make_api_request(account_url, headers, rate_limiter)
            if account_data and "puuid" in account_data:
                puuid = account_data.get("puuid")
                account_name = f"{account_data.get('gameName')}#{account_data.get('tagLine')}"
                print(f"Found account: {account_name}")
                print(f"PUUID: {puuid}")
                print(f"Found on region: {region}")
                estaed_puuids.append(puuid)
                estaed_account_names.append(account_name)
                estaed_target_games.append(account["target_games"])
                found = True
                break
        
        if not found:
            print(f"Could not find account: {account['game_name']}#{account['tag_line']}")
    
    if not estaed_puuids:
        print("\nCould not find any Estaed accounts")
        return
    
    print(f"\nFound {len(estaed_puuids)} Estaed accounts")
    
    # Step 2: Get existing games and count them
    existing_match_ids = get_existing_games()
    existing_games_count = len(existing_match_ids)
    print(f"Found {existing_games_count} existing match files")
    
    # Track games per account
    games_per_account = {name: 0 for name in estaed_account_names}
    
    # Count existing games per account
    for match_id in existing_match_ids:
        file_paths = list(estaed_games_dir.glob(f"*_{match_id}.json"))
        if not file_paths:
            continue
        
        file_path = file_paths[0]
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                match_data = json.load(f)
            
            for i, puuid in enumerate(estaed_puuids):
                if is_taric_game(match_data, puuid):
                    games_per_account[estaed_account_names[i]] += 1
                    break
        except Exception as e:
            print(f"Error counting games for {match_id}: {e}")
    
    # Print current game counts per account
    print("\nCurrent game counts per account:")
    for account_name in estaed_account_names:
        print(f"{account_name}: {games_per_account[account_name]} games")
    
    # Check if we need to validate existing games
    if existing_games_count > 0:
        validate = input("\nDo you want to check if existing games are Taric games? (y/n): ").lower() == 'y'
        if validate:
            print("\nValidating existing games...")
            valid_games = set()
            for match_id in existing_match_ids:
                file_paths = list(estaed_games_dir.glob(f"*_{match_id}.json"))
                if not file_paths:
                    continue
                
                file_path = file_paths[0]
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        match_data = json.load(f)
                    
                    is_valid = False
                    for puuid in estaed_puuids:
                        if is_taric_game(match_data, puuid):
                            is_valid = True
                            break
                    
                    if not is_valid:
                        print(f"Match {match_id} is not a Taric game, will be deleted")
                        os.remove(file_path)
                    else:
                        valid_games.add(match_id)
                        
                except Exception as e:
                    print(f"Error validating {match_id}: {e}")
            
            existing_match_ids = valid_games
            existing_games_count = len(existing_match_ids)
            print(f"After validation: {existing_games_count} valid Taric games")
    
    total_games_target = sum(estaed_target_games)
    total_games_collected = sum(games_per_account.values())
    
    if total_games_collected >= total_games_target:
        print(f"\nAlready have {total_games_collected} Taric games, target is {total_games_target}")
        print("No need to collect more games.")
        return
    
    print(f"\nNeed to collect {total_games_target - total_games_collected} more Taric games")
    
    # Step 3: Collect games from each Estaed account
    print("\nStep 3: Collecting Taric games from Estaed accounts...")
    
    # For SEA players, matches are in the SEA region
    match_region = "sea"
    
    # Parameters for pagination
    batch_size = 100  # Maximum allowed by API
    
    # Track games
    checked_match_ids = set()  # To avoid checking the same match twice
    
    # Process each Estaed account
    for i, puuid in enumerate(estaed_puuids):
        account_name = estaed_account_names[i]
        target_games = accounts[i]["target_games"]
        current_games = games_per_account[account_name]
        
        if current_games >= target_games:
            print(f"\nAlready have {current_games} games for {account_name}, target is {target_games}")
            continue
            
        simple_name = account_name.split("#")[0]  # Just the name part
        print(f"\nCollecting Taric games for {account_name} (Target: {target_games}, Current: {current_games})")
        
        start_index = 0
        account_games_collected = 0
        max_start_index = 1000  # Safety limit to prevent infinite loops
        
        while current_games + account_games_collected < target_games and start_index < max_start_index:
            # Get a batch of match IDs
            matches_url = f"https://{match_region}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?start={start_index}&count={batch_size}"
            
            print(f"Getting matches {start_index} to {start_index + batch_size - 1}...")
            match_ids = make_api_request(matches_url, headers, rate_limiter)
            
            if not match_ids:
                print(f"No more matches found for {account_name} or rate limit reached")
                # Wait a bit before trying the next account
                time.sleep(10)
                break
                
            # Process each match
            for match_id in match_ids:
                # Skip if we've already processed this match
                if match_id in checked_match_ids or match_id in existing_match_ids:
                    print(f"Match {match_id} already processed, skipping")
                    continue
                
                checked_match_ids.add(match_id)
                
                print(f"Processing match {match_id}...")
                match_url = f"https://{match_region}.api.riotgames.com/lol/match/v5/matches/{match_id}"
                
                match_data = make_api_request(match_url, headers, rate_limiter)
                if not match_data:
                    print(f"Could not get data for match {match_id}")
                    continue
                
                # Get match info
                info = match_data.get("info", {})
                
                # Check if the match is a valid queue type
                queue_id = info.get("queueId")
                map_id = info.get("mapId")
                
                if queue_id not in VALID_QUEUE_IDS or map_id != 11:  # 11 is Summoner's Rift
                    print(f"Skipping match {match_id}: Not a valid game mode (Queue: {queue_id}, Map: {map_id})")
                    continue
                
                # Check if Taric was played by this account
                if not is_taric_game(match_data, puuid):
                    print(f"Skipping match {match_id}: Taric was not played by {account_name}")
                    continue
                
                # Save the match
                file_name = f"{simple_name}_{match_id}.json"
                file_path = estaed_games_dir / file_name
                
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(match_data, f, indent=2)
                
                account_games_collected += 1
                print(f"Saved Taric game {match_id} - Progress: {current_games + account_games_collected}/{target_games} games for {account_name}")
                
                if current_games + account_games_collected >= target_games:
                    print(f"Reached target of {target_games} Taric games for {account_name}!")
                    break
            
            # Move to the next batch
            start_index += batch_size
        
        print(f"Collected {account_games_collected} Taric games for {account_name}")
    
    # Summary
    print(f"\nData collection complete!")
    print("\nFinal game counts per account:")
    for account_name in estaed_account_names:
        print(f"{account_name}: {games_per_account[account_name]} games")
    print(f"\nGames saved to {estaed_games_dir}")

if __name__ == "__main__":
    collect_estaed_data() 