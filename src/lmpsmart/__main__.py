# Copyright (c) 2025 Qiang Gan
# SPDX-License-Identifier: GPL-3.0-or-later
#!/usr/bin/env python
import sys
import argparse
import json
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from lmpsmart.arrange.config import load_config
from lmpsmart.arrange.readers import arrange
from lmpsmart.mapping.smooth import smooth, AVAILABLE_METHODS
from lmpsmart.mapping.filter import filter_outliers
from lmpsmart.api.agent import LmpparseAgent
from lmpsmart.api.logging import ExecutionLogger
from lmpsmart.api import llm as llm_mod


def cmd_arrange(args):
    cfg = load_config(args.config) if args.config else None
    modes = [m.strip() for m in args.modes.split(",")]
    result = arrange(
        input_path=args.path,
        modes=modes,
        config=cfg,
        ignored_time=args.ignored_time,
        timestep=args.timestep,
        encoding=args.encoding,
    )
    print(json.dumps({"status": "success", "modes": modes, "files": list(result.keys())}))
    return 0


def cmd_smooth(args):
    import numpy as np
    import os
    data_path = args.data
    if os.path.isfile(str(data_path)):
        data = list(np.loadtxt(data_path))
    else:
        try:
            data = json.loads(data_path)
        except json.JSONDecodeError:
            data = json.loads(f"[{data_path}]")
    method = args.method if args.method in AVAILABLE_METHODS else "moving_avg"
    result = smooth(data, method=method)
    result_list = result.tolist() if hasattr(result, 'tolist') else list(result)
    if args.output:
        import pandas as pd
        pd.DataFrame({"smoothed": result_list}).to_csv(args.output, index=False)
        print(json.dumps({"status": "success", "output": args.output}))
    else:
        print(json.dumps({"status": "success", "data": result_list[:10]}))
    return 0


def cmd_filter(args):
    import pandas as pd
    df = pd.read_csv(args.csv)
    methods = [m.strip() for m in args.methods.split(",")]
    result = filter_outliers(df, args.time_col, args.value_col, methods, args.threshold)
    if args.output:
        result.to_csv(args.output, index=False)
        print(json.dumps({"status": "success", "output": args.output, "kept": len(result), "removed": len(df) - len(result)}))
    else:
        print(json.dumps({"status": "success", "kept": len(result), "removed": len(df) - len(result)}))
    return 0


def cmd_config(args):
    cfg = load_config()
    info = {
        "cutoff_bonds": cfg.cutoff.bonds,
        "bocutoff_count": len(cfg.cutoff.bocutoff),
        "blcutoff_count": len(cfg.cutoff.blcutoff),
        "bonds_limit": cfg.bonds_limit,
        "default_timestep": cfg.default_timestep,
        "default_encoding": cfg.default_encoding,
    }
    if args.show:
        print(json.dumps(info, indent=2))
    else:
        print(json.dumps(info))
    return 0


def cmd_llm(args):
    cfg = llm_mod.load_llm_config()

    if args.action == "show":
        safe = {k: (v if k != "api_key" or not v else "***") for k, v in cfg.items()}
        print(json.dumps(safe, indent=2))

    elif args.action == "list":
        print("Provider:", cfg.get("provider"))
        print("Base URL:", cfg.get("base_url"))
        print("Default model:", cfg.get("default_model"))
        print("Available local models:")
        for m in llm_mod.AVAILABLE_LOCAL_MODELS:
            print(f"  - {m}")

    elif args.action == "test":
        ok = llm_mod.is_available(cfg)
        print(json.dumps({"status": "ok" if ok else "unavailable", "provider": cfg.get("provider"), "model": cfg.get("default_model")}))

    elif args.action == "setup":
        new_cfg = dict(cfg)
        if args.provider:
            new_cfg["provider"] = args.provider
        if args.base_url:
            new_cfg["base_url"] = args.base_url
        if args.api_key:
            new_cfg["api_key"] = args.api_key
        if args.model:
            new_cfg["default_model"] = args.model
            if "task_models" not in new_cfg:
                new_cfg["task_models"] = {}
            new_cfg["task_models"]["plan"] = args.model
            new_cfg["task_models"]["chat"] = args.model
        llm_mod.save_llm_config(new_cfg)
        print(json.dumps({"status": "saved", "config": new_cfg}))

    return 0


