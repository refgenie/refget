#!/bin/bash
# Run integration tests with ephemeral test database
#
# Usage: ./scripts/test-integration.sh [pytest args...]
#
# Examples:
#   ./scripts/test-integration.sh           # run all integration tests
#   ./scripts/test-integration.sh -v        # verbose output
#   ./scripts/test-integration.sh -k admin  # only admin tests
#
# Logs are saved to: tests/integration/logs/

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR/.."
LOG_DIR="$PROJECT_ROOT/tests/integration/logs"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$LOG_DIR/integration_$TIMESTAMP.log"

# Create log directory
mkdir -p "$LOG_DIR"

# Log function that writes to both console and file
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

cleanup() {
    log "Stopping test database..."
    "$PROJECT_ROOT/tests/integration/scripts/test-db.sh" stop >> "$LOG_FILE" 2>&1
    log "Log saved to: $LOG_FILE"
}

# Always cleanup on exit (even on failure)
trap cleanup EXIT

log "=== Integration Tests ==="
log "Log file: $LOG_FILE"

# Start test database
log "Starting test database..."
"$PROJECT_ROOT/tests/integration/scripts/test-db.sh" start >> "$LOG_FILE" 2>&1

# Run integration tests with any additional arguments
log "Running integration tests..."
cd "$PROJECT_ROOT"
RUN_INTEGRATION_TESTS=true pytest tests/integration/ "$@" 2>&1 | tee -a "$LOG_FILE"
