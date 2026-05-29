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
from lmpsmart.mapping.fit import fit as fit_data
from lmpsmart.mapping.plot import plot_dataframe
from lmpsmart.api.agent import LmpparseAgent
from lmpsmart.api.logging import ExecutionLogger
from lmpsmart.api import llm as llm_mod


def cmd_arrange(args):
    cfg = load_config(args.config) if args.config else None
    modes = [m.strip() for m in args.modes.split(",")]
    result, out_dir = arrange(
        input_path=args.path,
        modes=modes,
        config=cfg,
        ignored_time=args.ignored_time,
        timestep=args.timestep,
        encoding=args.encoding,
        output_path=args.output if getattr(args, "output", None) else None,
    )
    print(json.dumps({"status": "success", "modes": modes, "output_dir": out_dir, "files": list(result.keys())}))
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
        except (json.JSONDecodeError, ValueError):
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


def cmd_fit(args):
    import pandas as pd
    df = pd.read_csv(args.csv)
    result = fit_data(df[args.x], df[args.y], method=args.method, degree=args.degree, frac=args.frac)
    if args.output_csv:
        y_fitted = result.get("fitted", result.get("y", []))
        df_out = pd.DataFrame({
            args.x: df[args.x],
            args.y: df[args.y],
            f"{args.y}_fitted": y_fitted,
        })
        df_out.to_csv(args.output_csv, index=False)
    print(json.dumps({"status": "success", "method": result["method"], "r2": result["r2"], "coef": result.get("coef", [])}))
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


def cmd_plot(args):
    cfg = load_config(args.config) if args.config else None
    import pandas as pd
    df = pd.read_csv(args.csv)
    y_cols = [y.strip() for y in args.y.split(",")]
    plot_dataframe(
        df,
        x_col=args.x,
        y_cols=y_cols,
        output_path=args.output,
        mode=args.mode,
        plotset=cfg.plotset if cfg else None,
        hue_col=args.hue if args.hue else None,
        markers=args.markers,
        legend_loc=args.legend_loc or "best",
        subscript_labels=args.subscript,
    )
    print(json.dumps({"status": "success", "output": args.output}))
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

    elif args.action == "tune":
        from lmpsmart.api.llm_tune import tune
        result = tune(model=args.model, quick=args.quick)
        print(json.dumps({"status": "tuned", **result}))

    return 0


