const pptxgen = require("pptxgenjs");
const fs = require("fs");

const pptx = new pptxgen();
pptx.layout = "LAYOUT_16x9";
pptx.author = "Qiang Gan";
pptx.title = "LMPSmart v1.0.0 - LAMMPS MD Smart Data Processing Agent";
pptx.subject = "Agent Competition Submission";

// SmartOffice Academic Theme (Theme 5-Key Contract)
const C = {
  navy: "1A365D",
  lightNavy: "2C5282",
  teal: "319795",
  accent: "00B4D8",
  cream: "FDFBF7",
  warmWhite: "FEFCF9",
  lightBg: "F0F4F8",
  cardBg: "FFFFFF",
  darkText: "1A202C",
  grayText: "4A5568",
  lightGray: "E2E8F0",
  gold: "B7791F",
  orange: "DD6B20",
  purple: "6B46C1",
  pink: "B83280",
};

const fn = {
  title: "Georgia",
  cn: "Microsoft YaHei",
  mono: "Consolas",
  sans: "Arial",
};

// Slide factory: cream background + navy title bar + gold accent line
function addTitleBar(slide, titleText) {
  slide.background = { color: C.cream };
  slide.addShape(pptx.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.7, fill: { color: C.navy } });
  slide.addShape(pptx.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.06, fill: { color: C.gold } });
  slide.addText(titleText, {
    x: 0.5, y: 0.1, w: 9, h: 0.55, fontSize: 26, fontFace: fn.title, color: C.warmWhite, bold: true, margin: 0,
  });
}

function card(slide, x, y, w, h, opts) {
  opts = opts || {};
  slide.addShape(pptx.shapes.RECTANGLE, {
    x, y, w, h, fill: { color: opts.fill || C.cardBg }, line: { color: opts.line || C.lightGray, width: opts.lineWidth || 1 },
  });
}

function pill(slide, x, y, w, h, color, text, fontSize) {
  slide.addShape(pptx.shapes.ROUNDED_RECTANGLE, { x, y, w, h, fill: { color: color }, rectRadius: 0.05 });
  slide.addText(text, { x, y, w, h, fontSize: fontSize || 12, fontFace: fn.cn, color: C.warmWhite, bold: true, align: "center", valign: "middle" });
}

// ==============================================================
// Slide 1: Title
// ==============================================================
let slide = pptx.addSlide();
slide.background = { color: C.navy };
slide.addShape(pptx.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.08, fill: { color: C.gold } });

slide.addText("LMPSmart", {
  x: 0.5, y: 1.5, w: 9, h: 1.1, fontSize: 72, bold: true, color: C.accent, fontFace: fn.title, align: "center",
});
slide.addShape(pptx.shapes.RECTANGLE, { x: 3.5, y: 2.7, w: 3, h: 0.05, fill: { color: C.gold } });
slide.addText("LAMMPS Molecular Dynamics Smart Data Processing Agent", {
  x: 0.5, y: 2.85, w: 9, h: 0.55, fontSize: 22, color: C.warmWhite, fontFace: fn.cn, align: "center",
});
slide.addText("Agent 架构 · 标准化输出 · 全链路可追溯", {
  x: 0.5, y: 3.45, w: 9, h: 0.4, fontSize: 16, color: "A0AEC0", fontFace: fn.cn, align: "center",
});
const badges = [
  { text: "v1.0.0", x: 3.2 },
  { text: "GPL-3.0", x: 4.2 },
  { text: "Qiang Gan", x: 5.3 },
];
badges.forEach((b) => {
  slide.addShape(pptx.shapes.ROUNDED_RECTANGLE, { x: b.x, y: 4.1, w: 1.5, h: 0.4, fill: { color: C.lightNavy }, rectRadius: 0.05 });
  slide.addText(b.text, { x: b.x, y: 4.1, w: 1.5, h: 0.4, fontSize: 11, fontFace: fn.sans, color: C.warmWhite, align: "center", valign: "middle" });
});

// ==============================================================
// Slide 1.5: Molecular Dynamics Method
// ==============================================================
slide = pptx.addSlide();
addTitleBar(slide, "一、分子动力学方法");

// Left card
card(slide, 0.4, 0.85, 4.4, 2.35, { fill: C.cardBg, line: C.navy, lineWidth: 2 });
slide.addText("什么是分子动力学？", { x: 0.5, y: 0.9, w: 4.2, h: 0.38, fontSize: 15, fontFace: fn.cn, color: C.gold, bold: true, margin: 0 });
const mdDefs = [
  "依据牛顿运动定律模拟分子体系运动",
  "获得体系在相空间的时间演化轨迹",
  "抽取样本，计算宏观热力学和力学性质",
  "力场精度直接影响模拟结果质量",
];
mdDefs.forEach((d, i) => {
  slide.addText("▸ " + d, { x: 0.6, y: 1.35 + i * 0.44, w: 4.0, h: 0.4, fontSize: 12, fontFace: fn.cn, color: C.darkText, margin: 0 });
});

// Right card
card(slide, 5.1, 0.85, 4.5, 2.35, { fill: C.cardBg, line: C.teal, lineWidth: 2 });
slide.addText("材料性质研究应用", { x: 5.2, y: 0.9, w: 4.3, h: 0.38, fontSize: 15, fontFace: fn.cn, color: C.teal, bold: true, margin: 0 });
const mdApps = [
  "晶体形貌预测 & 力学性能分析",
  "冲击响应：撞击损伤、热点演化",
  "热分解：脱硝基反应机理",
  "相变研究：γ→ξ 等晶型转变",
];
mdApps.forEach((a, i) => {
  slide.addText("▸ " + a, { x: 5.3, y: 1.35 + i * 0.44, w: 4.1, h: 0.4, fontSize: 12, fontFace: fn.cn, color: C.darkText, margin: 0 });
});

