#!/bin/bash
# Run store-backed integration tests (no database needed)
#
# Usage: ./scripts/test-store-integration.sh [pytest args...]
#
# Examples:
#   ./scripts/test-store-integration.sh           # run store compliance tests
#   ./scripts/test-store-integration.sh -v         # verbose output
set -e
cd "$(dirname "${BASH_SOURCE[0]}")/.."
pytest tests/integration/test_store_compliance.py "$@"
