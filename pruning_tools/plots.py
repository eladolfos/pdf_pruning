import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy.spatial.distance import pdist, squareform
from typing import Callable, Optional, Tuple, List, Dict
from plotly.subplots import make_subplots


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
) -> go.Figure:
    """
    Bar chart of the neighbor degree distribution.
    Each bar = how many vectors have exactly k neighbors within R_cutoff.

    X-axis : number of neighbors k  (0, 1, 2, ...)
    Y-axis : number of vectors with exactly k neighbors

    Key markers:
      - k=0  (isolated): vectors that will ALWAYS be solo clusters
      - k>mean: hub vectors, drivers of compression
    """

    # ── 1. Prepare data ───────────────────────────────────────────────────
    if isinstance(data_input, pd.DataFrame):
        drop = [c for c in ["VID", "id", "ID", "vector_ID", "cluster_label", "idx"]
                if c in data_input.columns]
        X = data_input.drop(columns=drop).select_dtypes(include=[np.number]).values
    else:
        X = np.asarray(data_input, dtype=np.float64)

    N = len(X)

    # ── 2. Neighbor counts ────────────────────────────────────────────────
    D = squareform(pdist(X, metric=metric))
    np.fill_diagonal(D, np.inf)
    counts = np.sum(D <= R_cutoff, axis=1).astype(int)

    # ── 3. Statistics ─────────────────────────────────────────────────────
    n_isolated  = int(np.sum(counts == 0))
    mean_deg    = counts.mean()
    median_deg  = float(np.median(counts))
    max_deg     = int(counts.max())
    n_with_nbrs = N - n_isolated
    pairs_total = int(counts.sum() // 2)

    # Degree frequency: how many vectors have exactly k neighbors
    k_values = np.arange(0, max_deg + 1)
    freq     = np.array([np.sum(counts == k) for k in k_values])

    # CDF over vectors: fraction of vectors with <= k neighbors
    cdf_vec = np.cumsum(freq) / N

    if print_statistics:
        sep = "─" * 52
        print(sep)
        print(f"  Neighbor degree  (R = {R_cutoff}, {metric_name})")
        print(sep)
        print(f"  N vectors                : {N}")
        print(f"  Isolated  (k=0)          : {n_isolated}  ({n_isolated/N*100:.1f}%)")
        print(f"    → guaranteed solo clusters")
        print(f"  With neighbors (k≥1)     : {n_with_nbrs}  ({n_with_nbrs/N*100:.1f}%)")
        print(f"  Mean degree              : {mean_deg:.2f}")
        print(f"  Median degree            : {median_deg:.1f}")
        print(f"  Max degree (biggest hub) : {max_deg}")
        print(f"  Total close pairs        : {pairs_total}")
        print(sep)

    # ── 4. Colors per bar ─────────────────────────────────────────────────
    # k=0 → isolated color, k > mean → hub color, rest → neutral
    bar_colors = []
    for k in k_values:
        if k == 0:
            bar_colors.append(color_isolated)
        elif k > mean_deg:
            bar_colors.append(color_hubs)
        else:
            bar_colors.append("rgba(150, 150, 160, 0.7)")

    # ── 5. Figure ─────────────────────────────────────────────────────────
    fig = go.Figure()

    # Main bar chart
    fig.add_trace(go.Bar(
        x=k_values,
        y=freq,
        name="Vectors",
        marker_color=bar_colors,
        hovertemplate=(
            "<b>k = %{x} neighbors</b><br>"
            "Vectors: %{y}<br>"
            "Fraction of N: %{customdata:.1%}"
            "<extra></extra>"
        ),
        customdata=freq / N,
    ))

    # CDF overlay on second y-axis
    fig.add_trace(go.Scatter(
        x=k_values,
        y=cdf_vec,
        mode="lines+markers",
        name="Cumulative fraction",
        yaxis="y2",
        line=dict(color="rgba(80,80,80,0.6)", width=1.5, dash="dot"),
        marker=dict(size=5),
        hovertemplate=(
            "k = %{x}<br>"
            "Cumulative: %{y:.1%} of vectors have ≤ k neighbors"
            "<extra></extra>"
        ),
    ))

    # Vertical line: mean degree
    fig.add_vline(
        x=mean_deg,
        line_width=1.5, line_dash="dash", line_color="darkorange",
        annotation_text=f"mean = {mean_deg:.1f}",
        annotation_position="top right",
        annotation_font=dict(size=12, color="darkorange"),
    )

    # Annotation: isolated count
    if n_isolated > 0:
        fig.add_annotation(
            x=0, y=freq[0],
            xref="x", yref="y",
            text=f"{n_isolated} isolated<br>({n_isolated/N*100:.1f}% of N)",
            showarrow=True, arrowhead=2, arrowcolor=color_isolated,
            ax=40, ay=-40,
            font=dict(size=11, color=color_isolated),
            bgcolor="rgba(255,255,255,0.85)",
            bordercolor=color_isolated, borderwidth=1,
        )

    # Stats box
    fig.add_annotation(
        x=0.99, y=0.97, xref="paper", yref="paper",
        text=(
            f"<b>N = {N}</b><br>"
            f"isolated (k=0): {n_isolated} ({n_isolated/N*100:.1f}%)<br>"
            f"max hub size: {max_deg}<br>"
            f"close pairs: {pairs_total}"
        ),
        showarrow=False, xanchor="right", yanchor="top",
        bgcolor="rgba(255,255,255,0.88)", bordercolor="black", borderwidth=1,
        font=dict(size=12),
    )

    fig.update_layout(
        title=dict(
            text=(
                f"<b>{metric_name} — Neighbor degree distribution  (R = {R_cutoff})</b>"
                f"<br><sub>{title_suffix}</sub>"
            ),
            x=0.5, xanchor="center", font=dict(size=19),
        ),
        xaxis=dict(
            title="Number of neighbors within R  (degree k)",
            dtick=1,
            showline=True, linewidth=2, linecolor="black", mirror="allticks",
            showgrid=True, gridcolor="rgba(200,200,200,0.35)",
        ),
        yaxis=dict(
            title="Number of vectors",
            showline=True, linewidth=2, linecolor="black", mirror=False,
            showgrid=True, gridcolor="rgba(200,200,200,0.35)",
        ),
        yaxis2=dict(
            title="Cumulative fraction of vectors",
            overlaying="y", side="right",
            range=[0, 1.05],
            tickformat=".0%",
            showgrid=False,
            showline=True, linewidth=1.5, linecolor="rgba(80,80,80,0.5)",
        ),
        legend=dict(
            x=0.5, y=0.97, xanchor="center",
            bgcolor="rgba(255,255,255,0.88)",
            bordercolor="black", borderwidth=1,
            font=dict(size=13),
        ),
        bargap=0.15,
        hovermode="x unified",
        template=template,
        height=height, width=width,
        margin=dict(l=80, r=100, t=90, b=70),
    )

    return fig


def plot_cluster_separation(summary_df: pd.DataFrame) -> go.Figure:
    """
    Visualize cluster quality by comparing internal tightness vs. external separation.

    Creates a grouped bar chart showing two key metrics for each cluster:
      - Avg_Intra_Dist: Average distance from vectors to their cluster center
                        (lower = tighter, better-defined clusters)
      - Avg_Inter_Dist: Average distance from cluster center to other centers
                        (higher = more separated, better isolation)

    Ideally, intra-cluster distances should be small while inter-cluster distances
    are large, indicating well-separated, cohesive clusters.

    Args:
        summary_df (pd.DataFrame): Output of analyze_cluster_separation().
                                   Must contain columns:
                                     - Cluster        : cluster identifier
                                     - Avg_Intra_Dist : internal compactness metric
                                     - Avg_Inter_Dist : external separation metric

    Returns:
        go.Figure: Plotly Figure object with grouped bar chart.
                   Call .show() to display or .write_html() to save.

    Example:
        >>> summary = analyze_cluster_separation(final_jets, vectors_df)
        >>> fig = plot_cluster_separation(summary)
        >>> fig.show()
    """
    fig = go.Figure()

    # Intra-cluster distance (Tightness)
    # Lower values indicate vectors are clustered tightly around their center
    fig.add_trace(go.Bar(
        x=summary_df["Cluster"],
        y=summary_df["Avg_Intra_Dist"],
        name="Intra-Cluster (Tightness)",
        marker_color='indianred',
        hovertemplate="<b>Cluster %{x}</b><br>Intra Dist: %{y:.4f}<extra></extra>",
    ))

    # Inter-cluster distance (Separation)
    # Higher values indicate clusters are well-separated from each other
    fig.add_trace(go.Bar(
        x=summary_df["Cluster"],
        y=summary_df["Avg_Inter_Dist"],
        name="Inter-Cluster (Separation)",
        marker_color='skyblue',
        hovertemplate="<b>Cluster %{x}</b><br>Inter Dist: %{y:.4f}<extra></extra>",
    ))

    # Layout configuration
    fig.update_layout(
        title="<b>Cluster Quality: Internal Tightness vs. External Separation</b>",
        xaxis_title="Cluster Label",
        yaxis_title="Average Distance",
        barmode='group',
        template="plotly_white",
        hovermode="x unified",
        showlegend=True,
        height=500,
    )

    return fig


def plot_pairwise_cdf(
    data_input,
    metric: Callable,
    R_cutoff: float = None,
    percentile: float = None,
    metric_name: str = "Custom Metric",
    title_suffix: str = "",
    # --- Colors ---
    color_below: str = "crimson",
    color_above: str = "steelblue",
    color_cutoff: str = "darkred",
    color_median: str = "gray",
    # --- Layout ---
    template: str = "plotly_white",
    height: int = 550,
    width: int = 850,
    print_statistics: bool = True,
) -> go.Figure:
    """
    CDF plot of pairwise distances with a cutoff threshold visualization.

    The CDF is built directly from sorted data (no histogram), so the curve
    value at exactly R_cutoff always equals the fraction of pairs below it.

    Parameters
    ----------
    data_input : array-like or pd.DataFrame, shape (N, d)
    metric     : callable, metric(v1, v2) -> float
    R_cutoff   : float or None — distance threshold; pairs with d <= R_cutoff are "merged"
                 If None, calculated from `percentile`.
    percentile : float or None — percentile (0–100) of pairwise distances to use as R_cutoff.
                 Only used if R_cutoff is None.
                 Example: percentile=90 uses the 90th percentile of all pairwise distances.
    metric_name: str   — label shown in the title
    title_suffix: str  — optional subtitle line
    color_below: str   — color for CDF region at d <= R_cutoff
    color_above: str   — color for CDF region at d >  R_cutoff
    color_cutoff: str  — vertical line at R_cutoff
    color_median: str  — vertical line at median distance
    template   : str   — plotly template
    height/width: int  — figure dimensions in pixels
    print_statistics: bool
    """

    # ── 1. Prepare data ───────────────────────────────────────────────────────
    if isinstance(data_input, pd.DataFrame):
        drop = [c for c in ["VID", "id", "ID", "vector_ID", "cluster_label", "idx"]
                if c in data_input.columns]
        X = data_input.drop(columns=drop).select_dtypes(include=[np.number]).values
    else:
        X = np.asarray(data_input, dtype=np.float64)

    # ── 2. Pairwise distances ─────────────────────────────────────────────────
    distances = pdist(X, metric=metric)
    n_pairs   = len(distances)

    # ── 3. Determine R_cutoff ─────────────────────────────────────────────────
    if R_cutoff is None and percentile is None:
        raise ValueError("Either R_cutoff or percentile must be provided (not both None).")

    if R_cutoff is None:
        # Calculate R from percentile
        if not (0 <= percentile <= 100):
            raise ValueError(f"percentile must be in [0, 100], got {percentile}")
        R_cutoff = float(np.percentile(distances, percentile))
    else:
        percentile = None  # Mark that we're using explicit R_cutoff

    # ── 4. Statistics ─────────────────────────────────────────────────────────
    d_sorted   = np.sort(distances)
    mean_d     = d_sorted.mean()
    median_d   = np.median(d_sorted)
    std_d      = d_sorted.std()
    min_d      = d_sorted[0]
    max_d      = d_sorted[-1]

    # Exact fraction — this is what the CDF must read at R_cutoff
    n_below        = int(np.sum(distances <= R_cutoff))
    frac_below     = n_below / n_pairs
    frac_above     = 1.0 - frac_below

    if print_statistics:
        sep = "─" * 52
        print(sep)
        print(f"  Pairwise Distance Statistics  ({metric_name})")
        print(sep)
        print(f"  Vectors (N)        : {len(X):,}")
        print(f"  Pairs  N(N-1)/2    : {n_pairs:,}")
        print()
        print(f"  Min distance       : {min_d:.4f}")
        print(f"  Mean distance      : {mean_d:.4f}")
        print(f"  Median distance    : {median_d:.4f}")
        print(f"  Std deviation      : {std_d:.4f}")
        print(f"  Max distance       : {max_d:.4f}")
        print()
        print(f"  Cutoff  R = {R_cutoff:.6g}")
        if percentile is not None:
            print(f"    (from percentile {percentile}% of pairwise distances)")
        z = (R_cutoff - median_d) / (std_d + 1e-12)
        side = "below" if z < 0 else "above"
        print(f"    R is {abs(z):.2f} std devs {side} the median")
        print()
        print(f"  Pairs with d ≤ R   : {n_below:,} / {n_pairs:,}")
        print(f"  → Merged (pruned)  : {frac_below*100:.2f}%   "
              f"[CDF({R_cutoff:.6g}) = {frac_below:.4f}]")
        print(f"  → Unmerged         : {frac_above*100:.2f}%")
        print(sep)

    # ── 5. Build exact empirical CDF ──────────────────────────────────────────
    # x = sorted distances,  y = i/n  for i = 1..n
    # This guarantees CDF(R_cutoff) == frac_below by construction.
    cdf_x = d_sorted
    cdf_y = np.arange(1, n_pairs + 1) / n_pairs

    # Split at cutoff — include the boundary point in both halves so
    # the two traces share one point and connect without a visual gap.
    split = n_below  # first index where d > R_cutoff

    # "below" trace: indices 0 … split  (inclusive boundary)
    x_below = cdf_x[:split + 1]
    y_below = cdf_y[:split + 1]

    # "above" trace: indices split … n_pairs-1
    x_above = cdf_x[split:]
    y_above = cdf_y[split:]

    # ── 6. Build figure ───────────────────────────────────────────────────────
    fill_below = color_below.replace(")", ", 0.25)").replace("rgb", "rgba") \
        if color_below.startswith("rgb") else color_below
    fill_above = color_above.replace(")", ", 0.25)").replace("rgb", "rgba") \
        if color_above.startswith("rgb") else color_above

    # Helper: derive a semi-transparent fill from a named color
    FILLS = {
        "crimson":   "rgba(220, 20,  60,  0.20)",
        "steelblue": "rgba( 70, 130, 180, 0.20)",
        "gold":      "rgba(255, 215,   0, 0.20)",
        "darkred":   "rgba(139,   0,   0, 0.20)",
        "navy":      "rgba(  0,   0, 128, 0.20)",
        "darkorange":"rgba(255, 140,   0, 0.20)",
    }
    fill_below = FILLS.get(color_below, "rgba(220,20,60,0.20)")
    fill_above = FILLS.get(color_above, "rgba(70,130,180,0.20)")

    fig = go.Figure()

    # Trace: merged / below-cutoff region
    fig.add_trace(go.Scatter(
        x=x_below, y=y_below,
        mode="lines", fill="tozeroy",
        name=f"Merged  (d ≤ {R_cutoff:.6g})  —  {frac_below*100:.1f}% of pairs",
        line=dict(color=color_below, width=2.5),
        fillcolor=fill_below,
        hovertemplate=(
            "d = %{x:.4f}<br>"
            "CDF = %{y:.4f}  "
            f"({frac_below*100:.1f}% of pairs have d ≤ {R_cutoff:.6g})"
            "<extra>Merged region</extra>"
        ),
    ))

    # Trace: unmerged / above-cutoff region
    fig.add_trace(go.Scatter(
        x=x_above, y=y_above,
        mode="lines", fill="tozeroy",
        name=f"Unmerged (d > {R_cutoff:.6g})  —  {frac_above*100:.1f}% of pairs",
        line=dict(color=color_above, width=2.5),
        fillcolor=fill_above,
        hovertemplate=(
            "d = %{x:.4f}<br>"
            "CDF = %{y:.4f}"
            "<extra>Unmerged region</extra>"
        ),
    ))

    # Vertical line: cutoff
    fig.add_vline(
        x=R_cutoff, line_width=2, line_dash="dash", line_color=color_cutoff,
        annotation_text=f"R = {R_cutoff:.6g}  ({frac_below*100:.1f}%)",
        annotation_position="top left",
        annotation_font=dict(size=13, color=color_cutoff),
    )

    # Vertical line: median
    fig.add_vline(
        x=median_d, line_width=1.5, line_dash="dot", line_color=color_median,
        annotation_text=f"median = {median_d:.3f}",
        annotation_position="bottom right",
        annotation_font=dict(size=12, color=color_median),
    )

    # Stats annotation (bottom-right corner)
    fig.add_annotation(
        x=0.99, y=0.04, xref="paper", yref="paper",
        text=(
            f"<b>n pairs</b> = {n_pairs:,}<br>"
            f"<b>R = {R_cutoff:.6g}</b><br>"
            f"μ = {mean_d:.3f}<br>"
            f"σ = {std_d:.3f}<br>"
            f"median = {median_d:.3f}"
        ),
        showarrow=False, xanchor="right", yanchor="bottom",
        bgcolor="rgba(255,255,255,0.85)", bordercolor="black", borderwidth=1,
        font=dict(size=12),
    )

    fig.update_layout(
        title=dict(
            text=f"<b>{metric_name} — Pairwise Distance CDF  (R = {R_cutoff:.6g})</b><br><sub>{title_suffix}</sub>",
            x=0.5, xanchor="center", font=dict(size=19),
        ),
        xaxis=dict(
            title="Pairwise distance  d<sub>ij</sub>",
            range=[0, max_d * 1.08],
            showline=True, linewidth=2, linecolor="black", mirror="allticks",
            showgrid=True, gridcolor="rgba(200,200,200,0.35)",
            zeroline=False,
        ),
        yaxis=dict(
            title="Cumulative probability  P(d ≤ d<sub>ij</sub>)",
            range=[0, 1.06],
            showline=True, linewidth=2, linecolor="black", mirror="allticks",
            showgrid=True, gridcolor="rgba(200,200,200,0.35)",
            tickformat=".0%",
        ),
        legend=dict(
            x=0.02, y=0.97, xanchor="left", yanchor="top",
            bordercolor="black", borderwidth=1,
            bgcolor="rgba(255,255,255,0.88)",
            font=dict(size=13),
        ),
        hovermode="x",
        template=template,
        height=height, width=width,
        margin=dict(l=80, r=60, t=90, b=70),
    )

    return fig





FLAVOR_NAMES = {
    -6: "tbar",
    -5: "bbar",
    -4: "cbar",
    -3: "sbar",
    -2: "ubar",
    -1: "dbar",
    0: "gluon",
    1: "d",
    2: "u",
    3: "s",
    4: "c",
    5: "b",
    6: "t",
}

FLAVOR_COLORS = {
    -6: "#1f77b4", -5: "#aec7e8",
    -4: "#ff7f0e", -3: "#ffbb78",
    -2: "#2ca02c", -1: "#98df8a",
    0: "#d62728", 
    1: "#98df8a", 2: "#2ca02c",
    3: "#ffbb78", 4: "#ff7f0e",
    5: "#aec7e8", 6: "#1f77b4",
}


import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Optional, List

DEFAULT_FLAVORS = [2, 1, -2, -1, 3, -3, 4, 21]

DEFAULT_FLAVOR_LABELS = {
    2: "u", 1: "d", -2: "ubar", -1: "dbar",
    3: "s", -3: "sbar", 4: "c", 21: "g",
}

_DEFAULT_COLOR_CYCLE = [
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
    "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf",
]

# Special color for gluon to avoid matching discarded gray
FLAVOR_COLORS = {
    21: "#FF1493",  # Deep pink for gluon (distinct from gray)
}


def plot_pruned_vs_discarded_plotly(
    pruned_evaluations: pd.DataFrame,
    discarded_evaluations: pd.DataFrame,
    q_value: float,
    flavor_ids: Optional[List[int]] = None,
    n_cols: int = 3,
    figsize: tuple = (1400, 1000),
    log_x: bool = True,
) -> go.Figure:
    """
    Interactive Plotly function to compare pruned vs discarded PDFs.
    
    Click on "best" or "discarded" in the legend to toggle visibility.
    
    Parameters
    ----------
    pruned_evaluations : pd.DataFrame
        Output of get_pdf_evaluations() for pruned PDFs.
        Must contain columns: pdf_name, x, Q, flavor, xfx
    
    discarded_evaluations : pd.DataFrame
        Output of get_pdf_evaluations() for discarded PDFs.
        Must contain columns: pdf_name, x, Q, flavor, xfx
    
    q_value : float
        The Q value (in GeV) to plot.
    
    flavor_ids : list, optional
        Flavor IDs to plot. If None, uses DEFAULT_FLAVORS
    
    n_cols : int, default=3
        Number of columns for subplot layout.
        Options: 1, 2, 3, or 4 columns
    
    figsize : tuple, default=(1400, 1000)
        Figure size (width, height) in pixels.
        You may want to adjust this based on n_cols:
        - n_cols=1: (600, 400*n_flavors)
        - n_cols=2: (900, 500*ceil(n_flavors/2))
        - n_cols=3: (1400, 400*ceil(n_flavors/3))
        - n_cols=4: (1600, 350*ceil(n_flavors/4))
    
    log_x : bool, default=True
        Use logarithmic scale for x-axis
    
    Returns
    -------
    fig : plotly.graph_objects.Figure
        Interactive Plotly figure
    
    Examples
    --------
    >>> # Default 3 columns
    >>> fig = plot_pruned_vs_discarded_plotly(
    ...     pruned_evaluations=best_evals,
    ...     discarded_evaluations=discarded_evals,
    ...     q_value=2,
    ... )
    
    >>> # 2 columns for larger plots
    >>> fig = plot_pruned_vs_discarded_plotly(
    ...     pruned_evaluations=best_evals,
    ...     discarded_evaluations=discarded_evals,
    ...     q_value=2,
    ...     n_cols=2,
    ...     figsize=(1000, 1200),
    ... )
    
    >>> # 1 column for very detailed view
    >>> fig = plot_pruned_vs_discarded_plotly(
    ...     pruned_evaluations=best_evals,
    ...     discarded_evaluations=discarded_evals,
    ...     q_value=2,
    ...     n_cols=1,
    ...     figsize=(700, 3000),
    ... )
    
    >>> # 4 columns for compact view
    >>> fig = plot_pruned_vs_discarded_plotly(
    ...     pruned_evaluations=best_evals,
    ...     discarded_evaluations=discarded_evals,
    ...     q_value=2,
    ...     n_cols=4,
    ...     figsize=(1800, 800),
    ... )
    """
    
    if n_cols not in [1, 2, 3, 4]:
        raise ValueError("n_cols must be 1, 2, 3, or 4")
    
    if flavor_ids is None:
        flavor_ids = DEFAULT_FLAVORS
    
    # Filter to requested Q value
    pruned_at_q = pruned_evaluations[pruned_evaluations["Q"] == q_value].copy()
    discarded_at_q = discarded_evaluations[discarded_evaluations["Q"] == q_value].copy()
    
    if len(pruned_at_q) == 0:
        raise ValueError(f"No pruned data found for Q={q_value}")
    if len(discarded_at_q) == 0:
        raise ValueError(f"No discarded data found for Q={q_value}")
    
    # Create subplots
    n_flavors = len(flavor_ids)
    n_rows = (n_flavors + n_cols - 1) // n_cols
    
    subplot_titles = []
    for flavor_id in flavor_ids:
        flavor_label = DEFAULT_FLAVOR_LABELS.get(flavor_id, f"pid_{flavor_id}")
        subplot_titles.append(f"{flavor_label} (PID={flavor_id})")
    
    fig = make_subplots(
        rows=n_rows, cols=n_cols,
        subplot_titles=subplot_titles,
        vertical_spacing=0.12,
        horizontal_spacing=0.08,
    )
    
    # Track if we've already added legend entries
    best_legend_added = False
    discarded_legend_added = False
    
    # Plot each flavor
    for idx, flavor_id in enumerate(flavor_ids):
        row = idx // n_cols + 1
        col = idx % n_cols + 1
        
        # Get flavor label and color
        flavor_label = DEFAULT_FLAVOR_LABELS.get(flavor_id, f"pid_{flavor_id}")
        # Use special color for gluon if defined, otherwise use cycle
        if flavor_id in FLAVOR_COLORS:
            color = FLAVOR_COLORS[flavor_id]
        else:
            color = _DEFAULT_COLOR_CYCLE[idx % len(_DEFAULT_COLOR_CYCLE)]
        
        # Get data for this flavor
        pruned_flavor = pruned_at_q[pruned_at_q["flavor"] == flavor_id].sort_values("x")
        discarded_flavor = discarded_at_q[discarded_at_q["flavor"] == flavor_id].sort_values("x")
        
        # Plot pruned (best) PDFs - all individual
        if len(pruned_flavor) > 0:
            for pdf_idx, pdf_name in enumerate(pruned_flavor["pdf_name"].unique()):
                data = pruned_flavor[pruned_flavor["pdf_name"] == pdf_name].sort_values("x")
                
                # Only show legend entry for first best PDF
                show_legend = not best_legend_added
                name = "best" if show_legend else None
                
                fig.add_trace(
                    go.Scatter(
                        x=data["x"],
                        y=data["xfx"],
                        mode="lines",
                        name=name,
                        legendgroup="best",
                        showlegend=show_legend,
                        line=dict(color=color, width=1.5),
                        opacity=0.7,
                        hoverinfo="skip",
                    ),
                    row=row, col=col,
                )
                best_legend_added = True
        
        # Plot discarded PDFs - all individual
        if len(discarded_flavor) > 0:
            for pdf_idx, pdf_name in enumerate(discarded_flavor["pdf_name"].unique()):
                data = discarded_flavor[discarded_flavor["pdf_name"] == pdf_name].sort_values("x")
                
                # Only show legend entry for first discarded PDF
                show_legend = not discarded_legend_added
                name = "discarded" if show_legend else None
                
                fig.add_trace(
                    go.Scatter(
                        x=data["x"],
                        y=data["xfx"],
                        mode="lines",
                        name=name,
                        legendgroup="discarded",
                        showlegend=show_legend,
                        line=dict(color="gray", width=1.5, dash="dash"),
                        opacity=0.4,
                        hoverinfo="skip",
                    ),
                    row=row, col=col,
                )
                discarded_legend_added = True
        
        # Set x-axis type
        if log_x:
            fig.update_xaxes(type="log", row=row, col=col)
        
        fig.update_xaxes(title_text="x", row=row, col=col)
        fig.update_yaxes(title_text="xf(x,Q)", row=row, col=col)
    
    # Update layout
    fig.update_layout(
        title_text=f"PDF Comparison at Q = {q_value} GeV",
        height=figsize[1],
        width=figsize[0],
        hovermode=False,
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="right",
            x=0.99,
            bgcolor="rgba(255, 255, 255, 0.8)",
            bordercolor="black",
            borderwidth=1,
        ),
    )
    
    return fig
