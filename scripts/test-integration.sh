#!/bin/bash
# Run integration tests with ephemeral test database

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR/.."

echo "=== Integration Tests ==="

# Start test database
echo "Starting test database..."
$PROJECT_ROOT/tests/integration/scripts/test-db.sh start

# Run integration tests
echo "Running integration tests..."
cd $PROJECT_ROOT
RUN_INTEGRATION_TESTS=true pytest tests/integration/ -v -p no:asyncio
TEST_EXIT_CODE=$?

# Stop test database
echo "Stopping test database..."
$PROJECT_ROOT/tests/integration/scripts/test-db.sh stop

echo "=== Integration tests complete ==="
exit $TEST_EXIT_CODE
