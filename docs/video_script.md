# lmpsmart v1.0.0 演示视频脚本

## 基本信息
- **时长**: 8-10 分钟
- **风格**: 技术演示 + 竞赛汇报
- **语言**: 中文旁白 + 英文代码

---

## Slide 1: 开场（30秒）

**画面**: 深蓝色背景，大标题 lmpsmart，装饰性分子六边形图案

**旁白**:
> 大家好，我是 Qiang Gan。今天向大家介绍 lmpsmart v1.0.0——一个基于 Agent 架构的 LAMMPS 分子动力学数据处理工具。这是一个开源项目，采用 GPL-3.0 协议发布。

---

## Slide 2: 背景与问题（1分钟）

**画面**: 三个卡片（海量异构数据 / 传统方案局限 / 无可追溯性）+ 底部解决方框

**旁白**:
> 分子动力学模拟，特别是使用 ReaxFF 反应力场时，会产生海量非标准数据：热力学输出、键拓扑演化、原子轨迹、化学物种浓度。
>
> 传统方案依赖 OVITO、VMD 等工具计算派生物理量——但它们无法处理原始数据的标准化、去噪和过滤。
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
> plan_from_goal() 将目标分解为工具调用序列——目前基于关键词匹配，未来可替换为 LLM 推理。
>
> execute() 从 TOOL_REGISTRY 调用工具函数，18 个工具覆盖：Arrange、Read 八种格式、Mapping、以及化学计算。
>
> 每一步执行都写入 JSONL 日志——包含 log_id、时间戳、会话 ID、输入摘要、输出摘要、执行耗时。DataFrame 不序列化，只记录 shape 和 dtype，防止日志膨胀。

---

## Slide 7: YAML 配置（45秒）

**画面**: 左侧深色代码块（YAML 配置片段）+ 右侧四个功能卡片

**旁白**:
> lmpsmart 零硬编码的秘密在于 configs/default.yaml。
>
> 这里配置了 30 种键类型的键序阈值和键长阈值，8 种文件的 Glob 匹配模式，每个元素的化学键数上限，以及时间步长等物理参数。
>
> Pydantic 模型在加载时自动验证 YAML——配置错误在启动时就报错，而不是运行到一半崩溃。

---

## Slide 8: Glob 批量匹配（30秒）

**画面**: 左侧输入文件夹（多个 log 文件）+ 箭头 → 右侧输出（split 编号文件）

**旁白**:
> Glob 批量匹配是 lmpsmart 的一大特色。输入目录有多少文件，一次性全部解析，自动 split 编号命名。
>
> 不需要手动指定文件数量，不需要逐个处理——一条命令搞定整个数据集。

---

## Slide 9: 可追溯性（45秒）

**画面**: 深色背景，JSONL 代码块 + 底部四个字段卡片

**旁白**:
> 科研数据处理的可追溯性至关重要。lmpsmart 的 JSONL 执行日志完整记录每一步操作。
>
> log_id 是全局唯一追溯码，timestamp 精确到毫秒，session_id 支持会话级追踪。
>
> 最重要的是 output_summary——它记录 DataFrame 的 shape 和 dtype，但不序列化数据本身。这样既能完整追溯，又不会因为数据量大使日志膨胀到不可控。

---

## Slide 10: CLI 与 API（45秒）

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

## Slide 11: lmpsmart vs 主流 LAMMPS 数据处理工具（1分钟）

**画面**: 四列对比表（OVITO / mdapy / MDAnalysis / lmpsmart），十行维度，lmpsmart 列全部高亮 ✓

**旁白**:
> lmpsmart 与 OVITO、mdapy、MDAnalysis 的核心差异在哪里？
>
> 这三个工具都是计算派生物理量的——OVITO 的 RDF、Voronoi 分析、位错分析，mdapy 的 CHILL+ 算法，MDAnalysis 的 RMSD、RDF。
>
> 但它们都没有：数据标准化输出（Bond 阈值、Cell 提取、Atom 映射、分子量）、9 种平滑算法、polyfit/lowess 曲线拟合、统计异常值过滤、专业出版级曲线绘图、以及 Agent 自然语言接口。
>
> OVITO 只能输出专业 3D 原子模型图，无法直接导出出版级曲线图；lmpsmart 内置 YAML 配置的 matplotlib，专业曲线一键生成。
>
> lmpsmart 的定位是：其他工具的上游数据清洗层——先把温度、压力、能量曲线洗干净，再交给 OVITO 计算 RDF、交给 MDAnalysis 计算 RMSD。

---

## Slide 12: 总结（30秒）

**画面**: 深蓝色背景，三个统计数字 + 四个未来方向 + 底部 GitHub 地址

**旁白**:
> lmpsmart v1.0.0 核心特性：
>
> 8 种文件格式解析，8 大原创标准化输出（Bonds 阈值、Cell 提取、Atom 映射、分子量等），9 种平滑算法加曲线拟合，3 种统计异常值过滤，零硬编码的 YAML 配置驱动，Agent 自然语言接口，以及完整的 JSONL 执行日志。
>
> 未来方向：LLM 推理替换关键词匹配、Web UI、云端 Docker 部署、自动化统计验证。
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
