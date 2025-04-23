# MiniGolf RL Agent Docker Setup

This project contains a reinforcement learning agent that learns to play mini golf, along with a FastAPI server that interfaces with the game.

## Docker Setup

The application is containerized using Docker, with two services:
1. **app**: Runs the FastAPI server (app.py) on port 8000
2. **agent**: Runs the RL agent (rl_agent.py) on port 8001

### Prerequisites

- Docker and Docker Compose installed
- The Unity MiniGolf3D game running on your local machine

### How to Run with Docker

1. Navigate to the Backend directory:
   ```
   cd Backend
   ```

2. Build and start the Docker containers:
   ```
   docker-compose up --build
   ```

3. To run in detached mode:
   ```
   docker-compose up -d --build
   ```

4. To view logs:
   ```
   docker-compose logs -f
   ```

5. To stop the containers:
   ```
   docker-compose down
   ```

### Connecting Unity to Docker Containers

The Docker containers expose ports 8000 and 8001 to your host machine. Your Unity game should be configured to connect to:
- http://localhost:8000 (for the app service)
- http://localhost:8001 (for the agent service)

If you're running the Unity game on a different machine than Docker, replace "localhost" with the IP address of the machine running Docker.

### How to Run in Development Mode

If you prefer to run the services outside Docker for development:

1. Start the FastAPI server:
   ```
   cd Backend
   python app.py
   ```

2. In a separate terminal, start the RL agent:
   ```
   cd Backend
   python rl_agent.py --train
   ```

## Configuration

The Docker setup uses internal container networking with the following URLs:
- FastAPI server: http://app:8000
- RL Agent: http://agent:8001

When running in development mode, both services use localhost:
- FastAPI server: http://127.0.0.1:8000
- RL Agent: http://127.0.0.1:8001

## Troubleshooting

- If you encounter connection issues between containers, ensure both services are running correctly with `docker-compose ps`
- Check logs with `docker-compose logs app` or `docker-compose logs agent`
- Make sure your Unity game is configured to communicate with the correct ports (8000 and 8001)
- If you're seeing dependency errors related to Windows-specific packages (like pywin32), this is expected in Docker and can be ignored as those packages are excluded in the Docker setup
- If your Unity game can't connect to the Docker containers, check your firewall settings to ensure ports 8000 and 8001 are open 