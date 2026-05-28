# Copyright (c) 2025 Qiang Gan
# SPDX-License-Identifier: GPL-3.0-or-later
"""Configuration loader and validator."""
from __future__ import annotations
import os
from pathlib import Path
from typing import Any
import yaml
from pydantic import BaseModel, Field


class CutoffConfig(BaseModel):
    bonds: list[str] = Field(default_factory=list)
    bocutoff: list[float] = Field(default_factory=list)
    blcutoff: list[float] = Field(default_factory=list)


class FileRule1(BaseModel):
    datafilename: str = "*.anm"
    logfilename: str = "log.lammps*"
    bondsfilename: str = "bonds.reax.bof"
    dumpfilename: str = "*.trj"
    dumpfilename2: str = "dataofdump.*"
    speciesfilename: str = "species*"
    posfilename: str = "*.pos"
    ovitofilename: str = "ovito.*"
    cellfilename: str = "cell*"
    generalfilename: str = "*"


class PlotSet(BaseModel):
    width: int = 14
    high: int = 6
    dpi: int = 600
    labelsize: int = 20
    ticksize: int = 18
    fontscale: float = 1.5
    subadjust_wspace: float = 0.2
    subadjust_hspace: float = 0.2


class Config(BaseModel):
    cutoff: CutoffConfig = Field(default_factory=CutoffConfig)
    filerule1: FileRule1 = Field(default_factory=FileRule1)
    plotset: PlotSet = Field(default_factory=PlotSet)
    bonds_limit: dict[str, int] = Field(default_factory=dict)
    default_encoding: str = "UTF-8"
    default_timestep: float = 0.1
    default_thermostep: int = 1000

    @classmethod
    def from_yaml(cls, path: str | Path) -> "Config":
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        cutoff_data = data.get("cutoff", {})
        cutoff = CutoffConfig(
            bonds=cutoff_data.get("bonds", []),
            bocutoff=[float(x) for x in cutoff_data.get("bocutoff", [])],
            blcutoff=[float(x) for x in cutoff_data.get("blcutoff", [])],
        )
        filerule1_data = data.get("filerule1", {})
        filerule1 = FileRule1(**filerule1_data)
        plotset_data = data.get("plotset", {})
        plotset = PlotSet(
            width=plotset_data.get("multifig", {}).get("width", 14),
            high=plotset_data.get("multifig", {}).get("high", 6),
            dpi=plotset_data.get("multifig", {}).get("dpi", 600),
            labelsize=plotset_data.get("multifig", {}).get("labelsize", 20),
            ticksize=plotset_data.get("multifig", {}).get("ticksize", 18),
            fontscale=plotset_data.get("multifig", {}).get("fontscale", 1.5),
            subadjust_wspace=plotset_data.get("multifig", {}).get("subadjust", {}).get("wspace", 0.2),
            subadjust_hspace=plotset_data.get("multifig", {}).get("subadjust", {}).get("hspace", 0.2),
        )
        return cls(
            cutoff=cutoff,
            filerule1=filerule1,
            plotset=plotset,
            bonds_limit=data.get("bonds_limit", {}),
            default_encoding=data.get("encoding", {}).get("default", "UTF-8"),
            default_timestep=float(data.get("timestep", {}).get("default", "0.1")),
            default_thermostep=int(data.get("thermostep", {}).get("default", "1000")),
        )


DEFAULT_CONFIG: Config | None = None
DEFAULT_CONFIG_PATH: Path | None = None


def load_config(config_path: str | Path | None = None) -> Config:
    global DEFAULT_CONFIG, DEFAULT_CONFIG_PATH
    if config_path is None:
        pkg_dir = Path(__file__).parent.parent.parent.parent
        config_path = pkg_dir / "configs" / "default.yaml"
    config_path = Path(config_path)
    if DEFAULT_CONFIG is not None and DEFAULT_CONFIG_PATH == config_path:
        return DEFAULT_CONFIG
    DEFAULT_CONFIG = Config.from_yaml(config_path)
    DEFAULT_CONFIG_PATH = config_path
    return DEFAULT_CONFIG
