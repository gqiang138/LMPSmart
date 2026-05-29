# lmpsmart Plotting Principles

> Extracted from source code: `mapping/plot.py`, `mapping/advanced_plot.py`, `mapping/animation.py`, `arrange/config.py`, `api/tools.py`, and legacy `old/lmpanalysis.py`.
> These principles govern how the `plot` and `animation` tools render all figures. They are enforced by the codebase, not the LLM.

---

## 1. Three Rendering Modes

| Mode | Meaning | Use Case |
|---|---|---|
| `single` | All curves on **ONE** shared axes with one y-axis | Compare multiple quantities on the same scale (e.g., x/y/z trajectory, multiple energy terms) |
| `multi` | Each curve on its **own subplot**, shared x-axis | Inspect each quantity independently; auto-layout 2-column grid |
| `doubley` | Two y-axes on **one figure** | Two quantities with very different value ranges (e.g., Temperature + Pressure) |

**Critical defaults:**
- `single` is the **default** mode (`mode` parameter default in `plot_dataframe()`).
- To put x/y/z on **one single figure**: `mode="single"` + `y_cols=["x","y","z"]`. This generates a **legend** automatically.
- `mode="multi"` produces **subplots** — use when the user explicitly says "separate" or "subplot". It **does not** produce a legend.

---

## 2. Legend Configuration

### When Legend Appears

Legend is added **iff** at least one of these is true:
- `hue_col` is provided and present in the DataFrame
- `len(y_cols) > 1` (i.e., 2 or more y-columns on `single` mode)

### Legend Appearance
- `frameon=False` — legend has **no border box**
- `loc="best"` (default) — matplotlib auto-places to avoid data
- Override with `legend_loc` parameter: `"upper right"`, `"lower left"`, `"best"`, etc.
- Legend label: **column name directly** (e.g., `x`, `y`, `TotEng`) — no unit suffix added
- If `subscript_labels=True`, column names in legend are rendered as chemical-formula mathtext

### Legend Modes (`legend_type`)
| Mode | Behaviour | Use Case |
|---|---|---|
| `"auto"` (default) | Seaborn auto-labels from column name | Default — shows column names |
| `"list"` | Custom labels via `legend_labels=[...]` | Override labels completely |
| `"remove"` | No legend | Single curve, or force-hide |
| `"suffix"` | Column name + `legend_suffix` string | Add unit annotation to each label |

### Error Bars (`yerr_col`)
- Set `yerr_col="_std"` (or any column name) — adds `ax.errorbar` overlay on top of the lineplot
- Error bar style: gray, linewidth=1, caps=2px, zorder=0 (behind line)

### When Legend is Hidden
- Single curve (`len(y_cols) == 1`) **without** `hue_col` → **no legend**
- Empty label list from seaborn → legend not added

---

## 3. Color Palette & Styling

### Palette
- **Default: `tab10`** — categorical color palette (10 distinct colors)
  - Cycle: `#1f77b4`, `#ff7f0e`, `#2ca02c`, `#d62728`, `#9467bd`, `#8c564b`, `#e377c2`, `#7f7f7f`, `#bcbd22`, `#17becf`
- Palette applies **only** when `hue_col` is set; without `hue_col` seaborn uses its own default line coloring
- In `doubley` mode: `y1color="black"`, `y2color="red"` (hardcoded in config)

### Global Style (seaborn + matplotlib)
- `sns.set_theme(style="ticks")` — clean style with tick marks, no spine clutter
- `font.family = "serif"`, `font.serif = ["Times New Roman"]` — **Times New Roman** for ALL text
- `axes.unicode_minus = False` — prevents minus sign rendering issues
- `mathtext.fontset = "stix"` — proper math symbol rendering (e.g., subscripts, Greek letters)

### Line Styling
- `linewidth = 2.5` — fixed
- `dashes = False` — solid lines only
- `sort = True` — seaborn sorts by x before plotting
- `errorbar = None` — no confidence intervals

### Markers (optional)
- Triggered by `markers=True` in the `plot` tool
- Cycle: `["o", "s", "^", "D", "v", "p", "h", "*"]`
- Applied per curve index; only activates when `markers=True`

---

## 4. Figure Dimensions & DPI

