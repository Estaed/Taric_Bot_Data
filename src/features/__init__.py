"""
Feature engineering for Taric Bot AI.

This package contains modules for extracting advanced metrics and features
from state-action pairs for the Taric Bot AI project.
"""

from .combat_metrics import calculate_combat_metrics, calculate_healing_metrics, calculate_stun_metrics
from .vision_metrics import calculate_vision_metrics
from .positioning_metrics import calculate_positioning_metrics
from .mechanics_metrics import calculate_mechanics_metrics
from .feature_extraction import (
    extract_features_from_file,
    extract_features_from_directory,
    batch_process_features,
    merge_features
)
from .file_organizer import (
    organize_state_action_files,
    organize_feature_files,
    cleanup_unorganized_files
)

__all__ = [
    'calculate_combat_metrics',
    'calculate_healing_metrics',
    'calculate_stun_metrics',
    'calculate_vision_metrics',
    'calculate_positioning_metrics',
    'calculate_mechanics_metrics',
    'extract_features_from_file',
    'extract_features_from_directory',
    'batch_process_features',
    'merge_features',
    'organize_state_action_files',
    'organize_feature_files',
    'cleanup_unorganized_files',
] 