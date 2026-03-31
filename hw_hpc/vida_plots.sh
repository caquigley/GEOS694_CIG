#!/bin/bash
#SBATCH --ntasks=1
#SBATCH --tasks-per-node=1
#SBATCH --partition=debug
#SBATCH --time=01:00:00
#SBATCH --job-name="Vida_plot.%j"
#SBATCH --array=0-1
#SBATCH --output=%j_%a.out

module purge
module load slurm

ulimit -l unlimited

eval "$(conda shell.bash hook)"
conda activate GEOS694
python vida_plots.py iasp91 300 250 30 5.8 0.05