| Mode | Default `figsize` | Default `dpi` | Layout |
|---|---|---|---|
| `single` | **8 × 6** (width × height in inches) | 600 | tight bbox |
| `multi` | **14 × (rows × 6)** | 600 | 2-column subplot grid, `wspace=0.2`, `hspace=0.2` |
| `doubley` | **10 × 6** | 600 | tight bbox |

### Override Options
- `figsize=(width, height)` — tuple of ints, overrides mode default
- `figsize="width,height"` — string format also accepted by the `plot` tool
- `dpi=N` — integer, overrides default 600

---

## 5. Axis Labels

### Auto-label (DEFAULT)
Column names are mapped to human-readable labels via `DEFAULT_LABELS` in `plot.py`:

| Column | Label | Column | Label |
|---|---|---|---|
| `time` | Time/ps | `temp`, `temperature` | Temperature/K |
| `press`, `pressure` | Pressure/atm | `toteng`, `poteng`, `ke`, `pe` | Energy/(kcal·mol⁻¹) |
| `density` | Density/(g·cm⁻³) | `lx`, `ly`, `lz`, `a`, `b`, `c` | Cell length/Å |
| `x`, `y`, `z` | Position/Å | `vx`, `vy`, `vz` | Velocity/(Å·fs⁻¹) |
| `fx`, `fy`, `fz` | Force/(kcal·mol⁻¹·Å⁻¹) | `charge`, `q` | Charge/$e$ |
| `pxx`, `pyy`, `pzz` | Stress_{xx}/atm etc. | `c_ss` | Stress_{xx}/atm |
| `volume` | Volume/Å³ | `atoms`, `number` | Number |
| `bo` | Bond order | `blcutoff` | Bond length cutoff/Å |

Columns **not** in the map: returned as-is. Columns starting with `c_` get ` / (user-defined)` suffix.

### Manual Override
- `xlabel="..."` overrides auto x label
- `ylabel="..."` overrides auto y label
- Font size: `labelsize=16` (single/doubley), `labelsize=20` (multi)

---

## 6. Tick & Title Fonts

| Element | Size (single/doubley) | Size (multi) | Font |
|---|---|---|---|
| Tick labels | 14 | 18 | Times New Roman |
| Axis labels | 16 | 20 | Times New Roman |
| Title (if set) | 16 | 20 | Times New Roman |

- `subscript_labels=True` converts column names to chemical-formula mathtext (e.g., `H2O` → $H_2O$)
- Formula conversion: uses `re.findall(r"([A-Z][a-z]?)(\d+)", formula)` pattern

---

## 7. Output

- Always `bbox_inches="tight"` — removes excess whitespace
- Always `plt.close(fig)` after saving — releases memory
- Format: determined by file extension in `output_path` (`.png`, `.pdf`, `.jpg`, etc.)
- DPI affects file size: 600 DPI is publication-quality
- **Default output path**: When `output_path` is not specified, tools infer the output folder from `csv_path`:
  - If `csv_path` contains `/arrange/` or `/output/<name>/` → `plot` → `<csv_parent>/../plot/`, `animation` → `<csv_parent>/../animation/`
  - Otherwise → `output/plot/plot1.png` or `output/animation/animation.gif`
- **Arrangement output structure**: For user cases (no `src/` or `sample/` sibling), `arrange` puts data in `<input_path>/arrange/`. For lmpsmart project (with `src/` or `sample/` sibling), `arrange` puts data in `<project>/output/<case_name>/`.
- **Side-by-side CSV export**: `tool_plot` and `tool_animation` automatically save the plotted data as a `.csv` file in the same folder as the output image, using the same base name. This preserves `output/arrange/` (or `<input_path>/arrange/`) as immutable source data while providing verification and reuse alongside every figure.

---

## 8. Tool Parameter Reference

```python
tool_plot(
    csv_path,            # str: path to CSV file
    x_col,               # str: x-axis column name
    y_cols,              # list[str]: y-axis column name(s)
    output_path,         # str|null: save path
    mode="single",       # "single" | "multi" | "doubley"
    hue_col=None,        # str|null: group-by column (adds legend)
    markers=False,        # bool: show circle/square markers
    legend_loc="best",   # str: matplotlib legend location
    subscript=False,      # bool: render column names as mathtext
    title="",            # str: figure title
    xlabel="",           # str: override x label
    ylabel="",            # str: override y label
    figsize=None,         # tuple|str|null: (width,height)
    dpi=None,             # int|null: override default 600
    legend_type="auto",  # "auto" | "list" | "remove" | "suffix"
    legend_labels=None,   # list[str]|null: custom labels for "list" mode
    legend_suffix="",    # str: suffix added to each col name for "suffix" mode
    yerr_col=None,        # str|null: error bar column (e.g. "_std")
)
```

