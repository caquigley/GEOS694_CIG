#!/bin/bash
#SBATCH --partition=debug
#SBATCH --ntasks=2
#SBATCH --tasks-per-node=1
#SBATCH --job-name="helloworld!"
#SBATCH --time=00:00:05
#SBATCH --output=%j_%x.out
srun echo "Hello"

srun echo $SLURM_JOB_NODELIST

srun echo $SLURM_CPUS_ON_NODE

srun sleep 10

srun echo "World!"