// Bottom scale section
card(slide, 0.4, 3.35, 9.2, 2.1, { fill: C.navy });
slide.addText("分子动力学模拟尺度", { x: 0.6, y: 3.4, w: 8.8, h: 0.38, fontSize: 14, fontFace: fn.cn, color: C.gold, bold: true, margin: 0 });
const scales = [
  { label: "空间范围", value: "1nm ~ 100nm" },
  { label: "时间范围", value: "1ps ~ 10ns" },
  { label: "典型规模", value: "百万原子并行计算" },
  { label: "势函数", value: "ReaxFF-lg（反应力场，含能材料专用）" },
];
scales.forEach((s, i) => {
  const col = i % 2;
  const row = Math.floor(i / 2);
  slide.addText(s.label + "：" + s.value, { x: 0.6 + col * 4.5, y: 3.88 + row * 0.42, w: 4.3, h: 0.38, fontSize: 12, fontFace: fn.cn, color: C.warmWhite, margin: 0 });
});
slide.addText("应用领域：含能材料 · 金属材料 · 高分子聚合物 · 纳米材料", {
  x: 0.6, y: 5.02, w: 8.8, h: 0.28, fontSize: 10, fontFace: fn.cn, color: C.accent, margin: 0,
});

// ==============================================================
// Slide 1.6: LAMMPS Challenges
// ==============================================================
slide = pptx.addSlide();
addTitleBar(slide, "二、LAMMPS：强大但数据处理面临挑战");

// Left: pros
card(slide, 0.4, 0.85, 4.4, 2.2, { fill: C.cardBg, line: C.navy, lineWidth: 1.5 });
slide.addShape(pptx.shapes.RECTANGLE, { x: 0.4, y: 0.85, w: 4.4, h: 0.4, fill: { color: C.navy } });
slide.addText("LAMMPS 核心特点", { x: 0.5, y: 0.9, w: 4.2, h: 0.35, fontSize: 14, fontFace: fn.cn, color: C.warmWhite, bold: true, margin: 0 });
const lmpPros = ["✓ 开源免费，代码可自行修改", "✓ 支持百万原子级并行计算", "✓ 支持 ReaxFF 反应力场", "✓ 含能材料领域广泛验证"];
lmpPros.forEach((p, i) => {
  slide.addText(p, { x: 0.6, y: 1.35 + i * 0.42, w: 4.0, h: 0.38, fontSize: 12, fontFace: fn.cn, color: C.darkText, margin: 0 });
});

// Right: cons
card(slide, 5.1, 0.85, 4.5, 2.2, { fill: C.cardBg, line: "E07A5F", lineWidth: 1.5 });
slide.addShape(pptx.shapes.RECTANGLE, { x: 5.1, y: 0.85, w: 4.5, h: 0.4, fill: { color: "C05621" } });
slide.addText("LAMMPS 自身局限", { x: 5.2, y: 0.9, w: 4.3, h: 0.35, fontSize: 14, fontFace: fn.cn, color: C.warmWhite, bold: true, margin: 0 });
const lmpCons = ["✗ 无图形用户界面（GUI）", "✗ 无分子建模工具", "✗ 无复杂数据分析/可视化", "✗ 数据输出为非标准格式"];
lmpCons.forEach((c, i) => {
  slide.addText(c, { x: 5.3, y: 1.35 + i * 0.42, w: 4.1, h: 0.38, fontSize: 12, fontFace: fn.cn, color: C.darkText, margin: 0 });
});

// File format section
slide.addText("LAMMPS 输出典型文件格式", { x: 0.4, y: 3.2, w: 9.2, h: 0.38, fontSize: 16, fontFace: fn.cn, color: C.navy, bold: true, margin: 0 });
const formats = [
  { name: "log", desc: "热力学数据\n温度/压力/能量\n晶胞参数", color: C.navy },
  { name: "dump", desc: "原子轨迹\nxyz坐标/速度\n数千帧", color: C.teal },
  { name: "bonds", desc: "键级分析\n30种键类型\nReaxFF专用", color: C.accent },
  { name: "species", desc: "物种计数\n键级阈值依赖\n动态变化", color: C.lightNavy },
  { name: "pos", desc: "晶胞结构\n晶格常数\n体积密度", color: "F4A261" },
];
formats.forEach((f, i) => {
  const x = 0.4 + i * 1.88;
  card(slide, x, 3.65, 1.78, 1.55, { fill: C.cardBg, line: f.color, lineWidth: 1.5 });
  slide.addShape(pptx.shapes.RECTANGLE, { x, y: 3.65, w: 1.78, h: 0.38, fill: { color: f.color } });
  slide.addText(f.name.toUpperCase(), { x, y: 3.68, w: 1.78, h: 0.35, fontSize: 13, fontFace: fn.mono, color: C.warmWhite, bold: true, align: "center", margin: 0 });
  slide.addText(f.desc, { x: x + 0.05, y: 4.08, w: 1.68, h: 1.08, fontSize: 10, fontFace: fn.cn, color: C.darkText, align: "center" });
});

// ==============================================================
// Slide 2: Why lmpsmart?
// ==============================================================
slide = pptx.addSlide();
addTitleBar(slide, "三、为什么需要 lmpsmart？");

const problems = [
  { title: "海量异构数据", desc: "LAMMPS + ReaxFF 产生热力学、键拓扑、化学物种等多类型数据", icon: "数据" },
  { title: "传统方案局限", desc: "OVITO/VMD擅长可视化，但无法处理数据标准化、降噪和过滤", icon: "工具" },
  { title: "无可追溯性", desc: "手动操作无法复现，实验记录依赖人工备注", icon: "追溯" },
];
problems.forEach((p, i) => {
  const x = 0.4 + i * 3.1;
  card(slide, x, 0.85, 2.9, 2.55, { fill: C.cardBg, line: C.lightNavy });
  slide.addShape(pptx.shapes.RECTANGLE, { x, y: 0.85, w: 2.9, h: 0.08, fill: { color: C.lightNavy } });
  slide.addShape(pptx.shapes.OVAL, { x: x + 1.0, y: 1.0, w: 0.9, h: 0.9, fill: { color: C.navy } });
  slide.addText(p.icon, { x: x + 1.0, y: 1.08, w: 0.9, h: 0.75, fontSize: 11, fontFace: fn.cn, color: C.warmWhite, bold: true, align: "center", valign: "middle" });
  slide.addText(p.title, { x: x + 0.15, y: 2.0, w: 2.6, h: 0.4, fontSize: 15, fontFace: fn.cn, color: C.navy, bold: true, align: "center", margin: 0 });
  slide.addText(p.desc, { x: x + 0.15, y: 2.42, w: 2.6, h: 0.9, fontSize: 11, fontFace: fn.cn, color: C.grayText, align: "center" });
});

