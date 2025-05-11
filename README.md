# Taric Bot AI

An AI-powered system for playing Taric in League of Legends using reinforcement learning techniques. This project aims to collect high-quality gameplay data from skilled Taric players to ultimately build a real-time playing AI.

## Project Overview

This project aims to create an AI model that can learn optimal Taric gameplay strategies from high-ranking players and eventually be able to play the champion in real-time. The current phase focuses on comprehensive data collection and feature engineering to establish the foundation for the reinforcement learning model.

## Project Structure

```
├── data/                     # Data directory
│   ├── raw/                  # Raw match data
│   ├── cleaned/              # Processed match data
│   └── features/             # Engineered features
├── models/                   # Trained models
├── notebooks/                # Jupyter notebooks
├── src/                      # Source code
│   ├── api_client.py         # Riot API client
│   ├── collect_data.py       # Data collection script
│   ├── config.py             # Configuration settings
│   ├── predict.py            # Prediction script
│   ├── process_data.py       # Data processing script  
│   ├── features/             # Feature engineering modules
│   │   └── taric_features.py # Taric-specific features
│   └── models/               # ML models
│       └── taric_model.py    # Taric gameplay model
└── requirements.txt          # Project dependencies
```

## Current Phase: Data Collection & Feature Engineering

The project is currently in the data collection and feature engineering phase. The focus is on gathering high-quality gameplay data from Diamond+ tier Taric players, with special emphasis on Estaed#TAR's gameplay.

## Features

- **Data Collection**: Collects match data from high-ELO Taric players using the Riot API, with focus on Diamond+ games
- **Data Processing**: Extracts Taric-specific information from match data
- **Feature Engineering**: Calculates meaningful features for Taric gameplay analysis
- **Initial Model**: Preliminary model for analyzing gameplay patterns (not the final RL agent)

## Future Goals

- Implement a proper reinforcement learning environment for Taric
- Create a real-time playing agent capable of controlling Taric in-game
- Develop sophisticated action-decision mechanisms for optimal Taric play
- Train the agent using deep reinforcement learning techniques

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/Taric_Bot_AI.git
   cd Taric_Bot_AI
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file with your Riot API key:
   ```
   RIOT_API_KEY=your-api-key-here
   ```

## Data Collection Usage

The focus of the current phase is comprehensive data collection. Here are the main ways to collect data:

### Collect All Estaed#TAR Taric Games

```
python -m src.collect_data --estaed --count 50
```

### Collect Diamond+ Taric Games from Top Players

```
python -m src.collect_data --top-players --count 10 --min-tier DIAMOND
```

### Collect High-ELO Taric Games Directly

```
python -m src.collect_data --high-elo --count 20 --min-tier DIAMOND
```

### Process the Collected Data

```
python -m src.process_data
```

### Extract Features

```
python -m src.features.taric_features
```

## Data Analysis

While the current focus is on data collection, the project includes basic analysis capabilities to understand gameplay patterns:

```
python -m src.predict --healing 15000 --shielding 2000 --assists 12 --deaths 3
```

## Taric Gameplay Aspects Being Analyzed

### Combat Mechanics
- Healing efficiency
- Shielding efficiency
- Q (Starlight's Touch) usage
- E (Dazzle) stun accuracy
- R (Cosmic Radiance) timing
- Death prevention

### Positioning
- Vision control
- Ward placement
- Objective participation
- Positioning relative to allies

### Game State Awareness
- Early game impact
- Mid game objective control
- Late game team fighting
- Team composition synergy

### Mechanical Execution
- Ability sequencing
- W (Bastion) target selection
- Auto-attack weaving between abilities

## Development Roadmap

1. **Phase 1: Data Collection (Current)** - Gathering comprehensive gameplay data from high-ELO Taric players
2. **Phase 2: Environment Simulation** - Creating a proper reinforcement learning environment for Taric
3. **Phase 3: Agent Development** - Building the real-time playing agent using RL techniques
4. **Phase 4: Training & Optimization** - Training and refining the agent's gameplay capabilities
5. **Phase 5: Testing & Evaluation** - Evaluating the agent's performance in real game scenarios

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- Riot Games API for providing access to match data
- High-ELO Taric players, especially Estaed#TAR, for providing valuable gameplay data
- League of Legends community for insights into Taric gameplay 