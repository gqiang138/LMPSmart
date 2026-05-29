# Copyright (c) 2025 Qiang Gan
# SPDX-License-Identifier: GPL-3.0-or-later
"""18 Tool interfaces for lmpsmart Agent."""
from __future__ import annotations
import gc
import os
from pathlib import Path
from typing import Any
import pandas as pd
from lmpsmart.arrange.config import load_config
from lmpsmart.arrange.readers import (
    read_data, read_log, read_bonds, read_dump,
    read_cell, read_species, read_pos, read_ovito, read_general,
    arrange,
)
from lmpsmart.mapping.smooth import smooth, AVAILABLE_METHODS
from lmpsmart.mapping.filter import filter_outliers, filter_zscore, filter_mad, filter_iqr
from lmpsmart.mapping.fit import fit as fit_data
from lmpsmart.mapping.plot import plot_dataframe as tool_plot_dataframe
from lmpsmart.mapping.advanced_plot import (
    plot_boxplot as tool_plot_boxplot, plot_violin as tool_plot_violin,
    plot_scatter as tool_plot_scatter, plot_surface as tool_plot_surface,
    plot_contour as tool_plot_contour, plot_heatmap as tool_plot_heatmap,
)
from lmpsmart.mapping.animation import plot_animation as tool_plot_animation
from lmpsmart.mapping.clean import (
    groupby_aggregate, belong_filter,
    column_rename, select_columns, merge_data,
)
from lmpsmart.core.tools import (
    ELEMENT_WEIGHT, ELEMENT_ATOMIC, ELEMENT_MASS,
    atom_type, atom_order, type_atom, find_elements,
    molecular_weight, detect_encoding, autocode, folderfilter, filefilter,
)
from lmpsmart.api.logging import ExecutionLogger

_logger: ExecutionLogger | None = None


def get_logger() -> ExecutionLogger:
    global _logger
    if _logger is None:
        _logger = ExecutionLogger()
    return _logger


def _step(msg: str) -> list[str]:
    return [msg]


# arrange tools (2)
def tool_arrange(
    input_path: str,
    modes: list[str],
    output_path: str | None = None,
    config_path: str | None = None,
    ignored_time: float = 0.0,
    timestep: float = 0.1,
    encoding: str = "utf-8",
    supercell: str | None = None,
    log_indices: list[int] | None = None,
) -> dict[str, Any]:
    logger = get_logger()
    sc = None
    if supercell:
        parts = supercell.split(",")
        sc = tuple(int(p.strip()) for p in parts)
    steps = _step(f"arrange: modes={modes}, path={input_path}")
    cfg = load_config(config_path) if config_path else None
    try:
        result, out_dir = arrange(
            input_path=input_path, modes=modes, output_path=output_path,
            config=cfg, ignored_time=ignored_time, timestep=timestep,
            encoding=encoding, supercell=sc, log_indices=log_indices,
        )
        gc.collect()
        # Build CSV file paths from modes and output directory
        prefix_map = {
            "Log": "dataoflog", "Bonds": "dataofbonds", "Dump": "dataofdump",
            "Cell": "dataofcell", "Species": "dataofspecies",
            "POS": "dataofpos", "OVITO": "dataofovito", "General": "dataofgeneral",
        }
        csv_files = [
            f"{out_dir}/{prefix_map.get(m, 'dataof' + m.lower())}.csv"
            for m in modes
        ]
        logger.log("arrange", {"input_path": input_path, "modes": modes}, steps, result, status="success")
        return {"status": "success", "output_dir": out_dir, "files": csv_files, "outputs": result}
    except Exception as e:
        logger.log("arrange", {"input_path": input_path, "modes": modes}, steps, None, [str(e)], "failed")
        raise


def tool_load_config(config_path: str | None = None) -> dict[str, Any]:
    cfg = load_config(config_path)
    steps = _step(f"load_config: {config_path or 'default'}")
    get_logger().log("load_config", {"config_path": config_path}, steps, {"cutoff_keys": cfg.cutoff.bonds[:5]}, status="success")
    return {
        "status": "success",
        "cutoff_bonds": cfg.cutoff.bonds,
        "bocutoff": cfg.cutoff.bocutoff,
        "blcutoff": cfg.cutoff.blcutoff,
        "filerule1": cfg.filerule1.model_dump(),
    }


