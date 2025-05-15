# prd.md

This file tracks all features you have completed (**Done**) and those still in progress (**To Do**). Use the `Project Rules` section to automate updates when you start an approval prompt with **"okay super."**

---

## Done

0.  **Foundational Setup**
    -   **Virtual Environment (venv) Management**
        -   Phase 0 (Installation): Initial venv creation and activation.
        -   Phase 1 (Data Collection): Add/verify data acquisition and processing libraries.
    -   **GitHub Repository Management**
        -   Phase 0 (Installation): Initialize repository, setup .gitignore, main/develop branches.
        -   Phase 1 (Data Collection): Create branches for data fetching/processing scripts, commit initial data structure.

1. **Project initialization:** Created repository and defined folder structure (`data/`, `models/`, `src/`, `notebooks/`).

2. **Data fetching setup:** Implemented Riot API client to download match data for Taric games, collected 50 games from Estaed#TAR and 50 games from EstaedOCE#9591.

3. **Data Collection & Preprocessing (Partial)**
   - Collected replay data from Estaed accounts (50 games each)
   - Implemented API region handling to support all servers
   - Created and implemented `src/collect_estaed.py` for data collection

4. **Basic data-cleaning pipeline:** Implemented `src/process_data.py` to parse JSON, remove incomplete entries, and export cleaned data to `data/cleaned/taric_matches.csv`.

5. **Frame-by-frame analysis:** Implemented `src/frame_analysis.py` to create comprehensive state-action pairs for reinforcement learning, including:
   - Cooldown tracking for Taric's abilities
   - Proximity data about nearby allies and enemies
   - Targeting information for healing, shielding, and stunning
   - Reward signals to guide the learning process

6. **Feature Engineering (Phase 1)**
   - Implemented enhanced state representation with:
     - Team composition information
     - Lane matchup context
     - Game phase awareness (early/mid/late game)
     - Higher temporal resolution (15-second intervals)
   - Added ability haste calculations for dynamic cooldowns
   - Created critical decision scenarios for key moments
   - Added reward signal components for future RL model training

6a. **Feature Engineering (Phase 1.5) - Partial**
   - Optimized data storage structure:
     - Moved static match data to file level instead of duplicating in every state-action pair
     - Significantly reduced file sizes and improved processing efficiency
   - Implemented select advanced metrics:
     - **Combat Metrics:**
       - Stun opportunity detection
       - Healing target priority analysis
       - Heal/Shield Uptime (active duration ÷ game time)
       - Stun Rate (successful stuns ÷ attempts)
       - Detailed healing efficiency metrics
       - Damage prevented calculations
       - Healing distribution by game phase
       - Target priority analysis
     - **Positioning Metrics:**
       - Distance to allies
       - Distance to enemies
       - Region-based movement analysis
       - Lane proximity tracking over time
       - Champion pathing and movement efficiency metrics
       - Map region presence analysis
     - **Game State Features:**
       - Gold difference tracking
       - Level difference tracking
       - Basic objective control tracking
       - Event tracking for key game moments
     - **Mechanical Actions:**
       - Ability sequence timing
       - Target selection patterns
       - Detailed interaction timing analysis
       - Item active usage in relation to ability casts
       - Mouse click patterns (right-click vs left-click)
       - Auto-attack reset timing
       - Actions Per Minute (APM) and variation
       - Camera control patterns
     - **Vision Metrics:**
       - Ward coverage with region tracking
       - Vision control metrics by map region
       - Comprehensive objective control tracking
       - Vision control metrics (wards placed/cleared, areas revealed)
       - Vision advantage/disadvantage period analysis
   - Created file organization structure:
     - Organized files into appropriate subdirectories
     - Implemented backup functionality
     - Added automatic file organization during extraction

---

## To Do

0.  **Foundational Setup**
    -   **Virtual Environment (venv) Management**
        -   Phase 2 (Training): Add/verify ML/RL framework libraries (e.g., TensorFlow, PyTorch, RLlib).
        -   Phase 3 (Testing & Feedback): Add/verify testing and visualization libraries.
    -   **GitHub Repository Management**
        -   Phase 2 (Training): Create branches for model development, training scripts, and experiment tracking.
        -   Phase 3 (Testing & Feedback): Create branches for evaluation scripts, test cases, and feedback aggregation.

