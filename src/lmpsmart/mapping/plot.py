# Copyright (c) 2025 Qiang Gan
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations
import math
import re
from typing import Literal
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

DEFAULT_LABELS = {
    "time": r"Time/ps",
    "step": "Step",
    "frame": "Frame",
    "temp": r"Temperature/K",
    "temperature": r"Temperature/K",
    "press": r"Pressure/atm",
    "pressure": r"Pressure/atm",
    "toteng": r"Energy/(kcal$\cdot$mol$^{-1}$)",
    "poteng": r"Energy/(kcal$\cdot$mol$^{-1}$)",
    "kineng": r"Energy/(kcal$\cdot$mol$^{-1}$)",
    "e_vdwl": r"Energy/(kcal$\cdot$mol$^{-1}$)",
    "e_coul": r"Energy/(kcal$\cdot$mol$^{-1}$)",
    "e_long": r"Energy/(kcal$\cdot$mol$^{-1}$)",
    "pe": r"Energy/(kcal$\cdot$mol$^{-1}$)",
    "ke": r"Energy/(kcal$\cdot$mol$^{-1}$)",
    "energy": r"Energy/(kcal$\cdot$mol$^{-1}$)",
    "totale": r"Energy/(kcal$\cdot$mol$^{-1}$)",
    "total_energy": r"Energy/(kcal$\cdot$mol$^{-1}$)",
    "entropy": r"Entropy/(kcal$\cdot$mol$^{-1}\cdot$K$^{-1}$)",
    "density": r"Density/(g$\cdot$cm$^{-3}$)",
    "weight": r"Weight/(g$\cdot$cm$^{-3}$)",
    "lx": r"Cell length/Å",
    "ly": r"Cell length/Å",
    "lz": r"Cell length/Å",
    "a": r"Cell vector/Å",
    "b": r"Cell vector/Å",
    "c": r"Cell vector/Å",
    "a0": r"Cell vector/Å",
    "b0": r"Cell vector/Å",
    "c0": r"Cell vector/Å",
    "xy": r"Tilt factor/Å",
    "xz": r"Tilt factor/Å",
    "yz": r"Tilt factor/Å",
    "cella": r"Cell length/Å",
    "cellb": r"Cell length/Å",
    "cellc": r"Cell length/Å",
    "cellalpha": r"Angle/degree",
    "cellbeta": r"Angle/degree",
    "cellgamma": r"Angle/degree",
    "volume": r"Volume/Å$^3$",
    "x": r"Position/Å",
    "y": r"Position/Å",
    "z": r"Position/Å",
    "vx": r"Velocity/(Å$\cdot$fs$^{-1}$)",
    "vy": r"Velocity/(Å$\cdot$fs$^{-1}$)",
    "vz": r"Velocity/(Å$\cdot$fs$^{-1}$)",
    "vx_": r"Velocity/(Å$\cdot$fs$^{-1}$)",
    "vy_": r"Velocity/(Å$\cdot$fs$^{-1}$)",
    "vz_": r"Velocity/(Å$\cdot$fs$^{-1}$)",
    "fx": r"Force/(kcal$\cdot$mol$^{-1}\cdot$Å$^{-1}$)",
    "fy": r"Force/(kcal$\cdot$mol$^{-1}\cdot$Å$^{-1}$)",
    "fz": r"Force/(kcal$\cdot$mol$^{-1}\cdot$Å$^{-1}$)",
    "fx_": r"Force/(kcal$\cdot$mol$^{-1}\cdot$Å$^{-1}$)",
    "fy_": r"Force/(kcal$\cdot$mol$^{-1}\cdot$Å$^{-1}$)",
    "fz_": r"Force/(kcal$\cdot$mol$^{-1}\cdot$Å$^{-1}$)",
    "charge": r"Charge/$e$",
    "q": r"Charge/$e$",
    "number": "Number",
    "no_moles": "Moles",
    "no_specs": "Species count",
    "atoms": "Atom count",
    "nx": r"Position/Å",
    "ny": r"Position/Å",
    "nz": r"Position/Å",
    "c_ss": r"Stress$_{xx}$/atm",
    "c_ss_": r"Stress$_{xx}$/atm",
    "c_ss0": r"Stress$_{xx}$/atm",
    "px": r"Stress$_{xx}$/atm",
    "py": r"Stress$_{yy}$/atm",
    "pz": r"Stress$_{zz}$/atm",
    "pxx": r"Stress$_{xx}$/atm",
    "pyy": r"Stress$_{yy}$/atm",
    "pzz": r"Stress$_{zz}$/atm",
    "pxy": r"Stress$_{xy}$/atm",
    "pxz": r"Stress$_{xz}$/atm",
    "pyz": r"Stress$_{yz}$/atm",
    "bo": "Bond order",
    "bonds": "Bond count",
    "bocutoff": "Bond order cutoff",
    "blcutoff": r"Bond length cutoff/Å",
    "id1": "Atom ID",
    "id2": "Atom ID",
    "type1": "Atom type",
    "type2": "Atom type",
}


