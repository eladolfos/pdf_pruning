"""
Distance metrics for PDF replica clustering.

This module implements various distance metrics optimized for comparing
probability distribution function (PDF) replicas.
"""

import numpy as np
from scipy.spatial.distance import cdist


def pdf_dissimilarity(u: np.ndarray, v: np.ndarray, mindenom: float = 0.0001) -> float:
    """
    Calculate the normalized absolute difference between two PDF vectors.
    
    Implements the dissimilarity metric:
        D(u, v) = sum(2 * |u(x) - v(x)| / (|u(x)| + |v(x)|))
    
    This metric is designed to be sensitive to relative changes across
    PDF components, with numerical stability via mindenom threshold.
    
    Parameters
    ----------
    u : np.ndarray
        First vector, shape (n_features,)
    v : np.ndarray
        Second vector, shape (n_features,)
    mindenom : float, default=1e-4
        Minimum denominator threshold. Components where |u(x)| + |v(x)| <= mindenom
        are masked to ensure numerical stability and focus on physically significant regions.
    
    Returns
    -------
    float
        Dissimilarity distance between u and v.
    
    Examples
    --------
    >>> u = np.array([1.0, 2.0, 3.0])
    >>> v = np.array([1.1, 2.1, 3.1])
    >>> distance = pdf_dissimilarity(u, v)
    """
    abs_u, abs_v = np.abs(u), np.abs(v)
    denom = abs_u + abs_v
    mask = denom > mindenom
    
    if not np.any(mask):
        return 0.0
    
    return float(np.sum(2 * np.abs(u[mask] - v[mask]) / denom[mask]))


def percent_SMAPE(u: np.ndarray, v: np.ndarray, mindenom: float = 0.0001) -> float:
    """
    Calculate the normalized absolute difference between two PDF vectors.
    
    Implements the percent symmetric mean absolute percentage error (SMAPE) metric:
        D(u, v) = sum(2 * |u(x) - v(x)| / (|u(x)| + |v(x)|))/2n
    
    This metric is designed to be sensitive to relative changes across
    PDF components, with numerical stability via mindenom threshold.
    It is always between 0 and 100. 
    
    Parameters
    ----------
    u : np.ndarray
        First vector, shape (n_features,)
    v : np.ndarray
        Second vector, shape (n_features,)
    mindenom : float, default=1e-4
        Minimum denominator threshold. Components where |u(x)| + |v(x)| <= mindenom
        are masked to ensure numerical stability and focus on physically significant regions.
    
    Returns
    -------
    float
         "percentage error", SMAPE values between u and v.
    
    Examples
    --------
    >>> u = np.array([1.0, 2.0, 3.0])
    >>> v = np.array([1.1, 2.1, 3.1])
    >>> distance = pdf_dissimilarity(u, v)
    """
    abs_u, abs_v = np.abs(u), np.abs(v)
    denom = abs_u + abs_v
    mask = denom > mindenom
    
    if not np.any(mask):
        return 0.0
    
    SMAPE =float(( np.sum(2 * np.abs(u[mask] - v[mask]) / denom[mask]) ) / (2*len(u)) )

    return float(100*SMAPE)


def get_clustering_dist_sq(v1, v2, metric, mindenom):
    """
    Calculate squared distance for clustering.
    
    Parameters
    ----------
    v1 : np.ndarray
        First vector
    v2 : np.ndarray
        Second vector
    metric : str
        Distance metric ('euclidean', 'pdf_dissimilarity')
    mindenom : float
        Minimum denominator for PDF dissimilarity
    
    Returns
    -------
    float
        Squared distance
    """
    if metric == "pdf_dissimilarity":
        d = pdf_dissimilarity(v1, v2, mindenom=mindenom)
    elif metric == "euclidean":
        d = np.linalg.norm(v1 - v2)
    else:
        raise ValueError(f"Unknown metric: {metric}")
    
    return d ** 2


def euclidean_distance(u: np.ndarray, v: np.ndarray) -> float:
    """Calculate Euclidean distance between vectors."""
    return float(np.linalg.norm(u - v))


def standardized_euclidean_distance(
    u: np.ndarray, v: np.ndarray, variances: np.ndarray
) -> float:
    """
    Calculate standardized Euclidean distance (Mahalanobis-like).
    
    Parameters
    ----------
    u, v : np.ndarray
        Vectors to compare
    variances : np.ndarray
        Feature variances for standardization
    
    Returns
    -------
    float
        Standardized distance
    """
    scaled_diff = (u - v) / np.sqrt(variances + 1e-10)
    return float(np.linalg.norm(scaled_diff))
