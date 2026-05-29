# lmpsmart v1.0 系统部署与运行指南

> Data Agent 系统代码开源地址: https://github.com/gqiang138/LMPSmart
>
> 本文档提供完整的系统部署与运行指南，确保系统能够被复现与验证。

---

## 1. 系统概述

lmpsmart 是一个基于 Agent 架构的 LAMMPS 分子动力学数据处理工具，支持：

- **8种文件解析**：Log、Bonds、Dump、Cell、Species、POS、OVITO、General
- **8种原创标准化输出**：键序阈值筛选、晶胞维度提取、原子类型映射、分子量计算
- **9种平滑算法** + 曲线拟合 + **3种异常值过滤**
- **7种绘图类型** + **4种动图模式**
- **25个 MCP 工具**，通过 Model Context Protocol 向 AI Agent 暴露
- 完整 JSONL 执行日志，支持全流程可追溯

---

## 2. 系统架构

```
┌─────────────────────────────────────────────────────┐
│  Arrange Layer      ← 8 parsers + 8 原创标准化输出   │
│                     + glob 批量匹配 + YAML 配置驱动   │
└──────────────────────────┬──────────────────────────┘
                           ↓
                     pandas DataFrame
                           ↓
┌─────────────────────────────────────────────────────┐
│  Mapping Layer     ← 9 smoothers + curve fitting    │
│                     + 3 filters + 7 plots + 4 动画  │
└──────────────────────────┬──────────────────────────┘
                           ↓
                       Output files
┌─────────────────────────────────────────────────────┐
│  Agent Controller   ← plan_from_goal() → execute()    │
│                     + ExecutionLogger (JSONL)        │
└─────────────────────────────────────────────────────┘
```

---

## 3. 运行环境要求

### 3.1 软件环境

| 组件 | 版本要求 | 说明 |
|------|---------|------|
| Python | >= 3.10 | 推荐 3.12 |
| pip | 最新版 | 包管理器 |

### 3.2 核心依赖（必需）

```
numpy, pandas, scipy, statsmodels, pyyaml, pydantic>=2,
openpyxl, chardet, matplotlib
```

### 3.3 可选依赖

| 包 | 用途 | 安装命令 |
|----|------|---------|
| `mcp` | MCP Server（stdio/HTTP 传输） | `pip install mcp` |
| `pykalman` | 自适应卡尔曼平滑器 | `pip install pykalman` |
| `pywavelets` | 小波变换平滑器 | `pip install pywavelets` |
| `pillow` | 动图 GIF 输出 | `pip install pillow` |

### 3.4 硬件要求

- 最低：4GB RAM，多核 CPU
- 推荐：8GB+ RAM，支持并行计算
- 磁盘：至少 500MB（不含模拟数据）

---

## 4. 安装方式

### 方式一：智能安装向导（推荐）

```bash
git clone https://github.com/gqiang138/LMPSmart
cd lmpsmart
python install.py
```

安装向导自动检测 conda / venv / 系统 Python 环境，可选配置 LLM。

### 方式二：手动安装

```bash
git clone https://github.com/gqiang138/LMPSmart
cd lmpsmart
pip install -e .

# 验证安装
python -m lmpsmart config --show
```

### 方式三：使用现有环境

```bash
# conda 环境
conda create -n lmpsmart python=3.12 -y
conda activate lmpsmart
pip install -e .
```

---

## 5. 快速启动

### 5.1 CLI 模式

```bash
# 查看配置
python -m lmpsmart config --show

# 解析 LAMMPS 文件
python -m lmpsmart arrange --path ./data --modes Log,Bonds,Dump

# Agent 模式（自然语言驱动）
python -m lmpsmart agent --goal "平滑温度曲线并去除异常值"

# 绘图
python -m lmpsmart plot --csv output/arrange/dataoflog.csv \
    --x time --y TempEng --mode single --output energy.png
```

### 5.2 Python API

