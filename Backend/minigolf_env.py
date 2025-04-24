import time
import gym
import numpy as np
import requests
from gym import spaces
from app import ShotData, Vector3, WallData
from typing import List

MAX_WALLS = 12

class MiniGolfEnv(gym.Env):
    def __init__(self, agent_id: int = 1):
        super(MiniGolfEnv, self).__init__()
        obs_size = 3 + 3 + MAX_WALLS * 5 # 3 for ball position, 3 for hole position, and 5 for each wall (x, y, z, width, rotation)

        # Define action space: [power, direction_x, direction_z]
        # The original range [0, 200] is correct, but we need to normalize the model's output for better learning
        self.action_space = spaces.Box(
            low=np.array([0.01, -1, -1]), # Modified to allow all possible directions
            high=np.array([1, 1, 1]),  # Power normalized to [0,1], will be scaled up later
            dtype=np.float32
        )

        self.observation_space = spaces.Box(
            low=-np.inf, 
            high=np.inf, 
            shape=(obs_size,), 
            dtype=np.float32
        )

        self.agent_id = agent_id
        self.shots = 0
        self.max_shots = 5
        self.base_url = "http://127.0.0.1:8001"
        self.ball_position = np.zeros(3, dtype=np.float32)
        self.hole_position = np.zeros(3, dtype=np.float32)
        self.out_of_bounds = False
        self.max_power = 25.0  # Maximum power value for Unity (matching MaxForce in BallControl)
        self.previous_distance_to_hole = 0

    def step(self, action):
        info = {} 
        done = False
        reward = 0

        # Scale power from [0,1] to [0,max_power]
        power_normalized = action[0]
        power = power_normalized * self.max_power
        
        direction_x, direction_z = action[1], action[2]

        norm = np.sqrt(direction_x**2 + direction_z**2) # normalize direction vector to unit length
        if norm > 0:
            direction_x /= norm
            direction_z /= norm
        else:
            direction_x = 0
            direction_z = 1  # Default direction if zero vector

        direction = Vector3(x=direction_x, y=0, z=direction_z)

        shot_data = ShotData(
            agent_id=self.agent_id,
            power=power,
            direction=direction
        )

        self.previous_distance_to_hole = np.linalg.norm(self.ball_position - self.hole_position)
        
        shot_response = requests.post(f"{self.base_url}/shoot?agent_id={self.agent_id}", json=shot_data.model_dump())

        # # print(f"[DEBUG] Shot data sent: {shot_data.model_dump()}")
        # if shot_response.status_code ==  200:
        #     print(f"[DEBUG] Response received: {shot_response.json()}")
        # else:
        #     print(f"[ERROR] No response for shot received from Unity.")

        self.shots += 1
        # print(f"[DEBUG] Agent {self.agent_id} has taken a shot. Total shots: {self.shots}")
        self._ball_is_stationary()
        # print(f"[DEBUG] Ball has stopped moving. Shots taken: {self.shots}")

        # print(f"[DEBUG] Fetching environment data after shot...")
        obs = self._get_environment_data()
        self.ball_position = obs[:3]
        self.hole_position = obs[3:6]

        reward, done = self._calculate_reward()
            
        return obs, reward, done, info

    def reset(self):
        # print(f"[DEBUG] Resetting environment for agent {self.agent_id}...")
        
        env_data = self._get_environment_data()
        self.ball_position = env_data[:3]
        self.hole_position = env_data[3:6]
        self.shots = 0
        self.out_of_bounds = False
        self.previous_distance_to_hole = np.linalg.norm(self.ball_position - self.hole_position)

        success = False
        retry_count = 0
        while not success and retry_count < 5:
            try:
                reset_response = requests.post("http://127.0.0.1:8001/reset", timeout=5, json={})
                if reset_response.status_code == 200:
                    # print("[DEBUG] Reset confirmed. Moving to next generation...")
                    time.sleep(1)  # Small delay to ensure reset is processed
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

        return env_data

    # def _calculate_reward(self):
    #     reward = 0
    #     done = False
    #     distance_to_hole = np.linalg.norm(self.ball_position - self.hole_position)
    #     # print(f"[DEBUG] Distance to hole: {distance_to_hole}")
    #     if distance_to_hole < 0.2: # Increased hole detection radius for better rewards
    #         reward += 100 * (self.max_shots - self.shots)
    #         done = True
    #     if self.out_of_bounds: # if the ball is out of bounds
    #         reward -= 10
    #         done = True
    #     if self.shots >= self.max_shots: # if the agent has exhausted its shots
    #         reward -= 10 * distance_to_hole
    #         done = True
    #     reward -= self.shots * 5 # penalize for each shot taken
        
    #     return reward, done

    def _calculate_reward(self):
        reward = 0
        done = False

        distance_to_hole = np.linalg.norm(self.ball_position - self.hole_position)

        # Encourage getting closer to the hole
        progress = self.previous_distance_to_hole - distance_to_hole
        reward += 10 * progress  # small positive reward for improvement

        if distance_to_hole < 0.2:
            reward += 1000 * (self.max_shots - self.shots) + 1000  # success bonus scaled by efficiency
            done = True

        if self.out_of_bounds:
            reward -= 20
            done = True

        if self.shots >= self.max_shots:
            reward -= 5 + 5 * distance_to_hole  # penalty scaled by how far from goal
            done = True

        # Small penalty per shot
        reward -= 1

        self.previous_distance_to_hole = distance_to_hole  # update for next step

        return reward, done


    def _ball_is_stationary(self):
        ball_moving = True
        while ball_moving:
            status_response = requests.get(f"{self.base_url}/ball_velocity?agent_id={self.agent_id}")
            if status_response.status_code == 200:
                ball_moving = status_response.json().get("is_moving", False)
                if ball_moving:
                    import time
                    sleep = 3 # seconds
                    # print(f"[DEBUG] Sleeping for {sleep} seconds...")
                    time.sleep(sleep)  # Small delay to wait for ball to stop
                    # print(f"[DEBUG] I am awake!")
            else:
                # print(f"[ERROR] Failed to get ball status. Status code: {status_response.status_code}")
                break
        
    def _get_environment_data(self) -> np.ndarray:
        url = f"{self.base_url}/environment?agent_id={self.agent_id}"

        response = requests.get(url=url)

        # print(f"[DEBUG] _get_environment_data response for agent {response.json()["agent_id"]}")

        if response.status_code == 200:
            data = response.json()
            ball_pos = data["ball_position"]
            hole_pos = data["hole_position"]
            walls = data["walls"]

            ball_position = np.array([ball_pos["x"], ball_pos["y"], ball_pos["z"]])
            hole_position = np.array([hole_pos["x"], hole_pos["y"], hole_pos["z"]])
            wall_data = np.zeros(MAX_WALLS * 5, dtype=np.float32)
            
            num_walls = min(len(walls), MAX_WALLS)

            for i in range(num_walls):
                wall = walls[i]
                hit_point = wall["hitPoint"]
                
                wall_data[i*5] = hit_point["x"]
                wall_data[i*5+1] = hit_point["y"]
                wall_data[i*5+2] = hit_point["z"]
                wall_data[i*5+3] = wall["width"]
                wall_data[i*5+4] = wall["rotation"]

            obs = np.concatenate((ball_position, hole_position, wall_data))
            return obs
        else:
            # print(f"[ERROR] Failed to get environment data. Status code: {response.status_code}")
            return None
