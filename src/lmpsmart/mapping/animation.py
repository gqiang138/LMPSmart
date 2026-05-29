# Copyright (c) 2025 Qiang Gan
# SPDX-License-Identifier: GPL-3.0-or-later
"""Animation plotting module for lmpsmart.

Supports 4 animation modes:
- isograph : 2D filled contour (tricontourf) animated over frames
- bar     : bar chart animated frame by frame
- line    : line plot animated frame by frame
- reacdraw: 3D molecular structure with bond breaking/forming animation
"""
from __future__ import annotations

import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.animation as manim
import seaborn as sns
import pandas as pd
import numpy as np
from typing import Literal, Sequence

from lmpsmart.arrange.config import load_config

__all__ = [
    "plot_animation",
    "plot_isograph",
    "plot_bar_animation",
    "plot_line_animation",
    "plot_reacdraw",
]


def _apply_style(dpi: int, width: int, high: int) -> None:
    """Apply lmpsmart standard plotting style."""
    sns.set_theme(style="ticks", font="Times New Roman", font_scale=1.3)
    plt.rcParams.update({
        "font.family": "serif",
        "font.serif": ["Times New Roman"],
        "axes.unicode_minus": False,
        "mathtext.fontset": "stix",
    })


def _parse_figsize(
    figsize: tuple[int, int] | str | None,
    default_width: int,
    default_high: int,
) -> tuple[int, int]:
    if figsize is None:
        return default_width, default_high
    if isinstance(figsize, str):
        w, h = figsize.split(",")
        return int(w.strip()), int(h.strip())
    return figsize[0], figsize[1]


# ---------------------------------------------------------------------------
# isograph — tricontourf animation
# ---------------------------------------------------------------------------

def plot_isograph(
    df: pd.DataFrame,
    output_path: str,
    x_col: str,
    y_col: str,
    z_col: str,
    frames: Sequence[int] | None = None,
    interval: int = 200,
    repeat: bool = False,
    figsize: tuple[int, int] | str | None = None,
    dpi: int | None = None,
    cmap: str = "rainbow",
    isoset: list[float] | None = None,
    title: str = "",
    xlabel: str = "",
    ylabel: str = "",
    zlabel: str = "",
    config_path: str | None = None,
) -> dict:
    """Plot animated 2D filled-contour (isograph) over simulation frames.

    Uses ``plt.tricontourf`` to render a 2D spatial property map per frame.
    Common for chunk maps, temperature maps, concentration profiles.

    Parameters
    ----------
    df : pd.DataFrame
        Must contain x_col, y_col, z_col, and a 'frame' column.
    output_path : str
        Save path — extension determines format (.html or .gif).
    x_col, y_col : str
        Coordinate columns (e.g. x, y positions).
    z_col : str
        Value column to colour by (e.g. temperature, density).
    frames : sequence of int, optional
        Which frames to animate. Defaults to all unique frames.
    interval : int
        Milliseconds between frames (default 200).
    repeat : bool
        Whether to loop the animation (default False).
    figsize : tuple or str
        Figure size, e.g. (10, 8) or "10,8".
    dpi : int
        Resolution. Defaults to config animationscale.dpi.
    cmap : str
        Matplotlib colormap name (default "rainbow").
    isoset : list of float, optional
        Contour levels. Auto-computed if None.
    title, xlabel, ylabel, zlabel : str
        Axis / title labels.
    """
    cfg = load_config(config_path)
    ps = cfg.plotset.animationscale
    w, h = _parse_figsize(figsize, ps.width, ps.high)
    dpi_val = dpi if dpi is not None else ps.dpi

    _apply_style(dpi_val, w, h)

    if frames is None:
        frames = sorted(df["frame"].unique())

    fig, ax = plt.subplots(figsize=(w, h), dpi=dpi_val)
    fig.subplots_adjust(left=0.15, right=0.85)

    # Compute axis limits once
    x_min, x_max = df[x_col].min(), df[x_col].max()
    y_min, y_max = df[y_col].min(), df[y_col].max()
    axislimit = [x_min, x_max, y_min, y_max]

    # Auto-compute contour levels if not given
    if isoset is None:
        z_vals = df[z_col].dropna()
        z_min, z_max = z_vals.min(), z_vals.max()
        isoset = np.linspace(z_min, z_max, 15)

    # Pre-build font property (Times New Roman)
    fontprops = None  # matplotlibrc handles font globally

    def init():
        ax.cla()
        ax.set_xlim(x_min, x_max)
        ax.set_ylim(y_min, y_max)
        ax.set_xlabel(xlabel, fontsize=ps.labelsize)
        ax.set_ylabel(ylabel, fontsize=ps.labelsize)
        return []

    def update(frame):
        ax.cla()
        frame_df = df[df["frame"] == frame].reset_index(drop=True)
        X = frame_df[x_col].values
        Y = frame_df[y_col].values
        Z = frame_df[z_col].values
        ax.tricontourf(X, Y, Z, levels=isoset, cmap=cmap)
        ax.set_xlim(x_min, x_max)
        ax.set_ylim(y_min, y_max)
        ax.set_xlabel(xlabel, fontsize=ps.labelsize)
        ax.set_ylabel(ylabel, fontsize=ps.labelsize)
        ax.tick_params(labelsize=ps.ticksize)
        if zlabel:
            cbar = fig.colorbar(cm.ScalarMappable(cmap=cmap), ax=ax)
            cbar.set_label(zlabel, fontsize=ps.labelsize)
            cbar.ax.tick_params(labelsize=ps.ticksize)
        if title:
            ax.set_title(title, fontsize=ps.labelsize)
        return []

    ani = manim.FuncAnimation(
        fig, update, frames=frames, init_func=init,
        interval=interval, repeat=repeat, blit=False,
    )
    _save_animation(ani, output_path, dpi_val)
    plt.close(fig)
    return {"status": "success", "output": output_path, "mode": "isograph", "frames": len(frames)}


