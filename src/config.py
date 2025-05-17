"""
Configuration settings for the Taric Bot AI project.
Handles environment variables and project paths.
"""

import os
import dotenv
from pathlib import Path

# Load environment variables from .env file
dotenv.load_dotenv()

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
MODELS_DIR = PROJECT_ROOT / "models"
NOTEBOOKS_DIR = PROJECT_ROOT / "notebooks"

# Data subdirectories
RAW_DATA_DIR = DATA_DIR / "raw" / "Estaed games"
CLEANED_DATA_DIR = DATA_DIR / "cleaned"
STATE_ACTION_DIR = DATA_DIR / "state_action_pairs"
METRICS_DIR = DATA_DIR / "metrics_data"

# API settings
RIOT_API_KEY = os.getenv("RIOT_API_KEY")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# Ensure all directories exist
for directory in [DATA_DIR, MODELS_DIR, NOTEBOOKS_DIR, RAW_DATA_DIR, CLEANED_DATA_DIR, STATE_ACTION_DIR, METRICS_DIR]:
    directory.mkdir(exist_ok=True)

# Validation
if not RIOT_API_KEY and ENVIRONMENT != "test":
    print("Warning: RIOT_API_KEY environment variable not set.")
    print("Please create a .env file with your Riot API key for data collection.") 