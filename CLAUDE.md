# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**pdf_pruning** is a Python research project that implements a modified Cambridge-Aachen sequential recombination clustering algorithm for pruning PDF (Parton Distribution Function) replica vectors used in particle physics research. The goal is to identify representative PDF vectors and remove redundant replicas while maintaining physical accuracy.

The main algorithm is implemented as a modular Python package (`pruning_tools`) with Jupyter notebooks for experimentation and analysis.

## Setup & Installation

### Using pip (recommended for development)
```bash
pip install -r requirements.txt
```

### Using conda (recommended for scientific computing)
```bash
conda env create -f environment.yml
conda activate pdf_pruning
```

Core dependencies: numpy, pandas, scipy, plotly. See `requirements.txt` for versions.

## Running & Testing

### Start Jupyter for interactive work
```bash
jupyter notebook pdf_pruning.ipynb
```

Main notebooks:
- `pdf_pruning.ipynb` — Core algorithm demonstration with all analysis steps
- `260131_pdf_pruning.ipynb`, `260211_pdf_pruning.ipynb` — Examples on specific datasets
- `CT25alt_pdf_pruning.ipynb` — Example with CT25alt data

### Run the R-scan script
```bash
python HPCC_r_scan.py
```
This script scans multiple radius values (R) to evaluate clustering behavior and find optimal parameters.

### Code quality tools
```bash
black pruning_tools/       # Format code
flake8 pruning_tools/      # Check linting
pytest pruning_tools/      # Run tests (if test files exist)
```

## Project Structure & Architecture

```
pdf_pruning/
├── pruning_tools/              # Main package with clustering algorithms and utilities
│   ├── cambridge_algorithm.py  # Core clustering: cambridge_cluster()
│   ├── own_metrics.py          # Distance metrics: pdf_dissimilarity(), euclidean_distance()
│   ├── analysis.py             # Cluster analysis: neighbor_degree_analysis(), assign_cluster_data_to_metadata()
│   ├── plots.py                # Plotly visualizations: plot_neighbor_degree(), plot_pairwise_cdf()
│   ├── scan_r_parallel.py      # Parameter scanning: scan_R_parallel()
│   └── __init__.py             # Package exports
├── pdf_pruning.ipynb           # Main algorithm demonstration
├── HPCC_r_scan.py             # Script for scanning R parameter values
├── environment.yml / requirements.txt  # Dependency specs
└── README.md                   # Full documentation
```

## Key Modules & Workflows

### Core Clustering (cambridge_algorithm.py)
- **`cambridge_cluster(vectors, metric, R, ids=None)`** — Main entry point
  - Takes N×D array of vectors, a distance metric function, and radius R
  - Returns list of cluster dicts with `cluster_label`, `vectors_in_cluster`, `cluster_vector`, `num_vectors`, `closest_vec_to_centroid_id`
  - Implements sequential recombination with merging threshold = R

### Distance Metrics (own_metrics.py)
- **`pdf_dissimilarity(u, v, mindenom=0.0001)`** — Normalized absolute difference, optimized for PDF vectors
- **`euclidean_distance(u, v)`** — Standard Euclidean distance
- **`standardized_euclidean_distance(u, v, variances)`** — Mahalanobis-like distance

### Analysis Pipeline (analysis.py)
Typical workflow:
1. **`neighbor_degree_analysis()`** — Count neighbors within distance cutoff R; shows isolated vs. hub vectors
2. **`cambridge_cluster()`** — Run clustering algorithm
3. **`assign_cluster_data_to_metadata()`** — Map clusters back to metadata (3 modes: with metric column, with metadata only, or no metadata)
4. **`get_pruned_and_discarded_vectors()`** — Separate representatives from discarded vectors
5. **`analyze_cluster_separation()`** — Compute intra/inter-cluster distances and separation ratios

### Visualization (plots.py)
- `plot_neighbor_degree()` — Bar chart + CDF of neighbor distribution (identifies isolated vs. hub vectors)
- `plot_pairwise_cdf()` — CDF of all pairwise distances; shows merge threshold impact
- `plot_cluster_separation()` — Grouped bars comparing intra vs. inter-cluster distances

