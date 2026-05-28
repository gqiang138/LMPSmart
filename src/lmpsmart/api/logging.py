# Copyright (c) 2025 Qiang Gan
# SPDX-License-Identifier: GPL-3.0-or-later
"""Execution logger for Agent traceability."""
from __future__ import annotations
import json
import time
import uuid
import datetime
from pathlib import Path
from typing import Any
import pandas as pd


class ExecutionLogger:
    def __init__(self, log_dir: str | Path | None = None):
        self.log_dir = Path(log_dir) if log_dir else Path.cwd() / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.session_id = str(uuid.uuid4())[:8]
        self.log_file = self.log_dir / f"agent_session_{self.session_id}.jsonl"
        self.entries: list[dict] = []

    def log(
        self,
        tool: str,
        input_data: dict[str, Any],
        execution_steps: list[str],
        output: Any = None,
        warnings: list[str] | None = None,
        status: str = "success",
        extra: dict[str, Any] | None = None,
    ) -> str:
        entry = {
            "log_id": str(uuid.uuid4())[:12],
            "timestamp": datetime.datetime.now().isoformat(),
            "session_id": self.session_id,
            "tool": tool,
            "input": self._safe_serialize(input_data),
            "execution_steps": execution_steps,
            "output_summary": self._summarize(output),
            "warnings": warnings or [],
            "status": status,
            "elapsed_ms": getattr(self, "_elapsed_ms", 0),
        }
        if extra:
            entry.update(extra)
        self.entries.append(entry)
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return entry["log_id"]

    def _safe_serialize(self, data: Any) -> Any:
        if isinstance(data, pd.DataFrame):
            return {"__dataframe__": True, "shape": list(data.shape), "columns": data.columns.tolist()}
        if isinstance(data, dict):
            return {k: self._safe_serialize(v) for k, v in data.items()}
        if isinstance(data, (list, tuple)):
            return [self._safe_serialize(x) for x in data]
        if isinstance(data, (str, int, float, bool, type(None))):
            return data
        return str(type(data).__name__)

    def _summarize(self, data: Any) -> Any:
        if isinstance(data, pd.DataFrame):
            return {"shape": list(data.shape), "dtypes": {k: str(v) for k, v in data.dtypes.items()}}
        if isinstance(data, dict):
            return {k: self._summarize(v) for k, v in list(data.items())[:5]}
        if isinstance(data, (list, tuple)):
            return f"list[{len(data)}]"
        return str(data)[:200]

    def get_log(self) -> list[dict]:
        entries = []
        if self.log_file.exists():
            with open(self.log_file, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        entries.append(json.loads(line))
        return entries

    def summary(self) -> dict:
        entries = self.get_log()
        return {
            "session_id": self.session_id,
            "total_calls": len(entries),
            "success": sum(1 for e in entries if e["status"] == "success"),
            "failed": sum(1 for e in entries if e["status"] == "failed"),
            "tools_used": list({e["tool"] for e in entries}),
        }
