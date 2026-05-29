# Copyright (c) 2025 Qiang Gan
# SPDX-License-Identifier: GPL-3.0-or-later
"""Auto-tune Ollama LLM parameters for LMPSmart tasks.

Usage:
    python -m lmpsmart.api.llm_tune [--model MODEL] [--quick]
    python -m lmpsmart llm tune --model qwen3.5-9b:latest
"""
from __future__ import annotations
import json
import time
import urllib.request
import urllib.error
from pathlib import Path

BENCHMARK_PROMPTS = {
    "plan": [
        {
            "goal": "parse log file data/ and plot energy",
            "expected_tools": ["arrange", "plot"],
        },
        {
            "goal": "smooth temperature data and fit a curve",
            "expected_tools": ["smooth", "fit", "plot"],
        },
        {
            "goal": "filter outliers in output/arrange/dataofdump.csv for column temp",
            "expected_tools": ["filter_outliers"],
        },
        {
            "goal": "从dump文件提取原子轨迹并绘图",
            "expected_tools": ["arrange", "plot"],
        },
    ],
    "chat": [
        {
            "goal": "介绍一下你的功能",
            "expected_contains": ["LAMMPS", "Qiang Gan"],
        },
        {
            "goal": "LMPSmart支持哪些数据格式",
            "expected_contains": ["Log", "Dump", "Data"],
        },
    ],
    "coding": [
        {
            "goal": "解释一下什么是ReaxFF力场",
            "expected_contains": ["reactive", "bond order", "LAMMPS"],
        },
        {
            "goal": "含能材料分子动力学模拟的基本流程是什么",
            "expected_contains": ["LAMMPS", "力场", "能量"],
        },
    ],
}

PARAM_GRID = {
    "plan": [
        {"temperature": 0.0, "num_predict": 256,  "thinking": False},
        {"temperature": 0.1, "num_predict": 384,  "thinking": False},
        {"temperature": 0.0, "num_predict": 512,  "thinking": False},
        {"temperature": 0.1, "num_predict": 768,  "thinking": False},
    ],
    "chat": [
        {"temperature": 0.3, "num_predict": 128,  "thinking": False},
        {"temperature": 0.5, "num_predict": 256,  "thinking": False},
        {"temperature": 0.7, "num_predict": 384,  "thinking": False},
    ],
    "coding": [
        {"temperature": 0.1, "num_predict": 512,  "thinking": False},
        {"temperature": 0.0, "num_predict": 768,  "thinking": False},
        {"temperature": 0.2, "num_predict": 1024, "thinking": False},
    ],
}


def load_config() -> dict:
    import os
    from lmpsmart.api.llm import load_llm_config
    return load_llm_config()


def save_config(cfg: dict) -> None:
    from lmpsmart.api.llm import save_llm_config
    save_llm_config(cfg)


def _strip_think(raw: str) -> str:
    import re
    return re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()


def _call_llama(base_url: str, model: str, prompt: str, options: dict, timeout: int) -> tuple[str, float]:
    payload = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": options,
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{base_url}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    start = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = json.loads(resp.read().decode("utf-8"))["response"]
    elapsed = time.time() - start
    return _strip_think(raw), elapsed


def _score_plan(response: str, expected_tools: list[str]) -> float:
    score = 0.0
    try:
        plan = json.loads(response)
        if isinstance(plan, list):
            score += 0.5
            tools = {s.get("tool") for s in plan if isinstance(s, dict)}
            for t in expected_tools:
                if any(t.lower() in (tools or "").lower() for _ in [1]):
                    pass
            matched = sum(1 for t in expected_tools
                          if any(t.lower() in str(s.get("tool","")).lower() for s in plan))
            score += 0.5 * matched / max(len(expected_tools), 1)
    except json.JSONDecodeError:
        score = 0.0
    return score


def _score_chat(response: str, expected_contains: list[str]) -> float:
    r_lower = response.lower()
    matched = sum(1 for kw in expected_contains if kw.lower() in r_lower)
    return matched / max(len(expected_contains), 1)


def _score_coding(response: str, expected_contains: list[str]) -> float:
    return _score_chat(response, expected_contains)


