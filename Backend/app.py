from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List
import uvicorn
# from rl_agent import calculate_shot
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

# Updated /update_shots endpoint
class ShotUpdate(BaseModel):
    agent_id: int
    shots_remaining: int

agent_shot_counts = {}  # Format: {agent_id: shots_remaining, ...}
global_agent_count = 0  
reset_pending = False  

@app.post("/reset_complete")
async def reset_complete():
    global reset_pending
    print("[BACKEND] Received reset completion notification from Unity.")
    reset_pending = False
    agent_shot_counts.clear()  
    print("[BACKEND] Reset state cleared, now accepting new environment updates.")
    return JSONResponse(content={"message": "Reset completion acknowledged"})

@app.post("/agent_count")
async def agent_count(data: AgentCountData):
    global global_agent_count, agent_shot_counts
    global_agent_count = data.agent_count
    agent_shot_counts.clear()
    for i in range(1, data.agent_count + 1):
        agent_shot_counts[i] = 5
    print(f"[AGENT COUNT] Received agent count from Unity: {data.agent_count}. Shot counts reset: {agent_shot_counts}")
    return JSONResponse(content={"message": f"Agent count {data.agent_count} received and shot counts initialized"})

@app.get("/get_agent_count")
async def get_agent_count():
    return JSONResponse(content={"agent_count": global_agent_count})

if __name__ == '__main__':
    try:
        uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
    except KeyboardInterrupt:
        print("Keyboard interrupt received. Shutting down the server.")