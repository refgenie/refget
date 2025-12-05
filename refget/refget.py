import json
import os
import logging
import requests

from copy import copy

from .agents import RefgetDBAgent

_LOGGER = logging.getLogger(__name__)

SCHEMA_FILEPATH = os.path.join(os.path.dirname(__file__), "schemas")

sequence_schema = """description: "Schema for a single raw sequence"
henge_class: sequence
type: string
description: "Actual sequence content"
"""


def build_argparser():
    from . import __version__

    version_str = f"{__version__} "
    from ubiquerg import VersionInHelpParser

    additional_description = "https://refgenie.org/refget"
    banner = f"%(prog)s - a tool for getting sequences by digest"
    parser = VersionInHelpParser(
        prog="refget",
        description=banner,
        epilog=additional_description,
        version=version_str,
    )
    subparsers = parser.add_subparsers(dest="command")

    # --- load command (replaces add-fasta) ---
    load_parser = subparsers.add_parser(
        "load",
        help="Load FASTA files into the refget database",
        description="Load FASTA files into the database, creating SequenceCollection and FastaDrsObject records.",
    )
    load_parser.add_argument("--fasta", "-f", help="Single FASTA file to load")
    load_parser.add_argument("--name", "-n", help="Human-readable name for the FASTA")
    load_parser.add_argument("--pep", "-p", help="Local PEP file for batch loading")
    load_parser.add_argument("--pephub", help="PEPhub project (e.g., nsheff/human_fasta_ref)")
    load_parser.add_argument(
        "--fa-root", "-r", help="Root directory for FASTA files (with --pep/--pephub)"
    )

    # --- register command ---
    register_parser = subparsers.add_parser(
        "register",
        help="Upload to cloud storage and register access methods",
        description="Upload FASTA files to cloud storage and register access methods on existing FastaDrsObject records.",
    )
    register_parser.add_argument("--digest", "-d", help="Seqcol digest (for single file)")
    register_parser.add_argument("--fasta", "-f", help="FASTA file to upload")
    register_parser.add_argument("--pep", "-p", help="Local PEP file for batch registration")
    register_parser.add_argument("--pephub", help="PEPhub project")
    register_parser.add_argument("--fa-root", "-r", help="Root directory for FASTA files")
    register_parser.add_argument("--bucket", "-b", required=True, help="S3 bucket name")
    register_parser.add_argument("--prefix", default="", help="S3 key prefix/folder")
    register_parser.add_argument(
        "--cloud", "-c", default="aws", help="Cloud provider (default: aws)"
    )
    register_parser.add_argument(
        "--region", default="us-east-1", help="Cloud region (default: us-east-1)"
    )

    # --- load-and-register command ---
    full_parser = subparsers.add_parser(
        "load-and-register",
        help="Load FASTAs and register with cloud storage (full workflow)",
        description="Full workflow: load FASTAs into database, upload to cloud, and register access methods.",
    )
    full_parser.add_argument("--fasta", "-f", help="Single FASTA file")
    full_parser.add_argument("--name", "-n", help="Human-readable name for the FASTA")
    full_parser.add_argument("--pep", "-p", help="Local PEP file for batch processing")
    full_parser.add_argument("--pephub", help="PEPhub project")
    full_parser.add_argument("--fa-root", "-r", help="Root directory for FASTA files")
    full_parser.add_argument("--bucket", "-b", required=True, help="S3 bucket name")
    full_parser.add_argument("--prefix", default="", help="S3 key prefix/folder")
    full_parser.add_argument("--cloud", "-c", default="aws", help="Cloud provider (default: aws)")
    full_parser.add_argument(
        "--region", default="us-east-1", help="Cloud region (default: us-east-1)"
    )

    # --- digest-fasta command (local, no DB) ---
    digest_fasta = subparsers.add_parser(
        "digest-fasta",
        help="Compute digest of a FASTA file (no database)",
    )
    digest_fasta.add_argument("fasta_file", help="Path to the fasta file")
    digest_fasta.add_argument(
        "--level", "-l", help="Output level, one of 0, 1 or 2 (default).", default=2, type=int
    )

    # --- add-fasta (deprecated, hidden) ---
    add_fasta = subparsers.add_parser("add-fasta", help="[Deprecated: use 'load' instead]")
    add_fasta.add_argument("--fasta-file", help="Path to the fasta file", default=None)
    add_fasta.add_argument(
        "--pep", "-p", help="Set to input a pep of FASTA files", type=str, default=False
    )
    add_fasta.add_argument("--fa-root", "-r", help="Root directory for fasta files", default="")

    return parser


class BytesEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, bytes):
            return obj.decode(errors="ignore")  # or use base64 encoding
        return super().default(obj)


def load_pep(pep_path=None, pephub=None):
    """Load a PEP from file or pephub."""
    if pep_path:
        import peppy

        return peppy.Project(pep_path)
    elif pephub:
        import pephubclient

        phc = pephubclient.PEPHubClient()
        return phc.load_project(pephub)
    return None


def add_fasta(
    fasta_path, name=None, dbagent=None, storage=None, skip_upload=False, force_upload=False
):
    """
    Add a FASTA file to the refget database.

    Creates SequenceCollection and FastaDrsObject records.
    Optionally uploads to cloud storage and registers access URLs.
    Idempotent: re-running updates existing records.

    Args:
        fasta_path: Path to the FASTA file
        name: Human-readable name (optional)
        dbagent: RefgetDBAgent instance (creates one if not provided)
        storage: Optional list of storage locations, each with keys:
            - bucket: S3 bucket name
            - prefix: Optional prefix/folder in the bucket (default: "")
            - cloud: Cloud provider ("aws", "gcp", "azure", "backblaze", etc.)
            - region: Cloud region (e.g., "us-east-1")
            - url: (optional) Pre-existing URL (used when skip_upload=True)
        skip_upload: If True, don't upload files - just register URLs.
            When True, each storage entry should have a 'url' key, or the URL
            will be constructed from bucket/prefix/filename.
        force_upload: If True, re-upload files even if they already exist (default: False)

    Returns:
        str: The seqcol digest
    """
    if dbagent is None:
        dbagent = RefgetDBAgent()
    if name:
        seqcol = dbagent.seqcol.add_from_fasta_file_with_name(fasta_path, name, update=True)
    else:
        seqcol = dbagent.seqcol.add_from_fasta_file(fasta_path, update=True)

    digest = seqcol.digest

    if storage:
        filename = os.path.basename(fasta_path)
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
                # Resolve credentials: JSON > {CLOUD}_ACCESS_KEY env var > boto3 default
                cloud = loc.get("cloud", "").upper()
                access_key = loc.get("access_key") or os.environ.get(f"{cloud}_ACCESS_KEY")
                secret_key = loc.get("secret_key") or os.environ.get(f"{cloud}_SECRET_KEY")
                url = _upload_to_s3(
                    fasta_path,
                    loc["bucket"],
                    prefix=loc.get("prefix", ""),
                    access_key=access_key,
                    secret_key=secret_key,
                    endpoint=loc.get("endpoint"),
                    region=loc.get("region"),
                    url_base=loc.get("url_base"),
                    force=force_upload,
                )

            add_access_method(
                digest=digest,
                url=url,
                cloud=loc["cloud"],
                region=loc["region"],
                type_=loc.get("type", "s3" if loc["cloud"] in ("aws", "backblaze") else "https"),
                dbagent=dbagent,
            )

    return digest


def add_fasta_pep(pep, fa_root, dbagent=None, storage=None, skip_upload=False, force_upload=False):
    """
    Add FASTA files from a PEP to the refget database.

    Optionally uploads to cloud storage and registers access methods.

    Args:
        pep: peppy.Project object
        fa_root: Root directory containing the FASTA files
        dbagent: RefgetDBAgent instance (creates one if not provided)
        storage: Optional list of storage locations (see add_fasta for format)
        skip_upload: If True, don't upload files - just register URLs
        force_upload: If True, re-upload files even if they already exist (default: False)

    Returns:
        dict: Mapping of FASTA filenames to seqcol digests
    """
    if dbagent is None:
        dbagent = RefgetDBAgent()
    results = {}
    total = len(pep.samples)
    for i, s in enumerate(pep.samples, 1):
        fa_path = os.path.join(fa_root, s.fasta)
        name = getattr(s, "sample_name", None)
        print(f"[{i}/{total}] Adding {s.fasta}...")
        digest = add_fasta(
            fa_path,
            name=name,
            dbagent=dbagent,
            storage=storage,
            skip_upload=skip_upload,
            force_upload=force_upload,
        )
        print(f"         -> {digest}")
        results[s.fasta] = digest
    return results


