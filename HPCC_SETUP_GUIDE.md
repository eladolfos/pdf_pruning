# MSU HPCC Setup & Execution Guide

This guide explains how to set up and run the pdf_pruning project on Michigan State University's HPCC cluster.

## Quick Start

1. **Clone/upload the repository to HPCC:**
   ```bash
   # On HPCC login node
   cd /mnt/home/USERNAME/
   # Clone from GitHub or upload files
   ```

2. **Create the conda environment:**
   ```bash
   cd pdf_pruning
   conda env create -f environment.yml
   conda activate pdf_pruning
   ```

3. **Submit the job:**
   ```bash
   sbatch srun_HPCC_r_scan.sb
   ```

4. **Monitor the job:**
   ```bash
   squeue -u USERNAME
   tail -f srun_HPCC_r_scan_<job_id>.log
   ```

---

## Detailed Setup Instructions

### Step 1: Access HPCC

```bash
# SSH to login node (from your local machine)
ssh USERNAME@hpcc.msu.edu
```

The HPCC environment uses SLURM for job scheduling. You interact with compute nodes through login nodes.

### Step 2: Prepare the Project

```bash
# Navigate to your home directory on HPCC
cd /mnt/home/USERNAME/

# Option A: Clone from GitHub
git clone https://github.com/your-username/pdf_pruning.git
cd pdf_pruning

# Option B: Upload files from local machine (from your local terminal)
# scp -r /path/to/pdf_pruning USERNAME@hpcc.msu.edu:/mnt/home/USERNAME/
```

### Step 3: Set Up Python Environment

#### Option 1: Conda (Recommended)

Conda is pre-installed on HPCC. Create the environment:

```bash
cd /mnt/home/USERNAME/pdf_pruning
conda env create -f environment.yml
```

Activate it:
```bash
conda activate pdf_pruning
```

Verify installation:
```bash
python -c "import numpy, pandas, scipy, plotly, lhapdf; print('All imports OK')"
```

#### Option 2: Pip + Virtualenv

If you prefer not to use conda:

```bash
cd /mnt/home/USERNAME/pdf_pruning
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Then edit `srun_HPCC_r_scan.sb` to use the venv option (lines ~115-123).

#### Troubleshooting LHAPDF Installation

If you get an error like:
```
UnavailableInvalidChannel: HTTP 404 Not Found for channel lhapdf
```

**See: LHAPDF_INSTALL_FIX.md** for detailed solutions.

Quick fix:
1. Delete broken environment: `conda env remove --name pdf_pruning`
2. Recreate with updated `environment.yml`: `conda env create -f environment.yml`
   (Now uses pip for LHAPDF, which is more reliable)

**Alternative options:**

**Option 1: Load LHAPDF as a module** (if available on HPCC)
```bash
module load LHAPDF/6.3.0
conda env create -f environment_no_lhapdf.yml
```

Check if available:
```bash
module avail lhapdf
```

**Option 2: Skip LHAPDF entirely**
Use the no-LHAPDF environment (works for clustering/visualization):
```bash
conda env create -f environment_no_lhapdf.yml
conda activate pdf_pruning
```

**Option 3: Contact HPCC support**
- Email: hpcc-support@msu.edu
- Ask about LHAPDF Python bindings installation

### Step 4: Configure the SLURM Script

Edit `srun_HPCC_r_scan.sb` to match your needs:

```bash
# Key parameters to adjust:

# Line ~20: Job name and output
#SBATCH --job-name=pdf_pruning_r_scan_v1

# Line ~26-28: Resource allocation
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16        # ← Adjust number of cores (8, 16, 32, 40)
#SBATCH --mem=16G                 # ← Adjust memory (16G, 32G, 64G)

# Line ~35: Walltime (wall-clock limit)
#SBATCH --time=00:30:00           # ← Adjust: 00:30:00, 01:00:00, etc.

# Line ~39: Partition
#SBATCH --partition=standard       # ← standard, short, long, gpu, etc.
```

**Resource Guidelines:**

| Use Case | Cores | Memory | Time | Partition |
|----------|-------|--------|------|-----------|
| Quick test (10 R values) | 8 | 8G | 10:00 | short |
| Small scan (50 R values) | 16 | 16G | 30:00 | standard |
| Medium scan (100 R values) | 32 | 32G | 60:00 | standard |
| Large scan (200+ R values) | 40 | 64G | 120:00 | long |

To see available partitions:
```bash
sinfo
```

### Step 5: Submit the Job

```bash
cd /mnt/home/USERNAME/pdf_pruning

# Standard submission
sbatch srun_HPCC_r_scan.sb

# Or with overrides:
sbatch --time=01:00:00 --cpus-per-task=32 srun_HPCC_r_scan.sb
```

You'll get a job ID (e.g., `12345678`).

### Step 6: Monitor Job Progress

```bash
# Check job status
squeue -u USERNAME
squeue -j 12345678               # Check specific job

# Watch log output (updates in real-time)
tail -f srun_HPCC_r_scan_12345678.log

# See more details
scontrol show job 12345678
```

### Step 7: Retrieve Results

Once the job completes:

```bash
# List output files
ls -lah *.npy *.log *.err

# Download results to local machine (from your local terminal)
scp USERNAME@hpcc.msu.edu:/mnt/home/USERNAME/pdf_pruning/R_scan.npy .