---

## 9. Data Flow for Common Use Cases

### Case A: Atom trajectory (x/y/z vs time) → single figure + legend
```json
{
  "tool": "select_columns",
  "params": {"csv_path": "output/arrange/dataofdump.csv", "columns": ["time","x","y","z"], "output_path": "output/arrange/tmp.csv"}
}
{
  "tool": "belong_filter",
  "params": {"csv_path": "output/arrange/tmp.csv", "col": "id", "values": [1], "keep": true, "output_path": "output/arrange/atom1.csv"}
}
{
  "tool": "plot",
  "params": {"csv_path": "output/arrange/atom1.csv", "x_col": "time", "y_cols": ["x","y","z"], "output_path": "output/plot/atom1_trajectory.png", "mode": "single"}
}
```
→ **Legend appears** (len(y_cols)=3), all three curves on ONE shared axes, column names (`x`, `y`, `z`) used as legend labels directly.

### Case B: Multiple energy terms → single figure + legend
```json
{
  "tool": "plot",
  "params": {"csv_path": "output/arrange/dataoflog.csv", "x_col": "time", "y_cols": ["TotEng","PotEng","KinEng"], "output_path": "output/plot/energy.png", "mode": "single"}
}
```

### Case C: Temperature and pressure on different scales → doubley
```json
{
  "tool": "plot",
  "params": {"csv_path": "output/arrange/dataoflog.csv", "x_col": "time", "y_cols": ["Temp","Press"], "output_path": "output/plot/temp_press.png", "mode": "doubley"}
}
```

### Case D: Each bond type's BO over time → separate subplots
```json
{
  "tool": "plot",
  "params": {"csv_path": "output/arrange/dataofbonds.csv", "x_col": "time", "y_cols": ["C-O","C-H","N-H"], "output_path": "output/plot/bo_subplots.png", "mode": "multi"}
}
```

---

## 10. Common Mistakes to Avoid

1. **Using `mode="multi"` when you want a legend on one figure** — `multi` creates subplots, no legend. Use `mode="single"` with `y_cols=[...]` instead.

2. **Single y_col with no legend** — If user wants a label, use `title` or `ylabel` as the label.

3. **Unicode Å vs LaTeX `\AA`** — The codebase uses **Unicode `Å`** directly in `DEFAULT_LABELS` (line 52-54). Do not use `\AA` (LaTeX syntax) since `mathtext.fontset="stix"` and non-usetex mode do not render it as Å.

4. **`hue_col` adds color groups** — If you want a legend for a single y-column split by another categorical column (e.g., different atom types), set `hue_col="type"` instead of calling `plot` multiple times.

5. **Output dir must exist** — `plot_dataframe` does not create directories. Ensure `output_path`'s directory exists before calling `plot`.

---

## 11. Color Maps (Colormaps)

Available colormaps for `tricontourf` (isograph), surface plots, and heatmaps:

| Name | Description |
|---|---|
| `rainbow` | Full visible spectrum (matplotlib default for contour) |
| `jet` | Classic blue-white-red thermal scale |
| `turbo` | Improved thermal scale (perceptually uniform) |
| `viridis` | Perceptually uniform, colorblind-safe |
| `plasma` | Magenta-to-yellow, colorblind-safe |
| `YlOrBr` | Yellow-orange-brown sequential |
| `gnuplot` | GNU plot style |
| `gnuplot2` | Improved GNU plot style |
| `brg` | Blue-red-green diverging |
| `gist_rainbow` | Full spectrum rainbow |
| `Spectral` | Diverging (blue-white-red), for signed data |
| `coolwarm` | Blue-white-red diverging |
| `seismic` | Blue-black-red diverging |

**Usage**: When creating isograph / contour plots, pass `cmap="rainbow"` or any matplotlib colormap name to `tricontourf`.

---

## 12. Advanced Plot Types

### 12.1 Scatter with Size Encoding
```python
# Encode a third variable (e.g., temperature, weight) as marker size
plt.scatter(x, y, s=size_values, alpha=0.6)
# s values: DataFrame['size_col'] normalized to reasonable pixel range (e.g., 10-200)
# Common use: bubble chart — x=time, y=molecule, s=weight/concentration
```

