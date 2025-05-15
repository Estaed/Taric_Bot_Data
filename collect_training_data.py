#!/usr/bin/env python
"""
Taric Bot AI - Training Data Collector

This script collects training data directly from League of Legends replay frames,
combining frame analysis and feature extraction in a single pipeline.

Usage:
    python collect_training_data.py --replay-dir [REPLAY_DIR] --output-dir [OUTPUT_DIR]
"""

import os
import sys
import json
import time
import argparse
import logging
from pathlib import Path
from datetime import datetime
from tqdm import tqdm

# Import frame processing and feature extraction
from src.frame_analysis.frame_processor import load_replay_frames
from src.features.extract_training_features import TrainingFeatureExtractor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("training_data_collection.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def process_replay_file(replay_file, output_dir, sample_rate=1):
    """
    Process a single replay file and extract training data.
    
    Args:
        replay_file (str): Path to replay file
        output_dir (str): Directory to save training data
        sample_rate (int): Process every Nth frame (for performance)
        
    Returns:
        bool: Success status
    """
    logger.info(f"Processing replay file: {replay_file}")
    
    try:
        # Create output subdirectory based on replay filename
        replay_name = Path(replay_file).stem
        replay_output_dir = Path(output_dir) / replay_name
        replay_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load replay frames
        frames = load_replay_frames(replay_file)
        logger.info(f"Loaded {len(frames)} frames from replay")
        
        if not frames:
            logger.warning(f"No frames found in replay: {replay_file}")
            return False
        
        # Initialize feature extractor
        extractor = TrainingFeatureExtractor()
        
        # Process frames
        frame_count = 0
        feature_count = 0
        save_interval = 100  # Save features every 100 processed frames
        
        for i, frame in enumerate(tqdm(frames, desc="Processing frames")):
            # Skip frames based on sample rate
            if i % sample_rate != 0:
                continue
            
            # Process frame
            features, extractor = process_frame_with_extractor(frame, extractor)
            frame_count += 1
            
            # Count features and save periodically
            if features:
                feature_count += 1
                
                if feature_count % save_interval == 0:
                    save_path = extractor.save_training_data(replay_output_dir)
                    logger.info(f"Saved interim training data: {save_path}")
        
        # Save final training data
        final_save_path = extractor.save_training_data(replay_output_dir)
        
        logger.info(f"Successfully processed {frame_count} frames from {replay_file}")
        logger.info(f"Generated {feature_count} feature sets")
        logger.info(f"Final training data saved to: {final_save_path}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error processing {replay_file}: {str(e)}", exc_info=True)
        return False


def process_frame_with_extractor(frame, extractor):
    """
    Process a single frame with the feature extractor.
    
    Args:
        frame (dict): Frame data
        extractor (TrainingFeatureExtractor): Feature extractor instance
        
    Returns:
        tuple: (features, extractor)
    """
    try:
        # Process frame to extract features
        features = extractor.process_frame(frame)
        return features, extractor
    except Exception as e:
        logger.error(f"Error processing frame: {str(e)}")
        return None, extractor


def process_replay_directory(replay_dir, output_dir, sample_rate=1):
    """
    Process all replay files in a directory.
    
    Args:
        replay_dir (str): Directory containing replay files
        output_dir (str): Directory to save training data
        sample_rate (int): Process every Nth frame (for performance)
        
    Returns:
        int: Number of successfully processed replays
    """
    # Create output directory if it doesn't exist
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Find all replay files
    replay_files = list(Path(replay_dir).glob("*.replay.json"))
    
    if not replay_files:
        logger.warning(f"No replay files found in {replay_dir}")
        return 0
    
    logger.info(f"Found {len(replay_files)} replay files to process")
    
    # Process each replay file
    success_count = 0
    
    for replay_file in tqdm(replay_files, desc="Processing replays"):
        success = process_replay_file(replay_file, output_dir, sample_rate)
        if success:
            success_count += 1
    
    success_rate = (success_count / len(replay_files) * 100) if replay_files else 0
    logger.info(f"Processed {len(replay_files)} replays with {success_count} successes ({success_rate:.1f}%)")
    
    return success_count


def generate_summary_report(output_dir):
    """
    Generate a summary report of the collected training data.
    
    Args:
        output_dir (str): Directory containing training data
        
    Returns:
        dict: Summary information
    """
    # Find all training data files
    training_files = list(Path(output_dir).glob("**/*taric_training_data_*.json"))
    
    if not training_files:
        logger.warning(f"No training data files found in {output_dir}")
        return None
    
    # Initialize summary data
    summary = {
        "total_files": len(training_files),
        "total_feature_sets": 0,
        "feature_types": {
            "combat": 0,
            "vision": 0,
            "positioning": 0,
            "mechanics": 0,
            "game_state": 0
        },
        "game_modes": {},
        "total_labels": 0,
        "label_distribution": {
            "abilities": {},
            "targets": {},
            "items": {}
        },
        "generated_at": datetime.now().isoformat()
    }
    
    # Process each file for summary
    for file_path in tqdm(training_files, desc="Generating summary"):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Count feature sets
            features = data.get('features', {})
            summary["total_feature_sets"] += 1
            
            # Count feature types
            for feature_type in summary["feature_types"]:
                if feature_type in features:
                    summary["feature_types"][feature_type] += 1
            
            # Count game modes
            game_mode = data.get('metadata', {}).get('game_mode', 'unknown')
            summary["game_modes"][game_mode] = summary["game_modes"].get(game_mode, 0) + 1
            
            # Count labels
            labels = data.get('labels', [])
            summary["total_labels"] += len(labels)
            
            # Count label distribution
            for label in labels:
                # Abilities
                ability = label.get('ability')
                if ability:
                    summary["label_distribution"]["abilities"][ability] = (
                        summary["label_distribution"]["abilities"].get(ability, 0) + 1
                    )
                
                # Target types
                target_type = label.get('target_type')
                if target_type:
                    summary["label_distribution"]["targets"][target_type] = (
                        summary["label_distribution"]["targets"].get(target_type, 0) + 1
                    )
                
                # Items
                item = label.get('item_used')
                if item:
                    summary["label_distribution"]["items"][item] = (
                        summary["label_distribution"]["items"].get(item, 0) + 1
                    )
            
        except Exception as e:
            logger.error(f"Error processing {file_path} for summary: {str(e)}")
    
    # Save summary report
    summary_path = os.path.join(output_dir, "training_data_summary.json")
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Summary report generated at {summary_path}")
    return summary


def main():
    """Main entry point for training data collection."""
    parser = argparse.ArgumentParser(description='Collect training data from League of Legends replays')
    parser.add_argument('--replay-dir', required=True, help='Directory containing replay files')
    parser.add_argument('--output-dir', required=True, help='Directory to save training data')
    parser.add_argument('--sample-rate', type=int, default=5, help='Process every Nth frame (default: 5)')
    parser.add_argument('--summary', action='store_true', help='Generate a summary report after collection')
    
    args = parser.parse_args()
    
    logger.info("=== Starting Training Data Collection ===")
    logger.info(f"Replay directory: {args.replay_dir}")
    logger.info(f"Output directory: {args.output_dir}")
    logger.info(f"Sample rate: {args.sample_rate}")
    
    start_time = time.time()
    
    # Process replay files
    success_count = process_replay_directory(
        args.replay_dir,
        args.output_dir,
        args.sample_rate
    )
    
    # Generate summary report if requested
    if args.summary and success_count > 0:
        summary = generate_summary_report(args.output_dir)
    
    end_time = time.time()
    total_time = end_time - start_time
    
    logger.info(f"=== Training Data Collection Complete ===")
    logger.info(f"Processed {success_count} replay files in {total_time:.2f} seconds")


if __name__ == "__main__":
    main() 