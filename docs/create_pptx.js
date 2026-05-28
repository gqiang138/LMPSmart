const pptxgen = require("pptxgenjs");
const fs = require("fs");

const pptx = new pptxgen();

// Color palette
const DARK_BG = "0D1B2A";
const DEEP_BLUE = "065A82";
const TEAL = "1C7293";
const MIDNIGHT = "21295C";
const LIGHT_BG = "F0F4F8";
const ACCENT = "00B4D8";
const TEXT_LIGHT = "FFFFFF";
const TEXT_DARK = "1B263B";
const MUTED = "778DA9";
const CARD_BG = "E8F0F7";

const opts = {
  slideNumber: { color: MUTED, fontSize: 10 },
  margin: 0.5,
};

// ==============================================================
// Slide 1: Title
// ==============================================================
let slide = pptx.addSlide();
slide.background = { color: DARK_BG };

slide.addText("lmpsmart", {
  x: 0.5, y: 1.8, w: 9, h: 1.2,
  fontSize: 72, bold: true, color: ACCENT, fontFace: "Georgia",
  align: "left",
});

slide.addText("LAMMPS Molecular Dynamics Data Processing Agent", {
  x: 0.5, y: 3.0, w: 9, h: 0.6,
  fontSize: 24, color: TEXT_LIGHT, fontFace: "Calibri",
  align: "left",
});

// Hexagonal decorative shapes (simplified as circles in hex pattern)
const hexPositions = [
  [8.5, 0.5], [9.0, 1.0], [8.2, 1.2], [9.3, 1.7], [8.7, 2.0],
  [8.0, 0.8], [9.6, 0.8], [8.9, 2.4], [7.8, 1.6],
];
hexPositions.forEach(([x, y]) => {
  slide.addShape(pptx.shapes.OVAL, {
    x, y, w: 0.18, h: 0.18,
    fill: { color: DEEP_BLUE, transparency: 60 },
    line: { color: TEAL, width: 0.5, transparency: 40 },
  });
});

slide.addText("v1.0.0  |  GPL-3.0  |  Qiang Gan", {
  x: 0.5, y: 4.5, w: 9, h: 0.4,
  fontSize: 14, color: MUTED, fontFace: "Calibri",
});

slide.addShape(pptx.shapes.RECTANGLE, {
  x: 0.5, y: 3.7, w: 3.5, h: 0.05,
  fill: { color: ACCENT },
});

// ==============================================================
// Slide 2: Background & Problem
// ==============================================================
slide = pptx.addSlide();
slide.background = { color: LIGHT_BG };

slide.addText("为什么需要 lmpsmart？", {
  x: 0.5, y: 0.3, w: 9, h: 0.7,
  fontSize: 36, bold: true, color: TEXT_DARK, fontFace: "Georgia",
  margin: 0,
});

// Three problem cards
const problems = [
  { icon: "DATASET", title: "海量异构数据", desc: "LAMMPS + ReaxFF 产生热力学、键拓扑、化学物种等多类型数据" },
  { icon: "GUI", title: "传统方案局限", desc: "GUI工具（OVITO/VMD）+ 定制脚本（硬编码参数、无批量处理）" },
  { icon: "TRACE", title: "无可追溯性", desc: "手动操作无法复现，实验记录依赖人工备注" },
];

problems.forEach((p, i) => {
  const x = 0.5 + i * 3.1;
  // Card background
  slide.addShape(pptx.shapes.ROUNDED_RECTANGLE, {
    x, y: 1.2, w: 2.9, h: 2.8,
    fill: { color: CARD_BG },
    line: { color: DEEP_BLUE, width: 1 },
    rectRadius: 0.08,
  });
  // Icon circle
  slide.addShape(pptx.shapes.OVAL, {
    x: x + 1.05, y: 1.4, w: 0.8, h: 0.8,
    fill: { color: DEEP_BLUE },
  });
  slide.addText(p.icon.substring(0, 2), {
    x: x + 1.05, y: 1.5, w: 0.8, h: 0.6,
    fontSize: 16, bold: true, color: TEXT_LIGHT, align: "center", valign: "middle",
  });
  slide.addText(p.title, {
    x: x + 0.15, y: 2.4, w: 2.6, h: 0.5,
    fontSize: 16, bold: true, color: TEXT_DARK, align: "center",
  });
  slide.addText(p.desc, {
    x: x + 0.15, y: 2.9, w: 2.6, h: 0.9,
    fontSize: 12, color: TEXT_DARK, align: "center", valign: "top",
  });
});

// Arrow down to solution
slide.addShape(pptx.shapes.RECTANGLE, {
  x: 4.5, y: 4.1, w: 0.08, h: 0.5,
  fill: { color: TEAL },
});
slide.addText("↓", {
  x: 4.3, y: 4.55, w: 0.5, h: 0.4,
  fontSize: 20, color: TEAL, align: "center",
});

// Solution box
slide.addShape(pptx.shapes.ROUNDED_RECTANGLE, {
  x: 2.5, y: 4.9, w: 5, h: 0.7,
  fill: { color: DEEP_BLUE },
  rectRadius: 0.06,
});
slide.addText("lmpsmart：Config-Driven + Agent 架构 + 全链路可追溯", {
  x: 2.5, y: 4.9, w: 5, h: 0.7,
  fontSize: 14, bold: true, color: TEXT_LIGHT, align: "center", valign: "middle",
});

// ==============================================================
// Slide 3: Architecture Overview
// ==============================================================
slide = pptx.addSlide();
slide.background = { color: DARK_BG };