# read tools (8)
def tool_read_log(log_path: str, log_indices: list[int] | None = None, supercell: str | None = None,
                   ignored_time: float = 0.0, timestep: float = 0.1) -> pd.DataFrame:
    sc = None
    if supercell:
        sc = tuple(int(p.strip()) for p in supercell.split(","))
    steps = _step(f"read_log: {log_path}")
    df = read_log(log_path, log_indices, sc, ignored_time, timestep)
    get_logger().log("read_log", {"log_path": log_path}, steps, df, status="success")
    return df


def tool_read_bonds(bonds_path: str, data_path: str | None = None,
                     ignored_time: float = 0.0, timestep: float = 0.1) -> pd.DataFrame:
    steps = _step(f"read_bonds: {bonds_path}")
    df = read_bonds(bonds_path, data_path, None, None, ignored_time, timestep)
    get_logger().log("read_bonds", {"bonds_path": bonds_path}, steps, df, status="success")
    return df


def tool_read_dump(dump_path: str, data_path: str | None = None,
                    ignored_time: float = 0.0, timestep: float = 0.1) -> pd.DataFrame:
    steps = _step(f"read_dump: {dump_path}")
    df = read_dump(dump_path, data_path, None, ignored_time, timestep)
    get_logger().log("read_dump", {"dump_path": dump_path}, steps, df, status="success")
    return df


def tool_read_data(data_path: str) -> dict[str, pd.DataFrame]:
    steps = _step(f"read_data: {data_path}")
    result = read_data(data_path)
    get_logger().log("read_data", {"data_path": data_path}, steps, result, status="success")
    return result


def tool_read_cell(dump_path: str, ignored_time: float = 0.0, timestep: float = 0.1) -> pd.DataFrame:
    steps = _step(f"read_cell: {dump_path}")
    df = read_cell(dump_path, ignored_time, timestep)
    get_logger().log("read_cell", {"dump_path": dump_path}, steps, df, status="success")
    return df


def tool_read_species(species_path: str, ignored_time: float = 0.0, timestep: float = 0.1) -> pd.DataFrame:
    steps = _step(f"read_species: {species_path}")
    df = read_species(species_path, ignored_time, timestep)
    get_logger().log("read_species", {"species_path": species_path}, steps, df, status="success")
    return df


def tool_read_pos(pos_path: str, ignored_time: float = 0.0, timestep: float = 0.1) -> pd.DataFrame:
    steps = _step(f"read_pos: {pos_path}")
    df = read_pos(pos_path, ignored_time, timestep)
    get_logger().log("read_pos", {"pos_path": pos_path}, steps, df, status="success")
    return df


def tool_read_general(file_path: str, sep: str | None = None, header: int | None = None) -> pd.DataFrame:
    steps = _step(f"read_general: {file_path}")
    df = read_general(file_path, sep, header)
    get_logger().log("read_general", {"file_path": file_path}, steps, df, status="success")
    return df


# mapping tools (4)
def tool_smooth(data: list[float] | pd.Series, method: str = "moving_avg", **kwargs) -> list[float]:
    steps = _step(f"smooth: method={method}")
    if method not in AVAILABLE_METHODS:
        raise ValueError(f"method must be one of {AVAILABLE_METHODS}")
    result = smooth(data, method=method, **kwargs)
    get_logger().log("smooth", {"method": method, "kwargs": kwargs}, steps, result, status="success")
    return result


def tool_filter_outliers(df: pd.DataFrame, time_col: str, value_col: str,
                          methods: str | list[str] = "zscore", threshold: float = 3.0) -> pd.DataFrame:
    steps = _step(f"filter_outliers: methods={methods}, threshold={threshold}")
    result = filter_outliers(df, time_col, value_col, methods, threshold)
    get_logger().log("filter_outliers", {"time_col": time_col, "value_col": value_col, "methods": methods},
                     steps, result, status="success")
    return result