# ---------------------------------------------------------------------------
# bar animation
# ---------------------------------------------------------------------------

def plot_bar_animation(
    df: pd.DataFrame,
    output_path: str,
    x_col: str,
    y_col: str,
    frames: Sequence[int] | None = None,
    interval: int = 200,
    repeat: bool = False,
    figsize: tuple[int, int] | str | None = None,
    dpi: int | None = None,
    barscale: float = 0.5,
    title: str = "",
    xlabel: str = "",
    ylabel: str = "",
    config_path: str | None = None,
) -> dict:
    """Plot animated bar chart over simulation frames.

    Suitable for species counts, histogram-type data evolving over time.
    """
    cfg = load_config(config_path)
    ps = cfg.plotset.animationscale
    w, h = _parse_figsize(figsize, ps.width, ps.high)
    dpi_val = dpi if dpi is not None else ps.dpi

    _apply_style(dpi_val, w, h)

    if frames is None:
        frames = sorted(df["frame"].unique())

    fig, ax = plt.subplots(figsize=(w, h), dpi=dpi_val)
    fig.subplots_adjust(left=0.15, bottom=0.15)

    x_min, x_max = df[x_col].min(), df[x_col].max()
    y_min, y_max = df[y_col].min(), df[y_col].max()
    axislimit = [x_min, x_max * 1.02, y_min, y_max * 1.02]

    def init():
        ax.cla()
        ax.set_xlim(axislimit[0], axislimit[1])
        ax.set_ylim(axislimit[2], axislimit[3])
        return []

    def update(frame):
        ax.cla()
        frame_df = df[df["frame"] == frame].reset_index(drop=True)
        x = frame_df[x_col].values
        y = frame_df[y_col].values
        ax.bar(x, y, width=barscale)
        ax.set_xlim(axislimit[0], axislimit[1])
        ax.set_ylim(axislimit[2], axislimit[3])
        ax.set_xlabel(xlabel, fontsize=ps.labelsize)
        ax.set_ylabel(ylabel, fontsize=ps.labelsize)
        ax.tick_params(labelsize=ps.ticksize)
        if title:
            ax.set_title(title, fontsize=ps.labelsize)
        return []

    ani = manim.FuncAnimation(
        fig, update, frames=frames, init_func=init,
        interval=interval, repeat=repeat, blit=False,
    )
    _save_animation(ani, output_path, dpi_val)
    plt.close(fig)
    return {"status": "success", "output": output_path, "mode": "bar", "frames": len(frames)}


