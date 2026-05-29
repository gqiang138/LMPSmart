# LMPSmart v1.0 — LAMMPS Data Agent

[![GitHub](https://img.shields.io/badge/GitHub-gqiang138/LMPSmart-brightgreen)](https://github.com/gqiang138/LMPSmart)
[![License](https://img.shields.io/badge/License-GPL--3.0-blue)](https://opensource.org/licenses/GPL-3.0)
[![Python](https://img.shields.io/badge/Python-3.10+-yellow)](https://www.python.org/)
[![MCP](https://img.shields.io/badge/MCP-25%20tools-6AB04A)](https://modelcontextprotocol.io)

**GitHub**: https://github.com/gqiang138/LMPSmart

LAMMPS molecular dynamics simulation data processing tool with autonomous Agent architecture.
Parses 8 file formats, standardizes LAMMPS non-standard data into 8 original structured outputs,
smooths signals, filters outliers, computes metrics — all driven by YAML config.

## Key Features

| Category | Count | Details |
|---|---|---|
| File Parsers | 8 | Log, Bonds, Dump, Cell, Species, POS, OVITO, General |
| Standardized Outputs | 8 | Bocutoff/blcutoff, Cell dimensions, Atom mapping, Molecular weight |
| Smoothing Algorithms | 9 | segment_spline, adaptive_kalman, physics_constrained, robust_lowess, dynamic_wavelet, moving_avg, savgol, wavelet, ewma |
| Curve Fitting | 2 | polyfit.n polynomial, LOWESS local regression |
| Outlier Filters | 3 | zscore, MAD, IQR |
| Plot Types | 7 | line, scatter, boxplot, violin, surface (3D), contour, heatmap |
| Animation Modes | 4 | isograph, bar, line, reacdraw (3D bond animation) |
| MCP Tools | 25 | Full tool suite exposed via Model Context Protocol |

## Quick Start

```bash
# Install
git clone https://github.com/gqiang138/LMPSmart
cd lmpsmart
pip install -e .

# CLI
python -m lmpsmart arrange --path ./data --modes Log,Bonds,Dump
python -m lmpsmart agent --goal "plot energy vs time from output/arrange/dataoflog.csv"

# MCP (stdio — OpenCode, Claude Desktop)
python -m lmpsmart.api.mcp_server

# MCP (HTTP — Cherry Studio, remote)
python -m lmpsmart.api.mcp_server --http --port 8765

# Python API
python -m lmpsmart config --show
from lmpsmart import arrange, smooth
df = arrange("data/", modes=["Log", "Bonds"])
```

## Architecture

```
Input files (LAMMPS)
       ↓
   Arrange Layer         ← 8 parsers + 8 standardized outputs + glob batch + YAML config
       ↓
    DataFrame
       ↓
   Mapping Layer         ← 9 smoothers + curve fitting + 3 filters + 7 plots + 4 animations
       ↓
    Output files
       ↑
   Agent Controller      ← plan_from_goal() → execute()
```

## Agent Tools (25 total)

```
arrange, load_config,
read_log, read_bonds, read_dump, read_data,
read_cell, read_species, read_pos, read_general,
smooth, filter_outliers, fit, plot, animation,
groupby_aggregate, belong_filter, column_rename,
select_columns, merge_data,
molecular_weight, find_elements, atom_type,
detect_encoding, autocode
```

## MCP Integration

lmpsmart exposes all 25 tools via MCP. Connect any MCP-compatible host:

- **OpenCode**: `opencode mcp add lmpsmart <python> -m lmpsmart.api.mcp_server`
- **Cherry Studio**: HTTP transport on port 8765
- **Claude Desktop**: `claude_desktop_config.json` entry

The host's LLM handles planning; lmpsmart handles execution only.

## Examples

RDX molecular dynamics simulation data — see `output/`:

| Directory | Contents |
|-----------|----------|
| `output/arrange/` | 6 CSV files parsed from RDX simulation |
| `output/plot/` | 10 PNG plots from parsed data |

```bash
python -m lmpsmart arrange --path ./data/RDX --modes Log,Bonds,Dump,Cell,Species,POS
```

## Reproducibility

Every tool call is logged to `logs/agent_session_{session_id}.jsonl`:

```json
{"log_id": "a1b2c3d4e5f6", "timestamp": "...",
 "tool": "arrange", "input": {"modes": ["Log"]},
 "execution_steps": ["arrange: modes=['Log'], path=./data"],
 "output_summary": {"shape": [100, 20]},
 "status": "success", "elapsed_ms": 234}
```

## Requirements

- Python >= 3.10
- Core: numpy, pandas, scipy, statsmodels, pyyaml, pydantic, openpyxl, chardet
- Visualization: matplotlib, pillow (for animation GIF output)
- Optional: pykalman (adaptive_kalman), pywavelets (wavelet smoother), mcp (MCP server)

## License

GNU General Public License v3.0 (GPL-3.0)

Copyright (c) 2025 Qiang Gan
