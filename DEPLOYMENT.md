# Deployment Guide

## System Requirements

- Python >= 3.10
- pip
- Optional: pykalman (for adaptive_kalman smoother), pywavelets (for wavelet smoother)

## Installation

### Option A: Smart Installer (Recommended)

```bash
python install.py
```

Interactive wizard that:
1. Auto-detects conda / venv / pyenv / system Python environments
2. Creates new conda env (Python 3.12) or venv if needed
3. Installs core + optional packages
4. Verifies installation
5. Offers optional LLM configuration (can be skipped)

### Option B: Manual

```bash
# 1. Clone
git clone <repo>
cd lmpsmart

# 2. Create environment (optional)
conda create -n lmpsmart python=3.12 -y
conda activate lmpsmart

# 3. Install
pip install -e .

# 4. Verify
python -m lmpsmart config --show
```

### Option C: No environment, use current Python

```bash
pip install -e .
python -m lmpsmart config --show
```

### Post-install: Configure LLM (optional)

```bash
# Configure later — keyword fallback works without any LLM
python -m lmpsmart llm setup --provider local --model qwen3:8b
```

### Dependencies

Core (required):
```
numpy, pandas, scipy, statsmodels, pyyaml, pydantic, openpyxl, chardet
```

Optional (for all smoothers):
```
pykalman     # adaptive_kalman smoother
pywavelets   # wavelet smoother
matplotlib   # plotting
```

## Project Structure

```
lmpsmart/
├── configs/
│   └── default.yaml       ← All configuration (30 bond types, glob patterns, plot params)
├── src/lmpsmart/
│   ├── arrange/
│   │   ├── config.py     ← Pydantic YAML config loader
│   │   └── readers.py    ← 8 file parsers + arrange() main function
│   ├── mapping/
│   │   ├── smooth.py     ← 9 smoothing algorithms
│   │   └── filter.py     ← 3 outlier filters (zscore, MAD, IQR)
│   ├── core/
│   │   └── tools.py      ← Element tables, encoding detection, utils
│   └── api/
│       ├── agent.py       ← LmpparseAgent (plan + execute)
│       ├── tools.py       ← 18 tool wrappers
│       └── logging.py     ← ExecutionLogger (JSONL traceability)
├── docs/
│   └── REPORT.md         ← Technical report
├── DEPLOYMENT.md         ← This file
├── README.md
└── pyproject.toml
```

## CLI Full Reference

### arrange — Parse LAMMPS files

```bash
python -m lmpsmart arrange --path ./data --modes Log,Bonds,Dump
```

| Option        | Required | Description                              |
|---------------|----------|------------------------------------------|
| `--path`      | Yes      | Input directory                          |
| `--modes`     | Yes      | Comma-separated: Log,Bonds,Dump,Cell,Species,POS,OVITO,General |
| `--config`    | No       | YAML config path (default: configs/default.yaml) |
| `--timestep`  | No       | Time step in fs (default: 0.1)           |
| `--encoding`  | No       | File encoding (default: utf-8)            |
| `--ignored-time` | No    | Ignore first N ps (default: 0.0)          |

Output: `dataoflog.csv`, `dataofbonds.0.csv`, etc.

### smooth — Smooth time-series data

```bash
python -m lmpsmart smooth --data "[1,2,3,2,1,2,3,2,1]" --method moving_avg
python -m lmpsmart smooth --data values.csv --method savgol --output smoothed.csv
```

| Option     | Required | Description                        |
|------------|----------|------------------------------------|
| `--data`   | Yes      | JSON list or CSV file path          |
| `--method` | No       | One of: moving_avg, savgol, ewma, segment_spline, adaptive_kalman, physics_constrained, robust_lowess, dynamic_wavelet, wavelet (default: moving_avg) |
| `--output` | No       | Output CSV path                     |

### filter — Remove outliers

```bash
python -m lmpsmart filter --csv data.csv --value-col temperature --methods zscore --threshold 3.0
```

| Option        | Required | Description                              |
|---------------|----------|------------------------------------------|
| `--csv`       | Yes      | Input CSV file                           |
| `--time-col`  | No       | Time column name (default: time)          |
| `--value-col` | Yes      | Column to filter                         |
| `--methods`   | No       | zscore,mad,iqr or comma-combination      |
| `--threshold` | No       | Threshold value (default: 3.0)            |
| `--output`    | No       | Output CSV path                          |

### config — Show configuration

```bash
python -m lmpsmart config --show
```

### agent — Autonomous goal execution

```bash
python -m lmpsmart agent --goal "arrange log files and smooth temperature"
python -m lmpsmart agent --goal "arrange bonds and filter outliers with zscore" --dry-run
```

| Option       | Required | Description                          |
|--------------|----------|--------------------------------------|
| `--goal`     | Yes      | Natural language goal                 |
| `--dry-run`  | No       | Show plan without executing           |
| `--no-llm`   | No       | Use keyword matching instead of LLM   |

## LLM Configuration

Configure the LLM provider (local Ollama or online OpenAI-compatible API):

```bash
# Show current config
python -m lmpsmart llm show

# List available models
python -m lmpsmart llm list

# Test connection
python -m lmpsmart llm test

# Setup local Ollama (default)
python -m lmpsmart llm setup --provider local --base-url http://localhost:11434 --model qwen3:8b

# Setup online API (OpenRouter, OpenAI, etc.)
python -m lmpsmart llm setup --provider online \
    --base-url https://openrouter.ai/api/v1 \
    --api-key sk-or-xxxxx \
    --model anthropic/claude-3-haiku
```

Config file: `configs/llm.yaml`

```yaml
provider: local           # local | online
base_url: http://localhost:11434
api_key: ""              # required for online provider
default_model: qwen3:8b
timeout: 120
task_models:             # optional per-task model override
  plan: qwen3:8b         # task decomposition
  chat: qwen3:8b         # conversation mode
  coding: qwen3:8b       # code generation
```

When Ollama is unavailable, Agent falls back to keyword matching automatically.

## Configuration

Edit `configs/default.yaml`:

```yaml
# Bond types for ReaxFF analysis (30 types)
cutoff:
  bonds:
    - CC; - CN; - CO; - CH; - NN; - NO; - NH; ...

# Input file glob patterns
filerule1:
  logfilename: "log.lammps*"
  bondsfilename: "bonds.reax.bof"
  dumpfilename: "*.trj"

# Visualization
plotset:
  multifig:
    width: 14; high: 6; dpi: 600
```

## Reproducibility

Execution logs in `logs/agent_session_{session_id}.jsonl`:

```json
{
  "log_id": "abc123",
  "timestamp": "2026-05-27T23:00:00",
  "session_id": "s1a2b3",
  "tool": "arrange",
  "input": {"modes": ["Log", "Bonds"]},
  "execution_steps": ["arrange: modes=['Log', 'Bonds'], path=./data"],
  "output_summary": {"shape": [100, 20]},
  "status": "success"
}
```

To replay a session:
```python
from lmpsmart.api.logging import ExecutionLogger
logger = ExecutionLogger("logs")
summary = logger.summary()
```

## Troubleshooting

**ModuleNotFoundError: No module named 'lmpsmart'**
→ Run `pip install -e .` from project root

**YAML parsing error with bond types (NO, ON, NC)**
→ Already fixed: these are quoted in default.yaml

**adaptive_kalman / wavelet smoother unavailable**
→ Install optional deps: `pip install pykalman pywavelets`

**UTF-8 decode error**
→ Use `--encoding GBK` for Chinese Windows systems
