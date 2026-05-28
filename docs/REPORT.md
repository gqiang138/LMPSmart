# Technical Report: lmpsmart — LAMMPS Data Agent

## 1. Problem Statement

Molecular dynamics (MD) simulations using LAMMPS with the ReaxFF reactive force field generate massive time-series datasets containing thermodynamic properties (temperature, pressure, energy), bond topology evolution, atomic trajectories, and chemical species concentrations. Analyzing these datasets for energetic materials research requires parsing heterogeneous file formats, applying signal processing algorithms, and filtering measurement noise — all while maintaining full reproducibility.

Traditional approaches rely on GUI-based tools (e.g., OVITO, VMD) or bespoke scripts that hardcode parameters. The original `lmpanalysis.py` tool addressed this with a Tkinter GUI, but suffered from three critical limitations: no autonomous reasoning (all operations require manual user input), no reproducibility (actions are not logged), and hardcoded parameters that make batch processing impractical. This project重构将 GUI 架构转化为自主 Agent 架构，保留核心计算逻辑的同时实现可追溯性。

## 2. System Architecture

### 2.1 Three-Layer Architecture

The system implements a three-layer pipeline:

```
Input files (LAMMPS)
       ↓
  Arrange Layer         ← 8 parsers + glob batch + YAML config
       ↓
   DataFrame
       ↓
  Mapping Layer         ← 9 smoothers + 3 outlier filters
       ↓
   Output files
       ↑
  Agent Controller     ← plan_from_goal() → execute()
```

**Arrange Layer** (`arrange/readers.py`): Reads LAMMPS output files using regex-based parsers. Supports glob pattern matching for batch processing — multiple files of the same type produce `dataoflog.csv`, `dataoflog.split0.csv`, `dataoflog.split1.csv`, etc. Configuration is loaded entirely from `configs/default.yaml`, with no hardcoded values.

**Mapping Layer** (`mapping/smooth.py`, `mapping/filter.py`): Applies signal processing algorithms to DataFrames. All parameters are configurable via YAML. Parallel execution is supported via ThreadPoolExecutor.

**Agent Layer** (`api/agent.py`): Orchestrates the pipeline. The `LmpparseAgent` class receives a natural language goal, decomposes it into a tool execution plan via `plan_from_goal()`, executes each step via `execute()`, and logs every operation via `ExecutionLogger`.

### 2.2 Config-Driven Design

All behavior is driven by `configs/default.yaml`, migrated from the original `default.txt`. Key sections:

```yaml
cutoff:
  bonds: [CC, CN, CO, CH, NN, NO, NH, OO, OH, HH, NC, OC, HC, ON, HN, HO, AlC, AlH, AlN, AlO, CAl, HAl, NAl, OAl, AlAl, C, N, O, H, Al]
  bocutoff: [0.55, 0.30, 0.65, ...]   # bond order thresholds
  blcutoff: [1.8, 2.1, 1.9, ...]      # bond length thresholds

filerule1:
  logfilename: "log.lammps*"
  bondsfilename: "bonds.reax.bof"
  dumpfilename: "*.trj"

bonds_limit:
  Al: 6; C: 4; H: 1; N: 3; O: 2      # per-element bond count limits
```

The `CutoffConfig`, `FileRule1`, and `PlotSet` Pydantic models validate the YAML at load time. YAML 1.1 boolean parsing requires quoting `NO`, `ON`, and `NC` to prevent misinterpretation as boolean literals.

## 3. Smoothing Algorithms

Nine smoothing methods are implemented, each targeting different noise characteristics:

**segment_spline**: Splits the time series at inflection points detected by curvature analysis, then fits cubic splines within each segment. Parameters: `spline_threshold` (inflection sensitivity), `spline_s` (smoothing factor).

**adaptive_kalman**: Applies a Kalman filter with noise covariance estimated from residuals. Uses `pykalman.KalmanFilter` with initial state mean from first data point, observation covariance = 1, and adaptive transition covariance = `clip(std(residuals) × 0.1, 1e-6, 0.5)`.

**physics_constrained**: Fits a polynomial baseline while enforcing physical constraints (e.g., energy must be non-negative). Uses constrained least squares via `scipy.optimize.minimize`.

**robust_lowess**: Locally weighted scatterplot smoothing using `statsmodels.nonparametric.lowess` with bisquare robust M-estimator to downweight outliers.

**dynamic_wavelet**: Discrete wavelet transform (pywt) with level selected by平稳性 (stationarity) heuristic, soft thresholding using the universal threshold λ = σ√(2log n).

**moving_avg**: Simple rolling mean with configurable window size. Fast, O(n) complexity.

**savgol**: Savitzky-Golay filter via `scipy.signal.savgol_filter`. Fits polynomials of configurable order within a sliding window — preserves peaks better than moving average.

**wavelet**: Alias for dynamic_wavelet; applies DWT denoising with universal threshold.

**ewma**: Exponentially weighted moving average with configurable span α = 2/(span+1). Gives more weight to recent observations.

## 4. Outlier Filtering

Three methods for removing anomalous measurements:

**zscore**: Computes z = |x - μ| / σ. Points with z > threshold (default 3.0) are flagged as outliers. Uses sample std (ddof=1).

