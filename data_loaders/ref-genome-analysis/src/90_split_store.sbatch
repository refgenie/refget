#!/bin/bash
#SBATCH --job-name=split_store
#SBATCH --output=split_store_%j.log
#SBATCH --error=split_store_%j.log
#SBATCH --partition=standard
#SBATCH --time=4:00:00
#SBATCH --mem=16G
#SBATCH --cpus-per-task=1
#SBATCH --account=shefflab

module load miniforge/24.3.0-py3.11

cd /home/ns5bc/code/ref-genome-analysis
source env/on-cluster.env

python src/90_split_store.py
