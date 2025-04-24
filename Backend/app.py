"""
This module defines the FastAPI backend for the mini-golf game.
It provides endpoints for managing the game environment, agent interactions, and reset operations.
"""

import sys
from fastapi import FastAPI #, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List
import uvicorn
# from rl_agent import calculate_shot
# import asyncio
# import requests
import subprocess

app = FastAPI()

# Data Models
class Vector3(BaseModel):
    """
    Represents a 3D vector with x, y, and z components.

    Attributes:
        x (float): The x-coordinate.
        y (float): The y-coordinate.
        z (float): The z-coordinate.
    """
    x: float
    y: float
    z: float

class WallData(BaseModel):
    """
    Represents data for a wall in the environment.

    Attributes:
        hitPoint (Vector3): The point where the wall is hit.
        width (float): The width of the wall.
        rotation (float): The rotation of the wall.
    """
    hitPoint: Vector3
    width: float
    rotation: float

class EnvironmentData(BaseModel):
    """
    Represents the environment data for the mini-golf game.

    Attributes:
        agent_id (int): The ID of the agent.
        ball_position (Vector3): The position of the ball.
        hole_position (Vector3): The position of the hole.
        walls (List[WallData]): A list of walls in the environment.
    """
    agent_id: int
    ball_position: Vector3
    hole_position: Vector3
    walls: List[WallData] = []

class ShotData(BaseModel):
    """
    Represents data for a shot taken by an agent.

    Attributes:
        agent_id (int): The ID of the agent taking the shot.
        power (float): The power of the shot.
        direction (Vector3): The direction of the shot.
    """
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

# Updated /update_shots endpoint
class ShotUpdate(BaseModel):
    agent_id: int
    shots_remaining: int

agent_shot_counts = {}  # Format: {agent_id: shots_remaining, ...}
global_agent_count = 0  
reset_pending = False  

@app.post("/reset_complete")
async def reset_complete():
    """
    Endpoint to notify the backend that the reset operation is complete.

    Returns:
        JSONResponse: Acknowledgment of the reset completion.
    """
    global reset_pending
    print("[BACKEND] Received reset completion notification from Unity.")
    reset_pending = False
    agent_shot_counts.clear()  
    print("[BACKEND] Reset state cleared, now accepting new environment updates.")
    return JSONResponse(content={"message": "Reset completion acknowledged"})

@app.post("/agent_count")
async def agent_count(data: AgentCountData):
    """
    Endpoint to set the number of agents in the game.

    Args:
        data (AgentCountData): The data containing the agent count.

    Returns:
        JSONResponse: Confirmation of the agent count update.
    """
    global global_agent_count, agent_shot_counts
    global_agent_count = data.agent_count
    agent_shot_counts.clear()
    for i in range(1, data.agent_count + 1):
        agent_shot_counts[i] = 5
    print(f"[AGENT COUNT] Received agent count from Unity: {data.agent_count}. Shot counts reset: {agent_shot_counts}")
    subprocess.Popen([sys.executable, "rl_agent.py", "--play"])
    return JSONResponse(content={"message": f"Agent count {data.agent_count} received and shot counts initialized"})

@app.get("/get_agent_count")
async def get_agent_count():
    """
    Endpoint to retrieve the current number of agents in the game.

    Returns:
        JSONResponse: The current agent count.
    """
    return JSONResponse(content={"agent_count": global_agent_count})

if __name__ == '__main__':
    try:
        uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
    except KeyboardInterrupt:
        print("Keyboard interrupt received. Shutting down the server.")