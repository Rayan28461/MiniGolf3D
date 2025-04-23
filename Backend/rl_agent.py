import os
# import random
# import numpy as np
# import gym
import sys

# Set protobuf environment variable to avoid errors
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

try:
    from minigolf_env import MiniGolfEnv
    from stable_baselines3 import PPO
    from stable_baselines3.common.vec_env import DummyVecEnv, SubprocVecEnv
    from stable_baselines3.common.callbacks import BaseCallback
except TypeError as e:
    if "Descriptors cannot be created directly" in str(e):
        print("ERROR: Encountered protobuf error. Trying to fix...")
        # Try to fix the protobuf error by installing a compatible version
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "protobuf==3.20.3"])
        os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"
        print("Restarting the script to apply fixes...")
        os.execv(sys.executable, [sys.executable] + sys.argv)
    else:
        raise

from typing import Dict
import requests
import torch
import time
from app import ShotData, Vector3
import numpy as np
import argparse
import signal

# Get server URLs from environment variables or use defaults
APP_SERVER_URL = os.environ.get("APP_SERVER_URL", "http://127.0.0.1:8000")
AGENT_SERVER_URL = os.environ.get("AGENT_SERVER_URL", "http://127.0.0.1:8001")
DEBUG_MODE = os.environ.get("DEBUG_MODE", "false").lower() == "true"

# Signal handling for graceful exit
running = True
def signal_handler(sig, frame):
    global running
    debug_print("Received signal to terminate. Exiting gracefully...")
    running = False
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

MODEL_PATH = "ppo_minigolf_multi_1"  # model file expected as "ppo_minigolf_multi.zip"

def debug_print(*args, **kwargs):
    """Print only if debug mode is enabled"""
    if DEBUG_MODE:
        print("[DEBUG]", *args, **kwargs)
        sys.stdout.flush()  # Ensure output is flushed immediately

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
        response = requests.get(f"{APP_SERVER_URL}/get_agent_count", timeout=5)
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

def execute_shot(shot_data, base_url=AGENT_SERVER_URL):
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

def run_persistent_agent(model):
    """Run the agent in a persistent mode that doesn't exit"""
    debug_print("Starting persistent agent mode...")
    
    global running
    while running:
        try:
            debug_print("Checking for game session...")
            
            # Check if the app server is ready
            try:
                response = requests.get(f"{APP_SERVER_URL}/get_agent_count", timeout=5)
                if response.status_code == 200:
                    agent_count = response.json().get("agent_count", 0)
                    debug_print(f"Detected {agent_count} agents in game")
                    
                    if agent_count > 0:
                        debug_print("Game session detected. Starting agent loop...")
                        run_game_loop(model)
                    else:
                        debug_print("No active game session. Waiting...")
                else:
                    debug_print(f"Failed to get agent count. Status: {response.status_code}")
            except Exception as e:
                debug_print(f"Error connecting to app server: {e}")
            
            # Sleep before next check
            debug_print("Sleeping for 10 seconds before next check...")
            time.sleep(10)
            
        except Exception as e:
            debug_print(f"Error in persistent mode: {e}")
            time.sleep(10)

def run_game_loop(model):
    """Run a game loop for a single session"""
    
    shots = 0
    max_shots = 5
    max_attempts = 3
    
    while shots < max_shots and running:
        try:
            debug_print(f"Shot {shots+1}/{max_shots} - Getting environment data...")
            
            # Create an environment instance for getting observations
            env = MiniGolfEnv(agent_id=1)
            
            # Get the current environment state
            observation = None
            for attempt in range(max_attempts):
                observation = env._get_environment_data()
                if observation is not None:
                    break
                debug_print(f"Failed to get environment data. Attempt {attempt+1}/{max_attempts}")
                time.sleep(5)
            
            if observation is None:
                debug_print("All attempts to get environment data failed. Skipping this round.")
                return
                
            # Predict and execute shot
            debug_print("Predicting shot...")
            shot_data = predict_shot(1, observation)
            debug_print(f"Taking shot with power: {shot_data.power:.2f}, direction: ({shot_data.direction.x:.2f}, {shot_data.direction.z:.2f})")
            
            success = execute_shot(shot_data)
            if not success:
                debug_print("Shot execution failed. Moving to next round.")
                return
            
            shots += 1
            debug_print(f"Shot {shots}/{max_shots} completed")

            # Wait a bit before the next shot to allow for game processing
            time.sleep(5)
            
        except KeyboardInterrupt:
            debug_print("Game interrupted by user. Exiting.")
            break
        except Exception as e:
            debug_print(f"Error in game loop: {e}")
            time.sleep(5)
            break
    
    debug_print("Game session completed.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RL Agent for MiniGolf")
    parser.add_argument('--train', action='store_true', help='Train the agent')
    parser.add_argument('--continue-training', action='store_true', help='Continue training from saved model')
    parser.add_argument('--timesteps', type=int, default=10000, help='Number of timesteps to train for')
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    parser.add_argument('--persistent', action='store_true', help='Run in persistent mode (default in Docker)')
    args = parser.parse_args()
    
    # Set debug mode if passed as argument
    if args.debug:
        DEBUG_MODE = True

    # In Docker, default to persistent mode
    if os.environ.get("DOCKER_CONTAINER", "false").lower() == "true":
        args.persistent = True
    
    debug_print(f"Starting RL agent with: APP_SERVER_URL={APP_SERVER_URL}, AGENT_SERVER_URL={AGENT_SERVER_URL}")
    debug_print(f"Command line arguments: {args}")
    
    try:
        debug_print("Checking connection to app server...")
        response = requests.get(f"{APP_SERVER_URL}/get_agent_count", timeout=10)
        debug_print(f"App server response: {response.status_code} - {response.text}")
    except Exception as e:
        debug_print(f"Error connecting to app server: {e}")
        debug_print("Will continue anyway, hoping the connection will be established later.")
    
    model = None
    
    if args.train:
        agent_count = wait_for_agent_count()
        debug_print(f"Training model with {agent_count} agents for {args.timesteps} timesteps...")
        model = train_rl_agent(num_agents=agent_count, total_timesteps=args.timesteps)
    elif args.continue_training:
        debug_print(f"Continuing training for {args.timesteps} timesteps...")
        model = continue_training(total_timesteps=args.timesteps)
    else:
        # Just load the model
        debug_print("Loading existing model...")
        model = load_or_train_model()

    if model is None:
        debug_print("Failed to load or train model. Exiting.")
        exit(1)

    debug_print("Model loaded successfully. Ready to play!")
    
    if args.persistent:
        debug_print("Running in persistent mode")
        run_persistent_agent(model)
    else:
        debug_print("Running single game session")
        run_game_loop(model)
    
    debug_print("Agent exiting.")
    
    # Sleep indefinitely in Docker to keep container alive
    if DEBUG_MODE and os.environ.get("DOCKER_CONTAINER", "false").lower() == "true":
        debug_print("Debug mode enabled in Docker - keeping container alive indefinitely")
        while running:
            time.sleep(60)
            debug_print("Agent still alive, waiting for commands...")
