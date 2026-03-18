#!/bin/bash
#SBATCH --job-name=backfill_aliases
#SBATCH --output=backfill_aliases_%j.log
#SBATCH --error=backfill_aliases_%j.log
#SBATCH --partition=standard
#SBATCH --time=2:00:00
#SBATCH --mem=16G
#SBATCH --cpus-per-task=1
#SBATCH --account=shefflab

module load miniforge/24.3.0-py3.11

cd $HOME/code/ref-genome-analysis
source env/on-cluster.env

# Backfill VGP store
python src/backfill_sequence_aliases.py --target $BRICK_ROOT/vgp_reference_store

# Backfill ref store (if it exists)
if [ -d "$BRICK_ROOT/refgenome_jungle_store" ]; then
    python src/backfill_sequence_aliases.py --target $BRICK_ROOT/refgenome_jungle_store
fi