// Solution box
card(slide, 1.2, 3.55, 7.6, 1.65, { fill: C.navy });
slide.addText("lmpsmart 解决方案", { x: 1.4, y: 3.6, w: 7.2, h: 0.38, fontSize: 14, fontFace: fn.cn, color: C.gold, bold: true, margin: 0 });
const solutions = [
  ["8大原创标准化输出", "YAML零硬编码"],
  ["9种平滑 + 曲线拟合", "Glob批量处理"],
  ["Agent自然语言接口", "JSONL完整追溯"],
];
solutions.forEach((row, ri) => {
  row.forEach((s, ci) => {
    const x = 1.4 + ci * 3.8;
    const y = 4.05 + ri * 0.38;
    slide.addShape(pptx.shapes.RECTANGLE, { x, y: y + 0.04, w: 0.08, h: 0.26, fill: { color: C.gold } });
    slide.addText(s, { x: x + 0.15, y, w: 3.5, h: 0.34, fontSize: 12, fontFace: fn.cn, color: C.warmWhite, margin: 0 });
  });
});

// ==============================================================
// Slide 3: Architecture
// ==============================================================
slide = pptx.addSlide();
addTitleBar(slide, "四、三层架构设计");

const layers = [
  { label: "INPUT", sub: "LAMMPS files (Log, Bonds, Dump...)", color: C.navy },
  { label: "ARRANGE LAYER", sub: "8 parsers + glob batch + YAML config", color: C.lightNavy },
  { label: "DataFrame", sub: "pandas DataFrame intermediate", color: C.teal },
  { label: "MAPPING LAYER", sub: "9 smoothers + 3 outlier filters", color: C.lightNavy },
  { label: "OUTPUT", sub: "CSV, JSON, figures", color: C.navy },
];
layers.forEach((l, i) => {
  const isBox = !l.label.includes("INPUT") && !l.label.includes("OUTPUT");
  slide.addShape(pptx.shapes.RECTANGLE, { x: 0.4, y: 0.85 + i * 0.75, w: 6.0, h: 0.65, fill: { color: l.color }, line: isBox ? {} : {} });
  slide.addText(l.label, { x: 0.5, y: 0.87 + i * 0.75, w: 2.2, h: 0.6, fontSize: 13, fontFace: fn.sans, color: C.warmWhite, bold: true, valign: "middle", margin: 0 });
  slide.addText(l.sub, { x: 2.7, y: 0.87 + i * 0.75, w: 3.6, h: 0.6, fontSize: 12, fontFace: fn.cn, color: C.warmWhite, valign: "middle", margin: 0 });
  if (i < layers.length - 1) slide.addText("▼", { x: 3.0, y: 0.85 + i * 0.75 + 0.6, w: 0.5, h: 0.2, fontSize: 10, color: C.grayText, align: "center" });
});

// Agent controller on right
card(slide, 6.7, 0.85, 2.9, 2.65, { fill: C.navy, line: C.accent, lineWidth: 2 });
slide.addText("AGENT CONTROLLER", { x: 6.7, y: 0.9, w: 2.9, h: 0.38, fontSize: 12, fontFace: fn.sans, color: C.accent, bold: true, align: "center", margin: 0 });
slide.addText("plan_from_goal()\n       ↓\nexecute()\n       ↓\nJSONL Logger", { x: 6.8, y: 1.35, w: 2.7, h: 1.1, fontSize: 11, fontFace: fn.mono, color: C.warmWhite, align: "center" });
slide.addShape(pptx.shapes.LINE, { x: 6.7, y: 2.1, w: -0.6, h: 0, line: { color: C.accent, width: 1, dashType: "dash" } });

// Key numbers
const archStats = [
  { num: "8", label: "文件解析器" },
  { num: "9+3", label: "平滑+过滤" },
  { num: "18", label: "Agent工具" },
];
archStats.forEach((s, i) => {
  const x = 0.4 + i * 3.1;
  card(slide, x, 4.7, 2.9, 0.8, { fill: C.navy });
  slide.addText(s.num, { x, y: 4.72, w: 2.9, h: 0.45, fontSize: 28, fontFace: fn.title, color: C.accent, bold: true, align: "center", margin: 0 });
  slide.addText(s.label, { x, y: 5.15, w: 2.9, h: 0.3, fontSize: 12, fontFace: fn.cn, color: C.warmWhite, align: "center", margin: 0 });
});

// ==============================================================
// Slide 4: Arrange Layer
// ==============================================================
slide = pptx.addSlide();
addTitleBar(slide, "五、Arrange Layer：8种文件格式解析");

const parsers = [
  { name: "Log", desc: "热力学输出\n温度、压力、能量", color: C.navy },
  { name: "Bonds", desc: "键序分析 (ReaxFF)\n30种键类型", color: C.teal },
  { name: "Dump", desc: "原子轨迹\n位置/速度/力", color: C.accent },
  { name: "Cell", desc: "晶胞维度\n晶格常数变化", color: C.lightNavy },
  { name: "Species", desc: "化学物种计数\n实时物种分布", color: C.navy },
  { name: "POS", desc: "POSCAR格式\n晶体结构文件", color: C.teal },
  { name: "OVITO", desc: "OVITO导出格式\n可视化中间格式", color: C.accent },
  { name: "General", desc: "通用 CSV/TSV\n自动检测分隔符", color: C.lightNavy },
];
parsers.forEach((p, i) => {
  const col = i % 4;
  const row = Math.floor(i / 4);
  const x = 0.4 + col * 2.38;
  const y = 0.85 + row * 2.1;
  card(slide, x, y, 2.2, 1.75, { fill: C.cardBg, line: p.color, lineWidth: 2 });
  slide.addShape(pptx.shapes.RECTANGLE, { x, y, w: 0.1, h: 1.75, fill: { color: p.color } });
  slide.addShape(pptx.shapes.OVAL, { x: x + 0.7, y: y + 0.12, w: 0.75, h: 0.75, fill: { color: p.color } });
  slide.addText(p.name.substring(0, 3), { x: x + 0.7, y: y + 0.18, w: 0.75, h: 0.62, fontSize: 11, fontFace: fn.sans, color: C.warmWhite, bold: true, align: "center", valign: "middle" });
  slide.addText(p.name, { x: x + 0.1, y: y + 0.92, w: 2.0, h: 0.3, fontSize: 13, fontFace: fn.cn, color: C.navy, bold: true, align: "center", margin: 0 });
  slide.addText(p.desc, { x: x + 0.1, y: y + 1.22, w: 2.0, h: 0.48, fontSize: 10, fontFace: fn.cn, color: C.grayText, align: "center" });
});

