# Copyright (c) 2025 Qiang Gan
# SPDX-License-Identifier: GPL-3.0-or-later
"""LAMMPS file readers for Arrange module."""
from __future__ import annotations
import gc
import re
import os
import glob
import chardet
from pathlib import Path
from typing import Literal, Any
import numpy as np
import pandas as pd
from openpyxl import load_workbook
from lmpsmart.core.tools import atom_type as identify_element


def detect_encoding(file_path: str) -> str:
    with open(file_path, "rb") as f:
        result = chardet.detect(f.read(1000))
    return result.get("encoding", "utf-8") or "utf-8"


def autocode(file_path: str, engine: str = "pandas", **kwargs) -> pd.DataFrame | Any:
    encoding = detect_encoding(file_path)
    sep = kwargs.get("sep", r"\s+")
    header = kwargs.get("header", None)
    if engine == "pandas":
        try:
            return pd.read_csv(file_path, sep=sep, encoding=encoding, header=header)
        except Exception:
            return pd.read_csv(file_path, encoding=encoding)


def df_atoms(data_path: str) -> list[dict]:
    with open(data_path, encoding="utf-8") as f:
        lines = f.readlines()
    atoms_section = False
    atoms_data = []
    for line in lines:
        stripped = line.strip()
        if "Atoms" in stripped:
            atoms_section = True
            continue
        if atoms_section:
            if stripped == "":
                continue
            if stripped.isdigit():
                break
            parts = stripped.split()
            if len(parts) >= 4:
                atom_id = int(parts[0])
                if len(parts) == 4:
                    atom_type = int(parts[1])
                    x, y, z = float(parts[2]), float(parts[3]), 0.0
                    atoms_data.append(
                        {"id": atom_id, "molecule": 0, "type": atom_type, "x": x, "y": y, "z": z}
                    )
                elif len(parts) == 6:
                    atom_type = int(parts[1])
                    x, y, z = float(parts[3]), float(parts[4]), float(parts[5])
                    atoms_data.append(
                        {"id": atom_id, "molecule": 0, "type": atom_type, "x": x, "y": y, "z": z}
                    )
                else:
                    mol_id = int(parts[1])
                    atom_type = int(parts[2])
                    x, y, z = float(parts[4]), float(parts[5]), float(parts[6])
                    atoms_data.append(
                        {"id": atom_id, "molecule": mol_id, "type": atom_type, "x": x, "y": y, "z": z}
                    )
    return atoms_data


def df_masses(data_path: str) -> pd.DataFrame:
    with open(data_path, encoding="utf-8") as f:
        lines = f.readlines()
    masses_section = False
    masses_data = []
    for line in lines:
        stripped = line.strip()
        if "Masses" in stripped:
            masses_section = True
            continue
        if masses_section:
            if stripped == "":
                continue
            parts = stripped.split()
            if not parts or not parts[0].isdigit():
                break
            if len(parts) >= 2:
                try:
                    atom_type = int(parts[0])
                    mass = float(parts[1])
                    element = identify_element(mass)
                    raw_line = line.strip()
                    if "#" in raw_line:
                        elem_part = raw_line.split("#", 1)[1].strip()
                        if elem_part:
                            element = elem_part.split()[0].strip()
                    masses_data.append({"type": atom_type, "mass": mass, "element": element})
                except ValueError:
                    continue
    return pd.DataFrame(masses_data)


def read_data(
    data_path: str,
    encoding: str = "utf-8",
    config: Any = None,
) -> dict[str, pd.DataFrame]:
    result = {}
    dfatoms = pd.DataFrame(df_atoms(data_path))
    dfatoms["type"] = dfatoms["type"].astype(int)
    dfatoms = dfatoms[dfatoms["type"] != 0]
    dfmasses = df_masses(data_path)
    if not dfmasses.empty:
        dfatoms = dfatoms.merge(dfmasses, on="type", how="left")
    with open(data_path, encoding="utf-8") as f:
        lines = f.readlines()
    for line in lines:
        stripped = line.strip()
        if "Atoms" in stripped:
            if "full" in stripped:
                result["atom_style"] = "full"
            elif "charge" in stripped:
                result["atom_style"] = "charge"
            break
    result["atoms"] = dfatoms
    return result