slide.addText("三层架构设计", {
  x: 0.5, y: 0.3, w: 9, h: 0.7,
  fontSize: 36, bold: true, color: TEXT_LIGHT, fontFace: "Georgia",
  margin: 0,
});

// Flow diagram: 3 layers
const layers = [
  { y: 1.2, color: DEEP_BLUE, label: "INPUT", sub: "LAMMPS files (Log, Bonds, Dump...)" },
  { y: 2.0, color: TEAL, label: "ARRANGE LAYER", sub: "8 parsers + glob batch + YAML config" },
  { y: 2.9, color: ACCENT, label: "DataFrame", sub: "pandas DataFrame intermediate" },
  { y: 3.7, color: TEAL, label: "MAPPING LAYER", sub: "9 smoothers + 3 outlier filters" },
  { y: 4.5, color: DEEP_BLUE, label: "OUTPUT", sub: "CSV, JSON, figures" },
];

layers.forEach((l, i) => {
  const isBox = l.label.includes("LAYER") || l.label === "DataFrame";
  if (isBox) {
    slide.addShape(pptx.shapes.ROUNDED_RECTANGLE, {
      x: 0.5, y: l.y, w: 9, h: 0.7,
      fill: { color: l.color },
      rectRadius: 0.06,
    });
  }
  slide.addText(l.label, {
    x: 0.6, y: l.y, w: 2.5, h: 0.7,
    fontSize: 14, bold: true, color: TEXT_LIGHT, valign: "middle",
    fontFace: "Calibri",
  });
  slide.addText(l.sub, {
    x: 3.2, y: l.y, w: 6, h: 0.7,
    fontSize: 13, color: TEXT_LIGHT, valign: "middle",
    fontFace: "Calibri",
  });
  // Arrow
  if (i < layers.length - 1) {
    slide.addText("▼", {
      x: 4.7, y: l.y + 0.65, w: 0.5, h: 0.3,
      fontSize: 12, color: MUTED, align: "center",
    });
  }
});

// Agent Controller on right
slide.addShape(pptx.shapes.ROUNDED_RECTANGLE, {
  x: 6.5, y: 2.0, w: 3.2, h: 1.5,
  fill: { color: MIDNIGHT },
  line: { color: ACCENT, width: 1.5 },
  rectRadius: 0.06,
});
slide.addText("AGENT\nCONTROLLER", {
  x: 6.5, y: 2.05, w: 3.2, h: 0.5,
  fontSize: 13, bold: true, color: ACCENT, align: "center",
  fontFace: "Calibri",
});
slide.addText("plan_from_goal()\n     ↓\nexecute()\n     ↓\nJSONL Logger", {
  x: 6.6, y: 2.55, w: 3, h: 0.9,
  fontSize: 11, color: TEXT_LIGHT, align: "center",
  fontFace: "Consolas",
});

// Connecting line from agent to Arrange
slide.addShape(pptx.shapes.LINE, {
  x: 6.5, y: 2.75, w: -0.7, h: 0,
  line: { color: ACCENT, width: 1, dashType: "dash" },
});

// ==============================================================
// Slide 4: Arrange Layer - 8 file parsers
// ==============================================================
slide = pptx.addSlide();
slide.background = { color: LIGHT_BG };

slide.addText("Arrange Layer：8种文件格式解析", {
  x: 0.5, y: 0.3, w: 9, h: 0.7,
  fontSize: 36, bold: true, color: TEXT_DARK, fontFace: "Georgia",
  margin: 0,
});

const parsers = [
  { name: "Log", desc: "LAMMPS 热力学输出\n温度、压力、能量", color: DEEP_BLUE },
  { name: "Bonds", desc: "键序分析 (ReaxFF)\n30种键类型", color: TEAL },
  { name: "Dump", desc: "原子轨迹\n位置/速度/力", color: ACCENT },
  { name: "Cell", desc: "晶胞维度\n晶格常数变化", color: MIDNIGHT },
  { name: "Species", desc: "化学物种计数\n实时物种分布", color: DEEP_BLUE },
  { name: "POS", desc: "POSCAR格式\n晶体结构文件", color: TEAL },
  { name: "OVITO", desc: "OVITO导出格式\n可视化中间格式", color: ACCENT },
  { name: "General", desc: "通用 CSV/TSV\n自动检测分隔符", color: MIDNIGHT },
];

parsers.forEach((p, i) => {
  const col = i % 4;
  const row = Math.floor(i / 4);
  const x = 0.4 + col * 2.4;
  const y = 1.2 + row * 2.0;

  // Card
  slide.addShape(pptx.shapes.ROUNDED_RECTANGLE, {
    x, y, w: 2.2, h: 1.7,
    fill: { color: CARD_BG },
    line: { color: p.color, width: 2 },
    rectRadius: 0.08,
  });
  // Color bar on left
  slide.addShape(pptx.shapes.RECTANGLE, {
    x, y, w: 0.12, h: 1.7,
    fill: { color: p.color },
  });
  // Icon
  slide.addShape(pptx.shapes.OVAL, {
    x: x + 0.75, y: y + 0.15, w: 0.7, h: 0.7,
    fill: { color: p.color },
  });
  slide.addText(p.name.substring(0, 3), {
    x: x + 0.75, y: y + 0.2, w: 0.7, h: 0.6,
    fontSize: 12, bold: true, color: TEXT_LIGHT, align: "center", valign: "middle",
  });
  slide.addText(p.name, {
    x: x + 0.15, y: y + 0.9, w: 1.9, h: 0.3,
    fontSize: 14, bold: true, color: TEXT_DARK, align: "center",
  });
  slide.addText(p.desc, {
    x: x + 0.15, y: y + 1.2, w: 1.9, h: 0.45,
    fontSize: 10, color: MUTED, align: "center",
  });
});