### 12.2 Isograph (Filled Contour, 2D Projection)
```python
# triangulated filled contour — for 2D spatial data projected from 3D trajectory
import matplotlib.tri as mtri
import numpy as np
ax.tricontourf(X, Y, Z, levels=isoset, cmap='rainbow')
ax.set_xlabel('X Label', fontproperties=fontset)
ax.set_ylabel('Y Label', fontproperties=fontset)
ax.set_title(title)
plt.colorbar().set_label('Z Label')
```
- `X, Y`: 1D arrays of coordinates (same length as Z)
- `Z`: scalar values at each point
- `levels`: list of contour thresholds (e.g., `np.linspace(0, 1, 20)`)
- `cmap`: colormap — use `rainbow`, `jet`, `viridis`, etc.
- Use when: visualizing a scalar field over a 2D slice from MD trajectory (e.g., temperature, density, stress)

### 12.3 Boxplot
```python
sns.boxplot(data=df, x='group_col', y='value_col', hue='hue_col')
# Use for: comparing distributions across groups (e.g., bond lengths by atom type)
```

### 12.4 Violinplot
```python
sns.violinplot(data=df, x='group_col', y='value_col', hue='hue_col')
# Use for: distribution shape comparison (shows density + quartiles)
```

### 12.5 Surface Plot (3D)
```python
from mpl_toolkits.mplot3d import Axes3D
ax = fig.add_subplot(111, projection='3d')
X, Y = np.meshgrid(x_vals, y_vals)
Z = np.reshape(z_vals, X.shape)
ax.plot_surface(X, Y, Z, cmap='viridis', alpha=0.8)
ax.set_xlabel('X'); ax.set_ylabel('Y'); ax.set_zlabel('Z')
# Use for: 3D energy surfaces, potential landscapes, E(volume) surfaces
```

### 12.6 Stress-Strain Curve
```python
# Special case: x = strain, y = stress, from stress-strain data
# Auto-label: strain → dimensionless, stress → GPa (if unit provided)
# Often paired with polyfit for yield strength extraction
plt.plot(strain, stress, 'o-', linewidth=1.5)
plt.xlabel('Strain', fontsize=16)
plt.ylabel('Stress/GPa', fontsize=16)
# Common fit: piecewise linear (elastic + plastic regions)
```

### 12.7 NEB Energy Profile
```python
# x = reaction coordinate (normalized 0-1), y = energy
# Plot reaction barriers as line + scatter
plt.plot(reaction_coord, energy, 'o-', color='blue')
plt.xlabel('Reaction Coordinate', fontsize=16)
plt.ylabel('Energy/eV', fontsize=16)
# Mark saddle points with different marker
```

### 12.8 MSXRD Pattern
```python
# x = 2θ (degrees), y = intensity
# Plot as step line or area fill
plt.plot(two_theta, intensity, 'k-', linewidth=1)
plt.xlabel('2θ/degree', fontsize=16)
plt.xlabel('Intensity/counts', fontsize=16)
# Peak identification overlays possible
```

---

## 13. Animation Plotting (动图) — 3 Animation Types

### 13.1 Overview
Animation plots iterate over simulation frames, generating sequential figures. Output formats: `.html` (interactive, via `matplotlib.animation.HTMLWriter`) and `.gif` (animated image, via `pillow`).

### 13.2 Common Parameters
- `frames`: `range(start_frame, end_frame + 1, step)`
- `interval`: ms between frames (default 50)
- `repeat`: `False` (no loop)
- `FuncAnimation(fig, update_func, frames=..., fargs=(...))`

### 13.3 Type A: Isograph (2D Filled Contour)
```python
# For spatial scalar fields from MD trajectories (temp, density, stress field)
from matplotlib.animation import FuncAnimation
import matplotlib.colors as mcolors

def animate_isograph(frame, df, fig, ax):
    df_frame = df[df['frame'] == frame].reset_index(drop=True)
    ax.cla()
    X = df_frame['x'].values  # or 'nx', 'Coord1' with cell offset
    Y = df_frame['y'].values
    Z = df_frame['scalar_col'].values  # temp, density, c_ss, etc.
    levels = np.linspace(Z.min(), Z.max(), 20)
    ax.tricontourf(X, Y, Z, levels=levels, cmap='rainbow')
    ax.set_xlabel('X/Å', fontsize=14)
    ax.set_ylabel('Y/Å', fontsize=14)
    ax.set_title(f'Frame {frame}', fontsize=14)
    return []

ani = FuncAnimation(fig, animate_isograph,
    frames=range(frames[0], frames[1]+1, thermostep),
    fargs=(df, fig, ax),
    interval=interval_val, repeat=False)
ani.save('isograph.gif', writer='pillow', dpi=200)
ani.save('isograph.html', writer='html', dpi=100)
```