def read_log(
    log_path: str,
    log_indices: list[int] | None = None,
    supercell: tuple[int, int, int] | None = None,
    ignored_time: float = 0.0,
    timestep: float = 0.1,
    encoding: str = "utf-8",
) -> pd.DataFrame:
    with open(log_path, encoding=encoding) as f:
        loglines = f.read().splitlines()
    line0, line1 = [], []
    for i, line in enumerate(loglines):
        tokens = re.split(r" +", line.strip())
        if tokens and tokens[0] == "Step":
            line0.append(i)
        elif tokens and tokens[0] == "Loop":
            line1.append(i)
    if not line0:
        raise ValueError(f"No Step data found in {log_path}")
    if log_indices is None:
        log_indices = list(range(len(line0)))
    logcolumns = re.split(r" +", loglines[line0[log_indices[0]]].strip())
    dflog = pd.DataFrame()
    for idx in log_indices:
        if idx >= len(line0):
            continue
        end = line1[idx] if idx < len(line1) else len(loglines) - 1
        rows = []
        for k in loglines[line0[idx] + 1 : end]:
            tokens = re.split(r" +", k.strip())
            if len(tokens) == len(logcolumns):
                rows.append(tokens)
        dflog = pd.concat([dflog, pd.DataFrame(rows, columns=logcolumns)], ignore_index=True)
    dflog = dflog.groupby("Step").first().reset_index()
    if "Press" in dflog.columns:
        dflog["Press"] = dflog["Press"].astype(float) / 10000
    if supercell is not None:
        sa, sb, sc = supercell
        if "Cella" in dflog.columns:
            dflog["Cella"] = dflog["Cella"].astype(float) / sa
        if "Cellb" in dflog.columns:
            dflog["Cellb"] = dflog["Cellb"].astype(float) / sb
        if "Cellc" in dflog.columns:
            dflog["Cellc"] = dflog["Cellc"].astype(float) / sc
        if "Volume" in dflog.columns:
            dflog["Volume"] = dflog["Volume"].astype(float) / (sa * sb * sc)
    dflog = dflog.rename(columns={"Step": "frame"})
    dflog["frame"] = dflog["frame"].astype(int) - int(ignored_time * 1000 / timestep)
    dflog["frame"] = dflog["frame"].astype(int)
    dflog = dflog.sort_values("frame", ascending=True)
    dflog.insert(1, "time", round(dflog["frame"] * timestep * 0.001, 3))
    return dflog


