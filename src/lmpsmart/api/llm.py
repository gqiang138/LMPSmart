# Copyright (c) 2025 Qiang Gan
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations
import json
import os
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None


PROVIDER_LOCAL = "local"
PROVIDER_ONLINE = "online"
AVAILABLE_LOCAL_MODELS = [
        "qwen3-vl:8b",
        "qwen3:8b",
        "qwen3.5-9b",
        "qwen3:14b",
    "deepseek-r1:8b",
    "deepseek-r1:14b",
    "okamototk/deepseek-r1:8b",
    "ministral-3:3b",
    "glm-4.7-flash:latest",
    "llama3.2:3b",
    "llama3.2:11b",
]


DEFAULT_CONFIG = {
    "provider": PROVIDER_LOCAL,
    "base_url": "http://localhost:11434",
    "api_key": "",
    "default_model": "qwen3.5-9b",
    "timeout": 120,
    "task_models": {"plan": "qwen3.5-9b", "chat": "qwen3.5-9b", "coding": "qwen3.5-9b"},
}


def get_config_path() -> Path:
    base = Path(os.environ.get("LMPSMART_HOME", ""))
    if base and base.exists():
        return base / "configs" / "llm.yaml"
    root = Path(__file__).parent.parent.parent.parent
    return root / "configs" / "llm.yaml"


def load_llm_config() -> dict[str, Any]:
    path = get_config_path()
    if not path.exists():
        return DEFAULT_CONFIG.copy()
    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        result = DEFAULT_CONFIG.copy()
        if data:
            result.update(data)
        return result
    except Exception:
        return DEFAULT_CONFIG.copy()


