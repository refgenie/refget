#!/bin/bash
#SBATCH --job-name=build_digest_map
#SBATCH --output=build_digest_map_%j.log
#SBATCH --error=build_digest_map_%j.log
#SBATCH --partition=standard
#SBATCH --time=4:00:00
#SBATCH --mem=16G
#SBATCH --cpus-per-task=1
#SBATCH --account=shefflab

module load miniforge/24.3.0-py3.11

cd $HOME/code/ref-genome-analysis
source env/on-cluster.env

python src/02_build/build_digest_map.py
