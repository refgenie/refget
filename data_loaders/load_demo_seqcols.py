"""
Load demo sequence collections into the refget database.

Before running this script, set up env vars:
    source deployment/local_demo/local_demo.env

Usage:
    python data_loaders/load_demo_seqcols.py
"""

import os
import json

from refget import add_fasta
from refget.agents import RefgetDBAgent

# Configuration
FA_ROOT = "test_fasta"
DEMO_FASTA = json.load(open("test_fasta/test_fasta_digests.json"))

# Storage locations from environment (if set, will upload; otherwise use demo defaults with skip_upload)
ENV_STORAGE = json.loads(os.environ.get("FASTA_STORAGE_LOCATIONS", "[]"))
if ENV_STORAGE:
    DEMO_STORAGE = ENV_STORAGE
    SKIP_UPLOAD = False
else:
    DEMO_STORAGE = [
        {
            "bucket": "my-bucket",
            "prefix": "fasta/",
            "cloud": "aws",
            "region": "us-east-1",
            "type": "s3",
        },
        {
            "bucket": "myaccount.blob.core.windows.net",
            "prefix": "fasta/",
            "cloud": "azure",
            "region": "eastus",
            "type": "https",
        },
    ]
    SKIP_UPLOAD = True

# Initialize database agent
dbc = RefgetDBAgent()
print(f"SQL Engine: {dbc.engine}")

# Add FASTA files to the database with demo access URLs (skip actual upload)
print("\nAdding demo sequence collections...")
demo_results = {}

for name, demo_file in DEMO_FASTA.items():
    filename = demo_file["name"]
    fasta_path = os.path.join(FA_ROOT, filename)

    digest = add_fasta(
        fasta_path,
        name=name,
        dbagent=dbc,
        storage=DEMO_STORAGE,
        skip_upload=SKIP_UPLOAD,
    )
    demo_results[filename] = digest
    print(f"  {filename}: {digest}")

print(f"\nAdded {len(demo_results)} sequence collections.")
print(f"\nResults: {json.dumps(demo_results, indent=2)}")