**MAD (Modified Z-score)**: Uses Median Absolute Deviation as a robust dispersion measure: MAD = median(|x - median(x)|), Modified Z = 0.6745 × (x - median) / MAD. Threshold 3.5 is equivalent to 3σ for normal distributions but robust to up to 50% outliers.

**IQR (Interquartile Range)**: Defines bounds as [Q1 - k×IQR, Q3 + k×IQR] where IQR = Q3 - Q1, default k = 1.5. Non-parametric, requires no distributional assumption.

All methods operate directly on the `value_col` Series without groupby — LAMMPS time-series data has unique timestamps per row, so groupby adds no statistical value.

## 5. Agent Architecture

### 5.1 Agent Definition

An Agent is defined by five core capabilities:感知 (Perceive), 推理 (Reason), 规划 (Plan), 行动 (Act), and 记忆 (Remember). The `LmpparseAgent` class implements all five:

- **Perceive**: Reads input path and natural language goal
- **Plan**: `plan_from_goal()` uses LLM inference (Ollama/OpenAI) with keyword matching as fallback when LLM is unavailable
- **Act**: `execute()` calls functions from `TOOL_REGISTRY`
- **Remember**: `ExecutionLogger` writes every call to JSONL

### 5.2 Tool Registry

18 tools are registered, mapping natural language to function calls:

| Tool Category | Tools |
|---|---|
| Arrange | `arrange`, `load_config` |
| Read | `read_log`, `read_bonds`, `read_dump`, `read_data`, `read_cell`, `read_species`, `read_pos`, `read_general` |
| Mapping | `smooth`, `filter_outliers` |
| Chemistry | `molecular_weight`, `find_elements`, `atom_type`, `detect_encoding`, `autocode` |

### 5.3 Execution Logger

Every tool invocation writes a JSONL record:

```json
{
  "log_id": "a1b2c3d4e5f6",
  "timestamp": "2026-05-27T23:00:00",
  "session_id": "x9y8z7",
  "tool": "arrange",
  "input": {"modes": ["Log", "Bonds"]},
  "execution_steps": ["arrange: modes=['Log', 'Bonds'], path=./data"],
  "output_summary": {"shape": [100, 20], "dtypes": {...}},
  "warnings": [],
  "status": "success",
  "elapsed_ms": 234
}
```

DataFrames are summarized by shape and dtype (not serialized), preventing log bloat.

## 6. Comparison: GUI vs Agent Architecture

| Aspect | Original Tkinter GUI | New Agent Architecture |
|---|---|---|
| Reasoning engine | None | LLM inference + keyword fallback |
| Tool selection | User clicks button | Autonomous from goal |
| Iteration/reflection | None | Execute and log |
| Config | Partially hardcoded | Fully YAML-driven |
| Batch processing | Manual, one at a time | Glob + split naming |
| Reproducibility | Manual (user notes) | Automatic JSONL logging |
| Entry point | GUI window (requires display) | CLI or Python API |
| LLM integration | None | Fully integrated (Ollama + OpenAI-compatible) |

The Tkinter GUI was a user interface, not an Agent. It mapped user clicks to fixed functions without any reasoning, planning, or autonomous decision-making. The重构 preserves all computational logic while wrapping it in an Agent controller that can accept natural language goals.

## 7. Installation and Usage

```bash
pip install lmpsmart
python -m lmpsmart config --show
python -m lmpsmart arrange --path ./data --modes Log,Bonds,Dump
python -m lmpsmart agent --goal "arrange log files and smooth temperature"
```

Python API:
```python
from lmpsmart import arrange, smooth, filter_outliers
df = arrange("data/", modes=["Log", "Bonds"])
smoothed = smooth(df["temperature"], method="savgol")
filtered = filter_outliers(df, "time", "temperature", "zscore", 3.0)
```

## 8. Reproducibility Mechanism

The execution logger enables complete reproducibility:

1. Every tool call is logged with session_id, timestamp, input summary, and output summary
2. Session summary (`logger.summary()`) provides total_calls, success/failed counts, tools used
3. JSONL files in `logs/` directory can be replayed to reconstruct any analysis run
4. Configuration is versioned in `configs/default.yaml` (git-tracked)

## 9. Limitations and Future Work

**Current status**: LLM inference is fully integrated — `plan_from_goal()` tries Ollama or OpenAI-compatible API first, falls back to keyword matching if LLM is unavailable. Config via `llm setup` (local Ollama or online API).

**Current limitations**: The nine smoothing algorithms cover most MD time-series use cases but some physics-informed constraints are simplified.

**Future directions**:
1. **Web UI**: REST API + React frontend for non-CLI users
2. **Cloud deployment**: Docker container for HPC cluster integration
3. **Additional formats**: phonopy, XDATCAR support
4. **Statistical validation**: Automated hypothesis testing on smoothed vs. raw data

## 10. Conclusion

lmpsmart transforms LAMMPS MD data analysis from a GUI-driven, hardcoded workflow into a config-driven, reproducible Agent architecture. The three-layer design (Arrange → Mapping → Agent) separates concerns cleanly: file parsing is handled by specialized readers, signal processing by configurable algorithms, and workflow orchestration by the Agent controller. The YAML-based configuration eliminates hardcoding, the execution logger enables full reproducibility, and the Agent paradigm makes the tool accessible via natural language while maintaining computational power. All core computational logic from the original ~2800-line GUI has been preserved and refactored into a modular, testable architecture.
