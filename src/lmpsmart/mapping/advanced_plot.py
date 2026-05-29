# Copyright (c) 2025 Qiang Gan
# SPDX-License-Identifier: GPL-3.0-or-later
"""Advanced plotting: boxplot, violin, scatter, surface, contour, heatmap."""
from __future__ import annotations

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

__all__ = [
    "plot_boxplot",
    "plot_violin",
    "plot_scatter",
    "plot_surface",
    "plot_contour",
    "plot_heatmap",
]


def _style(fig, ax, ps):
    sns.set_theme(style=ps.sns_style, font="Times New Roman", font_scale=ps.fontscale)
    plt.rcParams.update({
        "font.family": "serif",
        "font.serif": ["Times New Roman"],
        "font.size": ps.ticksize,
        "axes.unicode_minus": False,
        "mathtext.fontset": "stix",
    })
    ax.tick_params(labelsize=ps.ticksize)


def _figsize_arg(figsize, ps):
    if figsize:
        if isinstance(figsize, str):
            w, h = figsize.split(",")
            return int(w.strip()), int(h.strip())
        return figsize[0], figsize[1]
    return ps.width, ps.high


def plot_boxplot(
    df: pd.DataFrame,
    output_path: str,
    x_col: str,
    y_col: str,
    hue_col: str | None = None,
    order: list[str] | None = None,
    title: str = "",
    xlabel: str = "",
    ylabel: str = "",
    figsize: tuple[int, int] | str | None = None,
    dpi: int | None = None,
    palette: str = "tab10",
    legend_loc: str = "best",
) -> dict:
    """Box plot using seaborn.

    For comparing distributions across categories, e.g. species energy distributions,
    stress distributions per atom type.
    """
    from lmpsmart.arrange.config import load_config
    cfg = load_config()
    ps = cfg.plotset.singlescale
    w, h = _figsize_arg(figsize, ps)
    dpi_val = dpi if dpi is not None else ps.dpi

    fig, ax = plt.subplots(figsize=(w, h), dpi=dpi_val)
    _style(fig, ax, ps)

    kwargs = {"data": df, "x": x_col, "y": y_col}
    if hue_col:
        kwargs["hue"] = hue_col
        kwargs["palette"] = palette
    if order:
        kwargs["order"] = order
    sns.boxplot(ax=ax, **kwargs)

    if xlabel:
        ax.set_xlabel(xlabel, fontsize=ps.labelsize)
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=ps.labelsize)
    if title:
        ax.set_title(title, fontsize=ps.labelsize)
    if hue_col:
        handles, labels = ax.get_legend_handles_labels()
        if labels:
            ax.legend(handles, labels, loc=legend_loc, frameon=False, fontsize=ps.ticksize)

    plt.tight_layout()
    fig.savefig(output_path, dpi=dpi_val, bbox_inches="tight")
    plt.close(fig)
    return {"status": "success", "output": output_path}


def plot_violin(
    df: pd.DataFrame,
    output_path: str,
    x_col: str,
    y_col: str,
    hue_col: str | None = None,
    order: list[str] | None = None,
    title: str = "",
    xlabel: str = "",
    ylabel: str = "",
    figsize: tuple[int, int] | str | None = None,
    dpi: int | None = None,
    palette: str = "tab10",
    legend_loc: str = "best",
) -> dict:
    """Violin plot using seaborn.

    Shows full distribution shape — useful for comparing energy/velocity distributions
    across groups.
    """
    from lmpsmart.arrange.config import load_config
    cfg = load_config()
    ps = cfg.plotset.singlescale
    w, h = _figsize_arg(figsize, ps)
    dpi_val = dpi if dpi is not None else ps.dpi

    fig, ax = plt.subplots(figsize=(w, h), dpi=dpi_val)
    _style(fig, ax, ps)

    kwargs = {"data": df, "x": x_col, "y": y_col}
    if hue_col:
        kwargs["hue"] = hue_col
        kwargs["palette"] = palette
    if order:
        kwargs["order"] = order
    sns.violinplot(ax=ax, **kwargs)

    if xlabel:
        ax.set_xlabel(xlabel, fontsize=ps.labelsize)
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=ps.labelsize)
    if title:
        ax.set_title(title, fontsize=ps.labelsize)
    if hue_col:
        handles, labels = ax.get_legend_handles_labels()
        if labels:
            ax.legend(handles, labels, loc=legend_loc, frameon=False, fontsize=ps.ticksize)

    plt.tight_layout()
    fig.savefig(output_path, dpi=dpi_val, bbox_inches="tight")
    plt.close(fig)
    return {"status": "success", "output": output_path}


