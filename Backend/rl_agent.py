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
from app import ShotData, Vector3
import numpy as np

MODEL_PATH = "ppo_minigolf_multi_1"  # model file expected as "ppo_minigolf_multi.zip"


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
    # model = PPO("MlpPolicy", vec_env, verbose=1, device=device)
    model = PPO("MlpPolicy", vec_env, verbose=1, n_steps=512, batch_size=64, n_epochs=4, device=device)
    print(f"Training model for {num_agents} agents for {total_timesteps} timesteps on {device}...")
    # Pass the custom callback to track shots and trigger resets.
    model.learn(total_timesteps=total_timesteps, callback=ShotsTrackingCallback(verbose=1), progress_bar=True)
    model.save(MODEL_PATH)
    print("Training complete and model saved to", MODEL_PATH + ".zip")
    return model

def continue_training(total_timesteps: int = 10000):
    """
    Load existing model and continue training it with additional timesteps.
    
    Args:
        total_timesteps: Number of additional timesteps to train for
    
    Returns:
        The trained model
    """
    # Check if model exists
    if not os.path.exists(MODEL_PATH + ".zip"):
        print("Model does not exist. Please train a model first using --train")
        return None
        
    try:
        # Load existing model
        print(f"Loading existing model from {MODEL_PATH}")
        model = PPO.load(MODEL_PATH)
        
        # Get number of agents from backend
        agent_count = wait_for_agent_count()
        print(f"[DEBUG] Continuing training with {agent_count} agent(s) for {total_timesteps} additional timesteps")
        
        # Create environments for training
        env_fns = [make_env(i+1) for i in range(agent_count)]
        vec_env = DummyVecEnv(env_fns)
        
        # Set the environment for the loaded model
        model.set_env(vec_env)
        
        # Continue training
        print(f"Continuing training for {total_timesteps} timesteps...")
        model.learn(total_timesteps=total_timesteps, callback=ShotsTrackingCallback(verbose=1), progress_bar=True, reset_num_timesteps=False)
        
        # Save the model
        model.save(MODEL_PATH)
        print("Training complete and model saved to", MODEL_PATH + ".zip")
        
        return model
    except Exception as e:
        print(f"Error continuing training: {e}")
        return None

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

def predict_shot(agent_id, env_data):
    """
    Use the trained model to predict the best shot for the given environment state.
    
    Args:
        agent_id: ID of the agent making the shot
        env_data: Observation data from the environment
        
    Returns:
        ShotData object with the predicted shot parameters
    """
    # Convert observation to the format expected by the model
    observation = np.array(env_data, dtype=np.float32)
    
    # Get the action from the model
    action, _ = model.predict(observation, deterministic=True)
    
    # Scale power from [0,1] to [0,max_power]
    power_normalized = action[0]
    power = power_normalized * 25.0  # max_power value
    
    direction_x, direction_z = action[1], action[2]
    
    # Normalize direction vector
    norm = np.sqrt(direction_x**2 + direction_z**2)
    if norm > 0:
        direction_x /= norm
        direction_z /= norm
    else:
        direction_x = 0
        direction_z = 1  # Default direction if zero vector
    
    shot_data = ShotData(
        agent_id=agent_id,
        power=power,
        direction=Vector3(x=direction_x, y=0, z=direction_z)
    )
    
    return shot_data

def execute_shot(shot_data, base_url="http://127.0.0.1:8001"):
    """
    Send the shot data to the game and wait for the ball to stop.
    
    Args:
        shot_data: ShotData object with shot parameters
        base_url: URL of the game server
        
    Returns:
        True if shot was executed successfully, False otherwise
    """
    try:
        shot_response = requests.post(
            f"{base_url}/shoot?agent_id={shot_data.agent_id}", 
            json=shot_data.model_dump()
        )
        
        if shot_response.status_code != 200:
            print(f"Error executing shot: {shot_response.status_code}")
            return False
            
        # Wait for the ball to stop moving
        ball_moving = True
        while ball_moving:
            status_response = requests.get(f"{base_url}/ball_velocity?agent_id={shot_data.agent_id}")
            if status_response.status_code == 200:
                ball_moving = status_response.json().get("is_moving", False)
                if ball_moving:
                    time.sleep(0.5)  # Small delay before checking again
            else:
                print(f"Error getting ball status: {status_response.status_code}")
                return False
                
        return True
    except Exception as e:
        print(f"Exception during shot execution: {e}")
        return False

if __name__ == "__main__":
    import sys
    if "--train" in sys.argv:
        agent_count = 1
        print(f"Manual training: Detected {agent_count} agents.")
        model = load_or_train_model()
        if model is None:
            print("Failed to load or train model. Exiting.")
            exit(1)
        continue_training(total_timesteps=10000)
    elif "--play" in sys.argv:
        model = load_or_train_model()
        if model is None:
            print("Failed to load model. Exiting.")
            exit(1)
            
        print("Model loaded successfully. Ready to play!")
        
        # Create an environment instance for getting observations
        env = MiniGolfEnv(agent_id=1)
        
        # Main game loop
        shots = 0
        while shots < 5:
            try:
                # Get the current environment state
                observation = env._get_environment_data()
                if observation is None:
                    print("Failed to get environment data. Waiting...")
                    time.sleep(2)
                    continue
                    
                # Predict and execute shot
                shot_data = predict_shot(env.agent_id, observation)
                print(f"Taking shot with power: {shot_data.power:.2f}, direction: ({shot_data.direction.x:.2f}, {shot_data.direction.z:.2f})")
                
                success = execute_shot(shot_data)
                if not success:
                    print("Shot execution failed. Retrying...")
                    time.sleep(1)
                    continue
                
                shots += 1

                # Wait a bit before the next shot to allow for any game processing
                time.sleep(1)
                
            except KeyboardInterrupt:
                print("Game interrupted by user. Exiting.")
                break
            except Exception as e:
                print(f"Error in game loop: {e}")
                time.sleep(2)