# Copyright (c) 2025 Qiang Gan
# SPDX-License-Identifier: GPL-3.0-or-later
"""Core utility functions for LAMMPS data processing."""
from __future__ import annotations
import re
import os
import glob
import chardet
from pathlib import Path
from collections import Counter
import numpy as np
import pandas as pd

ELEMENT_WEIGHT = {
    1: "H", 2: "He",
    6: "C", 7: "N", 8: "O", 9: "F",
    13: "Al", 14: "Si", 16: "S",
    26: "Fe", 29: "Cu",
    27: "Co", 30: "Zn", 40: "Zr",
}

ELEMENT_ATOMIC = {
    "H": 1, "He": 2,
    "C": 6, "N": 7, "O": 8, "F": 9,
    "Al": 13, "Si": 14, "S": 16,
    "Fe": 26, "Cu": 29,
    "Co": 27, "Zn": 30, "Zr": 40,
}

ELEMENT_MASS = {
    "H": 1.008, "C": 12.011, "N": 14.007, "O": 15.999,
    "F": 18.998, "Al": 26.982, "Si": 28.086, "S": 32.065,
    "Fe": 55.845, "Cu": 63.546, "Co": 58.933, "Zn": 65.38,
    "Zr": 91.224,
}


def atom_type(mass_value: float) -> str:
    num = round(mass_value, 0)
    if num in ELEMENT_WEIGHT:
        return ELEMENT_WEIGHT[num]
    closest = min(ELEMENT_WEIGHT.keys(), key=lambda x: abs(x - mass_value))
    return ELEMENT_WEIGHT[closest]


def atom_order(element: str) -> int:
    return ELEMENT_ATOMIC.get(element, 0)


def type_atom(element: str) -> float:
    return ELEMENT_MASS.get(element, 0.0)


def find_elements(input_string: str) -> list[str]:
    pattern = re.compile(r"[A-Z][a-z]?")
    return pattern.findall(input_string)


def molecular_weight(formula: str) -> float:
    formula = formula.translate(str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789"))
    elements = re.findall(r"([A-Z][a-z]?)(\d*)", formula)
    total = 0.0
    for element, count in elements:
        mass = ELEMENT_MASS.get(element, 0.0)
        total += mass * (int(count) if count else 1)
    return total


def merge_list(my_list: list, order: int = 1) -> list:
    merged = []
    for item in my_list:
        if item is None or (isinstance(item, float) and pd.isna(item)):
            continue
        if order >= 2 and isinstance(item, (list, tuple)):
            merged.extend(merge_list(item, order - 1))
        else:
            merged.append(item)
    return merged


def dfsort(df0: pd.DataFrame, col: str, mode: str) -> pd.DataFrame:
    if mode == "num":
        df0[col + "_sort"] = df0[col].apply(
            lambda x: float(re.findall(r"\d+\.?\d*", str(x))[0]) if re.findall(r"\d+\.?\d*", str(x)) else 0
        )
        df0 = df0.sort_values(col + "_sort").reset_index(drop=True).drop(col + "_sort", axis=1)
    elif mode == "str":
        df0 = df0.sort_values(col).reset_index(drop=True)
    return df0


def detect_encoding(file_path: str) -> str:
    with open(file_path, "rb") as f:
        result = chardet.detect(f.read(1000))
    return result.get("encoding", "utf-8") or "utf-8"


def autocode(file_path: str, engine: str = "pandas", **kwargs) -> pd.DataFrame:
    encoding = detect_encoding(file_path)
    sep = kwargs.get("sep", r"\s+")
    header = kwargs.get("header", None)
    if engine == "pandas":
        try:
            return pd.read_csv(file_path, sep=sep, encoding=encoding, header=header)
        except Exception:
            return pd.read_csv(file_path, encoding=encoding)


def four_five(num: float) -> float:
    return round(num)


def folderfilter(inpath: str, folder: str) -> list[str]:
    if not os.path.exists(inpath):
        return []
    if folder == "all" or folder == "":
        items = os.listdir(inpath)
        return [i for i in items if os.path.isdir(os.path.join(inpath, i))]
    pattern = folder.replace("*", "")
    matched = []
    for item in os.listdir(inpath):
        if os.path.isdir(os.path.join(inpath, item)) and pattern in item:
            matched.append(item)
    return matched


def filefilter(inpath: str, folder: str, read: str) -> list[str]:
    if read:
        target = os.path.join(inpath, folder, read)
    else:
        target = os.path.join(inpath, folder)
    if not os.path.exists(target):
        return []
    return [f for f in os.listdir(target) if os.path.isfile(os.path.join(target, f))]
