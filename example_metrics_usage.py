#!/usr/bin/env python
"""
Example usage of the enhanced metrics_extraction module.

This script demonstrates two ways to use the metrics_extraction module:
1. Extract summary metrics (aggregated statistics)
2. Extract per-second metrics (time series data for visualization)

Usage:
    python example_metrics_usage.py
"""

import os
import json
import matplotlib.pyplot as plt
from datetime import datetime

# Import the metrics_extraction module
from src.metrics_extraction.metrics_extraction import (
    extract_metrics_from_file, 
    extract_metrics_to_file,
    process_all_files,
    generate_summary_report
)

# File paths
STATE_ACTION_DIR = "data/state_action_pairs"
METRICS_DIR = "data/metrics_data"
SUMMARY_DIR = os.path.join(METRICS_DIR, "summary")
PER_SECOND_DIR = os.path.join(METRICS_DIR, "per_second")

def extract_summary_metrics():
    """Extract summary metrics from state-action pairs."""
    print("\n=== Extracting Summary Metrics ===\n")
    
    # Create output directory
    os.makedirs(SUMMARY_DIR, exist_ok=True)
    
    # Process a single file example
    files = [f for f in os.listdir(STATE_ACTION_DIR) if f.endswith('.json')]
    if files:
        example_file = os.path.join(STATE_ACTION_DIR, files[0])
        print(f"Processing single file: {example_file}")
        
        # Extract metrics with validation
        metrics = extract_metrics_from_file(
            example_file, 
            validate_zeros=True,
            output_format="summary"
        )
        
        # Save to file
        output_file = os.path.join(SUMMARY_DIR, f"example_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, indent=2)
        
        print(f"Saved summary metrics to: {output_file}")
        
        # Print some example metrics
        print("\nExample Combat Metrics:")
        for metric, value in list(metrics['features']['combat'].items())[:5]:
            print(f"  {metric}: {value}")
        
        print("\nExample Vision Metrics:")
        for metric, value in list(metrics['features']['vision'].items())[:5]:
            print(f"  {metric}: {value}")
    else:
        print("No state-action files found.")

def extract_per_second_metrics():
    """Extract per-second metrics for visualization."""
    print("\n=== Extracting Per-Second Metrics ===\n")
    
    # Create output directory
    os.makedirs(PER_SECOND_DIR, exist_ok=True)
    
    # Process a single file example
    files = [f for f in os.listdir(STATE_ACTION_DIR) if f.endswith('.json')]
    if files:
        example_file = os.path.join(STATE_ACTION_DIR, files[0])
        print(f"Processing single file: {example_file}")
        
        # Extract metrics with per-second data
        metrics = extract_metrics_from_file(
            example_file, 
            validate_zeros=True,
            output_format="per_second"
        )
        
        # Save to file
        output_file = os.path.join(PER_SECOND_DIR, f"example_per_second_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, indent=2)
        
        print(f"Saved per-second metrics to: {output_file}")
        
        # Create visualizations of the per-second data
        try:
            time_series = metrics['time_series']
            
            # Create output directory for visualizations
            viz_dir = os.path.join(PER_SECOND_DIR, "visualizations")
            os.makedirs(viz_dir, exist_ok=True)
            
            # Plot health and mana over time
            plt.figure(figsize=(12, 6))
            plt.plot(time_series['timestamp'], time_series['combat']['health_percent'], 'g-', label='Health %')
            plt.plot(time_series['timestamp'], time_series['combat']['mana_percent'], 'b-', label='Mana %')
            plt.title('Taric Health and Mana Over Time')
            plt.xlabel('Game Time (seconds)')
            plt.ylabel('Percentage')
            plt.legend()
            plt.grid(True)
            
            # Save the plot
            plot_file = os.path.join(viz_dir, f"health_mana_plot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            plt.savefig(plot_file)
            plt.close()
            print(f"Saved health/mana visualization to: {plot_file}")
            
            # Plot ability usage over time
            plt.figure(figsize=(12, 6))
            abilities = time_series['mechanics']['abilities_used']
            timestamps = time_series['timestamp']
            
            # Prepare data for ability usage
            q_usage = [1 if 'Q' in a else 0 for a in abilities]
            w_usage = [1 if 'W' in a else 0 for a in abilities]
            e_usage = [1 if 'E' in a else 0 for a in abilities]
            r_usage = [1 if 'R' in a else 0 for a in abilities]
            
            plt.plot(timestamps, q_usage, 'b.', label='Q - Starlight Touch')
            plt.plot(timestamps, w_usage, 'g.', label='W - Bastion')
            plt.plot(timestamps, e_usage, 'r.', label='E - Dazzle')
            plt.plot(timestamps, r_usage, 'y*', markersize=10, label='R - Cosmic Radiance')
            
            plt.title('Taric Ability Usage')
            plt.xlabel('Game Time (seconds)')
            plt.ylabel('Ability Used')
            plt.yticks([0, 1], ['No', 'Yes'])
            plt.legend()
            plt.grid(True)
            
            # Save the plot
            abilities_plot = os.path.join(viz_dir, f"abilities_plot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            plt.savefig(abilities_plot)
            plt.close()
            print(f"Saved abilities visualization to: {abilities_plot}")
            
            # Plot position changes over time
            plt.figure(figsize=(12, 6))
            plt.scatter(
                time_series['positioning']['x_position'], 
                time_series['positioning']['y_position'],
                c=time_series['timestamp'],
                cmap='viridis',
                alpha=0.7,
                s=30
            )
            plt.colorbar(label='Game Time (seconds)')
            plt.title('Taric Movement throughout the Game')
            plt.xlabel('X Position')
            plt.ylabel('Y Position')
            plt.grid(True)
            
            # Add arrows to show movement direction
            for i in range(1, len(time_series['timestamp'])):
                if i % 10 == 0:  # Only show every 10th arrow to avoid clutter
                    plt.arrow(
                        time_series['positioning']['x_position'][i-1],
                        time_series['positioning']['y_position'][i-1],
                        time_series['positioning']['x_position'][i] - time_series['positioning']['x_position'][i-1],
                        time_series['positioning']['y_position'][i] - time_series['positioning']['y_position'][i-1],
                        head_width=0.3,
                        head_length=0.5,
                        fc='black',
                        ec='black',
                        alpha=0.5
                    )
            
            # Save the plot
            position_plot = os.path.join(viz_dir, f"position_plot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            plt.savefig(position_plot)
            plt.close()
            print(f"Saved position visualization to: {position_plot}")
            
        except Exception as e:
            print(f"Error creating visualization: {e}")
            
    else:
        print("No state-action files found.")

def process_batch():
    """Process a batch of files with the metrics extraction pipeline."""
    print("\n=== Processing Batch of Files ===\n")
    
    # Process all files in the directory
    result = process_all_files(
        STATE_ACTION_DIR,
        METRICS_DIR,
        batch_size=5,
        organize_files=True,
        validate_zeros=True,
        output_format="summary"
    )
    
    if result:
        print(f"Processed {result['total_files']} files")
        print(f"  Successful: {result['successful_files']}")
        print(f"  Failed: {result['failed_files']}")
        
        # Check for suspicious zero values
        if result['summary'] and 'validation_results' in result['summary']:
            summary = result['summary']
            if summary['validation_results']['files_with_suspicious_zeros'] > 0:
                print(f"\nFound suspicious zero values in {summary['validation_results']['files_with_suspicious_zeros']} files:")
                for category, metrics in summary['validation_results']['suspicious_metrics'].items():
                    if metrics:
                        print(f"  {category}: {', '.join(metrics)}")
            else:
                print("\nNo suspicious zero values found in the processed files!")
    else:
        print("No files were processed or an error occurred.")

def main():
    """Main function to demonstrate metrics extraction."""
    print("=== Taric Bot AI Metrics Extraction Example ===")
    
    # Extract summary metrics
    extract_summary_metrics()
    
    # Extract per-second metrics
    extract_per_second_metrics()
    
    # Process batch of files (uncomment to run)
    # process_batch()

if __name__ == "__main__":
    main() 