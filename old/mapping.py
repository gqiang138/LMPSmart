import glob, re, os, sys
import pandas as pd
import dask.dataframe as dd
import numpy as np
from scipy.signal import savgol_filter, butter, filtfilt
from scipy.interpolate import UnivariateSpline
from statsmodels.nonparametric.smoothers_lowess import lowess
import pywt    # pywavelets
from core.manual import *
import seaborn as sns
import matplotlib.pyplot as plt
from pykalman import KalmanFilter  # pip install pykalman

def preprocessing(typelist0, dictfile, path0, dict0, rule0):
    typelist1 = ['dumpbonds', 'chemreac', 'chemspec']
    for type0 in typelist0:
        jfile = glob.glob(path0 + dictfile[type0])[0].replace('\\','/')
        if type0 in ['log', 'dump', 'bonds', 'dumpbonds', 'cell', 'species', 'reacspecies', 'reacspace', 'pos', 'varxmd', 'rmsd', 'chunk','msxcd']:
            if type0 in ['dump', 'bonds']:
                try: 
                    df0 = dd.read_csv(jfile)
                    df0 = df0.compute()
                except:
                    df0 = autocode(jfile, 'pandas')      
            else: df0 = autocode(jfile, 'pandas')
            if type0 =='bonds':
                df0 = df0[df0['bo']-df0['bocutoff']>=0]
            elif type0 == 'reacspecies': 
                for item in df0.columns.tolist():
                    if item not in ['frame','time','weight','phase','molecule','moleculesmile','smierror']:
                        try: df0[item] = df0[item].apply(eval)
                        except: pass
            elif type0 == 'reacspace':            
                for k in set(df0.columns.tolist())-set(['frame','time','reaction','reactionsmile','reactiontype','phase_change']):
                    try: df0[k] = df0[k].apply(eval)
                    except: pass
            elif type0 == 'varxmd':
                df0['reaction'] = df0['reaction'].apply(lambda x:list_react_nosub([x], rule0))
        elif type0 == 'stress':
            df0 = pd.read_csv(jfile, sep=' +', skiprows=1, names=["strain", "stress"])
        elif len([type0 for i in typelist1 if i in type0])>0:
            df0 = autocode(jfile, 'pandas')
            if 'dumpbonds' in type0:
                if type0.split('.')[1] == 'bl':
                    df0 = df0[df0['blcutoff']-df0['bl']>=0]     # 用键长阈值筛选成键原子对。   
                elif type0.split('.')[1] == 'bo':
                    df0 = df0[df0['bocutoff']-df0['bo']<=0]     # 用键级阈值筛选成键原子对。
        elif 'ovito' in type0:
            df0 = pd.read_excel(jfile, sheet_name=re.split("ovito",type0)[1], header=0)
        elif 'neb' in type0:
            df0 = pd.read_excel(jfile, sheet_name=re.split("neb",type0)[1], header=0)
        else:
            df0 = autocode(jfile, 'pandas')
            df0.columns = [cm.strip() for cm in df0.columns]  # remove space in column names.
        dict0[type0] = df0
    return dict0

