# Frame Analysis Package Documentation

## Overview

The Frame Analysis package is a core component of the Taric Bot AI project, responsible for analyzing frame-by-frame data from League of Legends matches featuring Taric. This package extracts detailed game state information, creates state-action pairs for reinforcement learning, and generates critical decision scenarios that help train the AI to make optimal decisions in various gameplay situations.

## Recent Updates and Optimizations

### 1. Optimized Data Storage Structure
- **File-Level Match Data**: Moved static match information (team compositions, champion data, etc.) to the top level of each file instead of duplicating in every state-action pair
- **Significantly Reduced File Size**: This change substantially decreased storage requirements and improved processing efficiency
- **Implementation**: Modified `_create_game_state` and `save_state_action_pairs` in frame_analysis.py

### 2. Removed Synthetic Environmental Context
- **Eliminated Placeholder Data**: Removed the environmental_context component from state-action pairs since it contained only synthetic data rather than actual game information
- **Future Enhancement**: Plan to integrate with Riot Games Live Client Data API to replace this with real-time game information

### 3. Action Event Classification
- **Improved Event Classification**: Changed "NO_ACTION" event type to "OBSERVE" to better represent moments when the player is gathering information
- **Maintains Data Frequency**: Still analyzes game state every second regardless of action type
- **Reduces Bias**: Avoids dataset bias toward only action-taking moments

### 4. Advanced Combat Metrics Implementation
- **Enhanced Healing Analysis**:
  - Added target priority tracking (high/medium/low priority targets)
  - Implemented healing distribution scoring
  - Added optimal heal timing detection for critical moments
  - Improved heal uptime calculation with overlapping windows
- **Advanced Shield Metrics**:
  - Added W link efficiency tracking
  - Implemented threat period detection for optimal shielding
  - Added W empowerment usage tracking for ability combos
- **Detailed Damage Prevention**:
  - Added detailed tracking of damage prevented by W and R
  - Implemented ultimate timing scoring based on damage prevented
  - Added per-minute damage prevention metrics

### 5. Advanced Positioning Metrics Implementation
- **Lane Proximity Tracking Over Time**:
  - Added detailed lane proximity timeline
  - Implemented primary lane detection and lane adherence scoring
  - Added lane rotation tracking and analysis
  - Calculated lane presence by game phase (early/mid/late)
- **Champion Pathing Analysis**:
  - Implemented path efficiency and directness calculations
  - Added backtracking detection and quantification
  - Measured objective approaches and movement patterns
  - Calculated phase-specific movement metrics

### 6. Advanced Vision Metrics Implementation
- **Region-Based Ward Coverage Analysis**:
  - Mapped strategic regions across the map (Baron, Dragon, rivers, buffs)
  - Calculated vision coverage percentage by region
  - Measured objective vision control over time
  - Analyzed ward placement optimality using reference ward spots
- **Vision Control by Game Phase**:
  - Tracked vision evolution across early, mid, and late game
  - Analyzed region-specific vision focus during different phases
  - Measured vision control before objective spawns
- **Vision Denial and Advantage Measurement**:
  - Quantified vision advantage periods
  - Evaluated vision denial effectiveness
  - Calculated objective-specific vision control percentages

### 7. Feature Engineering Implementation
The system now includes a comprehensive feature extraction system that calculates advanced metrics from the optimized state-action pairs:

- **Combat Metrics**: Healing efficiency, shield effectiveness, stun success rate, damage prevention
- **Vision Metrics**: Ward coverage, vision score, map awareness, regional vision control
- **Positioning Metrics**: Lane proximity tracking, path analysis, map presence
- **Mechanics Metrics**: Ability sequencing, target selection, action timing

### 8. File Organization
- Organized files by game version, mode, and champion matchups
- Structured feature files by metric type
- Implemented backup and cleanup functionality

## Package Structure

The package is located in `src/frame_analysis/` and consists of the following key components:

