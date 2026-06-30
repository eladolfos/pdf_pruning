# HPCC Quick Reference Card

## Essential Commands

### Job Submission & Monitoring

```bash
# Submit a job
sbatch srun_HPCC_r_scan.sb

# Submit with parameter overrides
sbatch --time=02:00:00 --cpus-per-task=32 srun_HPCC_r_scan.sb

# Check job status
squeue -u USERNAME
squeue -j 12345678              # Specific job ID

# View detailed job info
scontrol show job 12345678

# Cancel a job
scancel 12345678

# Watch job in real-time
sstat -j 12345678 --format=AveCPU,AveRSS,MaxRSS -i 5
```

### Monitoring Output

```bash
# Stream the log (live updates)
tail -f srun_HPCC_r_scan_*.log

# Get last 50 lines
tail -50 srun_HPCC_r_scan_*.log

# View all output
cat srun_HPCC_r_scan_*.log

# Check error log
cat srun_HPCC_r_scan_*.err

# Search for specific text in output
grep "Error\|Progress" srun_HPCC_r_scan_*.log
```

### Environment Management

```bash
# List available Python modules
module avail python

# Load Python
module load Python/3.10.10

# List available LHAPDF
module avail lhapdf

# Load LHAPDF
module load LHAPDF/6.3.0

# Show currently loaded modules
module list

# Unload a module
module unload Python/3.10.10

# Create conda environment
conda env create -f environment.yml

# Activate environment
conda activate pdf_pruning

# Deactivate environment
conda deactivate

# List conda environments
conda env list

# Remove conda environment
conda env remove --name pdf_pruning
```

### File Management on HPCC

```bash
# Navigate to home directory
cd /mnt/home/USERNAME/

# Navigate to scratch (temporary, fast storage)
cd /mnt/scratch/USERNAME/

# Check disk usage
du -sh /mnt/home/USERNAME/pdf_pruning
df -h /mnt/home /mnt/scratch

# Copy results to local machine (from local terminal)
scp USERNAME@hpcc.msu.edu:/mnt/home/USERNAME/pdf_pruning/R_scan.npy .

# Upload files to HPCC
scp -r local_directory USERNAME@hpcc.msu.edu:/mnt/home/USERNAME/

# Remote file listing (from local machine)
ssh USERNAME@hpcc.msu.edu ls -lah /mnt/home/USERNAME/pdf_pruning/
```

---

## SLURM Script Customization

Common parameter adjustments in `srun_HPCC_r_scan.sb`:

| What | Change This | Value Options | Notes |
|------|-------------|----------------|-------|
| Job name | `--job-name=` | Any string | Helps identify in `squeue` |
| Cores | `--cpus-per-task=` | 8, 16, 32, 40 | More cores = faster but contended |
| Memory | `--mem=` | 8G, 16G, 32G, 64G | Increase if OOM errors |
| Time limit | `--time=` | HH:MM:SS | Increase if job times out |
| Queue | `--partition=` | standard, short, long | short = faster access, lower priority |
| Email alerts | `--mail-type=` | BEGIN,END,FAIL,REQUEUE | Receive job status emails |

---

## Common Workflows

### Quick Test Run
```bash
sbatch --time=00:10:00 --cpus-per-task=4 --mem=8G srun_HPCC_r_scan.sb
squeue -u USERNAME
tail -f srun_HPCC_r_scan_*.log
```

### Production Run (Large Dataset)
```bash
sbatch --time=02:00:00 --cpus-per-task=32 --mem=64G --partition=standard srun_HPCC_r_scan.sb
squeue -u USERNAME
# Wait for completion...
scp USERNAME@hpcc.msu.edu:/mnt/home/USERNAME/pdf_pruning/R_scan.npy .
```

### Debug Run (Interactive)
```bash
salloc -N 1 --ntasks=1 --cpus-per-task=8 --mem=16G --time=01:00:00
module load Python/3.10.10
conda activate pdf_pruning
python HPCC_r_scan.py
exit
```

### Multiple Jobs (Job Array)
```bash
# Edit srun_HPCC_r_scan.sb and add:
#SBATCH --array=1-5

# Submit once, runs 5 times in parallel
sbatch srun_HPCC_r_scan.sb
```

---

## Performance Rules of Thumb

- **Cores:** 1 core per million vectors (e.g., 1M vectors → 1 core, 50M vectors → 50 cores)
- **Memory:** ~1 MB per vector (e.g., 1M vectors → 1 GB, 100M vectors → 100 GB)
- **Time:** Start with 30 min, increase 50% for each test until job completes
- **Partition:** Use `short` for quick tests (<10 min), `standard` for normal jobs (10 min–2 hours)

---

## Troubleshooting Checklist

**Job stuck in PENDING?**
- Check resources: `sinfo` (are cores/memory available?)
- Reduce resource request: lower cores or memory
- Use `short` partition instead of `standard`

**Job times out?**
- Increase `--time` (start at 2× current estimate)
- Reduce problem size (fewer R values)
- Use more cores (faster parallelization)

**ImportError or module not found?**
- Run `module load Python/3.10.10` in script before conda
- Check `module list` to see what's loaded
- Try `conda install <missing_package>`

**Out of memory?**
- Increase `--mem` (16G → 32G → 64G)
- Reduce `--cpus-per-task` (fewer workers = less overhead)
- Check actual usage: `sstat -j <job_id>`

**Script runs locally but fails on HPCC?**
- Verify conda environment: `conda activate pdf_pruning && python -c "import pruning_tools"`
- Check file paths (use absolute paths, not relative)
- Look at error log: `cat srun_HPCC_r_scan_*.err`

---

## Useful Links

- HPCC Home: https://hpcc.msu.edu/
- HPCC Wiki: https://wiki.hpcc.msu.edu/
- SLURM Docs: https://slurm.schedmd.com/sbatch.html
- MSU IT Help: https://tech.msu.edu/
- Email Support: hpcc-support@msu.edu
