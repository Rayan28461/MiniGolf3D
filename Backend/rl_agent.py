import os
# import random
# import numpy as np
# import gym
from minigolf_env import MiniGolfEnv
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, SubprocVecEnv
from typing import Dict
import requests
import torch
import time
from stable_baselines3.common.callbacks import BaseCallback

MODEL_PATH = "ppo_minigolf_multi"  # model file expected as "ppo_minigolf_multi.zip"


# NEW: Callback to track per-agent shot counts during training.
class ShotsTrackingCallback(BaseCallback):
    def __init__(self, verbose=0):
        super(ShotsTrackingCallback, self).__init__(verbose)
        self.reset_sent = False

    def _on_step(self) -> bool:
        return True
        # all_exhausted = True
        # for env in self.training_env.envs:
        #     current_shots = getattr(env, "shots", 0)
        #     max_shots = getattr(env, "max_shots", 5)
        #     remaining = max_shots - current_shots
        #     print(f"[DEBUG] Agent {env.agent_id} remaining shots: {remaining}")
        #     if remaining > 0:
        #         all_exhausted = False

        # if all_exhausted and not self.reset_sent:
        #     print("[DEBUG] All agents exhausted. Sending reset request...")
        #     success = False
        #     retry_count = 0
        #     while not success and retry_count < 5:
        #         try:
        #             reset_response = requests.post("http://127.0.0.1:8001/reset", timeout=5, json={})
        #             if reset_response.status_code == 200:
        #                 print("[DEBUG] Reset confirmed. Moving to next generation...")
        #                 success = True
        #             else:
        #                 print("[DEBUG] Reset request failed, retrying... Status:",
        #                       reset_response.status_code, reset_response.text)
        #         except Exception as e:
        #             print("[DEBUG] Reset request error, retrying...", e)
        #         if not success:
        #             time.sleep(2)
        #             retry_count += 1
        #     if not success:
        #         print("[DEBUG] Failed to reset environment after multiple attempts. Continuing without reset.")
        #     # Block further environment processing until reset is complete
        #     for env in self.training_env.envs:
        #         env.shots = 0
        #     self.reset_sent = True
        # else:
        #     if not all_exhausted:
        #         self.reset_sent = False
        # return True

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

def make_env(agent_id):
    def _init():
        env = MiniGolfEnv(agent_id=agent_id)
        return env
    return _init

def train_rl_agent(num_agents: int, total_timesteps: int = 10000):
    env_fns = [make_env(i+1) for i in range(num_agents)]
    # Wrap each environment to ensure it sets default shot tracking.
    vec_env = DummyVecEnv(env_fns)
    device = "cuda" if torch.cuda.is_available() else "cpu" # choose device
    model = PPO("MlpPolicy", vec_env, verbose=1, device=device)
    print(f"Training model for {num_agents} agents for {total_timesteps} timesteps on {device}...")
    # Pass the custom callback to track shots and trigger resets.
    model.learn(total_timesteps=total_timesteps, callback=ShotsTrackingCallback(verbose=1), progress_bar=True)
    model.save(MODEL_PATH)
    print("Training complete and model saved to", MODEL_PATH + ".zip")
    return model

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

if __name__ == "__main__":
    import sys
    if "--train" in sys.argv:
        agent_count = 1
        print(f"Manual training: Detected {agent_count} agents.")
        # train_rl_agent(num_agents=agent_count, total_timesteps=20000)
        load_or_train_model()
    else:
        print("No training command detected. Exiting.")