1. **frame_analysis.py**: The main module that processes match data, extracts timeline events, and creates state-action pairs
2. **enhanced_data_extraction.py**: Extracts additional high-level features from game state information
3. **taric_scenarios.py**: Defines templates for various game scenarios for Taric gameplay
4. **integrate_scenarios.py**: Integrates the scenario templates with the frame analyzer
5. **inspect_enhanced_data.py**: Utilities for visualizing and validating enhanced data
6. **__init__.py**: Exposes key functions and classes from the package

## Key Components

### FrameAnalyzer Class

The `FrameAnalyzer` class is the central component that processes match data to extract detailed timeline events, analyze game states at different timestamps, and create state-action pairs for reinforcement learning. Key features include:

- **Timeline Data Extraction**: Processes match data to extract frame-by-frame information
- **Taric Event Detection**: Identifies events related to Taric's gameplay
- **State-Action Pair Creation**: Generates state-action pairs for reinforcement learning
- **Cooldown Tracking**: Calculates ability cooldowns with ability haste considerations
- **Unit Analysis**: Tracks nearby allies and enemies for positional awareness
- **Reward Signal Calculation**: Computes various reward signals for reinforcement learning

### Data Structure Optimization

The system optimizes storage by keeping static match information at the file level rather than duplicating it in every state-action pair:

- **Team Compositions**: Stored once per match
- **Game Context**: Match-wide information stored centrally
- **Lane Matchups**: Stored at the file level
- **Match Metadata**: Single copy per analysis file

This structure reduces file sizes and improves processing efficiency.

### Enhanced Data Extraction

The enhanced data extraction system captures additional high-level information from game states, including:

1. **Positional Data**:
   - Map region analysis (jungle, lane, river, base)
   - Objective proximity (Baron, Dragon, Herald)
   - Team positioning patterns (grouped, split, flanking)

2. **Combat Metrics**:
   - Healing target prioritization
   - Stun opportunity detection
   - Combat advantage calculation
   - Enemy threat assessment

3. **Decision Context**:
   - Game phase awareness (early, mid, late game)
   - Objective timing detection
   - Team advantage evaluation
   - Win condition tracking

4. **Player Input Analysis**:
   - Ability sequence patterns
   - Target selection tendencies
   - Combat style classification
   - Mechanical skill assessment

5. **Vision Control**:
   - Strategic ward placement analysis
   - Vision coverage by map region
   - Objective control vision
   - Ward placement optimality

## Output Format

The frame analysis outputs structured state-action pairs in JSON format with:

1. **Match-level data** (stored once per file):
   - Team compositions
   - Game metadata
   - Match context

2. **State-action pairs** (sequence of events):
   - Game state at each timestamp
   - Action taken by Taric
   - Enhanced data features:
     - Positional data
     - Combat metrics
     - Decision context
     - Player input patterns
     - Vision control data

## Scenario Types

The package generates a comprehensive set of scenarios to train the Taric Bot AI in various situations. These scenarios include:

### Ability-Specific Scenarios