# ---------------------------------------------------------------------------
# line animation
# ---------------------------------------------------------------------------

def plot_line_animation(
    df: pd.DataFrame,
    output_path: str,
    x_col: str,
    y_col: str,
    frames: Sequence[int] | None = None,
    interval: int = 200,
    repeat: bool = False,
    figsize: tuple[int, int] | str | None = None,
    dpi: int | None = None,
    title: str = "",
    xlabel: str = "",
    ylabel: str = "",
    config_path: str | None = None,
) -> dict:
    """Plot animated line chart over simulation frames.

    For time-series or property evolution where each frame is a snapshot.
    """
    cfg = load_config(config_path)
    ps = cfg.plotset.animationscale
    w, h = _parse_figsize(figsize, ps.width, ps.high)
    dpi_val = dpi if dpi is not None else ps.dpi

    _apply_style(dpi_val, w, h)

    if frames is None:
        frames = sorted(df["frame"].unique())

    fig, ax = plt.subplots(figsize=(w, h), dpi=dpi_val)
    fig.subplots_adjust(left=0.15, bottom=0.15)

    x_min, x_max = df[x_col].min(), df[x_col].max()
    y_min, y_max = df[y_col].min(), df[y_col].max()
    axislimit = [x_min, x_max, y_min, y_max]

    def init():
        ax.cla()
        ax.set_xlim(axislimit[0], axislimit[1])
        ax.set_ylim(axislimit[2], axislimit[3])
        return []

    def update(frame):
        ax.cla()
        frame_df = df[df["frame"] == frame].reset_index(drop=True)
        ax.plot(frame_df[x_col], frame_df[y_col], linewidth=2)
        ax.set_xlim(axislimit[0], axislimit[1])
        ax.set_ylim(axislimit[2], axislimit[3])
        ax.set_xlabel(xlabel, fontsize=ps.labelsize)
        ax.set_ylabel(ylabel, fontsize=ps.labelsize)
        ax.tick_params(labelsize=ps.ticksize)
        if title:
            ax.set_title(title, fontsize=ps.labelsize)
        return []

    ani = manim.FuncAnimation(
        fig, update, frames=frames, init_func=init,
        interval=interval, repeat=repeat, blit=False,
    )
    _save_animation(ani, output_path, dpi_val)
    plt.close(fig)
    return {"status": "success", "output": output_path, "mode": "line", "frames": len(frames)}


# ---------------------------------------------------------------------------
# reacdraw — 3D molecular structure animation
# ---------------------------------------------------------------------------

