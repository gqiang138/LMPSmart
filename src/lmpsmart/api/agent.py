# Copyright (c) 2025 Qiang Gan
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations
import json
from pathlib import Path
from typing import Any
from lmpsmart.api.tools import TOOL_REGISTRY
from lmpsmart.api.logging import ExecutionLogger


class LmpparseAgent:
    def __init__(
        self,
        log_dir: str | Path | None = None,
        use_llm: bool = True,
        llm_cfg: dict[str, Any] | None = None,
    ):
        self.logger = ExecutionLogger(log_dir)
        self.tools = TOOL_REGISTRY
        self.use_llm = use_llm
        self.llm_cfg = llm_cfg
        self._llm_available: bool | None = None

    def _check_llm(self) -> bool:
        if self._llm_available is None:
            from lmpsmart.api import llm as llm_mod
            self._llm_available = llm_mod.is_available(self.llm_cfg)
        return self._llm_available

    def plan_from_goal(self, goal: str) -> list[dict[str, Any]]:
        if self.use_llm and self._check_llm():
            from lmpsmart.api import llm as llm_mod
            try:
                plan = llm_mod.plan(goal, task="plan", cfg=self.llm_cfg)
                if plan:
                    self.logger.log(
                        "llm_plan",
                        {"goal": goal},
                        [f"LLM generated {len(plan)}-step plan"],
                        plan,
                        status="success",
                    )
                    return plan
            except Exception:
                pass
        return self._keyword_plan(goal)

    def _keyword_plan(self, goal: str) -> list[dict[str, Any]]:
        goal_lower = goal.lower()
        plan = []
        if "arrange" in goal_lower and any(m in goal_lower for m in ["log", "bonds", "dump", "cell"]):
            modes = [m for m in ["Log", "Bonds", "Dump", "Cell", "Species", "POS", "OVITO", "General"]
                     if m.lower() in goal_lower]
            if not modes:
                modes = ["Log", "Bonds", "Dump"]
            plan.append({"tool": "arrange", "params": {"modes": modes}})
        if "smooth" in goal_lower:
            method = "moving_avg"
            for m in ["segment_spline", "adaptive_kalman", "physics_constrained",
                       "robust_lowess", "dynamic_wavelet", "savgol", "wavelet", "ewma"]:
                if m in goal_lower:
                    method = m
                    break
            plan.append({"tool": "smooth", "params": {"method": method}})
        if "filter" in goal_lower or "outlier" in goal_lower:
            method = "zscore"
            for m in ["mad", "iqr"]:
                if m in goal_lower:
                    method = m
                    break
            plan.append({"tool": "filter_outliers", "params": {"methods": method}})
        return plan

    def execute(self, task: dict[str, Any]) -> dict[str, Any]:
        tool_name = task.get("tool")
        params = task.get("params", {})
        if tool_name not in self.tools:
            return {"status": "error", "message": f"Unknown tool: {tool_name}"}
        try:
            result = self.tools[tool_name](**params)
            return {"status": "success", "result": result}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def execute_plan(self, plan: list[dict[str, Any]]) -> list[dict[str, Any]]:
        results = []
        for step in plan:
            result = self.execute(step)
            results.append({"step": step, "result": result})
        return results

    def session_summary(self) -> dict:
        return self.logger.summary()