def read_bonds(
    bonds_path: str,
    data_path: str | None = None,
    dfatoms: pd.DataFrame | None = None,
    dfcutoff: pd.DataFrame | None = None,
    ignored_time: float = 0.0,
    timestep: float = 0.1,
    encoding: str = "utf-8",
) -> pd.DataFrame:
    if dfatoms is None and data_path:
        dfatoms = pd.DataFrame(df_atoms(data_path))
        dfatoms["type"] = dfatoms["type"].astype(int)
        dfatoms = dfatoms[dfatoms["type"] != 0]
    with open(bonds_path, encoding=encoding) as f:
        bondslines = f.read().splitlines()
    if len(bondslines) < 10:
        raise ValueError(f"bonds file too short: {bonds_path}")
    try:
        atomall = int(bondslines[2].split()[4])
    except (IndexError, ValueError) as e:
        raise ValueError(f"Cannot parse atom count from bonds file {bonds_path} line 3: {e}")
    listid, listtype = [], []
    for i in range(7, atomall + 7):
        match = re.findall(r"[+\-]?[0-9]*\.?[0-9]+", bondslines[i])
        listid.append(int(match[0]))
        listtype.append(int(match[1]))
    dictidtype = dict(zip(listid, listtype))
    bondslist = []
    for i, line in enumerate(bondslines):
        if "Timestep" in line:
            frame = int(line.split(" ")[2])
            try:
                for j in range(i + 7, i + 7 + atomall):
                    match = re.findall(r"[+\-]?[0-9]*\.?[0-9]+", bondslines[j])
                    if len(match) < 4:
                        continue
                    n_bonds = int(match[2])
                    if n_bonds > 0:
                        for k in range(n_bonds):
                            bondslist.append(
                                [
                                    frame,
                                    int(match[0]),
                                    int(match[3 + k]),
                                    int(match[1]),
                                    dictidtype.get(int(match[3 + k]), 0),
                                    float(match[3 + n_bonds + k + 1]),
                                ]
                            )
                    elif n_bonds == 0:
                        bondslist.append([frame, int(match[0]), 0, int(match[1]), 0, 0])
            except Exception:
                continue
    dfbonds = pd.DataFrame(
        bondslist, columns=["frame", "id1", "id2", "type1", "type2", "bo"]
    )
    if dfatoms is not None and "element" in dfatoms.columns:
        dfbonds["bonds"] = (
            dfbonds["type1"].map(dict(zip(dfbonds["type1"], dfatoms["element"])))
            + dfbonds["type2"].map(dict(zip(dfbonds["type2"], dfatoms["element"])))
        ).fillna("")
    dfbonds = dfbonds.groupby(["frame", "id1", "id2"]).first().reset_index()
    if dfcutoff is not None and not dfcutoff.empty:
        if len(dfcutoff) == 1 and dfcutoff.iloc[0]["bonds"] == "":
            dfbonds["bocutoff"] = dfcutoff.iloc[0]["bocutoff"]
            dfbonds["blcutoff"] = dfcutoff.iloc[0]["blcutoff"]
            dfbonds.loc[dfbonds["id2"] == 0, "bocutoff"] = np.nan
            dfbonds.loc[dfbonds["id2"] == 0, "blcutoff"] = np.nan
        else:
            dfbonds = dfbonds.merge(dfcutoff, how="left", on="bonds")
    dfbonds["frame"] = dfbonds["frame"].astype(int) - int(ignored_time * 1000 / timestep)
    dfbonds["frame"] = dfbonds["frame"].astype(int)
    dfbonds.insert(1, "time", round(dfbonds["frame"] * timestep * 0.001, 3))
    return dfbonds


def read_dump(
    dump_path: str,
    data_path: str | None = None,
    dfatoms: pd.DataFrame | None = None,
    ignored_time: float = 0.0,
    timestep: float = 0.1,
    encoding: str = "utf-8",
) -> pd.DataFrame:
    if dfatoms is None and data_path:
        dfatoms = pd.DataFrame(df_atoms(data_path))
        dfatoms["type"] = dfatoms["type"].astype(int)
        dfatoms = dfatoms[dfatoms["type"] != 0]
    with open(dump_path, encoding=encoding) as f:
        dumplines = f.read().splitlines()
    pattern = re.compile(r"ITEM: TIMESTEP")
    framelines = [i for i, line in enumerate(dumplines) if pattern.search(line)]
    if not framelines:
        raise ValueError(f"No TIMESTEP found in {dump_path}")
    dumpcolumns = re.split(r" +", dumplines[framelines[0] + 8])[2:]
    dfdump = pd.DataFrame()
    for idx in framelines:
        frame0 = int(dumplines[idx + 1])
        atomall = int(dumplines[idx + 3])
        lines = dumplines[idx + 9 : idx + 9 + atomall]
        data = [re.split(r" +", j) for j in lines]
        dfdump0 = pd.DataFrame(data, columns=dumpcolumns)
        dfdump0.insert(0, "frame", frame0)
        dfdump = pd.concat([dfdump, dfdump0], ignore_index=True)
    dfdump.rename(columns={"xu": "x", "yu": "y", "zu": "z"}, inplace=True)
    nullframelist = dfdump[dfdump.isna().any(axis=1)]["frame"].tolist()
    if nullframelist:
        dfdump = dfdump[~dfdump["frame"].isin(nullframelist)]
    dfdump["frame"] = dfdump["frame"] - int(ignored_time * 1000 / timestep)
    dfdump["frame"] = dfdump["frame"].astype(int)
    dfdump.insert(1, "time", round(dfdump["frame"] * timestep * 0.001, 3))
    dfdump[["id", "type"]] = dfdump[["id", "type"]].astype(int)
    dfdump = dfdump.sort_values(["frame", "id"], ascending=True)
    if dfatoms is not None:
        merge_src = dfatoms[["type", "mass", "element"]].drop_duplicates("type")
        dfdump = dfdump.merge(merge_src, how="left", on="type")
    return dfdump


