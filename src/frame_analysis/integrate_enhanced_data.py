"""
Integration script for all enhanced data extraction features.

This script integrates the enhanced data extraction module with the frame analysis
pipeline to provide comprehensive data collection for the Taric bot.
"""

import os
import sys
from pathlib import Path
import numpy as np
import json

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.frame_analysis import FrameAnalyzer
from src.frame_analysis.enhanced_data_extraction import extract_enhanced_data

def run_enhanced_analysis(match_id=None):
    """
    Run the enhanced frame analysis on a specific match or all matches.
    
    Args:
        match_id (str, optional): Specific match ID to analyze. If None, processes all matches.
        
    Returns:
        list: Paths to output files
    """
    print("Starting enhanced frame analysis...")
    
    if match_id:
        # Process a single match
        analyzer = FrameAnalyzer()
        if analyzer.load_match_by_id(match_id):
            pairs = analyzer.create_state_action_pairs()
            
            # Generate critical decision scenarios
            try:
                critical_scenarios = analyzer.create_critical_decision_scenarios()
                if critical_scenarios:
                    print(f"Added {len(critical_scenarios)} critical decision scenarios")
                    analyzer.state_action_pairs.extend(critical_scenarios)
            except Exception as e:
                print(f"Warning: Could not create critical scenarios: {e}")
                
            # Save the state-action pairs
            output_file = analyzer.save_state_action_pairs()
            
            if output_file:
                print(f"Successfully created enhanced state-action pairs for match {match_id}")
                print(f"Output saved to: {output_file}")
                return [output_file]
            else:
                print(f"Failed to create state-action pairs for match {match_id}")
                return []
        else:
            print(f"Failed to load match {match_id}")
            return []
    else:
        # Process all matches
        return process_all_matches_with_enhanced_data()

def process_all_matches_with_enhanced_data():
    """
    Process all match files with enhanced data extraction.
    
    Returns:
        list: List of output files
    """
    from src.frame_analysis import process_all_matches
    return process_all_matches()

def validate_enhanced_data(output_file):
    """
    Validate the enhanced data in a state-action pairs file.
    
    Args:
        output_file (str or Path): Path to the output file
        
    Returns:
        dict: Validation statistics
    """
    try:
        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        pairs = data.get('state_action_pairs', [])
        
        # Count pairs with enhanced data
        enhanced_count = 0
        for pair in pairs:
            if 'enhanced_data' in pair.get('state', {}):
                enhanced_count += 1
        
        # Calculate percentage
        total_pairs = len(pairs)
        enhanced_percentage = enhanced_count / total_pairs * 100 if total_pairs > 0 else 0
        
        # Sample one enhanced data entry for review
        sample_enhanced_data = None
        for pair in pairs:
            if 'enhanced_data' in pair.get('state', {}):
                sample_enhanced_data = pair['state']['enhanced_data']
                break
        
        # Check if environmental_context is present (should be removed in updated version)
        has_environmental = False
        if sample_enhanced_data and 'environmental_context' in sample_enhanced_data:
            has_environmental = True
            print("  Warning: environmental_context is still present in the data")
        
        validation = {
            'total_pairs': total_pairs,
            'enhanced_pairs': enhanced_count,
            'enhanced_percentage': enhanced_percentage,
            'sample_enhanced_data': sample_enhanced_data,
            'has_environmental_context': has_environmental
        }
        
        print(f"Enhanced Data Validation for {output_file}:")
        print(f"  Total pairs: {total_pairs}")
        print(f"  Pairs with enhanced data: {enhanced_count} ({enhanced_percentage:.1f}%)")
        
        # Check for static match data at file level
        if 'team_composition' in data:
            print("  Static match data optimized: Yes")
        else:
            print("  Static match data optimized: No")
        
        return validation
        
    except Exception as e:
        print(f"Error validating enhanced data: {e}")
        return None

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Run enhanced frame analysis on matches')
    parser.add_argument('--match-id', help='Specific match ID to analyze')
    parser.add_argument('--validate', action='store_true', help='Validate the enhanced data in output files')
    
    args = parser.parse_args()
    
    output_files = run_enhanced_analysis(args.match_id)
    
    if args.validate and output_files:
        for output_file in output_files:
            validate_enhanced_data(output_file) 