// ==============================================================
// Slide 5: Mapping Layer - smoothers + filters
// ==============================================================
slide = pptx.addSlide();
slide.background = { color: DARK_BG };

slide.addText("Mapping Layer：信号处理算法", {
  x: 0.5, y: 0.3, w: 9, h: 0.7,
  fontSize: 36, bold: true, color: TEXT_LIGHT, fontFace: "Georgia",
  margin: 0,
});

// Smoothing algorithms - 3 groups
const groups = [
  {
    title: "物理约束类", color: TEAL,
    algos: ["segment_spline", "adaptive_kalman", "physics_constrained"],
    desc: "基于物理模型或约束的平滑方法",
  },
  {
    title: "统计平滑类", color: ACCENT,
    algos: ["robust_lowess", "moving_avg", "ewma"],
    desc: "基于统计估计的局部/全局平滑",
  },
  {
    title: "频域处理类", color: MIDNIGHT,
    algos: ["wavelet", "dynamic_wavelet", "savgol"],
    desc: "基于小波/频域变换的信号去噪",
  },
];

groups.forEach((g, gi) => {
  const x = 0.4 + gi * 3.15;
  slide.addShape(pptx.shapes.ROUNDED_RECTANGLE, {
    x, y: 1.1, w: 3.0, h: 2.3,
    fill: { color: g.color, transparency: 20 },
    line: { color: g.color, width: 1.5 },
    rectRadius: 0.06,
  });
  slide.addText(g.title, {
    x, y: 1.15, w: 3.0, h: 0.45,
    fontSize: 15, bold: true, color: g.color, align: "center", valign: "middle",
  });
  slide.addText(g.desc, {
    x: x + 0.1, y: 1.6, w: 2.8, h: 0.3,
    fontSize: 10, color: MUTED, align: "center",
  });
  g.algos.forEach((a, ai) => {
    slide.addShape(pptx.shapes.ROUNDED_RECTANGLE, {
      x: x + 0.15, y: 2.0 + ai * 0.42, w: 2.7, h: 0.35,
      fill: { color: g.color },
      rectRadius: 0.04,
    });
    slide.addText(a, {
      x: x + 0.15, y: 2.0 + ai * 0.42, w: 2.7, h: 0.35,
      fontSize: 12, color: TEXT_LIGHT, align: "center", valign: "middle",
      fontFace: "Consolas",
    });
  });
});

// Outlier filters section
slide.addText("异常值过滤", {
  x: 0.5, y: 3.55, w: 9, h: 0.4,
  fontSize: 18, bold: true, color: TEXT_LIGHT,
});
const filters = [
  { name: "zscore", desc: "Z分数法 |z|>σ阈值为异常 | 等效3σ原则", color: "F4A261" },
  { name: "MAD", desc: "中位数绝对偏差 | 50%异常数据仍鲁棒", color: "E76F51" },
  { name: "IQR", desc: "四分位距法 | 非参数，无需分布假设", color: "2A9D8F" },
];
filters.forEach((f, i) => {
  const x = 0.4 + i * 3.15;
  slide.addShape(pptx.shapes.ROUNDED_RECTANGLE, {
    x, y: 4.0, w: 3.0, h: 0.85,
    fill: { color: f.color },
    rectRadius: 0.06,
  });
  slide.addText(f.name.toUpperCase(), {
    x, y: 4.02, w: 3.0, h: 0.35,
    fontSize: 14, bold: true, color: TEXT_LIGHT, align: "center",
  });
  slide.addText(f.desc, {
    x: x + 0.1, y: 4.38, w: 2.8, h: 0.45,
    fontSize: 10, color: TEXT_LIGHT, align: "center",
  });
});

// ==============================================================
// Slide 6: Agent Architecture
// ==============================================================
slide = pptx.addSlide();
slide.background = { color: LIGHT_BG };

slide.addText("Agent 架构：自然语言 → 工具链", {
  x: 0.5, y: 0.3, w: 9, h: 0.7,
  fontSize: 36, bold: true, color: TEXT_DARK, fontFace: "Georgia",
  margin: 0,
});

// Flow: Goal → plan → tools → log
const flowSteps = [
  { x: 0.3, w: 1.8, label: "Natural\nLanguage\nGoal", bg: DEEP_BLUE },
  { x: 2.3, w: 2.2, label: "plan_from_goal()\n关键词/LLM\n规划工具链", bg: TEAL },
  { x: 4.7, w: 2.5, label: "execute()\n18 tools in\nTOOL_REGISTRY", bg: ACCENT },
  { x: 7.4, w: 2.0, label: "JSONL\nLogger\n完整追溯", bg: MIDNIGHT },
];
flowSteps.forEach((s, i) => {
  slide.addShape(pptx.shapes.ROUNDED_RECTANGLE, {
    x: s.x, y: 1.1, w: s.w, h: 1.0,
    fill: { color: s.bg },
    rectRadius: 0.06,
  });
  slide.addText(s.label, {
    x: s.x, y: 1.1, w: s.w, h: 1.0,
    fontSize: 12, bold: true, color: TEXT_LIGHT, align: "center", valign: "middle",
  });
  if (i < flowSteps.length - 1) {
    slide.addText("→", {
      x: s.x + s.w, y: 1.35, w: 0.4, h: 0.5,
      fontSize: 20, color: DEEP_BLUE, align: "center",
    });
  }
});

