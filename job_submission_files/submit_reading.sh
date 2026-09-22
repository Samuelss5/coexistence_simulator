#!/bin/bash

# Job Parameters
#SBATCH --job-name=JOB_SAMUEL
#SBATCH --output="/home/users/samuelss/coexistence_simulator/job_submission_files/reading_results/reading_output/out_%A_%a..txt"
#SBATCH --error="/home/users/samuelss/coexistence_simulator/job_submission_files/reading_results/reading_error/error_%A_%a..txt"
# Job Resources
#SBATCH --mincpus=32
#SBATCH --mem=15G
#SBATCH --time=99:00:00

echo -e "Job started at $(date)"
# Use srun to run the simulation such that the "sstat" command returns useful information for the job

cd /home/users/samuelss/
source cellfreetdd/bin/activate
cd coexistence_simulator/
srun python3 /home/users/samuelss/coexistence_simulator/snapshots_reading.py -s $SLURM_ARRAY_TASK_ID
echo -e "Job ended at $(date)"