def cmd_agent(args):
    llm_cfg = llm_mod.load_llm_config() if not getattr(args, "no_llm", False) else None
    agent = LmpparseAgent(use_llm=llm_cfg is not None, llm_cfg=llm_cfg)
    plan = agent.plan_from_goal(args.goal)
    print(json.dumps({"status": "success", "goal": args.goal, "plan": plan}))
    if not args.dry_run:
        results = agent.execute_plan(plan)
        print(json.dumps({"status": "executed", "results": [{"step": r["step"]["tool"], "status": r["result"]["status"]} for r in results]}))
    return 0


def main():
    p = argparse.ArgumentParser(prog="lmpsmart", description="LAMMPS Molecular Dynamics Data Agent")
    p.add_argument("--version", action="version", version="lmpsmart 1.0.0")
    sub = p.add_subparsers(dest="cmd")

    sp = sub.add_parser("arrange", help="Parse LAMMPS files")
    sp.add_argument("--path", required=True, help="Input directory")
    sp.add_argument("--modes", required=True, help="Comma-separated modes: Log,Bonds,Dump,Cell,Species,POS,OVITO,General")
    sp.add_argument("--config", help="YAML config path")
    sp.add_argument("--timestep", type=float, default=0.1)
    sp.add_argument("--encoding", default="utf-8")
    sp.add_argument("--ignored-time", type=float, default=0.0)

    sm = sub.add_parser("smooth", help="Smooth time-series data")
    sm.add_argument("--data", required=True, help="JSON list or file path")
    sm.add_argument("--method", default="moving_avg", choices=AVAILABLE_METHODS)
    sm.add_argument("--output", help="Output CSV path")

    ft = sub.add_parser("filter", help="Filter outliers")
    ft.add_argument("--csv", required=True, help="Input CSV")
    ft.add_argument("--time-col", default="time")
    ft.add_argument("--value-col", required=True, help="Column to filter")
    ft.add_argument("--methods", default="zscore")
    ft.add_argument("--threshold", type=float, default=3.0)
    ft.add_argument("--output", help="Output CSV path")

    cfg = sub.add_parser("config", help="Show/save parsing config (bonds/cutoff)")
    cfg.add_argument("--show", action="store_true")

    llm_cfg = sub.add_parser("llm", help="LLM provider configuration (local Ollama / online API)")
    llm_cfg.add_argument("action", choices=["show", "list", "test", "setup"],
                        help="show=list config, list=list available models, test=ping server, setup=update config")
    llm_cfg.add_argument("--provider", choices=["local", "online"], help="Provider type")
    llm_cfg.add_argument("--base-url", help="Base URL (e.g. http://localhost:11434 or https://openrouter.ai/api/v1)")
    llm_cfg.add_argument("--api-key", help="API key for online provider")
    llm_cfg.add_argument("--model", help="Default model name")

    ag = sub.add_parser("agent", help="Run Agent with natural language goal")
    ag.add_argument("--goal", required=True, help="Natural language goal")
    ag.add_argument("--dry-run", action="store_true", help="Show plan without executing")
    ag.add_argument("--no-llm", action="store_true", help="Disable LLM, use keyword matching")

    args = p.parse_args()
    if args.cmd is None:
        p.print_help()
        return 0
    try:
        status = {
            "arrange": cmd_arrange,
            "smooth": cmd_smooth,
            "filter": cmd_filter,
            "config": cmd_config,
            "llm": cmd_llm,
            "agent": cmd_agent,
        }[args.cmd](args)
        sys.exit(status if status is not None else 0)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(json.dumps({"status": "error", "message": str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    sys.exit(main())