def read_cell(
    dump_path: str,
    ignored_time: float = 0.0,
    timestep: float = 0.1,
    encoding: str = "utf-8",
) -> pd.DataFrame:
    with open(dump_path, encoding=encoding) as f:
        dumplines = f.read().splitlines()
    framelist, celllist = [], []
    i = 0
    while i < len(dumplines):
        if "ITEM: TIMESTEP" in dumplines[i]:
            framelist.append(int(dumplines[i + 1].strip()))
            i += 1
        elif "ITEM: BOX BOUNDS" in dumplines[i]:
            items = dumplines[i].split("ITEM: BOX BOUNDS")[1].split()
            if len(items) == 3:
                a = float(dumplines[i + 1].split()[1]) - float(dumplines[i + 1].split()[0])
                b = float(dumplines[i + 2].split()[1]) - float(dumplines[i + 2].split()[0])
                c = float(dumplines[i + 3].split()[1]) - float(dumplines[i + 3].split()[0])
                a0 = float(dumplines[i + 1].split()[0])
                b0 = float(dumplines[i + 2].split()[0])
                c0 = float(dumplines[i + 3].split()[0])
                xy = xz = yz = 0.0
                px, py, pz = items[0], items[1], items[2]
            elif len(items) == 6:
                xy = float(dumplines[i + 1].split()[2])
                xz = float(dumplines[i + 2].split()[2])
                yz = float(dumplines[i + 3].split()[2])
                a0 = float(dumplines[i + 1].split()[0]) - min(0.0, xy, xz, xy + xz)
                b0 = float(dumplines[i + 2].split()[0]) - min(0.0, yz)
                c0 = float(dumplines[i + 3].split()[0])
                a = (float(dumplines[i + 1].split()[1]) - float(dumplines[i + 1].split()[0])
                     - max(0.0, xy, xz, xy + xz) + min(0.0, xy, xz, xy + xz))
                b = (float(dumplines[i + 2].split()[1]) - float(dumplines[i + 2].split()[0])
                     - max(0.0, yz) + min(0.0, yz))
                c = float(dumplines[i + 3].split()[1]) - float(dumplines[i + 3].split()[0])
                px, py, pz = items[3], items[4], items[5]
            else:
                a = b = c = a0 = b0 = c0 = xy = xz = yz = 0.0
                px = py = pz = ""
            celllist.append([a, b, c, a0, b0, c0, xy, xz, yz, px, py, pz])
            i += 4
        else:
            i += 1
    dfcell = pd.DataFrame(celllist, columns=["a", "b", "c", "a0", "b0", "c0", "xy", "xz", "yz", "px", "py", "pz"])
    dfcell.insert(0, "frame", framelist)
    dfcell["frame"] = dfcell["frame"].astype(int) - int(ignored_time * 1000 / timestep)
    dfcell["frame"] = dfcell["frame"].astype(int)
    dfcell = dfcell.sort_values("frame", ascending=True).reset_index(drop=True)
    return dfcell


