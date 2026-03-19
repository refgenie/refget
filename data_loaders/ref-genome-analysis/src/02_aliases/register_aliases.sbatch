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

cd $HOME/code/ref-genome-analysis
source env/on-cluster.env

python src/02_aliases/register_ncbi_aliases.py
