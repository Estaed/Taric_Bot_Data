# prd.md

This file tracks all features you have completed (**Done**) and those still in progress (**To Do**). Use the `Project Rules` section to automate updates when you start an approval prompt with **"okay super."**

---

## Done

---

## To Do

1. **Project initialization:** Created repository and defined folder structure (`data/`, `models/`, `src/`, `notebooks/`).
2. **Data fetching setup:** Implemented Riot API client to download match data for Taric games and saved raw JSON files under `data/raw/`.
3. **Basic data-cleaning pipeline:** Wrote script `src/clean_data.py` to parse JSON, remove incomplete entries, and export cleaned CSVs to `data/cleaned/`.
4. **Data Collection & Preprocessing**
   - Collect replay data from high-ELO Taric players and Estaed#OCE taric data
   - Record player actions, game state, and outcomes
   - Implement frame-by-frame analysis of replays
    - Explore and potentially integrate League Client API (LCU) for real-time game state data during live testing/inference.
    - Investigate methods for extracting high-fidelity data from replay files, including precise positioning and detailed event timestamps.
   - Create dataset of state-action pairs for training

5. **Feature Engineering**
   - Write scripts in `src/features/` to calculate:
     - **Combat Metrics:**
       - Heal/Shield Uptime (active duration ÷ game time)
       - Stun Rate (successful stuns ÷ attempts)
     - **Positioning Metrics:**
       - Distance to allies
       - Distance to enemies
       - Ward coverage
        - Champion pathing and movement efficiency metrics.
     - **Game State Features:**
       - Gold difference
       - Level difference
       - Objective status
       - Team composition
        - Vision control metrics (wards placed/cleared, areas revealed).
     - **Mechanical Actions:**
       - Mouse click patterns (right-click vs left-click)
       - Ability sequence timing
       - Auto-attack reset timing
       - Target selection patterns
        - Actions Per Minute (APM) and variation.
        - Camera control patterns (if applicable).
        - Detailed interaction timings (e.g., time between spell cast and follow-up action).
        - Explore features derived from computer vision (e.g., identifying specific visual cues).
        - Develop features to represent ally and enemy intentions/likely actions based on their movement and state.
   - Export to `data/features/taric_features.csv`

6. **Reinforcement Learning Setup**
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

7. **Model Training**
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

8. **Model Evaluation & Tuning**
   - Create evaluation suite with:
     - Win rate against different champions
     - Average KDA
     - Objective control rate
     - Team fight participation
        - Key Taric metric analysis (Heal/Shield amount, Stun uptime, Ult effectiveness).
        - Comparison of AI metrics against high-ELO human players.
   - Implement hyperparameter tuning
   - Save best parameters to `reports/hyperparam_tuning.md`

9. **Inference & Game Integration**
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

10. **Testing & Validation**
   - Create test suite for model behavior
   - Implement unit tests for feature engineering
   - Add integration tests for full pipeline
   - Create benchmark against human players
    - Automated testing environment setup (e.g., using custom games).
    - Testing against Riot's built-in bots.

11. **Deployment & Monitoring**
   - `src/cli.py`: CLI entry point
   - Implement logging and monitoring
   - Create performance dashboards
   - Set up automated retraining pipeline
    - Consider ethical implications and Riot's Terms of Service regarding bot usage.
    - Implement safeguards against detection by anti-cheat systems (if operating in environments where this is relevant - though note Riot's Vanguard rollout).

12. **AI Action Visualization & Testing**
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