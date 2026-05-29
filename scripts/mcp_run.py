#!/usr/bin/env python3
"""MCP server launcher — reads Python path and project root from configs/llm.yaml."""
import sys, os
from pathlib import Path
import yaml

config_path = Path(__file__).parent.parent / "configs" / "llm.yaml"
with open(config_path) as f:
    cfg = yaml.safe_load(f)

python_exe = cfg.get("python_path")
project_root = cfg.get("project_root")

if not python_exe:
    raise RuntimeError(f"python_path not set in {config_path}")

python_exe = Path(python_exe).expanduser()
if not python_exe.is_file():
    raise RuntimeError(f"Python executable not found: {python_exe}")

os.chdir(project_root)
os.execv(str(python_exe), [str(python_exe), "-m", "lmpsmart.api.mcp_server", *sys.argv[1:]])
