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
> 分子动力学模拟，特别是使用 ReaxFF 反应力场时，会产生海量数据：热力学输出、键拓扑演化、原子轨迹、化学物种浓度。
>
> 传统方案依赖 OVITO、VMD 等 GUI 工具，或者定制 Python 脚本——问题是参数硬编码，无法批量处理，更没有可追溯性。
>
> lmpsmart 从根本上解决这三个问题：YAML 配置驱动零硬编码，Glob 批量匹配，JSONL 执行日志完整记录每一步操作。

---

## Slide 3: 系统架构（1分钟）

**画面**: 三层流程图（INPUT → Arrange Layer → DataFrame → Mapping Layer → OUTPUT）+ 右侧 Agent Controller

**旁白**:
> lmpsmart 采用三层架构设计。
>
> 第一层是 Arrange Layer，接收 LAMMPS 文件，通过 8 种专用解析器，将原始数据转换为 pandas DataFrame——所有解析规则完全由 YAML 配置驱动，没有硬编码。
>
> 第二层是 Mapping Layer，对 DataFrame 应用 9 种平滑算法和 3 种异常值过滤方法。
>
> 第三层是 Agent Controller，它接收自然语言目标，通过 plan_from_goal() 规划工具链，execute() 执行每一步，所有操作自动记录到 JSONL 日志。

---

## Slide 4: Arrange Layer（45秒）

**画面**: 4×2 卡片网格，每个卡片有颜色边框、图标、名称和描述

**旁白**:
> Arrange Layer 支持 8 种文件格式。
>
> Log 解析热力学输出，Bonds 解析 ReaxFF 键序分析，Bonds 支持 30 种键类型。
>
> Dump 处理原子轨迹，Cell 提取晶胞维度变化，Species 追踪化学物种。
>
> POS 兼容 POSCAR 晶体格式，OVITO 处理可视化中间导出，General 自动检测 CSV 和 TSV。
>
> 所有格式支持 Glob 通配符——输入目录中有多少文件，自动全部解析，自动输出 split 编号。

---

## Slide 5: Mapping Layer（1分钟）

**画面**: 深色背景，三个平滑算法分类组 + 底部三个过滤方法

**旁白**:
> Mapping Layer 实现 9 种平滑算法，分三类。
>
> 物理约束类包括：segment_spline 在拐点分割后拟合样条；adaptive_kalman 用卡尔曼滤波自适应估计噪声；physics_constrained 用约束最小二乘施加物理约束。
>
> 统计平滑类包括：robust_lowess 用局部加权散点平滑加双平方鲁棒估计；moving_avg 滑动平均快速去噪；ewma 指数加权移动平均。
>
> 频域处理类包括：小波变换 wavelet、动态小波 denoising dynamic_wavelet、以及 Savitzky-Golay 滤波器 savgol——后者在保持峰形方面特别出色。
>
> 三种异常值过滤方法：Z-score、MAD 和 IQR，分别适用于不同噪声分布场景。

---

## Slide 6: Agent 架构（1分钟）

**画面**: 四步流程图（Goal → plan_from_goal → execute → JSONL）+ 三列工具分类

**旁白**:
> lmpsmart 的核心创新是将 Tkinter GUI 转化为 Agent 架构。
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

## Slide 11: GUI vs Agent（45秒）

**画面**: 表格对比（六行维度），Agent 列高亮显示 ✓

**旁白**:
> 为什么 Agent 架构优于传统 GUI？
>
> GUI 是用户界面，不是 Agent——它只是把用户点击映射到函数调用，没有推理、没有规划、没有自主决策。
>
> lmpsmart Agent 能从自然语言目标自主规划工具链，支持批量处理，自动记录可追溯日志，还能接入 LLM 做更智能的推理。这是 GUI 架构根本无法实现的。

---

## Slide 12: 总结（30秒）

**画面**: 深蓝色背景，三个统计数字 + 四个未来方向 + 底部 GitHub 地址

**旁白**:
> lmpsmart v1.0.0 核心特性：
> 8 种文件格式解析，9 种平滑算法加 3 种过滤方法，零硬编码的 YAML 配置驱动，以及完整的 JSONL 执行日志。
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
