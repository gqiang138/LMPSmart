# Copyright (c) 2025 Qiang Gan
# SPDX-License-Identifier: GPL-3.0-or-later
"""Data cleaning tools for LAMMPS processing pipeline."""
from __future__ import annotations
import os
import pandas as pd


def groupby_aggregate(
    csv_path: str,
    group_col: str,
    agg_col: str,
    agg_func: str = "mean",
    output_path: str | None = None,
) -> dict:
    df = pd.read_csv(csv_path)
    if group_col not in df.columns:
        raise ValueError(f"Column '{group_col}' not found in {df.columns.tolist()}")
    if agg_col not in df.columns:
        raise ValueError(f"Column '{agg_col}' not found in {df.columns.tolist()}")
    valid_funcs = {"mean", "sum", "count", "min", "max", "std", "median"}
    if agg_func not in valid_funcs:
        raise ValueError(f"agg_func must be one of {valid_funcs}")
    grouped = df.groupby(group_col)[agg_col].agg(agg_func).reset_index()
    grouped.columns = [group_col, f"{agg_col}_{agg_func}"]
    if output_path is None:
        base, ext = os.path.splitext(csv_path)
        output_path = f"{base}_groupby_{agg_func}{ext}"
    grouped.to_csv(output_path, index=False)
    return {"output_path": output_path, "rows": len(grouped)}


def belong_filter(
    csv_path: str,
    col: str,
    values: list,
    keep: bool = True,
    output_path: str | None = None,
) -> dict:
    df = pd.read_csv(csv_path)
    if col not in df.columns:
        raise ValueError(f"Column '{col}' not found in {df.columns.tolist()}")
    mask = df[col].isin(values)
    if not keep:
        mask = ~mask
    filtered = df[mask]
    if output_path is None:
        base, ext = os.path.splitext(csv_path)
        output_path = f"{base}_filtered{ext}"
    filtered.to_csv(output_path, index=False)
    return {"output_path": output_path, "rows": len(filtered), "removed": len(df) - len(filtered)}


def column_rename(
    csv_path: str,
    rename_map: dict,
    output_path: str | None = None,
) -> dict:
    df = pd.read_csv(csv_path)
    df = df.rename(columns=rename_map)
    if output_path is None:
        base, ext = os.path.splitext(csv_path)
        output_path = f"{base}_renamed{ext}"
    df.to_csv(output_path, index=False)
    return {"output_path": output_path, "columns": list(df.columns)}


def select_columns(
    csv_path: str,
    columns: list[str],
    output_path: str | None = None,
) -> dict:
    df = pd.read_csv(csv_path)
    missing = [c for c in columns if c not in df.columns]
    if missing:
        raise ValueError(f"Columns {missing} not found in {df.columns.tolist()}")
    selected = df[columns]
    if output_path is None:
        base, ext = os.path.splitext(csv_path)
        output_path = f"{base}_selected{ext}"
    selected.to_csv(output_path, index=False)
    return {"output_path": output_path, "columns": columns, "rows": len(selected)}


def merge_data(
    csv_paths: list[str],
    how: str = "concat",
    on_col: str | None = None,
    output_path: str | None = None,
) -> dict:
    if not csv_paths:
        raise ValueError("csv_paths cannot be empty")
    if len(csv_paths) == 1:
        df = pd.read_csv(csv_paths[0])
        if output_path is None:
            base, ext = os.path.splitext(csv_paths[0])
            output_path = f"{base}_merged{ext}"
        df.to_csv(output_path, index=False)
        return {"output_path": output_path, "rows": len(df), "files": len(csv_paths)}
    if how == "concat":
        dfs = [pd.read_csv(p) for p in csv_paths]
        merged = pd.concat(dfs, ignore_index=True)
    elif how == "merge":
        if on_col is None:
            raise ValueError("on_col is required for merge mode")
        dfs = [pd.read_csv(p) for p in csv_paths]
        merged = dfs[0]
        for other in dfs[1:]:
            merged = pd.merge(merged, other, on=on_col, how="outer")
    else:
        raise ValueError("how must be 'concat' or 'merge'")
    if output_path is None:
        base, ext = os.path.splitext(csv_paths[0])
        output_path = f"{base}_merged{ext}"
    merged.to_csv(output_path, index=False)
    return {"output_path": output_path, "rows": len(merged), "files": len(csv_paths)}
