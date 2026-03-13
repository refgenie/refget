# ref-genome-analysis

Pipeline for loading reference genome FASTA files into a RefgetStore and enriching them with NCBI aliases and FHR provenance metadata.

## Pipeline stages

Execute in order:

```
inventory --> build --> aliases --> fhr --> verify
```

| Stage | Directory | Purpose |
|---|---|---|
| **inventory** | `inventory/` | Scan brickyard FASTA files, produce `refgenomes_inventory.csv` |
| **build** | `build/` | Load FASTAs into RefgetStore, produce `digest_map.csv` |
| **aliases** | `aliases/` | Download NCBI assembly reports, build alias table, register sequence/collection aliases |
| **fhr** | `fhr/` | Generate and attach FHR provenance metadata (species, taxon, accession, submitter, etc.) |
| **verify** | `verify/` | Automated pass/fail checks against the store |
| **profiling** | `profiling/` | Memory and timing benchmarks |
| **examples** | `examples/` | End-to-end test scripts (e.g., load 20 genomes with FHR) |

## Rivanna paths

All data lives within the `refgenomes_fasta` brickyard brick:

```
/project/shefflab/brickyard/datasets_downloaded/refgenomes_fasta/
├── homo_sapiens/...              # Source FASTAs
├── mus_musculus/...
├── refgenomes_inventory.csv      # Inventory of all FASTAs
├── refget_store/                 # The RefgetStore (fixed-format, don't modify manually)
└── refget_staging/               # Pipeline intermediates
    ├── assembly_reports/         # Downloaded NCBI assembly_report.txt files
    ├── ncbi_alias_table.csv      # Parsed alias table (367K sequence rows)
    ├── fhr_metadata/             # Generated FHR provenance JSON files
    └── digest_map.csv            # Build output mapping FASTAs to digests
```

- **Store**: `.../refgenomes_fasta/refget_store`
- **Staging**: `.../refgenomes_fasta/refget_staging`
- **This pipeline**: `.../refgenomes_fasta/refget/data_loaders/ref-genome-analysis/`

## Quick start (Rivanna)

```bash
module load miniforge/24.3.0-py3.11

# 1. Build store
sbatch build/build_refgetstore.sbatch

# 2. Register NCBI aliases
sbatch aliases/register_aliases.sbatch

# 3. Attach FHR metadata
cd fhr && python load_fhr_metadata.py --store-path /project/shefflab/brickyard/datasets_downloaded/refgenomes_fasta/refget_store --fhr-dir metadata/

# 4. Verify
cd verify && python verify_refgetstore.py
```