def tool_fit(
    x_data: list[float] | pd.Series,
    y_data: list[float] | pd.Series,
    method: str = "polyfit",
    degree: int = 2,
    frac: float = 0.3,
) -> dict:
    steps = _step(f"fit: method={method}")
    result = fit_data(x_data, y_data, method=method, degree=degree, frac=frac)
    get_logger().log("fit", {"method": method, "degree": degree}, steps, result, status="success")
    return result


def tool_plot(
    csv_path: str,
    x_col: str,
    y_cols: list[str],
    output_path: str | None = None,
    mode: str = "single",
    hue_col: str | None = None,
    markers: bool = False,
    legend_loc: str = "best",
    subscript: bool = False,
    config_path: str | None = None,
    title: str = "",
    xlabel: str = "",
    ylabel: str = "",
    figsize: tuple[int, int] | str | None = None,
    dpi: int | None = None,
    plot_type: str = "line",
    size_col: str | None = None,
    color_col: str | None = None,
    cmap: str = "tab10",
    levels: int = 20,
    filled: bool = True,
    annot: bool = False,
    elev: int = 30,
    azim: int = 45,
    legend_type: str = "auto",
    legend_labels: list[str] | None = None,
    legend_suffix: str = "",
    yerr_col: str | None = None,
) -> dict:
    from lmpsmart.arrange.config import load_config
    cfg = load_config(config_path) if config_path else None
    if output_path is None:
        # Infer case folder from csv_path: if it contains /arrange/ → plot goes to sibling /plot/
        p = Path(csv_path)
        if "/arrange/" in csv_path.replace("\\", "/") or "/output/" in csv_path.replace("\\", "/"):
            case_root = p.parent.parent  # step up from /arrange/ or /output/<name>/
            plot_root = case_root / "plot"
        else:
            plot_root = Path("output/plot")
        output_path = str(plot_root / "plot1.png")
    steps = _step(f"plot: x={x_col}, y={y_cols}")
    df = pd.read_csv(csv_path)
    fig_tuple: tuple[int, int] | None = None
    if figsize is not None:
        if isinstance(figsize, str):
            w, h = figsize.split(",")
            fig_tuple = (int(w.strip()), int(h.strip()))
        else:
            fig_tuple = figsize

    # Dispatch on plot_type
    if plot_type == "line":
        tool_plot_dataframe(
            df,
            x_col=x_col,
            y_cols=y_cols,
            output_path=output_path,
            mode=mode,
            plotset=cfg.plotset if cfg else None,
            hue_col=hue_col,
            markers=markers,
            legend_loc=legend_loc,
            subscript_labels=subscript,
            title=title,
            xlabel=xlabel,
            ylabel=ylabel,
            figsize=fig_tuple,
            dpi=dpi,
            legend_type=legend_type,
            legend_labels=legend_labels,
            legend_suffix=legend_suffix,
            yerr_col=yerr_col,
        )
    elif plot_type == "scatter":
        for yc in y_cols:
            tool_plot_scatter(
                df=df, output_path=output_path,
                x_col=x_col, y_col=yc,
                size_col=size_col, color_col=color_col,
                hue_col=hue_col, title=title,
                xlabel=xlabel, ylabel=ylabel,
                figsize=fig_tuple, dpi=dpi,
                palette=cmap, markers=markers,
                legend_loc=legend_loc,
            )
    elif plot_type == "boxplot":
        for yc in y_cols:
            tool_plot_boxplot(
                df=df, output_path=output_path,
                x_col=x_col, y_col=yc,
                hue_col=hue_col, title=title,
                xlabel=xlabel, ylabel=ylabel,
                figsize=fig_tuple, dpi=dpi,
                palette=cmap, legend_loc=legend_loc,
            )
    elif plot_type == "violin":
        for yc in y_cols:
            tool_plot_violin(
                df=df, output_path=output_path,
                x_col=x_col, y_col=yc,
                hue_col=hue_col, title=title,
                xlabel=xlabel, ylabel=ylabel,
                figsize=fig_tuple, dpi=dpi,
                palette=cmap, legend_loc=legend_loc,
            )
    elif plot_type == "surface":
        tool_plot_surface(
            df=df, output_path=output_path,
            x_col=x_col, y_col=y_cols[0], z_col=y_cols[1] if len(y_cols) > 1 else y_cols[0],
            cmap=cmap, title=title,
            xlabel=xlabel, ylabel=ylabel,
            figsize=fig_tuple, dpi=dpi,
            elev=elev, azim=azim,
        )
    elif plot_type == "contour":
        tool_plot_contour(
            df=df, output_path=output_path,
            x_col=x_col, y_col=y_cols[0], z_col=y_cols[1] if len(y_cols) > 1 else y_cols[0],
            levels=levels, cmap=cmap, filled=filled,
            title=title, xlabel=xlabel, ylabel=ylabel,
            figsize=fig_tuple, dpi=dpi,
        )
    elif plot_type == "heatmap":
        tool_plot_heatmap(
            df=df, output_path=output_path,
            x_col=x_col, y_col=y_cols[0], value_col=y_cols[1] if len(y_cols) > 1 else y_cols[0],
            cmap=cmap, annot=annot,
            title=title, figsize=fig_tuple, dpi=dpi,
        )
    else:
        raise ValueError(f"Unknown plot_type: {plot_type!r}")

    # Export plot data CSV alongside the figure (same name, .csv extension)
    csv_out = Path(output_path).with_suffix(".csv")
    os.makedirs(csv_out.parent, exist_ok=True)
    df[[x_col] + y_cols].to_csv(csv_out, index=False)

    get_logger().log("plot", {"x_col": x_col, "y_cols": y_cols, "plot_type": plot_type}, steps, {"output": output_path, "csv": str(csv_out)}, status="success")
    return {"status": "success", "output": output_path, "csv": str(csv_out)}


