#!/bin/bash
# This script starts a local demo of the SeqCol API service and loads the demo data
# It requires the following environment variables to be set:
# - POSTGRES_USER: the username for the postgres database
# - POSTGRES_PASSWORD: the password for the postgres database
# - POSTGRES_DB: the name of the postgres database
# - POSTGRES_HOST: the hostname of the postgres database

# Function to handle cleanup on Ctrl+C
cleanup() {
    echo "Stopping uvicorn (PID: $PID)..."
    kill -15 $PID
    wait $PID 2>/dev/null
    echo "Uvicorn stopped."
    exit 0
}

source deployment/local_demo/local_demo.env

echo "Running docker postgres..."

docker run --rm -d --name refget-postgres -p 127.0.0.1:5432:5432 \
  -e POSTGRES_PASSWORD \
  -e POSTGRES_USER \
  -e POSTGRES_DB \
  -e POSTGRES_HOST \
  postgres:17.0

echo "Running uvicorn API service..."
uvicorn seqcolapi.main:app --reload --port 8100 &
PID=$!

echo "Loading demo sequence collections..."
python load_demo_data.py

# Set up cleanup on Ctrl+C
trap cleanup SIGINT
# Ensure that the docker container is stopped when the script exits
trap "docker stop refget-postgres" EXIT

# Wait indefinitely until Ctrl+C is pressed
wait $PID
