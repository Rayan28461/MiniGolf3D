import os
import random
import numpy as np
import gym
from minigolf_env import MiniGolfEnv
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv
from typing import Dict
import requests
import torch
import time
from stable_baselines3.common.callbacks import BaseCallback

MODEL_PATH = "ppo_minigolf_multi"  # model file expected as "ppo_minigolf_multi.zip"

# NEW: Modified wait_for_agent_count() that performs a single request to get the agent count.
def wait_for_agent_count() -> int:
    try:
        response = requests.get("http://127.0.0.1:8000/get_agent_count", timeout=5)
        if response.status_code == 200:
            data = response.json()
            count = data.get("agent_count", 0)
            print(f"[DEBUG] Agent count received from backend: {count}")
            # Ensure a valid count; if 0, default to 1.
            return count if count > 0 else 1
    except Exception as e:
        print("Error getting agent count:", e)
    print("[DEBUG] Using fallback agent count: 1")
    return 1

# Helper: Create new environment for each agent.
def make_env(agent_id):
    def _init():
        env = MiniGolfEnv(agent_id=agent_id)
        return env
    return _init

# NEW: Callback to track per-agent shot counts during training.
class ShotsTrackingCallback(BaseCallback):
    def __init__(self, verbose=0):
        super(ShotsTrackingCallback, self).__init__(verbose)
        self.reset_sent = False

    def _on_step(self) -> bool:
        all_exhausted = True
        for env in self.training_env.envs:
            current_shots = getattr(env, "shots", 0)
            max_shots = getattr(env, "max_shots", 5)
            remaining = max_shots - current_shots
            print(f"[DEBUG] Agent {env.agent_id} remaining shots: {remaining}")
            if remaining > 0:
                all_exhausted = False

        if all_exhausted and not self.reset_sent:
            print("[DEBUG] All agents exhausted. Sending reset request...")
            success = False
            retry_count = 0
            while not success and retry_count < 5:
                try:
                    reset_response = requests.post("http://127.0.0.1:8001/reset_environment", timeout=5, json={})
                    if reset_response.status_code == 200:
                        print("[DEBUG] Reset confirmed. Moving to next generation...")
                        success = True
                    else:
                        print("[DEBUG] Reset request failed, retrying... Status:",
                              reset_response.status_code, reset_response.text)
                except Exception as e:
                    print("[DEBUG] Reset request error, retrying...", e)
                if not success:
                    time.sleep(2)
                    retry_count += 1
            if not success:
                print("[DEBUG] Failed to reset environment after multiple attempts. Continuing without reset.")
            # Block further environment processing until reset is complete
            for env in self.training_env.envs:
                env.shots = 0
            self.reset_sent = True
        else:
            if not all_exhausted:
                self.reset_sent = False
        return True

# Train RL model with multiple agents parallelized using DummyVecEnv.
def train_rl_agent(num_agents: int, total_timesteps: int = 10000):
    env_fns = [make_env(i+1) for i in range(num_agents)]
    # Wrap each environment to ensure it sets default shot tracking.
    vec_env = DummyVecEnv(env_fns)
    device = "cuda" if torch.cuda.is_available() else "cpu"  # NEW: choose device
    model = PPO("MlpPolicy", vec_env, verbose=1, device=device)
    print(f"Training model for {num_agents} agents for {total_timesteps} timesteps on {device}...")
    # Pass the custom callback to track shots and trigger resets.
    model.learn(total_timesteps=total_timesteps, callback=ShotsTrackingCallback(verbose=1))
    model.save(MODEL_PATH)
    print("Training complete and model saved to", MODEL_PATH + ".zip")
    return model

# Returns the model; if not found, wait for agent count and auto-train one.
def load_or_train_model():
    if not os.path.exists(MODEL_PATH + ".zip"):
        print("Model file not found. Retrieving agent count from backend...")
        agent_count = wait_for_agent_count()   # Single retrieval; no extra polling.
        print(f"[DEBUG] Training with {agent_count} agent(s) as per backend configuration.")
        train_rl_agent(num_agents=agent_count, total_timesteps=10000)
    try:
        model = PPO.load(MODEL_PATH)
        return model
    except Exception as e:
        print(f"Error loading trained model: {e}")
        return None

# def calculate_shot(env_data: Dict) -> Dict:
#     """
#     Multi-agent prediction:
#     - Ensures that the trained model exists (auto-trains if needed).
#     - Loads the trained model.
#     - Queries the live environment state from Unity before predicting.
#     - Constructs the observation vector [ball_x, ball_y, ball_z, hole_x, hole_y, hole_z].
#     - Predicts and returns the shot decision.
#     """
#     model = load_or_train_model()
#     if model is None:
#         # Fallback: return a random valid shot.
#         return {
#             "agent_id": env_data["agent_id"],
#             "power": random.uniform(1.0, 5.0),
#             "direction": {"x": random.uniform(-1.0, 1.0), "y": 0.0, "z": random.uniform(-1.0, 1.0)}
#         }
#     agent_id = env_data["agent_id"]
#     # Query latest state via HTTP.
#     live_state = get_latest_state(agent_id)
#     if not live_state:
#         live_state = {
#             "ball_position": env_data["ball_position"],
#             "hole_position": env_data["hole_position"]
#         }
#     ball = live_state.get("ball_position", env_data["ball_position"])
#     hole = live_state.get("hole_position", env_data["hole_position"])
#     obs = np.array([ball["x"], ball["y"], ball["z"], hole["x"], hole["y"], hole["z"]], dtype=np.float32)
#     action, _ = model.predict(obs.reshape(1, -1), deterministic=True)
#     # Expected output: [power, direction_x, direction_z]
#     shot = {
#         "agent_id": agent_id,
#         "power": float(action[0]),
#         "direction": {"x": float(action[1]), "y": 0.0, "z": float(action[2])}
#     }
#     return shot

def calculate_shot(env_data: Dict) -> Dict:
    import random
    # TEMPORARY: Return random shot variables instead of using the RL model.
    agent_id = env_data["agent_id"]
    shot = {
        "agent_id": agent_id,
        "power": random.uniform(1.0, 5.0),
        "direction": {"x": random.uniform(-1.0, 1.0), "y": 0.0, "z": random.uniform(-1.0, 1.0)}
    }
    # print(f"[TEMPORARY] Returning random shot for agent {agent_id}: {shot}")
    # requests.post("http://127.0.0.1:8000/update_shots", json={"agent_id": agent_id, "shots": 1})
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
        agent_count = wait_for_agent_count()
        print(f"Manual training: Detected {agent_count} agents from backend.")
        train_rl_agent(num_agents=agent_count, total_timesteps=20000)
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