def tool_animation(
    csv_path: str,
    mode: str,
    x_col: str,
    y_col: str,
    z_col: str | None = None,
    value_col: str | None = None,
    hue_col: str | None = None,
    output_path: str | None = None,
    config_path: str | None = None,
    interval: int = 200,
    frames: list[int] | None = None,
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
) -> dict:
    from lmpsmart.arrange.config import load_config
    cfg = load_config(config_path) if config_path else None
    if output_path is None:
        p = Path(csv_path)
        if "/arrange/" in csv_path.replace("\\", "/") or "/output/" in csv_path.replace("\\", "/"):
            case_root = p.parent.parent
            anim_root = case_root / "animation"
        else:
            anim_root = Path("output/animation")
        output_path = str(anim_root / "animation.gif")
    steps = _step(f"animation: mode={mode}, x={x_col}, y={y_col}")
    df = pd.read_csv(csv_path)
    fig_tuple: tuple[int, int] | None = None
    if figsize is not None:
        if isinstance(figsize, str):
            w, h = figsize.split(",")
            fig_tuple = (int(w.strip()), int(h.strip()))
        else:
            fig_tuple = figsize
    result = tool_plot_animation(
        df=df,
        output_path=output_path,
        mode=mode,
        x_col=x_col,
        y_col=y_col,
        z_col=z_col,
        value_col=value_col,
        hue_col=hue_col,
        frames=frames,
        interval=interval,
        repeat=repeat,
        figsize=fig_tuple,
        dpi=dpi,
        cmap=cmap,
        isoset=isoset,
        barscale=barscale,
        scatterscale=scatterscale,
        title=title,
        xlabel=xlabel,
        ylabel=ylabel,
        zlabel=zlabel,
        config_path=config_path,
    )
    # Export animation data CSV alongside the figure (same name, .csv extension)
    cols = [x_col, y_col]
    if z_col:
        cols.append(z_col)
    if value_col:
        cols.append(value_col)
    if output_path:
        csv_out = Path(output_path).with_suffix(".csv")
        os.makedirs(csv_out.parent, exist_ok=True)
        df[[c for c in cols if c in df.columns]].to_csv(csv_out, index=False)
        result["csv"] = str(csv_out)
    get_logger().log("animation", {"mode": mode, "x_col": x_col, "y_col": y_col}, steps, result, status="success")
    return result


def tool_groupby_aggregate(
    csv_path: str,
    group_col: str,
    agg_col: str,
    agg_func: str = "mean",
    output_path: str | None = None,
) -> dict:
    steps = _step(f"groupby_aggregate: {group_col}.{agg_col}.{agg_func}")
    result = groupby_aggregate(csv_path, group_col, agg_col, agg_func, output_path)
    get_logger().log("groupby_aggregate", {"group_col": group_col, "agg_col": agg_col},
                     steps, result, status="success")
    return {"status": "success", **result}


