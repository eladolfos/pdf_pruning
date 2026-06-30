# HPCC Setup Summary

This document summarizes all changes made to support running pdf_pruning on MSU HPCC.

## What Changed

### 1. **Updated Dependencies**

#### requirements.txt
- Added `lhapdf>=6.0.0` to support PDF handling
- See file for complete list of all dependencies

#### environment.yml
- Updated to include `lhapdf::lhapdf>=6.0.0` from conda-forge
- Added note about loading LHAPDF via module system on HPCC

**Why:** Analysis code imports `lhapdf` for PDF replica handling. This was missing from the original dependencies.

### 2. **SLURM Batch Scripts**

#### srun_HPCC_r_scan.sb (PRIMARY SCRIPT)
**Use this for most runs.** Fully featured SLURM script with:
- Resource allocation (cores, memory, time, partition)
- Module loading (Python, LHAPDF)
- Conda environment setup
- Error checking and logging
- Detailed comments explaining each section
- Optional email notifications

**Quick start:**
```bash
sbatch srun_HPCC_r_scan.sb
```

**Customizable parameters:**
- `--cpus-per-task` : Cores (8, 16, 32, 40)
- `--mem` : Memory (8G, 16G, 32G, 64G)
- `--time` : Walltime (HH:MM:SS)
- `--partition` : Queue (standard, short, long)

#### srun_HPCC_r_scan_advanced.sb (OPTIONAL)
For advanced use cases:
- Job arrays (parallel parameter sweeps)
- Different R ranges per job
- Result aggregation
- Customizable per-task logic

**Use when:** You want to split the R-scan into multiple parallel jobs.

### 3. **Documentation**

#### HPCC_SETUP_GUIDE.md
Comprehensive step-by-step guide covering:
- Quick start (4 steps)
- Detailed setup (conda/venv/LHAPDF)
- SLURM script configuration
- Resource allocation guidelines
- Job monitoring and result retrieval
- Advanced usage (job arrays, scratch filesystem, Jupyter)
- Troubleshooting common issues
- Performance tips and HPCC resources

**Use this:** First-time setup or when you need detailed explanations.

#### HPCC_QUICK_REFERENCE.md
Quick reference card with:
- Essential SLURM commands (submit, monitor, cancel)
- Environment management (modules, conda)
- File operations (upload, download, cleanup)
- Common workflows (quick test, production run, debug)
- Performance rules of thumb
- Troubleshooting checklist
- Useful links

**Use this:** When you need a quick command or remember something you saw before.

### 4. **Updated CLAUDE.md**
Added section on MSU HPCC deployment with:
- Cross-references to detailed guides
- Quick start command
- Dependency notes
- LHAPDF loading instructions

## File Listing

### New Files
```
├── srun_HPCC_r_scan.sb              ← PRIMARY: Ready-to-use SLURM script
├── srun_HPCC_r_scan_advanced.sb     ← OPTIONAL: Advanced job array script
├── HPCC_SETUP_GUIDE.md              ← Comprehensive setup & usage guide
├── HPCC_QUICK_REFERENCE.md          ← Command quick reference
└── HPCC_SUMMARY.md                  ← This file
```

### Updated Files
```
├── requirements.txt                 ← Added lhapdf>=6.0.0
├── environment.yml                  ← Added lhapdf conda package
└── CLAUDE.md                        ← Added HPCC section
```

## Dependency Analysis

All imports found in the codebase:

| Module | Imported From | Required | Added? |
|--------|---------------|----------|--------|
| numpy | pruning_tools, analysis, cambridge, metrics, plots | ✓ | No (already present) |
| pandas | HPCC_r_scan, analysis, plots | ✓ | No (already present) |
| scipy | analysis, metrics, plots | ✓ | No (already present) |
| plotly | plots | ✓ | No (already present) |
| **lhapdf** | **analysis** | ✓ | **YES** |
| concurrent.futures | scan_r_parallel | ✓ (stdlib) | No (built-in) |
| pathlib | HPCC_r_scan | ✓ (stdlib) | No (built-in) |
| os, time, typing | various | ✓ (stdlib) | No (built-in) |

**New dependency identified:** `lhapdf` (Parton Distribution Functions library)

