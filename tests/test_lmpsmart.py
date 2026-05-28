# Copyright (c) 2025 Qiang Gan
# SPDX-License-Identifier: GPL-3.0-or-later

import pytest


class TestCoreTools:
    def test_molecular_weight(self):
        from lmpsmart.core.tools import molecular_weight
        assert molecular_weight("H2O") > 0

    def test_find_elements(self):
        from lmpsmart.core.tools import find_elements
        assert "H" in find_elements("H2O")

    def test_atom_type(self):
        from lmpsmart.core.tools import atom_type
        assert atom_type(12.0) == "C"


class TestSmooth:
    def test_moving_avg(self):
        from lmpsmart.mapping.smooth import smooth
        data = [1.0, 2.0, 3.0, 4.0, 5.0]
        result = smooth(data, method="moving_avg")
        assert len(result) == len(data)

    def test_all_methods_available(self):
        from lmpsmart.mapping.smooth import AVAILABLE_METHODS
        expected = [
            "segment_spline", "adaptive_kalman", "physics_constrained",
            "robust_lowess", "dynamic_wavelet", "moving_avg",
            "savgol", "wavelet", "ewma",
        ]
        assert sorted(AVAILABLE_METHODS) == sorted(expected)


class TestFilter:
    def test_zscore(self):
        from lmpsmart.mapping.filter import filter_zscore
        import pandas as pd
        s = pd.Series([1, 2, 3, 4, 5, 100])
        mask = filter_zscore(s, threshold=3.0)
        assert mask.sum() < len(s)

    def test_iqr(self):
        from lmpsmart.mapping.filter import filter_iqr
        import pandas as pd
        s = pd.Series([1, 2, 3, 4, 5])
        mask = filter_iqr(s, threshold=1.5)
        assert mask.sum() >= 3


class TestConfig:
    def test_load_default_config(self):
        from lmpsmart.arrange.config import load_config
        cfg = load_config()
        assert cfg.default_timestep > 0


class TestLLM:
    def test_llm_import(self):
        from lmpsmart.api import llm as llm_mod
        assert hasattr(llm_mod, "plan")
        assert hasattr(llm_mod, "load_llm_config")
