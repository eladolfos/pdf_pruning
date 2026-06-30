# HPCC Documentation Index

Quick navigation guide to all HPCC-related files and resources.

## Start Here

👉 **New to HPCC?** Start with: [HPCC_SETUP_GUIDE.md](HPCC_SETUP_GUIDE.md)

👉 **Quick reference?** Use: [HPCC_QUICK_REFERENCE.md](HPCC_QUICK_REFERENCE.md)

👉 **Overview of changes?** Read: [HPCC_SUMMARY.md](HPCC_SUMMARY.md)

---

## File Guide

### Documentation Files

| File | Purpose | Audience | Read Time |
|------|---------|----------|-----------|
| **HPCC_SETUP_GUIDE.md** | Step-by-step setup, conda environment, job submission, monitoring, troubleshooting | First-time users, detailed learners | 20 min |
| **HPCC_QUICK_REFERENCE.md** | Commands, parameters, common workflows, troubleshooting checklist | Experienced users, quick lookups | 5 min |
| **HPCC_SUMMARY.md** | Overview of changes made, dependency analysis, file listing | Project leads, overview readers | 10 min |
| **HPCC_INDEX.md** | This file — navigation guide | All users | 2 min |

### SLURM Batch Scripts

| File | Purpose | When to Use |
|------|---------|------------|
| **srun_HPCC_r_scan.sb** | Standard SLURM script with full features | Most jobs (default choice) |
| **srun_HPCC_r_scan_advanced.sb** | Job arrays, custom R ranges, aggregation | Parallel parameter sweeps |

### Configuration Files

| File | What Changed | Details |
|------|-------------|---------|
| **requirements.txt** | Added `lhapdf>=6.0.0` | Needed for PDF handling in analysis |
| **environment.yml** | Added lhapdf conda package | Conda equivalent of requirements.txt |
| **CLAUDE.md** | Added HPCC deployment section | Links to guides and quick start |

---

## Common Workflows

### "I'm setting up for the first time"
1. Read: [HPCC_SETUP_GUIDE.md](HPCC_SETUP_GUIDE.md) → "Quick Start" (3 min)
2. Follow: Step-by-step setup instructions
3. Run: `sbatch srun_HPCC_r_scan.sb`
4. Monitor: Use commands from [HPCC_QUICK_REFERENCE.md](HPCC_QUICK_REFERENCE.md)

### "I've set up before, just need to submit a job"
1. Look up: [HPCC_QUICK_REFERENCE.md](HPCC_QUICK_REFERENCE.md) → "Essential Commands"
2. Edit: `srun_HPCC_r_scan.sb` (adjust resources if needed)
3. Run: `sbatch srun_HPCC_r_scan.sb`

### "Something went wrong"
1. Check: [HPCC_QUICK_REFERENCE.md](HPCC_QUICK_REFERENCE.md) → "Troubleshooting Checklist"
2. If not resolved: [HPCC_SETUP_GUIDE.md](HPCC_SETUP_GUIDE.md) → "Troubleshooting"
3. Check logs: `cat srun_HPCC_r_scan_<job_id>.err`

### "I need to run parameter sweeps in parallel"
1. Read: [srun_HPCC_r_scan_advanced.sb](srun_HPCC_r_scan_advanced.sb) → "CONFIGURATION 1"
2. Uncomment the job array lines
3. Modify the task logic for your R ranges
4. Run: `sbatch srun_HPCC_r_scan_advanced.sb`

### "I want to understand the setup"
1. Read: [HPCC_SUMMARY.md](HPCC_SUMMARY.md) → "What Changed" + "Dependency Analysis"
2. Review: Updated files (requirements.txt, environment.yml)
3. Understand: SLURM scripts (see comments)

---

## Quick Reference: Key Commands

```bash
# Submit a job
sbatch srun_HPCC_r_scan.sb

# Check job status
squeue -u USERNAME

# Monitor live output
tail -f srun_HPCC_r_scan_*.log

# Cancel a job
scancel <job_id>

# Activate environment
conda activate pdf_pruning

# Set up environment (first time)
conda env create -f environment.yml
```

See [HPCC_QUICK_REFERENCE.md](HPCC_QUICK_REFERENCE.md) for more commands.

---

## SLURM Parameters Cheat Sheet

Edit these in `srun_HPCC_r_scan.sb`:

| What | Parameter | Recommended Values | Notes |
|------|-----------|-------------------|-------|
| Job name | `--job-name=` | `pdf_r_scan_v1` | For job identification |
| Cores | `--cpus-per-task=` | 8, 16, 32, 40 | More = faster, more contention |
| Memory | `--mem=` | 8G, 16G, 32G, 64G | Increase if OOM errors |
| Time | `--time=` | HH:MM:SS | Increase if timeout |
| Queue | `--partition=` | standard, short | short = faster access |

Quick command:
```bash
sbatch --cpus-per-task=32 --mem=32G --time=02:00:00 srun_HPCC_r_scan.sb
```

See [HPCC_SETUP_GUIDE.md](HPCC_SETUP_GUIDE.md) → "Resource Guidelines" for detailed recommendations.

---

## Dependency Summary

**Required packages added to support HPCC deployment:**

- `lhapdf>=6.0.0` — PDF (Parton Distribution Function) handling

See [HPCC_SUMMARY.md](HPCC_SUMMARY.md) → "Dependency Analysis" for complete table.

---

## File Size Summary

```
HPCC Documentation:
├── HPCC_INDEX.md                 (this file)
├── HPCC_SUMMARY.md               (7.0 KB)
├── HPCC_SETUP_GUIDE.md           (8.8 KB)
├── HPCC_QUICK_REFERENCE.md       (4.9 KB)
├── srun_HPCC_r_scan.sb           (6.4 KB)  ← Use this
└── srun_HPCC_r_scan_advanced.sb  (6.6 KB)  ← Advanced only

Configuration:
├── requirements.txt              (449 B)
└── environment.yml               (983 B)

Main code:
├── HPCC_r_scan.py               (1.5 KB)
├── pruning_tools/                (various)
└── pdf_pruning.ipynb             (large)
```

---

## Links & Resources

### Documentation
- [HPCC_SETUP_GUIDE.md](HPCC_SETUP_GUIDE.md) — Comprehensive guide
- [HPCC_QUICK_REFERENCE.md](HPCC_QUICK_REFERENCE.md) — Quick commands
- [CLAUDE.md](CLAUDE.md) — General project guide

### MSU HPCC
- [HPCC Wiki](https://wiki.hpcc.msu.edu/) — Official documentation
- [SLURM Documentation](https://slurm.schedmd.com/sbatch.html) — Scheduler docs
- [MSU IT Support](https://tech.msu.edu/) — Help center

### Email Support
- hpcc-support@msu.edu — MSU HPCC team

---

## Navigation Tips

- **Ctrl+F** (Find) works in all markdown files for quick searching
- Click any file link above to jump to that section
- SLURM scripts have detailed comments — read them!
- When in doubt, check [HPCC_QUICK_REFERENCE.md](HPCC_QUICK_REFERENCE.md) first

---

**Last Updated:** 2026-06-30  
**Status:** Ready for deployment  
**Questions?** See [HPCC_SETUP_GUIDE.md](HPCC_SETUP_GUIDE.md) → Troubleshooting
