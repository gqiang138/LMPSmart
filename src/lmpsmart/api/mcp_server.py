# Copyright (c) 2025 Qiang Gan
# SPDX-License-Identifier: GPL-3.0-or-later
"""MCP Server for lmpsmart — exposes LAMMPS data tools via Model Context Protocol.

This server allows any MCP-compatible host (OpenCode, Cherry Studio, Claude Desktop)
to use lmpsmart tools without requiring a separate lmpsmart LLM configuration.
The host's LLM handles planning; this server handles tool execution only.

Usage:
    # stdio (for OpenCode, Claude Desktop)
    python -m lmpsmart.api.mcp_server

    # HTTP (for Cherry Studio, remote access)
    python -m lmpsmart.api.mcp_server --http --port 8765
"""
from __future__ import annotations
import argparse
import json
import sys
from typing import Any

try:
    from mcp.server.fastmcp import FastMCP
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    FastMCP = None

from lmpsmart.api import tools as tools_module
from lmpsmart.api.tools import TOOL_REGISTRY


def _serialize(result: Any) -> Any:
    if result is None:
        return None
    if hasattr(result, "to_dict"):
        return result.to_dict()
    if hasattr(result, "to_json"):
        return json.loads(result.to_json())
    if hasattr(result, "to_csv"):
        return {"_dataframe": result.to_csv(index=False), "_type": "DataFrame"}
    if hasattr(result, "dtypes"):
        return {
            "_dataframe": result.to_csv(index=False),
            "_type": "DataFrame",
            "shape": list(result.shape),
            "columns": list(result.columns),
        }
    if isinstance(result, (int, float, str, bool)):
        return result
    if isinstance(result, (list, tuple)):
        return [_serialize(x) for x in result]
    if isinstance(result, dict):
        return {k: _serialize(v) for k, v in result.items()}
    return str(result)