def read_species(
    species_path: str,
    ignored_time: float = 0.0,
    timestep: float = 0.1,
    encoding: str = "utf-8",
    elementorder: dict | None = None,
) -> pd.DataFrame:
    with open(species_path, encoding=encoding) as f:
        lines = f.readlines()
    rows = []
    species_names = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#"):
            parts = stripped.split()
            if "Timestep" in parts:
                ts_idx = parts.index("Timestep")
                try:
                    frame = int(parts[ts_idx + 1])
                except (ValueError, IndexError):
                    pass
            name_parts = [p for p in stripped.split("#")[-1].split() if p]
            if name_parts:
                new_sp = [n for n in name_parts
                          if n not in ("Timestep", "No_Moles", "No_Specs")]
                for sp in new_sp:
                    if sp not in species_names:
                        species_names.append(sp)
            continue
        if not stripped:
            continue
        parts = stripped.split()
        if len(parts) < 2:
            continue
        try:
            frame = int(parts[0])
        except ValueError:
            continue
        no_moles = int(parts[1])
        no_specs = int(parts[2])
        adjusted_frame = frame - int(ignored_time * 1000 / timestep)
        for i, sp in enumerate(species_names):
            if i + 3 < len(parts):
                count = int(parts[i + 3])
                if count > 0:
                    rows.append({
                        "frame": adjusted_frame,
                        "No_Moles": no_moles,
                        "No_Specs": no_specs,
                        "molecule": sp,
                        "count": count,
                    })
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df["frame"] = df["frame"].astype(int)
    df = df.sort_values(["frame", "molecule"], ascending=[True, True]).reset_index(drop=True)
    df.insert(1, "time", round(df["frame"] * timestep * 0.001, 3))
    # Original format: number (count per molecule), weight (molecular weight)
    df = df.rename(columns={"count": "number"})
    from lmpsmart.core.tools import molecular_weight, reorder_molecule
    if elementorder:
        df["molecule"] = df["molecule"].apply(lambda m: reorder_molecule(m, elementorder))
    df["weight"] = df["molecule"].apply(molecular_weight)
    return df


def read_pos(
    pos_path: str,
    ignored_time: float = 0.0,
    timestep: float = 0.1,
    encoding: str = "utf-8",
    elementorder: dict | None = None,
) -> pd.DataFrame:
    with open(pos_path, encoding=encoding) as f:
        raw_lines = f.readlines()
    lines = [ln.rstrip("\n") for ln in raw_lines]
    is_species_com = any("Timestep" in ln and "NMole" in ln for ln in lines[:10])
    frames_data = {}
    current_frame = None
    if is_species_com:
        for line in lines:
            if "Timestep" in line and "NMole" in line:
                parts = line.split()
                try:
                    ts_idx = parts.index("Timestep")
                    current_frame = int(parts[ts_idx + 1])
                except (ValueError, IndexError):
                    continue
                if current_frame not in frames_data:
                    frames_data[current_frame] = []
            elif line.startswith("ID\t") or line.startswith("ID"):
                continue
            elif "\t" in line:
                parts = line.split("\t")
                if len(parts) >= 7:
                    try:
                        mol_id = int(parts[0])
                        atom_count = int(parts[1])
                        mol_type = parts[2].strip()
                        q = float(parts[3])
                        cx = float(parts[4])
                        cy = float(parts[5])
                        cz = float(parts[6])
                        if current_frame is not None:
                            frames_data[current_frame].append(
                                {"x": cx, "y": cy, "z": cz, "molecule": mol_type, "q": q, "atom_count": atom_count}
                            )
                    except (ValueError, IndexError):
                        continue
    else:
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("#"):
                continue
            parts = stripped.split()
            if len(parts) < 4:
                continue
            try:
                frame = int(float(parts[0]))
            except ValueError:
                continue
            if frame != current_frame:
                current_frame = frame
                frames_data[frame] = []
            frames_data[frame].append(
                {
                    "x": float(parts[1]),
                    "y": float(parts[2]),
                    "z": float(parts[3]),
                    "molecule": parts[4] if len(parts) > 4 else "X",
                    "q": 0.0,
                    "atom_count": 0,
                }
            )
    rows = []
    for frame, atoms in frames_data.items():
        for atom in atoms:
            rows.append(
                {
                    "frame": frame - int(ignored_time * 1000 / timestep),
                    "x": atom["x"],
                    "y": atom["y"],
                    "z": atom["z"],
                    "molecule": atom.get("molecule", "X"),
                    "q": atom.get("q", 0.0),
                    "atom_count": atom.get("atom_count", 0),
                }
            )
    dfpos = pd.DataFrame(rows)
    dfpos["frame"] = dfpos["frame"].astype(int)
    dfpos.insert(1, "time", round(dfpos["frame"] * timestep * 0.001, 3))
    dfpos = dfpos.sort_values(["frame", "molecule"], ascending=[True, True]).reset_index(drop=True)
    from lmpsmart.core.tools import molecular_weight, reorder_molecule
    if elementorder:
        dfpos["molecule"] = dfpos["molecule"].apply(lambda m: reorder_molecule(m, elementorder))
    dfpos["weight"] = dfpos["molecule"].apply(molecular_weight)
    cols = ["frame", "time", "molecule", "q", "x", "y", "z", "weight"]
    return dfpos[cols]


