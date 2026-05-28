# lmpsmart v1.0.0 演示视频脚本

## 基本信息
- **时长**: 10-12 分钟
- **风格**: 技术演示 + 竞赛汇报
- **语言**: 中文旁白 + 英文代码

---

## Slide 1: 开场（30秒）

**画面**: 深蓝色背景，大标题 lmpsmart，装饰性分子六边形图案

**旁白**:
> 大家好，我是 Qiang Gan。今天向大家介绍 lmpsmart v1.0.0——一个基于 Agent 架构的 LAMMPS 分子动力学数据处理工具。这是一个开源项目，采用 GPL-3.0 协议发布。

---

## Slide 1.5: 分子动力学方法（1分钟）

**画面**: 深蓝色背景，两栏布局（左：什么是分子动力学？/ 右：含能材料研究应用）+ 底部模拟尺度说明

**旁白**:
> 首先介绍分子动力学方法。分子动力学依据牛顿运动定律模拟分子体系运动，获得体系在相空间的时间演化轨迹，从中抽取样本计算宏观热力学和力学性质。
>
> 力场精度直接决定模拟结果质量——对于含能材料，ReaxFF-lg 反应力场是目前的主流选择，可以模拟键的生成与断裂、描述化学反应过程。
>
> 分子动力学在含能材料领域有广泛应用：晶体形貌预测与力学性能分析、冲击响应研究（撞击损伤、热点演化机理）、热分解性能（脱硝基反应机理）、以及 γ→ξ 等晶型相变研究。
>
> 典型模拟尺度：空间范围 1nm 到 100nm，时间范围 1ps 到 10ns，可处理百万原子级并行计算。

---

## Slide 1.6: LAMMPS：强大但数据处理面临挑战（1分钟）

**画面**: 浅色背景，上方两栏对比（LAMMPS 核心特点 / LAMMPS 自身局限）+ 下方五种输出文件格式卡片

**旁白**:
> LAMMPS 是目前最广泛使用的分子动力学模拟平台之一，由美国 Sandia 国家实验室开发，开源免费。
>
> 它支持百万原子级并行计算，ReaxFF 反应力场在含能材料领域得到广泛验证——但 LAMMPS 自身有三个重要局限：无图形界面、无分子建模工具、无复杂数据分析与可视化功能。
>
> 更重要的是，LAMMPS 的输出数据格式复杂多样：log 文件记录温度、压力、能量等热力学信息；dump 轨迹文件包含数千帧原子坐标和速度数据；bonds 键级文件输出 30 种化学键的键序和键长；species 物种文件依赖键级阈值统计各时刻化学物种数量；pos 晶胞结构文件记录晶格常数和体积变化。
>
> 这些文件格式各异、数据量庞大，给后续分析带来巨大挑战。

---

## Slide 2: 为什么需要 lmpsmart？（1分钟）

**画面**: 三个卡片（海量异构数据 / 传统方案局限 / 无可追溯性）+ 底部解决方框

**旁白**:
> LAMMPS + ReaxFF 产生的海量非标准数据，给分子动力学研究带来巨大挑战。
>
> OVITO 和 VMD 等可视化工具擅长 3D 轨迹展示和派生物理量计算，但无法处理原始数据的标准化——键序阈值筛选、晶胞参数提取、原子类型映射、分子量计算，这些都需要专门的数据处理。
>
> OVITO 导出的大量轨迹文件数据处理难度也很大——需要脚本逐帧分析，无法批量处理。
>
> 此外，传统方案缺乏可追溯性：手动操作无法复现，实验记录依赖人工备注。
>
> lmpsmart 从根本上解决这些问题：8 大原创标准化输出（Bond 阈值、Cell 提取、Atom 映射、分子量等），YAML 配置驱动零硬编码，9 种平滑加曲线拟合，Glob 批量匹配，JSONL 执行日志完整记录每一步操作。

---

## Slide 3: 系统架构（1分钟）

**画面**: 三层流程图（INPUT → Arrange Layer → DataFrame → Mapping Layer → OUTPUT）+ 右侧 Agent Controller

**旁白**:
> lmpsmart 采用三层架构设计。
>
> 第一层是 Arrange Layer，接收 LAMMPS 文件，通过 8 种专用解析器，将原始数据转换为 pandas DataFrame——更重要的是，它将 LAMMPS 的非标准数据转化为 8 种标准一维结构化输出，包括：Bonds 附加键序和键长阈值、Dump 轨迹提取晶胞维度、Atom 编号映射元素、Species/POS 附加分子量、OVITO 多帧整合为单表。
>
> 第二层是 Mapping Layer，对 DataFrame 应用 9 种平滑算法、曲线拟合（polyfit.n 多项式拟合、LOWESS 局部回归）和 3 种异常值过滤方法。
>
> 第三层是 Agent Controller，它接收自然语言目标，通过 plan_from_goal() 规划工具链，execute() 执行每一步，所有操作自动记录到 JSONL 日志。

