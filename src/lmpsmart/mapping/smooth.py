# Copyright (c) 2025 Qiang Gan
# SPDX-License-Identifier: GPL-3.0-or-later
"""Smoothing algorithms for LAMMPS time-series data."""
from __future__ import annotations
import numpy as np
import pandas as pd
from scipy.signal import savgol_filter, butter, filtfilt
from scipy.interpolate import UnivariateSpline
from statsmodels.nonparametric.smoothers_lowess import lowess
import pywt


def smooth(data, method="moving_avg", **kwargs):
    if hasattr(data, "values"):
        orig_index = data.index
        orig_name = getattr(data, "name", None)
        data = data.values
    elif not isinstance(data, (list, np.ndarray)):
        raise ValueError("Input must be list, numpy array or pandas Series")
    else:
        orig_index = None
        orig_name = None

    if len(data) < 2:
        return pd.Series(data, index=orig_index, name=orig_name) if orig_index is not None else list(data) if isinstance(data, list) else data

    data = np.asarray(data, dtype=float)

    if method == "segment_spline":
        threshold = kwargs.get("spline_threshold", 0.2)
        s = kwargs.get("spline_s", 0.5)
        grad = np.gradient(data)
        std_grad = np.std(grad)
        break_points = np.where(np.abs(grad) > threshold * std_grad)[0]
        x = np.arange(len(data))
        if len(break_points) > 0:
            spl = UnivariateSpline(x, data, k=3, s=s)
            smoothed = spl(x)
        else:
            smoothed = data

    elif method == "adaptive_kalman":
        from pykalman import KalmanFilter
        process_noise = kwargs.get("process_noise", 0.1)
        kf = KalmanFilter(
            initial_state_mean=data[0],
            observation_covariance=1,
            transition_covariance=process_noise,
            transition_matrices=[1],
        )
        state_means, _ = kf.filter(data)
        residuals = data - state_means.flatten()
        adaptive_noise = np.clip(np.std(residuals) * 0.1, 1e-6, 0.5)
        kf.transition_covariance = adaptive_noise
        smoothed = kf.smooth(data)[0].flatten()

    elif method == "physics_constrained":
        timestep = kwargs["timestep"]
        cutoff_freq = kwargs.get("cutoff_freq", 0.2)
        fs = 1000.0 / timestep
        nyquist = 0.5 * fs
        normal_cutoff = cutoff_freq / nyquist
        b, a = butter(4, normal_cutoff, btype="low", analog=False)
        smoothed = filtfilt(b, a, data)

    elif method == "robust_lowess":
        frac = kwargs.get("lowess_frac", 0.1)
        it = kwargs.get("lowess_it", 3)
        x = np.arange(len(data))
        smoothed = lowess(data, x, frac=frac, it=it, is_sorted=True, return_sorted=False)

    elif method == "dynamic_wavelet":
        base_thresh = kwargs.get("base_thresh", 0.1)
        sensitivity = kwargs.get("dwt_sensitivity", 2.0)
        coeffs = pywt.wavedec(data, "db4", level=5)
        for i in range(1, len(coeffs)):
            window_size = len(coeffs[i]) // 10 or 1
            local_std = np.convolve(np.abs(coeffs[i]), np.ones(window_size) / window_size, mode="same")
            thresh = base_thresh * (1 + sensitivity * (local_std / np.max(local_std) - 0.5))
            coeffs[i] = pywt.threshold(coeffs[i], thresh, "soft")
        smoothed = pywt.waverec(coeffs, "db4")[: len(data)]

    elif method == "moving_avg":
        window_size = kwargs.get("window_size", 5)
        if window_size <= 1:
            return data
        padding = kwargs.get("padding", "edge")
        if padding == "edge":
            pad_left = np.full((window_size - 1) // 2, data[0])
            pad_right = np.full((window_size - 1) // 2, data[-1])
            if window_size % 2 == 0:
                pad_right = np.append(pad_right, data[-1])
            padded = np.concatenate([pad_left, data, pad_right])
            smoothed = np.convolve(padded, np.ones(window_size) / window_size, mode="valid")
        else:
            smoothed = np.convolve(data, np.ones(window_size) / window_size, mode="same")

    elif method == "savgol":
        window_length = kwargs.get("window_length", min(11, len(data) // 2 * 2 - 1))
        polyorder = kwargs.get("polyorder", 2)
        if window_length > len(data):
            window_length = len(data) if len(data) % 2 else len(data) - 1
        smoothed = savgol_filter(data, window_length, polyorder)

    elif method == "wavelet":
        wavelet = kwargs.get("wavelet", "db4")
        max_level = pywt.dwt_max_level(len(data), pywt.Wavelet(wavelet).dec_len)
        level = min(kwargs.get("level", 5), max_level)
        threshold = kwargs.get("threshold", 0.1) * np.max(np.abs(data - np.mean(data)))
        coeffs = pywt.wavedec(data, wavelet, level=level)
        coeffs[1:] = [pywt.threshold(c, threshold, mode="soft") for c in coeffs[1:]]
        smoothed = pywt.waverec(coeffs, wavelet)[: len(data)]

    elif method == "ewma":
        alpha = kwargs.get("alpha", 0.3)
        span = kwargs.get("span", None)
        adjust = kwargs.get("adjust", True)
        min_periods = kwargs.get("min_periods", 1)
        if span is not None:
            alpha = 2.0 / (span + 1)
        result = np.empty_like(data, dtype=float)
        result[:] = np.nan
        if len(data) > 0:
            result[0] = data[0]
            if adjust:
                weighted_sum = data[0]
                sum_weights = 1.0
                for i in range(1, len(data)):
                    weighted_sum = alpha * data[i] + (1 - alpha) * weighted_sum
                    sum_weights = alpha + (1 - alpha) * sum_weights
                    result[i] = weighted_sum / sum_weights
            else:
                for i in range(1, len(data)):
                    result[i] = alpha * data[i] + (1 - alpha) * result[i - 1]
            if min_periods > 1:
                result[: min_periods - 1] = np.nan
        smoothed = result

    else:
        raise ValueError(f"Unsupported smoothing method: {method}")

    if orig_index is not None:
        return pd.Series(smoothed, index=orig_index, name=orig_name)
    return smoothed.tolist() if isinstance(data, list) else smoothed


AVAILABLE_METHODS = [
    "segment_spline",
    "adaptive_kalman",
    "physics_constrained",
    "robust_lowess",
    "dynamic_wavelet",
    "moving_avg",
    "savgol",
    "wavelet",
    "ewma",
]
