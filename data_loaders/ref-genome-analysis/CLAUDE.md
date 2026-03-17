# ref-genome-analysis

Pipeline for building a RefgetStore from reference genome FASTA files. Inventories genomes from the brickyard, loads them into a refget store, registers NCBI aliases, generates FAIR Header Representation (FHR) metadata, and verifies the result.

## Setup

Source the environment for your compute target:
- HPC (from laptop): `source env/remote-hpc.env`
- HPC (direct): `source env/on-cluster.env`

To start mutagen sync: `./env/mutagen-setup.sh`

## Pipeline Phases

Execute in order:

1. **01_inventory** -- Scan brickyard, generate CSV inventory of all FASTA files
   - `python src/01_inventory/inventory_genomes.py`

2. **02_aliases** -- Download NCBI assembly reports, build alias table, register in store
   - Phase A: `python src/02_aliases/build_ncbi_alias_table.py` (downloads from NCBI, slow)
   - Phase B: `sbatch src/02_aliases/register_aliases.sbatch`

3. **03_fhr** -- Generate FAIR Header Representation metadata, load into store
   - `python src/03_fhr/batch_generate_fhr.py --inventory $INVENTORY_CSV --output-dir $STAGING/fhr_metadata`
   - `python src/03_fhr/load_fhr_metadata.py --store-path $STORE_PATH --fhr-dir $STAGING/fhr_metadata`

4. **04_verify** -- Validate store integrity
   - `python src/04_verify/verify_refgetstore.py`

## Key Environment Variables

- `BRICK_ROOT` -- Root of the refgenomes_fasta brick
- `STORE_PATH` -- Path to the RefgetStore database
- `STAGING` -- Staging area for intermediates (assembly reports, alias tables, FHR JSON)
- `INVENTORY_CSV` -- Path to the genome inventory CSV

## Dependencies

- Python 3.11+ (via `module load miniforge/24.3.0-py3.11` on Rivanna)
- `refget` or `gtars` Python package (for RefgetStore)
- Internet access for NCBI API calls (phases 2 and 3)

## Notes

- All phases are resumable -- cached downloads, idempotent store operations
- Phase 2A rate-limits NCBI requests (0.3s between calls)
- `src/05_profiling/` contains memory/timing benchmarks (not part of the main pipeline)
- `src/examples/` contains a 20-genome integration test
