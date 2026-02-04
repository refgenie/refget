"""
Admin/database operations for the refget CLI.

Commands for managing PostgreSQL infrastructure, loading seqcol
metadata, and registering FASTA files with cloud storage.

Commands:
    load     - Load seqcol metadata to database
    register - Upload FASTA to cloud and create DRS record
    ingest   - Load metadata + register FASTA (combined)
    status   - Show admin/db connection status
    info     - Show system info (version, etc.)
"""

import json
import os
from pathlib import Path
from typing import Optional, List, Dict, Any

import typer

from refget.cli.output import (
    EXIT_CONFIG_ERROR,
    EXIT_FILE_NOT_FOUND,
    EXIT_FAILURE,
    EXIT_SUCCESS,
    print_error,
    print_info,
    print_json,
    print_success,
    print_warning,
)

# Heavy imports (sqlmodel) are done lazily inside functions that need them

app = typer.Typer(
    name="admin",
    help="Admin/database operations",
    no_args_is_help=True,
)


def _get_dbagent():
    """
    Create a RefgetDBAgent from environment variables.

    Returns:
        RefgetDBAgent instance or None if connection fails
    """
    from refget.agents import RefgetDBAgent

    try:
        return RefgetDBAgent()
    except Exception as e:
        print_error(f"Database connection failed: {e}", EXIT_CONFIG_ERROR)
        return None


def _check_boto3():
    """Check if boto3 is available."""
    try:
        import boto3  # noqa: F401

        return True
    except ImportError:
        return False


def _load_pep(pep_path: Optional[Path] = None, pephub: Optional[str] = None):
    """Load a PEP from file or pephub."""
    if pep_path:
        import peppy

        return peppy.Project(str(pep_path))
    elif pephub:
        import pephubclient

        phc = pephubclient.PEPHubClient()
        return phc.load_project(pephub)
    return None


def _upload_to_s3(
    fasta_path: str,
    bucket: str,
    prefix: str = "",
    access_key: Optional[str] = None,
    secret_key: Optional[str] = None,
    endpoint: Optional[str] = None,
    region: Optional[str] = None,
    url_base: Optional[str] = None,
    force: bool = False,
) -> str:
    """
    Upload a file to S3-compatible storage and return the URL.

    Args:
        fasta_path: Path to the file to upload
        bucket: Bucket name
        prefix: Key prefix (folder path)
        access_key: AWS access key ID (optional, uses default credentials if not provided)
        secret_key: AWS secret access key (optional)
        endpoint: Custom endpoint URL for S3-compatible services (e.g., Backblaze, MinIO)
        region: AWS region (optional)
        url_base: Base URL for constructing public access URLs (optional, defaults to endpoint-based URL)
        force: If True, upload even if file already exists (default: False)

    Returns:
        URL to the uploaded file
    """
    import boto3

    # Build client kwargs
    client_kwargs = {}
    if access_key and secret_key:
        client_kwargs["aws_access_key_id"] = access_key
        client_kwargs["aws_secret_access_key"] = secret_key
    if endpoint:
        # Ensure endpoint has https:// prefix
        if not endpoint.startswith("http"):
            endpoint = f"https://{endpoint}"
        client_kwargs["endpoint_url"] = endpoint
    if region:
        client_kwargs["region_name"] = region

    s3 = boto3.client("s3", **client_kwargs)
    key = (
        os.path.join(prefix, os.path.basename(fasta_path))
        if prefix
        else os.path.basename(fasta_path)
    )

    # Check if file already exists (unless force=True)
    if not force:
        try:
            s3.head_object(Bucket=bucket, Key=key)
            print(f"  Skipping upload, already exists: {key}")
        except s3.exceptions.ClientError:
            s3.upload_file(fasta_path, bucket, key)
    else:
        s3.upload_file(fasta_path, bucket, key)

    # Build URL: use url_base if provided, otherwise fall back to endpoint or default S3
    if url_base:
        # url_base is the full public URL prefix (e.g., https://cloud2.databio.org/)
        url_base = url_base.rstrip("/")
        return f"{url_base}/{key}"
    elif endpoint:
        return f"{endpoint}/{bucket}/{key}"
    else:
        return f"https://{bucket}.s3.amazonaws.com/{key}"


