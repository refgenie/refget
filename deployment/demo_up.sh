#!/bin/bash
# This script starts a local demo of the SeqCol API service and loads the demo data

# Function to handle cleanup on Ctrl+C
cleanup() {
    echo "Stopping uvicorn (PID: $PID)..."
    kill -15 $PID
    wait $PID 2>/dev/null
    echo "Uvicorn stopped."
    # Ensure that the docker container is stopped when the script exits
    echo "Stopping docker postgres..."
    docker stop refget-postgres
    exit 0
}
# Load environment variables
source deployment/local_demo/local_demo.env

echo "Running docker postgres..."
# Run the container in the background
docker run --rm -d --name refget-postgres -p 127.0.0.1:5432:5432 \
  -e POSTGRES_PASSWORD \
  -e POSTGRES_USER \
  -e POSTGRES_DB \
  -e POSTGRES_HOST \
  postgres:17.0
  
  # Wait for the postgres container to be ready
  until docker exec refget-postgres pg_isready -U $POSTGRES_USER; do
    >&2 echo "Postgres is unavailable - sleeping"
    sleep 1
  done
  echo "Postgres is up - continuing"

echo "Running uvicorn API service..."
uvicorn seqcolapi.main:app --reload --port 8100 &
PID=$!

echo "Loading demo sequence collections..."
python data_loaders/load_demo_seqcols.py

# Set up cleanup on Ctrl+C
trap cleanup SIGINT EXIT


# Wait indefinitely until Ctrl+C is pressed
wait $PID