// Tool categories - 3 columns
const toolCats = [
  {
    title: "Arrange", tools: ["arrange", "load_config"],
    color: DEEP_BLUE,
  },
  {
    title: "Read (8)", tools: ["read_log", "read_bonds", "read_dump", "read_data", "read_cell", "read_species", "read_pos", "read_general"],
    color: TEAL,
  },
  {
    title: "Map + Chem", tools: ["smooth", "filter_outliers", "molecular_weight", "find_elements", "atom_type", "detect_encoding", "autocode"],
    color: ACCENT,
  },
];

toolCats.forEach((cat, i) => {
  const x = 0.3 + i * 3.2;
  slide.addShape(pptx.shapes.ROUNDED_RECTANGLE, {
    x, y: 2.3, w: 3.0, h: 2.3,
    fill: { color: CARD_BG },
    line: { color: cat.color, width: 1.5 },
    rectRadius: 0.06,
  });
  slide.addShape(pptx.shapes.RECTANGLE, {
    x, y: 2.3, w: 3.0, h: 0.4,
    fill: { color: cat.color },
  });
  slide.addText(cat.title, {
    x, y: 2.3, w: 3.0, h: 0.4,
    fontSize: 13, bold: true, color: TEXT_LIGHT, align: "center", valign: "middle",
  });
  slide.addText(
    cat.tools.map((t, ti) => ({ text: t, options: { breakLine: ti < cat.tools.length - 1, fontFace: "Consolas", fontSize: 10, color: TEXT_DARK } })),
    { x: x + 0.15, y: 2.8, w: 2.7, h: 1.7, valign: "top" }
  );
});

// ==============================================================
// Slide 7: Config-Driven Design
// ==============================================================
slide = pptx.addSlide();
slide.background = { color: DARK_BG };

slide.addText("YAML驱动：零硬编码", {
  x: 0.5, y: 0.3, w: 9, h: 0.7,
  fontSize: 36, bold: true, color: TEXT_LIGHT, fontFace: "Georgia",
  margin: 0,
});

// YAML code block (left)
slide.addShape(pptx.shapes.ROUNDED_RECTANGLE, {
  x: 0.4, y: 1.1, w: 4.8, h: 3.8,
  fill: { color: MIDNIGHT },
  line: { color: TEAL, width: 1 },
  rectRadius: 0.06,
});

const yamlLines = [
  { text: "cutoff:", color: ACCENT },
  { text: "  bonds: [CC, CN, CO, CH...]", color: TEXT_LIGHT },
  { text: "  bocutoff: [0.55, 0.30, 0.65...]", color: TEXT_LIGHT },
  { text: "  blcutoff: [1.8, 2.1, 1.9...]", color: TEXT_LIGHT },
  { text: "", color: TEXT_LIGHT },
  { text: "filerule1:", color: ACCENT },
  { text: "  logfilename: \"log.lammps*\"", color: TEXT_LIGHT },
  { text: "  bondsfilename: \"bonds.reax.bof\"", color: TEXT_LIGHT },
  { text: "", color: TEXT_LIGHT },
  { text: "bonds_limit:", color: ACCENT },
  { text: "  Al: 6; C: 4; H: 1; N: 3; O: 2", color: TEXT_LIGHT },
  { text: "", color: TEXT_LIGHT },
  { text: "timestep: 0.1  # fs", color: MUTED },
  { text: "thermostep: 100", color: MUTED },
];
slide.addText(
  yamlLines.map((l, i) => ({ text: l.text, options: { breakLine: i < yamlLines.length - 1, fontFace: "Consolas", fontSize: 11, color: l.color } })),
  { x: 0.55, y: 1.25, w: 4.5, h: 3.5, valign: "top" }
);

// Key features (right)
const features = [
  { icon: "CFG", title: "30种键类型", desc: "bonds/bocutoff/blcutoff" },
  { icon: "GLOB", title: "Glob批量", desc: "8种文件格式自动匹配" },
  { icon: "LIMIT", title: "键数限制", desc: "Al:6, C:4, H:1, N:3, O:2" },
  { icon: "STEP", title: "时间参数", desc: "timestep/thermostep/supercell" },
];
features.forEach((f, i) => {
  const y = 1.1 + i * 0.9;
  slide.addShape(pptx.shapes.OVAL, {
    x: 5.5, y: y + 0.1, w: 0.55, h: 0.55,
    fill: { color: TEAL },
  });
  slide.addText(f.icon.substring(0, 2), {
    x: 5.5, y: y + 0.15, w: 0.55, h: 0.45,
    fontSize: 12, bold: true, color: TEXT_LIGHT, align: "center", valign: "middle",
  });
  slide.addText(f.title, {
    x: 6.2, y: y, w: 3.3, h: 0.35,
    fontSize: 14, bold: true, color: TEXT_LIGHT,
  });
  slide.addText(f.desc, {
    x: 6.2, y: y + 0.35, w: 3.3, h: 0.3,
    fontSize: 11, color: MUTED,
  });
});

// Pydantic validation note
slide.addShape(pptx.shapes.ROUNDED_RECTANGLE, {
  x: 0.4, y: 5.0, w: 9.2, h: 0.55,
  fill: { color: ACCENT, transparency: 80 },
  line: { color: ACCENT, width: 1 },
  rectRadius: 0.04,
});
slide.addText("Pydantic 模型在加载时验证 YAML — 运行时零错误", {
  x: 0.4, y: 5.0, w: 9.2, h: 0.55,
  fontSize: 13, color: ACCENT, align: "center", valign: "middle",
});

// ==============================================================
// Slide 8: Glob Batch Matching
// ==============================================================
slide = pptx.addSlide();
slide.background = { color: LIGHT_BG };