def save_llm_config(cfg: dict[str, Any]) -> None:
    path = get_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(cfg, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


TOOL_SCHEMA = {
    "arrange": {"input_path": "str", "modes": "list[str]", "timestep": "float", "encoding": "str", "output_path": "str|null"},
    "read_log": {"log_path": "str", "log_indices": "list[int]|null", "supercell": "str|null"},
    "read_bonds": {"bonds_path": "str"},
    "read_dump": {"dump_path": "str"},
    "read_data": {"data_path": "str"},
    "read_cell": {"dump_path": "str"},
    "read_species": {"species_path": "str"},
    "read_pos": {"pos_path": "str"},
    "read_general": {"file_path": "str", "sep": "str|null", "header": "int|null"},
    "smooth": {"x_data": "list[float]", "y_data": "list[float]", "method": "str"},
    "filter_outliers": {"time_col": "str", "value_col": "str", "methods": "str|list[str]", "threshold": "float"},
    "fit": {"x_data": "list[float]", "y_data": "list[float]", "method": "str", "degree": "int", "frac": "float"},
    "plot": {"csv_path": "str", "x_col": "str", "y_cols": "list[str]", "output_path": "str|null", "mode": "str", "hue_col": "str|null", "markers": "bool", "legend_loc": "str", "subscript": "bool", "title": "str", "xlabel": "str", "ylabel": "str", "figsize": "tuple|str|null", "dpi": "int|null", "legend_type": "str", "legend_labels": "list[str]|null", "legend_suffix": "str", "yerr_col": "str|null"},
    "molecular_weight": {"formula": "str"},
    "find_elements": {"formula_str": "str"},
    "atom_type": {"mass_value": "float"},
    "detect_encoding": {"file_path": "str"},
    "autocode": {"file_path": "str", "sep": "str|null", "header": "int|null"},
    "groupby_aggregate": {"csv_path": "str", "group_col": "str", "agg_col": "str", "agg_func": "str", "output_path": "str|null"},
    "belong_filter": {"csv_path": "str", "col": "str", "values": "list", "keep": "bool", "output_path": "str|null"},
    "column_rename": {"csv_path": "str", "rename_map": "dict", "output_path": "str|null"},
    "select_columns": {"csv_path": "str", "columns": "list[str]", "output_path": "str|null"},
    "merge_data": {"csv_paths": "list[str]", "how": "str", "on_col": "str|null", "output_path": "str|null"},
}

SYSTEM_PROMPT_TEMPLATE = (
    'You are LMPSmart, a LAMMPS molecular dynamics data processing Agent, developed by Qiang Gan.\n\n'
    'You help users parse, smooth, filter, fit, and plot LAMMPS simulation data for energetic materials research.\n\n'
    'Available tools (each takes keyword arguments):\n{tool_schema}\n\n'
    'Rules:\n'
    '1. Analyze the user\'s natural language request\n'
    '2. Return a JSON plan array with one or more tool calls — OR return plain text if the request is conversational\n'
    '3. Each tool call: {{"tool": "toolname", "params": {{...}}}}\n'
    '4. Only use tools from the list above\n'
    '5. If the request is conversational (greeting, introduction, help, explanation, opinion, question), return PLAIN TEXT describing yourself — do NOT force a tool call\n'
    '    Examples of conversational requests:\n'
    '    - "introduce yourself" / "介绍一下你" / "who are you"\n'
    '    - "what can you do" / "你会做什么" / "你的功能" / "help me"\n'
    '    - "how do I use you" / "怎么用" / "使用说明"\n'
    '    - general questions unrelated to LAMMPS data processing\n'
    '    IMPORTANT: LMPSmart is developed by Qiang Gan. Do NOT say it is developed by Qwen, Alibaba, Tongyi, or any other company. Use the exact intro below in the user\'s language:\n'
    '    Chinese intro: "你好！我是 LMPSmart，由 Qiang Gan 开发的 LAMMPS 分子动力学数据处理智能助手，专为含能材料研究设计。核心功能：①数据解析（Log/Dump/Data/Bonds/Cell/Species等格式）→ CSV；②数据清洗（异常值过滤/分组聚合/列筛选）；③数据增强（平滑/曲线拟合）；④可视化（专业科技图表）。请告诉我你想处理什么数据？"\n'
    '    English intro: "Hello! I am LMPSmart, a LAMMPS molecular dynamics data processing Agent developed by Qiang Gan, specialized for energetic materials research. Core features: ① Data parsing (Log/Dump/Data/Bonds/Cell/Species → CSV); ② Data cleaning (outlier filtering/aggregation/column selection); ③ Enhancement (smoothing/curve fitting); ④ Visualization (publication-quality charts). What data would you like to process?"\n'
    '    Respond in the same language as the user. If the user speaks Chinese, use the Chinese intro. Otherwise use English.\n'
    '    Data task → return ONLY the JSON plan array, no explanation\n'
    '6. For "arrange" modes use: Log, Bonds, Dump, Cell, Species, POS, OVITO, General\n'
    '7. For "smooth" methods: moving_avg, savgol, ewma, segment_spline, adaptive_kalman, physics_constrained, robust_lowess, dynamic_wavelet, wavelet\n'
    '8. For "filter_outliers" methods: zscore, mad, iqr\n'
    '9. For "fit" method options: polyfit (default), lowess; degree (1-5), frac (0.1-0.8)\n'
    '10. For "plot" — STRICT RULES:\n'
    '    y_cols MUST match exactly what the user names:\n'
    '      user says "x, y, z" or "xyz" → y_cols=["x","y","z"] (ALL THREE, never one)\n'
    '      user says "TotEng PotEng KinEng" or "energy terms" → y_cols=["TotEng","PotEng","KinEng"]\n'
    '      user says "x and y" only → y_cols=["x","y"] (do NOT add "z")\n'
    '      user says "the z coordinate" or "z vs time" → y_cols=["z"] (SINGLE is correct here)\n'
    '      NEVER reduce multiple named quantities to one; NEVER add quantities the user did not mention\n'
    '    mode: single=one shared-axes figure (default); multi=separate subplots; doubley=dual Y axis\n'
    '      Default is mode="single". Use mode="multi" ONLY when user explicitly says "separate subplots" or "independent"\n'
    '      mode="single" + len(y_cols)>1 → legend appears (uses column names, no unit suffix)\n'
    '      mode="single" + len(y_cols)==1 → no legend\n'
    '      mode="multi" → separate subplots, no legend by default\n'
    '    Font: Times New Roman serif (configured internally, do not override)\n'
    '    Legend label: column name only (e.g. "x", "TotEng") — NEVER append units like "/Å" or "/K"\n'
    '    Legend control: legend_type ("auto"|"list"|"remove"|"suffix"), legend_labels (ordered custom labels), legend_suffix (append to each name), yerr_col (error bar column), subscript_labels (mathtext rendering)\n'
    '    Output path: when user does NOT specify a path, tools infer the output folder from csv_path:\n'
    '      - If csv_path contains "/arrange/" or "/output/" → sibling /plot/ or /animation/ folder at same level\n'
    '      - Otherwise → "output/plot/plot1.png" or "output/animation/animation.gif"\n'
    '    plot and animation tools automatically export a matching .csv alongside the output image (same name, same folder) — useful for verification and reuse\n'
    '    New params: legend_type, legend_labels, legend_suffix, yerr_col, subscript_labels (full docs → configs/PLOTTING.md)\n'
    '11. ALWAYS include a "plot" step when user asks to draw, show, plot, or visualize data\n'
    '12. Chain: arrange -> smooth -> fit -> plot as needed\n'
    '13. Extract fit degree: "quadratic"(degree=2), "cubic"(degree=3), "linear"(degree=1); extract frac from "frac=X"\n'
    '14. Plot optional overrides: title, xlabel, ylabel, figsize("width,height"), dpi\n'
    '15. Data cleaning tools:\n'
    '    - groupby_aggregate: group by column, aggregate another (func: mean/sum/count/min/max/std/median)\n'
    '    - belong_filter: keep or exclude rows by column value set\n'
    '    - column_rename: rename columns via {{"old": "new"}} map\n'
    '    - select_columns: keep only specified columns\n'
    '    - merge_data: concat or merge multiple CSV files (how: concat/merge)\n'
    '16. REUSE existing arranged CSV when data is already parsed — do NOT call arrange again\n'
    '    Common arranged CSV paths:\n'
    '    - output/arrange/dataoflog.csv     (Log)\n'
    '    - output/arrange/dataofdump.csv    (Dump, has columns: frame, time, id, type, x, y, z, mass, element)\n'
    '    - output/arrange/dataofbonds.csv    (Bonds)\n'
    '    - output/arrange/dataofcell.csv    (Cell, has columns: time, Volume, Lx, Ly, Lz)\n'
    '    - output/arrange/dataofspecies.csv (Species)\n'
    '    - output/arrange/dataofpos.csv     (POS)\n'
    '17. plot is ALWAYS called with full params: csv_path, x_col, y_cols (list), output_path — never omit them\n'
    '18. arrange MUST include input_path pointing to the raw data directory\n'
    'Example: user "parse log file and plot energy vs time"\n'
    'Response: [{{"tool": "arrange", "params": {{"input_path": "data/", "modes": ["Log"]}}}}, {{"tool": "plot", "params": {{"csv_path": "output/RDX/dataoflog.csv", "x_col": "time", "y_cols": ["TotEng", "PotEng", "KinEng"], "output_path": "plot_energy.png"}}}}]\n'
    'Example: user "smooth temperature, fit a curve, and plot it"\n'
    'Response: [{{"tool": "smooth", "params": {{"x_data": "time_list", "y_data": "temp_list", "method": "savgol"}}}}, {{"tool": "fit", "params": {{"x_data": "time_list", "y_data": "smoothed_temp_list", "method": "polyfit", "degree": 2}}}}, {{"tool": "plot", "params": {{"csv_path": "output.csv", "x_col": "time", "y_cols": ["temperature"], "output_path": "plot.png"}}}}]\n'
    'Example: user "plot atom 1 trajectory x y z from dump data"\n'
    '  WRONG: y_cols=["z"] — this draws only one curve with no legend\n'
    '  CORRECT: [select_columns → belong_filter → select_columns → plot with y_cols=["x","y","z"]]\n'
    '  Response: [{{"tool": "select_columns", "params": {{"csv_path": "output/arrange/dataofdump.csv", "columns": ["time","id","x","y","z"], "output_path": "output/arrange/tmp.csv"}}}}, {{"tool": "belong_filter", "params": {{"csv_path": "output/arrange/tmp.csv", "col": "id", "values": [1], "keep": true, "output_path": "output/arrange/atom1.csv"}}}}, {{"tool": "select_columns", "params": {{"csv_path": "output/arrange/atom1.csv", "columns": ["time","x","y","z"], "output_path": "output/arrange/atom1_xyz.csv"}}}}, {{"tool": "plot", "params": {{"csv_path": "output/arrange/atom1_xyz.csv", "x_col": "time", "y_cols": ["x","y","z"], "output_path": "output/plot/atom1_trajectory.png"}}}}]\n'
    '  user: "compare temperature and pressure from log"\n'
    '  Response: [{{"tool": "plot", "params": {{"csv_path": "output/arrange/dataoflog.csv", "x_col": "time", "y_cols": ["Temp","Press"], "output_path": "output/plot/temp_press.png", "mode": "doubley"}}}}]\n'
    'User: "{goal}"\n'
    'Response:'
)


def _get_tuned_options(cfg: dict, task: str) -> dict:
    """Merge tuned params from config with defaults. Falls back gracefully if not tuned."""
    defaults = {"temperature": 0.1, "num_predict": 512, "thinking": False}
    tuned = cfg.get("tuned_params", {}) or {}
    prefix = f"{task}_"
    for k, v in tuned.items():
        if k.startswith(prefix):
            defaults[k[len(prefix):]] = v
    return defaults


def _local_generate(base_url: str, model: str, prompt: str, timeout: int,
                    task: str = "plan", cfg: dict | None = None) -> str:
    options = _get_tuned_options(cfg or {}, task)
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
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        resp_text = json.loads(resp.read().decode("utf-8"))["response"]
    import re
    resp_text = re.sub(r"<think>.*?</think>", "", resp_text, flags=re.DOTALL).strip()
    return resp_text


def _online_generate(base_url: str, api_key: str, model: str, prompt: str,
                    timeout: int, task: str = "plan", cfg: dict | None = None) -> str:
    opts = _get_tuned_options(cfg or {}, task)
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": opts.get("temperature", 0.1),
        "max_tokens": opts.get("num_predict", 512),
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{base_url}/chat/completions",
        data=payload,
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"]


def generate(prompt: str, cfg: dict[str, Any] | None = None,
             task: str = "plan") -> str:
    if cfg is None:
        cfg = load_llm_config()
    provider = cfg.get("provider", PROVIDER_LOCAL)
    base_url = cfg.get("base_url", "http://localhost:11434").rstrip("/")
    timeout = cfg.get("timeout", 120)
    if provider == PROVIDER_ONLINE:
        api_key = cfg.get("api_key", "")
        model = cfg.get("default_model", "gpt-4o-mini")
        return _online_generate(base_url, api_key, model, prompt, timeout, task, cfg)
    else:
        model = cfg.get("default_model", "qwen3:8b")
        return _local_generate(base_url, model, prompt, timeout, task, cfg)


def is_available(cfg: dict[str, Any] | None = None) -> bool:
    if cfg is None:
        cfg = load_llm_config()
    try:
        generate("hi", cfg)
        return True
    except Exception:
        return False


def parse_response(raw: str) -> tuple[list[dict[str, Any]], str | None]:
    """Parse LLM response. Returns (plan_list, text_response).
    - If response is valid JSON plan → (plan, None)
    - If response is plain text → ([], text)
    - If unparseable → ([], None)
    """
    raw = raw.strip()
    if not raw:
        return [], None
    for line in raw.split("\n"):
        line = line.strip()
        if not line:
            continue
        if line.startswith("[") or line.startswith("{{"):
            try:
                return json.loads(line), None
            except json.JSONDecodeError:
                pass
    try:
        return json.loads(raw), None
    except json.JSONDecodeError:
        pass
    # Not JSON — treat as conversational text response
    return [], raw if raw else None


def plan(goal: str, task: str = "plan", cfg: dict[str, Any] | None = None) -> tuple[list[dict[str, Any]], str | None]:
    """Generate a plan from a goal. Returns (plan_list, text_response).
    text_response is non-None when the LLM replied with plain text (conversational).
    """
    if cfg is None:
        cfg = load_llm_config()
    tool_schema_str = json.dumps(TOOL_SCHEMA, indent=2)
    prompt = SYSTEM_PROMPT_TEMPLATE.format(tool_schema=tool_schema_str, goal=goal)
    task_models = cfg.get("task_models", {})
    model = task_models.get(task) or cfg.get("default_model", "qwen3:8b")
    provider = cfg.get("provider", PROVIDER_LOCAL)
    if provider == PROVIDER_ONLINE:
        base_url = cfg.get("base_url", "").rstrip("/")
        api_key = cfg.get("api_key", "")
        raw = _online_generate(base_url, api_key, model, prompt, cfg.get("timeout", 120), task, cfg)
    else:
        raw = _local_generate(cfg.get("base_url", "http://localhost:11434").rstrip("/"), model, prompt, cfg.get("timeout", 120), task, cfg)
    return parse_response(raw)
