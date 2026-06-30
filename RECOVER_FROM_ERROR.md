# Quick Recovery from LHAPDF Error

You got this error:
```
UnavailableInvalidChannel: HTTP 404 Not Found for channel lhapdf
```

## Fix (3 steps, 2 minutes)

### Step 1: Delete the broken environment
```bash
conda env remove --name pdf_pruning
```

You'll be asked to confirm. Type `y` and press Enter.

### Step 2: Update from git (or manually update files)

The environment.yml has been fixed. Either:

**Option A: Pull from git**
```bash
cd /mnt/home/USERNAME/pdf_pruning
git pull origin main
```

**Option B: Replace environment.yml manually**
Delete the old one and use the updated version:
```bash
# The updated environment.yml now installs LHAPDF via pip (more reliable)
# It should be in your repository
```

### Step 3: Re-create the environment
```bash
cd /mnt/home/USERNAME/pdf_pruning
conda env create -f environment.yml
```

This will take ~3-5 minutes. You should see:
```
Collecting package metadata (repodata.json): done
Solving environment: done
Downloading and Extracting Packages
...
Done
```

### Step 4: Verify it works
```bash
conda activate pdf_pruning
python -c "import lhapdf; print('✓ LHAPDF OK')"
```

You should see: `✓ LHAPDF OK`

## Done! Now you can run:

```bash
sbatch srun_HPCC_r_scan.sb
```

---

## If Step 3 Still Fails

Try this alternative (skips LHAPDF):

```bash
conda env create -f environment_no_lhapdf.yml
conda activate pdf_pruning
python HPCC_r_scan.py  # Test run
sbatch srun_HPCC_r_scan.sb  # Submit job
```

This works fine for the R-scan (doesn't need LHAPDF).

---

## If You Want Full Details

See: **LHAPDF_INSTALL_FIX.md** for all solutions.

---

## Support

If still stuck:
- Email: hpcc-support@msu.edu
- Ask: "How to install LHAPDF on HPCC?"
