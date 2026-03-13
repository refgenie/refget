#!/bin/bash
#SBATCH --job-name=ncbi_aliases
#SBATCH --output=ncbi_aliases_%j.log
#SBATCH --error=ncbi_aliases_%j.log
#SBATCH --partition=standard
#SBATCH --time=4:00:00
#SBATCH --mem=8G
#SBATCH --cpus-per-task=1
#SBATCH --account=shefflab

module load miniforge/24.3.0-py3.11

cd /project/shefflab/brickyard/datasets_downloaded/refgenomes_fasta/refget/data_loaders/ref-genome-analysis/aliases

python register_ncbi_aliases.py --store-path /project/shefflab/brickyard/datasets_downloaded/refgenomes_fasta/refget_store