def cmd_agent(args):
    if not getattr(args, "interactive", False) and not getattr(args, "goal", None):
        print("error: --goal is required (or use --interactive for REPL mode)", file=sys.stderr)
        return 1
    llm_cfg = llm_mod.load_llm_config() if not getattr(args, "no_llm", False) else None
    agent = LmpparseAgent(use_llm=llm_cfg is not None, llm_cfg=llm_cfg)

    if getattr(args, "interactive", False):
        print("lmpsmart agent [interactive mode] — Ctrl+C to exit")
        print(f"LLM: {llm_cfg.get('provider') if llm_cfg else 'disabled'} | model={llm_cfg.get('default_model') if llm_cfg else 'n/a'}")
        print()
        while True:
            try:
                goal = input("lmpsmart> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye.")
                return 0
            if not goal:
                continue
            print()
            plan, text = agent.plan_from_goal(goal)
            if text is not None:
                print(text)
                print()
                continue
            if args.dry_run or getattr(args, "dry_run", False):
                print(f"[plan] {len(plan)} step(s):")
                for i, s in enumerate(plan, 1):
                    print(f"  {i}. {s['tool']}({s.get('params', {})})")
            else:
                results = agent.execute_plan(plan)
                for r in results:
                    tool = r["step"]["tool"]
                    status = r["result"].get("status", "unknown")
                    res = r["result"]
                    params = r["step"].get("params", {})

                    if tool == "arrange":
                        files = res.get("result", {}).get("files", []) if isinstance(res.get("result"), dict) else []
                        out_dir = res.get("result", {}).get("output_dir", "?") if isinstance(res.get("result"), dict) else "?"
                        print(f"  ✓ arrange → 输出目录: {out_dir}")
                        for f in files:
                            print(f"    · {f}")

                    elif tool == "plot":
                        out = res.get("result", {}).get("output", "?") if isinstance(res.get("result"), dict) else "?"
                        x = params.get("x_col", "?")
                        ys = params.get("y_cols", [])
                        mode = params.get("mode", "single")
                        print(f"  ✓ 绘图完成 → {out}")
                        print(f"    坐标: {x} vs {ys}  (mode={mode})")

                    elif tool == "select_columns":
                        out = params.get("output_path", "?")
                        cols = params.get("columns", [])
                        print(f"  ✓ 列筛选 → {out}  ({len(cols)} 列: {cols})")

                    elif tool == "belong_filter":
                        out = params.get("output_path", "?")
                        col = params.get("col", "?")
                        vals = params.get("values", [])
                        print(f"  ✓ 行过滤 → {out}  ({col} in {vals})")

                    elif tool == "groupby_aggregate":
                        out = params.get("output_path", "?")
                        print(f"  ✓ 分组聚合 → {out}")

                    elif tool == "column_rename":
                        out = params.get("output_path", "?")
                        print(f"  ✓ 列重命名 → {out}")

                    elif tool == "merge_data":
                        out = params.get("output_path", "?")
                        print(f"  ✓ 数据合并 → {out}")

                    elif tool == "smooth":
                        print(f"  ✓ 平滑完成 → method={params.get('method', '?')}")

                    elif tool == "fit":
                        fit_res = res.get("result", {}) if isinstance(res.get("result"), dict) else {}
                        r2 = fit_res.get("r2", "?")
                        method = params.get("method", "?")
                        print(f"  ✓ 拟合完成 → {method}, R²={r2}")

                    elif tool == "filter_outliers":
                        print(f"  ✓ 异常值过滤完成")

                    else:
                        print(f"  ✓ {tool} → {'success' if status == 'success' else status}")
            print()
    else:
        plan, text = agent.plan_from_goal(args.goal)
        if text is not None:
            print(text)
            return 0
        if args.dry_run:
            print(f"[plan] {len(plan)} step(s):")
            for i, s in enumerate(plan, 1):
                print(f"  {i}. {s['tool']}({s.get('params', {})})")
            return 0
        results = agent.execute_plan(plan)
        for r in results:
            tool = r["step"]["tool"]
            res = r["result"]
            params = r["step"].get("params", {})
            if tool == "arrange":
                out_dir = res.get("result", {}).get("output_dir", "?") if isinstance(res.get("result"), dict) else "?"
                print(f"✓ arrange → {out_dir}")
            elif tool == "plot":
                out = res.get("result", {}).get("output", "?") if isinstance(res.get("result"), dict) else "?"
                print(f"✓ plot → {out}")
            else:
                print(f"✓ {tool} → {res.get('status', 'done')}")
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
    sp.add_argument("--output", help="Output directory (default: project_root/output/<input_name>)")

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

    fi = sub.add_parser("fit", help="Polynomial / LOWESS fitting")
    fi.add_argument("--csv", required=True, help="Input CSV")
    fi.add_argument("--x", required=True, help="X column name")
    fi.add_argument("--y", required=True, help="Y column name")
    fi.add_argument("--method", default="polyfit", choices=["polyfit", "lowess"])
    fi.add_argument("--degree", type=int, default=2, help="Polynomial degree (polyfit only)")
    fi.add_argument("--frac", type=float, default=0.3, help="LOWESS frac (lowess only)")
    fi.add_argument("--output-csv", help="Output CSV with fitted values")

    cfg_p = sub.add_parser("config", help="Show/save parsing config (bonds/cutoff)")
    cfg_p.add_argument("--show", action="store_true")

    pl = sub.add_parser("plot", help="Plot CSV with Seaborn (old lmpanalysis style)")
    pl.add_argument("--csv", required=True, help="Input CSV file")
    pl.add_argument("--x", required=True, help="X-axis column name")
    pl.add_argument("--y", required=True, help="Comma-separated Y-axis column names")
    pl.add_argument("--output", required=True, help="Output PNG path")
    pl.add_argument("--mode", default="single", choices=["single", "multi", "doubley"])
    pl.add_argument("--hue", help="Column for color grouping (hue)")
    pl.add_argument("--markers", action="store_true", help="Show line markers")
    pl.add_argument("--legend-loc", default="best", help="Legend location")
    pl.add_argument("--subscript", action="store_true", help="Apply Unicode subscript to Y-axis labels (for molecule formulas)")
    pl.add_argument("--config", help="YAML config path")

    llm_sub = sub.add_parser("llm", help="LLM provider configuration (local Ollama / online API)")
    llm_sub.add_argument("action", choices=["show", "list", "test", "setup", "tune"],
                         help="show=list config, list=list available models, test=ping server, setup=update config, tune=auto-tune params")
    llm_sub.add_argument("--provider", choices=["local", "online"], help="Provider type")
    llm_sub.add_argument("--base-url", help="Base URL (e.g. http://localhost:11434 or https://openrouter.ai/api/v1)")
    llm_sub.add_argument("--api-key", help="API key for online provider")
    llm_sub.add_argument("--model", help="Default model name")
    llm_sub.add_argument("--quick", action="store_true", help="Quick tune: 1 param combo per task")

    ag = sub.add_parser("agent", help="Run Agent with natural language goal")
    ag.add_argument("--goal", help="Natural language goal (required unless --interactive)")
    ag.add_argument("--interactive", action="store_true", help="Interactive REPL mode — enter goals interactively")
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
            "fit": cmd_fit,
            "config": cmd_config,
            "plot": cmd_plot,
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
