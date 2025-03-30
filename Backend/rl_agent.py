import os
import random
import numpy as np
import gym
from minigolf_env import MiniGolfEnv
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv
from typing import Dict
import requests

MODEL_PATH = "ppo_minigolf_multi"  # model file expected as "ppo_minigolf_multi.zip"

# Helper: Create new environment for each agent.
def make_env(agent_id):
    def _init():
        env = MiniGolfEnv(agent_id=agent_id)
        return env
    return _init

# Train RL model with multiple agents parallelized using DummyVecEnv.
def train_rl_agent(num_agents: int = 4, total_timesteps: int = 10000):
    env_fns = [make_env(i+1) for i in range(num_agents)]
    vec_env = DummyVecEnv(env_fns)
    model = PPO("MlpPolicy", vec_env, verbose=1)
    print(f"Training model for {num_agents} agents for {total_timesteps} timesteps...")
    model.learn(total_timesteps=total_timesteps)
    model.save(MODEL_PATH)
    print("Training complete and model saved to", MODEL_PATH + ".zip")
    return model

# Returns the model; if not found, automatically trains one.
def load_or_train_model():
    if not os.path.exists(MODEL_PATH + ".zip"):
        print("Model file not found. Auto-training a new RL model...")
        # You can adjust num_agents and total_timesteps accordingly.
        train_rl_agent(num_agents=4, total_timesteps=10000)
    try:
        model = PPO.load(MODEL_PATH)
        return model
    except Exception as e:
        print(f"Error loading trained model: {e}")
        return None

def calculate_shot(env_data: Dict) -> Dict:
    """
    Multi-agent prediction:
    - Ensures that the trained model exists (auto-trains if needed).
    - Loads the trained model.
    - Queries the live environment state from Unity before predicting.
    - Constructs the observation vector [ball_x, ball_y, ball_z, hole_x, hole_y, hole_z].
    - Predicts and returns the shot decision.
    """
    model = load_or_train_model()
    if model is None:
        # Fallback: return a random valid shot.
        return {
            "agent_id": env_data["agent_id"],
            "power": random.uniform(1.0, 5.0),
            "direction": {"x": random.uniform(-1.0, 1.0), "y": 0.0, "z": random.uniform(-1.0, 1.0)}
        }
    agent_id = env_data["agent_id"]
    # Query latest state via HTTP.
    live_state = get_latest_state(agent_id)
    if not live_state:
        live_state = {
            "ball_position": env_data["ball_position"],
            "hole_position": env_data["hole_position"]
        }
    ball = live_state.get("ball_position", env_data["ball_position"])
    hole = live_state.get("hole_position", env_data["hole_position"])
    obs = np.array([ball["x"], ball["y"], ball["z"], hole["x"], hole["y"], hole["z"]], dtype=np.float32)
    action, _ = model.predict(obs.reshape(1, -1), deterministic=True)
    # Expected output: [power, direction_x, direction_z]
    shot = {
        "agent_id": agent_id,
        "power": float(action[0]),
        "direction": {"x": float(action[1]), "y": 0.0, "z": float(action[2])}
    }
    return shot

# NEW: Helper to get latest state from Unity.
def get_latest_state(agent_id: int) -> Dict:
    url = f"http://127.0.0.1:8001/environment?agent_id={agent_id}"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching latest state for agent {agent_id}: {e}")
        return {}

# Manual training command; run with: python rl_agent.py -train
if __name__ == "__main__":
    import sys
    if "-train" in sys.argv:
        # Trigger manual training command.
        train_rl_agent(num_agents=4, total_timesteps=20000)
    else:
        # Simple test of calculate_shot() with dummy environment data.
        dummy_env = {
            "agent_id": 1,
            "ball_position": {"x": 0, "y": 0, "z": 0},
            "hole_position": {"x": 10, "y": 0, "z": 10},
            "walls": []
        }
        shot = calculate_shot(dummy_env)
        print("Shot computed:", shot)
