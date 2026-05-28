# Copyright (c) 2025 Qiang Gan
# SPDX-License-Identifier: GPL-3.0-or-later
"""18 Tool interfaces for lmpsmart Agent."""
from __future__ import annotations
import os
from pathlib import Path
from typing import Any
import pandas as pd
from lmpsmart.arrange.config import load_config
from lmpsmart.arrange.readers import (
    read_data, read_log, read_bonds, read_dump,
    read_cell, read_species, read_pos, read_ovito, read_general,
    arrange,
)
from lmpsmart.mapping.smooth import smooth, AVAILABLE_METHODS
from lmpsmart.mapping.filter import filter_outliers, filter_zscore, filter_mad, filter_iqr
from lmpsmart.core.tools import (
    ELEMENT_WEIGHT, ELEMENT_ATOMIC, ELEMENT_MASS,
    atom_type, atom_order, type_atom, find_elements,
    molecular_weight, detect_encoding, autocode, folderfilter, filefilter,
)
from lmpsmart.api.logging import ExecutionLogger

_logger: ExecutionLogger | None = None


def get_logger() -> ExecutionLogger:
    global _logger
    if _logger is None:
        _logger = ExecutionLogger()
    return _logger


def _step(msg: str) -> list[str]:
    return [msg]


# arrange tools (2)
def tool_arrange(
    input_path: str,
    modes: list[str],
    output_path: str | None = None,
    config_path: str | None = None,
    ignored_time: float = 0.0,
    timestep: float = 0.1,
    encoding: str = "utf-8",
    supercell: str | None = None,
    log_indices: list[int] | None = None,
) -> dict[str, Any]:
    logger = get_logger()
    sc = None
    if supercell:
        parts = supercell.split(",")
        sc = tuple(int(p.strip()) for p in parts)
    steps = _step(f"arrange: modes={modes}, path={input_path}")
    cfg = load_config(config_path) if config_path else None
    try:
        result = arrange(
            input_path=input_path, modes=modes, output_path=output_path,
            config=cfg, ignored_time=ignored_time, timestep=timestep,
            encoding=encoding, supercell=sc, log_indices=log_indices,
        )
        logger.log("arrange", {"input_path": input_path, "modes": modes}, steps, result, status="success")
        return {"status": "success", "files": list(result.keys()), "outputs": result}
    except Exception as e:
        logger.log("arrange", {"input_path": input_path, "modes": modes}, steps, None, [str(e)], "failed")
        raise


def tool_load_config(config_path: str | None = None) -> dict[str, Any]:
    cfg = load_config(config_path)
    steps = _step(f"load_config: {config_path or 'default'}")
    get_logger().log("load_config", {"config_path": config_path}, steps, {"cutoff_keys": cfg.cutoff.bonds[:5]}, status="success")
    return {
        "status": "success",
        "cutoff_bonds": cfg.cutoff.bonds,
        "bocutoff": cfg.cutoff.bocutoff,
        "blcutoff": cfg.cutoff.blcutoff,
        "filerule1": cfg.filerule1.model_dump(),
    }


# read tools (8)
def tool_read_log(log_path: str, log_indices: list[int] | None = None, supercell: str | None = None,
                   ignored_time: float = 0.0, timestep: float = 0.1) -> pd.DataFrame:
    sc = None
    if supercell:
        sc = tuple(int(p.strip()) for p in supercell.split(","))
    steps = _step(f"read_log: {log_path}")
    df = read_log(log_path, log_indices, sc, ignored_time, timestep)
    get_logger().log("read_log", {"log_path": log_path}, steps, df, status="success")
    return df


def tool_read_bonds(bonds_path: str, data_path: str | None = None,
                     ignored_time: float = 0.0, timestep: float = 0.1) -> pd.DataFrame:
    steps = _step(f"read_bonds: {bonds_path}")
    df = read_bonds(bonds_path, data_path, None, None, ignored_time, timestep)
    get_logger().log("read_bonds", {"bonds_path": bonds_path}, steps, df, status="success")
    return df


def tool_read_dump(dump_path: str, data_path: str | None = None,
                    ignored_time: float = 0.0, timestep: float = 0.1) -> pd.DataFrame:
    steps = _step(f"read_dump: {dump_path}")
    df = read_dump(dump_path, data_path, None, ignored_time, timestep)
    get_logger().log("read_dump", {"dump_path": dump_path}, steps, df, status="success")
    return df