def _safe_call(tool_func, **kwargs) -> dict:
    try:
        result = tool_func(**kwargs)
        return {"status": "success", "result": _serialize(result)}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def _register_tools(mcp: FastMCP) -> None:
    t = TOOL_REGISTRY

    @mcp.tool(title="arrange", description="Parse LAMMPS output files (Log, Bonds, Dump, Cell, Species, POS, OVITO, General) into structured CSVs")
    def tool_arrange(input_path: str, modes: list[str], timestep: float = 0.1,
                     encoding: str = "utf-8", output_path: str | None = None,
                     config_path: str | None = None, ignored_time: float = 0.0,
                     supercell: str | None = None, log_indices: list[int] | None = None) -> dict:
        return _safe_call(t["arrange"], input_path=input_path, modes=modes,
                          timestep=timestep, encoding=encoding, output_path=output_path,
                          config_path=config_path, ignored_time=ignored_time,
                          supercell=supercell, log_indices=log_indices)

    @mcp.tool(title="load_config", description="Load and return lmpsmart YAML configuration")
    def tool_load_config(config_path: str | None = None) -> dict:
        return _safe_call(t["load_config"], config_path=config_path)

    @mcp.tool(title="read_log", description="Read LAMMPS log file and return thermodynamics DataFrame")
    def tool_read_log(log_path: str, log_indices: list[int] | None = None,
                      supercell: str | None = None, ignored_time: float = 0.0,
                      timestep: float = 0.1) -> dict:
        return _safe_call(t["read_log"], log_path=log_path, log_indices=log_indices,
                          supercell=supercell, ignored_time=ignored_time, timestep=timestep)

    @mcp.tool(title="read_bonds", description="Read ReaxFF bond order file and return bond data")
    def tool_read_bonds(bonds_path: str, data_path: str | None = None,
                        ignored_time: float = 0.0, timestep: float = 0.1) -> dict:
        return _safe_call(t["read_bonds"], bonds_path=bonds_path, data_path=data_path,
                          ignored_time=ignored_time, timestep=timestep)

    @mcp.tool(title="read_dump", description="Read LAMMPS dump trajectory file")
    def tool_read_dump(dump_path: str, data_path: str | None = None,
                       ignored_time: float = 0.0, timestep: float = 0.1) -> dict:
        return _safe_call(t["read_dump"], dump_path=dump_path, data_path=data_path,
                          ignored_time=ignored_time, timestep=timestep)

    @mcp.tool(title="read_data", description="Read LAMMPS data file (multiple DataFrames)")
    def tool_read_data(data_path: str) -> dict:
        return _safe_call(t["read_data"], data_path=data_path)

    @mcp.tool(title="read_cell", description="Read unit cell dimensions from dump file")
    def tool_read_cell(dump_path: str, ignored_time: float = 0.0, timestep: float = 0.1) -> dict:
        return _safe_call(t["read_cell"], dump_path=dump_path,
                          ignored_time=ignored_time, timestep=timestep)

    @mcp.tool(title="read_species", description="Read chemical species counts over time")
    def tool_read_species(species_path: str, ignored_time: float = 0.0,
                           timestep: float = 0.1) -> dict:
        return _safe_call(t["read_species"], species_path=species_path,
                          ignored_time=ignored_time, timestep=timestep)

    @mcp.tool(title="read_pos", description="Read POSCAR-style crystal structure file")
    def tool_read_pos(pos_path: str, ignored_time: float = 0.0, timestep: float = 0.1) -> dict:
        return _safe_call(t["read_pos"], pos_path=pos_path,
                          ignored_time=ignored_time, timestep=timestep)

    @mcp.tool(title="read_general", description="Read generic CSV/TSV file with auto-detection")
    def tool_read_general(file_path: str, sep: str | None = None, header: int | None = None) -> dict:
        return _safe_call(t["read_general"], file_path=file_path, sep=sep, header=header)

    @mcp.tool(title="smooth", description="Smooth time-series data (moving_avg, savgol, ewma, wavelet, etc.)")
    def tool_smooth(x_data: list[float] | None = None, y_data: list[float] | None = None,
                     method: str = "moving_avg", **kwargs) -> dict:
        return _safe_call(t["smooth"], x_data=x_data, y_data=y_data, method=method, **kwargs)

    @mcp.tool(title="filter_outliers", description="Remove outliers from time-series using zscore, MAD, or IQR")
    def tool_filter_outliers(df_json: str | None = None, time_col: str = "time",
                              value_col: str = "value", methods: str | list[str] = "zscore",
                              threshold: float = 3.0) -> dict:
        import pandas as pd
        if df_json:
            df = pd.read_json(df_json)
            return _safe_call(t["filter_outliers"], df=df, time_col=time_col,
                              value_col=value_col, methods=methods, threshold=threshold)
        return {"status": "error", "error": "df_json is required"}

    @mcp.tool(title="fit", description="Fit curve to data (polyfit with degree 1-5, or lowess)")
    def tool_fit(x_data: list[float], y_data: list[float], method: str = "polyfit",
                  degree: int = 2, frac: float = 0.3) -> dict:
        return _safe_call(t["fit"], x_data=x_data, y_data=y_data,
                          method=method, degree=degree, frac=frac)

    @mcp.tool(title="plot", description="Plot CSV data as line/scatter figure (single, multi, doubley modes)")
    def tool_plot(csv_path: str, x_col: str, y_cols: list[str],
                   mode: str = "single", hue_col: str | None = None, markers: bool = False,
                   legend_loc: str = "best", subscript: bool = False,
                   title: str = "", xlabel: str = "", ylabel: str = "",
                   figsize: str | None = None, dpi: int | None = None,
                   config_path: str | None = None,
                   legend_type: str = "auto", legend_labels: list[str] | None = None,
                   legend_suffix: str = "", yerr_col: str | None = None,
                   output_path: str | None = None) -> dict:
        return _safe_call(t["plot"], csv_path=csv_path, x_col=x_col, y_cols=y_cols,
                          output_path=output_path, mode=mode, hue_col=hue_col,
                          markers=markers, legend_loc=legend_loc, subscript=subscript,
                          config_path=config_path, title=title, xlabel=xlabel,
                          ylabel=ylabel, figsize=figsize, dpi=dpi,
                          legend_type=legend_type, legend_labels=legend_labels,
                          legend_suffix=legend_suffix, yerr_col=yerr_col)

    @mcp.tool(title="groupby_aggregate", description="Group CSV by column and aggregate another column (mean, sum, count, etc.)")
    def tool_groupby_aggregate(csv_path: str, group_col: str, agg_col: str,
                                agg_func: str = "mean", output_path: str | None = None) -> dict:
        return _safe_call(t["groupby_aggregate"], csv_path=csv_path, group_col=group_col,
                          agg_col=agg_col, agg_func=agg_func, output_path=output_path)

    @mcp.tool(title="belong_filter", description="Keep or exclude rows by column value set")
    def tool_belong_filter(csv_path: str, col: str, values: list, keep: bool = True,
                            output_path: str | None = None) -> dict:
        return _safe_call(t["belong_filter"], csv_path=csv_path, col=col, values=values,
                          keep=keep, output_path=output_path)

    @mcp.tool(title="column_rename", description="Rename CSV columns via {\"old_name\": \"new_name\"} map")
    def tool_column_rename(csv_path: str, rename_map: dict, output_path: str | None = None) -> dict:
        return _safe_call(t["column_rename"], csv_path=csv_path, rename_map=rename_map,
                          output_path=output_path)

    @mcp.tool(title="select_columns", description="Keep only specified columns from CSV")
    def tool_select_columns(csv_path: str, columns: list[str], output_path: str | None = None) -> dict:
        return _safe_call(t["select_columns"], csv_path=csv_path, columns=columns,
                          output_path=output_path)

    @mcp.tool(title="merge_data", description="Merge or concatenate multiple CSV files")
    def tool_merge_data(csv_paths: list[str], how: str = "concat",
                        on_col: str | None = None, output_path: str | None = None) -> dict:
        return _safe_call(t["merge_data"], csv_paths=csv_paths, how=how,
                          on_col=on_col, output_path=output_path)

    @mcp.tool(title="molecular_weight", description="Calculate molecular weight from chemical formula")
    def tool_molecular_weight(formula: str) -> dict:
        return _safe_call(t["molecular_weight"], formula=formula)

    @mcp.tool(title="find_elements", description="Extract element symbols from chemical formula")
    def tool_find_elements(formula_str: str) -> dict:
        return _safe_call(t["find_elements"], formula_str=formula_str)

    @mcp.tool(title="atom_type", description="Identify atom element from atomic mass")
    def tool_atom_type(mass_value: float) -> dict:
        return _safe_call(t["atom_type"], mass_value=mass_value)

    @mcp.tool(title="detect_encoding", description="Auto-detect file text encoding (UTF-8, GBK, etc.)")
    def tool_detect_encoding(file_path: str) -> dict:
        return _safe_call(t["detect_encoding"], file_path=file_path)

    @mcp.tool(title="autocode", description="Auto-detect and parse LAMMPS data file structure")
    def tool_autocode(file_path: str, sep: str | None = None, header: int | None = None) -> dict:
        return _safe_call(t["autocode"], file_path=file_path, sep=sep, header=header)


