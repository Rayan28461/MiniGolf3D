from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List
import uvicorn
from rl_agent import calculate_shot
import asyncio
import requests

app = FastAPI()

# Data Models
class Vector3(BaseModel):
    x: float
    y: float
    z: float

class WallData(BaseModel):
    hitPoint: Vector3
    width: float
    rotation: float

class EnvironmentData(BaseModel):
    agent_id: int
    ball_position: Vector3
    hole_position: Vector3
    walls: List[WallData] = []

class ShotData(BaseModel):
    agent_id: int
    power: float
    direction: Vector3

# NEW: Model for agent count
class AgentCountData(BaseModel):
    agent_count: int

# NEW: Model for initialization request
class InitData(BaseModel):
    agent_id: int
    shots: int

# NEW: Global dictionaries to track agent shot counts and initial shots.
agent_shot_counts = {}  # Format: {agent_id: shots_remaining, ...}
initial_shots = {}      # Format: {agent_id: initial_shots, ...}
current_generation = 1

# Updated background task to periodically check shot counts and reset only after a successful response.
async def monitor_shot_counts():
    global agent_shot_counts, current_generation, initial_shots
    while True:
        await asyncio.sleep(5)
        print("Current agent shot counts:", agent_shot_counts)
        # Check if we have received shot count updates and if all agents have 0 shots remaining.
        if agent_shot_counts and all(shots <= 0 for shots in agent_shot_counts.values()):
            # Build mapping of id to number of shots done.
            shots_done = {agent: initial_shots[agent] - agent_shot_counts[agent] for agent in initial_shots.keys()}
            print("Shots done for this generation:", shots_done)
            print(f"All agents exhausted shots for generation {current_generation}. Sending /reset request to Unity.")
            try:
                # Send a reset request to Unity.
                reset_response = requests.post("http://127.0.0.1:8001/reset", json={})
                if reset_response.status_code == 200 and "reset successful" in reset_response.text.lower():
                    print("Reset confirmed from Unity:", reset_response.text)
                else:
                    print("Reset failed, status:", reset_response.status_code, reset_response.text)
                    continue  # Skip advancing generation if reset failed.
            except Exception as e:
                print("Failed to call Unity /reset:", e)
                continue  # Try again in the next cycle.
            # Wait briefly to ensure Unity completes the reset.
            await asyncio.sleep(2)
            current_generation += 1
            print(f"Generation advanced to {current_generation}.")
            # Clear shot counts and initial_shots so next generation starts fresh.
            agent_shot_counts = {}
            initial_shots = {}
        else:
            print("Not all agents exhausted yet.")

# NEW: Start the monitor task on startup.
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(monitor_shot_counts())

# Updated /init endpoint: record initial shots for each agent.
@app.post("/init")
async def init_agent(data: InitData):
    print(f"Agent {data.agent_id} initialized with {data.shots} shots")
    initial_shots[data.agent_id] = data.shots   # Save the initial shot count.
    return JSONResponse(content={"message": f"Agent {data.agent_id} initialized with {data.shots} shots"})

# Updated /update_shots endpoint: print remaining shots and shots done.
class ShotUpdate(BaseModel):
    agent_id: int
    shots_remaining: int

@app.post("/update_shots")
async def update_shots(data: ShotUpdate):
    global agent_shot_counts, initial_shots
    agent_shot_counts[data.agent_id] = data.shots_remaining
    done = initial_shots.get(data.agent_id, 0) - data.shots_remaining  # shots done calculation.
    print(f"Received shot update: Agent {data.agent_id} has {data.shots_remaining} shots remaining. Shots done: {done}")
    print("Updated agent shot counts:", agent_shot_counts)
    return JSONResponse(content={"message": "Shot update received"})

# Endpoint to receive environment data and respond with a shot decision.
@app.post("/environment", response_model=ShotData)
async def receive_environment(env_data: EnvironmentData):
    print(f"Received environment data for agent {env_data.agent_id}")
    # Log the received walls.
    # if env_data.walls and len(env_data.walls) > 0:
    #     print("Received walls:")
    #     for wall in env_data.walls:
    #         print(f"Wall: hitPoint=({wall.hitPoint.x}, {wall.hitPoint.y}, {wall.hitPoint.z}), width={wall.width}, rotation={wall.rotation}")
    # else:
    #     print("No walls received.")
        
    shot = calculate_shot(env_data.dict())
    return shot

# Endpoint to reset the game.
@app.post("/reset")
async def reset_game():
    print("Game reset received")
    return JSONResponse(content={"status": "reset successful"})

@app.post("/agent_count")
async def agent_count(data: AgentCountData):
    print(f"Received agent count from Unity: {data.agent_count}")
    return JSONResponse(content={"message": f"Agent count {data.agent_count} received"})

if __name__ == '__main__':
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