---

## Slide 4: Arrange Layer（1分钟）

**画面**: 左侧 8 种文件格式网格 + 右侧 8 大原创标准化输出

**旁白**:
> Arrange Layer 的核心价值在于：将 LAMMPS 的非标准数据——键序文件、多帧轨迹、原子坐标——全部转化为标准一维结构化 DataFrame。
>
> 它支持 8 种文件格式：Log 解析热力学输出，Bonds 解析 ReaxFF 键序并附加 bocutoff 键序阈值和 blcutoff 键长阈值——这是 lmpsmart 的原创功能，方便用户直接按阈值筛选有效键。
>
> Dump 处理原子轨迹，同时能提取晶胞维度（Lx、Ly、Lz、Volume）作为独立数据表——这也是原创功能。Atom 列在解析时自动建立原子编号到元素的映射。
>
> Species 和 POS 额外附加分子量输出（molecular_weight），OVITO 导出的多帧 Excel 整合为一张一维数据表，General 自动检测 CSV 和 TSV。
>
> 所有格式支持 Glob 通配符——输入目录有多少文件，自动全部解析，自动 split 编号命名。

---

## Slide 5: Mapping Layer（1分钟）

**画面**: 深色背景，三个平滑+拟合分类组 + 底部三个过滤方法

**旁白**:
> Mapping Layer 实现 9 种平滑算法加曲线拟合，分三类。
>
> 物理约束类：segment_spline 在拐点分割后拟合样条；adaptive_kalman 用卡尔曼滤波自适应估计噪声；physics_constrained 用约束最小二乘施加物理约束。
>
> 统计平滑类：robust_lowess 用局部加权散点平滑加双平方鲁棒估计；moving_avg 滑动平均快速去噪；ewma 指数加权移动平均。
>
> 频域处理类：小波变换 wavelet、动态小波 denoising dynamic_wavelet、以及 Savitzky-Golay 滤波器 savgol——后者在保持峰形方面特别出色。
>
> 曲线拟合：polyfit.n 多项式拟合（含 R² 报告）和 LOWESS 局部回归——可直接输出拟合参数用于后续物理计算。
>
> 三种异常值过滤方法：Z-score、MAD 和 IQR，分别适用于不同噪声分布场景。

---

## Slide 6: Agent 架构（1分钟）

**画面**: 四步流程图（Goal → plan_from_goal → execute → JSONL）+ 三列工具分类

**旁白**:
> lmpsmart 的核心创新是基于 Agent 架构自主规划数据处理流水线。
>
> Agent 接收自然语言目标——比如"解析日志文件并平滑温度曲线"。
>
> plan_from_goal() 将目标分解为工具调用序列。核心创新：lmpsmart 的 Agent 架构天然支持大模型扩展——三步走：自然语言理解、自主规划、工具执行。
>
> execute() 从 TOOL_REGISTRY 调用工具函数，18 个工具覆盖：Arrange、Read 八种格式、Mapping、以及化学计算。
>
> 每一步执行都写入 JSONL 日志——包含 log_id、时间戳、会话 ID、输入摘要、输出摘要、执行耗时。DataFrame 不序列化，只记录 shape 和 dtype，防止日志膨胀。

---

## Slide 6.5: 大模型赋能 lmpsmart：三大应用场景（1分钟）

**画面**: 深蓝色介绍条 + 三个场景卡片（自然语言驱动 / 批量自动规划 / 智能数据质量分析）+ 底部金色未来方向条

**旁白**:
> lmpsmart 的 Agent 架构天然支持大模型扩展。底层设计：三步走——自然语言理解意图、自主规划工具链、执行并记录日志。
>
> 场景一：自然语言驱动数据处理。用户说"平滑温度曲线，去除异常值，并输出出版级图片"——LLM 理解语义，自动规划工具链：read_log 读取 → smooth(savgol) 平滑 → filter_outliers(zscore) 去噪 → plot() 绘图。
>
> 场景二：批量流水线自动规划。用户说"解析目录下所有 ReaxFF 输出文件，计算键级分布"——Agent 自动识别 Glob 模式，并行 arrange Log、Bonds、Dump，统计 bonds.csv 中各化学键数量。
>
> 场景三：智能数据质量分析。用户说"分析温度数据质量，识别异常升温或降温阶段"——LLM 理解"异常"的语义，自动调用 adaptive_kalman 卡尔曼滤波加 Z-score 过滤，输出异常阶段时间戳和可视化。
>
> LLM 推理已落地——Agent 架构内置 Ollama/qwen3:8b 和在线 API 两种模式，关键词匹配作为降级备选。后续扩展 Web UI、云端 Docker 部署、自动化统计验证。

---

## Slide 8: YAML 配置（45秒）

