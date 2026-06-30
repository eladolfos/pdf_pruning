import pandas as pd
import numpy as np
from scipy.spatial.distance import cdist, squareform, pdist
from typing import Callable, Optional, Union, Tuple, List, Dict
import lhapdf
import os



def neighbor_degree_analysis(
    data_input,
    metric: Callable,
    R_cutoff: float = 2.0,
    print_summary: bool = True,
) -> dict:
    """
    For each vector, count how many other vectors lie within distance R_cutoff.
    This is the 'degree' of each vector in the R-ball graph.

    Returns a dict with:
        counts      : np.ndarray (N,) — neighbor count per vector
        isolated    : int — vectors with 0 neighbors (will stay as solo clusters)
        hubs        : int — vectors with above-average neighbors
        pairs_check : int — should equal n_pairs_below_cutoff from your CDF
    """
    # ── prepare data (same as your plot function) ─────────────────────────
    if isinstance(data_input, pd.DataFrame):
        drop = [c for c in ["VID", "id", "ID", "vector_ID", "cluster_label", "idx"]
                if c in data_input.columns]
        X = data_input.drop(columns=drop).select_dtypes(include=[np.number]).values
    else:
        X = np.asarray(data_input, dtype=np.float64)

    N = len(X)

    # ── full distance matrix ───────────────────────────────────────────────
    # squareform(pdist(...)) is O(N²) memory — fine up to ~50k vectors.
    # For larger N, switch to the chunked version below.
    D = squareform(pdist(X, metric=metric))
    np.fill_diagonal(D, np.inf)            # don't count self as a neighbor

    counts = np.sum(D <= R_cutoff, axis=1).astype(int)

    # ── statistics ────────────────────────────────────────────────────────
    isolated   = int(np.sum(counts == 0))
    hubs       = int(np.sum(counts > counts.mean()))
    pairs_check = int(counts.sum() // 2)   # must equal CDF count

    if print_summary:
        sep = "─" * 52
        print(sep)
        print(f"  Neighbor degree analysis  (R = {R_cutoff})")
        print(sep)
        print(f"  Vectors (N)              : {N}")
        print()
        print(f"  Isolated  (0 neighbors)  : {isolated}")
        print(f"  → These will ALWAYS form solo clusters, regardless of R.")
        print()
        print(f"  With >= 1 neighbor       : {N - isolated}")
        print(f"  → These are candidates for merging.")
        print()
        print(f"  Min neighbors            : {counts.min()}")
        print(f"  Max neighbors            : {counts.max()}  ← hub size")
        print(f"  Mean neighbors           : {counts.mean():.2f}")
        print(f"  Median neighbors         : {np.median(counts):.1f}")
        print()
        print(f"  Vectors above mean       : {hubs}  ← potential cluster cores")
        print()
        print(f"  Pairs check (sum/2)      : {pairs_check}")
        print(f"  → Should match n_pairs_below_cutoff from plot_pairwise_cdf.")
        print()
        # Predict cluster range
        # Lower bound: all connected vectors collapse into 1 cluster per component
        # Upper bound: each vector keeps its own cluster (no merging)
        lower = isolated + hubs  # rough: one cluster per hub + all isolated
        print(f"  Predicted clusters (rough estimate)")
        print(f"  → Lower bound (aggressive): {isolated} isolated + {hubs} hubs"
              f" = ~{isolated + hubs}")
        print(f"  → Upper bound              = N = {N}  (no merging at all)")
        print(sep)

    return {
        "counts": counts,
        "isolated": isolated,
        "hubs": hubs,
        "pairs_check": pairs_check,
        "mean": counts.mean(),
        "max": counts.max(),
    }




def assign_cluster_data_to_metadata(
    final_jets: list[dict],
    metadata_df: Optional[pd.DataFrame] = None,
    metric_column: Optional[str] = None,
    best_mode: str = "min",
    cluster_best_field: str = "closest_vec_to_centroid_id",
) -> pd.DataFrame:
    """
    Maps cluster statistics back to a metadata table, or synthesises a
    minimal metadata table from the cluster results when no metadata is
    available.

    Three operating modes
    ---------------------
    A) WITH metadata + metric_column
        Full behaviour. metric_column must name a numeric column in
        metadata_df. The "best" vector in each cluster is selected by
        that column (lowest if best_mode="min", highest if best_mode="max").
        Extra columns added:
            cluster_label
            cluster_size
            cluster_best_idx
            cluster_best_<metric_column>
            cluster_avg_<metric_column>

    B) WITH metadata, NO metric_column
        metadata_df contains only names / labels / non-numeric information
        and has no column suitable for ranking. cluster_best_field is used
        instead to identify the best vector (same logic as mode C).
        Extra columns added:
            cluster_label
            cluster_size
            cluster_best_idx
            is_best
            <cluster_best_field>
            any extra scalar fields found in the cluster dicts

    C) WITHOUT metadata (metadata_df is None)
        A synthetic table is built from the cluster dicts alone, one row
        per original vector id. cluster_best_field names the key in each
        cluster dict whose value is the pre-computed best id.
        Columns produced:
            <cluster_best_field>
            cluster_label
            cluster_size
            cluster_best_idx
            is_best
            any extra scalar fields found in the cluster dicts

    Parameters
    ----------
    final_jets : list[dict]
        Output of cambridge_cluster. Each dict must contain at least:
            cluster_label          : int
            vectors_in_cluster     : list[int]
            num_vectors            : int
        Modes B and C additionally require:
            <cluster_best_field>   : int  (pre-computed best id)

    metadata_df : pd.DataFrame, optional
        Original metadata table whose integer index matches the ids inside
        vectors_in_cluster. Pass None for mode C.

    metric_column : str, optional
        Column in metadata_df used to rank vectors within each cluster.
        Required for mode A; omit (or pass None) for modes B and C.

    best_mode : str
        "min" → lowest  metric value is best  (default).
        "max" → highest metric value is best.
        Only used in mode A.

    cluster_best_field : str
        Key in each cluster dict that holds the pre-computed best vector id.
        Used in modes B and C. Defaults to "closest_vec_to_centroid_id".

    Returns
    -------
    pd.DataFrame  — see mode descriptions above.

    Examples
    --------
    # Mode A — metadata with a numeric ranking column
    result = assign_cluster_data_to_metadata(
        final_jets=clusters,
        metadata_df=df,           # df has a "chi2f" column
        metric_column="chi2f",
        best_mode="min",
    )

    # Mode B — metadata with only names / labels, no numeric column
    result = assign_cluster_data_to_metadata(
        final_jets=clusters,
        metadata_df=df,           # df has only "name", "category", etc.
        cluster_best_field="closest_vec_to_centroid_id",
    )

    # Mode C — no metadata at all
    result = assign_cluster_data_to_metadata(
        final_jets=clusters,
        cluster_best_field="closest_vec_to_centroid_id",
    )
    """
    # ---------------------------------------------------------------------- #
    # Validation                                                               #
    # ---------------------------------------------------------------------- #
    if best_mode not in ("min", "max"):
        raise ValueError(f"best_mode must be 'min' or 'max', got '{best_mode}'")

    if metadata_df is not None and metric_column is not None:
        if metric_column not in metadata_df.columns:
            raise ValueError(
                f"metric_column '{metric_column}' not found in metadata_df. "
                f"Available columns: {list(metadata_df.columns)}"
            )

    # ---------------------------------------------------------------------- #
    # Shared helper: extra scalar fields present in cluster dicts             #
    # (e.g. dist_of_closest_to_centroid) — surfaced in modes B and C         #
    # ---------------------------------------------------------------------- #
    standard_keys = {
        "cluster_label", "vectors_in_cluster", "cluster_vector", "num_vectors",
    }

    def _extra_numeric_keys(jets: list[dict]) -> list[str]:
        if not jets:
            return []
        return [
            k for k, v in jets[0].items()
            if k not in standard_keys
            and k != cluster_best_field
            and np.isscalar(v)
            and not isinstance(v, str)
        ]

    def _validate_cluster_best_field(jets: list[dict]) -> None:
        if jets and cluster_best_field not in jets[0]:
            raise ValueError(
                f"cluster_best_field '{cluster_best_field}' not found in "
                f"cluster dicts. Available keys: {list(jets[0].keys())}"
            )

    # ---------------------------------------------------------------------- #
    # Shared helper: build per-member rows using cluster_best_field           #
    # Used by modes B and C                                                   #
    # ---------------------------------------------------------------------- #
    def _build_cluster_rows(jets: list[dict]) -> dict[int, dict]:
        _validate_cluster_best_field(jets)
        extra_keys = _extra_numeric_keys(jets)
        rows: dict[int, dict] = {}

        for jet in jets:
            members: list[int] = jet["vectors_in_cluster"]
            best_idx: int      = jet.get(cluster_best_field)
            label: int         = jet["cluster_label"]
            size: int          = jet["num_vectors"]
            extra_vals         = {k: jet.get(k) for k in extra_keys}

            for idx in members:
                rows[idx] = {
                    cluster_best_field: best_idx,
                    "cluster_label":    label,
                    "cluster_size":     size,
                    "cluster_best_idx": best_idx,
                    "is_best":          (idx == best_idx),
                    **extra_vals,
                }
        return rows

    # ---------------------------------------------------------------------- #
    # Mode A: WITH metadata AND metric_column                                  #
    # ---------------------------------------------------------------------- #
    if metadata_df is not None and metric_column is not None:
        metric_series: pd.Series = metadata_df[metric_column]
        selector = min if best_mode == "min" else max
        records: dict[int, dict] = {}

        for jet in final_jets:
            members: list[int]  = jet["vectors_in_cluster"]
            valid               = [i for i in members if i in metric_series.index]
            member_metrics      = metric_series.loc[valid].to_dict()

            if not member_metrics:
                cluster_info = {
                    "cluster_label":                 jet["cluster_label"],
                    "cluster_size":                  jet["num_vectors"],
                    "cluster_best_idx":              None,
                    f"cluster_best_{metric_column}": float("nan"),
                    f"cluster_avg_{metric_column}":  float("nan"),
                }
            else:
                best_idx = selector(member_metrics, key=member_metrics.get)
                avg_val  = float(np.mean(list(member_metrics.values())))
                cluster_info = {
                    "cluster_label":                 jet["cluster_label"],
                    "cluster_size":                  jet["num_vectors"],
                    "cluster_best_idx":              best_idx,
                    f"cluster_best_{metric_column}": member_metrics[best_idx],
                    f"cluster_avg_{metric_column}":  avg_val,
                }

            for idx in members:
                records[idx] = cluster_info

        lookup_df = pd.DataFrame.from_dict(records, orient="index")
        lookup_df.index.name = metadata_df.index.name
        return metadata_df.join(lookup_df, how="left")

    # ---------------------------------------------------------------------- #
    # Mode B: WITH metadata, NO metric_column                                  #
    # ---------------------------------------------------------------------- #
    if metadata_df is not None and metric_column is None:
        rows = _build_cluster_rows(final_jets)
        lookup_df = pd.DataFrame.from_dict(rows, orient="index")
        lookup_df.index.name = metadata_df.index.name
        return metadata_df.join(lookup_df, how="left")

    # ---------------------------------------------------------------------- #
    # Mode C: WITHOUT metadata                                                 #
    # ---------------------------------------------------------------------- #
    rows = _build_cluster_rows(final_jets)
    result_df = pd.DataFrame.from_dict(rows, orient="index")
    result_df.index.name = "vector_id"
    result_df.sort_index(inplace=True)
    return result_df

import numpy as np
import pandas as pd
from typing import Optional


def get_pruned_and_discarded_vectors(
    vectors_df: pd.DataFrame,
    labeled_metadata: pd.DataFrame,
    metric_column: Optional[str] = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Separates the original vectors into 'Representatives' and 'Discarded'
    sets, using the shared positional index as the key.

    Works in two modes depending on what was used in
    assign_cluster_data_to_metadata():

    Mode A — ranked by a metadata metric column (e.g. "chi2f")
        Pass the same metric_column that was given to
        assign_cluster_data_to_metadata(). The pruned set will have that
        column's best value attached for downstream use, and the summary
        will report it by name.

    Mode B/C — best vector from cluster result field (e.g.
        "closest_vec_to_centroid_id") or no metadata at all.
        Pass metric_column=None (the default). The representative is
        identified purely via cluster_best_idx. If labeled_metadata
        contains a "dist_of_closest_to_centroid" column it is attached
        to the pruned set automatically; any other extra scalar cluster
        columns are attached too.

    Parameters
    ----------
    vectors_df : pd.DataFrame
        Full DataFrame of vectors. Its index must match
        labeled_metadata's index.

    labeled_metadata : pd.DataFrame
        Output of assign_cluster_data_to_metadata(). Must contain
        'cluster_best_idx'. In mode A it should also contain
        'cluster_best_<metric_column>'.

    metric_column : str, optional
        The metric column used when calling
        assign_cluster_data_to_metadata() (e.g. "chi2f").
        Pass None when no metadata metric was used (modes B/C).
        Defaults to None.

    Returns
    -------
    pruned_df : pd.DataFrame
        One representative vector per cluster.
        In mode A: has metric_column attached.
        In mode B/C: has any extra scalar cluster columns attached
        (e.g. dist_of_closest_to_centroid).

    discarded_df : pd.DataFrame
        All redundant vectors removed during pruning.

    Examples
    --------
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
    """
    if "cluster_best_idx" not in labeled_metadata.columns:
        raise ValueError(
            "'cluster_best_idx' not found in labeled_metadata. "
            "Make sure you pass the output of assign_cluster_data_to_metadata()."
        )

    # ------------------------------------------------------------------ #
    # 1. Identify representatives and split                               #
    # ------------------------------------------------------------------ #
    representative_idx = (
        labeled_metadata["cluster_best_idx"].dropna().astype(int).unique()
    )

    is_representative = vectors_df.index.isin(representative_idx)
    pruned_df    = vectors_df[ is_representative].copy()
    discarded_df = vectors_df[~is_representative].copy()

    # ------------------------------------------------------------------ #
    # 2. Attach extra columns to the pruned set                           #
    # ------------------------------------------------------------------ #

    # Columns we never want to forward onto vectors_df
    _skip = {"cluster_label", "cluster_size", "cluster_best_idx", "is_best"}

    if metric_column is not None:
        # Mode A: attach the best metric value from the labeled metadata
        metric_col_name = f"cluster_best_{metric_column}"
        if metric_col_name in labeled_metadata.columns:
            best_metric = (
                labeled_metadata[["cluster_best_idx", metric_col_name]]
                .drop_duplicates(subset="cluster_best_idx")
                .set_index("cluster_best_idx")
                .rename(columns={metric_col_name: metric_column})
            )
            pruned_df = pruned_df.join(best_metric, how="left")
        summary_label = metric_column

    else:
        # Mode B/C: attach any extra scalar cluster columns that are not
        # standard bookkeeping fields and not already in vectors_df.
        extra_cols = [
            c for c in labeled_metadata.columns
            if c not in _skip
            and c not in vectors_df.columns
        ]
        if extra_cols:
            # One row per representative is enough; drop_duplicates on
            # cluster_best_idx keeps the canonical value.
            extra_df = (
                labeled_metadata[["cluster_best_idx"] + extra_cols]
                .drop_duplicates(subset="cluster_best_idx")
                .set_index("cluster_best_idx")
            )
            pruned_df = pruned_df.join(extra_df, how="left")
        summary_label = "cluster_best_idx"

    # ------------------------------------------------------------------ #
    # 3. Summary                                                          #
    # ------------------------------------------------------------------ #
    print(f"--- Pruning Summary (best by: {summary_label}) ---")
    print(f"Total Original : {len(vectors_df)}")
    print(f"Kept (Best)    : {len(pruned_df)}")
    print(f"Discarded      : {len(discarded_df)}")
    print(f"Reduction      : {len(discarded_df) / len(vectors_df) * 100:.1f}%")

    return pruned_df, discarded_df

def get_pruned_and_discarded_metadata(
    labeled_metadata: pd.DataFrame,
    metric_column: Optional[str] = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Separates the original metadata into 'Representatives' and 'Discarded'
    sets, using cluster_best_idx to identify which rows are representatives.

    Works in two modes depending on what was used in
    assign_cluster_data_to_metadata():

    Mode A — ranked by a metadata metric column (e.g. "chi2f")
        Pass the same metric_column that was given to
        assign_cluster_data_to_metadata(). The pruned set will retain
        that column for downstream use, and the summary will report it
        by name.

    Mode B/C — best vector from cluster result field (e.g.
        "closest_vec_to_centroid_id") or no metadata at all.
        Pass metric_column=None (the default). The representative is
        identified purely via cluster_best_idx.

    Parameters
    ----------
    labeled_metadata : pd.DataFrame
        Output of assign_cluster_data_to_metadata(). Must contain
        'cluster_best_idx'. In mode A it should also contain
        'cluster_best_<metric_column>'.

    metric_column : str, optional
        The metric column used when calling
        assign_cluster_data_to_metadata() (e.g. "chi2f").
        Pass None when no metadata metric was used (modes B/C).
        Defaults to None.

    Returns
    -------
    pruned_metadata : pd.DataFrame
        One representative metadata row per cluster.
        All cluster bookkeeping columns are retained.

    discarded_metadata : pd.DataFrame
        All redundant metadata rows removed during pruning.

    Examples
    --------
    # Mode A — was ranked by chi2f
    pruned_meta, discarded_meta = get_pruned_and_discarded_metadata(
        labeled_metadata=labeled,
        metric_column="chi2f",
    )

    # Mode B/C — best chosen by cluster result field or no metadata
    pruned_meta, discarded_meta = get_pruned_and_discarded_metadata(
        labeled_metadata=labeled,
    )
    """
    if "cluster_best_idx" not in labeled_metadata.columns:
        raise ValueError(
            "'cluster_best_idx' not found in labeled_metadata. "
            "Make sure you pass the output of assign_cluster_data_to_metadata()."
        )

    # ------------------------------------------------------------------ #
    # 1. Identify representatives and split                               #
    # ------------------------------------------------------------------ #
    representative_idx = (
        labeled_metadata["cluster_best_idx"].dropna().astype(int).unique()
    )

    is_representative = labeled_metadata.index.isin(representative_idx)
    pruned_metadata    = labeled_metadata[ is_representative].copy()
    discarded_metadata = labeled_metadata[~is_representative].copy()

    # ------------------------------------------------------------------ #
    # 2. Summary                                                          #
    # ------------------------------------------------------------------ #
    if metric_column is not None:
        summary_label = metric_column
    else:
        summary_label = "cluster_best_idx"

    print(f"--- Metadata Pruning Summary (best by: {summary_label}) ---")
    print(f"Total Original : {len(labeled_metadata)}")
    print(f"Kept (Best)    : {len(pruned_metadata)}")
    print(f"Discarded      : {len(discarded_metadata)}")
    print(f"Reduction      : {len(discarded_metadata) / len(labeled_metadata) * 100:.1f}%")

    return pruned_metadata, discarded_metadata




def analyze_cluster_separation(
    final_jets: list[dict],
    original_vectors_df: pd.DataFrame,
    metric: Union[str, Callable] = "euclidean",
) -> pd.DataFrame:
    """
    Calculates average internal distance (Intra) and
    distance between cluster centers (Inter).

    Args:
        final_jets           (list[dict])  : Output of cambridge_cluster.
                                             Each dict must have:
                                               - cluster_label      : int
                                               - vectors_in_cluster : list of ints (row indices)
                                               - cluster_vector     : np.ndarray
                                               - num_vectors        : int
        original_vectors_df  (pd.DataFrame): Full vector DataFrame. Its integer index
                                             must match the ids in vectors_in_cluster.
        metric               (str or callable) : Distance metric to use for both intra- and
                                             inter-cluster distance calculations.
                                             
                                             If str: metric name recognized by scipy.spatial.distance.cdist
                                             Options: "euclidean" (default), "cosine", "manhattan",
                                             "chebyshev", "minkowski", etc.
                                             
                                             If callable: custom distance function with signature
                                             func(u: np.ndarray, v: np.ndarray) -> float
                                             The function receives two 1-D arrays and must return
                                             a scalar distance value.

    Returns:
        pd.DataFrame with columns:
            - Cluster          : cluster label
            - Size             : number of vectors in cluster
            - Avg_Intra_Dist   : mean distance from members to their cluster center
            - Avg_Inter_Dist   : mean distance from this center to all other centers
            - Separation_Ratio : Avg_Inter_Dist / (Avg_Intra_Dist + ε)

    Examples:
        # Default euclidean metric
        summary = analyze_cluster_separation(final_jets, vectors_df)

        # Using cosine similarity (good for normalized vectors)
        summary = analyze_cluster_separation(
            final_jets, vectors_df, metric="cosine"
        )

        # Using custom metric function
        def pdf_dissimilarity(u, v, mindenom=0.0001):
            abs_u, abs_v = np.abs(u), np.abs(v)
            denom = abs_u + abs_v
            mask = denom > mindenom
            if not np.any(mask):
                return 0.0
            return float(np.sum(2 * np.abs(u[mask] - v[mask]) / denom[mask]))
        
        summary = analyze_cluster_separation(
            final_jets, vectors_df, metric=pdf_dissimilarity
        )
    """
    intra_distances = []
    cluster_centers = []
    labels          = []

    for jet in final_jets:
        center     = np.array(jet["cluster_vector"])
        member_idx = jet["vectors_in_cluster"]

        # Retrieve member rows directly by positional index — no id column needed
        member_vectors = original_vectors_df.loc[member_idx].values

        if len(member_vectors) > 1:
            # Use the same metric for intra-cluster distances
            if isinstance(metric, str) and metric == "euclidean":
                # Optimize euclidean: use fast norm calculation
                dists = np.linalg.norm(member_vectors - center, axis=1)
            else:
                # For other metrics (string or callable), use cdist with single center
                dists = cdist([center], member_vectors, metric=metric)[0]
            
            avg_intra = float(np.mean(dists))
        else:
            avg_intra = 0.0  # single-member clusters have no internal spread

        intra_distances.append(avg_intra)
        cluster_centers.append(center)
        labels.append(jet["cluster_label"])

    # Inter: pairwise distances between all cluster centers
    centers_matrix    = np.array(cluster_centers)
    inter_dist_matrix = cdist(centers_matrix, centers_matrix, metric=metric)

    # For each cluster: mean distance to every *other* center (exclude self on diagonal)
    np.fill_diagonal(inter_dist_matrix, np.nan)
    avg_inter = np.nanmean(inter_dist_matrix, axis=1).tolist()

    summary_df = pd.DataFrame({
        "Cluster":          labels,
        "Size":             [j["num_vectors"] for j in final_jets],
        "Avg_Intra_Dist":   intra_distances,
        "Avg_Inter_Dist":   avg_inter,
        "Separation_Ratio": np.array(avg_inter) / (np.array(intra_distances) + 1e-9),
    })

    return summary_df



def load_pdfs_from_metadata(
    pruned_metadata: pd.DataFrame,
    discarded_metadata: pd.DataFrame,
    pdf_set_name: str,
    pdf_folder: str = ".",
    member_column: Optional[str] = None,
    verbose: bool = True,
) -> Tuple[Dict[int, lhapdf.PDF], Dict[int, lhapdf.PDF]]:
    """
    Loads LHAPDF PDF sets based on metadata indices.
    
    Simple and flexible: provide the PDF set name, folder location, and 
    optionally a column with member indices. If no column specified, uses 
    the DataFrame index as member numbers.
    
    Parameters
    ----------
    pruned_metadata : pd.DataFrame
        Metadata of representative/best PDFs.
    
    discarded_metadata : pd.DataFrame
        Metadata of discarded/redundant PDFs.
    
    pdf_set_name : str
        Name of the PDF set (e.g., "pq125a").
        LHAPDF will look for files like pq125a_0001.dat, pq125a_0002.dat, etc.
    
    pdf_folder : str, default="."
        Path to the folder containing PDF grid files.
        Example: "./pq125a" or "/path/to/pdf/folder"
    
    member_column : str, optional
        Name of column in metadata containing member indices.
        If None, uses the DataFrame index as member numbers.
        Useful if your metadata has a specific column tracking which PDF it came from.
    
    verbose : bool, default=True
        Print loading progress and summary information.
    
    Returns
    -------
    pruned_pdfs : dict
        Dictionary mapping member index to loaded LHAPDF.PDF objects (pruned set).
        Keys are member numbers (integers), values are lhapdf.PDF objects
    
    discarded_pdfs : dict
        Dictionary mapping member index to loaded LHAPDF.PDF objects (discarded set).
    
    Examples
    --------
    >>> # Method 1: Use DataFrame indices as member numbers
    >>> pruned_pdfs, discarded_pdfs = load_pdfs_from_metadata(
    ...     pruned_metadata=pruned_meta,
    ...     discarded_metadata=discarded_meta,
    ...     pdf_set_name="pq125a",
    ...     pdf_folder="./pq125a"
    ... )
    
    >>> # Method 2: Use a specific column for member numbers
    >>> pruned_pdfs, discarded_pdfs = load_pdfs_from_metadata(
    ...     pruned_metadata=pruned_meta,
    ...     discarded_metadata=discarded_meta,
    ...     pdf_set_name="pq125a",
    ...     pdf_folder="./pq125a",
    ...     member_column="replica_id"
    ... )
    
    >>> # Access a PDF
    >>> pdf = pruned_pdfs[1]  # member 1
    >>> pdf.xfxQ2(0.5, 0, 100.0)  # evaluate gluon at x=0.5, Q2=100
    """
    
    # Validate folder exists
    if not os.path.isdir(pdf_folder):
        raise ValueError(
            f"PDF folder not found: {pdf_folder}\n"
            f"Current working directory: {os.getcwd()}"
        )
    
    # Register LHAPDF path
    lhapdf.pathsPrepend(pdf_folder)
    
    if verbose:
        print(f"Loading PDF set '{pdf_set_name}' from: {pdf_folder}")
    
    def _load_pdfs_from_metadata_df(metadata_df: pd.DataFrame, set_type: str) -> Dict[int, lhapdf.PDF]:
        """Load PDFs from a metadata DataFrame."""
        pdf_dict = {}
        
        # Determine which column to use for member indices
        if member_column is not None:
            if member_column not in metadata_df.columns:
                raise ValueError(
                    f"'{member_column}' not found in metadata. "
                    f"Available columns: {metadata_df.columns.tolist()}"
                )
            member_indices = metadata_df[member_column].values
        else:
            # Use the index as member numbers
            member_indices = metadata_df.index.values
        
        if verbose:
            print(f"\nLoading {set_type} PDFs ({len(member_indices)} members)...")
        
        for member_idx in member_indices:
            member_idx = int(member_idx)  # Ensure it's an integer
            try:
                # Load the PDF using LHAPDF
                pdf = lhapdf.mkPDF(pdf_set_name, member_idx)
                pdf_dict[member_idx] = pdf
                
                if verbose:
                    print(f"  ✓ Loaded member {member_idx}")
                    
            except RuntimeError as e:
                print(f"  ✗ Failed to load member {member_idx}: {str(e)}")
                # Don't raise, just skip missing members (graceful degradation)
            except Exception as e:
                print(f"  ✗ Unexpected error loading member {member_idx}: {str(e)}")
        
        return pdf_dict
    
    # Load both sets
    pruned_pdfs = _load_pdfs_from_metadata_df(pruned_metadata, "Pruned")
    discarded_pdfs = _load_pdfs_from_metadata_df(discarded_metadata, "Discarded")
    
    # Summary
    if verbose:
        print(f"\n--- PDF Loading Summary ---")
        print(f"Pruned PDFs loaded   : {len(pruned_pdfs)}")
        print(f"Discarded PDFs loaded: {len(discarded_pdfs)}")
        print(f"Total PDFs loaded    : {len(pruned_pdfs) + len(discarded_pdfs)}")
    
    return pruned_pdfs, discarded_pdfs


def load_pdfs_from_names(
    pruned_metadata: pd.DataFrame,
    discarded_metadata: pd.DataFrame,
    pdf_set_name: str,
    pdf_folder: str = ".",
    pdf_name_column: str = "pdf_name",
    verbose: bool = True,
) -> Tuple[Dict[int, lhapdf.PDF], Dict[int, lhapdf.PDF]]:
    """
    Loads LHAPDF PDF sets by parsing PDF names from metadata.
    
    Extracts member indices from PDF names like "pq125a_0001" or "pq125a001"
    (without .dat extension) and loads them using LHAPDF.
    
    Parameters
    ----------
    pruned_metadata : pd.DataFrame
        Metadata of representative/best PDFs.
        Must contain a column with PDF names.
    
    discarded_metadata : pd.DataFrame
        Metadata of discarded/redundant PDFs.
        Must contain a column with PDF names.
    
    pdf_set_name : str
        Name of the PDF set (e.g., "pq125a").
        Used to validate that PDF names match the set name.
    
    pdf_folder : str, default="."
        Path to the folder containing PDF grid files.
    
    pdf_name_column : str, default="pdf_name"
        Name of the column in metadata containing PDF names (without .dat).
        Examples: "pq125a_0001", "pq125a001"
    
    verbose : bool, default=True
        Print loading progress and summary information.
    
    Returns
    -------
    pruned_pdfs : dict
        Dictionary mapping member index to loaded LHAPDF.PDF objects (pruned set).
    
    discarded_pdfs : dict
        Dictionary mapping member index to loaded LHAPDF.PDF objects (discarded set).
    
    Raises
    ------
    ValueError
        If pdf_name_column not found, or PDF names can't be parsed.
    
    Examples
    --------
    >>> # Metadata has "pdf_name" column with values like "pq125a_0001"
    >>> pruned_pdfs, discarded_pdfs = load_pdfs_from_names(
    ...     pruned_metadata=pruned_meta,
    ...     discarded_metadata=discarded_meta,
    ...     pdf_set_name="pq125a",
    ...     pdf_folder="./pq125a",
    ...     pdf_name_column="pdf_name"
    ... )
    
    >>> # Or column named differently
    >>> pruned_pdfs, discarded_pdfs = load_pdfs_from_names(
    ...     pruned_metadata=pruned_meta,
    ...     discarded_metadata=discarded_meta,
    ...     pdf_set_name="pq125a",
    ...     pdf_folder="./pq125a",
    """
    
    # Convert to absolute path
    pdf_folder = os.path.abspath(pdf_folder)
    
    # Validate folder exists
    if not os.path.isdir(pdf_folder):
        raise ValueError(
            f"PDF folder not found: {pdf_folder}\n"
            f"Current working directory: {os.getcwd()}\n"
            f"Available directories: {os.listdir('.')}"
        )
    
    # Check that .info file exists
    info_file = os.path.join(pdf_folder, f"{pdf_set_name}.info")
    if not os.path.isfile(info_file):
        available_files = os.listdir(pdf_folder)
        info_files = [f for f in available_files if f.endswith(".info")]
        raise ValueError(
            f"Info file not found: {info_file}\n"
            f"Folder contents: {available_files}\n"
            f"Available .info files in {pdf_folder}: {info_files}\n"
            f"Make sure the PDF set name '{pdf_set_name}' matches your .info filename."
        )
    
    # Register LHAPDF path - use the parent directory
    # LHAPDF expects the folder containing the PDF set folder
    parent_folder = os.path.dirname(pdf_folder)
    lhapdf.pathsPrepend(parent_folder)
    
    if verbose:
        print(f"Loading PDF set '{pdf_set_name}'")
        print(f"  Info file: {info_file}")
        print(f"  LHAPDF path: {parent_folder}")
    
    def _extract_member_number(pdf_name: str) -> int:
        """
        Extract member number from PDF name.
        
        Handles formats like:
        - "pq125a_0001" → 1
        - "pq125a0001"  → 1  (no underscore)
        - "pq125a001" → 1
        - "pq125a_1" → 1
        - "0001" → 1
        - "pq125a_0001.dat" → 1 (ignores .dat)
        """
        # Remove any .dat extension if present
        pdf_name = pdf_name.replace(".dat", "").strip()
        
        # Strategy: find the longest sequence of trailing digits
        trailing_digits = ""
        for i in range(len(pdf_name) - 1, -1, -1):
            if pdf_name[i].isdigit():
                trailing_digits = pdf_name[i] + trailing_digits
            else:
                break
        
        if not trailing_digits:
            raise ValueError(
                f"Cannot extract member number from '{pdf_name}'. "
                f"Expected format like 'pq125a_0001', 'pq125a0001', or '0001'"
            )
        
        # Convert to integer (removes leading zeros)
        member_number = int(trailing_digits)
        
        if member_number == 0:
            raise ValueError(
                f"Invalid member number 0 extracted from '{pdf_name}'. "
                f"Member numbers start from 1."
            )
        
        return member_number
    
    def _load_pdfs_from_names_df(metadata_df: pd.DataFrame, set_type: str) -> Dict[int, lhapdf.PDF]:
        """Load PDFs from a metadata DataFrame with PDF names."""
        pdf_dict = {}
        
        # Validate column exists
        if pdf_name_column not in metadata_df.columns:
            raise ValueError(
                f"'{pdf_name_column}' not found in metadata. "
                f"Available columns: {metadata_df.columns.tolist()}"
            )
        
        pdf_names = metadata_df[pdf_name_column].dropna().unique()
        
        if verbose:
            print(f"\nLoading {set_type} PDFs ({len(pdf_names)} unique names)...")
        
        for pdf_name in pdf_names:
            try:
                # Extract member number from PDF name
                member_idx = _extract_member_number(str(pdf_name))
                
                # Load the PDF using LHAPDF
                pdf = lhapdf.mkPDF(pdf_set_name, member_idx)
                pdf_dict[member_idx] = pdf
                
                if verbose:
                    print(f"  ✓ Loaded {pdf_name} → member {member_idx}")
                    
            except ValueError as e:
                print(f"  ✗ Failed to parse '{pdf_name}': {str(e)}")
                raise
            except RuntimeError as e:
                print(f"  ✗ Failed to load member from '{pdf_name}': {str(e)}")
                print(f"     Checking if file exists...")
                # Check if the .dat file exists
                dat_file = os.path.join(pdf_folder, f"{pdf_set_name}_{member_idx:04d}.dat")
                if not os.path.isfile(dat_file):
                    print(f"     ✗ Data file not found: {dat_file}")
                # Skip this member (graceful degradation)
            except Exception as e:
                print(f"  ✗ Unexpected error loading '{pdf_name}': {str(e)}")
        
        return pdf_dict
    
    # Load both sets
    pruned_pdfs = _load_pdfs_from_names_df(pruned_metadata, "Pruned")
    discarded_pdfs = _load_pdfs_from_names_df(discarded_metadata, "Discarded")
    
    # Summary
    if verbose:
        print(f"\n--- PDF Loading Summary ---")
        print(f"Pruned PDFs loaded   : {len(pruned_pdfs)}")
        print(f"Discarded PDFs loaded: {len(discarded_pdfs)}")
        print(f"Total PDFs loaded    : {len(pruned_pdfs) + len(discarded_pdfs)}")
    
    return pruned_pdfs, discarded_pdfs


def get_pdf_evaluations(
    pdf_dict: Dict[int, lhapdf.PDF],
    x_values: np.ndarray,
    q_values: np.ndarray,
    flavor_ids: Optional[list] = None,
    pdf_set_name: Optional[str] = None,
) -> pd.DataFrame:
    """
    Evaluate a set of PDFs at given x and Q values.
    
    Parameters
    ----------
    pdf_dict : dict
        Dictionary of loaded LHAPDF.PDF objects (output of load_pdfs_from_metadata)
        Keys are member indices (integers), values are lhapdf.PDF objects
    
    x_values : np.ndarray
        Momentum fraction values to evaluate at
    
    q_values : np.ndarray or float
        Momentum transfer values (Q) in GeV to evaluate at.
        Uses xfxQ internally (not xfxQ2).
        Examples: [2, 10, 100, 1000] for 2, 10, 100, 1000 GeV
        Can also be a single value like q_values=10
    
    flavor_ids : list, optional
        Parton flavor IDs to evaluate (-6 to 6, where 0=gluon, ±1=d/dbar, etc.)
        If None, evaluates only gluon (flavor=0)
    
    pdf_set_name : str, optional
        Name of the PDF set (for labeling in output). If None, just uses member index.
    
    Returns
    -------
    pd.DataFrame
        Columns: pdf_name (or member_idx if pdf_set_name is None), x, Q, flavor, xfx
        Each row is one evaluation
    
    Examples
    --------
    >>> evaluations = get_pdf_evaluations(
    ...     pdf_dict=pruned_pdfs,
    ...     x_values=np.array([0.1, 0.5, 0.9]),
    ...     q_values=np.array([2, 10, 100]),  # Q in GeV
    ...     flavor_ids=[0, 1, -1],
    ...     pdf_set_name="pq125a"
    ... )
    
    >>> # Or with a single Q value
    >>> evaluations = get_pdf_evaluations(
    ...     pruned_pdfs,
    ...     x_values=np.linspace(0.001, 0.999, 50),
    ...     q_values=10,  # Single Q value
    ...     flavor_ids=[0, 1, -1],
    ... )
    """
    if flavor_ids is None:
        flavor_ids = [0]  # gluon only
    
    # Ensure q_values is iterable (convert single value to array)
    if isinstance(q_values, (int, float)):
        q_values = np.array([q_values])
    else:
        q_values = np.asarray(q_values)
    
    results = []
    
    for member_idx, pdf in pdf_dict.items():
        # Create a label for the PDF
        if pdf_set_name is not None:
            pdf_label = f"{pdf_set_name}_{member_idx:04d}"
        else:
            pdf_label = f"member_{member_idx}"
        
        for x in x_values:
            for q in q_values:
                for flavor in flavor_ids:
                    try:
                        # Use xfxQ which takes Q (not Q²)
                        xfx = pdf.xfxQ(flavor, x, float(q))
                        results.append({
                            "pdf_name": pdf_label,
                            "member_idx": member_idx,
                            "x": x,
                            "Q": float(q),
                            "flavor": flavor,
                            "xfx": xfx,
                        })
                    except Exception as e:
                        print(f"Error evaluating member {member_idx} at x={x}, Q={q}, flavor={flavor}: {e}")
    
    return pd.DataFrame(results)

# --------------------------------------------------------------------------- #
# Convenience: pull out arrays for plotting n_clusters vs R                     #
# --------------------------------------------------------------------------- #
def n_clusters_vs_R(results):
    """Return (R_array, n_clusters_array) sorted by R, ready for plotting."""
    Rs = np.array(sorted(results))
    n = np.array([results[R]["n_clusters"] for R in Rs])
    return Rs, n