#!/usr/bin/env python
"""
Feature Extraction Runner

This script provides a simple interface to run the entire feature extraction pipeline:
1. Processes state-action pairs
2. Extracts all metrics (combat, vision, positioning, game state, mechanics)
3. Organizes output files
4. Generates a summary report

Usage:
    python run_feature_extraction.py --input-dir [STATE_ACTION_DIR] --output-dir [OUTPUT_DIR]
"""

import os
import sys
import json
import time
import argparse
import logging
from pathlib import Path
from tqdm import tqdm
from datetime import datetime

# Import all metric modules
from src.features.combat_metrics import calculate_combat_metrics
from src.features.vision_metrics import calculate_vision_metrics
from src.features.positioning_metrics import calculate_positioning_metrics
from src.features.mechanics_metrics import calculate_mechanics_metrics
from src.features.game_state_metrics import calculate_game_state_metrics
from src.features.file_organizer import organize_feature_files, organize_state_action_files

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("feature_extraction.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def get_match_id_from_filename(filename):
    """Extract match ID from filename."""
    # Example: taric_sa_pairs_OC1_666436490_20250515_195729.json
    parts = os.path.basename(filename).replace('.json', '').split('_')
    # Return the match ID part
    return '_'.join(parts[2:4])  # OC1_666436490

def extract_features_from_file(file_path, output_dir):
    """Extract all features from a single state-action pair file."""
    logger.info(f"Processing file: {file_path}")
    
    try:
        # Load state-action pair data
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extract metadata and match data
        metadata = data.get('metadata', {})
        match_data = data.get('match_data', {})
        state_action_pairs = data.get('state_action_pairs', [])
        
        # Add start time for processing
        start_time = time.time()
        
        # Calculate all features
        logger.info("Calculating combat metrics...")
        combat_metrics = calculate_combat_metrics(state_action_pairs, match_data)
        
        logger.info("Calculating vision metrics...")
        vision_metrics = calculate_vision_metrics(state_action_pairs, match_data)
        
        logger.info("Calculating positioning metrics...")
        positioning_metrics = calculate_positioning_metrics(state_action_pairs, match_data)
        
        logger.info("Calculating mechanics metrics...")
        mechanics_metrics = calculate_mechanics_metrics(state_action_pairs, match_data)
        
        logger.info("Calculating game state metrics...")
        game_state_metrics = calculate_game_state_metrics(state_action_pairs, match_data)
        
        # Add end time and calculate duration
        end_time = time.time()
        processing_duration = end_time - start_time
        
        # Get match ID from metadata or filename
        match_id = metadata.get('match_id', get_match_id_from_filename(file_path))
        
        # Add processing metadata
        processing_metadata = {
            "processing_start_time": datetime.fromtimestamp(start_time).isoformat(),
            "processing_end_time": datetime.fromtimestamp(end_time).isoformat(),
            "processing_duration_seconds": processing_duration,
            "metrics_modules": [
                "combat_metrics",
                "vision_metrics",
                "positioning_metrics",
                "mechanics_metrics",
                "game_state_metrics"
            ]
        }
        
        # Combine all features
        all_features = {
            'metadata': {
                **metadata,
                'processing': processing_metadata
            },
            'match_id': match_id,
            'features': {
                'combat': combat_metrics,
                'vision': vision_metrics,
                'positioning': positioning_metrics,
                'mechanics': mechanics_metrics,
                'game_state': game_state_metrics
            }
        }
        
        # Generate output filename
        output_file = os.path.join(output_dir, f"taric_features_{match_id}.json")
        
        # Save features to file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_features, f, indent=2)
        
        logger.info(f"Successfully processed {file_path} in {processing_duration:.2f} seconds")
        return True
        
    except Exception as e:
        logger.error(f"Error processing {file_path}: {str(e)}")
        return False

def process_all_files(input_dir, output_dir, batch_size=5, organize_files=True):
    """Process all state-action pair files in the input directory."""
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Find all state-action pair files
    input_path = Path(input_dir)
    sa_files = list(input_path.glob("taric_sa_pairs_*.json"))
    
    if not sa_files:
        logger.warning(f"No state-action pair files found in {input_dir}")
        return 0
    
    logger.info(f"Found {len(sa_files)} state-action pair files to process")
    
    # Process files in batches
    total_processed = 0
    total_success = 0
    
    for i in range(0, len(sa_files), batch_size):
        batch_files = sa_files[i:i+batch_size]
        logger.info(f"Processing batch {i//batch_size + 1}/{(len(sa_files)-1)//batch_size + 1}")
        
        for file_path in tqdm(batch_files, desc=f"Batch {i//batch_size + 1}"):
            total_processed += 1
            success = extract_features_from_file(file_path, output_dir)
            if success:
                total_success += 1
    
    # Organize output files if requested
    if organize_files and total_success > 0:
        logger.info("Organizing extracted feature files...")
        organize_feature_files(output_dir)
    
    success_rate = (total_success / total_processed * 100) if total_processed > 0 else 0
    logger.info(f"Processed {total_processed} files with {total_success} successes ({success_rate:.1f}%)")
    
    return total_success

def generate_summary_report(output_dir):
    """Generate a summary report of the extracted features."""
    # Find all feature files
    feature_path = Path(output_dir)
    feature_files = list(feature_path.glob("**/*taric_features_*.json"))
    
    if not feature_files:
        logger.warning(f"No feature files found in {output_dir}")
        return
    
    # Initialize summary data
    summary = {
        "total_files": len(feature_files),
        "metrics_present": {
            "combat": 0,
            "vision": 0,
            "positioning": 0,
            "mechanics": 0,
            "game_state": 0
        },
        "game_modes": {},
        "champions": {},
        "total_state_actions": 0,
        "generated_at": datetime.now().isoformat()
    }
    
    # Process each file for summary
    for file_path in tqdm(feature_files, desc="Generating summary"):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Count metrics present
            for metric_type in summary["metrics_present"]:
                if metric_type in data.get('features', {}):
                    summary["metrics_present"][metric_type] += 1
            
            # Count game modes
            game_mode = data.get('metadata', {}).get('game_mode', 'unknown')
            summary["game_modes"][game_mode] = summary["game_modes"].get(game_mode, 0) + 1
            
            # Count champions (allies and enemies)
            allies = data.get('metadata', {}).get('allies', [])
            enemies = data.get('metadata', {}).get('enemies', [])
            
            for champ in allies + enemies:
                champion_name = champ.get('champion', 'unknown')
                summary["champions"][champion_name] = summary["champions"].get(champion_name, 0) + 1
            
            # Count total state-action pairs
            sa_count = data.get('metadata', {}).get('state_action_count', 0)
            summary["total_state_actions"] += sa_count
            
        except Exception as e:
            logger.error(f"Error processing {file_path} for summary: {str(e)}")
    
    # Save summary report
    summary_path = os.path.join(output_dir, "extraction_summary.json")
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Summary report generated at {summary_path}")
    return summary

def main():
    """Main entry point for feature extraction."""
    parser = argparse.ArgumentParser(description='Run complete feature extraction pipeline')
    parser.add_argument('--input-dir', required=True, help='Directory containing state-action pair files')
    parser.add_argument('--output-dir', required=True, help='Directory to save extracted features')
    parser.add_argument('--batch-size', type=int, default=5, help='Number of files to process in each batch')
    parser.add_argument('--no-organize', action='store_false', dest='organize', help='Skip organizing output files')
    parser.add_argument('--summary', action='store_true', help='Generate a summary report after extraction')
    parser.set_defaults(organize=True)
    
    args = parser.parse_args()
    
    logger.info("=== Starting Feature Extraction Pipeline ===")
    logger.info(f"Input directory: {args.input_dir}")
    logger.info(f"Output directory: {args.output_dir}")
    
    start_time = time.time()
    
    # Process all files
    processed_count = process_all_files(
        args.input_dir, 
        args.output_dir, 
        args.batch_size, 
        args.organize
    )
    
    # Generate summary report if requested
    if args.summary and processed_count > 0:
        summary = generate_summary_report(args.output_dir)
    
    end_time = time.time()
    total_time = end_time - start_time
    
    logger.info(f"=== Feature Extraction Complete ===")
    logger.info(f"Processed {processed_count} files in {total_time:.2f} seconds")

if __name__ == "__main__":
    main() 