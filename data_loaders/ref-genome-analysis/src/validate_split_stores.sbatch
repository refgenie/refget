#!/bin/bash
#SBATCH --job-name=validate_split
#SBATCH --output=validate_split_%j.log
#SBATCH --error=validate_split_%j.log
#SBATCH --partition=standard
#SBATCH --time=2:00:00
#SBATCH --mem=16G
#SBATCH --cpus-per-task=1
#SBATCH --account=shefflab

module load miniforge/24.3.0-py3.11

cd $HOME/code/ref-genome-analysis
source env/on-cluster.env

python src/validate_split_stores.py "$@"
