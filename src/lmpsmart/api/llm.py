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
    "arrange": {"path": "str", "modes": "list[str]", "timestep": "float", "encoding": "str"},
    "read_log": {"log_path": "str", "log_indices": "list[int]|null", "supercell": "str|null"},
    "read_bonds": {"bonds_path": "str"},
    "read_dump": {"dump_path": "str"},
    "read_data": {"data_path": "str"},
    "read_cell": {"dump_path": "str"},
    "read_species": {"species_path": "str"},
    "read_pos": {"pos_path": "str"},
    "read_general": {"file_path": "str"},
    "smooth": {"data": "list[float]", "method": "str"},
    "filter_outliers": {"time_col": "str", "value_col": "str", "methods": "str|list[str]", "threshold": "float"},
    "molecular_weight": {"formula": "str"},
    "find_elements": {"formula_str": "str"},
    "atom_type": {"mass_value": "float"},
    "detect_encoding": {"file_path": "str"},
    "autocode": {"file_path": "str"},
}

SYSTEM_PROMPT_TEMPLATE = (
    'You are lmpsmart, a LAMMPS molecular dynamics data processing Agent.\n\n'
    'You help users parse, smooth, and filter LAMMPS simulation data for energetic materials research.\n\n'
    'Available tools (each takes keyword arguments):\n{tool_schema}\n\n'
    'Rules:\n'
    '1. Analyze the user\'s natural language request\n'
    '2. Return a JSON plan array with one or more tool calls\n'
    '3. Each tool call: {{"tool": "toolname", "params": {{...}}}}\n'
    '4. Only use tools from the list above\n'
    '5. Be concise — return ONLY the JSON, no explanation\n'
    '6. For "arrange" modes use: Log, Bonds, Dump, Cell, Species, POS, OVITO, General\n'
    '7. For "smooth" methods: moving_avg, savgol, ewma, segment_spline, adaptive_kalman, physics_constrained, robust_lowess, dynamic_wavelet, wavelet\n'
    '8. For "filter_outliers" methods: zscore, mad, iqr\n'
    '9. If ambiguous, return a clarifying question\n\n'
    'Example: user "parse log file and smooth temperature with savgol"\n'
    'Response: [{{"tool": "arrange", "params": {{"modes": ["Log"]}}}}, {{"tool": "smooth", "params": {{"method": "savgol"}}}}]\n\n'
    'User: "{goal}"\n'
    'Response:'
)


def _local_generate(base_url: str, model: str, prompt: str, timeout: int) -> str:
    payload = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.1, "num_predict": 512},
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{base_url}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))["response"]


def _online_generate(base_url: str, api_key: str, model: str, prompt: str, timeout: int) -> str:
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": 512,
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


def generate(prompt: str, cfg: dict[str, Any] | None = None) -> str:
    if cfg is None:
        cfg = load_llm_config()
    provider = cfg.get("provider", PROVIDER_LOCAL)
    base_url = cfg.get("base_url", "http://localhost:11434").rstrip("/")
    timeout = cfg.get("timeout", 120)
    if provider == PROVIDER_ONLINE:
        api_key = cfg.get("api_key", "")
        model = cfg.get("default_model", "gpt-4o-mini")
        return _online_generate(base_url, api_key, model, prompt, timeout)
    else:
        model = cfg.get("default_model", "qwen3:8b")
        return _local_generate(base_url, model, prompt, timeout)


def is_available(cfg: dict[str, Any] | None = None) -> bool:
    if cfg is None:
        cfg = load_llm_config()
    try:
        generate("hi", cfg)
        return True
    except Exception:
        return False


def parse_response(raw: str) -> list[dict[str, Any]]:
    raw = raw.strip()
    for line in raw.split("\n"):
        line = line.strip()
        if not line:
            continue
        if line.startswith("[") or line.startswith("{{"):
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                pass
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return []


def plan(goal: str, task: str = "plan", cfg: dict[str, Any] | None = None) -> list[dict[str, Any]]:
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
        raw = _online_generate(base_url, api_key, model, prompt, cfg.get("timeout", 120))
    else:
        raw = _local_generate(cfg.get("base_url", "http://localhost:11434").rstrip("/"), model, prompt, cfg.get("timeout", 120))
    return parse_response(raw)