// ==============================================================
// Slide 5: Mapping Layer
// ==============================================================
slide = pptx.addSlide();
addTitleBar(slide, "六、Mapping Layer：信号处理算法");

const groups = [
  { title: "物理约束类", color: C.teal, algos: ["segment_spline", "adaptive_kalman", "physics_constrained"], desc: "基于物理模型或约束的平滑方法" },
  { title: "统计平滑类", color: C.accent, algos: ["robust_lowess", "moving_avg", "ewma"], desc: "基于统计估计的局部/全局平滑" },
  { title: "频域处理类", color: C.lightNavy, algos: ["wavelet", "dynamic_wavelet", "savgol"], desc: "基于小波/频域变换的信号去噪" },
];
groups.forEach((g, gi) => {
  const x = 0.4 + gi * 3.15;
  card(slide, x, 0.85, 2.95, 2.3, { fill: C.cardBg, line: g.color, lineWidth: 1.5 });
  slide.addShape(pptx.shapes.RECTANGLE, { x, y: 0.85, w: 2.95, h: 0.4, fill: { color: g.color } });
  slide.addText(g.title, { x, y: 0.88, w: 2.95, h: 0.36, fontSize: 14, fontFace: fn.cn, color: C.warmWhite, bold: true, align: "center", valign: "middle" });
  slide.addText(g.desc, { x: x + 0.1, y: 1.28, w: 2.75, h: 0.28, fontSize: 10, fontFace: fn.cn, color: C.warmWhite, align: "center", margin: 0 });
  g.algos.forEach((a, ai) => {
    slide.addShape(pptx.shapes.RECTANGLE, { x: x + 0.1, y: 1.62 + ai * 0.38, w: 2.75, h: 0.3, fill: { color: g.color } });
    slide.addText(a, { x: x + 0.1, y: 1.62 + ai * 0.38, w: 2.75, h: 0.3, fontSize: 11, fontFace: fn.mono, color: C.warmWhite, align: "center", valign: "middle" });
  });
});

// Filters
slide.addText("异常值过滤", { x: 0.4, y: 3.28, w: 9.2, h: 0.38, fontSize: 16, fontFace: fn.cn, color: C.navy, bold: true, margin: 0 });
const filters = [
  { name: "zscore", desc: "Z分数法 |z|>σ阈值为异常 | 等效3σ原则", color: "F4A261" },
  { name: "MAD", desc: "中位数绝对偏差 | 50%异常数据仍鲁棒", color: "E76F51" },
  { name: "IQR", desc: "四分位距法 | 非参数，无需分布假设", color: "2A9D8F" },
];
filters.forEach((f, i) => {
  const x = 0.4 + i * 3.15;
  card(slide, x, 3.72, 2.95, 0.85, { fill: f.color });
  slide.addText(f.name.toUpperCase(), { x, y: 3.75, w: 2.95, h: 0.35, fontSize: 14, fontFace: fn.sans, color: C.warmWhite, bold: true, align: "center", margin: 0 });
  slide.addText(f.desc, { x: x + 0.1, y: 4.1, w: 2.75, h: 0.4, fontSize: 10, fontFace: fn.cn, color: C.warmWhite, align: "center" });
});

// ==============================================================
// Slide 6: Agent Architecture
// ==============================================================
slide = pptx.addSlide();
addTitleBar(slide, "七、Agent 架构：自然语言 → 工具链");

const flowSteps = [
  { x: 0.25, w: 1.9, label: "Natural Language\nGoal", bg: C.navy },
    { x: 2.3, w: 2.1, label: "plan_from_goal()\nLLM优先推理\n→ 关键词降级", bg: C.lightNavy },
  { x: 4.55, w: 2.4, label: "execute()\n18 tools in\nTOOL_REGISTRY", bg: C.teal },
  { x: 7.1, w: 2.0, label: "JSONL Logger\n完整追溯", bg: C.accent },
];
flowSteps.forEach((s, i) => {
  card(slide, s.x, 0.85, s.w, 1.05, { fill: s.bg });
  slide.addText(s.label, { x: s.x, y: 0.85, w: s.w, h: 1.05, fontSize: 11, fontFace: fn.cn, color: C.warmWhite, bold: true, align: "center", valign: "middle" });
  if (i < flowSteps.length - 1) slide.addText("→", { x: s.x + s.w, y: 1.1, w: 0.35, h: 0.55, fontSize: 18, color: C.navy, align: "center" });
});

// Tool categories
const toolCats = [
  { title: "Arrange", tools: ["arrange", "load_config"], color: C.navy },
  { title: "Read (8)", tools: ["read_log", "read_bonds", "read_dump", "read_data", "read_cell", "read_species", "read_pos", "read_general"], color: C.teal },
  { title: "Map + Chem", tools: ["smooth", "filter_outliers", "molecular_weight", "find_elements", "atom_type", "detect_encoding", "autocode"], color: C.accent },
];
toolCats.forEach((cat, i) => {
  const x = 0.25 + i * 3.25;
  card(slide, x, 2.1, 3.0, 2.5, { fill: C.cardBg, line: cat.color, lineWidth: 1.5 });
  slide.addShape(pptx.shapes.RECTANGLE, { x, y: 2.1, w: 3.0, h: 0.42, fill: { color: cat.color } });
  slide.addText(cat.title, { x, y: 2.12, w: 3.0, h: 0.38, fontSize: 13, fontFace: fn.cn, color: C.warmWhite, bold: true, align: "center", valign: "middle" });
  slide.addText(cat.tools.map((t, ti) => ({ text: t, options: { breakLine: ti < cat.tools.length - 1, fontFace: fn.mono, fontSize: 10, color: C.darkText } })), { x: x + 0.12, y: 2.58, w: 2.76, h: 1.95, valign: "top" });
});