# Aliases for backwards compatibility
load_fasta = add_fasta
load_fasta_pep = add_fasta_pep


def _check_boto3():
    """Check if boto3 is available."""
    try:
        import boto3  # noqa: F401

        return True
    except ImportError:
        return False


def _upload_to_s3(
    fasta_path,
    bucket,
    prefix="",
    access_key=None,
    secret_key=None,
    endpoint=None,
    region=None,
    url_base=None,
    force=False,
):
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


def add_access_method(digest, url, cloud, region, type_="https", dbagent=None):
    """
    Add an access method to an existing FastaDrsObject.

    Use this to register URLs for files already hosted somewhere
    (without uploading).

    Args:
        digest: The seqcol digest
        url: The URL where the file is accessible
        cloud: Cloud provider ("aws", "gcp", "azure", "backblaze", etc.)
        region: Cloud region (e.g., "us-east-1", "eastus")
        type_: Access type ("s3", "https", "gs", etc.) - default "https"
        dbagent: RefgetDBAgent instance (creates one if not provided)
    """
    from .models import AccessMethod, AccessURL

    if dbagent is None:
        dbagent = RefgetDBAgent()

    dbagent.fasta_drs.add_access_method(
        digest=digest,
        access_method=AccessMethod(
            type=type_,
            cloud=cloud,
            region=region,
            access_url=AccessURL(url=url),
        ),
    )


def register_fasta(
    digest, fasta_path, bucket, prefix="", cloud="aws", region="us-east-1", dbagent=None
):
    """
    Upload a FASTA file to cloud storage and register the access method.

    The FASTA must already be loaded (use load_fasta first).
    Requires boto3.

    Args:
        digest: The seqcol digest (from load_fasta)
        fasta_path: Path to the FASTA file
        bucket: S3 bucket name
        prefix: Optional prefix/folder in the bucket
        cloud: Cloud provider ("aws", "gcp", "azure", "backblaze", etc.)
        region: Cloud region (e.g., "us-east-1")
        dbagent: RefgetDBAgent instance (creates one if not provided)

    Returns:
        str: The cloud URL
    """
    if dbagent is None:
        dbagent = RefgetDBAgent()

    # Upload to S3
    url = _upload_to_s3(fasta_path, bucket, prefix)

    # Register access method
    add_access_method(
        digest=digest,
        url=url,
        cloud=cloud,
        region=region,
        type_="s3" if cloud in ("aws", "backblaze") else "https",
        dbagent=dbagent,
    )
    return url


def register_fasta_pep(
    pep, fa_root, bucket, prefix="", cloud="aws", region="us-east-1", dbagent=None, digest_map=None
):
    """
    Upload FASTA files from a PEP to cloud storage and register access methods.

    The FASTAs must already be loaded. Provide digest_map from load_fasta_pep,
    or digests will be computed from the files.

    Args:
        pep: peppy.Project object
        fa_root: Root directory containing the FASTA files
        bucket: S3 bucket name
        prefix: Optional prefix/folder in the bucket
        cloud: Cloud provider
        region: Cloud region
        dbagent: RefgetDBAgent instance
        digest_map: Optional dict mapping filenames to digests (from load_fasta_pep)

    Returns:
        dict: Mapping of FASTA filenames to cloud URLs
    """
    from .utilities import fasta_to_digest

    if dbagent is None:
        dbagent = RefgetDBAgent()

    results = {}
    total = len(pep.samples)
    for i, s in enumerate(pep.samples, 1):
        fa_path = os.path.join(fa_root, s.fasta)
        # Get digest from map or compute it
        if digest_map and s.fasta in digest_map:
            digest = digest_map[s.fasta]
        else:
            digest = fasta_to_digest(fa_path)
        print(f"[{i}/{total}] Registering {s.fasta} ({digest})...")
        url = register_fasta(digest, fa_path, bucket, prefix, cloud, region, dbagent)
        print(f"         -> {url}")
        results[s.fasta] = url
    return results