def plot_reacdraw(
    df: pd.DataFrame,
    output_path: str,
    frames: Sequence[int] | None = None,
    interval: int = 200,
    repeat: bool = False,
    figsize: tuple[int, int] | str | None = None,
    dpi: int | None = None,
    scatterscale: float = 1.0,
    title: str = "",
    xlabel: str = "X / Å",
    ylabel: str = "Y / Å",
    zlabel: str = "Z / Å",
    config_path: str | None = None,
) -> dict:
    """Plot animated 3D molecular structure with bond breaking/forming.

    Expects df with per-frame columns:
      idlist, xyz, elements, idbond, break, create

    where:
      xyz     : list of (x, y, z) tuples as strings (use eval on read)
      elements: list of element symbols
      idbond  : list of (id1, id2) atom-id pairs
      break   : list of start atoms whose bond is breaking
      create  : list of start atoms whose bond is forming

    Bond colouring:
      black — stable bond
      red   — breaking bond
      green — forming bond

    Uses mpl_toolkits.mplot3d.Axes3D.scatter for atoms and plot for bonds.
    """
    from mpl_toolkits.mplot3d import Axes3D

    cfg = load_config(config_path)
    ps = cfg.plotset.animationscale
    w, h = _parse_figsize(figsize, ps.width, ps.high)
    dpi_val = dpi if dpi is not None else ps.dpi

    _apply_style(dpi_val, w, h)

    if frames is None:
        frames = sorted(df["frame"].unique())

    # Element → colour map (C=C0, H=C1, N=C3, O=C4, Al=C5)
    _elem_color = {"C": "C0", "H": "C1", "N": "C3", "O": "C4", "Al": "C5"}

    fig = plt.figure(figsize=(w, h), dpi=dpi_val)
    ax = fig.add_subplot(111, projection="3d")

    def update(frame):
        ax.cla()
        frame_df = df[df["frame"] == frame].reset_index(drop=True)
        if frame_df.empty:
            return []

        row = frame_df.iloc[0]

        # Parse stored list columns
        idlist = row["idlist"]
        xyz_raw = row["xyz"]
        elelist = row["elements"]
        idbond = row["idbond"]
        breaks = row["break"] if "break" in row else []
        creates = row["create"] if "create" in row else []

        # Parse xyz if stored as string
        if isinstance(xyz_raw, str):
            import ast
            xyzlist = ast.literal_eval(xyz_raw)
        else:
            xyzlist = xyz_raw

        if isinstance(idlist, str):
            import ast
            idlist = ast.literal_eval(idlist)
        if isinstance(elelist, str):
            elelist = ast.literal_eval(elelist)
        if isinstance(idbond, str):
            idbond = ast.literal_eval(idbond)
        if isinstance(breaks, str):
            breaks = ast.literal_eval(breaks)
        if isinstance(creates, str):
            creates = ast.literal_eval(creates)

        if not xyzlist:
            return []

        # Build id→xyz dict
        iddict = {lid: xyz for lid, xyz in zip(idlist, xyzlist)}

        # Scatter atoms with element colours
        xs = [p[0] for p in xyzlist]
        ys = [p[1] for p in xyzlist]
        zs = [p[2] for p in xyzlist]
        colors = [_elem_color.get(e, "C0") for e in elelist]
        ax.scatter(xs, ys, zs, s=float(scatterscale), c=colors, marker="o", alpha=1)

        # Draw bonds with colour coding
        bond_color_map = {}
        for bond_pair in idbond:
            if len(bond_pair) < 2:
                continue
            p1, p2 = bond_pair[0], bond_pair[1]
            if p1 not in iddict or p2 not in iddict:
                continue
            pt1, pt2 = iddict[p1], iddict[p2]
            xline = [pt1[0], pt2[0]]
            yline = [pt1[1], pt2[1]]
            zline = [pt1[2], pt2[2]]
            # Determine colour
            start_key = (pt1[0], pt1[1], pt1[2])
            if start_key in breaks:
                col = "red"
            elif start_key in creates:
                col = "green"
            else:
                col = "black"
            ax.plot(xline, yline, zline, color=col, linewidth=2)

        ax.set_xlabel(xlabel, fontsize=ps.labelsize)
        ax.set_ylabel(ylabel, fontsize=ps.labelsize)
        ax.set_zlabel(zlabel, fontsize=ps.labelsize)
        ax.tick_params(labelsize=ps.ticksize)
        if title:
            time_val = frame_df.iloc[0].get("time", frame)
            ax.set_title(f"{title}  t={time_val:.4f} ps", fontsize=ps.labelsize)
        ax.relim()
        ax.autoscale_view()
        return []

    ani = manim.FuncAnimation(
        fig, update, frames=frames,
        interval=interval, repeat=repeat, blit=False,
    )
    _save_animation(ani, output_path, dpi_val)
    plt.close(fig)
    return {"status": "success", "output": output_path, "mode": "reacdraw", "frames": len(frames)}


# ---------------------------------------------------------------------------
# unified entry point
# ---------------------------------------------------------------------------