def tool_belong_filter(
    csv_path: str,
    col: str,
    values: list,
    keep: bool = True,
    output_path: str | None = None,
) -> dict:
    steps = _step(f"belong_filter: {col} in {values}")
    result = belong_filter(csv_path, col, values, keep, output_path)
    get_logger().log("belong_filter", {"col": col, "values": values}, steps, result, status="success")
    return {"status": "success", **result}


def tool_column_rename(
    csv_path: str,
    rename_map: dict,
    output_path: str | None = None,
) -> dict:
    steps = _step(f"column_rename: {rename_map}")
    result = column_rename(csv_path, rename_map, output_path)
    get_logger().log("column_rename", {"rename_map": rename_map}, steps, result, status="success")
    return {"status": "success", **result}


def tool_select_columns(
    csv_path: str,
    columns: list[str],
    output_path: str | None = None,
) -> dict:
    steps = _step(f"select_columns: {columns}")
    result = select_columns(csv_path, columns, output_path)
    get_logger().log("select_columns", {"columns": columns}, steps, result, status="success")
    return {"status": "success", **result}


def tool_merge_data(
    csv_paths: list[str],
    how: str = "concat",
    on_col: str | None = None,
    output_path: str | None = None,
) -> dict:
    steps = _step(f"merge_data: {len(csv_paths)} files, how={how}")
    result = merge_data(csv_paths, how, on_col, output_path)
    get_logger().log("merge_data", {"how": how, "files": len(csv_paths)}, steps, result, status="success")
    return {"status": "success", **result}


# chem tools (5)
def tool_molecular_weight(formula: str) -> float:
    steps = _step(f"molecular_weight: {formula}")
    mw = molecular_weight(formula)
    get_logger().log("molecular_weight", {"formula": formula}, steps, mw, status="success")
    return mw


def tool_find_elements(formula_str: str) -> list[str]:
    steps = _step(f"find_elements: {formula_str}")
    elems = find_elements(formula_str)
    get_logger().log("find_elements", {"formula_str": formula_str}, steps, elems, status="success")
    return elems


def tool_atom_type(mass_value: float) -> str:
    steps = _step(f"atom_type: mass={mass_value}")
    elem = atom_type(mass_value)
    get_logger().log("atom_type", {"mass_value": mass_value}, steps, elem, status="success")
    return elem


def tool_detect_encoding(file_path: str) -> str:
    steps = _step(f"detect_encoding: {file_path}")
    enc = detect_encoding(file_path)
    get_logger().log("detect_encoding", {"file_path": file_path}, steps, enc, status="success")
    return enc


def tool_autocode(file_path: str, sep: str | None = None, header: int | None = None) -> pd.DataFrame:
    steps = _step(f"autocode: {file_path}")
    df = autocode(file_path, sep=sep, header=header)
    get_logger().log("autocode", {"file_path": file_path}, steps, df, status="success")
    return df


TOOL_REGISTRY = {
    "arrange": tool_arrange,
    "load_config": tool_load_config,
    "read_log": tool_read_log,
    "read_bonds": tool_read_bonds,
    "read_dump": tool_read_dump,
    "read_data": tool_read_data,
    "read_cell": tool_read_cell,
    "read_species": tool_read_species,
    "read_pos": tool_read_pos,
    "read_general": tool_read_general,
    "smooth": tool_smooth,
    "filter_outliers": tool_filter_outliers,
    "fit": tool_fit,
    "plot": tool_plot,
    "animation": tool_animation,
    "groupby_aggregate": tool_groupby_aggregate,
    "belong_filter": tool_belong_filter,
    "column_rename": tool_column_rename,
    "select_columns": tool_select_columns,
    "merge_data": tool_merge_data,
    "molecular_weight": tool_molecular_weight,
    "find_elements": tool_find_elements,
    "atom_type": tool_atom_type,
    "detect_encoding": tool_detect_encoding,
    "autocode": tool_autocode,
}