6b. **League Director Integration (Phase 1.5)**
   - Setup and configure League Director for replay analysis:
     - Install League Director from https://github.com/riotgames/leaguedirector
     - Configure game.cfg with EnableReplayApi=1
     - Set graphics settings to Very High for full feature access
   - Implement visual data extraction scripts:
     - **Precise Positioning Data:**
       - Track exact mouse movement patterns during combos
       - Record camera positioning during key gameplay moments
       - Extract visual cues that trigger decision-making
     - **Sequence Analysis:**
       - Record optimal Taric ability combos as training examples  
       - Measure precise timing between actions at frame level
       - Save and categorize sequences for model training
     - **First-Person Perspective Analysis:**
       - Capture champion's viewpoint during decision-making
       - Analyze vision limitations and their impact on gameplay
       - Record eye tracking approximation (what's visible on screen)
     - **Detailed Mechanical Analysis:**
       - Slow-motion analysis of skill shots and dodging
       - Multi-angle study of team fight positioning
       - Track cursor movement during targeting and ability execution
   - Develop data processing pipeline:
     - Create a standardized format for visual data
     - Integrate with existing feature datasets
     - Export processed visual data to `data/cleaned/taric_visual_features.csv`
   - Implement replay management system:
     - Catalog and organize replay files
     - Tag replays with relevant metadata (matchup, performance, etc.)
     - Create a retrieval system for finding specific gameplay scenarios

7. **Reinforcement Learning Setup**
   - Implement environment wrapper for League of Legends
   - Define state space, action space, and reward function:
    - **State Space:**
      - Screen coordinates
      - Mouse position
      - Ability cooldowns
      - Target information
      - Health/mana values
        - Detailed game state information from LCU (if integrated).
        - Information about nearby allies and enemies (positions, health, mana, cooldowns).
        - Vision state of the map.
    - **Action Space:**
      - Mouse movements (x, y coordinates)
      - Click types (right/left)
      - Ability casts (Q, W, E, R)
      - Item usage
      - Summoner spells
        - Camera control actions (if applicable).
    - **Reward Function:**
      - **Combat Rewards:**
        - Takedowns (kills + assists)
        - Structures destroyed
        - Epic monster kills (Dragon, Baron, Herald)
        - Damage dealt and damage mitigated.
      - **Ability-Specific Rewards:**
        - E (Dazzle) rewards:
          - Champions stunned
          - Multiple champions stunned (bonus)
        - W (Bastion) rewards:
          - Damage prevented on allies
          - Successful shields applied
          - Effective W usage for empowered Q/E.
        - Q (Starlight's Touch) rewards:
          - Healing amount
          - Auto-attack reset efficiency
          - Healing multiple allies.
        - R (Cosmic Radiance) rewards:
          - Allies getting takedowns within 5 seconds of ult
          - Damage prevented by ult
          - Successful ult usage preventing key enemy abilities or engage.
        - Passive (Bravado) rewards:
          - Magic damage dealt
          - Auto-attack reset efficiency
      - **Positioning Rewards:**
        - Proper positioning for ability usage
        - Staying in range of allies for W
        - Optimal positioning for E stuns
          - Positioning relative to minions and terrain.
          - Vision control and denial (warding/sweeping rewards).
      - **Team Fight Rewards:**
        - Successful team fight participation
        - Proper ult timing
        - Multiple ability hits
          - Peeling for carries.
          - Engaging or counter-engaging effectively.
        - Lane phase specific rewards (e.g., successful trades, CS denial).
        - Objective control rewards (assisting with Dragon/Baron, taking towers).
   - Create custom reward shaping for Taric-specific mechanics
   - Set up PPO training pipeline

8. **Model Training**
   - `src/train_rl.py`: Implement RL training loop
   - Focus on mechanical skills:
    - Auto-attack reset timing with Q
    - E-W combo execution
    - R timing in team fights
    - Proper target selection
    - Mouse movement efficiency
      - Dodging skill shots.
      - Efficient item and summoner spell usage.
   - Save model checkpoints to `models/`
   - Log training metrics in `notebooks/training_results.ipynb`
   - Implement early stopping and model validation

9. **Model Evaluation & Tuning**
   - Create evaluation suite with:
    - Win rate against different champions
    - Average KDA
    - Objective control rate
    - Team fight participation
      - Key Taric metric analysis (Heal/Shield amount, Stun uptime, Ult effectiveness).
      - Comparison of AI metrics against high-ELO human players.
   - Implement hyperparameter tuning
   - Save best parameters to `reports/hyperparam_tuning.md`

10. **Inference & Game Integration**
   - `src/infer.py`: Load model, process game state
   - Implement action selection and execution:
    - Mouse movement prediction
    - Click type selection
    - Ability timing
    - Target selection
      - Smooth and human-like mouse movement implementation.
      - Handling of different game resolutions and settings.
   - Add safety checks and fallback behaviors:
    - Maximum click rate limits
    - Ability cooldown checks
    - Target validation
      - Handling disconnections and game pauses.
      - Implementing basic AFK prevention.
      - Error handling for unexpected game states or API issues.
   - Create visualization of AI decision-making:
    - Mouse movement paths
    - Ability usage timing
    - Target selection reasoning
      - Overlaying AI's perception of game state.

11. **Testing & Validation**
   - Create test suite for model behavior
   - Implement unit tests for feature engineering
   - Add integration tests for full pipeline
   - Create benchmark against human players
    - Automated testing environment setup (e.g., using custom games).
    - Testing against Riot's built-in bots.

12. **Deployment & Monitoring**
   - `src/cli.py`: CLI entry point
   - Implement logging and monitoring
   - Create performance dashboards
   - Set up automated retraining pipeline
    - Consider ethical implications and Riot's Terms of Service regarding bot usage.
    - Implement safeguards against detection by anti-cheat systems (if operating in environments where this is relevant - though note Riot's Vanguard rollout).

13. **AI Action Visualization & Testing**
   - Create visualization system:
    - Real-time display of AI's decision-making process
    - Heat maps of mouse movements and click patterns
    - Ability usage timing visualization
    - Target selection indicators
      - Display of AI's internal state representation.
   - Multi-account testing framework:
    - Test AI on different accounts/regions
    - Compare performance across:
      - Different ELO ranges
      - Various team compositions
      - Different playstyles
    - Collect and analyze performance metrics:
      - Win rates per account
      - KDA ratios
      - Objective control
      - Team fight participation
      - Detailed per-game performance analysis.
   - Create replay analysis tool:
    - Compare AI actions vs human actions
    - Highlight key decision points
    - Show alternative action possibilities
    - Generate improvement suggestions
      - Automated identification of suboptimal AI plays.

---

## Project Rules

These replace old `.cursorrules`. Whenever you start a user command with **"okay super"**, Cursor will:

1. Open `[prd.md](mdc:prd.md)`.
2. Find the **## Done** section.
3. Grab the summary of your most recently approved feature.
4. If it's not already listed, append it to **## Done**.

*(Fires only on prompts beginning with "okay super.")*

---

*All prompts and code must be in English.*