def _formula_to_mathtext(formula: str) -> str:
    matched = [(m.group(1), m.group(2), m.start(), m.end())
               for m in re.finditer(r"([A-Z][a-z]?)(\d+)", formula)]
    if not matched:
        return formula
    result = ""
    prev_end = 0
    for elem, num, start, end in matched:
        if start > prev_end:
            for ch in formula[prev_end:start]:
                result += rf"\mathrm{{{ch}}}"
        result += rf"\mathrm{{{elem}}}" + f"_{{{num}}}"
        prev_end = end
    if prev_end < len(formula):
        for ch in formula[prev_end:]:
            result += rf"\mathrm{{{ch}}}"
    return f"${result}$"


def _default_label(col: str) -> str:
    col_lower = col.lower().strip()
    if col_lower in DEFAULT_LABELS:
        return DEFAULT_LABELS[col_lower]
    if col_lower.startswith("c_"):
        return f"{col} / (user-defined)"
    return col


def _legend_params(loc: str, frameon: bool = False, fontsize: int | None = None):
    kwargs = {"loc": loc, "frameon": frameon}
    if fontsize:
        kwargs["fontsize"] = fontsize
    return kwargs


def plot_dataframe(
    df: pd.DataFrame,
    x_col: str,
    y_cols: list[str],
    output_path: str,
    mode: Literal["single", "multi", "doubley"] = "single",
    plotset=None,
    hue_col: str | None = None,
    title: str = "",
    xlabel: str = "",
    ylabel: str = "",
    figsize: tuple[int, int] | None = None,
    dpi: int | None = None,
    legend_loc: str = "best",
    markers: bool = False,
    subscript_labels: bool = False,
    legend_type: Literal["auto", "list", "remove", "suffix"] = "auto",
    legend_labels: list[str] | None = None,
    legend_suffix: str = "",
    yerr_col: str | None = None,
) -> None:
    if plotset is None:
        plotset = _default_plotset()

    if mode == "single":
        ps = plotset.singlescale
    elif mode == "doubley":
        ps = plotset.doubleyscale
    else:
        ps = plotset.multifig

    sns.set_theme(style=ps.sns_style, font="Times New Roman", font_scale=ps.fontscale)
    plt.rcParams.update({
        "font.family": "serif",
        "font.serif": ["Times New Roman", "SimSun", "FangSong", "SimHei"],
        "font.size": ps.ticksize,
        "axes.unicode_minus": False,
        "mathtext.fontset": "stix",
    })

    width = figsize[0] if figsize else ps.width
    high = figsize[1] if figsize else ps.high
    dpi_val = dpi if dpi else ps.dpi
    palette = ps.palette or "tab10"
    num_figs = len(y_cols)

    if mode == "single":
        fig, ax = plt.subplots(1, 1, figsize=(width, high), dpi=dpi_val)
        axes = [ax]
    elif mode == "multi":
        cols = 2
        rows = math.ceil(num_figs / cols)
        fig, axes = plt.subplots(rows, cols, figsize=(width, rows * high), dpi=dpi_val)
        axes = list(axes.flatten()[:num_figs])
    else:  # doubley
        fig, ax = plt.subplots(1, 1, figsize=(width, high), dpi=dpi_val)
        axes = [ax]

    fig.subplots_adjust(wspace=ps.subadjust_wspace, hspace=ps.subadjust_hspace)
    markers_list = ["o", "s", "^", "D", "v", "p", "h", "*"] if markers else None

    yerr_map: dict[str, str | None] = {}
    if yerr_col and yerr_col in df.columns:

        for y_col in y_cols:
            candidates = [
                yerr_col,
                y_col + "_std",
                y_col.rsplit("_", 1)[0] + "_std" if "_" in y_col else y_col + "_std",
            ]
            for cand in candidates:
                if cand in df.columns:
                    yerr_map[y_col] = cand
                    break
            else:
                yerr_map[y_col] = None

    for idx, y_col in enumerate(y_cols):
        ax = axes[idx] if mode == "multi" else axes[0]
        if y_col not in df.columns:
            continue

        has_hue = bool(hue_col and hue_col in df.columns)
        has_yerr = yerr_map.get(y_col) is not None

        marker_val = markers_list[idx] if markers else None
        extra_kwargs = {}
        if not has_hue:
            extra_kwargs["legend"] = True
            extra_kwargs["label"] = y_col
        sns.lineplot(
            data=df,
            x=x_col,
            y=y_col,
            linewidth=2.5,
            dashes=False,
            palette=palette if has_hue else None,
            sort=True,
            errorbar=None,
            markers=marker_val,
            ax=ax,
            **({"hue": hue_col} if has_hue else {}),
            **extra_kwargs,
        )

        if has_yerr:
            err_col = yerr_map[y_col]
            ax.errorbar(
                df[x_col], df[y_col], yerr=df[err_col],
                fmt="none", ecolor="gray", elinewidth=1, capsize=2,
                zorder=0, ax=ax,
            )

        if mode == "multi":
            x_label = xlabel if xlabel else _default_label(x_col)
            ax.set_xlabel(x_label, fontsize=ps.labelsize)
            y_label = ylabel if ylabel else _default_label(y_col)
            if subscript_labels:
                y_label = _formula_to_mathtext(y_label)
            ax.set_ylabel(y_label, fontsize=ps.labelsize)

    # Set axis labels once (shared for single/doubley modes; per-axis done inside loop for multi)
    if mode != "multi":
        x_label = xlabel if xlabel else _default_label(x_col)
        ax.set_xlabel(x_label, fontsize=ps.labelsize)
        if not ylabel:
            if len(y_cols) == 1:
                y_label = _default_label(y_cols[0])
            else:
                y_label = r"Position/Å"
            if subscript_labels:
                y_label = _formula_to_mathtext(y_label)
        else:
            y_label = ylabel
            if subscript_labels:
                y_label = _formula_to_mathtext(y_label)
        ax.set_ylabel(y_label, fontsize=ps.labelsize)

    ax.tick_params(labelsize=ps.ticksize)
    if title:
        ax.set_title(title, fontsize=ps.labelsize)

    should_show_legend = (
        (hue_col and hue_col in df.columns) or len(y_cols) > 1 or
        legend_type in ("list", "remove", "suffix")
    )

    if should_show_legend:
        handles, labels = ax.get_legend_handles_labels()

        if legend_type == "remove":
            ax.legend().remove()
        elif legend_type == "list" and legend_labels:
            ax.legend(handles, legend_labels, **_legend_params(legend_loc, frameon=False))
        elif legend_type == "suffix":
            final = [_formula_to_mathtext(l) + legend_suffix for l in labels] if subscript_labels else [l + legend_suffix for l in labels]
            ax.legend(handles, final, **_legend_params(legend_loc, frameon=False))
        elif legend_type == "auto":
            if labels:
                final_labels = labels
                if subscript_labels:
                    final_labels = [_formula_to_mathtext(l) for l in labels]
                ax.legend(handles, final_labels, **_legend_params(legend_loc, frameon=False))

    if mode == "multi" and len(y_cols) < len(axes):
        for idx in range(len(y_cols), len(axes)):
            axes[idx].set_visible(False)

    fig.savefig(output_path, dpi=dpi_val, bbox_inches="tight")
    plt.close(fig)


def _default_plotset():
    from lmpsmart.arrange.config import PlotSet, PlotSetSingle, PlotSetDoubleY
    return PlotSet(
        multifig=PlotSetSingle(width=14, high=6, dpi=600, labelsize=20, ticksize=18, fontscale=1.5,
                               subadjust_wspace=0.2, subadjust_hspace=0.2, sns_style="ticks", palette="tab10"),
        singlescale=PlotSetSingle(width=8, high=6, dpi=600, labelsize=16, ticksize=14, fontscale=1.5,
                                  subadjust_wspace=0.2, subadjust_hspace=0.2, sns_style="ticks", palette="tab10"),
        doubleyscale=PlotSetDoubleY(width=10, high=6, dpi=600, labelsize=16, ticksize=14, fontscale=1.5,
                                    sns_style="ticks", palette="tab10"),
        sns_style="ticks",
        palette="tab10",
    )
