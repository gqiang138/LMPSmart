# lmpsmart — LAMMPS Data Agent

LAMMPS molecular dynamics simulation data processing tool with autonomous Agent architecture.
Parses 8 file formats, standardizes LAMMPS non-standard data into 8 original structured outputs, smooths signals, filters outliers, computes metrics — all driven by YAML config.

## Features

- **8 file parsers**: Log, Bonds, Dump, Cell, Species, POS, OVITO, General
- **8 original standardized outputs**: Bonds (bocutoff/blcutoff thresholds), Cell (Lx/Ly/Lz/Volume from Dump), Atom (id→element mapping), Species/POS (molecular weight), OVITO multi-frame integration
- **9 smoothing algorithms + curve fitting**: segment_spline, adaptive_kalman, physics_constrained, robust_lowess, dynamic_wavelet, moving_avg, savgol, wavelet, ewma; polyfit.n polynomial fitting; LOWESS local regression
- **3 outlier filters**: zscore, MAD, IQR
- **Config-driven** (YAML): no hardcoding, all parameters in `configs/default.yaml`
- **Glob batch matching**: process multiple files simultaneously with split naming
- **Agent architecture**: natural language goal → LLM-first plan → tool chain (falls back to keyword matching)
- **Multi-provider LLM**: local Ollama / online OpenAI-compatible API, config-driven
- **Execution logger**: full traceability (JSONL) for reproducibility

## Installation

```bash
# Smart installer (auto-detects env, offers LLM config)
python install.py

# Or manual
pip install -e .
```

## Quick Start

```bash
# Direct CLI (from src/)
python src/lmpsmart/__main__.py config --show
python src/lmpsmart/__main__.py arrange --path ./data --modes Log,Bonds,Dump
python src/lmpsmart/__main__.py agent --goal "arrange log files and smooth temperature"

# Python API
python -m lmpsmart config --show  # after pip install -e .

from lmpsmart import arrange, smooth, filter_outliers
df = arrange("data/", modes=["Log", "Bonds"])
smoothed = smooth(df["temperature"], method="moving_avg")
```

## Architecture

```
Input files (LAMMPS)
       ↓
  Arrange Layer        ← 8 parsers + 8 original standardized outputs + glob batch + YAML config
       ↓
   DataFrame
       ↓
  Mapping Layer       ← 9 smoothers + curve fitting + 3 filters + metrics (RMSD/CED/mweight)
       ↓
   Output files
       ↑
  Agent Controller     ← plan_from_goal() → execute()
```

## Supported File Formats

| Format   | Description                          | Parser             |
|----------|--------------------------------------|--------------------|
| Log      | LAMMPS thermodynamic output          | `read_log()`       |
| Bonds    | Bond order analysis (ReaxFF)         | `read_bonds()`     |
| Dump     | Atomic trajectory (positions/velocities)| `read_dump()`     |
| Cell     | Unit cell dimensions                 | `read_cell()`      |
| Species  | Chemical species counts              | `read_species()`   |
| POS      | POSCAR-style crystal files           | `read_pos()`       |
| OVITO    | OVITO export format                 | `read_ovito()`     |
| General  | Auto-detected CSV/TSV               | `read_general()`    |

## Configuration

All parameters in `configs/default.yaml`:

- `cutoff`: 30 bond types + bond order cutoffs + bond length cutoffs
- `filerule1`: input glob patterns for 8 file types
- `filerule2`: output naming rules
- `plotset`: matplotlib figure parameters
- `bonds_limit`: per-element bond count limits
- `timestep`, `thermostep`, `ignoredtime`, `supercell`

## Agent Tools (18 total)

```
arrange, load_config,
read_log, read_bonds, read_dump, read_data,
read_cell, read_species, read_pos, read_general,
smooth, filter_outliers,
molecular_weight, find_elements, atom_type,
detect_encoding, autocode
```

### LLM Agent (Fully Integrated)

Agent 默认启用 LLM 推理（Ollama 本地或在线 API），关键词匹配作为降级备选。

```bash
# Agent 默认调用 LLM（自动检测可用性）
python -m lmpsmart agent --goal "平滑温度曲线，去除异常值"

# 配置 Ollama 本地模型（默认）
python -m lmpsmart llm setup --provider local --model qwen3.5-9b

# 配置在线 API（OpenRouter 等 OpenAI 兼容接口）
python -m lmpsmart llm setup --provider online \
    --base-url https://openrouter.ai/api/v1 \
    --api-key sk-or-xxxxx --model anthropic/claude-3-haiku

# 强制使用关键词匹配（无 LLM 环境）
python -m lmpsmart agent --goal "arrange log" --no-llm
```

## Reproducibility

Every tool call is logged to `logs/agent_session_{session_id}.jsonl`:

```json
{"log_id": "a1b2c3d4e5f6", "timestamp": "...", "session_id": "...", "tool": "arrange",
 "input": {...}, "execution_steps": [...], "output_summary": {...}, "status": "success"}
```

## License

GNU General Public License v3.0 (GPL-3.0)

Copyright (c) 2025 Qiang Gan
