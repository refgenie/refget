# Configuration Reference

The `refget` CLI uses a TOML configuration file and environment variables to manage settings. This page documents all configuration options.

## Configuration priority

Settings are resolved in this order (highest priority first):

1. **CLI flags** - Command-line arguments
2. **Environment variables** - System environment
3. **Config file** - `~/.refget/config.toml`
4. **Defaults** - Built-in default values

## Config file location

By default, the configuration file is located at:

```
~/.refget/config.toml
```

Override this with the `REFGET_CONFIG` environment variable:

```bash
export REFGET_CONFIG=/path/to/custom/config.toml
```

View the current config path:

```bash
refget config path
```

## Config file format

The configuration file uses [TOML](https://toml.io/) format with these sections:

### Complete example

```toml
# Local RefgetStore path
[store]
path = "~/.refget/store"

# Seqcol API servers for remote queries
[[seqcol_servers]]
url = "https://seqcolapi.databio.org"
name = "databio"

[[seqcol_servers]]
url = "https://my-internal-server.org"
name = "internal"

# Remote RefgetStores for sequence retrieval
[[remote_stores]]
url = "s3://my-bucket/refget-store/"
name = "s3-store"

# Sequence servers (GA4GH refget sequences API)
[[sequence_servers]]
url = "https://www.ebi.ac.uk/ena/cram"
name = "ena"

# Database settings for admin commands
[admin]
postgres_host = "localhost"
postgres_port = "5432"
postgres_db = "refget"
postgres_user = "postgres"
postgres_password = "secret"
```

## Configuration sections

### store

Local RefgetStore settings.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `path` | string | `~/.refget/store` | Path to local RefgetStore directory |

```toml
[store]
path = "~/.refget/store"
```

### seqcol_servers

List of sequence collection API servers. Used by `refget seqcol` commands.

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `url` | string | Yes | Server URL (e.g., `https://seqcolapi.databio.org`) |
| `name` | string | No | Friendly name for the server |

```toml
[[seqcol_servers]]
url = "https://seqcolapi.databio.org"
name = "databio"
```

**Default:** `[{url: "https://seqcolapi.databio.org", name: "databio"}]`

### remote_stores

List of remote RefgetStores for sequence retrieval. Used by `refget store` commands when accessing remote data.

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `url` | string | Yes | Store URL (supports `s3://`, `https://`, local paths) |
| `name` | string | No | Friendly name for the store |

```toml
[[remote_stores]]
url = "s3://my-bucket/refget-store/"
name = "cloud-store"
```

**Default:** `[]` (empty list)

### sequence_servers

List of GA4GH refget sequence servers. Used by `SequenceClient` for raw sequence retrieval.

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `url` | string | Yes | Server URL |
| `name` | string | No | Friendly name |

```toml
[[sequence_servers]]
url = "https://www.ebi.ac.uk/ena/cram"
name = "ena"
```

**Default:** `[]` (empty list)

### admin

Database connection settings for admin commands (`refget admin`).

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `postgres_host` | string | `localhost` | PostgreSQL server hostname |
| `postgres_port` | string | `5432` | PostgreSQL server port |
| `postgres_db` | string | `refget` | Database name |
| `postgres_user` | string | `postgres` | Database username |
| `postgres_password` | string | (none) | Database password |

```toml
[admin]
postgres_host = "localhost"
postgres_port = "5432"
postgres_db = "refget"
postgres_user = "postgres"
postgres_password = "secret"
```

## Environment variables

Environment variables override config file values. Use these for deployment or CI/CD.

### General settings

| Variable | Config equivalent | Description |
|----------|-------------------|-------------|
| `REFGET_CONFIG` | (file path) | Path to config file |
| `REFGET_STORE` | `store.path` | Local store path |
| `REFGET_STORE_PATH` | `store.path` | Local store path (explicit form) |

### Server overrides

These replace the entire server list with a single server:

| Variable | Config equivalent | Description |
|----------|-------------------|-------------|
| `REFGET_SEQCOL_URL` | `seqcol_servers` | Single seqcol server URL |
| `REFGET_STORE_URL` | `remote_stores` | Single remote store URL |
| `REFGET_SEQUENCE_URL` | `sequence_servers` | Single sequence server URL |

### Database settings

| Variable | Config equivalent | Description |
|----------|-------------------|-------------|
| `POSTGRES_HOST` | `admin.postgres_host` | Database host |
| `POSTGRES_PORT` | `admin.postgres_port` | Database port |
| `POSTGRES_DB` | `admin.postgres_db` | Database name |
| `POSTGRES_USER` | `admin.postgres_user` | Database user |
| `POSTGRES_PASSWORD` | `admin.postgres_password` | Database password |

### Example: Docker deployment

```bash
docker run -e POSTGRES_HOST=db \
           -e POSTGRES_DB=refget \
           -e POSTGRES_USER=app \
           -e POSTGRES_PASSWORD=secret \
           -e REFGET_SEQCOL_URL=https://seqcolapi.databio.org \
           my-refget-app
```

## CLI config commands

Manage configuration from the command line:

```bash
# Initialize config interactively
refget config init

# Show all configuration
refget config show

# Show specific section
refget config show store
refget config show admin

# Get a specific value
refget config get store.path
refget config get admin.postgres_host

# Set a value
refget config set store.path ~/my-store
refget config set admin.postgres_host db.example.com

# Add a server
refget config add seqcol_server https://my-server.org
refget config add remote_store s3://my-bucket/store/

# Remove a server
refget config remove seqcol_server databio
refget config remove remote_store my-store

# Show config file path
refget config path

# Validate config file
refget config validate
```

## Common configurations

### Minimal config (local only)

```toml
[store]
path = "~/.refget/store"
```

### Research server

```toml
[store]
path = "/data/refget/store"

[[seqcol_servers]]
url = "https://seqcolapi.databio.org"
name = "databio"

[[remote_stores]]
url = "s3://lab-bucket/refget-store/"
name = "lab-store"
```

### Admin/server deployment

```toml
[admin]
postgres_host = "db.internal"
postgres_port = "5432"
postgres_db = "seqcol_prod"
postgres_user = "seqcol_app"
# Password via POSTGRES_PASSWORD env var for security
```

## Troubleshooting

### Config not being read

1. Check the config path: `refget config path`
2. Verify file exists and is valid TOML: `refget config validate`
3. Check environment overrides: `env | grep REFGET`

### Server connection issues

1. Verify server URLs are correct: `refget config show seqcol_servers`
2. Test connectivity: `refget seqcol info`
3. Check for environment overrides: `echo $REFGET_SEQCOL_URL`

### Database connection issues

1. Verify settings: `refget config show admin`
2. Test connection: `refget admin status`
3. Check environment variables are set correctly
