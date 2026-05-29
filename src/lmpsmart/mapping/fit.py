# Copyright (c) 2025 Qiang Gan
# SPDX-License-Identifier: GPL-3.0-or-later
"""Curve fitting for LAMMPS time-series data."""
from __future__ import annotations
import numpy as np
import pandas as pd


def polyfit(x, y, degree=2):
    """
    Polynomial fit y = f(x).

    Parameters
    ----------
    x, y : list or array
        Data points.
    degree : int
        Polynomial degree (default 2).

    Returns
    -------
    dict with keys: coef (list), r2 (float), fitted (list)
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    coef = np.polyfit(x, y, degree)
    poly = np.poly1d(coef)
    y_fit = poly(x)
    ss_res = np.sum((y - y_fit) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r2 = 1.0 if ss_tot == 0.0 else 1.0 - ss_res / ss_tot
    return {
        "coef": coef.tolist(),
        "r2": float(r2),
        "fitted": y_fit.tolist(),
    }


def lowess_fit(x, y, frac=0.3):
    """
    LOWESS local regression fit.

    Parameters
    ----------
    x, y : list or array
        Data points.
    frac : float
        Fraction of data used for each local regression.

    Returns
    -------
    dict with keys: x (list), y (list), r2 (float)
    """
    from statsmodels.nonparametric.smoothers_lowess import lowess as sm_lowess
    x_arr = np.asarray(x, dtype=float)
    y_arr = np.asarray(y, dtype=float)
    result = sm_lowess(y_arr, x_arr, frac=frac, is_sorted=False, return_sorted=False)
    y_smooth = result[:, 1]
    ss_res = np.sum((y_arr - y_smooth) ** 2)
    ss_tot = np.sum((y_arr - np.mean(y_arr)) ** 2)
    r2 = 1.0 if ss_tot == 0.0 else 1.0 - ss_res / ss_tot
    return {
        "x": x_arr.tolist(),
        "y": y_smooth.tolist(),
        "r2": float(r2),
    }


def fit(x, y, method="polyfit", **kwargs):
    """
    Unified fitting entry point.

    Parameters
    ----------
    x, y : list/array/DataFrame column/Series
        Independent and dependent variables.
    method : str
        "polyfit" (default) or "lowess".
    **kwargs
        For polyfit: degree (default 2)
        For lowess: frac (default 0.3)

    Returns
    -------
    dict with status, method, and fit result
    """
    if hasattr(x, "values"):
        x = x.values
    if hasattr(y, "values"):
        y = y.values
    x = np.asarray(x, dtype=float).flatten()
    y = np.asarray(y, dtype=float).flatten()
    if len(x) != len(y):
        raise ValueError(f"x and y must have same length, got {len(x)} and {len(y)}")
    if method == "lowess":
        result = lowess_fit(x, y, frac=kwargs.get("frac", 0.3))
    else:
        result = polyfit(x, y, degree=kwargs.get("degree", 2))
    return {"status": "success", "method": method, **result}
