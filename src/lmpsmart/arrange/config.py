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


class PlotSetSingle(BaseModel):
    width: int = 14
    high: int = 6
    dpi: int = 600
    labelsize: int = 20
    ticksize: int = 18
    fontscale: float = 1.5
    subadjust_wspace: float = 0.2
    subadjust_hspace: float = 0.2
    sns_style: str = "ticks"
    palette: str = "tab10"
    font_family: str = "Times New Roman"


class PlotSetDoubleY(BaseModel):
    width: int = 10
    high: int = 6
    dpi: int = 600
    labelsize: int = 16
    ticksize: int = 18
    fontscale: float = 1.5
    sns_style: str = "ticks"
    palette: str = "tab10"
    font_family: str = "Times New Roman"
    y1color: str = "black"
    y2color: str = "red"
    y2tickcolor: str = "red"
    y2labelcolor: str = "red"


class PlotSetAnimation(BaseModel):
    width: int = 12
    high: int = 8
    dpi: int = 100
    labelsize: int = 16
    ticksize: int = 14
    fontscale: float = 1.3
    subadjust_wspace: float = 0.2
    subadjust_hspace: float = 0.2
    sns_style: str = "ticks"
    palette: str = "tab10"
    font_family: str = "Times New Roman"
    default_interval: int = 200
    default_cmap: str = "rainbow"
    default_format: str = "gif"


class PlotSet(BaseModel):
    multifig: PlotSetSingle = Field(default_factory=PlotSetSingle)
    singlescale: PlotSetSingle = Field(default_factory=PlotSetSingle)
    doubleyscale: PlotSetDoubleY = Field(default_factory=PlotSetDoubleY)
    animationscale: PlotSetAnimation = Field(default_factory=PlotSetAnimation)
    sns_style: str = "ticks"
    palette: str = "tab10"
    font_family: str = "Times New Roman"

    def get_mode(self, mode: str) -> PlotSetSingle | PlotSetDoubleY | PlotSetAnimation:
        return getattr(self, mode, self.multifig)


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

        ps_data = data.get("plotset", {})
        global_sns = ps_data.get("sns_style", "ticks")
        global_pal = ps_data.get("palette", "tab10")

        def _ps_from_dict(d: dict) -> PlotSetSingle:
            return PlotSetSingle(
                width=d.get("width", 14),
                high=d.get("high", 6),
                dpi=d.get("dpi", 600),
                labelsize=d.get("labelsize", 20),
                ticksize=d.get("ticksize", 18),
                fontscale=d.get("fontscale", 1.5),
                subadjust_wspace=d.get("subadjust", {}).get("wspace", 0.2),
                subadjust_hspace=d.get("subadjust", {}).get("hspace", 0.2),
                sns_style=d.get("sns_style", global_sns),
                palette=d.get("palette", global_pal),
                font_family=d.get("font_family", ps_data.get("font_family", "Times New Roman")),
            )

        def _ps_double_from_dict(d: dict) -> PlotSetDoubleY:
            return PlotSetDoubleY(
                width=d.get("width", 10),
                high=d.get("high", 6),
                dpi=d.get("dpi", 600),
                labelsize=d.get("labelsize", 16),
                ticksize=d.get("ticksize", 18),
                fontscale=d.get("fontscale", 1.5),
                sns_style=d.get("sns_style", global_sns),
                palette=d.get("palette", global_pal),
                y1color=d.get("y1color", "black"),
                y2color=d.get("y2color", "red"),
                y2tickcolor=d.get("y2tickcolor", "red"),
                y2labelcolor=d.get("y2labelcolor", "red"),
            )

        def _ps_ani_from_dict(d: dict) -> PlotSetAnimation:
            return PlotSetAnimation(
                width=d.get("width", 12),
                high=d.get("high", 8),
                dpi=d.get("dpi", 100),
                labelsize=d.get("labelsize", 16),
                ticksize=d.get("ticksize", 14),
                fontscale=d.get("fontscale", 1.3),
                subadjust_wspace=d.get("subadjust", {}).get("wspace", 0.2),
                subadjust_hspace=d.get("subadjust", {}).get("hspace", 0.2),
                sns_style=d.get("sns_style", global_sns),
                palette=d.get("palette", global_pal),
                font_family=d.get("font_family", "Times New Roman"),
                default_interval=d.get("default_interval", 200),
                default_cmap=d.get("default_cmap", "rainbow"),
                default_format=d.get("default_format", "gif"),
            )

        multifig_data = ps_data.get("multifig", {})
        singlescale_data = ps_data.get("singlescale", {})
        doubleyscale_data = ps_data.get("doubleyscale", {})
        animationscale_data = ps_data.get("animationscale", {})

        plotset = PlotSet(
            multifig=_ps_from_dict(multifig_data),
            singlescale=_ps_from_dict(singlescale_data),
            doubleyscale=_ps_double_from_dict(doubleyscale_data),
            animationscale=_ps_ani_from_dict(animationscale_data),
            sns_style=global_sns,
            palette=global_pal,
            font_family=ps_data.get("font_family", "serif"),
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
