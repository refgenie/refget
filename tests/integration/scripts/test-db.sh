#!/bin/bash
# Test Database Management Script
# Manages Docker PostgreSQL container for integration tests

CONTAINER_NAME="refget-postgres-test"
DB_PORT="5433"  # Different from dev port 5432!
DB_USER="testuser"
DB_PASS="testpass"
DB_NAME="refget_test"

case "$1" in
    start)
        echo "Starting test PostgreSQL database..."

        # Remove existing container if it exists
        docker rm -f "$CONTAINER_NAME" 2>/dev/null

        # Start PostgreSQL container with tmpfs for speed
        docker run -d \
            --name "$CONTAINER_NAME" \
            -e POSTGRES_USER="$DB_USER" \
            -e POSTGRES_PASSWORD="$DB_PASS" \
            -e POSTGRES_DB="$DB_NAME" \
            -p "${DB_PORT}:5432" \
            --tmpfs /var/lib/postgresql/data \
            postgres:17

        echo "Waiting for database to be ready..."

        # Wait for healthy status (up to 30 seconds)
        for i in {1..30}; do
            if docker exec "$CONTAINER_NAME" pg_isready -U "$DB_USER" -d "$DB_NAME" 2>/dev/null; then
                echo "Test database is ready!"
                exit 0
            fi
            sleep 1
        done

        echo "Failed to start test database"
        docker logs "$CONTAINER_NAME"
        exit 1
        ;;
    stop)
        echo "Stopping test PostgreSQL database..."
        docker rm -f "$CONTAINER_NAME" 2>/dev/null
        echo "Test database stopped and removed"
        ;;
    restart)
        $0 stop
        $0 start
        ;;
    status)
        docker ps -f "name=$CONTAINER_NAME"
        ;;
    logs)
        docker logs -f "$CONTAINER_NAME"
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs}"
        exit 1
        ;;
esac
