# Taric Bot AI

A reinforcement learning project to develop an AI that can play the champion Taric in League of Legends.

## Project Structure

```
Taric_Bot_AI/
│
├── data/                # All data files
│   ├── raw/             # Raw match data from Riot API
│   ├── cleaned/         # Processed data files 
│   └── features/        # Engineered features for training
│
├── models/              # Trained model files
│
├── src/                 # Source code
│
├── notebooks/           # Jupyter notebooks for exploration and visualization
│
├── requirements.txt     # Python dependencies
└── README.md            # Project documentation
```

## Setup

1. Create and activate a virtual environment:
   ```
   python -m venv venv
   venv\Scripts\activate  # Windows
   source venv/bin/activate  # Unix/MacOS
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up Riot API key:
   Create a `.env` file in the project root and add your API key:
   ```
   RIOT_API_KEY=your-api-key-here
   ```

## Project Phases

1. **Data Collection & Preprocessing**
2. **Feature Engineering**
3. **Reinforcement Learning Setup**
4. **Model Training**
5. **Evaluation & Tuning**
6. **Inference & Game Integration**
7. **Testing & Validation**

## Contributing

This project follows a development workflow with two main branches:
- `main`: Stable, production-ready code
- `develop`: Development branch where feature branches are merged 