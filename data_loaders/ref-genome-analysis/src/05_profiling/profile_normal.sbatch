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

cd $HOME/code/ref-genome-analysis
source env/on-cluster.env

python src/05_profiling/profile_normal.py