slide.addText("Glob 批量处理：一次解析多个文件", {
  x: 0.5, y: 0.3, w: 9, h: 0.7,
  fontSize: 36, bold: true, color: TEXT_DARK, fontFace: "Georgia",
  margin: 0,
});

// Input folder
slide.addShape(pptx.shapes.ROUNDED_RECTANGLE, {
  x: 0.4, y: 1.2, w: 3.5, h: 2.8,
  fill: { color: CARD_BG },
  line: { color: MUTED, width: 1, dashType: "dash" },
  rectRadius: 0.06,
});
slide.addText("📁 input/", {
  x: 0.4, y: 1.25, w: 3.5, h: 0.4,
  fontSize: 14, bold: true, color: TEXT_DARK, align: "center",
});
const inputFiles = [
  "log.lammps.0", "log.lammps.1", "log.lammps.2",
  "bonds.reax.0", "bonds.reax.1",
  "dump.0.trj", "dump.1.trj",
];
inputFiles.forEach((f, i) => {
  slide.addText("📄 " + f, {
    x: 0.5, y: 1.7 + i * 0.3, w: 3.3, h: 0.28,
    fontSize: 10, color: TEXT_DARK, fontFace: "Consolas",
  });
});

// Arrow
slide.addText("glob →", {
  x: 4.0, y: 2.3, w: 1.0, h: 0.5,
  fontSize: 18, bold: true, color: DEEP_BLUE, align: "center",
});

// Output
slide.addShape(pptx.shapes.ROUNDED_RECTANGLE, {
  x: 5.2, y: 1.2, w: 4.4, h: 2.8,
  fill: { color: CARD_BG },
  line: { color: TEAL, width: 1.5 },
  rectRadius: 0.06,
});
slide.addText("Output", {
  x: 5.2, y: 1.25, w: 4.4, h: 0.4,
  fontSize: 14, bold: true, color: TEAL, align: "center",
});

const outputFiles = [
  { f: "dataoflog.csv", note: "(split0)" },
  { f: "dataoflog.split0.csv", note: "" },
  { f: "dataoflog.split1.csv", note: "" },
  { f: "dataoflog.split2.csv", note: "" },
  { f: "bonds.csv", note: "" },
  { f: "dump.csv", note: "" },
];
outputFiles.forEach((o, i) => {
  slide.addShape(pptx.shapes.ROUNDED_RECTANGLE, {
    x: 5.35, y: 1.72 + i * 0.35, w: 4.1, h: 0.3,
    fill: { color: TEAL, transparency: 85 },
    rectRadius: 0.03,
  });
  slide.addText("📊 " + o.f + (o.note ? " " + o.note : ""), {
    x: 5.4, y: 1.72 + i * 0.35, w: 4.0, h: 0.3,
    fontSize: 10, color: TEXT_DARK, fontFace: "Consolas", valign: "middle",
  });
});

// Key benefit
slide.addShape(pptx.shapes.ROUNDED_RECTANGLE, {
  x: 1.5, y: 4.2, w: 7, h: 1.3,
  fill: { color: DEEP_BLUE },
  rectRadius: 0.08,
});
slide.addText("核心优势", {
  x: 1.7, y: 4.3, w: 2, h: 0.35,
  fontSize: 14, bold: true, color: ACCENT,
});
slide.addText([
  { text: "✓ ", options: { color: "4CAF50" } },
  { text: "自动检测文件数量     ", options: { color: TEXT_LIGHT } },
  { text: "✓ ", options: { color: "4CAF50" } },
  { text: "自动编号命名     ", options: { color: TEXT_LIGHT } },
  { text: "✓ ", options: { color: "4CAF50" } },
  { text: "零配置批量处理", options: { color: TEXT_LIGHT } },
], {
  x: 1.7, y: 4.7, w: 6.5, h: 0.7, fontSize: 14,
});

// ==============================================================
// Slide 9: Reproducibility - JSONL Logger
// ==============================================================
slide = pptx.addSlide();
slide.background = { color: DARK_BG };

slide.addText("JSONL 执行日志：完整可追溯", {
  x: 0.5, y: 0.3, w: 9, h: 0.7,
  fontSize: 36, bold: true, color: TEXT_LIGHT, fontFace: "Georgia",
  margin: 0,
});

// JSONL code block
slide.addShape(pptx.shapes.ROUNDED_RECTANGLE, {
  x: 0.4, y: 1.05, w: 9.2, h: 2.8,
  fill: { color: MIDNIGHT },
  line: { color: TEAL, width: 1 },
  rectRadius: 0.06,
});

const jsonLines = [
  { text: "{", color: TEXT_LIGHT },
  { text: '  "log_id": "a1b2c3d4",', color: "4ECDC4" },
  { text: '  "timestamp": "2026-05-28T10:00:00",', color: MUTED },
  { text: '  "session_id": "x9y8z7",', color: MUTED },
  { text: '  "tool": "arrange",', color: ACCENT },
  { text: '  "input": {"modes": ["Log","Bonds"], "path": "./data"},', color: TEXT_LIGHT },
  { text: '  "execution_steps": ["arrange: modes=[Log,Bonds]..."],', color: TEXT_LIGHT },
  { text: '  "output_summary": {"shape": [100,20], "files": 3},', color: TEXT_LIGHT },
  { text: '  "status": "success",', color: "4CAF50" },
  { text: '  "elapsed_ms": 234', color: MUTED },
  { text: "}", color: TEXT_LIGHT },
];
slide.addText(
  jsonLines.map((l, i) => ({ text: l.text, options: { breakLine: i < jsonLines.length - 1, fontFace: "Consolas", fontSize: 11, color: l.color } })),
  { x: 0.6, y: 1.2, w: 8.8, h: 2.5, valign: "top" }
);