### Parameter Scanning (scan_r_parallel.py)
- **`scan_R_parallel(vectors, chi2, metric, rec_crit, R_values)`** — Evaluates clustering quality across a range of R values using parallelization; useful for finding optimal radius

## Common Workflows

### Quick clustering with PDF metric
```python
from pruning_tools import cambridge_cluster, pdf_dissimilarity
import numpy as np

vectors = np.load('vectors.npy')
metric = lambda v1, v2: pdf_dissimilarity(v1, v2, mindenom=0.0001)
clusters = cambridge_cluster(vectors, metric=metric, R=1.5)
```

### Full analysis pipeline
1. Load vectors (TSV or NumPy format)
2. Call `plot_pairwise_cdf()` to inspect distance distribution and pick R cutoff
3. Call `neighbor_degree_analysis()` to identify isolated vs. hub vectors
4. Run `cambridge_cluster()` with chosen R
5. Use `assign_cluster_data_to_metadata()` to label clusters (choose mode A/B/C based on metadata availability)
6. Use `get_pruned_and_discarded_vectors()` to extract representatives
7. Call `analyze_cluster_separation()` and `plot_cluster_separation()` to assess quality

### Optimizing the R parameter
- Use `scan_R_parallel()` to evaluate multiple R values and find the optimal clustering
- Common criteria: minimizing chi2, balancing cluster count with pruning ratio, or maximizing separation ratio

## Data Formats

- **Vectors**: TSV files with headers, or NumPy .npy arrays (shape N×D)
- **Metadata**: TSV or CSV, indexed by vector ID (member_idx), with optional numeric columns for ranking (e.g., chi2f)
- **Example datasets** in subdirectories: `260131_data/`, `260211_data/`, `CT25altData/`

## Mathematical Foundation

The algorithm is a geometric-based sequential recombination inspired by the Cambridge-Aachen jet clustering algorithm from particle physics. For detailed theory:
- See `PDFs_and_the_modified_Cambrige-Aachen.pdf` in the repo root
- Algorithm merges pairs with distance < R using simple vector averaging as recombination

## MSU HPCC Deployment

For running on Michigan State University's HPCC cluster, see dedicated documentation:
- **HPCC_SETUP_GUIDE.md** — Step-by-step setup, environment configuration, job monitoring
- **HPCC_QUICK_REFERENCE.md** — Command quick reference, troubleshooting, performance tips
- **srun_HPCC_r_scan.sb** — SLURM batch script (ready to use; customize resource parameters)

**Quick start on HPCC:**
```bash
cd /mnt/home/USERNAME/pdf_pruning
conda env create -f environment.yml
conda activate pdf_pruning
sbatch srun_HPCC_r_scan.sb
squeue -u USERNAME
```

## Dependencies & Modules

All required packages are listed in `requirements.txt` and `environment.yml`.

**Core dependencies:**
- numpy, pandas, scipy, plotly (standard scientific stack)
- lhapdf (PDF handling; may require module load on HPC)

On HPCC, load modules before activating conda:
```bash
module load Python/3.10.10
# Optionally: module load LHAPDF/6.3.0
conda activate pdf_pruning
```

## Notes for Development

- **Type hints** are used throughout; check function signatures for parameter types
- **Numerical stability**: `pdf_dissimilarity()` uses `mindenom` parameter to avoid division by near-zero
- **Vector IDs**: If not provided to `cambridge_cluster()`, vectors are indexed 0..N-1
- **Clustering radius R**: Lower R → more clusters (finer granularity); higher R → fewer clusters (more merging). Use visualization and analysis functions to choose R.
- **Best vector selection**: Within each cluster, the closest vector to the centroid (by Euclidean distance) is marked as the representative, or you can override via `assign_cluster_data_to_metadata()` mode A with a metric column
- **Parallelization**: `scan_R_parallel()` uses `concurrent.futures.ProcessPoolExecutor`; metrics must be picklable (no lambdas)
- **LHAPDF**: Used in `analysis.py` for PDF handling. On HPCC, may be loaded as a module rather than pip package.
