# LHAPDF Installation Fix for MSU HPCC

If you're getting the error:
```
UnavailableInvalidChannel: HTTP 404 Not Found for channel lhapdf
```

Follow this guide to resolve it.

## The Problem

LHAPDF is not available in the standard Anaconda channels, causing `conda env create` to fail. 

## Solution 1: Use Corrected environment.yml (RECOMMENDED)

The `environment.yml` has been fixed to install LHAPDF via **pip** instead of conda.

### Steps:

1. **Delete the broken environment:**
   ```bash
   conda env remove --name pdf_pruning
   ```

2. **Re-create with fixed environment.yml:**
   ```bash
   cd /mnt/home/USERNAME/pdf_pruning
   conda env create -f environment.yml
   ```

   This will now:
   - Create the base environment with conda
   - Install LHAPDF via pip (which is more reliable)

3. **Activate:**
   ```bash
   conda activate pdf_pruning
   ```

4. **Test:**
   ```bash
   python -c "import lhapdf; print('LHAPDF OK')"
   ```

## Solution 2: Load LHAPDF as an HPCC Module (Alternative)

If the pip installation doesn't work, LHAPDF may be available as a system module:

1. **Check if LHAPDF module exists:**
   ```bash
   module avail lhapdf
   ```

2. **If found, load it:**
   ```bash
   module load LHAPDF/6.3.0  # or whatever version is available
   ```

3. **Create environment WITHOUT LHAPDF:**
   ```bash
   conda env create -f environment_no_lhapdf.yml
   conda activate pdf_pruning
   ```

4. **Test:**
   ```bash
   python -c "import lhapdf; print('LHAPDF OK')"
   ```

5. **Update SLURM script** to always load the LHAPDF module:
   Edit `srun_HPCC_r_scan.sb` and uncomment:
   ```bash
   module load LHAPDF/6.3.0
   ```

## Solution 3: Install LHAPDF from Conda-Forge Directly

If you want to use conda (not pip), try installing directly from conda-forge:

```bash
conda activate pdf_pruning
conda install -c conda-forge lhapdf
```

## Solution 4: Skip LHAPDF if Not Needed

If your script doesn't use the analysis functions that require LHAPDF:

1. **Comment out the import** in `pruning_tools/analysis.py`:
   ```python
   # import lhapdf  # Optional: only needed for some analysis functions
   ```

2. **Create environment without LHAPDF:**
   ```bash
   conda env remove --name pdf_pruning
   pip install -r requirements_no_lhapdf.txt
   ```

   Or edit `environment.yml` and remove the pip lhapdf line, then:
   ```bash
   conda env create -f environment.yml
   ```

## Recommended Approach

**Use Solution 1** (already implemented):
- ✅ Most reliable on HPCC
- ✅ Pip installs LHAPDF correctly
- ✅ No need to load modules
- ✅ Works consistently

## Verify Installation

After choosing a solution, verify it works:

```bash
conda activate pdf_pruning

# Test all imports
python << 'EOF'
import numpy as np
import pandas as pd
import scipy
import plotly
print("✓ numpy, pandas, scipy, plotly OK")

try:
    import lhapdf
    print("✓ lhapdf OK")
except ImportError:
    print("⚠ lhapdf not available (may be OK if not used)")

import pruning_tools
print("✓ pruning_tools OK")

print("\nAll core dependencies installed!")
EOF
```

## If Still Failing

Contact MSU HPCC support:
- Email: hpcc-support@msu.edu
- Ask: "How to install LHAPDF Python bindings on HPCC?"

They can help with system-level LHAPDF installation.

## For Future Reference

The updated files that fix this:
- `environment.yml` — Now uses pip for LHAPDF (lines ~31-33)
- `requirements.txt` — Already had lhapdf (pip compatible)
- `srun_HPCC_r_scan.sb` — Now checks for LHAPDF availability (lines ~62-71)

---

**Status:** ✅ Ready to use with corrected environment.yml
