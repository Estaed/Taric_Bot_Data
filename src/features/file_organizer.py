"""
File organization module for Taric Bot AI.

This module provides functions to organize state-action pairs and feature files
into appropriate subdirectories based on their content and metadata.
"""

import os
import json
import shutil
from pathlib import Path
import logging
from datetime import datetime
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def organize_state_action_files(input_dir, output_dir=None, create_backup=True):
    """
    Organize state-action pair files into a structured directory hierarchy.
    
    Organization structure:
    - By patch version
    - By game mode
    - By champion matchup
    
    Args:
        input_dir (str): Directory containing state-action pair JSON files
        output_dir (str, optional): Directory to organize files into. If None, uses input_dir
        create_backup (bool): Whether to create backup of original files
        
    Returns:
        dict: Summary of organization results
    """
    # Setup directories
    input_dir = Path(input_dir)
    if output_dir is None:
        output_dir = input_dir
    else:
        output_dir = Path(output_dir)
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Create backup if requested
    if create_backup:
        backup_dir = input_dir / "backup_sa_pairs"
        os.makedirs(backup_dir, exist_ok=True)
        logger.info(f"Creating backup in {backup_dir}")
        
        # Copy all JSON files to backup
        for file_path in input_dir.glob("taric_sa_pairs_*.json"):
            shutil.copy2(file_path, backup_dir / file_path.name)
    
    # Track organization results
    results = {
        "total_files": 0,
        "organized_files": 0,
        "skipped_files": 0,
        "by_patch": {},
        "by_game_mode": {},
        "by_matchup": {}
    }
    
    # Process each state-action pair file
    for file_path in input_dir.glob("taric_sa_pairs_*.json"):
        results["total_files"] += 1
        
        try:
            # Load file to extract metadata
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract organization metadata
            metadata = data.get("metadata", {})
            match_data = data.get("match_data", {})
            
            patch_version = metadata.get("patch_version", "unknown_patch")
            game_mode = metadata.get("queue_id", "unknown_mode")
            match_id = metadata.get("match_id", "unknown_match")
            
            # Clean patch version for directory name
            patch_version = re.sub(r'[^0-9.]', '', patch_version)
            
            # Determine game mode name from queue ID
            game_mode_name = {
                "400": "draft",
                "420": "ranked_solo",
                "430": "blind",
                "440": "ranked_flex",
                "450": "aram",
                "700": "clash",
                "900": "urf",
                "1020": "one_for_all"
            }.get(str(game_mode), f"mode_{game_mode}")
            
            # Extract champion matchup
            ally_champions = []
            enemy_champions = []
            
            # Get champions from team data
            for team in match_data.get("teams", []):
                is_player_team = any(p.get("summoner_name") == metadata.get("player_name") 
                                    for p in team.get("participants", []))
                
                for participant in team.get("participants", []):
                    champion = participant.get("champion_name", "unknown")
                    if is_player_team:
                        ally_champions.append(champion)
                    else:
                        enemy_champions.append(champion)
            
            # Create directory structure
            # /patch_13.10/ranked_solo/taric_ezreal_vs_thresh_jinx/
            ally_champions.sort()
            enemy_champions.sort()
            
            # Ensure Taric is first in ally champions list
            if "Taric" in ally_champions:
                ally_champions.remove("Taric")
                ally_champions.insert(0, "Taric")
            
            ally_str = "_".join(ally_champions).lower()
            enemy_str = "_".join(enemy_champions).lower()
            matchup_dir = f"{ally_str}_vs_{enemy_str}"
            
            # Create organized directory path
            organize_path = output_dir / f"patch_{patch_version}" / game_mode_name / matchup_dir
            os.makedirs(organize_path, exist_ok=True)
            
            # Create new filename with match timestamp
            match_date = metadata.get("match_date", "")
            if match_date:
                try:
                    # Convert ISO date to more readable format
                    date_obj = datetime.fromisoformat(match_date.replace('Z', '+00:00'))
                    date_str = date_obj.strftime("%Y%m%d")
                    new_filename = f"taric_sa_pairs_{date_str}_{match_id}.json"
                except:
                    new_filename = file_path.name
            else:
                new_filename = file_path.name
            
            # Move the file
            destination = organize_path / new_filename
            if output_dir == input_dir:
                # Move the file if organizing in place
                shutil.move(file_path, destination)
            else:
                # Copy the file if organizing to a different location
                shutil.copy2(file_path, destination)
            
            # Update results
            results["organized_files"] += 1
            
            if patch_version not in results["by_patch"]:
                results["by_patch"][patch_version] = 0
            results["by_patch"][patch_version] += 1
            
            if game_mode_name not in results["by_game_mode"]:
                results["by_game_mode"][game_mode_name] = 0
            results["by_game_mode"][game_mode_name] += 1
            
            if matchup_dir not in results["by_matchup"]:
                results["by_matchup"][matchup_dir] = 0
            results["by_matchup"][matchup_dir] += 1
            
        except Exception as e:
            logger.error(f"Error organizing {file_path}: {str(e)}")
            results["skipped_files"] += 1
    
    logger.info(f"Organization complete: {results['organized_files']}/{results['total_files']} files organized")
    return results