def tool_read_data(data_path: str) -> dict[str, pd.DataFrame]:
    steps = _step(f"read_data: {data_path}")
    result = read_data(data_path)
    get_logger().log("read_data", {"data_path": data_path}, steps, result, status="success")
    return result


def tool_read_cell(dump_path: str, ignored_time: float = 0.0, timestep: float = 0.1) -> pd.DataFrame:
    steps = _step(f"read_cell: {dump_path}")
    df = read_cell(dump_path, ignored_time, timestep)
    get_logger().log("read_cell", {"dump_path": dump_path}, steps, df, status="success")
    return df


def tool_read_species(species_path: str, ignored_time: float = 0.0, timestep: float = 0.1) -> pd.DataFrame:
    steps = _step(f"read_species: {species_path}")
    df = read_species(species_path, ignored_time, timestep)
    get_logger().log("read_species", {"species_path": species_path}, steps, df, status="success")
    return df


def tool_read_pos(pos_path: str, ignored_time: float = 0.0, timestep: float = 0.1) -> pd.DataFrame:
    steps = _step(f"read_pos: {pos_path}")
    df = read_pos(pos_path, ignored_time, timestep)
    get_logger().log("read_pos", {"pos_path": pos_path}, steps, df, status="success")
    return df


def tool_read_general(file_path: str, sep: str | None = None, header: int | None = None) -> pd.DataFrame:
    steps = _step(f"read_general: {file_path}")
    df = read_general(file_path, sep, header)
    get_logger().log("read_general", {"file_path": file_path}, steps, df, status="success")
    return df


# mapping tools (4)
def tool_smooth(data: list[float] | pd.Series, method: str = "moving_avg", **kwargs) -> list[float]:
    steps = _step(f"smooth: method={method}")
    if method not in AVAILABLE_METHODS:
        raise ValueError(f"method must be one of {AVAILABLE_METHODS}")
    result = smooth(data, method=method, **kwargs)
    get_logger().log("smooth", {"method": method, "kwargs": kwargs}, steps, result, status="success")
    return result


def tool_filter_outliers(df: pd.DataFrame, time_col: str, value_col: str,
                          methods: str | list[str] = "zscore", threshold: float = 3.0) -> pd.DataFrame:
    steps = _step(f"filter_outliers: methods={methods}, threshold={threshold}")
    result = filter_outliers(df, time_col, value_col, methods, threshold)
    get_logger().log("filter_outliers", {"time_col": time_col, "value_col": value_col, "methods": methods},
                     steps, result, status="success")
    return result


# chem tools (5)
def tool_molecular_weight(formula: str) -> float:
    steps = _step(f"molecular_weight: {formula}")
    mw = molecular_weight(formula)
    get_logger().log("molecular_weight", {"formula": formula}, steps, mw, status="success")
    return mw


def tool_find_elements(formula_str: str) -> list[str]:
    steps = _step(f"find_elements: {formula_str}")
    elems = find_elements(formula_str)
    get_logger().log("find_elements", {"formula_str": formula_str}, steps, elems, status="success")
    return elems


def tool_atom_type(mass_value: float) -> str:
    steps = _step(f"atom_type: mass={mass_value}")
    elem = atom_type(mass_value)
    get_logger().log("atom_type", {"mass_value": mass_value}, steps, elem, status="success")
    return elem


def tool_detect_encoding(file_path: str) -> str:
    steps = _step(f"detect_encoding: {file_path}")
    enc = detect_encoding(file_path)
    get_logger().log("detect_encoding", {"file_path": file_path}, steps, enc, status="success")
    return enc


def tool_autocode(file_path: str, sep: str | None = None, header: int | None = None) -> pd.DataFrame:
    steps = _step(f"autocode: {file_path}")
    df = autocode(file_path, sep=sep, header=header)
    get_logger().log("autocode", {"file_path": file_path}, steps, df, status="success")
    return df


TOOL_REGISTRY = {
    "arrange": tool_arrange,
    "load_config": tool_load_config,
    "read_log": tool_read_log,
    "read_bonds": tool_read_bonds,
    "read_dump": tool_read_dump,
    "read_data": tool_read_data,
    "read_cell": tool_read_cell,
    "read_species": tool_read_species,
    "read_pos": tool_read_pos,
    "read_general": tool_read_general,
    "smooth": tool_smooth,
    "filter_outliers": tool_filter_outliers,
    "molecular_weight": tool_molecular_weight,
    "find_elements": tool_find_elements,
    "atom_type": tool_atom_type,
    "detect_encoding": tool_detect_encoding,
    "autocode": tool_autocode,
}