def read_ovito(
    ovito_path: str,
    sheet_name: int = 0,
    ignored_time: float = 0.0,
    timestep: float = 0.1,
) -> pd.DataFrame:
    df = pd.read_excel(ovito_path, sheet_name=sheet_name, header=0)
    if "Frame" in df.columns:
        df["frame"] = df["Frame"].astype(int) - int(ignored_time * 1000 / timestep)
        df["frame"] = df["frame"].astype(int)
        df.insert(1, "time", round(df["frame"] * timestep * 0.001, 3))
    return df


def read_paraments(input_path: str) -> dict[str, Any]:
    paraments_file = os.path.join(input_path, "paraments.txt")
    if not os.path.exists(paraments_file):
        return {}
    params = {}
    with open(paraments_file, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip()
                if "," in key and "{" not in val:
                    parts = [p.strip() for p in val.split(",")]
                    params["supercell"] = tuple(int(p) for p in parts)
                elif "," in val and "{" not in val:
                    parts = [p.strip() for p in val.split(",")]
                    if len(parts) == 3:
                        params["supercell"] = tuple(int(p) for p in parts)
                    else:
                        try:
                            params[key] = float(parts[0]) if "." in parts[0] else int(parts[0])
                        except ValueError:
                            params[key] = val
                else:
                    try:
                        params[key] = float(val)
                    except ValueError:
                        try:
                            params[key] = int(val)
                        except ValueError:
                            params[key] = val
    return params


def read_general(
    file_path: str,
    sep: str | None = None,
    header: int | None = None,
    encoding: str | None = None,
) -> pd.DataFrame:
    if encoding is None:
        encoding = detect_encoding(file_path)
    if sep is None:
        ext = Path(file_path).suffix.lower()
        if ext == ".csv":
            sep = ","
        else:
            sep = r"\s+"
    df = pd.read_csv(file_path, sep=sep, encoding=encoding, header=header)
    df.columns = [c.strip() for c in df.columns]
    return df


def arrange(
    input_path: str,
    modes: list[str],
    output_path: str | None = None,
    config: Any = None,
    ignored_time: float = 0.0,
    timestep: float = 0.1,
    encoding: str = "utf-8",
    supercell: tuple[int, int, int] | None = None,
    log_indices: list[int] | None = None,
) -> tuple[dict[str, pd.DataFrame], str]:
    if config is None:
        from lmpsmart.arrange.config import load_config
        config = load_config()

    if output_path is None:
        root = Path(input_path).resolve()
        for parent in [root] + list(root.parents):
            if parent.joinpath("src").exists() or parent.joinpath("sample").exists():
                output_path = str(parent.joinpath("output", root.name))
                break
        else:
            # User case: put arrange/ at the case folder level (input_path itself)
            output_path = str(root.joinpath("arrange"))
    elif output_path.endswith(".csv"):
        _sp = Path(output_path)
        _save_target = output_path
        _save_dir = str(_sp.parent)
        os.makedirs(_save_dir, exist_ok=True)
        output_path = _save_dir
    os.makedirs(output_path, exist_ok=True)

    params = read_paraments(input_path)
    timestep = params.get("timestep", timestep)
    if supercell is None and "supercell" in params:
        supercell = params["supercell"]
    elementorder = None
    if "elementorder" in params:
        try:
            elementorder = eval(params["elementorder"])
        except (NameError, SyntaxError, TypeError):
            pass

    results = {}
    data_pattern = config.filerule1.datafilename
    data_files = glob.glob(os.path.join(input_path, data_pattern))
    dfatoms = pd.DataFrame()
    if data_files:
        data_result = read_data(data_files[0], encoding=encoding, config=config)
        dfatoms = data_result.get("atoms", pd.DataFrame())

    cutoff_raw = config.cutoff
    dfcutoff = pd.DataFrame(
        {"bonds": cutoff_raw.bonds, "bocutoff": cutoff_raw.bocutoff, "blcutoff": cutoff_raw.blcutoff}
    )

    def _save(df: pd.DataFrame, prefix: str, idx: int | None = None, suffix: str = "", extra: str = ""):
        name = prefix
        if idx is not None:
            name += f".split{idx}"
        if extra:
            name += f".{extra}"
        if suffix:
            name += f".{suffix}"
        if "_save_target" in dir() and _save_target is not None and idx is None:
            out_file = _save_target
            _save_target = None
        else:
            out_file = os.path.join(output_path, f"{name}.csv")
        df.to_csv(out_file, encoding="utf-8-sig", index=False)
        gc.collect()

    for mode in modes:
        mode = mode.strip()
        if mode == "Log":
            log_files = sorted(glob.glob(os.path.join(input_path, config.filerule1.logfilename)))
            for n, lf in enumerate(log_files):
                df_log = read_log(
                    lf, log_indices=log_indices, supercell=supercell,
                    ignored_time=ignored_time, timestep=timestep, encoding=encoding,
                )
                _save(df_log, "dataoflog", None if len(log_files) == 1 else n)
                if n == 0:
                    results["log"] = df_log

        elif mode == "Bonds":
            bonds_files = sorted(glob.glob(os.path.join(input_path, config.filerule1.bondsfilename)))
            for n, bf in enumerate(bonds_files):
                df_b = read_bonds(
                    bf, data_path=data_files[0] if data_files else None,
                    dfatoms=dfatoms, dfcutoff=dfcutoff,
                    ignored_time=ignored_time, timestep=timestep, encoding=encoding,
                )
                _save(df_b, "dataofbonds", None if len(bonds_files) == 1 else n)
                if n == 0:
                    results["bonds"] = df_b

        elif mode == "Dump":
            dump_files = sorted(glob.glob(os.path.join(input_path, config.filerule1.dumpfilename)))
            for n, df_path in enumerate(dump_files):
                df_d = read_dump(
                    df_path, data_path=data_files[0] if data_files else None,
                    dfatoms=dfatoms,
                    ignored_time=ignored_time, timestep=timestep, encoding=encoding,
                )
                _save(df_d, "dataofdump", None if len(dump_files) == 1 else n)
                if n == 0:
                    results["dump"] = df_d

        elif mode == "Cell":
            cell_files = sorted(glob.glob(os.path.join(input_path, config.filerule1.cellfilename)))
            if not cell_files:
                dump_files = sorted(glob.glob(os.path.join(input_path, config.filerule1.dumpfilename)))
                cell_files = dump_files
            if cell_files:
                results["cell"] = read_cell(
                    cell_files[0], ignored_time=ignored_time, timestep=timestep, encoding=encoding,
                )
                _save(results["cell"], "dataofcell", None if len(cell_files) == 1 else 0)

        elif mode == "Species":
            species_files = sorted(glob.glob(os.path.join(input_path, config.filerule1.speciesfilename)))
            for n, sf in enumerate(species_files):
                df_s = read_species(sf, ignored_time=ignored_time, timestep=timestep, encoding=encoding, elementorder=elementorder)
                _save(df_s, "dataofspecies", None if len(species_files) == 1 else n)
                if n == 0:
                    results["species"] = df_s

        elif mode == "POS":
            pos_files = sorted(glob.glob(os.path.join(input_path, config.filerule1.posfilename)))
            for n, pf in enumerate(pos_files):
                df_p = read_pos(pf, ignored_time=ignored_time, timestep=timestep, encoding=encoding, elementorder=elementorder)
                _save(df_p, "dataofpos", None if len(pos_files) == 1 else n)
                if n == 0:
                    results["pos"] = df_p

        elif mode == "OVITO":
            ovito_files = sorted(glob.glob(os.path.join(input_path, config.filerule1.ovitofilename)))
            for n, of in enumerate(ovito_files):
                df_o = read_ovito(of, ignored_time=ignored_time, timestep=timestep)
                _save(df_o, "dataofovito", None if len(ovito_files) == 1 else n)
                if n == 0:
                    results["ovito"] = df_o

    return results, output_path
