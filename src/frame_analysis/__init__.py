"""
Frame Analysis package for Taric Bot AI.

This package contains modules for analyzing frame-by-frame data from League of Legends
matches featuring Taric, extracting enhanced features, and creating comprehensive
state-action pairs for reinforcement learning.
"""

from src.frame_analysis.frame_analysis import FrameAnalyzer, process_all_matches, TaricJSONEncoder
from src.frame_analysis.enhanced_data_extraction import extract_enhanced_data
from src.frame_analysis.integrate_scenarios import integrate_with_frame_analyzer, create_comprehensive_scenarios 