def plot_scatter(
    df: pd.DataFrame,
    output_path: str,
    x_col: str,
    y_col: str,
    size_col: str | None = None,
    color_col: str | None = None,
    hue_col: str | None = None,
    title: str = "",
    xlabel: str = "",
    ylabel: str = "",
    figsize: tuple[int, int] | str | None = None,
    dpi: int | None = None,
    palette: str = "tab10",
    markers: bool = True,
    alpha: float = 0.7,
    legend_loc: str = "best",
) -> dict:
    """Scatter plot with optional size encoding (bubble chart) and colour encoding.

    - ``size_col`` encodes marker size (bubble chart).
    - ``color_col`` encodes marker colour via a colormap.
    - ``hue_col`` groups by category using seaborn palette.
    """
    from lmpsmart.arrange.config import load_config
    cfg = load_config()
    ps = cfg.plotset.singlescale
    w, h = _figsize_arg(figsize, ps)
    dpi_val = dpi if dpi is not None else ps.dpi

    fig, ax = plt.subplots(figsize=(w, h), dpi=dpi_val)
    _style(fig, ax, ps)

    s = df[size_col].values * 10 if size_col and size_col in df.columns else 50
    c = None
    if color_col and color_col in df.columns:
        c = df[color_col].values

    sc = ax.scatter(
        df[x_col], df[y_col],
        s=s, c=c,
        cmap=palette if c is not None else None,
        marker="o" if markers else None,
        alpha=alpha,
        edgecolors="none" if not markers else None,
    )
    if c is not None:
        fig.colorbar(sc, ax=ax, label=color_col)

    if hue_col and hue_col in df.columns:
        for cat in df[hue_col].unique():
            subset = df[df[hue_col] == cat]
            ax.scatter(subset[x_col], subset[y_col], label=cat, s=s, alpha=alpha, edgecolors="none")
        handles, labels_ = ax.get_legend_handles_labels()
        ax.legend(handles, labels_, loc=legend_loc, frameon=False, fontsize=ps.ticksize)

    if xlabel:
        ax.set_xlabel(xlabel, fontsize=ps.labelsize)
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=ps.labelsize)
    if title:
        ax.set_title(title, fontsize=ps.labelsize)

    plt.tight_layout()
    fig.savefig(output_path, dpi=dpi_val, bbox_inches="tight")
    plt.close(fig)
    return {"status": "success", "output": output_path}


def plot_surface(
    df: pd.DataFrame,
    output_path: str,
    x_col: str,
    y_col: str,
    z_col: str,
    cmap: str = "viridis",
    title: str = "",
    xlabel: str = "",
    ylabel: str = "",
    zlabel: str = "",
    figsize: tuple[int, int] | str | None = None,
    dpi: int | None = None,
    elev: int = 30,
    azim: int = 45,
) -> dict:
    """3D surface plot via Axes3D.

    Pivot the DataFrame on x_col × y_col → z_col grid, then plot_surface.
    Use for energy landscapes, potential energy surfaces.
    """
    from mpl_toolkits.mplot3d import Axes3D
    from lmpsmart.arrange.config import load_config
    cfg = load_config()
    ps = cfg.plotset.singlescale
    w, h = _figsize_arg(figsize, ps)
    dpi_val = dpi if dpi is not None else ps.dpi

    fig = plt.figure(figsize=(w, h), dpi=dpi_val)
    ax = fig.add_subplot(111, projection="3d")
    _style(fig, ax, ps)

    pivot = df.pivot_table(index=y_col, columns=x_col, values=z_col, aggfunc="mean")
    X = pivot.columns.values
    Y = pivot.index.values
    X, Y = np.meshgrid(X, Y)
    Z = pivot.values

    surf = ax.plot_surface(X, Y, Z, cmap=cmap, linewidth=0, antialiased=True)
    ax.view_init(elev=elev, azim=azim)
    fig.colorbar(surf, ax=ax, shrink=0.5, aspect=10, label=zlabel)

    if xlabel:
        ax.set_xlabel(xlabel, fontsize=ps.labelsize)
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=ps.labelsize)
    if zlabel:
        ax.set_zlabel(zlabel, fontsize=ps.labelsize)
    if title:
        ax.set_title(title, fontsize=ps.labelsize)

    plt.tight_layout()
    fig.savefig(output_path, dpi=dpi_val, bbox_inches="tight")
    plt.close(fig)
    return {"status": "success", "output": output_path}