def plot_animation(
    df: pd.DataFrame,
    output_path: str,
    mode: Literal["isograph", "bar", "line", "reacdraw"],
    x_col: str,
    y_col: str,
    z_col: str | None = None,
    value_col: str | None = None,
    hue_col: str | None = None,
    frames: Sequence[int] | None = None,
    interval: int = 200,
    repeat: bool = False,
    figsize: tuple[int, int] | str | None = None,
    dpi: int | None = None,
    cmap: str = "rainbow",
    isoset: list[float] | None = None,
    barscale: float = 0.5,
    scatterscale: float = 1.0,
    title: str = "",
    xlabel: str = "",
    ylabel: str = "",
    zlabel: str = "",
    config_path: str | None = None,
) -> dict:
    """Unified animation plotting entry point.

    Dispatches to the appropriate animation function based on ``mode``.

    Parameters
    ----------
    mode : {"isograph", "bar", "line", "reacdraw"}
        Animation type:
        - ``"isograph"`` : 2D filled-contour animation (requires z_col)
        - ``"bar"``      : bar chart animation
        - ``"line"``     : line plot animation
        - ``"reacdraw"`` : 3D molecular structure animation
    x_col, y_col : str
        X and Y axis columns (used by isograph, bar, line).
    z_col : str, optional
        Z / value column for isograph mode.
    frames : sequence of int, optional
        Frame numbers to animate. Defaults to all unique frames.
    interval : int
        Milliseconds between frames (default 200).
    repeat : bool
        Loop animation (default False).
    cmap : str
        Colormap for isograph (default "rainbow").
    isoset : list of float, optional
        Contour levels for isograph.
    barscale : float
        Bar width scale (default 0.5).
    scatterscale : float
        Atom scatter size for reacdraw (default 1.0).
    """
    if mode == "isograph":
        if z_col is None:
            raise ValueError("isograph mode requires z_col")
        return plot_isograph(
            df, output_path, x_col, y_col, z_col,
            frames=frames, interval=interval, repeat=repeat,
            figsize=figsize, dpi=dpi, cmap=cmap, isoset=isoset,
            title=title, xlabel=xlabel, ylabel=ylabel, zlabel=zlabel,
            config_path=config_path,
        )
    elif mode == "bar":
        return plot_bar_animation(
            df, output_path, x_col, y_col,
            frames=frames, interval=interval, repeat=repeat,
            figsize=figsize, dpi=dpi, barscale=barscale,
            title=title, xlabel=xlabel, ylabel=ylabel,
            config_path=config_path,
        )
    elif mode == "line":
        return plot_line_animation(
            df, output_path, x_col, y_col,
            frames=frames, interval=interval, repeat=repeat,
            figsize=figsize, dpi=dpi,
            title=title, xlabel=xlabel, ylabel=ylabel,
            config_path=config_path,
        )
    elif mode == "reacdraw":
        return plot_reacdraw(
            df, output_path,
            frames=frames, interval=interval, repeat=repeat,
            figsize=figsize, dpi=dpi, scatterscale=scatterscale,
            title=title, xlabel=xlabel, ylabel=ylabel, zlabel=zlabel,
            config_path=config_path,
        )
    else:
        raise ValueError(f"Unknown animation mode: {mode!r}. Use isograph|bar|line|reacdraw.")


def _save_animation(ani: manim.FuncAnimation, output_path: str, dpi: int) -> None:
    """Save animation to HTML or GIF based on file extension."""
    lower = output_path.lower()
    if ".html" in lower:
        ani.save(output_path, writer=manim.HTMLWriter(), dpi=dpi)
    elif ".gif" in lower:
        try:
            ani.save(output_path, writer=manim.PillowWriter(), dpi=dpi)
        except Exception as e:
            raise RuntimeError(
                "GIF output requires pillow: pip install pillow"
            ) from e
    else:
        # Default to gif
        try:
            base, _ = output_path.rsplit(".", 1)
        except ValueError:
            base = output_path
        ani.save(f"{base}.gif", writer=manim.PillowWriter(), dpi=dpi)