def _add_fasta_to_db(
    fasta_path: str,
    dbagent,
    name: Optional[str] = None,
) -> str:
    """
    Add a FASTA file's seqcol metadata to the database.

    Args:
        fasta_path: Path to the FASTA file
        dbagent: RefgetDBAgent instance
        name: Human-readable name (optional)

    Returns:
        The seqcol digest
    """
    if name:
        seqcol = dbagent.seqcol.add_from_fasta_file_with_name(fasta_path, name, update=True)
    else:
        seqcol = dbagent.seqcol.add_from_fasta_file(fasta_path, update=True)
    return seqcol.digest


def _register_access_method(
    digest: str,
    url: str,
    cloud: str,
    region: str,
    type_: str,
    dbagent,
) -> None:
    """
    Register an access method for a FASTA file.

    Args:
        digest: The seqcol digest
        url: The URL where the file is accessible
        cloud: Cloud provider ("aws", "gcp", "azure", "backblaze", etc.)
        region: Cloud region (e.g., "us-east-1", "eastus")
        type_: Access type ("s3", "https", "gs", etc.)
        dbagent: RefgetDBAgent instance
    """
    from refget.models import AccessMethod, AccessURL

    dbagent.fasta_drs.add_access_method(
        digest=digest,
        access_method=AccessMethod(
            type=type_,
            cloud=cloud,
            region=region,
            access_url=AccessURL(url=url),
        ),
    )


def _add_fasta_pep_to_db(
    pep,
    fa_root: str,
    dbagent,
    storage: Optional[List[Dict[str, Any]]] = None,
    skip_upload: bool = False,
    force_upload: bool = False,
) -> Dict[str, str]:
    """
    Add FASTA files from a PEP to the database.

    Args:
        pep: peppy.Project object
        fa_root: Root directory containing the FASTA files
        dbagent: RefgetDBAgent instance
        storage: Optional list of storage locations for upload/registration
        skip_upload: If True, don't upload files - just register URLs
        force_upload: If True, re-upload files even if they already exist

    Returns:
        dict: Mapping of FASTA filenames to seqcol digests
    """
    results = {}
    total = len(pep.samples)
    for i, s in enumerate(pep.samples, 1):
        fa_path = os.path.join(fa_root, s.fasta)
        name = getattr(s, "sample_name", None)
        print(f"[{i}/{total}] Adding {s.fasta}...")
        digest = _add_fasta_to_db(fa_path, dbagent, name=name)

        if storage:
            filename = os.path.basename(fa_path)
            for loc in storage:
                if skip_upload:
                    # Use provided URL or construct from bucket/prefix
                    if "url" in loc:
                        url = loc["url"]
                    else:
                        prefix = loc.get("prefix", "")
                        url = f"https://{loc['bucket']}.s3.amazonaws.com/{prefix}{filename}"
                else:
                    # Actually upload
                    cloud_name = loc.get("cloud", "").upper()
                    access_key = loc.get("access_key") or os.environ.get(
                        f"{cloud_name}_ACCESS_KEY"
                    )
                    secret_key = loc.get("secret_key") or os.environ.get(
                        f"{cloud_name}_SECRET_KEY"
                    )
                    url = _upload_to_s3(
                        fa_path,
                        loc["bucket"],
                        prefix=loc.get("prefix", ""),
                        access_key=access_key,
                        secret_key=secret_key,
                        endpoint=loc.get("endpoint"),
                        region=loc.get("region"),
                        url_base=loc.get("url_base"),
                        force=force_upload,
                    )

                _register_access_method(
                    digest=digest,
                    url=url,
                    cloud=loc["cloud"],
                    region=loc["region"],
                    type_=loc.get(
                        "type", "s3" if loc["cloud"] in ("aws", "backblaze") else "https"
                    ),
                    dbagent=dbagent,
                )

        print(f"         -> {digest}")
        results[s.fasta] = digest
    return results


def _load_seqcol_from_json(json_path: Path, dbagent) -> str:
    """
    Load a sequence collection from a .seqcol.json file.

    Args:
        json_path: Path to the JSON file
        dbagent: RefgetDBAgent instance

    Returns:
        The seqcol digest
    """
    with open(json_path, "r") as f:
        seqcol_dict = json.load(f)
    seqcol = dbagent.seqcol.add_from_dict(seqcol_dict, update=True)
    return seqcol.digest