### 13.4 Type B: Bar Chart Animation
```python
# For species counts, bond counts, molecule populations over time
def animate_bar(frame, df, fig, ax):
    df_frame = df[df['frame'] == frame].reset_index(drop=True)
    ax.cla()
    x = df_frame['x_col'].values
    y = df_frame['y_col'].values
    ax.bar(x, y, width=bar_scale)
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min * 0.95, y_max * 1.05)
    ax.set_xlabel('Species', fontsize=14)
    ax.set_ylabel('Count', fontsize=14)
    return []

ani = FuncAnimation(fig, animate_bar,
    frames=range(...), fargs=(df, fig, ax),
    interval=interval_val, repeat=False)
ani.save('bar_anim.gif', writer='pillow', dpi=200)
```

### 13.5 Type C: Line Chart Animation
```python
# For trajectory data: x/y/z positions over time
def animate_line(frame, df, fig, ax):
    df_frame = df[df['frame'] == frame].reset_index(drop=True)
    ax.cla()
    x = df_frame['x_col'].values
    y = df_frame['y_col'].values
    ax.plot(x, y, 'o-', markersize=4)
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)
    return []

ani = FuncAnimation(fig, animate_line,
    frames=range(...), fargs=(df, fig, ax),
    interval=interval_val, repeat=False)
ani.save('line_anim.gif', writer='pillow', dpi=200)
```

### 13.6 Type D: Reacdraw (3D Molecule with Bonds)
```python
# 3D molecular structure with bond visualization
# Color coding: black=stable bonds, red=breaking bonds, green=forming bonds
# Threshold: bond length < 2.0 Å to display
from mpl_toolkits.mplot3d import Axes3D

def animate_reacdraw(frame, df, fig, ax, axislimits, title_str):
    df_frame = df[df['frame'] == frame].reset_index(drop=True)
    ax.cla()
    ax = fig.add_subplot(111, projection='3d')
    xyz = df_frame['xyzlist'].values[0]  # list of [x,y,z] per atom
    elems = df_frame['elements'].values[0]  # element symbols
    idbond = df_frame['idbond'].values[0]  # list of (id1, id2)
    breaks = df_frame['break'].values[0]
    creates = df_frame['create'].values[0]
    iddict = dict(zip(df_frame['idlist'].values[0], xyz))
    # scatter atoms
    x = [p[0] for p in xyz]; y = [p[1] for p in xyz]; z = [p[2] for p in xyz]
    cdict = {'C':'C0','H':'C1','N':'C3','O':'C4','Al':'C5'}
    colors = [cdict.get(e, 'gray') for e in elems]
    ax.scatter(x, y, z, c=colors, s=100, marker='o')
    # draw bonds
    for bond in idbond:
        p1 = np.array(iddict[bond[0]]); p2 = np.array(iddict[bond[1]])
        dist = np.linalg.norm(p1 - p2)
        if dist < 2.0:
            if bond[0] in breaks: col = 'red'
            elif bond[0] in creates: col = 'green'
            else: col = 'black'
            ax.plot([p1[0],p2[0]], [p1[1],p2[1]], [p1[2],p2[2]],
                    color=col, linewidth=4)
    ax.set_xlim(axislimits[0], axislimits[1])
    ax.set_ylim(axislimits[2], axislimits[3])
    ax.set_zlim(axislimits[4], axislimits[5])
    ax.set_xlabel('X/Å'); ax.set_ylabel('Y/Å'); ax.set_zlabel('Z/Å')
    ax.set_title(eval(title_str), fontsize=14)
    return []
```

---

## 14. Advanced Styling Details

### 14.1 Minor Ticks (Sub-ticks)
```python
from matplotlib.ticker import AutoMinorLocator
ax.xaxis.set_minor_locator(AutoMinorLocator(2))  # 2 minor ticks between major ticks
ax.yaxis.set_minor_locator(AutoMinorLocator(2))
ax.minorticks_on()
```

