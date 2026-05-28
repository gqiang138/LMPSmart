# Copyright (c) 2025 Qiang Gan
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations
import numpy as np
import pandas as pd


def filter_zscore(series: pd.Series, threshold: float = 3.0) -> pd.Series:
    mean = series.mean()
    std = series.std(ddof=1)
    if std == 0:
        return pd.Series(True, index=series.index)
    z = np.abs((series - mean) / std)
    return z <= threshold


def filter_mad(series: pd.Series, threshold: float = 3.5) -> pd.Series:
    med = series.median()
    mad = 1.4826 * np.median(np.abs(series - med))
    if mad == 0:
        return pd.Series(True, index=series.index)
    mad_score = 0.6745 * (series - med) / mad
    return np.abs(mad_score) <= threshold


def filter_iqr(series: pd.Series, threshold: float = 1.5) -> pd.Series:
    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    iqr = q3 - q1
    lower = q1 - threshold * iqr
    upper = q3 + threshold * iqr
    return (series >= lower) & (series <= upper)


def filter_outliers(
    df: pd.DataFrame,
    time_col: str,
    value_col: str,
    methods: str | list[str] = "zscore",
    threshold: float = 3.0,
) -> pd.DataFrame:
    if isinstance(methods, str):
        methods = [methods]
    vals = df[value_col]
    mask = pd.Series(True, index=df.index)
    for method in methods:
        if method == "zscore":
            mask &= filter_zscore(vals, threshold)
        elif method == "mad":
            mask &= filter_mad(vals, threshold)
        elif method == "iqr":
            mask &= filter_iqr(vals, threshold)
    return df[mask].copy()