// ==============================================================
// Slide 6.5: LLM Application Examples (NEW)
// ==============================================================
slide = pptx.addSlide();
addTitleBar(slide, "八、大模型赋能 lmpsmart：三大应用场景");

// Intro line
card(slide, 0.4, 0.85, 9.2, 0.72, { fill: C.navy });
slide.addText("lmpsmart 的 Agent 架构天然支持大模型（LLM）扩展——自然语言理解 → 自主规划 → 工具执行 → 可追溯日志", {
  x: 0.5, y: 0.88, w: 9.0, h: 0.66, fontSize: 13, fontFace: fn.cn, color: C.warmWhite, valign: "middle", margin: 0,
});

// Three examples
const llmExamples = [
  {
    title: "场景1：自然语言驱动数据处理",
    prompt: "平滑 log.lammps 中温度曲线，去除异常值，并输出出版级图片",
    response: "plan_from_goal 分解为：\nread_log → smooth(savgol) → filter_outliers(zscore) → plot()",
    color: C.teal,
    tag: "意图理解 → 工具链",
  },
  {
    title: "场景2：批量流水线自动规划",
    prompt: "解析 data/ 目录下所有 ReaxFF 输出文件，计算键级分布",
    response: "Agent 自动识别 Glob 模式 →\n并行 arrange(Log,Bonds,Dump) →\n统计 bonds.csv 中各键数量",
    color: C.navy,
    tag: "自动规划 → 批量执行",
  },
  {
    title: "场景3：智能数据质量分析",
    prompt: "分析 temperature 数据质量，识别异常升温/降温阶段",
    response: "LLM 理解'异常'语义 →\n调用 adaptive_kalman + zscore →\n输出异常阶段时间戳 + 可视化",
    color: C.purple,
    tag: "语义理解 → 智能分析",
  },
];

llmExamples.forEach((ex, i) => {
  const y = 1.72 + i * 1.1;
  card(slide, 0.4, y, 9.2, 0.98, { fill: C.cardBg, line: ex.color, lineWidth: 1.5 });
  slide.addShape(pptx.shapes.RECTANGLE, { x: 0.4, y, w: 0.08, h: 0.98, fill: { color: ex.color } });
  pill(slide, 0.6, y + 0.08, 2.5, 0.28, ex.color, ex.tag, 9);
  slide.addText(ex.title, { x: 3.2, y: y + 0.05, w: 6.2, h: 0.3, fontSize: 13, fontFace: fn.cn, color: C.navy, bold: true, margin: 0 });
  slide.addText("用户: " + ex.prompt, { x: 0.6, y: y + 0.38, w: 4.2, h: 0.26, fontSize: 10, fontFace: fn.cn, color: C.grayText, margin: 0 });
  slide.addText("→ " + ex.response, { x: 4.9, y: y + 0.38, w: 4.5, h: 0.5, fontSize: 10, fontFace: fn.mono, color: C.darkText, margin: 0 });
});

// Future LLM integration note
card(slide, 0.4, 5.08, 9.2, 0.45, { fill: C.gold, line: C.gold });
slide.addText("✅ 已落地：Agent 架构内置 LLM 推理（Ollama qwen3.5-9b / gpt-4o），关键词匹配作降级兜底", {
  x: 0.5, y: 5.1, w: 9.0, h: 0.4, fontSize: 12, fontFace: fn.cn, color: C.navy, bold: true, valign: "middle", margin: 0,
});

// ==============================================================
// Slide 7: Config-Driven
// ==============================================================
slide = pptx.addSlide();
addTitleBar(slide, "九、YAML驱动：零硬编码");

// YAML block
card(slide, 0.4, 0.85, 4.8, 3.85, { fill: C.navy });
slide.addText("configs/default.yaml", { x: 0.5, y: 0.88, w: 4.6, h: 0.35, fontSize: 12, fontFace: fn.mono, color: C.gold, margin: 0 });
const yamlLines = [
  { t: "cutoff:", c: C.accent },
  { t: "  bonds: [CC, CN, CO, CH...]", c: C.warmWhite },
  { t: "  bocutoff: [0.55, 0.30, 0.65...]", c: C.warmWhite },
  { t: "", c: C.warmWhite },
  { t: "filerule1:", c: C.accent },
  { t: '  logfilename: "log.lammps*"', c: C.warmWhite },
  { t: '  bondsfilename: "bonds.reax.bof"', c: C.warmWhite },
  { t: "", c: C.warmWhite },
  { t: "bonds_limit:", c: C.accent },
  { t: "  Al: 6; C: 4; H: 1; N: 3; O: 2", c: C.warmWhite },
  { t: "", c: C.warmWhite },
  { t: "timestep: 0.1  # fs", c: C.grayText },
  { t: "thermostep: 100", c: C.grayText },
];
yamlLines.forEach((l, i) => {
  slide.addText(l.t || " ", { x: 0.55, y: 1.25 + i * 0.27, w: 4.5, h: 0.25, fontSize: 11, fontFace: fn.mono, color: l.c, margin: 0 });
});

// Features
const cfgFeatures = [
  { icon: "CFG", title: "30种键类型", desc: "bonds/bocutoff/blcutoff" },
  { icon: "GLOB", title: "Glob批量", desc: "8种文件格式自动匹配" },
  { icon: "LIM", title: "键数限制", desc: "Al:6, C:4, H:1, N:3, O:2" },
  { icon: "STEP", title: "时间参数", desc: "timestep/thermostep/supercell" },
];
cfgFeatures.forEach((f, i) => {
  const y = 0.85 + i * 0.95;
  slide.addShape(pptx.shapes.OVAL, { x: 5.5, y: y + 0.08, w: 0.55, h: 0.55, fill: { color: C.teal } });
  slide.addText(f.icon, { x: 5.5, y: y + 0.12, w: 0.55, h: 0.47, fontSize: 10, fontFace: fn.sans, color: C.warmWhite, bold: true, align: "center", valign: "middle" });
  slide.addText(f.title, { x: 6.2, y: y, w: 3.4, h: 0.32, fontSize: 14, fontFace: fn.cn, color: C.navy, bold: true, margin: 0 });
  slide.addText(f.desc, { x: 6.2, y: y + 0.32, w: 3.4, h: 0.28, fontSize: 11, fontFace: fn.cn, color: C.grayText, margin: 0 });
});