// Key features row
const reproFeatures = [
  { icon: "ID", title: "log_id", desc: "全局唯一追溯码" },
  { icon: "TS", title: "timestamp", desc: "精确到毫秒" },
  { icon: "SID", title: "session_id", desc: "会话级追踪" },
  { icon: "SUM", title: "summary", desc: "DataFrame概要（非序列化，防日志膨胀）" },
];
reproFeatures.forEach((f, i) => {
  const x = 0.4 + i * 2.4;
  slide.addShape(pptx.shapes.ROUNDED_RECTANGLE, {
    x, y: 4.0, w: 2.25, h: 1.5,
    fill: { color: TEAL, transparency: 70 },
    line: { color: TEAL, width: 1 },
    rectRadius: 0.06,
  });
  slide.addShape(pptx.shapes.OVAL, {
    x: x + 0.75, y: 4.1, w: 0.75, h: 0.75,
    fill: { color: TEAL },
  });
  slide.addText(f.icon, {
    x: x + 0.75, y: 4.2, w: 0.75, h: 0.55,
    fontSize: 12, bold: true, color: TEXT_LIGHT, align: "center", valign: "middle",
  });
  slide.addText(f.title, {
    x, y: 4.9, w: 2.25, h: 0.25,
    fontSize: 13, bold: true, color: TEXT_LIGHT, align: "center",
  });
  slide.addText(f.desc, {
    x: x + 0.1, y: 5.15, w: 2.05, h: 0.3,
    fontSize: 10, color: MUTED, align: "center",
  });
});

// ==============================================================
// Slide 10: CLI + Python API
// ==============================================================
slide = pptx.addSlide();
slide.background = { color: LIGHT_BG };

slide.addText("简洁易用：CLI + Python API", {
  x: 0.5, y: 0.3, w: 9, h: 0.7,
  fontSize: 36, bold: true, color: TEXT_DARK, fontFace: "Georgia",
  margin: 0,
});

// CLI column
slide.addShape(pptx.shapes.ROUNDED_RECTANGLE, {
  x: 0.4, y: 1.1, w: 4.5, h: 3.5,
  fill: { color: DARK_BG },
  line: { color: DEEP_BLUE, width: 1 },
  rectRadius: 0.06,
});
slide.addText("CLI", {
  x: 0.4, y: 1.15, w: 4.5, h: 0.45,
  fontSize: 16, bold: true, color: ACCENT, align: "center",
});
const cliLines = [
  { text: "# 查看配置", color: MUTED },
  { text: "lmpsmart config --show", color: "98FB98" },
  { text: "", color: TEXT_LIGHT },
  { text: "# 解析LAMMPS文件", color: MUTED },
  { text: "lmpsmart arrange \ \n  --path ./data \ \n  --modes Log,Bonds,Dump", color: "98FB98" },
  { text: "", color: TEXT_LIGHT },
  { text: "# Agent模式", color: MUTED },
  { text: "lmpsmart agent --goal \n  \"arrange log files and \n   smooth temperature\"", color: "98FB98" },
];
slide.addText(
  cliLines.map((l, i) => ({ text: l.text, options: { breakLine: i < cliLines.length - 1, fontFace: "Consolas", fontSize: 11, color: l.color } })),
  { x: 0.55, y: 1.6, w: 4.2, h: 2.9, valign: "top" }
);

// Python API column
slide.addShape(pptx.shapes.ROUNDED_RECTANGLE, {
  x: 5.1, y: 1.1, w: 4.5, h: 3.5,
  fill: { color: DARK_BG },
  line: { color: TEAL, width: 1 },
  rectRadius: 0.06,
});
slide.addText("Python API", {
  x: 5.1, y: 1.15, w: 4.5, h: 0.45,
  fontSize: 16, bold: true, color: ACCENT, align: "center",
});
const pyLines = [
  { text: "from lmpsmart import (\n  arrange, smooth,\n  filter_outliers\n)", color: "98FB98" },
  { text: "", color: TEXT_LIGHT },
  { text: "# 解析 + 平滑 + 过滤", color: MUTED },
  { text: "df = arrange(\"data/\",\n  modes=[\"Log\",\"Bonds\"])", color: "98FB98" },
  { text: "", color: TEXT_LIGHT },
  { text: "smoothed = smooth(\n  df[\"temperature\"],\n  method=\"savgol\")", color: "98FB98" },
];
slide.addText(
  pyLines.map((l, i) => ({ text: l.text, options: { breakLine: i < pyLines.length - 1, fontFace: "Consolas", fontSize: 11, color: l.color } })),
  { x: 5.25, y: 1.6, w: 4.2, h: 2.9, valign: "top" }
);

// Subcommand badges
const subcmds = ["arrange", "smooth", "filter", "config", "llm", "agent"];
subcmds.forEach((s, i) => {
  slide.addShape(pptx.shapes.ROUNDED_RECTANGLE, {
    x: 0.4 + i * 1.55, y: 4.75, w: 1.4, h: 0.55,
    fill: { color: i % 2 === 0 ? DEEP_BLUE : TEAL },
    rectRadius: 0.06,
  });
  slide.addText(s, {
    x: 0.4 + i * 1.55, y: 4.75, w: 1.4, h: 0.55,
    fontSize: 13, bold: true, color: TEXT_LIGHT, align: "center", valign: "middle",
  });
});
slide.addText("6个子命令  ·  --help 查看详情  ·  --version 显示版本", {
  x: 0.4, y: 5.35, w: 9.2, h: 0.25,
  fontSize: 11, color: MUTED, align: "center",
});

