#!/bin/bash
#SBATCH --job-name=refgetstore
#SBATCH --output=refgetstore_%j.log
#SBATCH --error=refgetstore_%j.log
#SBATCH --partition=standard
#SBATCH --time=24:00:00
#SBATCH --mem=16G
#SBATCH --cpus-per-task=4
#SBATCH --account=shefflab

module load miniforge/24.3.0-py3.11

cd /project/shefflab/brickyard/datasets_downloaded/refgenomes_fasta/refget/data_loaders/ref-genome-analysis

python build_refgetstore.py --store-path /project/shefflab/brickyard/refget_store