def smooth(data, method='moving_avg', **kwargs):
    """  
    Parameters:
    -----------
    data : array-like
        输入数据（list/pandas series/np.array），长度建议≥10以获得较好效果
    method : str
    -----------
    data : array-like
        输入数据（list/pandas series/np.array），长度建议≥10以获得较好效果
    method : str
        平滑方法选项：
        - 'segment_spline' : 分段样条拟合（适合相变数据）
        - 'adaptive_kalman' : 自适应卡尔曼滤波（需安装pykalman）
        - 'physics_constrained' : 物理约束滤波（需提供timestep）
        - 'robust_lowess' : 稳健局部回归
        - 'dynamic_wavelet' : 时变小波阈值
        - 'moving_avg': np.convolve滑动平均（适合快速降噪，但可能模糊突变特征）
        - 'savgol': Savitzky-Golay滤波（保留峰值特征，适合光谱数据）
        - 'wavelet': 小波去噪（适合非平稳信号，处理突变效果好）
        - 'ewma': 指数加权移动平均 (需 alpha 或 span)
    **kwargs :
        方法专用参数：
        # segment_spline
        - spline_threshold : float (默认0.2)
            梯度突变阈值（0.1-0.5），值越大对突变越不敏感
        - spline_s : float (默认0.5)
            平滑强度（0=精确拟合，1=强平滑）
        
        # adaptive_kalman
        - process_noise : float (默认0.1)
            初始过程噪声（1e-6~1.0），值越大跟踪越快但噪声越多
        
        # physics_constrained
        - timestep : float (必需)
            模拟步长(fs)，金属体系建议0.5-2
        - cutoff_freq : float (默认0.2)
            截断频率(THz)，通常取体系最高振动频率的1/10
        
        # robust_lowess
        - lowess_frac : float (默认0.1)
            平滑窗口比例（0.05-0.5），值越大平滑越强
        - lowess_it : int (默认3)
            离群值处理迭代次数（1-5次）
        
        # dynamic_wavelet
        - base_thresh : float (默认0.1)
            基础阈值系数（0.05-0.3），值越大去噪越强
        - dwt_sensitivity : float (默认2.0)
            动态敏感度（0-3），值越大保留突变越多

        # moving_avg移动平均参数
        - window_size : int (默认5)
            窗口越大平滑效果越强，但边缘失真越明显
        - padding : str (默认'edge')
            边界处理方式：
            - 'edge' : 用首尾值填充（保边缘）
            - 'constant' : 用固定值填充（需配合pad_value参数）
            - None : 快速模式（边缘可能失真）
        - pad_value : float (默认0)
            当padding='constant'时的填充值

        # Savitzky-Golay参数
        - window_length : int (自动计算为≤数据长度的最大奇数)
            窗口长度应大于polyorder，建议值5-21：
            - 较小值：保留细节但降噪弱
            - 较大值：平滑强但可能过拟合
        - polyorder : int (默认2)
            多项式阶数，建议2-4：
            - 低阶：平滑效果好
            - 高阶：保留峰值特征

        # wavelet小波去噪参数
        - wavelet : str (默认'db4')
            小波基类型，可选：
            - 'haar' : 快速计算（适合阶跃信号）
            - 'db1'-'db20' : 不同消失矩（db4最常用）
            - 'sym2'-'sym20' : 对称小波（适合光滑信号）
            - 'coif1'-'coif5' : 科伊夫小波（平衡时频特性）
        - level : int (自动计算最大有效层数，默认5)
            分解层数建议：
            - 1-3层：高频噪声去除
            - 4-6层：深层特征提取
        - threshold : float (默认0.1)
            阈值系数（乘以信号标准差）：
            - 0.05-0.2 : 轻度降噪
            - 0.3-0.5 : 强降噪（可能丢失特征）
        - threshold_mode : str (默认'soft')
            阈值模式：'soft'（平滑过渡）/ 'hard'（锐利截断）

        # ewma
        - alpha : float, optional (默认: 0.5)
            平滑因子，范围 (0, 1]。值越大，近期数据权重越高（平滑程度越低）。
            - 0：完全忽略当前数据（无意义）
            - 1：仅使用当前数据（不平滑）
        - span : int, optional (默认: 0)
            等效窗口跨度，通过公式 `alpha = 2/(span + 1)` 自动计算 alpha。
            - 若同时指定 alpha 和 span，span 优先级更高
            - 典型值：span=5 对应约 5 个数据点的等效权重范围
        - min_periods : int, optional (默认: 0)
            结果有效的最小数据点数。窗口内数据不足时返回 NaN。
            - 0：从第1个点开始计算（可能因数据少导致初期波动）
            - N：前 N-1 个点返回 NaN
        - adjust : bool, optional (默认: True)
            是否动态归一化权重：
            - True：保证权重和=1，避免初期数据低估（推荐）
            - False：直接递推计算，速度更快但初期精度低

    Returns:
    --------
    smoothed_data : 
        与输入类型一致的平滑后数据
    Examples:
    ---------
    >>> # segment_spline检测LAMMPS体积相变
    >>> smooth(vol, method='segment_spline', spline_threshold=0.3)
    >>> # adaptive_kalman 示例 (非稳态体系跟踪)，适用于温度/压力剧烈波动的NPT模拟
    >>> smoothed = smooth(data, method='adaptive_kalman', process_noise=0.05)  # 初始噪声设为数据方差的5%
    >>> # physics_constrained含物理约束的滤波
    >>> smooth(temp, method='physics_constrained', timestep=1.0, cutoff_freq=0.5)    
    >>> # robust_lowess处理异常值
    >>> smooth(press, method='robust_lowess', lowess_frac=0.2, lowess_it=4)    
    >>> # dynamic_wavelet 示例 (多尺度特征提取), 适用于同时包含慢扩散和快振动的体系
    >>> smoothed = smooth(data, method='dynamic_wavelet',
    ...                   base_thresh=0.08,    # 基础阈值降低以保留弱信号
    ...                   dwt_sensitivity=2.5) # 提高对突变的敏感度
    >>> # 移动平均（强平滑）
    >>> smooth(data, window_size=11, padding='edge')
    >>> # Savitzky-Golay（保留峰值）
    >>> smooth(data, method='savgol', window_length=15, polyorder=3)
    >>> # 小波去噪（处理突变）
    >>> smooth(data, method='wavelet', wavelet='sym8', threshold=0.2)
    >>> # 指数加权移动平均（强平滑）
    >>> smooth(data, method='ewma', alpha=0.5, span=0, min_periods=0, adjust=True)
    """
    # 输入校验和统一类型处理
    # 新增pandas支持
    if hasattr(data, 'values'):  # 检测pandas Series/DataFrame列
        orig_index = data.index
        orig_name = getattr(data, 'name', None)
        data = data.values  # 提取numpy数组
    elif not isinstance(data, (list, np.ndarray)):
        raise ValueError("# Warning: Input must be list, numpy array or pandas Series/DataFrame column!")
    else:
        orig_index = None
        orig_name = None
        data = np.asarray(data)  # 统一转为numpy数组
    orig_type = type(data)

    if len(data) < 2:
        return orig_type(data) if orig_type is list else data
    # 方法分派
    try:
        if method == 'segment_spline':
            threshold = kwargs.get('spline_threshold', 0.2)
            s = kwargs.get('spline_s', 0.5)
            grad = np.gradient(data)
            std_grad = np.std(grad)
            break_points = np.where(np.abs(grad) > threshold*std_grad)[0]
            
            x = np.arange(len(data))
            if len(break_points) > 0:
                spl = UnivariateSpline(x, data, k=3, s=s)
                smoothed = spl(x)
            else:
                smoothed = data

        elif method == 'adaptive_kalman':
            if KalmanFilter is None:
                raise ImportError("pykalman package required for Kalman filtering")
            process_noise = kwargs.get('process_noise', 0.1)
            kf = KalmanFilter(
                initial_state_mean=data[0],
                observation_covariance=1,
                transition_covariance=process_noise,
                transition_matrices=[1]
            )
            state_means, _ = kf.filter(data)
            residuals = data - state_means.flatten()
            adaptive_noise = np.clip(np.std(residuals)*0.1, 1e-6, 0.5)
            kf.transition_covariance = adaptive_noise
            smoothed = kf.smooth(data)[0].flatten()

        elif method == 'physics_constrained':
            if 'timestep' not in kwargs:
                raise ValueError("timestep (in fs) must be provided for physics_constrained method")
            timestep = kwargs['timestep']
            cutoff_freq = kwargs.get('cutoff_freq', 0.2)
            fs = 1000/timestep  # 采样频率(THz)
            nyquist = 0.5 * fs
            normal_cutoff = cutoff_freq / nyquist
            b, a = butter(4, normal_cutoff, btype='low', analog=False)
            smoothed = filtfilt(b, a, data)

        elif method == 'robust_lowess':
            frac = kwargs.get('lowess_frac', 0.1)
            it = kwargs.get('lowess_it', 3)
            x = np.arange(len(data))
            smoothed = lowess(data, x, frac=frac, it=it, 
                            is_sorted=True, return_sorted=False)
            
        elif method == 'dynamic_wavelet':
            base_thresh = kwargs.get('base_thresh', 0.1)
            sensitivity = kwargs.get('dwt_sensitivity', 2.0)
            coeffs = pywt.wavedec(data, 'db4', level=5)
            
            for i in range(1, len(coeffs)):
                window_size = len(coeffs[i])//10 or 1
                local_std = np.convolve(
                    np.abs(coeffs[i]), 
                    np.ones(window_size)/window_size, 
                    mode='same'
                )
                thresh = base_thresh * (1 + sensitivity*(local_std/np.max(local_std)-0.5))
                coeffs[i] = pywt.threshold(coeffs[i], thresh, 'soft')
            
            smoothed = pywt.waverec(coeffs, 'db4')[:len(data)]        
        
        elif method == 'moving_avg':
            window_size = kwargs.get('window_size', 5)
            if window_size <= 1:
                return orig_type(data) if orig_type is list else data
            padding = kwargs.get('padding', 'edge')
            if padding == 'edge':
                pad_left = np.full((window_size-1)//2, data[0])
                pad_right = np.full((window_size-1)//2, data[-1])
                if window_size % 2 == 0:
                    pad_right = np.append(pad_right, data[-1])
                padded_data = np.concatenate([pad_left, data, pad_right])
                # mode='valid'确保卷积操作只在窗口完全覆盖数据时进行。
                smoothed = np.convolve(padded_data, np.ones(window_size)/window_size, mode='valid')
            else:
                smoothed = np.convolve(data, np.ones(window_size)/window_size, mode='same')

        elif method == 'savgol':
            window_length = kwargs.get('window_length', min(11, len(data)//2*2-1))
            polyorder = kwargs.get('polyorder', 2)
            if window_length > len(data):
                window_length = len(data) if len(data) % 2 else len(data)-1
            smoothed = savgol_filter(data, window_length, polyorder)
        
        elif method == 'wavelet':
            wavelet = kwargs.get('wavelet', 'db4')
            max_level = pywt.dwt_max_level(len(data), pywt.Wavelet(wavelet).dec_len)
            level = min(kwargs.get('level', 5), max_level)
            threshold = kwargs.get('threshold', 0.1) * np.max(np.abs(data - np.mean(data)))
            coeffs = pywt.wavedec(data, wavelet, level=level)
            coeffs[1:] = [pywt.threshold(c, threshold, mode='soft') for c in coeffs[1:]]
            smoothed = pywt.waverec(coeffs, wavelet)[:len(data)]  # 强制对齐原始长度，避免多一个值。
        
        # 指数加权移动平均 (直接嵌入)
        elif method == 'ewma':
            alpha = kwargs.get('alpha', 0.3)
            span = kwargs.get('span', None)
            adjust = kwargs.get('adjust', True)  # 实际生效的参数
            min_periods = kwargs.get('min_periods', 1)
            # 参数转换
            if span is not None:
                alpha = 2 / (span + 1)
            
            # 核心计算（考虑adjust参数）
            result = np.empty_like(data, dtype=float)
            result[:] = np.nan
            
            if len(data) > 0:
                result[0] = data[0]  # 第一个值不调整
                
                if adjust:  # 权重归一化模式
                    weighted_sum = data[0]
                    sum_weights = 1.0
                    for i in range(1, len(data)):
                        weighted_sum = alpha * data[i] + (1-alpha) * weighted_sum
                        sum_weights = alpha + (1-alpha) * sum_weights
                        result[i] = weighted_sum / sum_weights  # 归一化
                else:       # 简单递推模式
                    for i in range(1, len(data)):
                        result[i] = alpha * data[i] + (1-alpha) * result[i-1]
                
                # 处理min_periods
                if min_periods > 1:
                    result[:min_periods-1] = np.nan
                    
            return result   
        else:
            raise ValueError(f"# Error: Unsupported smoothing method: {method}")
    except Exception as e:
        raise ValueError(f"# Warning: Smoothing failed: {str(e)}") from e
    
    # 返回结果时恢复pandas特性
    if orig_index is not None:
        return pd.Series(smoothed, index=orig_index, name=orig_name)
    return smoothed.tolist() if orig_type is list else smoothed
# 对于大型pandas数据，GB级数据推荐预处理
def smooth_column(series, **kwargs):
    arr = series.to_numpy(copy=False)  # 避免内存复制
    smoothed = smooth(arr, **kwargs)
    return pd.Series(smoothed, index=series.index)

# @2025/5/20：定义多列IQR过滤函数，过滤异常值。
def remove_deviations(
    df, 
    time_col, 
    target_cols, 
    method='auto', 
    threshold=3,
    visualize='yes',
    fast_mode='no',
    n_jobs=4,
    verbose=True
):
    """
    高性能组合异常值过滤函数 (完整修复版)
    
    参数：
        df: 输入DataFrame
        time_col: 时间分组列名
        target_cols: 需要处理的数值列列表
        method: 'auto'/'zscore'/'mad'/'iqr' 或方法列表
        threshold: 异常判定阈值
        visualize: 是否显示可视化, 'yes'/'no'
        fast_mode: auto/yes/no
                  ('auto':自动检测大数据, yes:强制启用优化, no:禁用优化)
        n_jobs: 并行计算线程数
        verbose: 是否打印处理进度
    返回：
        过滤后的DataFrame (保留原始索引)
    """
    # ========== 数据预处理 ==========
    # 检查输入列是否存在
    missing_cols = [col for col in [time_col] + target_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"列不存在: {missing_cols}")
    # 处理缺失值
    df = df.dropna(subset=[time_col] + target_cols).copy()
    # ========== 性能优化预处理 ==========
    # 自动检测大数据模式
    if fast_mode == 'auto' and len(df) > 1e6:
        if verbose:
            print("⚡ 大数据模式激活 (样本量: {:,})".format(len(df)))
        fast_mode = True
    elif fast_mode == 'yes':
        fast_mode = True
    elif fast_mode == 'no':
        fast_mode = False
    # 列数据预转换 (减少内存消耗)
    if fast_mode:
        for col in target_cols:
            if pd.api.types.is_float_dtype(df[col]):
                df[col] = df[col].astype('float32')
    # ========== 方法选择逻辑 ==========
    if method == 'auto':
        if verbose:
            print("🔍 自动检测数据分布...")
        with ThreadPoolExecutor(max_workers=min(n_jobs, len(target_cols))) as executor:
            futures = []
            for col in target_cols[:3]:  # 最多检查前3列
                sample = df.groupby(time_col)[col].apply(lambda x: x.sample(min(100, len(x))))
                futures.append(executor.submit(normaltest, sample))
            p_values = [f.result().pvalue for f in futures]
        if any(p < 0.05 for p in p_values):
            method = ['mad', 'iqr']  # 非正态分布使用鲁棒方法
            if verbose:
                print("📊 检测到非正态分布，选择鲁棒方法: MAD + IQR")
        else:
            method = ['zscore', 'iqr']
            if verbose:
                print("📊 数据接近正态分布，选择标准方法: Z-Score + IQR")
    elif isinstance(method, str):
        method = [method]
    # ========== 核心过滤逻辑 ==========
    def compute_zscore(group):
        if fast_mode and len(group) > 1e5:
            # 近似计算 (Welford算法)
            mean = group.mean()
            std = np.sqrt(group.var(ddof=1))
            return np.abs((group - mean) / std)
        return np.abs((group - group.mean()) / group.std())
    def compute_mad(group):
        med = np.median(group)
        if fast_mode and len(group) > 1e5:
            # 使用百分位数近似中位数
            mad_val = 1.4826 * np.percentile(np.abs(group - med), 50)
        else:
            mad_val = 1.4826 * np.median(np.abs(group - med))
        return np.abs(0.6745 * (group - med) / mad_val)
    def compute_iqr(group):
        if fast_mode and len(group) > 1e5:
            q1, q3 = norm.ppf([0.25, 0.75], loc=group.mean(), scale=group.std())
        else:
            q1, q3 = group.quantile([0.25, 0.75])
        iqr = q3 - q1
        lower = q1 - threshold*iqr
        upper = q3 + threshold*iqr
        return (group >= lower) & (group <= upper)
    # 方法映射字典
    method_funcs = {
        'zscore': compute_zscore,
        'mad': compute_mad,
        'iqr': compute_iqr
    }
    final_mask = pd.Series(True, index=df.index)
    method_results = {}
    if verbose:
        print("🚀 开始并行计算... (方法: {})".format(", ".join(method)))
    with ThreadPoolExecutor(max_workers=n_jobs) as executor:
        for m in method:
            if m not in method_funcs:
                continue
            temp_masks = []
            futures = {}
            # 并行计算各列
            for col in target_cols:
                group = df.groupby(time_col)[col]
                # 修复点：直接传递函数对象
                futures[col] = executor.submit(
                    lambda g, func: g.transform(func),
                    group,
                    method_funcs[m]
                )
            # 收集结果
            for col, future in tqdm(futures.items(), desc=f"{m.upper()}计算", disable=not verbose):
                res = future.result()
                if m in ['zscore', 'mad']:
                    temp_masks.append(res <= threshold)  # 注意这里已经是绝对值
                else:  # iqr
                    temp_masks.append(res)
            method_results[m] = pd.concat(temp_masks, axis=1).all(axis=1)
            final_mask &= method_results[m]
    
    # ========== 结果处理 ==========
    # 过滤结果统计
    if verbose:
        report = ''
        report += "\n=== Filter Report ===\n"
        report += f" Initial data: {len(df):,} | Keep: {final_mask.sum():,} | Remove: {len(df)-final_mask.sum():,}\n"
        print("\n=== Filter Report ===")
        print(f"📊 Initial data: {len(df):,} | Keep: {final_mask.sum():,} | Remove: {len(df)-final_mask.sum():,}")
        for m, mask in method_results.items():
            report += f"  - {m.upper():<7} Remove: {len(df)-mask.sum():,}\n"
            print(f"  - {m.upper():<7} Remove: {len(df)-mask.sum():,}")
    # 可视化
    if visualize=='yes' and len(target_cols) > 0:
        plt.figure(figsize=(15, 5*len(target_cols)))
        for i, col in enumerate(target_cols, 1):
            plt.subplot(len(target_cols), 1, i)
            # 原始数据背景
            plt.scatter(df[time_col], df[col], 
                       c='lightgray', alpha=0.3, 
                       label=f'Initial Data (n={len(df)})')
            # 保留数据
            plt.scatter(df.loc[final_mask, time_col], 
                       df.loc[final_mask, col],
                       c='red', s=10, alpha=0.5,
                       label=f'Keep Data (n={final_mask.sum()})')
            # 异常点标注 (采样显示)
            colors = {'zscore':'blue', 'mad':'green', 'iqr':'purple'}
            for m in method:
                if m in method_results:
                    outliers = df[~method_results[m]].sample(min(100, len(df[~method_results[m]])))
                    if not outliers.empty:
                        plt.scatter(outliers[time_col], outliers[col],
                                   c=colors.get(m, 'orange'), 
                                   marker='x', s=30,
                                   label=f'{m}Removed Points')
            plt.title(f'{col} Filter Outliers (Metohds: {", ".join(method)})')
            plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        plt.show()
    return df[final_mask].copy(), df[~df.index.isin(df[final_mask].copy().index)], report

# @2025/11/8: define to filter y value.
def thirdfilter(df0, column0, zitem, k, groupbylist, ylist):
    def thirdfilter0(df0, column0, value0):
        if not df0.empty and isinstance(df0[column0].iloc[0], list):
            return df0[column0].apply(lambda x: value0 in x)
        else:
            return df0[column0]==value0
    if zitem != '':
        df0 = df0[thirdfilter0(df0, column0, zitem)]
    if k == 'first':
        df1 = df0[ylist].groupby(groupbylist).first().reset_index(drop=False)
    elif k =='sum':
        df1 = df0[ylist].groupby(groupbylist).sum().reset_index(drop=False)
    elif k == 'max':
        df1 = df0[ylist].groupby(groupbylist).max().reset_index(drop=False)
    elif k == 'min':
        df1 = df0[ylist].groupby(groupbylist).min().reset_index(drop=False)
    elif k == 'std':
        df1 = df0[ylist].groupby(groupbylist).std().reset_index(drop=False)
    elif k == 'mean':
        df1 = df0[ylist].groupby(groupbylist).mean().reset_index(drop=False)
    return df1

if __name__ == '__main__':
    tests = ['smooth', 'remove_deviations']
    test = tests[0]

    path = 'f:\\ganqiang\\Phase\\anneal\\ecl20temp1\\data\\dataoflog.csv'
    df = pd.read_csv(path)

    if test == tests[0]:
        # 检测LAMMPS体积相变
        df['VolumeA'] = smooth(df['Volume'], method='segment_spline', spline_threshold=0.3, spline_s=0.2)
        # adaptive_kalman 示例 (非稳态体系跟踪)，适用于温度/压力剧烈波动的NPT模拟
        df['VolumeB'] = smooth(df['Volume'], method='adaptive_kalman', process_noise=0.05)  # 初始噪声设为数据方差的5%        
        # 含物理约束的滤波
        df['VolumeC'] = smooth(df['Volume'], method='physics_constrained', timestep=0.1, cutoff_freq=0.5)
        # 处理异常值
        df['VolumeD'] = smooth(df['Volume'], method='robust_lowess', lowess_frac=0.3, lowess_it=4)        
        # dynamic_wavelet 示例 (多尺度特征提取), 适用于同时包含慢扩散和快振动的体系
        df['VolumeE'] = smooth(df['Volume'], method='dynamic_wavelet', base_thresh=0.3, dwt_sensitivity=2.5)    # 基础阈值降低以保留弱信号,提高对突变的敏感度
        # 移动平均（强平滑）
        df['VolumeF'] = smooth(df['Volume'], method='moving_avg', padding='edge', window_size=1000)
        # Savitzky-Golay（保留峰值）
        df['VolumeG'] = smooth(df['Volume'], method='savgol', polyorder=4, window_length=1000) 
        # 小波去噪（处理突变）
        df['VolumeH'] = smooth(df['Volume'], method='wavelet', wavelet='haar', threshold=0.8, threshold_mode='hard')
        # 指数加权移动平均（强平滑）
        df['VolumeI'] = smooth(df['Volume'], method='ewma', alpha=0.5, span=20, min_periods=10, adjust=False)
        # 保存结果
        df.to_csv('f:\\ganqiang\\Phase\\anneal\\ecl20temp1\\data\\abc.csv')
    elif test == tests[1]:
        # 使用示例
        df.to_csv('f:\\ganqiang\\Phase\\anneal\\ecl20temp1\\data\\abc.csv')
        # df2 = df[['Temp','Volume','VolumeA','VolumeB','VolumeC']]
        # df2.set_index('Temp', inplace=True)
        # sns.lineplot(data=df2)
        # plt.savefig('f:\\ganqiang\\Phase\\anneal\\ecl20temp1\\data\\log.png')
    elif test == tests[1]:
        # 使用示例
        df2, dfremoved, report = remove_deviations(df, time_col='time',
            target_cols=['x', 'y', 'z'],
            method='auto', fast_mode='auto', n_jobs=4, visualize='yes')
        dfremoved.to_csv("F:\\rensu\\three\\try\\45\\9\\wave0\\dataofdump.wave3.front.removed.csv",index=False)
        df2.to_csv("F:\\rensu\\three\\try\\45\\9\\wave0\\dataofdump.wave3.front.clean.csv",index=False)
        with open("F:\\rensu\\three\\try\\45\\9\\wave0\\filterreport.txt",'w', encoding='utf-8') as f:
            f.write(report)