def organize_feature_files(input_dir, output_dir=None, create_backup=True):
    """
    Organize feature files into a structured directory hierarchy.
    
    Args:
        input_dir (str): Directory containing feature JSON files
        output_dir (str, optional): Directory to organize files into. If None, uses input_dir
        create_backup (bool): Whether to create backup of original files
        
    Returns:
        dict: Summary of organization results
    """
    # Setup is similar to state-action pairs organization
    input_dir = Path(input_dir)
    if output_dir is None:
        output_dir = input_dir
    else:
        output_dir = Path(output_dir)
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Create backup if requested
    if create_backup:
        backup_dir = input_dir / "backup_features"
        os.makedirs(backup_dir, exist_ok=True)
        logger.info(f"Creating backup in {backup_dir}")
        
        # Copy all JSON files to backup
        for file_path in input_dir.glob("taric_features_*.json"):
            shutil.copy2(file_path, backup_dir / file_path.name)
    
    # Track organization results
    results = {
        "total_files": 0,
        "organized_files": 0,
        "skipped_files": 0,
        "by_metric_type": {}
    }
    
    # Process each feature file
    for file_path in input_dir.glob("taric_features_*.json"):
        results["total_files"] += 1
        
        try:
            # Load file to extract metadata
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract organization metadata
            metadata = data.get("metadata", {})
            match_id = metadata.get("match_id", "unknown_match")
            
            # Create metric-specific directories
            metrics = data.get("features", {})
            for metric_type in metrics.keys():
                metric_dir = output_dir / metric_type
                os.makedirs(metric_dir, exist_ok=True)
                
                # Create metric-specific file
                metric_data = {
                    "metadata": metadata,
                    "match_id": match_id,
                    metric_type: metrics[metric_type]
                }
                
                metric_filename = f"taric_{metric_type}_{match_id}.json"
                with open(metric_dir / metric_filename, 'w', encoding='utf-8') as f:
                    json.dump(metric_data, f, indent=2)
                
                # Update results
                if metric_type not in results["by_metric_type"]:
                    results["by_metric_type"][metric_type] = 0
                results["by_metric_type"][metric_type] += 1
            
            results["organized_files"] += 1
            
        except Exception as e:
            logger.error(f"Error organizing {file_path}: {str(e)}")
            results["skipped_files"] += 1
    
    logger.info(f"Feature organization complete: {results['organized_files']}/{results['total_files']} files organized")
    return results


def cleanup_unorganized_files(directory, file_pattern, keep_backup=True):
    """
    Clean up unorganized files after organization is complete.
    
    Args:
        directory (str): Directory containing files
        file_pattern (str): Glob pattern for files to clean up
        keep_backup (bool): Whether to keep backup directory
        
    Returns:
        int: Number of files cleaned up
    """
    directory = Path(directory)
    backup_dir = directory / f"backup_{file_pattern.split('_')[1]}"
    
    # Ensure backup exists before cleaning
    if not backup_dir.exists() and keep_backup:
        logger.warning(f"Backup directory {backup_dir} not found, skipping cleanup")
        return 0
    
    # Find and delete unorganized files
    count = 0
    for file_path in directory.glob(file_pattern):
        if file_path.parent == directory:  # Only remove files in the root directory
            file_path.unlink()
            count += 1
    
    logger.info(f"Cleaned up {count} unorganized files")
    return count


def main():
    """
    Command-line interface for file organization.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Organize Taric Bot AI files')
    parser.add_argument('--sa-dir', help='Directory containing state-action pair files')
    parser.add_argument('--feature-dir', help='Directory containing feature files')
    parser.add_argument('--no-backup', action='store_true', help='Skip creating backups')
    parser.add_argument('--cleanup', action='store_true', help='Clean up unorganized files after organization')
    
    args = parser.parse_args()
    
    if args.sa_dir:
        organize_state_action_files(args.sa_dir, create_backup=not args.no_backup)
        if args.cleanup:
            cleanup_unorganized_files(args.sa_dir, "taric_sa_pairs_*.json", keep_backup=not args.no_backup)
    
    if args.feature_dir:
        organize_feature_files(args.feature_dir, create_backup=not args.no_backup)
        if args.cleanup:
            cleanup_unorganized_files(args.feature_dir, "taric_features_*.json", keep_backup=not args.no_backup)


if __name__ == "__main__":
    main() 