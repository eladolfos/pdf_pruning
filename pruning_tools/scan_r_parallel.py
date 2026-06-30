"""
Parallel scan of the clustering radius R for the Cambridge/Aachen algorithm.

Runs `cambridge_cluster` for many values of R concurrently, using
(number of cores - 1) worker processes, and returns a dictionary
keyed by R with a summary of the clustering for each radius.

Usage
-----
    from cambridge import cambridge_cluster   # <-- your module
    from scan_R_parallel import scan_R_parallel
    import numpy as np

    vectors = np.random.randn(200, 3)
    R_values = np.linspace(0.1, 3.0, 30)

    # IMPORTANT: guard the entry point on macOS/Windows (spawn start method)
    if __name__ == "__main__":
        results = scan_R_parallel(
            vectors,
            metric="euclidean_sq",        # string key, or a TOP-LEVEL function
            R_values=R_values,
            rec_crit="best_chi2",
            chi2=chi2_array,
            CompleteLinkage=True,         # <-- NEW: use the strict merge rule
        )
        for R, s in results.items():
            print(R, s["n_clusters"])

Metric pickling note
--------------------
Worker processes need the metric to be picklable. A `lambda` is NOT picklable,
so pass one of:
  * a string key into the built-in registry below ("euclidean", "euclidean_sq"),
  * or a module-level (def) function,
  * or a functools.partial wrapping a module-level function.
"""

import os
import time
import numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed

# Import the original clustering routine. Adjust the module name to match
# wherever you keep `cambridge_cluster`. If it lives in this same file,
# delete this import.
from .cambridge_algorithm import cambridge_cluster


# --------------------------------------------------------------------------- #
# Built-in, picklable metrics (resolved by string key inside each worker)      #
# --------------------------------------------------------------------------- #
def _euclidean_sq(v1, v2):
    return float(np.sum((v1 - v2) ** 2))


def _euclidean(v1, v2):
    return float(np.sqrt(np.sum((v1 - v2) ** 2)))


_METRIC_REGISTRY = {
    "euclidean_sq": _euclidean_sq,
    "euclidean": _euclidean,
}


def _resolve_metric(metric_spec):
    """A string is looked up in the registry; a callable is returned as-is."""
    if isinstance(metric_spec, str):
        try:
            return _METRIC_REGISTRY[metric_spec]
        except KeyError:
            raise ValueError(
                f"Unknown metric {metric_spec!r}. "
                f"Known keys: {list(_METRIC_REGISTRY)}"
            )
    if callable(metric_spec):
        return metric_spec
    raise TypeError("metric must be a string key or a callable.")


# --------------------------------------------------------------------------- #
# Worker-side state (set once per process via the executor initializer)        #
# --------------------------------------------------------------------------- #
_WS = {}  # worker state


def _init_worker(vectors, metric_spec, ids, rec_crit, chi2, CompleteLinkage):
    """Runs once in each worker; stores the shared, R-independent inputs.

    CompleteLinkage is just another R-independent setting (like rec_crit
    or chi2), so it is stored here once and reused for every R value that
    this worker process handles.
    """
    _WS["vectors"] = np.asarray(vectors, dtype=np.float64)
    _WS["metric"] = _resolve_metric(metric_spec)
    _WS["ids"] = ids
    _WS["rec_crit"] = rec_crit
    _WS["chi2"] = chi2
    _WS["CompleteLinkage"] = CompleteLinkage


def _summarize_clusters(clusters, R, keep_full_clusters):
    """Condense one clustering result into a compact summary dict."""
    sizes = [c["num_vectors"] for c in clusters]

    summary = {
        "R": float(R),
        "n_clusters": len(clusters),
        "cluster_sizes": sizes,
        "n_singletons": sum(1 for s in sizes if s == 1),
        "largest_cluster": max(sizes) if sizes else 0,
        "mean_cluster_size": float(np.mean(sizes)) if sizes else 0.0,
    }

    # Report best-chi2 member per cluster when available (None otherwise).
    if clusters and clusters[0].get("best_chi2_id") is not None:
        summary["best_chi2_ids"] = [c["best_chi2_id"] for c in clusters]
        summary["best_chi2_values"] = [c["best_chi2_value"] for c in clusters]
    else:
        summary["best_chi2_ids"] = None
        summary["best_chi2_values"] = None

    # Diagnostic: largest within-cluster dissimilarity, found across all
    # clusters at this R. With CompleteLinkage=True this is guaranteed to
    # be <= R; with CompleteLinkage=False it can exceed R (chaining).
    # Only present if cambridge_cluster reports the field (it does, in the
    # CompleteLinkage-aware version).
    if clusters and "max_internal_dissimilarity" in clusters[0]:
        worst_vals = [c["max_internal_dissimilarity"] for c in clusters]
        summary["max_internal_dissimilarity_overall"] = float(max(worst_vals)) if worst_vals else 0.0
    else:
        summary["max_internal_dissimilarity_overall"] = None

    if keep_full_clusters:
        summary["clusters"] = clusters

    return summary


def _cluster_one_R(R, keep_full_clusters):
    """Cluster at a single radius using the pre-loaded worker state."""
    clusters = cambridge_cluster(
        _WS["vectors"],
        metric=_WS["metric"],
        R=R,
        ids=_WS["ids"],
        rec_crit=_WS["rec_crit"],
        chi2=_WS["chi2"],
        CompleteLinkage=_WS["CompleteLinkage"],
    )
    return float(R), _summarize_clusters(clusters, R, keep_full_clusters)