def main() -> None:
    parser = argparse.ArgumentParser(description="lmpsmart MCP Server")
    parser.add_argument("--http", action="store_true", help="Run HTTP transport instead of stdio")
    parser.add_argument("--port", type=int, default=8765, help="HTTP port (default: 8765)")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="HTTP host (default: 0.0.0.0)")
    parser.add_argument(
        "--python",
        type=str,
        default=None,
        dest="python_path",
        help="Python executable path (default: current interpreter). "
        "Set LMPSMART_PYTHON env var or use this flag to specify the expected Python env.",
    )
    args = parser.parse_args()

    if not MCP_AVAILABLE:
        print("Error: mcp package not installed. Run: pip install mcp", file=sys.stderr)
        sys.exit(1)

    _check_environment(args.python_path)

    mcp = FastMCP(
        "lmpsmart",
        instructions="LAMMPS molecular dynamics data processing tools — parse, smooth, filter, fit, plot, animate, clean",
    )
    _register_tools(mcp)

    if args.http:
        mcp.run(transport="streamable-http", host=args.host, port=args.port)
    else:
        mcp.run(transport="stdio")


def _check_environment(python_path: str | None = None) -> None:
    import os

    expected = python_path or os.environ.get("LMPSMART_PYTHON", "")
    actual = sys.executable

    banner = f"""
╔══════════════════════════════════════════════════════════╗
║  lmpsmart MCP Server v1.0                              ║
║  Python : {actual}
╚══════════════════════════════════════════════════════════╝
"""
    print(banner)

    if expected and os.path.normpath(expected) != os.path.normpath(actual):
        print(
            f"[WARN] Python env mismatch!\n"
            f"  Expected: {expected}\n"
            f"  Actual  : {actual}\n"
            f"  To fix  : Update MCP config to use '{actual}'\n"
            f"  Or set  : LMPSMART_PYTHON={actual}\n",
            file=sys.stderr,
        )

    try:
        import lmpsmart

        print(f"[OK] lmpsmart {lmpsmart.__version__ if hasattr(lmpsmart, '__version__') else '(version unknown)'} imported successfully")
    except ImportError as e:
        print(
            f"[ERROR] lmpsmart package not found in current Python env.\n"
            f"  Python : {actual}\n"
            f"  Error  : {e}\n"
            f"\n"
            f"  To fix:\n"
            f"  1. Install: {actual} -m pip install -e D:/MyObsidian/Projects/lmpsmart\n"
            f"  2. Or update MCP config 'command' to point to the correct Python:\n"
            f"     [{actual}] -m lmpsmart.api.mcp_server\n"
            f"  3. Or set env var before starting:\n"
            f"     set LMPSMART_PYTHON={actual} && python -m lmpsmart.api.mcp_server\n",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
