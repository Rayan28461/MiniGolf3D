#!/bin/bash
set -e

# Create run flag to track if we've already executed
RUN_FLAG="/tmp/agent_already_run"

if [ ! -f "$RUN_FLAG" ]; then
    echo "First execution, running diagnostics..."
    
    echo "========== AGENT CONTAINER DIAGNOSTIC INFO =========="
    echo "Date: $(date)"
    echo "Hostname: $(hostname)"
    echo "Container ID: $(cat /etc/hostname)"
    echo "Python version: $(python --version)"
    echo "Working directory: $(pwd)"
    echo "Files in current directory:"
    ls -la

    echo "========== NETWORK DIAGNOSTIC INFO =========="
    echo "Host entries:"
    cat /etc/hosts
    echo "Network interfaces:"
    ip addr
    echo "DNS resolution:"
    cat /etc/resolv.conf
    echo "Ping app server:"
    ping -c 2 app || echo "Ping failed"
    echo "Curl app server:"
    curl -v http://app:8000/get_agent_count || echo "Curl failed"

    # Create the flag file to avoid repeating diagnostics
    touch "$RUN_FLAG"
else
    echo "Restarting agent (skipping diagnostics)..."
fi

# Check for common Python modules to verify installation
echo "Verifying Python modules..."
python -c "import numpy; print(f'NumPy version: {numpy.__version__}')"
python -c "import torch; print(f'Torch version: {torch.__version__}')"
python -c "import gymnasium; print(f'Gymnasium version: {gymnasium.__version__}')"
python -c "import stable_baselines3; print(f'Stable Baselines3 version: {stable_baselines3.__version__}')"

echo "========== AGENT STARTUP =========="
echo "Starting RL agent with debug flags..."

# Setup trap to handle agent crashes
function handle_crash {
    echo "Agent process crashed or was killed. $(date)"
    echo "Exit code: $?"
}
trap handle_crash EXIT

# Run the agent with a timeout to prevent long-running processes from getting stuck
timeout 1800 python -u rl_agent.py --train --debug || echo "Agent timed out or failed with exit code $?"

# If the agent crashes, keep the container running
echo "Agent exited. Keeping container alive for troubleshooting..."
while true; do
  echo "Container still running. Timestamp: $(date)"
  sleep 600
done 