def _run_benchmark(base_url: str, model: str, task: str,
                   options: dict, prompts: list[dict], timeout: int) -> dict:
    total_score = 0.0
    total_time = 0.0
    results = []
    for p in prompts:
        goal = p["goal"]
        from lmpsmart.api.llm import SYSTEM_PROMPT_TEMPLATE, TOOL_SCHEMA
        schema_str = json.dumps({"dummy": "schema"}, indent=2)
        prompt = SYSTEM_PROMPT_TEMPLATE.format(tool_schema=schema_str, goal=goal)
        resp, elapsed = _call_llama(base_url, model, prompt, options, timeout)
        if task == "plan":
            score = _score_plan(resp, p["expected_tools"])
        elif task == "chat":
            score = _score_chat(resp, p["expected_contains"])
        else:
            score = _score_coding(resp, p["expected_contains"])
        total_score += score
        total_time += elapsed
        results.append({"goal": goal[:40], "score": score, "time_ms": round(elapsed * 1000)})
    avg_score = total_score / len(prompts) if prompts else 0
    avg_time = total_time / len(prompts) if prompts else 0
    return {"avg_score": avg_score, "avg_time_ms": round(avg_time * 1000), "details": results}


def tune(model: str | None = None, quick: bool = False) -> dict:
    cfg = load_config()
    base_url = cfg.get("base_url", "http://localhost:11434").rstrip("/")
    timeout = cfg.get("timeout", 120)
    target_model = model or cfg.get("default_model") or cfg.get("task_models", {}).get("plan") or "qwen3.5-9b"
    if quick:
        for t in PARAM_GRID:
            PARAM_GRID[t] = PARAM_GRID[t][:1]

    best: dict[str, dict] = {}
    report: dict[str, list] = {}

    for task, prompts in BENCHMARK_PROMPTS.items():
        grid = PARAM_GRID[task]
        best_score = -1
        best_params = None
        best_report = None
        for params in grid:
            r = _run_benchmark(base_url, target_model, task, params, prompts, timeout)
            print(f"  [{task}] temp={params['temperature']} num_pred={params['num_predict']}  "
                  f"score={r['avg_score']:.2f}  time={r['avg_time_ms']}ms")
            if r["avg_score"] > best_score:
                best_score = r["avg_score"]
                best_params = params
                best_report = r
        if best_params:
            best[task] = best_params
            report[task] = best_report

    task_models = dict(cfg.get("task_models", {}))
    for task, params in best.items():
        task_models[task] = target_model
    cfg["task_models"] = task_models

    best_params_flat = {f"{k}_temperature": v["temperature"] for k, v in best.items()}
    best_params_flat.update({f"{k}_num_predict": v["num_predict"] for k, v in best.items()})
    cfg["tuned_params"] = best_params_flat

    save_config(cfg)
    print(f"\nSaved best params to configs/llm.yaml for model {target_model}")
    return {"model": target_model, "best": best, "scores": report}


if __name__ == "__main__":
    import argparse, sys
    p = argparse.ArgumentParser(description="Auto-tune Ollama LLM parameters for LMPSmart")
    p.add_argument("--model", default=None, help="Ollama model to tune (default: from llm.yaml)")
    p.add_argument("--quick", action="store_true", help="Quick mode: only 1 param combo per task")
    p.add_argument("--timeout", type=int, default=120, help="Request timeout per call (default 120s)")
    args = p.parse_args()

    _cfg = load_config()
    _cfg["timeout"] = args.timeout

    import lmpsmart.api.llm as llm_mod
    _orig_load = llm_mod.load_llm_config
    def _patched_load():
        r = _orig_load()
        r["timeout"] = args.timeout
        return r
    llm_mod.load_llm_config = _patched_load

    print(f"Tuning model: {args.model or 'auto'}  quick={args.quick}")
    print("=" * 60)
    result = tune(model=args.model, quick=args.quick)
    print(f"\nDone. Best params saved.")
    for task, params in result["best"].items():
        print(f"  {task}: temperature={params['temperature']}  num_predict={params['num_predict']}")