**画面**: 左侧深色代码块（YAML 配置片段）+ 右侧四个功能卡片

**旁白**:
> lmpsmart 零硬编码的秘密在于 configs/default.yaml。
>
> 这里配置了 30 种键类型的键序阈值和键长阈值，8 种文件的 Glob 匹配模式，每个元素的化学键数上限，以及时间步长等物理参数。
>
> Pydantic 模型在加载时自动验证 YAML——配置错误在启动时就报错，而不是运行到一半崩溃。

---

## Slide 9: Glob 批量匹配（30秒）

**画面**: 左侧输入文件夹（多个 log 文件）+ 箭头 → 右侧输出（split 编号文件）

**旁白**:
> Glob 批量匹配是 lmpsmart 的一大特色。输入目录有多少文件，一次性全部解析，自动 split 编号命名。
>
> 不需要手动指定文件数量，不需要逐个处理——一条命令搞定整个数据集。

---

## Slide 10: 可追溯性（45秒）

**画面**: 深色背景，JSONL 代码块 + 底部四个字段卡片

**旁白**:
> 科研数据处理的可追溯性至关重要。lmpsmart 的 JSONL 执行日志完整记录每一步操作。
>
> log_id 是全局唯一追溯码，timestamp 精确到毫秒，session_id 支持会话级追踪。
>
> 最重要的是 output_summary——它记录 DataFrame 的 shape 和 dtype，但不序列化数据本身。这样既能完整追溯，又不会因为数据量大使日志膨胀到不可控。

---

## Slide 11: CLI 与 API（45秒）

**画面**: 两列对比（左侧深色 CLI 代码 / 右侧深色 Python 代码）+ 底部六个子命令徽章

**旁白**:
> lmpsmart 同时提供 CLI 和 Python API。
>
> CLI 适合脚本化和自动化，一条命令解析数据，或者用 Agent 模式用自然语言驱动整个流程。
>
> Python API 适合集成到更大的分析管线——直接 import arrange、smooth、filter_outliers，像用 pandas 一样简单。
>
> 六个子命令：arrange 解析文件、smooth 平滑信号、filter 过滤异常值、config 查看配置、llm 设置语言模型、agent 运行 Agent 模式。

---

## Slide 12: lmpsmart vs 主流 LAMMPS 数据处理工具（1分钟）

**画面**: 五列对比表（OVITO / VMD / mdapy / MDAnalysis / lmpsmart），十行维度，lmpsmart 列全部高亮 ✓

**旁白**:
> lmpsmart 与 OVITO、VMD、mdapy、MDAnalysis 的核心差异在哪里？
>
> 这四个工具都支持计算派生物理量（RDF、RMSD 等）——OVITO 和 VMD 主要用于轨迹可视化和 3D 模型展示，也提供一些分析功能；mdapy 用 C++ 加速；MDAnalysis 在学术领域最流行。
>
> 但它们都没有：数据标准化输出（Bond 阈值、Cell 提取、Atom 映射、分子量）、9 种平滑算法、polyfit/lowess 曲线拟合、统计异常值过滤。
>
> 尤其值得注意的是，OVITO 和 VMD 都只能输出专业 3D 原子模型图，无法直接导出出版级曲线图——而 lmpsmart 内置 YAML 配置的 matplotlib，专业曲线一键生成。
>
> lmpsmart 的定位是：其他工具的上游数据清洗层——先把温度、压力、能量曲线洗干净，再交给 OVITO 计算 RDF、交给 VMD 渲染轨迹、交给 MDAnalysis 计算 RMSD。

---

## Slide 13: 总结（30秒）

**画面**: 深蓝色背景，三个统计数字 + 四个未来方向 + 底部 GitHub 地址

**旁白**:
> lmpsmart v1.0.0 核心特性：
>
> 8 种文件格式解析，8 大原创标准化输出（Bonds 阈值、Cell 提取、Atom 映射、分子量等），9 种平滑算法加曲线拟合，3 种统计异常值过滤，零硬编码的 YAML 配置驱动，Agent 自然语言接口，以及完整的 JSONL 执行日志。
>
> 未来方向：LLM 推理已落地三大场景（自然语言驱动、批量规划、智能 QA），后续扩展 Web UI、云端 Docker 部署、自动化统计验证。
>
> 项目地址：github.com/qgan2025/lmpsmart，采用 GPL-3.0 开源协议，欢迎 Star 和贡献。
>
> 谢谢大家！

---

## 录制提示

1. **语速**: 保持平稳，每分钟约 150-180 字
2. **切换画面**: 每个 slide 说完标题后暂停 1-2 秒，让观众看清画面
3. **代码演示**: 可在 Slide 10 处打开终端，实际演示 `python -m lmpsmart --help`
4. **录制工具**: OBS Studio（免费，支持多场景切换）
5. **导出格式**: MP4，1080p，H.264，码率 8-10 Mbps