// ==============================================================
// Slide 11: lmpsmart vs Other LAMMPS Tools
// ==============================================================
slide = pptx.addSlide();
slide.background = { color: LIGHT_BG };

slide.addText("lmpsmart vs 主流 LAMMPS 数据处理工具", {
  x: 0.5, y: 0.3, w: 9, h: 0.7,
  fontSize: 34, bold: true, color: TEXT_DARK, fontFace: "Georgia",
  margin: 0,
});

// Tool badges at top
const tools = [
  { name: "OVITO", desc: "可视化+分析 · GUI主导", color: "E07A5F" },
  { name: "mdapy", desc: "快速Python分析 · C++加速", color: "3D405B" },
  { name: "MDAnalysis", desc: "轨迹分析 · 学术最流行", color: "5F9EA0" },
  { name: "lmpsmart", desc: "Agent架构 · 全链路可追溯", color: DEEP_BLUE },
];
tools.forEach((t, i) => {
  slide.addShape(pptx.shapes.ROUNDED_RECTANGLE, {
    x: 0.3 + i * 2.45, y: 1.0, w: 2.3, h: 0.5,
    fill: { color: t.color },
    rectRadius: 0.05,
  });
  slide.addText(t.name, {
    x: 0.3 + i * 2.45, y: 1.0, w: 2.3, h: 0.3,
    fontSize: 13, bold: true, color: TEXT_LIGHT, align: "center", valign: "middle",
  });
  slide.addText(t.desc, {
    x: 0.3 + i * 2.45, y: 1.28, w: 2.3, h: 0.22,
    fontSize: 8, color: TEXT_LIGHT, align: "center",
  });
});

// Comparison table
const comps = [
  {
    dim: "派生物理量计算\n（RDF/RMSD/CED等）",
    vals: ["OVITO ✓✓", "mdapy ✓", "MDAnalysis ✓", "lmpsmart ✓内置+可扩展"],
    color: ["E07A5F", "3D405B", "5F9EA0", DEEP_BLUE],
  },
  {
    dim: "数据标准化·原创输出\n（Bonds阈值/Cell/Atom/mweight等）",
    vals: ["OVITO ✗", "mdapy ✗", "MDAnalysis ✗", "lmpsmart ✓"],
    color: ["E07A5F", "3D405B", "5F9EA0", DEEP_BLUE],
  },
  {
    dim: "自定义指标扩展",
    vals: ["OVITO ~(Pro)", "mdapy ~", "MDAnalysis ~", "lmpsmart ✓"],
    color: ["778DA9", "778DA9", "778DA9", DEEP_BLUE],
  },
  {
    dim: "数据降噪+曲线拟合\n（9平滑+polyfit.n/lowess等）",
    vals: ["OVITO ✗", "mdapy ✗", "MDAnalysis ✗", "lmpsmart ✓"],
    color: ["E07A5F", "3D405B", "5F9EA0", DEEP_BLUE],
  },
  {
    dim: "统计异常值过滤\n（zscore/MAD/IQR）",
    vals: ["OVITO ✗", "mdapy ✗", "MDAnalysis ✗", "lmpsmart ✓"],
    color: ["E07A5F", "3D405B", "5F9EA0", DEEP_BLUE],
  },
  {
    dim: "专业曲线绘图（出版级）",
    vals: ["OVITO ✗(仅3D模型)", "mdapy ~", "MDAnalysis ~", "lmpsmart ✓"],
    color: ["E07A5F", "778DA9", "778DA9", DEEP_BLUE],
  },
  {
    dim: "自然语言命令",
    vals: ["OVITO ✗", "mdapy ✗", "MDAnalysis ✗", "lmpsmart ✓"],
    color: ["E07A5F", "3D405B", "5F9EA0", DEEP_BLUE],
  },
  {
    dim: "Agent 规划",
    vals: ["OVITO ✗", "mdapy ✗", "MDAnalysis ✗", "lmpsmart ✓"],
    color: ["E07A5F", "3D405B", "5F9EA0", DEEP_BLUE],
  },
  {
    dim: "JSONL 执行日志",
    vals: ["OVITO ✗", "mdapy ✗", "MDAnalysis ✗", "lmpsmart ✓"],
    color: ["E07A5F", "3D405B", "5F9EA0", DEEP_BLUE],
  },
  {
    dim: "批量 Glob 匹配",
    vals: ["OVITO ✗", "mdapy ~", "MDAnalysis ✗", "lmpsmart ✓"],
    color: ["E07A5F", "778DA9", "E07A5F", DEEP_BLUE],
  },
];

// Table header
slide.addShape(pptx.shapes.RECTANGLE, {
  x: 0.3, y: 1.65, w: 9.4, h: 0.45,
  fill: { color: DEEP_BLUE },
});
slide.addText("对比维度", { x: 0.3, y: 1.65, w: 2.2, h: 0.45, fontSize: 12, bold: true, color: TEXT_LIGHT, align: "center", valign: "middle" });
slide.addText("OVITO", { x: 2.5, y: 1.65, w: 1.8, h: 0.45, fontSize: 12, bold: true, color: "E07A5F", align: "center", valign: "middle" });
slide.addText("mdapy", { x: 4.3, y: 1.65, w: 1.8, h: 0.45, fontSize: 12, bold: true, color: "3D405B", align: "center", valign: "middle" });
slide.addText("MDAnalysis", { x: 6.1, y: 1.65, w: 1.8, h: 0.45, fontSize: 12, bold: true, color: "5F9EA0", align: "center", valign: "middle" });
slide.addText("lmpsmart", { x: 7.9, y: 1.65, w: 1.8, h: 0.45, fontSize: 12, bold: true, color: ACCENT, align: "center", valign: "middle" });

