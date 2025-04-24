This project is a Unity-based mini-golf game that integrates with a Python backend for reinforcement learning. The AI agent can learn to play the game using PPO (Proximal Policy Optimization) algorithm, analyzing the environment and making shots automatically.

## Project Structure

- **Assets/**: Contains Unity game files, scripts, and resources
- **Backend/**: Python backend for reinforcement learning
  - app.py: FastAPI server that handles communication between Unity and RL agent
  - minigolf_env.py: Custom Gym environment for mini-golf
  - rl_agent.py: Reinforcement learning agent implementation
  - `ppo_minigolf_multi_1.zip`: Trained PPO model

## Setup and Running Instructions

### Prerequisites
- Python 3.12+

### Setting up the Python Backend

1. **Create and activate a virtual environment**

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

2. **Install requirements**

```bash
cd Backend
pip install -r requirements.txt
```

3. **Start the backend server**

```bash
python app.py
```

The server will start on `http://0.0.0.0:8000` and is ready to receive requests from the Unity game.

### Running the Game

1. Navigate to the MiniGolf folder
2. Run the executable (`MiniGolf.exe` on Windows)

## Game Controls

- **Mouse navigation**: Move the mouse to look around
- **Camera rotation**: Click and drag outside the ball circle
- **Shooting**: Click and drag inside the ball circle to set direction and power, release to shoot

## Playing Modes

### Manual Play
Simply use the controls described above to play the mini-golf game manually.

### AI-Assisted Play
1. Start the backend server (`python app.py`)
2. Start the game
3. The AI agent will automatically connect and start making shots

## Training Your Own AI Model

To train a new reinforcement learning model:

```bash
cd Backend
python rl_agent.py --train
```

This will start the training process, which may take several hours depending on your hardware. The trained model will be saved in the Backend directory.

## Using a Pre-trained Model

To use the pre-trained model included in the repository:

```bash
cd Backend
python rl_agent.py --play
```

The model will be loaded automatically when the game connects to the backend server.

## Troubleshooting

- If the backend fails to connect to the game, make sure both are running and check the port settings
- If the AI agent is not making shots, check the console output for error messages
- For more detailed logs, uncomment the debug print statements in the code

## Note
- Docker stopped working after adding a requirement for the backend, which caused dependency issues. The code is found in the repository but is not functional. The backend should be run locally instead.
- The game is designed for Windows. If you want to run it on macOS or Linux, you may need to adjust the build settings in Unity.

## Credits

Art Assets: https://www.kenney.nl/assets/minigolf-kit

## Contributors
- [Rayan Fakhreddine](github.com/Rayan28461)
- [Mohammad Al Masri](github.com/Mxsrii)
- [Karim Abboud](github.com/Kaa75)