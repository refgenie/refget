#!/bin/bash
#SBATCH --job-name=profile_normal
#SBATCH --output=profile_normal_%j.log
#SBATCH --error=profile_normal_%j.log
#SBATCH --partition=standard
#SBATCH --time=0:30:00
#SBATCH --mem=8G
#SBATCH --cpus-per-task=4
#SBATCH --account=shefflab

module load miniforge/24.3.0-py3.11

cd /project/shefflab/brickyard/datasets_downloaded/refgenomes_fasta/refget/data_loaders/ref-genome-analysis/profiling

python profile_normal.py