@app.command()
def load(
    input_file: Optional[Path] = typer.Argument(
        None,
        help="FASTA or .seqcol.json file to load",
    ),
    pep: Optional[Path] = typer.Option(
        None,
        "--pep",
        help="PEP project file for batch loading",
    ),
    pephub: Optional[str] = typer.Option(
        None,
        "--pephub",
        help="PEPhub project (e.g., nsheff/human_fasta_ref)",
    ),
    fa_root: Optional[Path] = typer.Option(
        None,
        "--fa-root",
        help="Root directory for FASTA files (used with --pep/--pephub)",
    ),
    name: Optional[str] = typer.Option(
        None,
        "--name",
        "-n",
        help="Human-readable name for the FASTA",
    ),
) -> None:
    """
    Load seqcol metadata from FASTA or JSON into PostgreSQL.

    Can load from:
        - Single FASTA file
        - Single .seqcol.json file
        - Batch from PEP project file (--pep)
        - Batch from PEPhub project (--pephub)

    Database connection is configured via environment variables
    or config file (POSTGRES_HOST, POSTGRES_DB, etc.).

    Examples:
        refget admin load genome.fa
        refget admin load genome.fa --name "Human GRCh38"
        refget admin load genome.seqcol.json
        refget admin load --pep genomes.yaml --fa-root /data/fasta
        refget admin load --pephub nsheff/human_fasta_ref --fa-root /data/fasta
    """
    # Validate arguments
    if not input_file and not pep and not pephub:
        print_error(
            "Provide either a file to load, --pep, or --pephub",
            EXIT_FAILURE,
        )
        return

    if (pep or pephub) and not fa_root:
        print_error(
            "--fa-root is required when using --pep or --pephub",
            EXIT_FAILURE,
        )
        return

    dbagent = _get_dbagent()
    if dbagent is None:
        return

    # Single file loading
    if input_file:
        if not input_file.exists():
            print_error(f"File not found: {input_file}", EXIT_FILE_NOT_FOUND)
            return

        # Determine file type and load accordingly
        if str(input_file).endswith(".seqcol.json"):
            print_info(f"Loading seqcol from JSON: {input_file}")
            try:
                digest = _load_seqcol_from_json(input_file, dbagent)
                print_success(f"Loaded seqcol: {digest}")
                print_json({"digest": digest})
            except Exception as e:
                print_error(f"Failed to load JSON: {e}", EXIT_FAILURE)
        else:
            # Assume FASTA
            print_info(f"Loading seqcol from FASTA: {input_file}")
            try:
                digest = _add_fasta_to_db(str(input_file), dbagent, name=name)
                print_success(f"Loaded seqcol: {digest}")
                print_json({"digest": digest})
            except Exception as e:
                print_error(f"Failed to load FASTA: {e}", EXIT_FAILURE)
        return

    # Batch loading from PEP
    if pep or pephub:
        print_info("Loading from PEP project...")
        try:
            project = _load_pep(pep, pephub)
            if project is None:
                print_error("Failed to load PEP project", EXIT_FAILURE)
                return

            results = _add_fasta_pep_to_db(project, str(fa_root), dbagent)
            print_success(f"Loaded {len(results)} sequence collections")
            print_json(results)
        except ImportError as e:
            print_error(
                f"PEP loading requires peppy. Install with: pip install peppy\n{e}",
                EXIT_FAILURE,
            )
        except Exception as e:
            print_error(f"Failed to load from PEP: {e}", EXIT_FAILURE)