// Validation note
card(slide, 0.4, 4.85, 9.2, 0.55, { fill: C.accent, line: C.accent });
slide.addText("Pydantic 模型在加载时验证 YAML — 运行时零错误  |  yaml参数可自定义", {
  x: 0.5, y: 4.88, w: 9.0, h: 0.5, fontSize: 13, fontFace: fn.cn, color: C.navy, bold: true, valign: "middle", margin: 0,
});

// ==============================================================
// Slide 8: Glob Batch
// ==============================================================
slide = pptx.addSlide();
addTitleBar(slide, "十、Glob 批量处理：一次解析多个文件");

// Input
card(slide, 0.4, 0.85, 3.6, 2.85, { fill: C.cardBg, line: C.grayText, lineWidth: 1, lineType: "dash" });
slide.addText("📁 input/", { x: 0.4, y: 0.88, w: 3.6, h: 0.38, fontSize: 13, fontFace: fn.cn, color: C.navy, bold: true, align: "center", margin: 0 });
const inputFiles = ["log.lammps.0", "log.lammps.1", "log.lammps.2", "bonds.reax.0", "bonds.reax.1", "dump.0.trj", "dump.1.trj"];
inputFiles.forEach((f, i) => {
  slide.addText("📄 " + f, { x: 0.5, y: 1.32 + i * 0.28, w: 3.4, h: 0.26, fontSize: 10, fontFace: fn.mono, color: C.darkText, margin: 0 });
});

// Arrow
slide.addText("glob →", { x: 4.1, y: 1.8, w: 1.1, h: 0.55, fontSize: 16, fontFace: fn.sans, color: C.navy, bold: true, align: "center" });

// Output
card(slide, 5.3, 0.85, 4.3, 2.85, { fill: C.cardBg, line: C.teal, lineWidth: 1.5 });
slide.addText("Output", { x: 5.3, y: 0.88, w: 4.3, h: 0.38, fontSize: 13, fontFace: fn.cn, color: C.teal, bold: true, align: "center", margin: 0 });
const outputFiles = [
  "dataoflog.csv", "dataoflog.split0.csv",
  "dataoflog.split1.csv", "dataoflog.split2.csv",
  "bonds.csv", "dump.csv",
];
outputFiles.forEach((o, i) => {
  slide.addShape(pptx.shapes.RECTANGLE, { x: 5.42, y: 1.32 + i * 0.35, w: 4.06, h: 0.28, fill: { color: C.teal, transparency: 85 } });
  slide.addText("📊 " + o, { x: 5.48, y: 1.32 + i * 0.35, w: 3.94, h: 0.28, fontSize: 10, fontFace: fn.mono, color: C.darkText, valign: "middle", margin: 0 });
});

// Benefits
card(slide, 1.5, 3.85, 7.0, 1.35, { fill: C.navy });
slide.addText("核心优势", { x: 1.7, y: 3.9, w: 6.6, h: 0.35, fontSize: 13, fontFace: fn.cn, color: C.gold, bold: true, margin: 0 });
slide.addText("✓ 自动匹配文件类型     ✓ 自动识别拆分大文件     ✓ 零配置批量处理", {
  x: 1.7, y: 4.28, w: 6.6, h: 0.75, fontSize: 14, fontFace: fn.cn, color: C.warmWhite, margin: 0,
});

// ==============================================================
// Slide 9: Reproducibility
// ==============================================================
slide = pptx.addSlide();
addTitleBar(slide, "十一、JSONL 执行日志：完整可追溯");

card(slide, 0.4, 0.85, 9.2, 2.85, { fill: C.navy });
slide.addText("logs/session_20260528.jsonl", { x: 0.5, y: 0.88, w: 9.0, h: 0.32, fontSize: 11, fontFace: fn.mono, color: C.gold, margin: 0 });
const jsonLines = [
  { t: "{", c: C.warmWhite },
  { t: '  "log_id": "a1b2c3d4",', c: "4ECDC4" },
  { t: '  "timestamp": "2026-05-28T10:00:00",', c: C.grayText },
  { t: '  "session_id": "x9y8z7",', c: C.grayText },
  { t: '  "tool": "arrange",', c: C.accent },
  { t: '  "input": {"modes": ["Log","Bonds"], "path": "./data"},', c: C.warmWhite },
  { t: '  "execution_steps": ["arrange: modes=[Log,Bonds]..."],', c: C.warmWhite },
  { t: '  "output_summary": {"shape": [100,20], "files": 3},', c: C.warmWhite },
  { t: '  "status": "success",', c: "4CAF50" },
  { t: "}", c: C.warmWhite },
];
jsonLines.forEach((l, i) => {
  slide.addText(l.t || " ", { x: 0.55, y: 1.22 + i * 0.23, w: 8.9, h: 0.22, fontSize: 11, fontFace: fn.mono, color: l.c, margin: 0 });
});

const reproFeatures = [
  { icon: "ID", title: "log_id", desc: "全局唯一追溯码" },
  { icon: "TS", title: "timestamp", desc: "精确到毫秒" },
  { icon: "SID", title: "session_id", desc: "会话级追踪" },
  { icon: "SUM", title: "summary", desc: "DataFrame概要（非序列化，防日志膨胀）" },
];
reproFeatures.forEach((f, i) => {
  const x = 0.4 + i * 2.4;
  card(slide, x, 3.85, 2.25, 1.45, { fill: C.cardBg, line: C.teal, lineWidth: 1 });
  slide.addShape(pptx.shapes.OVAL, { x: x + 0.75, y: 3.92, w: 0.75, h: 0.75, fill: { color: C.teal } });
  slide.addText(f.icon, { x: x + 0.75, y: 4.02, w: 0.75, h: 0.55, fontSize: 11, fontFace: fn.sans, color: C.warmWhite, bold: true, align: "center", valign: "middle" });
  slide.addText(f.title, { x, y: 4.72, w: 2.25, h: 0.25, fontSize: 12, fontFace: fn.cn, color: C.navy, bold: true, align: "center", margin: 0 });
  slide.addText(f.desc, { x: x + 0.08, y: 4.97, w: 2.09, h: 0.28, fontSize: 10, fontFace: fn.cn, color: C.grayText, align: "center" });
});

