import gym
import numpy as np
import requests
from gym import spaces
from app import ShotData, Vector3
# import random
# from typing import Dict, Any

class MiniGolfEnv(gym.Env):
    metadata = {'render.modes': ['human']}

    def __init__(self, agent_id: int = 1):
        """
        Initialize the MiniGolf environment.
        
        Args:
            agent_id (int): Unique identifier for the agent. Defaults to 1.
                           Use different IDs for different agents when training multiple agents.
            number_of_agents (int): Total number of agents in Unity.
        """
        super(MiniGolfEnv, self).__init__()

        # Define action space: [power, direction_x, direction_z]
        self.action_space = spaces.Box(
            low=np.array([0, -1, -1]), 
            high=np.array([6, 1, 1]), 
            dtype=np.float32
        )

        # Define observation space
        self.observation_space = spaces.Box(
            low=-np.inf, 
            high=np.inf, 
            shape=(6,), 
            dtype=np.float32
        )

        self.agent_id = agent_id
        self.shots = 0           # NEW: track number of shots taken
        self.max_shots = 5       # NEW: maximum allowed shots per episode
        self.base_url = "http://127.0.0.1:8001"
        self.ball_position = None
        self.hole_position = None
        self.walls = []

    def step(self, action):
        info = {} 
        done = False
        reward = 0

        power, direction_x, direction_z = action

        norm = np.sqrt(direction_x**2 + direction_z**2) # normalize direction vector to unit length
        if norm > 0:
            direction_x /= norm
            direction_z /= norm
        else:
            direction_x = 0
            direction_z = 0
        direction = Vector3(x=direction_x, y=0, z=direction_z)

        shot_data = ShotData(
            agent_id=self.agent_id,
            power=power,
            direction=direction
        )
        
        shot_response = requests.post(f"{self.base_url}/shoot?agent_id={self.agent_id}", json=shot_data.model_dump())

        print(f"[DEBUG] Shot data sent: {shot_data.model_dump()}")
        if shot_response.status_code ==  200:
            print(f"[DEBUG] Response received: {shot_response.json()}")
        else:
            print(f"[ERROR] No response for shot received from Unity.")

        self.shots += 1
        self._ball_is_stationary()
        print(f"[DEBUG] Ball has stopped moving. Shots taken: {self.shots}")

        print(f"[DEBUG] Fetching environment data after shot...")
        obs = self._get_environment_data()
        self.ball_position = obs[:3]
        self.hole_position = obs[3:]

        if self.shots >= self.max_shots:
            done = True
            print(f"[INFO] Episode finished. Total shots taken: {self.shots}")
            
        return obs, reward, done, info

    def _calculate_reward(self) -> int:
        pass

    def _ball_is_stationary(self):
        ball_moving = True
        while ball_moving:
            status_response = requests.get(f"{self.base_url}/ball_velocity?agent_id={self.agent_id}")
            if status_response.status_code == 200:
                ball_moving = status_response.json().get("is_moving", False)
                if ball_moving:
                    import time
                    sleep = 5 # seconds
                    print(f"[DEBUG] Sleeping for {sleep} seconds...")
                    time.sleep(sleep)  # Small delay to avoid flooding the server
                    print(f"[DEBUG] I am awake!")
            else:
                print(f"[ERROR] Failed to get ball status. Status code: {status_response.status_code}")
                break
        
    def _get_environment_data(self) -> np.ndarray:
        url = f"{self.base_url}/environment?agent_id={self.agent_id}"

        response = requests.get(url=url)

        print(f"[DEBUG] _get_environment_data response for agent {response.json()["agent_id"]}")

        if response.status_code == 200:
            data = response.json()
            ball_pos = data["ball_position"]
            hole_pos = data["hole_position"]
            ball_position = np.array([ball_pos["x"], ball_pos["y"], ball_pos["z"]])
            hole_position = np.array([hole_pos["x"], hole_pos["y"], hole_pos["z"]])
            walls = [np.array(wall["hitPoint"]) for wall in data["walls"]]
            print(f"[DEBUG] ball position array: {ball_position}")
            print(f"[DEBUG] hole position array: {hole_position}")
            return np.concatenate((ball_position, hole_position))
        else:
            print(f"[ERROR] Failed to get environment data. Status code: {response.status_code}")
            return None

    def reset(self):
        """Reset the environment to its initial state and get initial observation."""

        env_data = self._get_environment_data()
        self.ball_position = env_data[:3]
        self.hole_position = env_data[3:]
        self.shots = 0
        
        return env_data

    # def render(self, mode="human"):
    #     """Render the environment."""
    #     if mode == "human":
    #         print(f"Agent ID: {self.agent_id}")
    #         print(f"Ball Position: {self.ball_position}")
    #         print(f"Hole Position: {self.hole_position}")
    #         print(f"Shots: {self.shots}")
    #         print("-" * 50)  # Print a line of 50 dashes as a visual separator

    # def close(self):
    #     """Clean up environment."""
    #     pass

# Example usage
if __name__ == "__main__":
    # Create and test the environment for a specific agent.
    env = MiniGolfEnv(agent_id=1)
    obs = env.reset()
    print("Starting MiniGolf Environment:")
    for _ in range(5):
        action = env.action_space.sample()
        obs, reward, done, info = env.step(action)
        env.render()
        if done:
            print(f"Episode finished with {info['shots']} shots!")
            obs = env.reset()
