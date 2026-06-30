# PDF Pruning with a Modified Cambridge-Aachen Algorithm

This project implements a modified Cambridge-Aachen sequential recombination clustering algorithm optimized for pruning PDF (Partond Distribution Function) replica vectors. The main algorithm is implemented in the `pdf_pruning.ipynb` Jupyter notebook, which calls various utility functions from the `pruning_tools`. The files `260131_pdf_pruning.ipynb` and `260211_pdf_pruning.ipynb` are examples applied to `260131.PN.ct25alt_nx21` and `260211.PN.pq206p357_nx22` vectors.



## Overview

The clustering algorithm uses geometric-based sequential recombination to group similar PDF vectors and identify representative samples, effectively reducing redundancy in PDF replica sets. The algorithm supports multiple distance metrics (PDF dissimilarity, Euclidean, etc.) and provides comprehensive analysis and visualization tools.

For detailed mathematical information about the modified Cambridge-Aachen algorithm and its implementation, see `PDFs_and_the_modified_Cambrige-Aachen.pdf`.

## Requirements

The project requires Python 3.10+ with the following libraries:

- **numpy** ≥1.20.0 — Numerical computing
- **pandas** ≥1.3.0 — Data manipulation and analysis
- **scipy** ≥1.7.0 — Scientific computing (spatial distances, statistics)
- **plotly** ≥5.0.0 — Interactive visualizations


For development/testing:
- **jupyter** — Notebook environment
- **pytest** — Testing framework
- **black** — Code formatter
- **flake8** — Linting

## Installation

### Local Option 1: PIP (Recommended for most users)

```bash
# Clone or download the repository
cd pdf_pruning

# Install dependencies
pip install -r requirements.txt
```

### Local Option 2: CONDA (Recommended for scientific computing)

```bash
# Clone or download the repository
cd pdf_pruning

# Create environment from file
conda env create -f environment.yml

# Activate environment
conda activate pdf_pruning
```

### Online Option: Google Colab

One of the simplest ways to run the notebook is via Google Colab:

1. Open the repository on GitHub
2. Click on `pdf_pruning.ipynb` 
3. Click "Open in Colab"
4. Mount your Google Drive and upload the `pruning_tools` folder to your Drive
5. Run cells as needed

## Usage

### Running the Jupyter Notebook

```bash
jupyter notebook pdf_pruning.ipynb
```

The notebook demonstrates:
1. Loading PDF vectors from TSV files
2. Computing pairwise distances with various metrics
3. Running the Cambridge-Aachen clustering algorithm
4. Analyzing cluster quality and separation
5. Identifying and extracting representative vectors
6. Pruning redundant vectors

### Using the pruning_tools Package

The `pruning_tools` package provides modular functions for clustering, analysis, and visualization:

```python
from pruning_tools import cambridge_cluster, plot_neighbor_degree
import numpy as np

# Load your vectors
vectors = np.load('vectors.npy')

# Define a distance metric
def my_metric(v1, v2):
    return np.sum((v1 - v2) ** 2)

# Run clustering
clusters = cambridge_cluster(vectors, metric=my_metric, R=1.0)

# Visualize neighbor degree distribution
fig = plot_neighbor_degree(vectors, metric=my_metric, R_cutoff=2.0)
fig.show()
```

For detailed documentation on available functions and how to extend the package, see [pruning_tools/README.md](pruning_tools/README.md).

## Project Structure

```
pdf_pruning/
├── README.md                              # This file
├── requirements.txt                       # Python package dependencies
├── environment.yml                        # Conda environment specification
├── pdf_pruning.ipynb                      # Main Jupyter notebook
├── PDFs_and_the_modified_Cambrige-Aachen.pdf  # Algorithm documentation
└── pruning_tools/                         # Utility package
    ├── __init__.py                        # Package initialization
    ├── cambridge_algorithm.py             # Core clustering algorithm
    ├── own_metrics.py                     # Distance metrics
    ├── analysis.py                        # Analysis functions
    ├── plots.py                           # Plotting functions
    └── README.md                          # pruning_tools documentation
```

## References

- Matteo Cacciari, Gavin P. Salam, and Gregory Soyez. The anti-kt jet clustering algorithm. JHEP, 04:063, 2008. doi: 10.1088/1126-6708/2008/04/063 
- Stan Bentvelsen and Irmtraud Meyer. The Cambridge jet algorithm: Features and applications. Eur.
Phys. J. C, 4:623–629, 1998. doi: 10.1007/s100520050232
- See `PDFs_and_the_modified_Cambrige-Aachen.pdf` for detailed mathematical background

---