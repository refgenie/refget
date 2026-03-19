#!/bin/bash
# Install and test BiocRefgetStore
# Usage: bash install_and_test.sh [install|test|both]
# Default: both

set -e

PKG_DIR="$(cd "$(dirname "$0")" && pwd)"
ACTION="${1:-both}"

R_CMD="bulker exec databio/nsheff -- R"
RSCRIPT_CMD="bulker exec databio/nsheff -- Rscript"

install_pkg() {
    echo "=== Installing BiocRefgetStore ==="
    $R_CMD CMD INSTALL --no-multiarch "$PKG_DIR"
    echo "=== Installation complete ==="
}

run_tests() {
    echo "=== Running tests ==="
    $RSCRIPT_CMD -e "testthat::test_local('$PKG_DIR')"
    echo "=== Tests complete ==="
}

case "$ACTION" in
    install)
        install_pkg
        ;;
    test)
        run_tests
        ;;
    both)
        install_pkg
        run_tests
        ;;
    *)
        echo "Usage: bash install_and_test.sh [install|test|both]"
        exit 1
        ;;
esac
