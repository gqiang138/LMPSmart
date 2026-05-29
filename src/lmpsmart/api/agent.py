# Copyright (c) 2025 Qiang Gan
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations
import json
import re
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

    def plan_from_goal(self, goal: str) -> tuple[list[dict[str, Any]], str | None]:
        """Return (plan, text_response).
        text_response is non-None when the LLM answered conversationally (no tools).
        """
        if self.use_llm and self._check_llm():
            from lmpsmart.api import llm as llm_mod
            try:
                plan, text = llm_mod.plan(goal, task="plan", cfg=self.llm_cfg)
                if plan:
                    self.logger.log(
                        "llm_plan",
                        {"goal": goal},
                        [f"LLM generated {len(plan)}-step plan"],
                        plan,
                        status="success",
                    )
                    return plan, None
                if text:
                    self.logger.log(
                        "llm_text",
                        {"goal": goal},
                        ["LLM replied with text"],
                        None,
                        status="success",
                    )
                    return [], text
            except Exception:
                pass
        return self._keyword_plan(goal), None

    def _keyword_plan(self, goal: str) -> list[dict[str, Any]]:
        goal_lower = goal.lower()
        plan = []

        if any(k in goal_lower for k in ["arrange", "parse", "处理", "解析"]) and any(m in goal_lower for m in ["log", "bonds", "dump", "cell", "trajectory"]):
            modes = [m for m in ["Log", "Bonds", "Dump", "Cell", "Species", "POS", "OVITO", "General"]
                     if m.lower() in goal_lower]
            if not modes:
                modes = ["Log", "Bonds", "Dump"]
            # Extract input_path from goal (common patterns: "in <path>", "from <path>", "<path>/...")
            input_path = None
            path_m = re.search(r"(?:in|from|from_dir|parse)\s+[\"']?([^\s\"'\",]+)", goal_lower)
            if path_m:
                input_path = path_m.group(1)
            else:
                # Try to extract as last path-like token
                path_m2 = re.search(r"([\w\\/\-.][\w\\/\-.]+)", goal)
                if path_m2:
                    candidate = path_m2.group(1)
                    if not any(k in candidate for k in ["parse", "arrange", "plot", "fit", "smooth", "log", "bond", "dump", "cell"]):
                        import os
                        if os.path.isdir(candidate) or os.path.sep in candidate or "/" in candidate or "\\" in candidate:
                            input_path = candidate
            params = {"modes": modes}
            if input_path:
                params["input_path"] = input_path
            plan.append({"tool": "arrange", "params": params})

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

        if "fit" in goal_lower or "拟合" in goal_lower or "polyfit" in goal_lower:
            method = "polyfit"
            degree = 2
            frac = 0.3
            if "lowess" in goal_lower:
                method = "lowess"
                frac_m = re.search(r"frac(?:t)?\s*[=:]\s*([0-9.]+)", goal_lower)
                if frac_m:
                    frac = float(frac_m.group(1))
            elif any(f"degree{i}" in goal_lower for i in range(1, 6)):
                m = re.search(r"degree\s*(\d)", goal_lower)
                if m:
                    degree = int(m.group(1))
            elif "linear" in goal_lower:
                degree = 1
            plan.append({"tool": "fit", "params": {"method": method, "degree": degree, "frac": frac}})

        # data cleaning: groupby/aggregate
        if any(k in goal_lower for k in ["group", "aggregate", "count per", "sum per", "统计每", "每组"]) and \
           any(k in goal_lower for k in ["species", "atom", "bond", "type", "frame", "group"]):
            plan.append({"tool": "groupby_aggregate", "params": {}})

        # data cleaning: belong/in filter
        if any(k in goal_lower for k in ["belong", "filter", "only", "keep only", "只保留", "筛选"]):
            plan.append({"tool": "belong_filter", "params": {}})

        # data cleaning: column rename
        if any(k in goal_lower for k in ["rename", "rename_col", "重命名", "改名"]):
            plan.append({"tool": "column_rename", "params": {}})

        # data cleaning: select/keep columns
        if any(k in goal_lower for k in ["select", "keep", "pick", "choose col", "只选", "选取列"]):
            plan.append({"tool": "select_columns", "params": {}})

        # data cleaning: merge/concat dataframes
        if any(k in goal_lower for k in ["merge", "join", "concat", "合并", "拼接"]):
            plan.append({"tool": "merge_data", "params": {}})

        if any(k in goal_lower for k in ["plot", "draw", "show", "figure", "图表", "绘图", "可视化", "visualize", "curve", "曲线"]):
            plan.append({"tool": "plot", "params": {"mode": "single"}})

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
        """Execute plan with automatic data-flow chaining.

        Each tool's output is tracked. When a subsequent tool needs a csv_path
        (smooth, fit, filter_outliers, plot, groupby_aggregate, belong_filter,
        merge_data, column_rename, select_columns) but doesn't have one explicitly
        provided, the last known CSV output is injected automatically.
        """
        results = []
        last_csv: str | None = None  # tracks most recent arrange/csv output
        last_arrange_modes: list[str] = []

        for step in plan:
            params = dict(step.get("params", {}))
            tool_name = step.get("tool", "")

            # Tools that need a csv_path but don't have one → inject from chain
            csv_needy = {
                "smooth", "fit", "filter_outliers", "plot",
                "groupby_aggregate", "belong_filter", "merge_data",
                "column_rename", "select_columns",
            }
            if tool_name in csv_needy and "csv_path" not in params and last_csv:
                params["csv_path"] = last_csv
                step = {"tool": tool_name, "params": params}

            result = self.execute(step)
            results.append({"step": step, "result": result})

            # Track CSV outputs for chaining
            if result.get("status") == "success":
                r = result.get("result")
                if tool_name == "arrange":
                    # arrange returns {"status": "success", "files": [...], "outputs": {...}}
                    outputs = r.get("outputs", {}) if isinstance(r, dict) else {}
                    files = r.get("files", []) if isinstance(r, dict) else []
                    for f in files:
                        if isinstance(f, str) and (f.endswith(".csv") or "\\" in f or "/" in f):
                            last_csv = f
                            break
                    files = r.get("files", []) if isinstance(r, dict) else []
                    for f in files:
                        if isinstance(f, str) and (f.endswith(".csv") or "\\" in f or "/" in f):
                            last_csv = f
                            break
                elif tool_name in ("groupby_aggregate", "belong_filter",
                                   "column_rename", "select_columns"):
                    if "output_path" in params and params["output_path"]:
                        last_csv = params["output_path"]

        return results

    def session_summary(self) -> dict:
        return self.logger.summary()
