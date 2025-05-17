"""
File organization utilities for the metrics extraction system.

This module provides functions to organize, sort, and clean up generated files.
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

def organize_state_action_files(input_dir, output_dir=None, by_date=True, by_match_id=False):
    """
    Organize state-action pair files into subdirectories.
    
    Args:
        input_dir (str): Directory containing state-action pair files
        output_dir (str, optional): Output directory. If None, uses input_dir.
        by_date (bool): Whether to organize by date (YYYY-MM-DD)
        by_match_id (bool): Whether to organize by match ID
        
    Returns:
        int: Number of files organized
    """
    if output_dir is None:
        output_dir = input_dir
    
    # Ensure Path objects
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    
    # Find all state-action pair files
    sa_files = list(input_dir.glob("**/taric_sa_pairs_*.json"))
    
    if not sa_files:
        logger.warning(f"No state-action pair files found in {input_dir}")
        return 0
    
    # Create a list to store (source, destination) tuples
    file_moves = []
    
    # Determine organization structure
    for file_path in sa_files:
        # Skip if already in a subdirectory structure (unless forced to reorganize)
        if len(file_path.parts) > len(input_dir.parts) + 1 and output_dir == input_dir:
            continue
        
        # Get file creation/modification time
        if by_date:
            file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
            date_str = file_time.strftime("%Y-%m-%d")
        
        # Extract match ID from filename
        match_id = None
        if by_match_id:
            # Example filename: taric_sa_pairs_OC1_666436490_20250515_195729.json
            match_pattern = re.search(r'taric_sa_pairs_([A-Z]+\d+_\d+)', file_path.name)
            if match_pattern:
                match_id = match_pattern.group(1)
            else:
                # Try alternate pattern: taric_sa_pairs_666436490_20250515_195729.json
                match_pattern = re.search(r'taric_sa_pairs_(\d+)', file_path.name)
                if match_pattern:
                    match_id = match_pattern.group(1)
        
        # Determine destination directory
        if by_date and by_match_id and match_id:
            dest_dir = output_dir / "by_date" / date_str / match_id
        elif by_date:
            dest_dir = output_dir / "by_date" / date_str
        elif by_match_id and match_id:
            dest_dir = output_dir / "by_match" / match_id
        else:
            dest_dir = output_dir
        
        # Create destination directory
        dest_dir.mkdir(parents=True, exist_ok=True)
        
        # Add to move list
        dest_file = dest_dir / file_path.name
        if file_path != dest_file:
            file_moves.append((file_path, dest_file))
    
    # Execute file moves
    for src, dest in file_moves:
        try:
            # Ensure directory exists
            dest.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy file if source and destination are different
            if src != dest:
                shutil.copy2(src, dest)
                
                # Remove original if successful and we're organizing in place
                if output_dir == input_dir:
                    src.unlink()
                
                logger.debug(f"Moved {src} to {dest}")
                
        except Exception as e:
            logger.error(f"Error moving {src} to {dest}: {e}")
    
    logger.info(f"Organized {len(file_moves)} state-action pair files")
    return len(file_moves)

def organize_metric_files(input_dir, output_dir=None, by_date=True, by_match_id=False):
    """
    Organize metric files into subdirectories.
    
    Args:
        input_dir (str): Directory containing metric files
        output_dir (str, optional): Output directory. If None, uses input_dir.
        by_date (bool): Whether to organize by date (YYYY-MM-DD)
        by_match_id (bool): Whether to organize by match ID
        
    Returns:
        int: Number of files organized
    """
    if output_dir is None:
        output_dir = input_dir
    
    # Ensure Path objects
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    
    # Find all metric files
    metric_files = list(input_dir.glob("**/taric_metrics_*.json"))
    
    if not metric_files:
        logger.warning(f"No metric files found in {input_dir}")
        return 0
    
    # Create a list to store (source, destination) tuples
    file_moves = []
    
    # Determine organization structure
    for file_path in metric_files:
        # Skip if already in a subdirectory structure (unless forced to reorganize)
        if len(file_path.parts) > len(input_dir.parts) + 1 and output_dir == input_dir:
            continue
        
        # Get file creation/modification time
        if by_date:
            file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
            date_str = file_time.strftime("%Y-%m-%d")
        
        # Extract match ID from filename
        match_id = None
        if by_match_id:
            # Example filename: taric_metrics_OC1_666436490.json
            match_pattern = re.search(r'taric_metrics_([A-Z]+\d+_\d+)', file_path.name)
            if match_pattern:
                match_id = match_pattern.group(1)
            else:
                # Try alternate pattern: taric_metrics_666436490.json
                match_pattern = re.search(r'taric_metrics_(\d+)', file_path.name)
                if match_pattern:
                    match_id = match_pattern.group(1)
        
        # Determine destination directory
        if by_date and by_match_id and match_id:
            dest_dir = output_dir / "by_date" / date_str / match_id
        elif by_date:
            dest_dir = output_dir / "by_date" / date_str
        elif by_match_id and match_id:
            dest_dir = output_dir / "by_match" / match_id
        else:
            dest_dir = output_dir
        
        # Create destination directory
        dest_dir.mkdir(parents=True, exist_ok=True)
        
        # Add to move list
        dest_file = dest_dir / file_path.name
        if file_path != dest_file:
            file_moves.append((file_path, dest_file))
    
    # Execute file moves
    for src, dest in file_moves:
        try:
            # Ensure directory exists
            dest.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy file if source and destination are different
            if src != dest:
                shutil.copy2(src, dest)
                
                # Remove original if successful and we're organizing in place
                if output_dir == input_dir:
                    src.unlink()
                
                logger.debug(f"Moved {src} to {dest}")
                
        except Exception as e:
            logger.error(f"Error moving {src} to {dest}: {e}")
    
    logger.info(f"Organized {len(file_moves)} metric files")
    return len(file_moves)

def cleanup_unorganized_files(directory, file_pattern):
    """
    Remove unorganized files (that are not in subdirectories).
    
    Args:
        directory (str): Directory to clean up
        file_pattern (str): File pattern to match
        
    Returns:
        int: Number of files removed
    """
    directory = Path(directory)
    
    # Find files directly in the directory (not in subdirectories)
    files = [f for f in directory.glob(file_pattern) if f.parent == directory]
    
    if not files:
        logger.info(f"No unorganized files found in {directory}")
        return 0
    
    count = 0
    for file_path in files:
        try:
            file_path.unlink()
            count += 1
            logger.debug(f"Removed {file_path}")
        except Exception as e:
            logger.error(f"Error removing {file_path}: {e}")
    
    logger.info(f"Removed {count} unorganized files from {directory}")
    return count

def main():
    """
    Command-line interface for file organization.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Organize state-action pairs and metric files")
    parser.add_argument("--sa-dir", help="Directory containing state-action pair files")
    parser.add_argument("--metrics-dir", help="Directory containing metric files")
    parser.add_argument("--by-date", action="store_true", default=True, help="Organize by date")
    parser.add_argument("--by-match", action="store_true", help="Organize by match ID")
    parser.add_argument("--cleanup", action="store_true", help="Clean up unorganized files after organizing")
    
    args = parser.parse_args()
    
    if args.sa_dir:
        organize_state_action_files(args.sa_dir, by_date=args.by_date, by_match_id=args.by_match)
        if args.cleanup:
            cleanup_unorganized_files(args.sa_dir, "taric_sa_pairs_*.json")
    
    if args.metrics_dir:
        organize_metric_files(args.metrics_dir, by_date=args.by_date, by_match_id=args.by_match)
        if args.cleanup:
            cleanup_unorganized_files(args.metrics_dir, "taric_metrics_*.json")

if __name__ == "__main__":
    main() 