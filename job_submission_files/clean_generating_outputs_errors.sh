#!/bin/bash

# Job Parameters
#SBATCH --job-name=JOB_SAMUEL
##SBATCH --output="/home/users/samuelss/coexistence_simulator/job_submission_files/generation_output/out_%A_%a..txt"
##SBATCH --error="/home/users/samuelss/coexistence_simulator/job_submission_files/generation_error/error_%A_%a..txt"
# Job Resources
#SBATCH --mincpus=4
#SBATCH --mem=15G
#SBATCH --time=99:00:00


cd /home/users/samuelss/coexistence_simulator/job_submission_files/generation_results/
srun rm -rf generation_output/*
srun rm -rf generation_error/*



