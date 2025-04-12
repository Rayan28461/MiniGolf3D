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

# NEW: Global dictionaries and variables.
agent_shot_counts = {}  # Format: {agent_id: shots_remaining, ...}
current_generation = 1
global_agent_count = 0  # NEW: to store agent count received from Unity.
movePlayed = False      # NEW: flag when move is played
reset_pending = False  # Prevent new environment updates when resetting

# # Updated background task to periodically check shot counts and wait for move before resetting env.
# async def monitor_shot_counts():
#     global agent_shot_counts, current_generation, movePlayed, reset_pending
#     while True:
#         await asyncio.sleep(5)
#         print("[MONITOR] Current agent shot counts:", agent_shot_counts)
#         if agent_shot_counts and all(shots == 0 for shots in agent_shot_counts.values()):
#             print("[MONITOR] All agents exhausted shots for generation {}. Triggering immediate reset...".format(current_generation))
#             reset_pending = True
            
#             # CHANGED: Immediately send reset request without waiting for move signal
#             try:
#                 print("[MONITOR] Sending immediate /reset request to Unity...")
#                 reset_response = requests.post("http://127.0.0.1:8001/reset", json={})
#                 if reset_response.status_code == 200 and "reset successful" in reset_response.text.lower():
#                     print("[MONITOR] Reset confirmed from Unity:", reset_response.text)
#                 else:
#                     print("[MONITOR] Reset failed, status:", reset_response.status_code, reset_response.text)
#                     reset_pending = False
#                     continue
#             except Exception as e:
#                 print("[MONITOR] Failed to call Unity /reset:", e)
#                 reset_pending = False
#                 continue
                
#             await asyncio.sleep(2)
#             current_generation += 1
#             print("[MONITOR] Generation advanced to {}.".format(current_generation))
#             agent_shot_counts = {}
#             movePlayed = False
#             reset_pending = False
#         else:
#             print("[MONITOR] Not all agents exhausted yet.")

# @app.on_event("startup")
# async def startup_event():
#     asyncio.create_task(monitor_shot_counts())

# # Updated /init endpoint
# @app.post("/init")
# async def init_agent(data: InitData):
#     print(f"[INIT AGENT] Agent {data.agent_id} initialized with {data.shots} shots")
#     # initial_shots[data.agent_id] = data.shots
#     return JSONResponse(content={"message": f"Agent {data.agent_id} initialized with {data.shots} shots"})


# @app.post("/update_shots")
# async def update_shots(data: ShotUpdate):
#     global agent_shot_counts
#     # Don't decrement manually - directly set to the reported value
#     agent_shot_counts[data.agent_id] = data.shots_remaining # HOW ARE THE SHOTS CHANGING THEN???
#     shots_done = 5 - data.shots_remaining   # Assuming 5 is the initial full shot count.
    
#     print(f"[BACKEND] Agent {data.agent_id} has {data.shots_remaining} shots remaining, completed {shots_done} shots.")
#     print("[UPDATE SHOTS] Updated agent shot counts:", agent_shot_counts)
    
#     # Check if all agents have exhausted their shots immediately after every update
#     if agent_shot_counts and all(shots <= 0 for shots in agent_shot_counts.values()):
#         print("[BACKEND] All agents have exhausted their shots. Triggering reset immediately!")
#         # Set reset_pending flag to block new environment updates
#         global reset_pending
#         reset_pending = True
        
#         # Send reset request immediately
#         try:
#             reset_response = requests.post("http://127.0.0.1:8001/reset", json={})
#             if reset_response.status_code == 200:
#                 print("[BACKEND] Reset request sent! Response:", reset_response.text)
#                 print("[BACKEND] Waiting for Unity to confirm reset completion...")
#                 # NOTE: We now wait for Unity to call /reset_complete to clear reset_pending
#             else:
#                 print(f"[BACKEND] Reset failed! Status: {reset_response.status_code}")
#                 reset_pending = False  # Allow retry if reset fails
#         except Exception as e:
#             print(f"[BACKEND] Reset request error: {e}")
#             reset_pending = False
    
#     return JSONResponse(content={"message": "Shot update received"})

# NEW: Add an endpoint for Unity to notify when reset is complete
@app.post("/reset_complete")
async def reset_complete():
    global reset_pending
    print("[BACKEND] Received reset completion notification from Unity.")
    reset_pending = False
    # Reset agent shot counts after Unity has confirmed the reset
    # The next /agent_count call from Unity will set new shot counts
    agent_shot_counts.clear()  
    print("[BACKEND] Reset state cleared, now accepting new environment updates.")
    return JSONResponse(content={"message": "Reset completion acknowledged"})

# Updated /agent_count endpoint to clear previous agent data and reinitialize shot counts.
@app.post("/agent_count")
async def agent_count(data: AgentCountData):
    global global_agent_count, agent_shot_counts
    global_agent_count = data.agent_count
    agent_shot_counts.clear()  # Clear previous shot tracking data.
    # Initialize each agent with full shots (5)
    for i in range(1, data.agent_count + 1):
        agent_shot_counts[i] = 5
    print(f"[AGENT COUNT] Received agent count from Unity: {data.agent_count}. Shot counts reset: {agent_shot_counts}")
    return JSONResponse(content={"message": f"Agent count {data.agent_count} received and shot counts initialized"})

# # NEW: Endpoint for Unity to signal that the move is played.
# @app.post("/move_played") # WHO IS TALKING WITH THIS ENDPOINT??? ANS: NO
# async def move_played_endpoint():
#     global movePlayed
#     movePlayed = True
#     print("[MOVE] Move played signal received from Unity.")
#     return JSONResponse(content={"message": "Move played received"})

# NEW: Endpoint to get the current agent count.
@app.get("/get_agent_count")
async def get_agent_count():
    return JSONResponse(content={"agent_count": global_agent_count})

# # Endpoint to receive environment data and respond with a shot decision.
# @app.post("/environment", response_model=ShotData)
# async def receive_environment(env_data: EnvironmentData):
#     global reset_pending
#     if reset_pending:
#         print(f"Skipping environment update for Agent {env_data.agent_id}, reset is pending...")
#         return JSONResponse(content={"message": "Skipping environment update, reset pending"})
#     # shot = calculate_shot(env_data.dict())
#     shot = None 
#     return shot

# # Endpoint to reset the game.
# @app.post("/reset") # WHAT DOES THIS DO??
# async def reset_game():
#     print("Game reset received")
#     return JSONResponse(content={"status": "reset successful"})

if __name__ == '__main__':
    try:
        uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
    except KeyboardInterrupt:
        print("Keyboard interrupt received. Shutting down the server.")
