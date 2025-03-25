import gym
import numpy as np
import requests
from gym import spaces
import app
import random

class MiniGolfEnv(gym.Env):

    metadata = {'render.modes': ['human']}


    """
    def __init__(self):
        super(MiniGolfEnv, self).__init__()
        self.action_space = spaces.Discrete(2)
        self.observation_space = spaces.Box(low=-1, high=1, shape=(6,))
        self.agent_id = 0
        self.shots = 0
        self.ball_position = np.array([0, 0, 0])
        self.hole_position = np.array([0, 0, 0])
        self.walls = []
        self.power = 0
        self.direction = np.array([0, 0, 0])"
    """

    def __init__(self):
        super(MiniGolfEnv, self).__init__()

        # Define action space: [power, direction_x, direction_z]
        self.action_space = spaces.Box(low=np.array([0, -1, -1]), high=np.array([6, 1, 1]), dtype=np.float32)

        # Define observation space: [ball_x, ball_y, ball_z, hole_x, hole_y, hole_z]
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(6,), dtype=np.float32)

        self.agent_id = 1 # if multiple agents?
        self.base_url = "http://127.0.0.1:8000"
        
    """""
    def step(self, action):
        # Send environment data to backend
        data = {
            "agent_id": self.agent_id,
            "ball_position": {"x": self.ball_position[0], "y": self.ball_position[1], "z": self.ball_position[2]},
            "hole_position": {"x": self.hole_position[0], "y": self.hole_position[1], "z": self.hole_position[2]},
            "walls": [{"x": w[0], "y": w[1], "z": w[2]} for w in self.walls]
        }
        response = requests.post("http://"
        "localhost:8000/shoot", json=data)
        response_data = response.json()
        self.power = response_data["power"]
        self.direction = np.array([response_data["direction"]["x"], response_data["direction"]["y"], response_data["direction"]["z"]])
        # Update ball position based on action
        if action == 0:
            self.ball_position += self.power * self.direction
        else:
            self.ball_position -= self.power * self.direction
        # Compute reward
        distance_to_hole = np.linalg.norm(self.ball_position - self.hole_position)
        reward = -distance_to_hole
        # Update shots
        self.shots += 1
        # Check if episode is done
        done = distance_to_hole < 0.1 or self.shots > 10
        return self._get_obs(), reward, done, {}
    
    def reset(self):
        self.shots = 0
        self.ball_position = np.array([0, 0, 0])
        self.hole_position = np.array([10, 0, 0])
        self.walls = [np.array([5, 0, 0]), np.array([5, 0, 5]), np.array([5, 0, -5])]
        return self._get_obs()
    """""

    def step(self, action):
        """Apply action (shot) and return new state, reward, done, info."""
        power, direction_x, direction_z = action

        # Send shot decision
        
        env_data = self._get_environment_data()
        ball_pos = {"x": env_data[0], "y": env_data[1], "z": env_data[2]}
        hole_pos = {"x": env_data[3], "y": env_data[4], "z": env_data[5]}

        shot_payload = {
            "agent_id": self.agent_id,
            "ball_position": ball_pos,
            "hole_position": hole_pos,
           # "walls": []  
        }

        shot_response = requests.post(f"{self.base_url}/shoot", json=shot_payload).json()

        # Get updated environment state
        next_state = self._get_environment_data()

        # TODO: Compute reward...

        #return next_state, reward, done, {}
    
    def _get_environment_data(self):
        """Helper function to fetch environment data from FastAPI."""
        # This should ideally be replaced with an actual API call once implemented
        env_data = requests.get(f"{self.base_url}/environment").json()
        ball_pos = env_data["ball_position"]
        hole_pos = env_data["hole_position"]

        return np.array([ball_pos["x"], ball_pos["y"], ball_pos["z"], hole_pos["x"], hole_pos["y"], hole_pos["z"]])
    
    
    def reset(self):
        """Reset the environment and get initial state."""
        response = requests.post(f"{self.base_url}/init", json={"agent_id": self.agent_id, "shots": 0})
        print(response.json())

        # Request environment data
        env_data = self._get_environment_data()

        # Store ball and hole positions
        self.ball_position = np.array([env_data[0], env_data[1], env_data[2]])
        self.hole_position = np.array([env_data[3], env_data[4], env_data[5]])

        return env_data
    
    
    def render(self, mode="human"):
        """Render the environment."""
        print(f"Ball: {self.ball_position}, Hole: {self.hole_position}") #or maybe another way to visualize the environment or from app.py

        pass

    def close(self):
        """Clean up environment."""
        pass

# Testing the environment


