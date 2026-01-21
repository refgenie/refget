# Testing

## Quick Start

```bash
# Unit tests (no dependencies)
pytest

# Integration tests (requires Docker)
./scripts/test-integration.sh
```

## Test Structure

```
tests/
├── local/                    # Unit tests (no external dependencies)
│   ├── test_digest_functions.py
│   ├── test_local_models.py
│   ├── test_local_models_gtars.py
│   └── test_refget_clients.py
│
├── integration/              # Integration tests (require Docker PostgreSQL)
│   ├── scripts/
│   │   └── test-db.sh       # Docker postgres management
│   ├── conftest.py          # Shared fixtures
│   ├── test_cli_admin_integration.py
│   ├── test_cli_seqcol_integration.py
│   └── test_seqcolapi_client.py
│
└── api/                      # Test data for API comparison tests
    └── comparison/
```

## Unit Tests

Unit tests run without any external dependencies:

```bash
# Run all unit tests
pytest tests/local

# Run specific test file
pytest tests/local/test_digest_functions.py

# Run with verbose output
pytest tests/local -v
```

## Integration Tests

Integration tests require Docker to run a PostgreSQL database.

### Automated (Recommended)

The integration test script handles database setup and teardown automatically:

```bash
# Run all integration tests
./scripts/test-integration.sh

# With pytest arguments
./scripts/test-integration.sh -v              # verbose
./scripts/test-integration.sh -k "admin"      # filter by name
./scripts/test-integration.sh -x              # stop on first failure
./scripts/test-integration.sh --tb=short      # shorter tracebacks
```

### Manual

If you need to run tests manually or debug:

```bash
# 1. Start the test database (port 5433 to avoid conflicts)
./tests/integration/scripts/test-db.sh start

# 2. Run tests
pytest tests/integration -v

# 3. Stop the database when done
./tests/integration/scripts/test-db.sh stop
```

Database management commands:
```bash
./tests/integration/scripts/test-db.sh start    # Start container
./tests/integration/scripts/test-db.sh stop     # Stop and remove container
./tests/integration/scripts/test-db.sh restart  # Restart container
./tests/integration/scripts/test-db.sh status   # Show container status
./tests/integration/scripts/test-db.sh logs     # Tail container logs
```

## Test Configuration

### pytest.ini / pyproject.toml

Default test paths are configured in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests/local"]
```

This means `pytest` with no arguments runs only unit tests.

### Integration Test Database

The test database runs on port **5433** (not 5432) to avoid conflicts with development databases. Configuration is in:

- `tests/integration/scripts/test-db.sh` - Docker container settings
- `tests/integration/conftest.py` - Environment variables for tests

## Writing Tests

### Unit Tests

Place in `tests/local/`. These should:
- Not require external services
- Run quickly (< 1 second each)
- Use fixtures from `conftest.py`

### Integration Tests

Place in `tests/integration/`. These can:
- Use the PostgreSQL database via `test_dbagent` fixture
- Use the FastAPI TestClient via `client` fixture
- Use the live test server via `test_server` fixture

Key fixtures (from `tests/integration/conftest.py`):
- `test_dbagent` - Database agent connected to test DB
- `loaded_dbagent` - Database agent pre-loaded with test FASTA files
- `client` - FastAPI TestClient
- `test_server` - Live uvicorn server URL for CLI tests
- `cli_runner` - Typer CLI test runner