def main(injected_args=None):
    parser = build_argparser()
    args = parser.parse_args()
    _LOGGER.debug(args)

    if not args.command:
        parser.print_help()
        return

    if args.command == "load":
        dbagent = RefgetDBAgent()
        if args.fasta:
            digest = load_fasta(args.fasta, name=args.name, dbagent=dbagent)
            print(f"Loaded: {digest}")
        elif args.pep or args.pephub:
            pep = load_pep(args.pep, args.pephub)
            results = load_fasta_pep(pep, args.fa_root, dbagent=dbagent)
            print("\nResults:")
            print(json.dumps(results, indent=2))
        else:
            parser.parse_args(["load", "--help"])

    elif args.command == "register":
        if not _check_boto3():
            print("Error: 'register' requires boto3. Install it with: pip install boto3")
            return
        dbagent = RefgetDBAgent()
        if args.digest and args.fasta:
            url = register_fasta(
                args.digest, args.fasta, args.bucket, args.prefix, args.cloud, args.region, dbagent
            )
            print(f"Registered: {url}")
        elif args.pep or args.pephub:
            pep = load_pep(args.pep, args.pephub)
            results = register_fasta_pep(
                pep, args.fa_root, args.bucket, args.prefix, args.cloud, args.region, dbagent
            )
            print("\nResults:")
            print(json.dumps(results, indent=2))
        else:
            parser.parse_args(["register", "--help"])

    elif args.command == "load-and-register":
        if not _check_boto3():
            print("Error: 'load-and-register' requires boto3. Install it with: pip install boto3")
            return
        dbagent = RefgetDBAgent()
        if args.fasta:
            digest = load_fasta(args.fasta, name=args.name, dbagent=dbagent)
            url = register_fasta(
                digest, args.fasta, args.bucket, args.prefix, args.cloud, args.region, dbagent
            )
            print(f"Digest: {digest}")
            print(f"URL: {url}")
        elif args.pep or args.pephub:
            pep = load_pep(args.pep, args.pephub)
            # Load first
            digest_map = load_fasta_pep(pep, args.fa_root, dbagent=dbagent)
            # Then register
            print("\nRegistering with cloud storage...")
            url_map = register_fasta_pep(
                pep,
                args.fa_root,
                args.bucket,
                args.prefix,
                args.cloud,
                args.region,
                dbagent,
                digest_map,
            )
            print("\nResults:")
            for fasta in digest_map:
                print(f"  {fasta}:")
                print(f"    digest: {digest_map[fasta]}")
                print(f"    url: {url_map[fasta]}")
        else:
            parser.parse_args(["load-and-register", "--help"])

    elif args.command == "add-fasta":
        # Deprecated - redirect to load
        print("Warning: 'add-fasta' is deprecated. Use 'refget load' instead.\n")
        if args.pep:
            _LOGGER.info(f"Adding fasta file from PEP: {args.pep}")
            import peppy

            p = peppy.Project(args.pep)
            agent = RefgetDBAgent()
            result = agent.seqcol.add_from_fasta_pep(p, args.fa_root)
            print(json.dumps(result, indent=2, cls=BytesEncoder))
        if args.fasta_file:
            _LOGGER.info(f"Adding fasta file: {args.fasta_file}")
            agent = RefgetDBAgent()
            agent.seqcol.add_from_fasta_file(args.fasta_file)
            _LOGGER.info("Added fasta file")

    elif args.command == "digest-fasta":
        _LOGGER.info(f"Digesting fasta file: {args.fasta_file}")
        if args.level == 0:
            from .utilities import fasta_to_digest

            digest = fasta_to_digest(args.fasta_file)
            print(digest)
        elif args.level == 1:
            from .utilities import fasta_to_seqcol_dict, seqcol_dict_to_level1_dict

            seqcol_dict = fasta_to_seqcol_dict(args.fasta_file)
            level1_dict = seqcol_dict_to_level1_dict(seqcol_dict)
            print(json.dumps(level1_dict, indent=2))
        elif args.level == 2:
            from .utilities import fasta_to_seqcol_dict

            seqcol_dict = fasta_to_seqcol_dict(args.fasta_file)
            print(json.dumps(seqcol_dict, indent=2, cls=BytesEncoder))

    else:
        print("No command given")
