#!/bin/bash
# Test the store-backed Docker image builds and starts correctly.
#
# Usage: ./scripts/test-store-docker.sh
#
# Builds a Docker image using LOCAL source code, compiles gtars from source
# if needed (cached as a wheel for subsequent runs), and verifies endpoints.

set -e

IMAGE_NAME="seqcolapi-store-test"
CONTAINER_NAME="seqcolapi-store-test"
PORT=8199
STORE_URL="https://refgenie.s3.us-east-1.amazonaws.com/refget-store/jungle/"
GTARS_REPO="${GTARS_REPO:-$(cd "$(dirname "$0")/../../gtars" 2>/dev/null && pwd)}"
WHEEL_CACHE_DIR="${HOME}/.cache/seqcolapi-test-wheels"

cleanup() {
    echo "Cleaning up..."
    docker stop "$CONTAINER_NAME" 2>/dev/null || true
    docker rm "$CONTAINER_NAME" 2>/dev/null || true
}
trap cleanup EXIT

# Build or find gtars wheel for cp311
mkdir -p "$WHEEL_CACHE_DIR"
GTARS_WHEEL=$(find "$WHEEL_CACHE_DIR" -name "gtars*cp311*linux*.whl" 2>/dev/null | head -1)

if [ -z "$GTARS_WHEEL" ] && [ -d "$GTARS_REPO" ]; then
    echo "Building gtars wheel for Python 3.11 (one-time, cached)..."
    docker run --rm -v "$GTARS_REPO:/src" -v "$WHEEL_CACHE_DIR:/wheels" \
        python:3.11-slim bash -c "
            apt-get update -qq && apt-get install -y -qq curl gcc > /dev/null 2>&1
            curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y > /dev/null 2>&1
            export PATH=\$HOME/.cargo/bin:\$PATH
            pip install maturin > /dev/null 2>&1
            cd /src/gtars-python && maturin build --release -o /wheels 2>&1 | tail -3
        "
    GTARS_WHEEL=$(find "$WHEEL_CACHE_DIR" -name "gtars*cp311*linux*.whl" 2>/dev/null | head -1)
fi

if [ -n "$GTARS_WHEEL" ]; then
    echo "Using cached gtars wheel: $(basename "$GTARS_WHEEL")"
    GTARS_INSTALL="COPY gtars.whl /tmp/gtars.whl
RUN pip install --no-cache-dir /tmp/gtars.whl"
    EXTRA_COPY="-v $GTARS_WHEEL:/tmp/build-context/gtars.whl:ro"
    # We'll copy the wheel into context below
else
    echo "No local gtars repo found, using PyPI version"
    GTARS_INSTALL="RUN pip install --no-cache-dir gtars"
    EXTRA_COPY=""
fi

# Build context — just refget source + wheel
CONTEXT_DIR="/tmp/seqcolapi-store-docker-context"
rm -rf "$CONTEXT_DIR"
mkdir -p "$CONTEXT_DIR"

# Copy only essential files, not .git or node_modules
rsync -a --exclude='.git' --exclude='node_modules' --exclude='__pycache__' \
    --exclude='*.pyc' --exclude='.pytest_cache' --exclude='frontend/node_modules' \
    . "$CONTEXT_DIR/refget/"

[ -n "$GTARS_WHEEL" ] && cp "$GTARS_WHEEL" "$CONTEXT_DIR/gtars.whl"

echo "Building Docker image from local source..."
docker build -t "$IMAGE_NAME" -f - "$CONTEXT_DIR" <<DOCKERFILE
FROM tiangolo/uvicorn-gunicorn:python3.11-slim
COPY refget /src/refget
RUN pip install --no-cache-dir /src/refget
${GTARS_INSTALL}
RUN pip install --no-cache-dir fastapi psycopg2-binary ubiquerg henge
COPY refget/seqcolapi/ /app/seqcolapi
CMD ["uvicorn", "seqcolapi.main:store_app", "--host", "0.0.0.0", "--port", "80"]
DOCKERFILE

echo "Starting container..."
docker run -d \
    --name "$CONTAINER_NAME" \
    -p "$PORT:80" \
    -e "REFGET_STORE_URL=$STORE_URL" \
    "$IMAGE_NAME"

echo "Waiting for server to start..."
for i in $(seq 1 60); do
    if curl -sf "http://localhost:$PORT/service-info" > /dev/null 2>&1; then
        echo "Server is up after ${i}s"
        break
    fi
    if [ "$i" -eq 60 ]; then
        echo "FAILED: Server did not start within 60s"
        echo "Container logs:"
        docker logs "$CONTAINER_NAME"
        exit 1
    fi
    sleep 1
done

echo "Checking /service-info..."
curl -s "http://localhost:$PORT/service-info" | python3 -c "
import sys, json
info = json.load(sys.stdin)
assert 'seqcol' in info, 'Missing seqcol in service-info'
print(f'  Name: {info[\"name\"]}')
print(f'  Store: {info[\"seqcol\"].get(\"refget_store\", {}).get(\"enabled\", False)}')
print(f'  SCOM: {info[\"seqcol\"].get(\"scom\", {}).get(\"enabled\", False)}')
"

echo "Checking /list/collection..."
curl -s "http://localhost:$PORT/list/collection?page_size=1" | python3 -c "
import sys, json
data = json.load(sys.stdin)
assert 'results' in data, 'Missing results in list response'
assert 'pagination' in data, 'Missing pagination'
print(f'  Total collections: {data[\"pagination\"][\"total\"]}')
"

echo ""
echo "PASSED: Store Docker image builds and runs correctly."