@app.command()
def register(
    fasta: Path = typer.Argument(
        ...,
        help="FASTA file to upload and register",
        exists=True,
        readable=True,
    ),
    bucket: str = typer.Option(
        ...,
        "--bucket",
        "-b",
        help="S3 bucket name for upload",
    ),
    prefix: str = typer.Option(
        "",
        "--prefix",
        "-p",
        help="S3 key prefix (default: none)",
    ),
    cloud: str = typer.Option(
        "aws",
        "--cloud",
        "-c",
        help="Cloud provider (default: aws)",
    ),
    region: str = typer.Option(
        "us-east-1",
        "--region",
        "-r",
        help="Cloud region (default: us-east-1)",
    ),
    digest: Optional[str] = typer.Option(
        None,
        "--digest",
        "-d",
        help="Seqcol digest (if not provided, will be computed from FASTA)",
    ),
) -> None:
    """
    Upload a FASTA file to S3 and create a DRS record.

    The FASTA is uploaded to the specified bucket, and a DRS
    (Data Repository Service) object record is created for access.

    Does NOT load seqcol metadata. Use 'ingest' for combined operation,
    or run 'load' first.

    Examples:
        refget admin register genome.fa --bucket my-refget-bucket
        refget admin register genome.fa -b my-bucket -p fasta/ -c aws -r us-west-2
        refget admin register genome.fa -b my-bucket --digest abc123...
    """
    if not _check_boto3():
        print_error(
            "'register' requires boto3. Install with: pip install boto3",
            EXIT_FAILURE,
        )
        return

    dbagent = _get_dbagent()
    if dbagent is None:
        return

    # Get or compute digest
    if not digest:
        print_info("Computing digest from FASTA...")
        from refget.store import digest_fasta

        digest = digest_fasta(str(fasta)).digest
        print_info(f"Computed digest: {digest}")

    print_info(f"Uploading {fasta} to s3://{bucket}/{prefix}...")

    try:
        # Upload to S3
        url = _upload_to_s3(str(fasta), bucket, prefix, region=region)

        # Register access method
        _register_access_method(
            digest=digest,
            url=url,
            cloud=cloud,
            region=region,
            type_="s3" if cloud in ("aws", "backblaze") else "https",
            dbagent=dbagent,
        )
        print_success(f"Registered: {url}")
        print_json({"digest": digest, "url": url})
    except Exception as e:
        print_error(f"Failed to register FASTA: {e}", EXIT_FAILURE)


@app.command()
def ingest(
    fasta: Optional[Path] = typer.Argument(
        None,
        help="FASTA file to load and register",
    ),
    bucket: str = typer.Option(
        ...,
        "--bucket",
        "-b",
        help="S3 bucket name for upload",
    ),
    prefix: str = typer.Option(
        "",
        "--prefix",
        "-p",
        help="S3 key prefix (default: none)",
    ),
    cloud: str = typer.Option(
        "aws",
        "--cloud",
        "-c",
        help="Cloud provider (default: aws)",
    ),
    region: str = typer.Option(
        "us-east-1",
        "--region",
        "-r",
        help="Cloud region (default: us-east-1)",
    ),
    pep: Optional[Path] = typer.Option(
        None,
        "--pep",
        help="PEP project file for batch ingestion",
    ),
    pephub: Optional[str] = typer.Option(
        None,
        "--pephub",
        help="PEPhub project (e.g., nsheff/human_fasta_ref)",
    ),
    fa_root: Optional[Path] = typer.Option(
        None,
        "--fa-root",
        help="Root directory for FASTA files (used with --pep/--pephub)",
    ),
    name: Optional[str] = typer.Option(
        None,
        "--name",
        "-n",
        help="Human-readable name for the FASTA",
    ),
) -> None:
    """
    Load seqcol metadata and register FASTA with cloud storage.

    Combines 'load' and 'register' in a single operation:
        1. Parse FASTA and extract seqcol metadata
        2. Store metadata in PostgreSQL
        3. Upload FASTA to S3
        4. Create DRS record for access

    Can process single files or batch from PEP.

    Examples:
        refget admin ingest genome.fa --bucket my-bucket
        refget admin ingest genome.fa -b my-bucket --name "Human GRCh38"
        refget admin ingest --pep genomes.yaml --fa-root /data/fasta --bucket my-bucket
    """
    if not _check_boto3():
        print_error(
            "'ingest' requires boto3. Install with: pip install boto3",
            EXIT_FAILURE,
        )
        return

    # Validate arguments
    if not fasta and not pep and not pephub:
        print_error(
            "Provide either a FASTA file, --pep, or --pephub",
            EXIT_FAILURE,
        )
        return

    if (pep or pephub) and not fa_root:
        print_error(
            "--fa-root is required when using --pep or --pephub",
            EXIT_FAILURE,
        )
        return

    dbagent = _get_dbagent()
    if dbagent is None:
        return

    # Build storage configuration
    storage = [
        {
            "bucket": bucket,
            "prefix": prefix,
            "cloud": cloud,
            "region": region,
        }
    ]

    # Single file ingestion
    if fasta:
        if not fasta.exists():
            print_error(f"File not found: {fasta}", EXIT_FILE_NOT_FOUND)
            return

        print_info(f"Loading and registering: {fasta}")
        try:
            # Load metadata
            digest = _add_fasta_to_db(str(fasta), dbagent, name=name)

            # Upload and register
            url = _upload_to_s3(str(fasta), bucket, prefix, region=region)
            _register_access_method(
                digest=digest,
                url=url,
                cloud=cloud,
                region=region,
                type_="s3" if cloud in ("aws", "backblaze") else "https",
                dbagent=dbagent,
            )
            print_success(f"Ingested: {digest}")
            print_json({"digest": digest, "bucket": bucket, "prefix": prefix})
        except Exception as e:
            print_error(f"Failed to ingest FASTA: {e}", EXIT_FAILURE)
        return

    # Batch ingestion from PEP
    if pep or pephub:
        print_info("Ingesting from PEP project...")
        try:
            project = _load_pep(pep, pephub)
            if project is None:
                print_error("Failed to load PEP project", EXIT_FAILURE)
                return

            results = _add_fasta_pep_to_db(
                project,
                str(fa_root),
                dbagent,
                storage=storage,
            )
            print_success(f"Ingested {len(results)} sequence collections")
            print_json(results)
        except ImportError as e:
            print_error(
                f"PEP loading requires peppy. Install with: pip install peppy\n{e}",
                EXIT_FAILURE,
            )
        except Exception as e:
            print_error(f"Failed to ingest from PEP: {e}", EXIT_FAILURE)