def plot_contour(
    df: pd.DataFrame,
    output_path: str,
    x_col: str,
    y_col: str,
    z_col: str,
    levels: int = 20,
    cmap: str = "viridis",
    filled: bool = True,
    title: str = "",
    xlabel: str = "",
    ylabel: str = "",
    figsize: tuple[int, int] | str | None = None,
    dpi: int | None = None,
) -> dict:
    """Filled or line contour plot.

    Pivot df on x_col × y_col → z_col, then contourf / contour.
    Use for 2D energy/stress maps, NEB profiles.
    """
    from lmpsmart.arrange.config import load_config
    cfg = load_config()
    ps = cfg.plotset.singlescale
    w, h = _figsize_arg(figsize, ps)
    dpi_val = dpi if dpi is not None else ps.dpi

    fig, ax = plt.subplots(figsize=(w, h), dpi=dpi_val)
    _style(fig, ax, ps)

    pivot = df.pivot_table(index=y_col, columns=x_col, values=z_col, aggfunc="mean")
    X = pivot.columns.values
    Y = pivot.index.values
    X, Y = np.meshgrid(X, Y)
    Z = pivot.values

    if filled:
        cf = ax.contourf(X, Y, Z, levels=levels, cmap=cmap)
    else:
        cf = ax.contour(X, Y, Z, levels=levels, cmap=cmap)
    fig.colorbar(cf, ax=ax, label=z_col)

    if xlabel:
        ax.set_xlabel(xlabel, fontsize=ps.labelsize)
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=ps.labelsize)
    if title:
        ax.set_title(title, fontsize=ps.labelsize)

    plt.tight_layout()
    fig.savefig(output_path, dpi=dpi_val, bbox_inches="tight")
    plt.close(fig)
    return {"status": "success", "output": output_path}


def plot_heatmap(
    df: pd.DataFrame,
    output_path: str,
    x_col: str,
    y_col: str,
    value_col: str,
    cmap: str = "coolwarm",
    annot: bool = False,
    fmt: str = ".2f",
    title: str = "",
    figsize: tuple[int, int] | str | None = None,
    dpi: int | None = None,
    cbar: bool = True,
) -> dict:
    """Heatmap via seaborn.

    Pivot df on y_col × x_col → value_col. Suitable for correlation matrices,
    species abundance vs temperature, MSXRD peak intensity heatmaps.
    """
    from lmpsmart.arrange.config import load_config
    cfg = load_config()
    ps = cfg.plotset.singlescale
    w, h = _figsize_arg(figsize, ps)
    dpi_val = dpi if dpi is not None else ps.dpi

    fig, ax = plt.subplots(figsize=(w, h), dpi=dpi_val)
    _style(fig, ax, ps)

    pivot = df.pivot_table(index=y_col, columns=x_col, values=value_col, aggfunc="mean")
    sns.heatmap(
        pivot, ax=ax, cmap=cmap,
        annot=annot, fmt=fmt,
        cbar=cbar,
        linewidths=0,
    )

    if title:
        ax.set_title(title, fontsize=ps.labelsize)
    plt.tight_layout()
    fig.savefig(output_path, dpi=dpi_val, bbox_inches="tight")
    plt.close(fig)
    return {"status": "success", "output": output_path}
