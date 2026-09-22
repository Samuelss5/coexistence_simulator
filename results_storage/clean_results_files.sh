#!/bin/bash

# Job Parameters
#SBATCH --job-name=cleaning_snapshots_storage
# Job Resources
#SBATCH --mincpus=4
#SBATCH --mem=15G
#SBATCH --time=99:00:00

cd /home/users/samuelss/coexistence_simulator/results_storage/
srun rm -rf inr_results/*
srun rm -rf num_ues_results/*
srun rm -rf se_results/*