@app.command()
def status() -> None:
    """
    Show admin/database connection status.

    Tests the database connection and displays connection info
    and table statistics.

    Example:
        refget admin status
    """
    # Check environment variables
    pg_host = os.environ.get("POSTGRES_HOST", "(not set)")
    pg_db = os.environ.get("POSTGRES_DB", "(not set)")
    pg_user = os.environ.get("POSTGRES_USER", "(not set)")
    pg_port = os.environ.get("POSTGRES_PORT", "5432")

    print_info("Database Configuration:")
    print(f"  Host: {pg_host}")
    print(f"  Port: {pg_port}")
    print(f"  Database: {pg_db}")
    print(f"  User: {pg_user}")
    print()

    # Test connection
    try:
        from refget.agents import RefgetDBAgent

        dbagent = RefgetDBAgent()
        print_success("Database connection: OK")

        # Get table counts
        seqcol_result = dbagent.seqcol.list_by_offset(limit=1, offset=0)
        fasta_drs_result = dbagent.fasta_drs.list_by_offset(limit=1, offset=0)

        print()
        print_info("Table Statistics:")
        print(f"  Sequence Collections: {seqcol_result['pagination']['total']}")
        print(f"  FASTA DRS Objects: {fasta_drs_result['pagination']['total']}")

    except Exception as e:
        print_error(f"Database connection: FAILED\n  {e}")
        raise typer.Exit(EXIT_FAILURE)


@app.command()
def info() -> None:
    """
    Show system info (version, dependencies, etc.).

    Displays version information and optional dependency status.

    Example:
        refget admin info
    """
    from refget._version import __version__

    print_info("Refget Admin Info")
    print()
    print(f"  refget version: {__version__}")

    # Check optional dependencies
    print()
    print_info("Dependencies:")

    # gtars
    try:
        from gtars import __version__ as gtars_version

        print(f"  gtars: {gtars_version}")
    except ImportError:
        print("  gtars: not installed")
    except AttributeError:
        print("  gtars: installed (version unknown)")

    # boto3
    try:
        import boto3

        print(f"  boto3: {boto3.__version__}")
    except ImportError:
        print("  boto3: not installed (required for cloud uploads)")

    # peppy
    try:
        import peppy

        print(f"  peppy: {peppy.__version__}")
    except ImportError:
        print("  peppy: not installed (required for PEP batch operations)")
    except AttributeError:
        print("  peppy: installed (version unknown)")

    # sqlmodel
    try:
        import sqlmodel

        print(f"  sqlmodel: {sqlmodel.__version__}")
    except ImportError:
        print("  sqlmodel: not installed")
    except AttributeError:
        print("  sqlmodel: installed (version unknown)")

    # Check boto3 for S3 support
    print()
    print_info("Cloud Storage:")
    if _check_boto3():
        print("  S3 uploads: available")
    else:
        print("  S3 uploads: not available (install boto3)")
