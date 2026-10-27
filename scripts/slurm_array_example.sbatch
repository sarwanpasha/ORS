#!/bin/bash
# Example Slurm array that spreads a sharded sym search over NJOBS nodes.
# Edit the partition/account lines for your cluster, then e.g.
#   sbatch --array=0-3 scripts/slurm_array_example.sbatch d 22 6 512 4 out_d22
#SBATCH --job-name=ORS_sym
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --time=24:00:00
##SBATCH --partition=YOUR_PARTITION
##SBATCH --account=YOUR_ACCOUNT
cd "$SLURM_SUBMIT_DIR"
bash scripts/run_sharded.sh $1 $2 $3 $4 $5 $SLURM_CPUS_PER_TASK $6 ${SLURM_ARRAY_TASK_ID:-0} ${SLURM_ARRAY_TASK_COUNT:-1}