1. **Q Ability (Starlight's Touch) Scenarios**:
   - **Low Health Healing**: Prioritizing low-health allies for healing
   - **Group Healing**: Maximizing healing across multiple allies
   - **Combat Healing**: Timing heals during combat
   - **Mana Conservation**: Conserving mana while providing healing
   - **Auto Attack Reset**: Using Q to reset auto-attack timing

2. **W Ability (Bastion) Scenarios**:
   - **Carry Protection**: Shielding the main damage dealer
   - **Link Optimization**: Choosing the optimal ally to link with
   - **Link Transfer**: Changing link target during fights
   - **Ability Synchronization**: Coordinating W usage with other abilities

3. **E Ability (Dazzle) Scenarios**:
   - **Multi-Target Stun**: Stunning multiple enemies
   - **Defensive Peel**: Using stuns to protect allies
   - **Engage Setup**: Using stuns to initiate fights
   - **W-E Combo**: Using W link to extend stun range
   - **Flash-E Combo**: Using Flash to reposition for stuns

4. **R Ability (Cosmic Radiance) Scenarios**:
   - **Team Fight Timing**: Using ultimate at the optimal moment in team fights
   - **Objective Contest**: Using ultimate to secure objectives
   - **Dive Protection**: Using ultimate to enable tower dives
   - **Defensive Ultimate**: Using ultimate to counter enemy engage
   - **Ult Economy**: Knowing when to save ultimate for later fights

### Positioning Scenarios

1. **Front Line Positioning**: Proper positioning as a front line tank
2. **Backline Protection**: Positioning to protect carries
3. **Zone Control**: Using positioning to control map areas
4. **Ability Range Optimization**: Positioning to maximize ability coverage
5. **Team Formation**: Positioning in relation to team members

### Vision Control Scenarios

1. **Strategic Ward Placement**: Optimal ward locations for objective control
2. **Vision Denial**: Clearing enemy wards and denying vision
3. **Vision Coverage Analysis**: Ensuring critical areas are warded
4. **Objective Vision Control**: Securing vision around baron and dragon
5. **Zone Vision**: Maintaining vision in key jungle pathways and entrances

### Combat Scenarios

1. **Team Fight Execution**: Optimal play during full team engagements
2. **Skirmish Handling**: Managing smaller 2v2 or 3v3 fights
3. **1v1 Duels**: Handling direct confrontations
4. **Focus Target Selection**: Choosing the right targets in combat
5. **Ability Sequencing**: Optimizing ability order in combat

### Other Scenario Categories

- **Item Usage Scenarios**: When and how to use active items
- **Wave Management Scenarios**: Helping control minion waves
- **Vision Control Scenarios**: Ward placement and vision denial
- **Macro Decision Scenarios**: Large-scale map movement and objective control
- **Team Coordination Scenarios**: Synchronizing actions with teammates
- **Game Phase Scenarios**: Early, mid, and late game decision making
- **Special Mechanics Scenarios**: Unique Taric-specific mechanics

## Integration with Other Modules

The Frame Analysis package interfaces with several other components of the Taric Bot AI project:

1. **Data Collection (src/collect_estaed.py)**:
   - Provides match data for analysis
   - The frame analysis package processes this raw data

2. **Data Processing (src/process_data.py)**:
   - Preprocesses match data before detailed frame analysis
   - Filters and cleans the data for more accurate analysis

3. **Configuration (src/config.py)**:
   - Provides project paths and settings
   - Defines locations for data storage and output files

4. **Analysis Tools (analyze_actions.py)**:
   - Uses the frame analysis output to analyze action distributions
   - Provides insights into Taric's gameplay patterns

5. **Feature Engineering (src/features/ directory)**:
   - Takes frame analysis data to calculate more complex metrics
   - Builds upon the foundation provided by frame analysis

## Usage Examples

### Basic Frame Analysis

```python
from src.frame_analysis import FrameAnalyzer

# Create analyzer with match data
analyzer = FrameAnalyzer()
analyzer.load_match_by_id("match_id")

# Create state-action pairs
pairs = analyzer.create_state_action_pairs()

# Save the results
analyzer.save_state_action_pairs()
```

### Enhanced Data Extraction

```python
from src.frame_analysis import extract_enhanced_data

# Extract enhanced features from game state
enhanced_data = extract_enhanced_data(
    game_state,
    timestamp,
    action,
    previous_states,
    previous_actions,
    analyzer  # Pass analyzer for access to static match data
)
```

### Scenario Generation

```python
from src.frame_analysis import FrameAnalyzer

analyzer = FrameAnalyzer()
analyzer.load_match_by_id("match_id")

# Generate critical decision scenarios
scenarios = analyzer.create_critical_decision_scenarios()
```

## Next Steps

1. **API Integration**: Replace synthetic environmental data with Riot Games Live Client Data
2. **Advanced Metrics**: Continue implementing remaining mechanics metrics
3. **DirectX Integration**: Set up League Director for visual data extraction

## Conclusion

The Frame Analysis package forms the foundation of the Taric Bot AI's learning process by transforming raw match data into structured state-action pairs and critical decision scenarios. These outputs provide the training data necessary for the reinforcement learning models to learn optimal Taric gameplay in various situations.

By processing both explicit game events and generating specialized scenarios, the package ensures comprehensive coverage of Taric's gameplay requirements, from basic ability usage to complex decision-making in critical moments. 