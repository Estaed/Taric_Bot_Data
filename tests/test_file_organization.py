"""
Test script for file organization functionality.

This script tests the file organization functionality for Taric Bot AI.
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# Add src to sys.path to import modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.features import organize_state_action_files, organize_feature_files

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_file_organization(sa_dir=None, feature_dir=None):
    """Test file organization functionality."""
    
    if sa_dir:
        logger.info(f"Testing state-action file organization in {sa_dir}")
        sa_path = Path(sa_dir)
        
        if not sa_path.exists():
            logger.error(f"Directory does not exist: {sa_dir}")
            return
        
        sa_files = list(sa_path.glob("taric_sa_pairs_*.json"))
        if not sa_files:
            logger.warning(f"No state-action pair files found in {sa_dir}")
        else:
            logger.info(f"Found {len(sa_files)} state-action pair files")
            
            # Test organization
            results = organize_state_action_files(sa_dir)
            
            # Print results
            logger.info("Organization results:")
            logger.info(f"  Total files: {results['total_files']}")
            logger.info(f"  Organized files: {results['organized_files']}")
            logger.info(f"  Skipped files: {results['skipped_files']}")
            
            if results['by_patch']:
                logger.info("  Files by patch:")
                for patch, count in results['by_patch'].items():
                    logger.info(f"    {patch}: {count}")
            
            if results['by_game_mode']:
                logger.info("  Files by game mode:")
                for mode, count in results['by_game_mode'].items():
                    logger.info(f"    {mode}: {count}")
    
    if feature_dir:
        logger.info(f"Testing feature file organization in {feature_dir}")
        feature_path = Path(feature_dir)
        
        if not feature_path.exists():
            logger.error(f"Directory does not exist: {feature_dir}")
            return
        
        feature_files = list(feature_path.glob("taric_features_*.json"))
        if not feature_files:
            logger.warning(f"No feature files found in {feature_dir}")
        else:
            logger.info(f"Found {len(feature_files)} feature files")
            
            # Test organization
            results = organize_feature_files(feature_dir)
            
            # Print results
            logger.info("Organization results:")
            logger.info(f"  Total files: {results['total_files']}")
            logger.info(f"  Organized files: {results['organized_files']}")
            logger.info(f"  Skipped files: {results['skipped_files']}")
            
            if results['by_metric_type']:
                logger.info("  Files by metric type:")
                for metric_type, count in results['by_metric_type'].items():
                    logger.info(f"    {metric_type}: {count}")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Test file organization functionality')
    parser.add_argument('--sa-dir', help='Directory containing state-action pair files')
    parser.add_argument('--feature-dir', help='Directory containing feature files')
    
    args = parser.parse_args()
    
    if not args.sa_dir and not args.feature_dir:
        logger.error("No directories specified. Use --sa-dir and/or --feature-dir")
        parser.print_help()
        return
    
    test_file_organization(args.sa_dir, args.feature_dir)


if __name__ == "__main__":
    main() 