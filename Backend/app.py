from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
import random
import uvicorn  # added uvicorn import

app = FastAPI()

# Data models
class InitData(BaseModel):
    agent_id: int
    shots: int

class Vector3(BaseModel):
    x: float
    y: float
    z: float

class EnvironmentData(BaseModel):
    agent_id: int
    ball_position: Vector3
    hole_position: Vector3
    walls: List[Vector3]

class InitResponse(BaseModel):
    message: str

class EnvironmentResponse(BaseModel):
    message: str

class ShotData(BaseModel):
    power: float
    direction: Vector3

# Endpoint to initialize the agent
@app.post("/init", response_model=InitResponse)
def init_agent(data: InitData):
    # ...logic to initialize agent...
    print(f"Agent {data.agent_id} initialized with {data.shots} shots")
    return InitResponse(message=f"Agent {data.agent_id} initialized with {data.shots} shots")

import logging
logging.basicConfig(level=logging.INFO)

# Endpoint to receive environment data
@app.post("/environment", response_model=EnvironmentResponse)
def send_environment(data: EnvironmentData):
    # ...logic to process environment data...
    logging.info("function called")
    logging.info(f"Received environment data for agent {data.agent_id}")
    return EnvironmentResponse(message=f"Environment data received for agent {data.agent_id}")

# # Endpoint to request a shot decision from the AI
# @app.get("/shot", response_model=ShotData)
# def request_shot(agent_id: int):
#     # ...logic to compute shot decision...
#     power = random.uniform(0, 5)
#     direction = Vector3(x=random.uniform(-1, 1), y=0, z=random.uniform(-1, 1))
#     return ShotData(power=power, direction=direction)

# New endpoint to handle combined environment data & shot request.
@app.post("/shoot", response_model=ShotData)
def shoot_decision(data: EnvironmentData):
    # ...logic to compute shot decision based on environment data...
    power = random.uniform(4, 6)
    direction = Vector3(x=random.uniform(-1, 1), y=0, z=random.uniform(-1, 1))
    return ShotData(power=power, direction=direction)

@app.get("/deduct")
def deduct_score(agent_id: int):
    print(f"Deduct score for agent {agent_id}")
    return {"message": f"Agent {agent_id} score deducted."}

if __name__ == '__main__':  # added main section to run uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