```python
from lmpsmart import arrange, smooth, filter_outliers

# 解析数据
df = arrange("data/", modes=["Log", "Bonds"])

# 平滑信号
smoothed = smooth(df["temperature"], method="savgol")

# 过滤异常值
filtered = filter_outliers(df, "time", "temperature", "zscore", 3.0)
```

### 5.3 MCP Server 模式（AI Agent 集成）

**stdio 传输（OpenCode / Claude Desktop）：**

```bash
python -m lmpsmart.api.mcp_server
```

**HTTP 传输（Cherry Studio / 远程访问）：**

```bash
python -m lmpsmart.api.mcp_server --http --port 8765
```

---

## 6. MCP Server 配置详解

### 6.1 OpenCode 配置

在项目根目录的 `opencode.json` 中添加：

```json
{
  "mcp": {
    "lmpsmart": {
      "type": "local",
      "command": [
        "E:\\Program\\anaconda3\\envs\\lmpsmart\\python.exe",
        "-m",
        "lmpsmart.api.mcp_server"
      ],
      "environment": {},
      "enabled": true
    }
  }
}
```

然后在 OpenCode 中执行：
```bash
opencode mcp add lmpsmart E:\Program\anaconda3\envs\lmpsmart\python.exe -m lmpsmart.api.mcp_server
```

### 6.2 Cherry Studio 配置

在 Settings → MCP Server 添加：

| 字段 | 值 |
|------|-----|
| Name | lmpsmart |
| Transport | `StreamableHTTP` |
| URL | `http://localhost:8765/mcp` |

### 6.3 Claude Desktop 配置

编辑 `~/Library/Application Support/Claude/claude_desktop_config.json`（macOS）
或 `%APPDATA%\Claude\claude_desktop_config.json`（Windows）：

```json
{
  "mcpServers": {
    "lmpsmart": {
      "command": "python",
      "args": ["-m", "lmpsmart.api.mcp_server"]
    }
  }
}
```

### 6.4 可用 MCP 工具（25个）

| 类别 | 工具 | 说明 |
|------|------|------|
| Parse | `arrange` | 解析 LAMMPS 文件 |
| Parse | `read_log` | 读取热力学输出 |
| Parse | `read_bonds` | 读取 ReaxFF 键序 |
| Parse | `read_dump` | 读取轨迹文件 |
| Parse | `read_data` | 读取 data 文件 |
| Parse | `read_cell` | 读取晶胞维度 |
| Parse | `read_species` | 读取物种统计 |
| Parse | `read_pos` | 读取 POSCAR |
| Parse | `read_general` | 通用 CSV/TSV |
| Process | `smooth` | 9种平滑算法 |
| Process | `filter_outliers` | 3种异常值过滤 |
| Process | `fit` | 曲线拟合 |
| Visualize | `plot` | 7种绘图类型 |
| Visualize | `animate` | 4种动图模式 |
| Clean | `groupby_aggregate` | 分组聚合 |
| Clean | `belong_filter` | 行列筛选 |
| Clean | `column_rename` | 列重命名 |
| Clean | `select_columns` | 列选择 |
| Clean | `merge_data` | 数据合并 |
| Chemistry | `molecular_weight` | 分子量计算 |
| Chemistry | `find_elements` | 元素提取 |
| Chemistry | `atom_type` | 原子类型识别 |
| Chemistry | `detect_encoding` | 编码检测 |
| Chemistry | `autocode` | 自动解析结构 |
| Config | `load_config` | 加载配置 |

---

## 7. 测试方法

### 7.1 验证安装

```bash
# 工具数量验证
python -c "from lmpsmart.api.tools import TOOL_REGISTRY; print(len(TOOL_REGISTRY))"
# 应输出: 25

# 配置加载验证
python -m lmpsmart config --show
```

### 7.2 运行示例任务

**示例1：解析 RDX 分子动力学数据**

```bash
python -m lmpsmart arrange --path ./data/RDX --modes Log,Bonds,Dump
```

**示例2：绘图**

