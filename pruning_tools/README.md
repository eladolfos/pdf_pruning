# pruning_tools Package Documentation

This package provides a complete toolkit for PDF vector clustering, analysis, and visualization using a modified Cambridge-Aachen sequential recombination algorithm.

## Table of Contents

1. [Package Overview](#package-overview)
2. [Module Documentation](#module-documentation)
   - [cambridge_algorithm](#cambridge_algorithm)
   - [own_metrics](#own_metrics)
   - [analysis](#analysis)
   - [plots](#plots)
3. [Quick Start](#quick-start)
4. [Adding New Functions](#adding-new-functions)
5. [Modifying Existing Functions](#modifying-existing-functions)

## Package Overview

The `pruning_tools` package is organized into four main modules:

| Module | Purpose |
|--------|---------|
| `cambridge_algorithm.py` | Core clustering algorithm implementation |
| `own_metrics.py` | Distance metrics for vector comparison |
| `analysis.py` | Cluster analysis and statistics functions |
| `plots.py` | Interactive visualization functions |

All public functions are exported in `__init__.py` for convenient importing.

## Module Documentation

### cambridge_algorithm

**File:** `cambridge_algorithm.py`

#### `cambridge_cluster()`

Core clustering function implementing the modified Cambridge-Aachen sequential recombination algorithm.

**Signature:**
```python
def cambridge_cluster(
    vectors,
    metric: Callable,
    R: float = 1.0,
    ids=None,
) -> list[dict]
```

**Parameters:**
- `vectors` (array-like, shape (N, d)): Input vectors to cluster
- `metric` (callable): Distance function `metric(v1, v2) -> float`. Must be symmetric and non-negative
- `R` (float, default=1.0): Clustering radius. Pairs with distance/R ≥ 1 are not merged
- `ids` (array-like of int, optional): Original identifiers for each vector. Defaults to 0..N-1

**Returns:**
List of cluster dictionaries with keys:
- `cluster_label` (int): Unique cluster identifier
- `vectors_in_cluster` (list[int]): IDs of vectors in this cluster
- `cluster_vector` (np.ndarray): Weighted-average centroid of the cluster
- `num_vectors` (int): Number of vectors in the cluster
- `closest_vec_to_centroid_id` (int): ID of the member vector nearest to the centroid (by Euclidean distance)
- `dist_of_closest_to_centroid` (float): Euclidean distance from that vector to the centroid

**Examples:**

Euclidean distance:
```python
from pruning_tools import cambridge_cluster
import numpy as np

vectors = np.random.randn(100, 50)
clusters = cambridge_cluster(
    vectors, 
    metric=lambda v1, v2: np.sum((v1 - v2) ** 2),
    R=1.0
)
```

Cosine distance with custom metric:
```python
def cosine_dist(v1, v2):
    sim = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-10)
    return (1 - sim) ** 2

clusters = cambridge_cluster(vectors, metric=cosine_dist, R=0.5)
```

PDF dissimilarity metric:
```python
from pruning_tools import pdf_dissimilarity

clusters = cambridge_cluster(
    vectors,
    metric=lambda v1, v2: pdf_dissimilarity(v1, v2, mindenom=0.0001),
    R=1.5
)
```

**Algorithm Details:**
- Uses sequential recombination with beam distance = 1 (geometric p=0)
- Merges pairs with distance < R
- Finalizes particles when nearest neighbor distance ≥ R
- Recombination uses simple averaging of merged vectors

---

### own_metrics

**File:** `own_metrics.py`

Distance metrics optimized for comparing PDF replica vectors and general vector spaces.

#### `pdf_dissimilarity()`

Calculate normalized absolute difference between two PDF vectors.

**Signature:**
```python
def pdf_dissimilarity(
    u: np.ndarray, 
    v: np.ndarray, 
    mindenom: float = 0.0001
) -> float
```

**Parameters:**
- `u, v` (np.ndarray): Vectors to compare, shape (n_features,)
- `mindenom` (float, default=1e-4): Minimum denominator threshold for numerical stability

**Formula:**
```
D(u, v) = sum(2 * |u(x) - v(x)| / (|u(x)| + |v(x)|))
```

**Returns:** Float distance value

**Notes:**
- Components where `|u(x)| + |v(x)| <= mindenom` are masked
- Focuses on physically significant regions of the PDF space
- Sensitive to relative changes in vector components

**Example:**
```python
from pruning_tools import pdf_dissimilarity
import numpy as np

u = np.array([1.0, 2.0, 3.0])
v = np.array([1.1, 2.1, 3.1])
distance = pdf_dissimilarity(u, v)
```

#### `euclidean_distance()`

Calculate Euclidean distance between vectors.

**Signature:**
```python
def euclidean_distance(u: np.ndarray, v: np.ndarray) -> float
```

**Returns:** Float Euclidean distance

#### `standardized_euclidean_distance()`

Calculate standardized Euclidean distance (Mahalanobis-like).

**Signature:**
```python
def standardized_euclidean_distance(
    u: np.ndarray, 
    v: np.ndarray, 
    variances: np.ndarray
) -> float
```

**Parameters:**
- `u, v` (np.ndarray): Vectors to compare
- `variances` (np.ndarray): Feature variances for standardization

**Returns:** Float standardized distance

#### `get_clustering_dist_sq()`

Calculate squared distance for clustering with multiple metric options.

**Signature:**
```python
def get_clustering_dist_sq(
    v1, 
    v2, 
    metric: str, 
    mindenom: float
) -> float
```

**Parameters:**
- `metric` (str): One of `"pdf_dissimilarity"` or `"euclidean"`
- `mindenom` (float): Passed to pdf_dissimilarity if metric is selected

**Returns:** Float squared distance

---

### analysis

**File:** `analysis.py`

Functions for analyzing cluster quality, pruning decisions, and generating summary statistics.

#### `neighbor_degree_analysis()`

Count neighbors within distance cutoff for each vector.

**Signature:**
```python
def neighbor_degree_analysis(
    data_input,
    metric: Callable,
    R_cutoff: float = 2.0,
    print_summary: bool = True,
) -> dict
```

**Parameters:**
- `data_input`: NumPy array or pandas DataFrame with vectors
- `metric` (callable): Distance metric function
- `R_cutoff` (float): Distance threshold for neighbor inclusion
- `print_summary` (bool): Print statistics summary to console

**Returns:** Dictionary with keys:
- `counts`: np.ndarray of neighbor counts per vector
- `isolated`: int, number of vectors with 0 neighbors
- `hubs`: int, number of vectors with above-average neighbors
- `pairs_check`: int, count of close pairs
- `mean`, `max`: Average and maximum neighbor counts

**Use Case:** Understand which vectors are isolated (will always be solo clusters) vs. hubs (likely to merge with others).

#### `assign_cluster_data_to_metadata()`

Maps cluster statistics back to metadata table, or synthesizes a minimal metadata table from cluster results when no metadata is available. Supports three operating modes.

**Signature:**
```python
def assign_cluster_data_to_metadata(
    final_jets: list[dict],
    metadata_df: Optional[pd.DataFrame] = None,
    metric_column: Optional[str] = None,
    best_mode: str = "min",
    cluster_best_field: str = "closest_vec_to_centroid_id",
) -> pd.DataFrame
```

**Three Operating Modes:**

**Mode A: WITH metadata + metric_column**
Full ranking by numeric column. metric_column must name a column in metadata_df.

Added columns:
- `cluster_label`: Cluster ID
- `cluster_size`: Number of vectors in cluster
- `cluster_best_idx`: Index of best vector in cluster
- `cluster_best_{metric_column}`: Metric value of best vector
- `cluster_avg_{metric_column}`: Average metric across cluster

**Mode B: WITH metadata, NO metric_column**
metadata_df contains only names/labels/non-numeric information. Uses cluster_best_field to identify the best vector.

Added columns:
- `cluster_label`: Cluster ID
- `cluster_size`: Number of vectors in cluster
- `cluster_best_idx`: Index of best vector
- `is_best`: Boolean flag for best vector
- `{cluster_best_field}`: The best vector ID
- Any extra scalar fields from cluster dicts

**Mode C: WITHOUT metadata**
Synthesizes table from cluster dicts alone, one row per original vector id.

Produced columns:
- `{cluster_best_field}`: The best vector ID
- `cluster_label`: Cluster ID
- `cluster_size`: Number of vectors in cluster
- `cluster_best_idx`: Index of best vector
- `is_best`: Boolean flag for best vector
- Any extra scalar fields from cluster dicts

**Parameters:**
- `final_jets` (list[dict]): Output of `cambridge_cluster()`
- `metadata_df` (pd.DataFrame, optional): Original metadata table. Index must match vector IDs. Pass None for Mode C.
- `metric_column` (str, optional): Column name to rank vectors in clusters (e.g., "chi2f", "loss"). Required for Mode A.
- `best_mode` (str): "min" (default) or "max" — how to select best vector in each cluster. Only used in Mode A.
- `cluster_best_field` (str): Key in cluster dict holding pre-computed best vector id. Defaults to "closest_vec_to_centroid_id".

**Examples:**
```python
from pruning_tools import assign_cluster_data_to_metadata
import pandas as pd

# Mode A — metadata with numeric ranking column
metadata = pd.read_csv('metadata.csv', index_col=0)
labeled = assign_cluster_data_to_metadata(
    final_jets=clusters,
    metadata_df=metadata,
    metric_column="chi2f",
    best_mode="min"
)

# Mode B — metadata with only names/labels
labeled = assign_cluster_data_to_metadata(
    final_jets=clusters,
    metadata_df=metadata,
    cluster_best_field="closest_vec_to_centroid_id"
)

# Mode C — no metadata at all
labeled = assign_cluster_data_to_metadata(
    final_jets=clusters,
    cluster_best_field="closest_vec_to_centroid_id"
)
```

#### `get_pruned_and_discarded_vectors()`

Separates original vectors into 'Representatives' and 'Discarded' sets using the shared positional index as the key.

**Signature:**
```python
def get_pruned_and_discarded_vectors(
    vectors_df: pd.DataFrame,
    labeled_metadata: pd.DataFrame,
    metric_column: Optional[str] = None,
) -> tuple[pd.DataFrame, pd.DataFrame]
```

**Two Operating Modes:**

**Mode A — Ranked by metadata metric column (e.g. "chi2f")**
Pass the same metric_column that was given to `assign_cluster_data_to_metadata()`. The pruned set will have that column's best value attached for downstream use.

**Mode B/C — Best vector from cluster result field or no metadata**
Pass metric_column=None (the default). The representative is identified purely via cluster_best_idx. If labeled_metadata contains a "dist_of_closest_to_centroid" column it is attached to the pruned set automatically; any other extra scalar cluster columns are attached too.

**Parameters:**
- `vectors_df` (pd.DataFrame): Full vector DataFrame. Index must match labeled_metadata's index.
- `labeled_metadata` (pd.DataFrame): Output of `assign_cluster_data_to_metadata()`. Must contain 'cluster_best_idx'.
- `metric_column` (str, optional): The metric column used in `assign_cluster_data_to_metadata()` (e.g. "chi2f"). Pass None for Mode B/C. Defaults to None.

**Returns:** Tuple of two DataFrames:
1. `pruned_df`: One representative vector per cluster
   - Mode A: has metric_column attached
   - Mode B/C: has any extra scalar cluster columns attached (e.g. dist_of_closest_to_centroid)
2. `discarded_df`: All redundant vectors removed during pruning

**Output:** Prints summary statistics showing original count, kept count, discarded count, and reduction percentage.

**Examples:**
```python
from pruning_tools import get_pruned_and_discarded_vectors
import pandas as pd

# Mode A — was ranked by chi2f
pruned, discarded = get_pruned_and_discarded_vectors(
    vectors_df=vdf,
    labeled_metadata=labeled,
    metric_column="chi2f",
)

# Mode B/C — best chosen by cluster result field or no metadata
pruned, discarded = get_pruned_and_discarded_vectors(
    vectors_df=vdf,
    labeled_metadata=labeled,
)
```

#### `analyze_cluster_separation()`

Calculate cluster quality metrics (internal tightness and external separation).

**Signature:**
```python
def analyze_cluster_separation(
    final_jets: list[dict],
    original_vectors_df: pd.DataFrame,
) -> pd.DataFrame
```

**Parameters:**
- `final_jets` (list[dict]): Output of `cambridge_cluster()`
- `original_vectors_df` (pd.DataFrame): Original vector DataFrame (indexed by vector ID)

**Returns:** DataFrame with columns:
- `Cluster`: Cluster label
- `Size`: Number of vectors in cluster
- `Avg_Intra_Dist`: Average distance from members to cluster center (lower = tighter)
- `Avg_Inter_Dist`: Average distance from this center to other centers (higher = more separated)
- `Separation_Ratio`: Inter_Dist / (Intra_Dist + ε) — higher is better

**Interpretation:**
- High `Avg_Intra_Dist` → cluster is spread out internally
- Low `Avg_Inter_Dist` → cluster is close to other clusters (overlapping)
- High `Separation_Ratio` → well-separated, cohesive cluster

---

### plots

**File:** `plots.py`

Interactive Plotly-based visualization functions for cluster analysis.

#### `plot_neighbor_degree()`

Bar chart of neighbor degree distribution with CDF overlay.

**Signature:**
```python
def plot_neighbor_degree(
    data_input,
    metric: Callable,
    R_cutoff: float = 2.0,
    metric_name: str = "Custom Metric",
    title_suffix: str = "",
    color_isolated: str = "steelblue",
    color_hubs: str = "crimson",
    template: str = "plotly_white",
    height: int = 550,
    width: int = 850,
    print_statistics: bool = True,
) -> go.Figure
```

**Parameters:**
- `data_input`: NumPy array or pandas DataFrame
- `metric` (callable): Distance metric function
- `R_cutoff` (float): Distance threshold for counting neighbors
- `metric_name` (str): Name for display in title
- `title_suffix` (str): Additional subtitle text
- `color_isolated`, `color_hubs` (str): Colors for visualization
- `template` (str): Plotly template (e.g., "plotly_white", "plotly_dark")
- `height`, `width` (int): Figure dimensions in pixels
- `print_statistics` (bool): Print summary statistics

**Returns:** `plotly.graph_objects.Figure` object

**Visualization:**
- X-axis: Number of neighbors (degree k)
- Y-axis: Count of vectors with exactly k neighbors
- Color coding:
  - **Steelblue** (k=0): Isolated vectors (solo clusters)
  - **Crimson** (k > mean): Hub vectors (drivers of merging)
  - **Gray** (k ≤ mean): Regular vectors
- Overlay: CDF curve showing cumulative fraction of vectors
- Annotations: Mean degree line, isolated count label, statistics box

#### `plot_cluster_separation()`

Grouped bar chart comparing intra- vs inter-cluster distances.

**Signature:**
```python
def plot_cluster_separation(summary_df: pd.DataFrame) -> go.Figure
```

**Parameters:**
- `summary_df` (pd.DataFrame): Output of `analyze_cluster_separation()`

**Returns:** `plotly.graph_objects.Figure` object

**Visualization:**
- X-axis: Cluster labels
- Y-axis: Average distance
- Red bars: Intra-cluster distance (tightness, lower is better)
- Blue bars: Inter-cluster distance (separation, higher is better)

#### `plot_pairwise_cdf()`

Cumulative distribution function of pairwise distances with cutoff threshold.

**Signature:**
```python
def plot_pairwise_cdf(
    data_input,
    metric: Callable,
    R_cutoff: float = 2.0,
    metric_name: str = "Custom Metric",
    title_suffix: str = "",
    color_below: str = "crimson",
    color_above: str = "steelblue",
    color_cutoff: str = "darkred",
    color_median: str = "gray",
    template: str = "plotly_white",
    height: int = 550,
    width: int = 850,
    print_statistics: bool = True,
) -> go.Figure
```

**Parameters:**
- `data_input`: NumPy array or pandas DataFrame
- `metric` (callable): Distance metric function
- `R_cutoff` (float): Distance threshold to visualize
- `metric_name`, `title_suffix` (str): Labels and annotation
- `color_below`, `color_above` (str): Colors for regions below and above cutoff
- `color_cutoff`, `color_median` (str): Colors for threshold and median lines
- `template`, `height`, `width`, `print_statistics`: As in `plot_neighbor_degree()`

**Returns:** `plotly.graph_objects.Figure` object

**Visualization:**
- Curve: Empirical CDF of all pairwise distances
- Below-cutoff region (crimson): Pairs that will merge (d ≤ R_cutoff)
- Above-cutoff region (steelblue): Pairs that won't merge (d > R_cutoff)
- Vertical lines: R_cutoff threshold and median distance
- Statistics box: Number of pairs, mean/median/std distances

---

## Quick Start

### Basic Workflow

```python
import numpy as np
import pandas as pd
from pruning_tools import (
    cambridge_cluster, 
    pdf_dissimilarity,
    assign_cluster_data_to_metadata,
    get_pruned_and_discarded_vectors,
    neighbor_degree_analysis,
    plot_neighbor_degree,
    plot_pairwise_cdf,
    analyze_cluster_separation,
    plot_cluster_separation,
)

# 1. Load vectors and metadata
vectors = np.load('vectors.npy')
metadata = pd.read_csv('metadata.csv', index_col=0)

# 2. Define distance metric
metric = lambda v1, v2: pdf_dissimilarity(v1, v2, mindenom=0.0001)

# 3. Visualize pairwise distances
fig_cdf = plot_pairwise_cdf(vectors, metric, R_cutoff=1.5)
fig_cdf.show()

# 4. Analyze neighbor distribution
neighbor_stats = neighbor_degree_analysis(vectors, metric, R_cutoff=1.5)

# 5. Run clustering
clusters = cambridge_cluster(vectors, metric=metric, R=1.5)

# 6. Assign cluster data to metadata (Mode A: with metric column)
metadata_labeled = assign_cluster_data_to_metadata(
    final_jets=clusters,
    metadata_df=metadata,
    metric_column="chi2f",
    best_mode="min"
)

# 7. Separate pruned vs discarded vectors
pruned_df, discarded_df = get_pruned_and_discarded_vectors(
    vectors_df=pd.DataFrame(vectors), 
    labeled_metadata=metadata_labeled, 
    metric_column="chi2f"
)

# 8. Analyze cluster quality
summary = analyze_cluster_separation(clusters, pd.DataFrame(vectors))
fig_sep = plot_cluster_separation(summary)
fig_sep.show()
```

---

## Adding New Functions

### Guidelines

1. **Location**: Place the function in the module that best matches its purpose:
   - Metrics → `own_metrics.py`
   - Clustering → `cambridge_algorithm.py`
   - Analysis → `analysis.py`
   - Visualization → `plots.py`

2. **Naming**: Use clear, verb-noun naming:
   - Analysis: `analyze_*`, `calculate_*`, `compute_*`
   - Metrics: `*_distance`, `*_metric`
   - Plots: `plot_*`

3. **Documentation**: Include docstrings following the NumPy convention:
   ```python
   def my_function(param1, param2: str) -> dict:
       """
       One-line summary.
       
       Longer description if needed.
       
       Parameters
       ----------
       param1 : array-like
           Description of param1
       param2 : str
           Description of param2
       
       Returns
       -------
       dict
           Keys:
           - key1 : type — description
           - key2 : type — description
       """
   ```

4. **Type Hints**: Always include type hints for parameters and return values.

5. **Error Handling**: Validate inputs and raise meaningful errors:
   ```python
   if not isinstance(data, (np.ndarray, pd.DataFrame)):
       raise TypeError("data must be ndarray or DataFrame")
   ```

### Example: Adding a New Metric

**File:** `own_metrics.py`

```python
def manhattan_distance(u: np.ndarray, v: np.ndarray) -> float:
    """
    Calculate Manhattan (L1) distance between vectors.
    
    Parameters
    ----------
    u, v : np.ndarray
        Vectors to compare
    
    Returns
    -------
    float
        Manhattan distance
    """
    return float(np.sum(np.abs(u - v)))
```

Then export in `__init__.py`:
```python
from .own_metrics import manhattan_distance
__all__ = [..., "manhattan_distance"]
```

### Example: Adding a New Analysis Function

**File:** `analysis.py`

```python
def calculate_cluster_sizes(final_jets: list[dict]) -> np.ndarray:
    """
    Extract cluster sizes from clustering results.
    
    Parameters
    ----------
    final_jets : list[dict]
        Output of cambridge_cluster()
    
    Returns
    -------
    np.ndarray
        Array of cluster sizes
    """
    return np.array([jet["num_vectors"] for jet in final_jets])
```

Then export in `__init__.py`.

---

## Modifying Existing Functions

### Safe Modifications

1. **Adding Optional Parameters** (backward compatible):
   ```python
   # Before
   def my_func(data, threshold):
       pass
   
   # After — old code still works
   def my_func(data, threshold, verbose: bool = False):
       pass
   ```

2. **Improving Documentation**: Update docstrings without changing behavior.

3. **Bug Fixes**: Fix bugs that violate documented behavior. Document the fix in commit message.

### Breaking Changes

If you must change function signature or return format:

1. **Deprecate Old Version**: Keep old function but mark as deprecated:
   ```python
   import warnings
   
   def old_function(data):
       warnings.warn(
           "old_function is deprecated, use new_function instead",
           DeprecationWarning,
           stacklevel=2
       )
       return new_function(data)
   ```

2. **Version Bump**: Increment package version (follow semantic versioning).

3. **Update** `__all__` in `__init__.py` to reflect changes.

### Testing Changes

Before committing modifications:

```python
# Test in isolated script or notebook
from pruning_tools import my_modified_function
import numpy as np

# Test with sample data
test_data = np.random.randn(100, 50)
result = my_modified_function(test_data)

# Verify output format and values
assert isinstance(result, expected_type)
assert result.shape == expected_shape
```

---

## Best Practices

1. **Keep Functions Focused**: Each function should do one thing well.

2. **Avoid Side Effects**: Functions should not modify global state or input parameters unexpectedly.

3. **Document Parameters Clearly**: Include units, valid ranges, and expected shapes.

4. **Handle Edge Cases**: Empty arrays, single vectors, NaN values, etc.

5. **Use Type Hints**: Help users and enable IDE autocomplete.

6. **Test Your Code**: Verify with different input sizes and types.

7. **Follow Naming Conventions**: Match existing style in the codebase.

---

## References

- Cambridge-Aachen sequential recombination algorithm
- PDF replica analysis in particle physics
- Plotly documentation: https://plotly.com/python/
- SciPy spatial distances: https://docs.scipy.org/doc/scipy/reference/spatial.distance.html