const rowH = 0.33;
comps.forEach((c, i) => {
  const y = 2.15 + i * rowH;
  const rowBg = i % 2 === 0 ? CARD_BG : LIGHT_BG;
  slide.addShape(pptx.shapes.RECTANGLE, { x: 0.3, y, w: 9.4, h: rowH, fill: { color: rowBg } });
  slide.addText(c.dim, { x: 0.35, y, w: 2.1, h: rowH, fontSize: 9, bold: true, color: TEXT_DARK, valign: "middle" });
  slide.addText(c.vals[0], { x: 2.5, y, w: 1.8, h: rowH, fontSize: 9, color: c.color[0], align: "center", valign: "middle" });
  slide.addText(c.vals[1], { x: 4.3, y, w: 1.8, h: rowH, fontSize: 9, color: c.color[1], align: "center", valign: "middle" });
  slide.addText(c.vals[2], { x: 6.1, y, w: 1.8, h: rowH, fontSize: 9, color: c.color[2], align: "center", valign: "middle" });
  slide.addText(c.vals[3], { x: 7.9, y, w: 1.8, h: rowH, fontSize: 9, color: c.color[3], bold: true, align: "center", valign: "middle" });
});

// Bottom insight
slide.addShape(pptx.shapes.ROUNDED_RECTANGLE, {
  x: 0.3, y: 5.5, w: 9.4, h: 0.55,
  fill: { color: DEEP_BLUE },
  rectRadius: 0.06,
});
slide.addText([
  { text: "lmpsmart = 数据标准化（8大原创输出） + 降噪+拟合（9平滑+polyfit.n/lowess等） + 过滤（3种） + Agent + JSONL日志", options: { color: TEXT_LIGHT, fontSize: 10 } },
  { text: "  |  OVITO/mdapy/MDAnalysis 专注派生物理量（RDF/MSD），lmpsmart 定位为互补前置清洗层", options: { color: "778DA9", fontSize: 9 } },
], {
  x: 0.4, y: 5.5, w: 9.2, h: 0.55,
  align: "center", valign: "middle",
});

// ==============================================================
// Slide 12: Conclusion
// ==============================================================
slide = pptx.addSlide();
slide.background = { color: DARK_BG };

slide.addText("总结与展望", {
  x: 0.5, y: 0.3, w: 9, h: 0.7,
  fontSize: 36, bold: true, color: TEXT_LIGHT, fontFace: "Georgia",
  margin: 0,
});

// Three achievement stats
const stats = [
  { num: "8", unit: "Parsers", label: "文件格式支持" },
  { num: "9+3", unit: "Algorithms", label: "平滑 + 过滤" },
  { num: "0", unit: "Hardcoding", label: "YAML驱动" },
];
stats.forEach((s, i) => {
  const x = 0.5 + i * 3.15;
  slide.addShape(pptx.shapes.ROUNDED_RECTANGLE, {
    x, y: 1.1, w: 2.95, h: 1.3,
    fill: { color: DEEP_BLUE },
    rectRadius: 0.08,
  });
  slide.addText(s.num, {
    x, y: 1.15, w: 2.95, h: 0.65,
    fontSize: 36, bold: true, color: ACCENT, align: "center", valign: "middle",
  });
  slide.addText(s.unit, {
    x, y: 1.75, w: 2.95, h: 0.3,
    fontSize: 12, bold: true, color: TEXT_LIGHT, align: "center",
  });
  slide.addText(s.label, {
    x, y: 2.05, w: 2.95, h: 0.3,
    fontSize: 10, color: MUTED, align: "center",
  });
});

// Future work
slide.addText("Future Work", {
  x: 0.5, y: 2.6, w: 9, h: 0.45,
  fontSize: 18, bold: true, color: ACCENT,
});
const futures = [
  { icon: "🤖", text: "LLM 推理替换关键词匹配（GPT-4o / Qwen3）" },
  { icon: "🌐", text: "REST API + React Web UI（无CLI用户友好）" },
  { icon: "☁️", text: "Docker 容器化（ HPC 集群一键部署）" },
  { icon: "📊", text: "自动化统计验证（平滑 vs 原始数据假设检验）" },
];
futures.forEach((f, i) => {
  const x = (i % 2) * 4.5 + 0.5;
  const y = 3.1 + Math.floor(i / 2) * 0.55;
  slide.addText(f.icon + "  " + f.text, {
    x, y, w: 4.3, h: 0.5,
    fontSize: 12, color: TEXT_LIGHT, valign: "middle",
  });
});

// Bottom info
slide.addShape(pptx.shapes.RECTANGLE, {
  x: 0, y: 4.6, w: 10, h: 1.0,
  fill: { color: MIDNIGHT },
});
slide.addText("github.com/qgan2025/lmpsmart  ·  GPL-3.0  ·  Copyright (c) 2025 Qiang Gan", {
  x: 0, y: 4.7, w: 10, h: 0.4,
  fontSize: 14, color: TEXT_LIGHT, align: "center",
});
slide.addText("LAMMPS Molecular Dynamics Data Processing Agent  ·  v1.0.0", {
  x: 0, y: 5.1, w: 10, h: 0.3,
  fontSize: 11, color: MUTED, align: "center",
});

// Save
const outPath = "D:/MyObsidian/Projects/lmpsmart/docs/lmpsmart_competition.pptx";
pptx.writeFile({ fileName: outPath })
  .then(() => console.log("Saved: " + outPath))
  .catch(err => { console.error("Error:", err); process.exit(1); });
