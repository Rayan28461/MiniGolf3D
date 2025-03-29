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
        self.base_url = "http://127.0.0.1:8000"
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
        distance_to_hole = np.linalg.norm(
            next_state[:3] - next_state[3:]  # distance = sqrt((ball_x - hole_x)^2 + (ball_y - hole_y)^2 + (ball_z - hole_z)^2)
        )
        
        # Define reward structure
        if distance_to_hole < 0.1:  # Ball in hole
            reward = 100.0
            done = True
        elif self.shots >= self.max_shots:  # Too many shots
            reward = -distance_to_hole  # Negative reward based on final distance
            done = True
        else:
            reward = -0.1  # Small negative reward for each shot to encourage efficiency
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
        """Helper function to fetch environment data from FastAPI."""
        env_data = requests.get(f"{self.base_url}/environment").json()
        ball_pos = env_data["ball_position"]
        hole_pos = env_data["hole_position"]

        return np.array([
            ball_pos["x"], ball_pos["y"], ball_pos["z"],
            hole_pos["x"], hole_pos["y"], hole_pos["z"]
        ])
    
    def reset(self):
        """Reset the environment and get initial state."""
        # Reset shots counter
        self.shots = 0
        
        # Initialize environment
        response = requests.post(
            f"{self.base_url}/init", 
            json={"agent_id": self.agent_id, "shots": self.shots}
        )
        
        # Get initial environment state
        env_data = self._get_environment_data()
        
        # Store positions
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
    # Create and test the environment
    env = MiniGolfEnv(agent_id=1)
    obs = env.reset()
    
    print("Starting MiniGolf Environment:")
    for _ in range(10):
        action = env.action_space.sample()
        obs, reward, done, info = env.step(action)
        env.render()
        if done:
            print(f"Episode finished with {info['shots']} shots!")
            obs = env.reset()