# Or copy entire results directory
scp -r USERNAME@hpcc.msu.edu:/mnt/home/USERNAME/pdf_pruning/results/ .
```

---

## Advanced Usage

### Running Multiple Jobs in Parallel

Create job arrays to scan different parameter sets in parallel:

```bash
# In srun_HPCC_r_scan.sb, add:
#SBATCH --array=1-3              # Run 3 jobs in parallel

# Then modify HPCC_r_scan.py to use SLURM_ARRAY_TASK_ID:
# E.g., different datasets or R ranges per job
```

### Using /mnt/scratch for Large Data

If your vectors are large, use the scratch filesystem (faster, temporary):

```bash
# In the SLURM script:
cd /mnt/scratch/USERNAME/pdf_pruning

# Copy input data
cp -r /mnt/home/USERNAME/pdf_pruning/CT25altData .

# Run script
python HPCC_r_scan.py

# Copy results back
cp R_scan.npy /mnt/home/USERNAME/pdf_pruning/
```

⚠️ **Note:** Scratch space is temporary and may be purged. Always copy important results back to `/mnt/home`.

### Interactive Jobs (for Debugging)

For interactive debugging, use `salloc`:

```bash
# Request interactive resources
salloc -N 1 --ntasks=1 --cpus-per-task=8 --mem=16G --time=01:00:00

# Once allocated, activate environment and run
conda activate pdf_pruning
python HPCC_r_scan.py

# Release resources when done
exit
```

### Running Jupyter Notebooks on HPCC

To run notebooks interactively:

```bash
# Request interactive resources with more memory
salloc -N 1 --ntasks=1 --cpus-per-task=8 --mem=32G --time=04:00:00

# Start Jupyter
conda activate pdf_pruning
jupyter notebook --ip=0.0.0.0 --no-browser --port=8888

# From another terminal (local machine), SSH tunnel:
ssh -L 8888:localhost:8888 USERNAME@hpcc.msu.edu

# Then open browser to http://localhost:8888
```

---

## Troubleshooting

### Job Fails Immediately

Check the error log:
```bash
cat srun_HPCC_r_scan_<job_id>.err
```

Common issues:
- **Module not found:** Load a Python module explicitly in the script
- **Conda not initialized:** Run `conda init bash` first
- **File path issues:** Use absolute paths (/mnt/home/...) not relative paths

### Out of Memory (OOM)

Increase memory in the SLURM script:
```bash
#SBATCH --mem=32G  # Increase from 16G
```

Or reduce the number of R values scanned at once.

### Job Times Out

Increase walltime:
```bash
#SBATCH --time=02:00:00  # Increase from 00:30:00
```

Or reduce the problem size (fewer R values).

### ImportError for lhapdf

If LHAPDF module isn't available:

1. Try loading via module:
   ```bash
   module avail lhapdf
   module load LHAPDF/6.3.0
   ```

2. Or install in conda:
   ```bash
   conda install -c conda-forge lhapdf
   ```

3. Or temporarily comment out the import in `pruning_tools/analysis.py` if it's not used.

### ProcessPoolExecutor Issues

If you see warnings about multiprocessing:
- Ensure `scan_R_parallel` uses a picklable metric (not a lambda)
- Check that your conda environment is properly activated in the script
- Try reducing `--cpus-per-task` if you have too many workers

---

## Performance Tips

1. **Use `-OMP_NUM_THREADS`:** Set in SLURM script to prevent thread oversubscription
   ```bash
   export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK
   ```

2. **Use scratch for I/O-heavy workloads:** Scratch is faster than /mnt/home for large reads/writes

3. **Profile before large runs:** Test with small data first
   ```bash
   # Quick test with 10 R values
   python -c "from pruning_tools import scan_R_parallel; ..."
   ```

4. **Monitor resource usage:**
   ```bash
   # In the log output, check if CPU/memory usage is high
   sstat -j <job_id> --format=AveCPU,AveRSS,AveVMSize
   ```

---

## Useful HPCC Resources

- **HPCC Documentation:** https://wiki.hpcc.msu.edu/
- **SLURM Docs:** https://slurm.schedmd.com/sbatch.html
- **SLURM Quick Reference:** https://slurm.schedmd.com/sbatch.html#SECTION_OPTIONS
- **MSU IT Support:** https://tech.msu.edu/

---

## Example Workflow

```bash
# 1. SSH to HPCC
ssh USERNAME@hpcc.msu.edu

# 2. Set up
cd /mnt/home/USERNAME/pdf_pruning
conda activate pdf_pruning

# 3. Test locally with small data
python HPCC_r_scan.py  # (will run serially, quick)

# 4. Edit SLURM script for full run
# Increase --cpus-per-task, --time, --mem as needed

# 5. Submit batch job
sbatch srun_HPCC_r_scan.sb

# 6. Monitor
squeue -u USERNAME
tail -f srun_HPCC_r_scan_*.log

# 7. Check results when done
ls -lh R_scan.npy
python -c "import numpy as np; data = np.load('R_scan.npy'); print(data.keys())"

# 8. Copy back to local machine
# (from local terminal)
scp USERNAME@hpcc.msu.edu:/mnt/home/USERNAME/pdf_pruning/R_scan.npy .
```

---

## Questions?

- Check the HPCC wiki: https://wiki.hpcc.msu.edu/
- Email HPCC support: hpcc-support@msu.edu
- Post on the MSU HPCC Slack (if available)