```bash
python -m lmpsmart plot --csv output/arrange/dataoflog.csv \
    --x time --y TempEng --mode single --output output/energy.png
```

**示例3：MCP 工具调用**

```bash
# 测试 MCP server 初始化
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' \
    | python -m lmpsmart.api.mcp_server
# 应返回 serverInfo，包含 name: lmpsmart

# 测试工具列表
echo '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' \
    | python -m lmpsmart.api.mcp_server
# 应返回 25 个工具
```

### 7.3 日志查看

执行日志位于 `logs/agent_session_*.jsonl`：

```bash
# 查看最新日志
ls -t logs/ | head -3

# 查看日志内容
cat logs/agent_session_$(ls -t logs/ | head -1)
```

JSONL 日志格式：
```json
{
  "log_id": "a1b2c3d4e5f6",
  "timestamp": "2026-05-29T17:12:10.640208",
  "session_id": "9d97249f",
  "tool": "plot",
  "input": {"x_col": "t", "y_cols": ["e"], "plot_type": "line"},
  "execution_steps": ["plot: x=t, y=['e']"],
  "output_summary": {"output": "C:\\temp\\l.png"},
  "warnings": [],
  "status": "success",
  "elapsed_ms": 0
}
```

---

## 8. LLM 配置

lmpsmart 支持本地 Ollama 和在线 OpenAI 兼容 API：

```bash
# 本地 Ollama（默认）
python -m lmpsmart llm setup --provider local --model qwen3.5-9b

# 在线 API（OpenRouter 等）
python -m lmpsmart llm setup --provider online \
    --base-url https://openrouter.ai/api/v1 \
    --api-key sk-or-xxxxx --model anthropic/claude-3-haiku

# 查看配置
python -m lmpsmart llm show

# 测试连接
python -m lmpsmart llm test
```

配置文件位于 `configs/llm.yaml`。

---

## 9. 故障排查

| 问题 | 解决方案 |
|------|---------|
| `ModuleNotFoundError: No module named 'lmpsmart'` | `pip install -e .` |
| `YAML parsing error (NO, ON, NC)` | 已在 default.yaml 中引用处理 |
| `adaptive_kalman unavailable` | `pip install pykalman` |
| `MCP server 连接失败` | 检查 Python 路径是否正确 |
| `UTF-8 decode error` | 使用 `--encoding GBK` |

---

## 10. 完整文件结构

```
lmpsmart/
├── configs/
│   ├── default.yaml       ← 全量配置（30种键类型、绘图参数等）
│   └── llm.yaml          ← LLM 配置
├── src/lmpsmart/
│   ├── arrange/
│   │   ├── config.py     ← Pydantic 配置加载
│   │   └── readers.py    ← 8种文件解析器 + arrange()
│   ├── mapping/
│   │   ├── smooth.py     ← 9种平滑算法
│   │   ├── filter.py     ← 3种异常值过滤
│   │   ├── plot.py       ← 基础绘图（line, scatter）
│   │   ├── advanced_plot.py ← 高级绘图（boxplot, violin, surface, contour, heatmap）
│   │   └── animation.py  ← 4种动图模式
│   ├── core/
│   │   └── tools.py      ← 元素表、编码检测等工具
│   └── api/
│       ├── agent.py       ← LmpparseAgent（规划 + 执行）
│       ├── tools.py       ← 25个工具包装器
│       ├── mcp_server.py  ← MCP Server（stdio/HTTP）
│       └── logging.py     ← JSONL 执行日志
├── scripts/
│   └── mcp_run.py        ← MCP 启动器（读取配置）
├── logs/                  ← 执行日志目录
├── output/
│   ├── arrange/          ← 解析结果 CSV
│   └── plot/            ← 绘图结果 PNG/GIF
├── docs/
│   ├── REPORT.md         ← 技术报告
│   └── video_script.md  ← 演示视频脚本
├── README.md
├── DEPLOYMENT.md
└── pyproject.toml
```
