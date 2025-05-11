"""
Data cleaning utilities for Taric match data.
Transforms raw JSON data from Riot API to structured format.
"""

import json
import pandas as pd
import os
from pathlib import Path
import glob

from src.config import RAW_DATA_DIR, CLEANED_DATA_DIR

class DataCleaner:
    """Process and clean raw match data for Taric."""
    
    def __init__(self, raw_data_dir=None, output_dir=None):
        """
        Initialize the data cleaner.
        
        Args:
            raw_data_dir (Path, optional): Directory with raw data. Defaults to config.RAW_DATA_DIR.
            output_dir (Path, optional): Output directory. Defaults to config.CLEANED_DATA_DIR.
        """
        self.raw_data_dir = raw_data_dir or RAW_DATA_DIR
        self.output_dir = output_dir or CLEANED_DATA_DIR
    
    def load_match_json(self, file_path):
        """
        Load a match JSON file.
        
        Args:
            file_path (str or Path): Path to JSON file
            
        Returns:
            dict: Match data
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def extract_taric_data(self, match_data):
        """
        Extract Taric-specific data from a match.
        
        Args:
            match_data (dict): Match data from Riot API
            
        Returns:
            dict: Extracted Taric data
        """
        # Implementation will be completed in Phase 1
        # This is just a placeholder for the structure
        pass
    
    def process_match(self, match_data):
        """
        Process a single match to extract relevant data.
        
        Args:
            match_data (dict): Match data from Riot API
            
        Returns:
            pd.DataFrame: Processed match data
        """
        # Implementation will be completed in Phase 1
        # This is just a placeholder for the structure
        pass
    
    def process_all_matches(self, save_csv=True):
        """
        Process all matches in the raw data directory.
        
        Args:
            save_csv (bool, optional): Whether to save results to CSV. Defaults to True.
            
        Returns:
            pd.DataFrame: Processed match data
        """
        # Implementation will be completed in Phase 1
        # This is just a placeholder for the structure
        pass
    
    def save_processed_data(self, data, file_name="taric_match_data.csv"):
        """
        Save processed data to CSV.
        
        Args:
            data (pd.DataFrame): Data to save
            file_name (str, optional): File name. Defaults to "taric_match_data.csv".
            
        Returns:
            Path: Path to saved file
        """
        file_path = self.output_dir / file_name
        data.to_csv(file_path, index=False)
        return file_path 