// ==============================================================
// Slide 10: CLI + API
// ==============================================================
slide = pptx.addSlide();
addTitleBar(slide, "十二、简洁易用：CLI + Python API");

// CLI
card(slide, 0.4, 0.85, 4.5, 3.55, { fill: C.navy });
slide.addText("CLI", { x: 0.4, y: 0.88, w: 4.5, h: 0.4, fontSize: 15, fontFace: fn.cn, color: C.accent, bold: true, align: "center", margin: 0 });
const cliLines = [
  { t: "# 查看配置", c: C.grayText },
  { t: "lmpsmart config --show", c: "98FB98" },
  { t: "", c: C.warmWhite },
  { t: "# 解析LAMMPS文件", c: C.grayText },
  { t: "lmpsmart arrange --path ./data --modes Log,Bonds,Dump", c: "98FB98" },
  { t: "", c: C.warmWhite },
  { t: "# Agent模式", c: C.grayText },
  { t: "lmpsmart agent --goal \"arrange log files and smooth temperature\"", c: "98FB98" },
];
cliLines.forEach((l, i) => {
  slide.addText(l.t || " ", { x: 0.55, y: 1.32 + i * 0.35, w: 4.2, h: 0.32, fontSize: 10, fontFace: fn.mono, color: l.c, margin: 0 });
});

// Python API
card(slide, 5.1, 0.85, 4.5, 3.55, { fill: C.navy });
slide.addText("Python API", { x: 5.1, y: 0.88, w: 4.5, h: 0.4, fontSize: 15, fontFace: fn.cn, color: C.accent, bold: true, align: "center", margin: 0 });
const pyLines = [
  { t: "from lmpsmart import (", c: "98FB98" },
  { t: "  arrange, smooth,", c: "98FB98" },
  { t: "  filter_outliers", c: "98FB98" },
  { t: ")", c: "98FB98" },
  { t: "", c: C.warmWhite },
  { t: "# 解析 + 平滑 + 过滤", c: C.grayText },
  { t: "df = arrange(\"data/\", modes=[\"Log\",\"Bonds\"])", c: "98FB98" },
  { t: "smoothed = smooth(df[\"temperature\"], method=\"savgol\")", c: "98FB98" },
];
pyLines.forEach((l, i) => {
  slide.addText(l.t || " ", { x: 5.25, y: 1.32 + i * 0.35, w: 4.2, h: 0.32, fontSize: 10, fontFace: fn.mono, color: l.c, margin: 0 });
});

// Subcommands
const subcmds = ["arrange", "smooth", "filter", "config", "llm", "agent"];
subcmds.forEach((s, i) => {
  pill(slide, 0.4 + i * 1.55, 4.55, 1.4, 0.5, i % 2 === 0 ? C.navy : C.lightNavy, s, 13);
});
slide.addText("6个子命令  ·  --help 查看详情  ·  --version 显示版本", {
  x: 0.4, y: 5.12, w: 9.2, h: 0.25, fontSize: 10, fontFace: fn.cn, color: C.grayText, align: "center", margin: 0,
});

// ==============================================================
// Slide 11: Comparison Table
// ==============================================================
slide = pptx.addSlide();
addTitleBar(slide, "十三、lmpsmart vs 主流 LAMMPS 数据处理工具");

// Comparison table (5 tools, only marks)
const comps = [
  { dim: "派生物理量计算\n（RDF/RMSD/CED等）", vals: ["✓✓", "✓✓", "✓", "✓", "✓ 内置+可扩展"], color: ["E07A5F", "6A5ACD", "3D405B", "5F9EA0", C.navy] },
  { dim: "数据标准化·原创输出\n（Bonds阈值/Cell/Atom/mweight等）", vals: ["✗", "✗", "✗", "✗", "✓"], color: ["E07A5F", "6A5ACD", "3D405B", "5F9EA0", C.navy] },
  { dim: "自定义指标扩展", vals: ["~(Pro)", "~(Tcl)", "~", "~", "✓ YAML可配"], color: [C.grayText, C.grayText, C.grayText, C.grayText, C.navy] },
  { dim: "数据降噪+曲线拟合\n（9平滑+polyfit.n/lowess等）", vals: ["✗", "✗", "✗", "✗", "✓"], color: ["E07A5F", "6A5ACD", "3D405B", "5F9EA0", C.navy] },
  { dim: "统计异常值过滤\n（zscore/MAD/IQR）", vals: ["✗", "✗", "✗", "✗", "✓"], color: ["E07A5F", "6A5ACD", "3D405B", "5F9EA0", C.navy] },
  { dim: "专业曲线绘图\n（出版级）", vals: ["✗", "✗", "~", "~", "✓ 内置"], color: ["E07A5F", "6A5ACD", C.grayText, C.grayText, C.navy] },
  { dim: "自然语言命令", vals: ["✗", "✗", "✗", "✗", "✓ LLM驱动"], color: ["E07A5F", "6A5ACD", "3D405B", "5F9EA0", C.navy] },
  { dim: "Agent 规划", vals: ["✗", "✗", "✗", "✗", "✓"], color: ["E07A5F", "6A5ACD", "3D405B", "5F9EA0", C.navy] },
  { dim: "JSONL 执行日志", vals: ["✗", "✗", "✗", "✗", "✓"], color: ["E07A5F", "6A5ACD", "3D405B", "5F9EA0", C.navy] },
  { dim: "批量 Glob 匹配", vals: ["✗", "~", "~", "✗", "✓"], color: ["E07A5F", C.grayText, C.grayText, "E07A5F", C.navy] },
];

