#!/bin/bash
set -e

# Create a file to track if dependencies are installed
DEPS_INSTALLED_FLAG="/.dependencies_installed"

# Only install dependencies if the flag file doesn't exist
if [ ! -f "$DEPS_INSTALLED_FLAG" ]; then
    echo "First run - installing dependencies..."

    echo "Downgrading protobuf to fix compatibility issues..."
    pip install --no-cache-dir protobuf==3.20.3

    echo "Installing core dependencies..."
    pip install --no-cache-dir numpy==1.23.5
    pip install --no-cache-dir torch==1.8.1

    echo "Installing FastAPI dependencies..."
    pip install --no-cache-dir fastapi==0.75.0 uvicorn==0.15.0 pydantic==1.9.0 requests==2.28.0

    echo "Installing ML dependencies..."
    pip install --no-cache-dir gymnasium==0.28.1 cloudpickle==1.6.0
    
    # Explicitly set environment variable to avoid protobuf issues
    export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python
    pip install --no-cache-dir stable-baselines3==1.2.0
    
    echo "Installing utilities..."
    pip install --no-cache-dir matplotlib==3.5.1 tensorboard==2.8.0 tqdm==4.64.0 PyYAML==6.0 psutil==5.9.0 opencv-python==4.5.5.64

    # Create flag file to avoid reinstalling on restart
    touch "$DEPS_INSTALLED_FLAG"
    echo "All dependencies installed."
else
    echo "Dependencies already installed. Skipping installation step."
fi

# Always set this environment variable to prevent protobuf issues
export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python
echo "Set PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python to avoid protobuf errors"

# If this is the agent container and app.py doesn't exist, wait for the app server
if [ ! -f "/app/app.py" ] && [ -f "/app/rl_agent.py" ]; then
  echo "Agent container detected. Waiting for app server to be ready..."
  
  # Wait for app server to be available
  for i in {1..30}; do
    if curl -s http://app:8000/get_agent_count &> /dev/null; then
      echo "App server is ready. Starting agent..."
      break
    fi
    
    echo "Waiting for app server... attempt $i/30"
    sleep 5
    
    if [ $i -eq 30 ]; then
      echo "App server not available after 30 attempts. Will try to continue anyway."
    fi
  done
fi

echo "Starting application..."

# Run the provided command
exec "$@" 