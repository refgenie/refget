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

cd /home/ns5bc/code/ref-genome-analysis
source env/on-cluster.env

python src/05_profiling/profile_memory.py 850 5
