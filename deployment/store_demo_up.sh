#!/bin/bash
# This script starts a local store-backed demo of the SeqCol API service

# Use local source instead of installed package
export PYTHONPATH="$(pwd):$PYTHONPATH"

# Function to handle cleanup on Ctrl+C
cleanup() {
    echo "Stopping uvicorn (PID: $PID)..."
    kill -15 $PID 2>/dev/null
    wait $PID 2>/dev/null
    echo "Uvicorn stopped."
    if [ -n "$STORE_HTTP_PID" ]; then
        echo "Stopping store HTTP server (PID: $STORE_HTTP_PID)..."
        kill -15 $STORE_HTTP_PID 2>/dev/null
        wait $STORE_HTTP_PID 2>/dev/null
    fi
    echo "Cleaning up demo store at $REFGET_STORE_PATH..."
    rm -rf "$REFGET_STORE_PATH"
    exit 0
}

# Load environment variables
source deployment/store_demo/store_demo.env

echo "Building demo store from test FASTA files..."
python data_loaders/demo_build_store.py test_fasta "$REFGET_STORE_PATH"

STORE_HTTP_PORT=8200
echo "Starting HTTP file server for store on port $STORE_HTTP_PORT..."
STORE_DIR="$REFGET_STORE_PATH" STORE_PORT="$STORE_HTTP_PORT" python -c '
import http.server, socketserver, os

class CORSHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.environ["STORE_DIR"], **kwargs)

socketserver.TCPServer(("", int(os.environ["STORE_PORT"])), CORSHandler).serve_forever()
' &
STORE_HTTP_PID=$!
export REFGET_STORE_HTTP_URL="http://localhost:$STORE_HTTP_PORT"

echo "Running store-backed uvicorn API service..."
uvicorn seqcolapi.main:store_app --reload --port ${SEQCOLAPI_PORT:-8100} &
PID=$!

echo ""
echo "Store-backed seqcolapi is running at http://localhost:${SEQCOLAPI_PORT:-8100}"
echo "  API docs:      http://localhost:${SEQCOLAPI_PORT:-8100}/docs"
echo "  Service info:  http://localhost:${SEQCOLAPI_PORT:-8100}/service-info"
echo "  Store files:   $REFGET_STORE_HTTP_URL"
echo ""

# Set up cleanup on Ctrl+C
trap cleanup SIGINT EXIT

# Wait indefinitely until Ctrl+C is pressed
wait $PID
