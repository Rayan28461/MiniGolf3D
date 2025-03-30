import gym
import numpy as np
import requests
from gym import spaces
import random
from typing import Dict, Any

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

        # Define observation space: [ball_x, ball_y, ball_z, hole_x, hole_y, hole_z]
        self.observation_space = spaces.Box(
            low=-np.inf, 
            high=np.inf, 
            shape=(6,), 
            dtype=np.float32
        )

        self.agent_id = agent_id
        # self.number_of_agents = number_of_agents
        self.base_url = "http://127.0.0.1:8001"
        self.shots = 0
        self.max_shots = 5
        self.ball_position = None
        self.hole_position = None
        self.walls = []

    def step(self, action):
        """Apply action (shot) and return new state, reward, done, info."""
        power, direction_x, direction_z = action

        # Prepare environment data for shot
        env_data = {
            "agent_id": self.agent_id,
            "ball_position": {
                "x": float(self.ball_position[0]),
                "y": float(self.ball_position[1]),
                "z": float(self.ball_position[2])
            },
            "hole_position": {
                "x": float(self.hole_position[0]),
                "y": float(self.hole_position[1]),
                "z": float(self.hole_position[2])
            },
            "walls": [{"x": float(w[0]), "y": float(w[1]), "z": float(w[2])} for w in self.walls]
        }

        # Send shot request
        shot_response = requests.post(f"{self.base_url}/shoot", json=env_data).json()
        
        # Update environment state
        next_state = self._get_environment_data()
        
        # Calculate Euclidean distance between ball and hole
        distance_to_hole = np.linalg.norm(next_state[:3] - next_state[3:])
        
        # Define reward structure
        if distance_to_hole < 0.1:
            reward = 100.0
            done = True
        elif self.shots >= self.max_shots:
            reward = -distance_to_hole
            done = True
        else:
            reward = -1
            done = False

        # Update shots counter
        self.shots += 1
        
        # Update positions
        self.ball_position = next_state[:3]
        self.hole_position = next_state[3:]

        info = {
            "shots": self.shots,
            "distance_to_hole": distance_to_hole,
            "agent_id": self.agent_id
        }

        return next_state, reward, done, info
    
    def _get_environment_data(self) -> np.ndarray:
        # Replace the single GET call with a loop that waits for a valid response.
        import time
        while True:
            try:
                response = requests.get(f"{self.base_url}/environment", params={"agent_id": self.agent_id}, timeout=10)
                response.raise_for_status()
                env_data = response.json()
                # Check if the response contains valid position data
                if "agent_position" in env_data or "ball_position" in env_data:
                    break
            except Exception as e:
                print("Waiting for response from Unity server...", e)
            time.sleep(0.5)

        # Use "agent_position" if present; otherwise, fallback to "ball_position"
        if "agent_position" in env_data:
            ball_pos = env_data["agent_position"]
        else:
            ball_pos = env_data["ball_position"]

        hole_pos = env_data["hole_position"]

        # If multiple agents data exists, expect lists of positions
        if "ball_positions" in env_data and "hole_positions" in env_data:
            ball_pos = env_data["ball_positions"][self.agent_id - 1]
            hole_pos = env_data["hole_positions"][self.agent_id - 1]

        return np.array([
            ball_pos["x"], ball_pos["y"], ball_pos["z"],
            hole_pos["x"], hole_pos["y"], hole_pos["z"]
        ])
    
    def reset(self):
        """Reset the environment to its initial state and get initial observation."""

        env_data = self._get_environment_data()
        self.ball_position = env_data[:3]
        self.hole_position = env_data[3:]
        return env_data
    
    def render(self, mode="human"):
        """Render the environment."""
        if mode == "human":
            print(f"Agent ID: {self.agent_id}")
            print(f"Ball Position: {self.ball_position}")
            print(f"Hole Position: {self.hole_position}")
            print(f"Shots: {self.shots}")
            print("-" * 50)  # Print a line of 50 dashes as a visual separator

    def close(self):
        """Clean up environment."""
        pass

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