// Table header (no separate badge row)
const colW = 1.48;
const labelW = 2.0;
const colX = [0.3 + labelW];
for (let ci = 0; ci < 4; ci++) colX.push(colX[ci] + colW);

slide.addShape(pptx.shapes.RECTANGLE, { x: 0.3, y: 0.88, w: 9.4, h: 0.47, fill: { color: C.navy } });
const toolLabels = ["OVITO\n可视化+分析", "VMD\n轨迹+Tcl", "mdapy\nC++加速", "MDAnalysis\n学术流行", "LMPSmart\nAgent可追溯"];
const toolHeaderColors = ["E07A5F", "6A5ACD", C.warmWhite, "5F9EA0", C.accent];
slide.addText("对比维度", { x: 0.3, y: 0.88, w: labelW, h: 0.47, fontSize: 11, fontFace: fn.cn, color: C.warmWhite, bold: true, align: "center", valign: "middle" });
toolLabels.forEach((h, i) => {
  slide.addText(h, { x: colX[i], y: 0.88, w: colW, h: 0.47, fontSize: 10, fontFace: fn.cn, color: toolHeaderColors[i], bold: true, align: "center", valign: "middle" });
});

const rowH = 0.40;
comps.forEach((c, i) => {
  const y = 1.4 + i * rowH;
  const rowBg = i % 2 === 0 ? C.cardBg : C.lightBg;
  slide.addShape(pptx.shapes.RECTANGLE, { x: 0.3, y, w: 9.4, h: rowH, fill: { color: rowBg } });
  slide.addText(c.dim, { x: 0.35, y, w: labelW - 0.05, h: rowH, fontSize: 10, fontFace: fn.cn, color: C.darkText, bold: true, valign: "middle" });
  for (let ci = 0; ci < 5; ci++) {
    slide.addText(c.vals[ci], { x: colX[ci], y, w: colW, h: rowH, fontSize: 10, fontFace: fn.cn, color: c.color[ci], bold: ci === 4, align: "center", valign: "middle" });
  }
});

// Insight
card(slide, 0.3, 5.5, 9.4, 0.55, { fill: C.navy });
slide.addText([
  { text: "lmpsmart = 数据标准化（8大原创输出） + 降噪+拟合（9平滑+polyfit.n/lowess等） + 过滤（3种） + Agent + JSONL日志", options: { color: C.warmWhite, fontSize: 10 } },
  { text: "  |  OVITO/VMD/mdapy/MDAnalysis 专注派生物理量，lmpsmart 定位为互补前置清洗层", options: { color: C.lightGray, fontSize: 10 } },
], { x: 0.4, y: 5.52, w: 9.2, h: 0.52, valign: "middle" });

// ==============================================================
// Slide 12: Conclusion
// ==============================================================
slide = pptx.addSlide();
slide.background = { color: C.navy };
slide.addShape(pptx.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.08, fill: { color: C.gold } });

slide.addText("总结与展望", { x: 0.5, y: 0.3, w: 9, h: 0.7, fontSize: 34, fontFace: fn.title, color: C.warmWhite, bold: true, margin: 0 });

// Stats
const stats = [
  { num: "8", unit: "Parsers", label: "文件格式支持" },
  { num: "9+3", unit: "Algorithms", label: "平滑 + 过滤" },
  { num: "0", unit: "Hardcoding", label: "YAML驱动" },
];
stats.forEach((s, i) => {
  const x = 0.5 + i * 3.15;
  card(slide, x, 1.1, 2.95, 1.25, { fill: C.lightNavy });
  slide.addText(s.num, { x, y: 1.12, w: 2.95, h: 0.65, fontSize: 34, fontFace: fn.title, color: C.accent, bold: true, align: "center", margin: 0 });
  slide.addText(s.unit, { x, y: 1.72, w: 2.95, h: 0.28, fontSize: 12, fontFace: fn.sans, color: C.warmWhite, bold: true, align: "center", margin: 0 });
  slide.addText(s.label, { x, y: 1.98, w: 2.95, h: 0.28, fontSize: 10, fontFace: fn.cn, color: C.grayText, align: "center", margin: 0 });
});

// Future
slide.addText("Future Work", { x: 0.5, y: 2.55, w: 9, h: 0.4, fontSize: 17, fontFace: fn.cn, color: C.gold, bold: true, margin: 0 });
const futures = [
  { icon: "🤖", text: "LLM 推理已落地（Ollama/qwen3.5-9b）——关键词匹配作降级兜底" },
  { icon: "🌐", text: "REST API + React Web UI（无CLI用户友好）" },
  { icon: "☁️", text: "Docker 容器化（ HPC 集群一键部署）" },
  { icon: "📊", text: "自动化统计验证（平滑 vs 原始数据假设检验）" },
];
futures.forEach((f, i) => {
  const x = (i % 2) * 4.5 + 0.5;
  const y = 3.0 + Math.floor(i / 2) * 0.52;
  slide.addText(f.icon + "  " + f.text, { x, y, w: 4.3, h: 0.48, fontSize: 12, fontFace: fn.cn, color: C.warmWhite, valign: "middle", margin: 0 });
});

// Footer
card(slide, 0, 4.6, 10, 1.0, { fill: C.lightNavy });
slide.addText("github.com/qgan2025/LMPSmart  ·  GPL-3.0  ·  Copyright (c) 2025 Qiang Gan", {
  x: 0, y: 4.7, w: 10, h: 0.38, fontSize: 13, fontFace: fn.cn, color: C.warmWhite, align: "center", margin: 0,
});
slide.addText("LAMMPS Molecular Dynamics Data Processing Agent  ·  v1.0.0", {
  x: 0, y: 5.1, w: 10, h: 0.28, fontSize: 10, fontFace: fn.cn, color: C.grayText, align: "center", margin: 0,
});

// Save
const outPath = "D:/MyObsidian/Projects/lmpsmart/docs/lmpsmart_competition.pptx";
pptx.writeFile({ fileName: outPath })
  .then(() => console.log("Saved: " + outPath))
  .catch(err => { console.error("Error:", err); process.exit(1); });