## How to Use These Files

### First Time on HPCC

1. **Read:** `HPCC_SETUP_GUIDE.md` (sections "Quick Start" and "Detailed Setup")
2. **Run:** Commands from the guide to set up conda environment
3. **Submit:** `sbatch srun_HPCC_r_scan.sb`
4. **Monitor:** Commands from `HPCC_QUICK_REFERENCE.md`

### Subsequent Runs

1. **Quick ref:** `HPCC_QUICK_REFERENCE.md` (Essential Commands section)
2. **Customize:** Edit resource parameters in `srun_HPCC_r_scan.sb`
3. **Submit:** `sbatch srun_HPCC_r_scan.sb`

### Troubleshooting

1. **Check:** `HPCC_QUICK_REFERENCE.md` (Troubleshooting Checklist)
2. **Read logs:** `cat srun_HPCC_r_scan_<job_id>.err`
3. **Detailed help:** `HPCC_SETUP_GUIDE.md` (Troubleshooting section)

### Advanced Use Cases

1. **Parallel scans:** `srun_HPCC_r_scan_advanced.sb` with job arrays
2. **Job monitoring:** `HPCC_QUICK_REFERENCE.md` (Monitoring Output section)
3. **Performance:** `HPCC_QUICK_REFERENCE.md` (Performance Rules of Thumb)

## Quick Start (TL;DR)

```bash
# 1. SSH to HPCC
ssh USERNAME@hpcc.msu.edu

# 2. Navigate to project
cd /mnt/home/USERNAME/pdf_pruning

# 3. Set up environment (first time only)
conda env create -f environment.yml

# 4. Activate environment
conda activate pdf_pruning

# 5. Verify it works locally (quick test)
python HPCC_r_scan.py  # Takes ~1-2 minutes on single core

# 6. Edit SLURM script if needed
# vim srun_HPCC_r_scan.sb
# Adjust: --cpus-per-task, --mem, --time, --partition

# 7. Submit batch job
sbatch srun_HPCC_r_scan.sb

# 8. Monitor
squeue -u USERNAME
tail -f srun_HPCC_r_scan_*.log

# 9. Retrieve results (from local machine)
scp USERNAME@hpcc.msu.edu:/mnt/home/USERNAME/pdf_pruning/R_scan.npy .
```

## Common Customizations

### More cores (faster)
```bash
sbatch --cpus-per-task=32 srun_HPCC_r_scan.sb
```

### More memory
```bash
sbatch --mem=32G srun_HPCC_r_scan.sb
```

### Longer time
```bash
sbatch --time=02:00:00 srun_HPCC_r_scan.sb
```

### Different queue (faster allocation)
```bash
sbatch --partition=short srun_HPCC_r_scan.sb
```

### All at once
```bash
sbatch --cpus-per-task=32 --mem=32G --time=02:00:00 --partition=standard srun_HPCC_r_scan.sb
```

## Verification Checklist

- [x] requirements.txt includes lhapdf
- [x] environment.yml includes lhapdf
- [x] SLURM script handles module loading
- [x] SLURM script activates conda environment
- [x] SLURM script exports OMP_NUM_THREADS
- [x] All imports analyzed (no missing dependencies)
- [x] Documentation written and linked

## Support Resources

- **HPCC Documentation:** https://wiki.hpcc.msu.edu/
- **SLURM Documentation:** https://slurm.schedmd.com/sbatch.html
- **MSU IT Support:** https://tech.msu.edu/
- **Email:** hpcc-support@msu.edu

## Notes for Future Development

- **LHAPDF Location:** On HPCC, LHAPDF may be available as a module (`module load LHAPDF/...`) or via conda. The SLURM script checks both.
- **ProcessPoolExecutor:** `scan_R_parallel()` uses multiprocessing; the SLURM script sets `OMP_NUM_THREADS` to prevent oversubscription.
- **Metric Pickling:** Metrics must be picklable (no lambdas) for parallel scanning.
- **Scratch Space:** For very large datasets, consider using `/mnt/scratch` (temporary but faster).

---

**Date Created:** 2026-06-30
**Author:** Claude Code
**Status:** Ready for deployment
