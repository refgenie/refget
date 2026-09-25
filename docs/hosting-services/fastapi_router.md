# How to add refget endpoints to an application

Add GA4GH refget sequence collection endpoints to your FastAPI application using `create_refget_router()`. See a [working example](https://github.com/refgenie/refget/blob/master/seqcolapi/main.py) in the refget repository.

## Basic setup

This is a minimal example of how it works:

```python
from fastapi import FastAPI
from refget.router import create_refget_router
from refget.agents import RefgetDBAgent

# Create your app in the usual way.
app = FastAPI()

# Create a router with create_refget_router and attach it to your app.
# Parameterize it to choose which endpoints to include.
refget_router = create_refget_router(sequences=False, pangenomes=False)
app.include_router(refget_router, prefix="/seqcol")

# Set up the database connection
# A RefgetDBAgent connects to your SQL database of collections
dbagent = RefgetDBAgent()  # Configured via env vars

# Attach the database object to the app. This is how the router will
# get access to the database to serve the endpoints
app.state.dbagent = dbagent
```

## Router parameters

The `create_refget_router()` function accepts these parameters:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `sequences` | bool | False | Include sequence retrieval endpoints (`/sequence/{digest}`) |
| `collections` | bool | True | Include sequence collection endpoints |
| `pangenomes` | bool | False | Include pangenome endpoints |
| `fasta_drs` | bool | False | Include FASTA DRS endpoints for file access |
| `refget_store_url` | str | None | URL of backing RefgetStore (for service-info discovery) |

## Endpoints added

The router adds endpoints organized into four categories:

- **Collection endpoints**: Retrieve sequence collections, compare collections, search by attribute
- **Sequence endpoints**: Retrieve individual sequences and their metadata
- **Pangenome endpoints**: Retrieve pangenome data and listings
- **FASTA DRS endpoints**: Access FASTA files and indices via GA4GH DRS

For the complete endpoint reference with detailed parameters and response formats, visit the [live interactive API documentation](https://seqcolapi.databio.org/docs) on the deployed service.

## Database configuration

The `RefgetDBAgent` requires PostgreSQL connection details. Configure via environment variables:

```bash
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_DB=refget
export POSTGRES_USER=postgres
export POSTGRES_PASSWORD=yourpassword
```

Or use the CLI config:

```bash
refget config set admin.postgres_host localhost
refget config set admin.postgres_db refget
```

## Complete example with lifespan

Here's a more complete example using FastAPI's lifespan for proper database connection management:

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from refget.router import create_refget_router
from refget.agents import RefgetDBAgent

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create database connection
    app.state.dbagent = RefgetDBAgent()
    yield
    # Shutdown: cleanup (if needed)

app = FastAPI(lifespan=lifespan)

# Add refget routes with all features enabled
refget_router = create_refget_router(
    sequences=True,
    collections=True,
    pangenomes=False,
    fasta_drs=True,
)
app.include_router(refget_router, prefix="/seqcol")
```

## See also

- [Compliance testing](compliance.md) - Verify your implementation
- [RefgetDB Agent tutorial](agent.ipynb) - Database operations
- [CLI reference](../reference/cli.md) - `refget admin` commands for loading data