### 14.2 Scientific Notation Control
```python
import matplotlib.ticker as ticker
formatter = ticker.ScalarFormatter()
formatter.set_scientific(False)  # Prevent 1e6 notation
ax.yaxis.set_major_formatter(formatter)
```

### 14.3 Subplot Adjustments (multi-panel)
```python
plt.subplots_adjust(
    left=0.10, bottom=0.12, right=0.95, top=0.90,
    wspace=0.25, hspace=0.30
)
```

### 14.4 Scatter Markers Cycle
Marker cycle for multi-dataset plotting: `["o", "s", "^", "D", "v", "p", "h", "*"]`
```python
marker_cycle = ["o", "s", "^", "D", "v", "p", "h", "*"]
markers = [marker_cycle[i % len(marker_cycle)] for i in range(n_curves)]
```

### 14.5 Bar Chart Width
Default bar width scale: `bar_scale = 5` (data units). Adjust per dataset density.

---

## 15. Common Use Cases from Legacy Source (targetfig examples)

These examples from `lmpanalysis.py` targetfig system show patterns the agent should recognize:

| Use Case | Data Source | X | Y | Hue/Filter | Notes |
|---|---|---|---|---|---|
| Energy vs time | log | time | TotEng, PotEng, KinEng | — | single, legend |
| Cell volume vs time | log | time | Volume | — | single |
| Species counts | species/reacspecies | time | number | molecule | belong filter |
| Bond order over time | bonds | time | bo (min) | bonds | belong filter |
| Species weight | reacspecies | weight | frame | — | size encoding |
| Reaction counts | reacspace | time | num | reaction | belong filter |
| Bond changes | reacspace | time | changenum | changebonds | cumsum option |
| Stress-strain | stress | strain | stress | — | piecewise fit |
| NEB energy profile | neb | normalize | dE | — | scatter markers |
| MSXRD pattern | custom | 2theta | intensity columns | — | line |
| Chunk temperature map | chunk+cell | Coord1 | Coord2 | temp | isograph |
| 3D molecule animation | dump | frame | x,y,z | id | reacdraw |
| Atom trajectory | dump | time | x,y,z | id | line animation |

---

## 16. Data Merge Patterns (from Legacy targetfig)

### 16.1 Merge — Join dataframes on column(s)
```python
# Merge two dataframes on frame/time columns
df_merged = pd.merge(df1, df2, on=['frame', 'time'], how='left')
# Common: merge chunk data with cell data for coordinate transformation
# Coord1_real = Coord1 * cell_lx + cell_x0
```

### 16.2 Concat — Stack dataframes (multi-folder aggregation)
```python
# Concatenate across folders, plot each folder separately (no hue)
df_all = pd.concat([df1, df2, df3], ignore_index=True)
# Add folder name as hue column
df_all['folder_name'] = df_all['source'].apply(lambda x: extract_name(x))
```

### 16.3 Third-Filter — Filter by third variable
```python
# Filter y data by a third column value (z filter)
# e.g., only plot time series for specific molecule species
df_filtered = df[df['molecule'].isin(['H2O', 'CO2'])]
```

---

## 17. Config Source of Truth

These defaults are defined in `configs/default.yaml` under the `plotset:` key and loaded via `arrange/config.py` → `PlotSetSingle` / `PlotSetDoubleY` Pydantic models. Any programmatic use should prefer reading from `load_config()` rather than hardcoding values.

```yaml
plotset:
  sns_style: ticks
  palette: tab10
  font_family: "Times New Roman"
  singlescale:     # mode="single"
    width: 8
    high: 6
    dpi: 600
    labelsize: 16
    ticksize: 14
  multifig:        # mode="multi"
    width: 14
    high: 6
    dpi: 600
    labelsize: 20
    ticksize: 18
  doubleyscale:    # mode="doubley"
    width: 10
    high: 6
    dpi: 600
    labelsize: 16
    ticksize: 14
    y1color: "black"
    y2color: "red"
  animationscale:  # animation plots
    width: 12
    high: 8
    dpi: 100
    labelsize: 16
    ticksize: 14
    default_interval: 200   # ms between frames
    default_cmap: "rainbow"
    default_format: "gif"
```

---

## 18. Advanced Plot Tools (`tool_plot`)

The `plot` tool now dispatches on `plot_type` to 7 different backends:

