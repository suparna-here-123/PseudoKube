#!/bin/bash

# Function to handle cleanup
cleanup() {
    echo "Cleaning up..."
    # Kill the Python process
    pkill -f "python3 ./userFrontend.py"
    # Stop and remove Redis container
    docker stop redisContainer || true
    docker rm redisContainer || true
    echo "Cleanup complete. Redis container has been removed."
    exit 0
}

# Set up trap for SIGINT (Ctrl+C) and SIGTERM
trap cleanup SIGINT SIGTERM

# Check if Redis container exists and is running
if docker ps -a | grep -q redisContainer; then
    if ! docker ps | grep -q redisContainer; then
        # Container exists but isn't running, remove it
        docker rm redisContainer
    else
        # Container is running, check if it's healthy
        if ! docker exec redisContainer redis-cli ping > /dev/null 2>&1; then
            # Container is running but Redis isn't responding, restart it
            docker stop redisContainer
            docker rm redisContainer
        else
            echo "Redis container is already running and healthy"
            exit 0
        fi
    fi
fi

# Kill any existing processes using port 8000
lsof -ti:8000 | xargs kill -9 2>/dev/null || true

# Pull and run Redis container
echo "Pulling fresh Redis container..."
docker pull redis:latest

docker run -d \
  --name redisContainer \
  -p 55000:6379 \
  redis:latest

# Wait for Redis to be ready
until docker exec redisContainer redis-cli ping > /dev/null 2>&1; do
    echo "Waiting for Redis to be ready..."
    sleep 1
done

echo "Redis container is ready!"

# Start the application
python3 ./userFrontend.py

# Wait for the application to finish
wait