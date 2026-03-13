#!/bin/bash
#SBATCH --job-name=profile_mem
#SBATCH --output=profile_mem_%j.log
#SBATCH --error=profile_mem_%j.log
#SBATCH --partition=standard
#SBATCH --time=2:00:00
#SBATCH --mem=16G
#SBATCH --cpus-per-task=4
#SBATCH --account=shefflab

module load miniforge/24.3.0-py3.11

cd /project/shefflab/brickyard/datasets_downloaded/refgenomes_fasta/refget/data_loaders/ref-genome-analysis/profiling

python profile_memory.py 850 5