# --------------------------------------------------------------------------- #
# Public entry point                                                           #
# --------------------------------------------------------------------------- #
def scan_R_parallel(
    vectors,
    metric,
    R_values,
    ids=None,
    rec_crit="average",
    chi2=None,
    CompleteLinkage=False,
    n_workers=None,
    keep_full_clusters=False,
):
    """
    Run `cambridge_cluster` over many R values in parallel.

    Parameters
    ----------
    vectors : array-like, shape (N, d)
        Input vectors to cluster (sent to the workers once).
    metric : str or callable
        Either a key into the built-in registry ("euclidean_sq", "euclidean")
        or a PICKLABLE callable (a top-level def or functools.partial, NOT a
        lambda).
    R_values : iterable of float
        Clustering radii to explore.
    ids, rec_crit, chi2 :
        Passed straight through to `cambridge_cluster`. Note that
        rec_crit="best_chi2" requires `chi2`.
    CompleteLinkage : bool, default False
        Passed straight through to `cambridge_cluster` for every R value.
            False : original single-linkage merge rule (a pair merges if
                    the distance between the two closest members is < R).
            True  : strict complete-linkage merge rule (a pair only merges
                    if the distance between the two FARTHEST members is
                    <= R). This guarantees that every pair of replicas
                    inside every returned cluster satisfies D(i,j) <= R,
                    at every R value scanned.
        This is the same flag for every worker and every R: it changes how
        clusters are formed, not which R values are tested.
    n_workers : int, optional
        Number of worker processes. Defaults to (cpu_count - 1), min 1.
    keep_full_clusters : bool
        If True, each summary also keeps the full list of cluster dicts under
        the "clusters" key. Off by default to keep the result light.

    Returns
    -------
    dict
        { R_value : summary_dict, ... }, ordered by increasing R. Each
        summary_dict contains:
            R, n_clusters, cluster_sizes, n_singletons, largest_cluster,
            mean_cluster_size, best_chi2_ids, best_chi2_values,
            max_internal_dissimilarity_overall
            (+ "clusters" if keep_full_clusters=True)
    """
    vectors = np.asarray(vectors, dtype=np.float64)
    R_values = [float(r) for r in R_values]

    if rec_crit == "best_chi2" and chi2 is None:
        raise ValueError("rec_crit='best_chi2' requires the chi2 array.")

    if n_workers is None:
        n_workers = max(1, (os.cpu_count() or 2) - 1)
    # No point spawning more workers than tasks.
    n_workers = min(n_workers, len(R_values))

    linkage_label = "complete-linkage" if CompleteLinkage else "single-linkage"
    print(f"Starting scan of {len(R_values)} R values using {n_workers} cores")
    print(f"Merge rule: {linkage_label} (CompleteLinkage={CompleteLinkage})")
    print(f"R range: [{R_values[0]:.4f}, {R_values[-1]:.4f}]")
    print(f"R values to analyze: {R_values}")

    results = {}

    # Serial fallback (1 worker or a single R): avoids process overhead.
    if n_workers <= 1:
        print("Running in serial mode (no parallelization)")
        metric_fn = _resolve_metric(metric)
        start_time = time.time()
        for idx, R in enumerate(R_values, 1):
            clusters = cambridge_cluster(
                vectors, metric=metric_fn, R=R, ids=ids,
                rec_crit=rec_crit, chi2=chi2,
                CompleteLinkage=CompleteLinkage,
            )
            results[R] = _summarize_clusters(clusters, R, keep_full_clusters)

            elapsed = time.time() - start_time
            avg_time_per_task = elapsed / idx
            remaining_tasks = len(R_values) - idx
            estimated_time_remaining = avg_time_per_task * remaining_tasks

            print(f"  Progress: {idx}/{len(R_values)} | "
                  f"Elapsed: {elapsed:.1f}s | "
                  f"Est. time remaining: {estimated_time_remaining:.1f}s")

        total_time = time.time() - start_time
        print(f"Scan complete. Analyzed {len(results)} R values in {total_time:.1f}s")
        return dict(sorted(results.items()))

    # Parallel path.
    print(f"Running in parallel mode with {n_workers} worker processes")
    start_time = time.time()
    with ProcessPoolExecutor(
        max_workers=n_workers,
        initializer=_init_worker,
        initargs=(vectors, metric, ids, rec_crit, chi2, CompleteLinkage),
    ) as ex:
        futures = {
            ex.submit(_cluster_one_R, R, keep_full_clusters): R
            for R in R_values
        }
        total_tasks = len(futures)
        completed_tasks = 0

        for fut in as_completed(futures):
            R, summary = fut.result()
            results[R] = summary
            completed_tasks += 1

            elapsed = time.time() - start_time
            avg_time_per_task = elapsed / completed_tasks
            remaining_tasks = total_tasks - completed_tasks
            estimated_time_remaining = avg_time_per_task * remaining_tasks

            print(f"  Progress: {completed_tasks}/{total_tasks} | "
                  f"Elapsed: {elapsed:.1f}s | "
                  f"Est. time remaining: {estimated_time_remaining:.1f}s")

    total_time = time.time() - start_time
    print(f"Scan complete. Analyzed {len(results)} R values in {total_time:.1f}s")
    return dict(sorted(results.items()))


#if __name__ == "__main__":
#    # Minimal self-contained demo.
#    rng = np.random.default_rng(0)
#    demo_vectors = rng.standard_normal((150, 3))
#    demo_R = np.linspace(0.2, 4.0, 25)
#
#    out = scan_R_parallel(demo_vectors, metric="euclidean_sq", R_values=demo_R)
#    Rs, ncl = n_clusters_vs_R(out)
#    for r, c in zip(Rs, ncl):
#        print(f"R = {r:5.2f}  ->  {c:3d} clusters")