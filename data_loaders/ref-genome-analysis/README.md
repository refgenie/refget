# ref-genome-analysis

Pipeline for loading reference genome FASTA files into a RefgetStore and enriching them with NCBI aliases and FHR provenance metadata.

## Setup

```bash
source env/on-cluster.env        # on Rivanna directly
source env/remote-hpc.env        # from laptop, targeting Rivanna
./env/mutagen-setup.sh           # start file sync (laptop only)
```

## Pipeline stages

Execute in order:

```
inventory --> build --> aliases --> fhr --> verify
```

| Stage | Location | Purpose |
|---|---|---|
| **inventory** | `src/01_inventory/` | Scan brickyard FASTA files, produce `refgenomes_inventory.csv` |
| **build** | `src/02_build/` | Compute seqcol digests for all FASTAs, produce `digest_map.csv` |
| **aliases** | `src/02_aliases/` | Download NCBI assembly reports, build alias table, register sequence/collection aliases |
| **fhr** | `src/03_fhr/` | Generate and attach FHR provenance metadata (species, taxon, accession, submitter, etc.) |
| **verify** | `src/04_verify/` | Automated pass/fail checks against the store |
| **profiling** | `src/05_profiling/` | Memory and timing benchmarks |
| **split** | `src/90_split_store.py` | Split combined store into VGP and reference genome stores |
| **backfill** | `src/backfill_sequence_aliases.py` | Re-register aliases into split stores from NCBI alias table |
| **validate** | `src/validate_split_stores.py` | Validate split stores (counts, aliases, FHR, sequences, cross-store) |
| **push** | `src/push_to_s3.sh` | Push split stores to S3 (`s3://refgenie/`) |
| **examples** | `src/examples/` | End-to-end test scripts (e.g., load 20 genomes with FHR) |

## Environment variables

All paths come from environment variables set by sourcing an env file. No hardcoded paths in scripts.

| Variable | Purpose |
|---|---|
| `BRICKYARD` | Lab-wide brickyard root |
| `BRICK_ROOT` | This project's brick (`$BRICKYARD/datasets_downloaded/refgenomes_fasta`) |
| `STORE_PATH` | The RefgetStore database |
| `STAGING` | Pipeline intermediates (assembly reports, alias tables, FHR JSON) |
| `INVENTORY_CSV` | Inventory of all FASTAs |

## Quick start (Rivanna)

```bash
source env/on-cluster.env
module load miniforge/24.3.0-py3.11

# 1. Inventory
python src/01_inventory/inventory_genomes.py

# 2. Register NCBI aliases
sbatch src/02_aliases/register_aliases.sbatch

# 3. Attach FHR metadata
python src/03_fhr/batch_generate_fhr.py --inventory $INVENTORY_CSV --output-dir $STAGING/fhr_metadata
python src/03_fhr/load_fhr_metadata.py --store-path $STORE_PATH --fhr-dir $STAGING/fhr_metadata

# 4. Verify
python src/04_verify/verify_refgetstore.py

# 5. Split into VGP + ref stores
sbatch src/90_split_store.sbatch

# 6. Backfill aliases into split stores
python src/backfill_sequence_aliases.py --target $BRICK_ROOT/vgp_reference_store
python src/backfill_sequence_aliases.py --target $BRICK_ROOT/refgenome_jungle_store

# 7. Validate split stores
sbatch src/validate_split_stores.sbatch

# 8. Push to S3 (requires GPG agent forwarding: ssh riva1_gpg)
bash src/push_to_s3.sh both
```

## S3 deployment

Requires GPG agent forwarding for `pass` credentials (see `ssh riva1_gpg` in SSH config).

```bash
ssh riva1_gpg
cd code/ref-genome-analysis
source env/on-cluster.env
bash src/push_to_s3.sh vgp   # or: ref, both, "vgp --dry-run"
```

Stores are pushed to `s3://refgenie/refget-store/vgp` and `s3://refgenie/refget-store/jungle`.

To load from S3:

```python
from refget.store import RefgetStore
store = RefgetStore.open_remote(
    "~/.refget/vgp_cache",
    "https://refgenie.s3.us-east-1.amazonaws.com/refget-store/vgp"
)
```
