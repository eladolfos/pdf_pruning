import numpy as np
from typing import Callable, Optional


def cambridge_cluster(
    vectors,
    metric: Callable,
    R: float = 1.0,
    ids=None,
    rec_crit: str = "average",
    chi2=None,
) -> list[dict]:
    """
    Cambridge/Aachen sequential recombination clustering for
    high-dimensional vector spaces.

    Clustering is purely geometric (p=0): no weights, no chi2 in the
    *distance*, no physics. The distance metric is fully delegated to
    the caller. What changes here is the *recombination scheme*: how a
    merged pair is represented afterwards.

    Recombination schemes (rec_crit)
    --------------------------------
    "average"  : (default, original behaviour) the merged particle is the
                 simple average of the two merging vectors. This introduces
                 a *new* vector that does not correspond to any input
                 replica.
    "best_chi2": no new vector is created. When two particles merge, the
                 surviving representative is the one whose underlying
                 replica has the lower chi2. Because min is associative,
                 the representative of a finished cluster is exactly the
                 lowest-chi2 replica among all its members, and the
                 cluster_vector is therefore a real input replica.
                 Requires the `chi2` array.

    Parameters
    ----------
    vectors : array-like, shape (N, d)
        Input vectors to cluster.
    metric : callable
        metric(v1, v2) -> float
        Any non-negative symmetric function. Called as-is; pass a
        closure or functools.partial if you need extra parameters.
    R : float
        Clustering radius. Pairs with delta/R >= 1 are not merged and
        are finalised as individual jets instead.
    ids : array-like of int, optional
        Original identifiers for each vector. Defaults to 0..N-1.
    rec_crit : {"average", "best_chi2"}
        Recombination scheme, see above. Default "average".
    chi2 : array-like of float, shape (N,), optional
        chi2[i] is the chi2 of vectors[i]. "best" means the *lowest*
        chi2 (best fit). Required when rec_crit="best_chi2". If supplied
        with rec_crit="average", it is not used for recombination but the
        best-chi2 member of each cluster is still reported (useful for
        comparing the two schemes on the same footing).

    Returns
    -------
    list of dict, one entry per cluster:
        cluster_label              : int
        vectors_in_cluster         : list of original ids
        cluster_vector             : np.ndarray
                                     - "average":  averaged centroid
                                     - "best_chi2": the lowest-chi2 member
        num_vectors                : int
        closest_vec_to_centroid_id : int   (id of the member vector nearest
                                            to the centroid by Euclidean distance)
        dist_of_closest_to_centroid: float (Euclidean distance from that vector
                                            to the centroid)
        best_chi2_id               : int   (id of the lowest-chi2 member, or
                                            None if no chi2 was provided)
        best_chi2_value            : float (its chi2, or None)
        best_chi2_vector           : np.ndarray (that member's vector, or None)

    Notes
    -----
    In "best_chi2" mode the centroid is itself a real member, so
    cluster_vector == best_chi2_vector and closest_vec_to_centroid_id ==
    best_chi2_id with dist_of_closest_to_centroid ~ 0. This is a useful
    self-consistency check.

    Examples
    --------
    Euclidean, original averaging scheme
        cambridge_cluster(vectors, metric=lambda v1, v2: float(np.sum((v1 - v2) ** 2)))

    Keep the best-chi2 replica instead of averaging
        cambridge_cluster(
            vectors,
            metric=lambda v1, v2: float(np.sum((v1 - v2) ** 2)),
            R=1.0,
            rec_crit="best_chi2",
            chi2=chi2_array,
        )
    """
    vectors = np.array(vectors, dtype=np.float64)
    N = len(vectors)

    if ids is None:
        ids = list(range(N))
    else:
        ids = list(ids)

    # ------------------------------------------------------------------ #
    # Recombination scheme / chi2 validation                              #
    # ------------------------------------------------------------------ #
    valid_schemes = ("average", "best_chi2")
    if rec_crit not in valid_schemes:
        raise ValueError(
            f"rec_crit must be one of {valid_schemes}, got {rec_crit!r}"
        )

    id_to_chi2 = None
    if chi2 is not None:
        chi2 = np.asarray(chi2, dtype=np.float64)
        if chi2.shape[0] != N:
            raise ValueError(
                f"chi2 must have one value per vector: expected {N}, got {chi2.shape[0]}"
            )
        id_to_chi2 = {ids[i]: float(chi2[i]) for i in range(N)}

    if rec_crit == "best_chi2" and id_to_chi2 is None:
        raise ValueError(
            "rec_crit='best_chi2' requires the chi2 array (one chi2 per vector)."
        )

    # Build a lookup from id -> original vector for centroid comparisons later.
    id_to_vector = {ids[i]: vectors[i] for i in range(N)}

    # ------------------------------------------------------------------ #
    # Internal state: one particle per input vector                        #
    # ------------------------------------------------------------------ #
    particles = []
    for i in range(N):
        p = {
            "id":     [ids[i]],
            "vector": vectors[i].copy(),
            "active": True,
        }
        if rec_crit == "best_chi2":
            # Track the chi2 (and id) of the replica this particle currently
            # represents, so a merge can keep the better-fitting one.
            p["rep_chi2"] = id_to_chi2[ids[i]]
            p["rep_id"]   = ids[i]
        particles.append(p)

    final_clusters = []
    cluster_counter = 0
    R_sq = R * R

    # ------------------------------------------------------------------ #
    # Main loop                                                            #
    # ------------------------------------------------------------------ #
    while True:
        active = [i for i, p in enumerate(particles) if p["active"]]
        if not active:
            break

        # Cambridge/Aachen: beam distance is uniform (p=0 -> W^0 = 1)
        # so d_iB = 1 for all particles.
        # A pair merges if  delta_sq / R_sq  < 1  (i.e. delta < R).
        # Otherwise the closest-to-beam particle is finalised.

        min_dist   = float("inf")
        merge_pair = (-1, -1)       # (-1, -1) means "finalise single"

        # Beam distances (all equal to 1 for C/A)
        for idx in active:
            if 1.0 < min_dist:
                min_dist   = 1.0
                merge_pair = (idx, -1)

        # Pair distances
        for loc, idx_i in enumerate(active):
            for idx_j in active[loc + 1:]:
                delta_sq = metric(particles[idx_i]["vector"],
                                  particles[idx_j]["vector"])
                d_ij = delta_sq*delta_sq / R_sq      # beam distance is 1 for both
                if d_ij < min_dist:
                    min_dist   = d_ij
                    merge_pair = (idx_i, idx_j)

        i, j = merge_pair

        if j == -1:
            # ---- Finalise as a cluster --------------------------------- #
            pt = particles[i]
            centroid = pt["vector"].copy()

            # Find the member vector (by original id) closest to the centroid
            # using Euclidean distance.
            closest_id   = None
            closest_dist = float("inf")
            for member_id in pt["id"]:
                dist = float(np.linalg.norm(id_to_vector[member_id] - centroid))
                if dist < closest_dist:
                    closest_dist = dist
                    closest_id   = member_id

            cluster = {
                "cluster_label":               cluster_counter,
                "vectors_in_cluster":          pt["id"],
                "cluster_vector":              centroid,
                "num_vectors":                 len(pt["id"]),
                "closest_vec_to_centroid_id":  closest_id,
                "dist_of_closest_to_centroid": closest_dist,
            }

            # Report the lowest-chi2 member of the cluster, whenever chi2 is
            # available (independent of the recombination scheme), so the two
            # schemes can be compared on the same footing.
            if id_to_chi2 is not None:
                best_chi2_id = min(pt["id"], key=lambda m: id_to_chi2[m])
                cluster["best_chi2_id"]     = best_chi2_id
                cluster["best_chi2_value"]  = id_to_chi2[best_chi2_id]
                cluster["best_chi2_vector"] = id_to_vector[best_chi2_id].copy()
            else:
                cluster["best_chi2_id"]     = None
                cluster["best_chi2_value"]  = None
                cluster["best_chi2_vector"] = None

            final_clusters.append(cluster)
            particles[i]["active"] = False
            cluster_counter += 1

        else:
            # ---- Merge ------------------------------------------------- #
            p1, p2 = particles[i], particles[j]

            if rec_crit == "average":
                # Simple average: introduces a new (synthetic) vector.
                new_vector = (p1["vector"] + p2["vector"]) / 2.0
                merged = {
                    "id":     p1["id"] + p2["id"],
                    "vector": new_vector,
                    "active": True,
                }
            else:  # rec_crit == "best_chi2"
                # Keep the representative with the lower (better) chi2.
                # No new vector is created.
                if p1["rep_chi2"] <= p2["rep_chi2"]:
                    keep_vector, keep_chi2, keep_id = (
                        p1["vector"], p1["rep_chi2"], p1["rep_id"]
                    )
                else:
                    keep_vector, keep_chi2, keep_id = (
                        p2["vector"], p2["rep_chi2"], p2["rep_id"]
                    )
                merged = {
                    "id":       p1["id"] + p2["id"],
                    "vector":   keep_vector.copy(),
                    "active":   True,
                    "rep_chi2": keep_chi2,
                    "rep_id":   keep_id,
                }

            particles[i] = merged
            particles[j]["active"] = False

    return final_clusters