| `plot_type` | Function | Use Case |
|---|---|---|
| `"line"` | `tool_plot_dataframe` | Default. Line plot (single/multi/doubley) via `sns.lineplot` |
| `"scatter"` | `tool_plot_scatter` | Scatter with optional `size_col` (bubble) and `color_col` (colormap encoding) |
| `"boxplot"` | `tool_plot_boxplot` | Distribution comparison across categories |
| `"violin"` | `tool_plot_violin` | Full distribution shape, split violins with `hue_col` |
| `"surface"` | `tool_plot_surface` | 3D energy landscape via `Axes3D.plot_surface`. `elev`/`azim` for view angle |
| `"contour"` | `tool_plot_contour` | 2D filled or line contours. `levels` controls contour count |
| `"heatmap"` | `tool_plot_heatmap` | Pivot-table heatmap. `annot=True` for cell values |

Key parameters:
- `cmap`: colormap name (`"tab10"`, `"rainbow"`, `"viridis"`, `"coolwarm"`, etc.)
- `levels`: contour level count for contour plots (default 20)
- `filled`: `True`=filled contour (`contourf`), `False`=line contours
- `annot`: show cell values in heatmap cells
- `elev`, `azim`: 3D surface view angles (default 30°, 45°)

### Advanced Plot Examples

**Boxplot**: Compare energy distributions per species category:
```
plot(csv_path, x_col="category", y_cols=["poteng"], plot_type="boxplot", hue_col="atom_type")
```

**Violin**: Show velocity distribution shape per atom type:
```
plot(csv_path, x_col="type", y_cols=["vx"], plot_type="violin")
```

**Scatter with size** (bubble chart — MSXRD peak intensity vs 2θ):
```
plot(csv_path, x_col="two_theta", y_cols=["intensity"], size_col="area", plot_type="scatter")
```

**3D Surface** (energy landscape):
```
plot(csv_path, x_col="rxn_coord", y_cols=["temperature", "energy"], plot_type="surface", cmap="viridis")
```

**Contour** (NEB energy profile):
```
plot(csv_path, x_col="image", y_cols=["coord", "energy"], plot_type="contour", filled=True)
```

**Heatmap** (species abundance vs time and temperature):
```
plot(csv_path, x_col="time", y_cols=["temp", "species_count"], plot_type="heatmap", annot=True)
```

---

## 19. Animation Tools (`tool_animation`)

The `animation` tool produces time-evolving figures as `.gif` or `.html`.

### Animation Modes

| Mode | Backend | Data Requirement |
|---|---|---|
| `"isograph"` | `plt.tricontourf` | DataFrame with x_col, y_col (coordinates), z_col (value), frame column |
| `"bar"` | `plt.bar` | DataFrame with x_col, y_col, frame column |
| `"line"` | `plt.plot` | DataFrame with x_col, y_col, frame column |
| `"reacdraw"` | `Axes3D.scatter + plot` | DataFrame with per-frame columns: idlist, xyz, elements, idbond, break, create |

### Animation Parameters

| Parameter | Default | Description |
|---|---|---|
| `interval` | 200 | Milliseconds between frames |
| `repeat` | `False` | Loop animation |
| `frames` | all unique frames | Frame sequence to animate |
| `cmap` | `"rainbow"` | Colormap (isograph mode) |
| `isoset` | auto | Contour levels for isograph |
| `barscale` | 0.5 | Bar width scale (bar mode) |
| `scatterscale` | 1.0 | Atom size for reacdraw |

### Animation Examples

**Isograph** (chunk map / temperature map over MD frames):
```
animation(csv_path, mode="isograph", x_col="x", y_col="y", z_col="temperature",
          output_path="chunk_map.gif", cmap="rainbow", interval=300)
```

**Bar chart** (species count evolution):
```
animation(csv_path, mode="bar", x_col="species", y_col="count",
          output_path="species_bar.gif", interval=200)
```

**Line animation** (property trajectory per frame):
```
animation(csv_path, mode="line", x_col="time", y_col="poteng",
          output_path="energy_line.gif", interval=200)
```

**Reacdraw** (3D molecular animation with bond colour coding):
```
animation(csv_path, mode="reacdraw", output_path="reaction.gif",
          scatterscale=1.0, interval=500, title="Reactions at t=")
```

Output format is auto-detected from extension: `.html` (interactive) or `.gif` (animated image).
