#-*- coding:utf-8 -*-
import warnings
warnings.filterwarnings('ignore')               # 忽略警告
import re, os, sys, glob, math, time, warnings, platform, shutil, tempfile, json, datetime, traceback, logging, gc  #, pygraphviz
# linux下支持中文。
if platform.system().lower() == 'linux':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
logging.getLogger('matplotlib.legend').setLevel(logging.ERROR)  # 完全禁用该记录器
import tkinter as tk
from tkinter import ttk
from tkinter import *
from tkinter.filedialog import *
from tkinter.ttk import *
from tkinter.messagebox import *
import numpy as np
import pandas as pd
import matplotlib as mpl
mpl.use('TkAgg') # 解决报错_tkinter.TclError: invalid command name ".!canvas"
from matplotlib import rcParams   #font_manager
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.animation import FuncAnimation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.ticker import AutoMinorLocator
import matplotlib.ticker as ticker
from matplotlib.font_manager import FontProperties
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.cm as cm
from collections import Counter
from pyvis.network import Network
from PIL import ImageDraw
import PIL.Image as Image0
import seaborn as sns
import statsmodels.api as sm
import networkx as nx
from multiprocessing import Pool, freeze_support, cpu_count
from openpyxl import load_workbook
from functools import partial
lowess = sm.nonparametric.lowess
# if platform.system() == 'Windows':
# from reacnetgenerator import ReacNetGenerator
# from reacnetgenerator.tools import calculate_rate
from rdkit.Chem import Draw
from openbabel import openbabel as ob
from openbabel import pybel
from pathlib import Path
from math import tan
from core import *
from scripts import *
from gui import *
# Set up logging if not already set up
if 'logging' in globals():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
controller = TaskController()               # import from tkwindow.py

# 基础路径示例
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CORE_DIR = os.path.join(BASE_DIR, "core")
SCRIPTS_DIR = os.path.join(BASE_DIR, "scripts")
UTILS_DIR = os.path.join(BASE_DIR, "utils")
if platform.system() == "Windows":
    LMPSETTING_PATH = os.path.join(UTILS_DIR, "lmpsetting.csv")
else:
    LMPSETTING_PATH = os.path.expanduser("~/Documents/lmpsetting.csv")
WEBVIEWER_PATH = os.path.join(SCRIPTS_DIR, "webviewer.py")
DEFAULT_PATH = os.path.join(CORE_DIR, "default.txt")

# 用法astring.translate(sub)
sub = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")
sup = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")
resub = str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")
resup = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹", "0123456789")

# 定义计算或分析函数
# 定义animateupdate函数，用于mapping。
def animateupdate(frame, df0, figtype0, *fargslist):
    df = df0[df0['frame']==frame].reset_index(drop=True)
    if figtype0 == 'isograph':
        fontset0, items0, axislimit0, title0, isoset0= fargslist
        X = df[items0[0][0]].values
        Y = df[items0[1][0]].values
        Z = df[items0[-1][0]].values
        plt.clf()    # 清空当前图形并开始绘制新的内容，而无需创建新的图形窗口。
        plt.tricontourf(X, Y, Z, levels=isoset0, cmap=mpl.cm.rainbow)  # cm.jet
        # 用盒子尺寸作为绘图坐标尺寸
        # plt.axis('scaled') #确保坐标轴的长度与坐标值范围一致
        plt.axis(axislimit0)
        # plt.rcParams['font.size'] = ticksize0           # 设置x,y,colorbar字号
        plt.xlabel(items0[0][1], fontproperties=fontset0)
        plt.ylabel(items0[1][1], fontproperties=fontset0)
        plt.colorbar().set_label(items0[-1][1], fontproperties=fontset0)
        if title0 !='':
            plt.title(eval(title0), fontproperties=fontset0)
        return plt.gcf()
    elif figtype0 in ['bar','line']:
        fontset0, items0, axislimit0, title0, barscale1 = fargslist
        x = df[items0[0][0]].values
        y = df[items0[1][0]].values
        plt.clf()    # 清空当前图形并开始绘制新的内容，而无需创建新的图形窗口。
        if figtype0 =='bar':
            plt.bar(x,y, width = barscale1)
        elif figtype0 =='line':
            plt.plot(x,y)
        plt.axis(axislimit0)
        plt.xlabel(items0[0][1], fontproperties=fontset0)
        plt.ylabel(items0[1][1], fontproperties=fontset0)
        # plt.tick_params(labelsize=ticksize0)
        if title0 !='':
            plt.title(eval(title0), fontproperties=fontset0)
        return plt.gcf()
    elif figtype0 == 'reacdraw':
        fig0, items0, dfdump0, axislimit0, title0, fontset0, ticksize0, styleset0, scatterscale0, rule0, axisoff0 = fargslist
        ax = fig0.add_subplot(111, projection='3d')
        time = format(df.loc[0,'time'],'.4f')      # 保留三维小数。
        reaction = list_react(list(set(df.loc[0,'reaction'])), rule0)
        reaction = '\n'.join(reaction)
        if len(items0) == 3:                     # 3D绘图
            # ax = fig0.add_subplot(111, projection='3d')
            if set(['xrange', 'yrange', 'zrange']).issubset(set(merge_list(items0, 2))):
                X = df[items0[0][0]].apply(lambda x: round((eval(x)[0]+eval(x)[1])/2,3)).values.tolist()
                Y = df[items0[1][0]].apply(lambda x: round((eval(x)[0]+eval(x)[1])/2,3)).values.tolist()
                Z = df[items0[-1][0]].apply(lambda x: round((eval(x)[0]+eval(x)[1])/2,3)).values.tolist()
                if len(X)>0:
                    for i in range(len(X)):
                        ax.scatter(X[i], Y[i], Z[i], s=float(scatterscale0['s']), alpha=1)
                else:
                    ax.scatter([],[],[])
            elif set(['x', 'y', 'z']).issubset(set(merge_list(items0, 2))):
                if len(df)>0:
                    idlist = df.loc[0,'idlist']
                    xyzlist = df.loc[0,'xyz']
                    elelist = df.loc[0,'elements']
                    idbond = df.loc[0,'idbond']
                    breaks = df.loc[0,'break']
                    creates = df.loc[0,'create']
                    changebond = {'break':breaks,'create':creates}
                    iddict = dict(zip(idlist, xyzlist))
                    # 绘制散点图。
                    x = [i[0] for i in xyzlist]
                    y = [i[1] for i in xyzlist]
                    z = [i[2] for i in xyzlist]
                    cdict = {'C':'C0','H':'C1','N':'C3','O':'C4','Al':'C5'}
                    color = [cdict[i] for i in elelist]
                    ax.scatter(x, y, z, s=float(scatterscale0['s']), c=color, marker='o', label=elelist, alpha = 1)
                    # 连线目标原子对。
                    for i in idbond:
                        xlist = [iddict[i[0]][0],iddict[i[1]][0]]
                        ylist = [iddict[i[0]][1],iddict[i[1]][1]]
                        zlist = [iddict[i[0]][2],iddict[i[1]][2]]
                        # @2025/5/6：计算两点距离
                        point1 = np.array(iddict[i[0]])
                        point2 = np.array(iddict[i[1]])
                        distance = np.linalg.norm(point1 - point2)
                        if distance < 2:   # 设置键长阈值为2.
                            if (xlist[0],ylist[0],zlist[0]) not in breaks+creates:
                                ax.plot(xlist, ylist, zlist, color='black', linewidth=5)
                            elif (xlist[0],ylist[0],zlist[0]) in breaks:
                                ax.plot(xlist, ylist, zlist, color='red', linewidth=5)
                            elif (xlist[0],ylist[0],zlist[0]) in creates:
                                ax.plot(xlist, ylist, zlist, color='green', linewidth=5)
                            else: pass
                else:
                    ax.scatter([],[],[])
                # 增加上下文本。 @2024/1/24。
                if title0 !='':
                    ax.set_title(eval(title0), x=0.2, y=1.0, fontproperties=fontset0)  # fontsize=fontsize0, # x,y范围0~1，设置位置可避免重影。
                # textset1 = """Time: {} ps\nReactions: {}""".format(time,reaction)
                # ax.set_text(x=0, y=0, z=45, s=textset1, size=fontsize0, fontproperties=fontset0)
                # ax.text(0, 0, 45, textset1, zorder=10, size=fontsize0, fontproperties=fontset0)
                # 增加text文字说明：
                # textset2 = """ReacSpace program © ganqiang@bit.edu.cn, All Rights Reserved."""
                # ax.text(x= 5, y=-20, z=-5, s=textset2, size=fontsize0)
                # 设置三维坐标范围。
                ax.relim()
                ax.autoscale_view()
                ax.set_xlim(axislimit0[0],axislimit0[1])
                ax.set_ylim(axislimit0[2],axislimit0[3])
                ax.set_zlim(axislimit0[4],axislimit0[5])
                if axisoff0:
                    # 隐藏所有坐标轴元素
                    ax.set_axis_off()
                else:
                    # 改变刻度标签的字体大小
                    ax.tick_params(labelsize=ticksize0)
                    ax.set_xlabel(items0[0][1], fontproperties=fontset0)
                    ax.set_ylabel(items0[1][1], fontproperties=fontset0)
                    ax.set_zlabel(items0[2][1], fontproperties=fontset0)
    # plt.show()
    return ax
# Animaiton定义事件处理，点击暂停，点击继续。ani在mapping中定义，忽略错误。
def toggle_pause():
    global paused
    if paused:
        ani.resume()
    else:
        ani.pause()
    paused = not paused
# 定义Animation子窗口，用于显示动图。目前无效 @2024/1/27。
def aniwindow(title0, fig0, ani0):
    aniwindowtk = tk.Tk()
    aniwindowtk.title(title0)
    canvas = FigureCanvasTkAgg(fig0, master=aniwindowtk)
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
    def play_pause(ani0):
        if ani0.event_source.running:
            ani0.event_source.stop()
            return False
        else:
            ani0.event_source.start()
            return True
    play_pause_button = tk.Button(aniwindowtk, text="Play/Pause", command=lambda: play_pause(ani0))
    play_pause_button.pack(side=tk.LEFT)
    def stop_animation():
        ani0.event_source.stop()
        ani0.frame_seq = []
        ani0.event_source.add_callback(lambda: None)
    stop_button = tk.Button(aniwindowtk, text="Stop", command=stop_animation)
    stop_button.pack(side=tk.LEFT)
    # aniwindowtk.geometry('800x600')
     # 根据图形的大小自动调整窗口尺寸
    # canvas.mpl_connect('resize_event', lambda event: aniwindowtk.geometry(f'{event.width}x{event.height}'))
    aniwindowtk.mainloop()
# @2024/3/12：气泡出现大黑边，不用。
def show_animation(animation):
    popup = tk.Toplevel()
    canvas = FigureCanvasTkAgg(animation._fig, master=popup)
    canvas.draw()
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
    popup.geometry('800x600')  # 设置弹出窗口的尺寸
# 调用reacspace各函数。
def start_reacspace(dfbonds, dfdump, dfcell, timestep, processes, smilimit, rule, bondslimit, sfactor, sdfset, bondspath):
    freeze_support()   # 正确地序列化Pandas类，并支持多进程操作。
    dfbonds, framelist, atoms = readbonds(dfbonds, dfdump, bondslimit, bondspath)
    dfspecies0 = run_species(dfbonds, dfdump, dfcell, framelist, timestep, processes, smilimit, atoms, rule, sfactor, sdfset, bondspath)
    dfspecies, dfspace = run_reaction(dfspecies0, framelist, timestep, processes, bondspath)
    return dfspecies, dfspace
# tkinter show plt
def show_plt(outpath):
    fig = plt.gcf()
    ax = fig.gca()  # 获取当前axes对象
    root = tk.Tk()
    root.title("Reaction Network Visualization")
    # 强制使用TkAgg后端
    # matplotlib.use('TkAgg')
    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    # 保存按钮
    save_button = tk.Button(root, text="Save Image", 
                          command=lambda: save_plt(outpath))
    save_button.pack(side=tk.BOTTOM)
    # 快捷键绑定
    root.bind('<Control-s>', lambda event: save_plt(outpath))
    # 窗口最大化
    try:
        root.state('zoomed')
    except:
        try:
            root.attributes('-zoomed', True)
        except:
            root.geometry(f"{root.winfo_screenwidth()}x{root.winfo_screenheight()}+0+0")
    
    # # 修正的拖动事件处理函数
    # def on_click(event, pos):
    #     global selected_node
    #     if event.inaxes is not ax:  # 现在ax已定义
    #         return
    #     for node in pos:
    #         x, y = pos[node]
    #         dist = (event.xdata - x)**2 + (event.ydata - y)**2 
    #         if dist < (0.1 * fig.dpi/72)**2:
    #             selected_node = node
    #             def on_drag(event):
    #                 if event.inaxes is not ax or selected_node is None:
    #                     return
    #                 pos[selected_node] = (event.xdata, event.ydata)
    #                 canvas.draw()  # 改为使用canvas.draw()而不是draw_graph()
    #             canvas.mpl_connect('motion_notify_event', on_drag)
    #             break
    
    # def on_release(event):
    #     global selected_node
    #     selected_node = None
    
    # # 重新绑定事件到新的canvas
    # # canvas.mpl_connect('button_press_event', on_click)
    # canvas.mpl_connect('button_press_event', lambda event: on_click(event, pos))
    # canvas.mpl_connect('button_release_event', on_release)
    
    root.mainloop()
# tkinter save plt
# 保存图像的函数
def save_plt(outpath = None):
    if outpath:
        os.makedirs(os.path.dirname(outpath), exist_ok=True)
        filepath = outpath
    else:
        filepath = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
        )
    if filepath:
        fig = plt.gcf()  # 获取当前的图表对象
        fig.savefig(filepath, bbox_inches='tight')
        print(f"Image saved to: {filepath}")

# root主函数
def create_window(label0,news0):
    version = news0.split('\n')[1].split(':')[1].strip()
    data = news0.split('\n')[2].split(':')[1].strip()
    # 新建一个窗体
    root = Tk()
    root.tk.call('encoding', 'system', 'utf-8')  # 支持中文。
    # 创建样式对象
    style = ttk.Style()
    # 统一字体家族（保持字号差异）
    if platform.system() == 'Windows': baseset = 10
    else: baseset = 13
    base_font = ('Times New Roman',baseset)  # 统一字体家族
    # 配置所有ttk组件
    style.configure('.', font=base_font)  # 全局默认
    style.configure('TNotebook.Tab', font=base_font)  # 特殊组件
    style.configure('TButton', font=base_font)  # 示例其他组件    
    root.resizable(True, True)        # 用户可调整窗口大小
    root.option_add('*Font', base_font) 
    # 设置程序占屏幕比例1/2。
    set_window_size(root)
    root.title("LMPAnalysis")
    # 建立分页Tab
    tabControl = ttk.Notebook(root)
    tab1 = ttk.Frame(tabControl)
    tabControl.add(tab1, text=' Arrange ')
    tab2 = ttk.Frame(tabControl)
    tabControl.add(tab2, text=' Mapping ')
    tabControl.pack(expand=1, fill="both")
    tab3 = ttk.Frame(tabControl)
    tabControl.add(tab3, text=' Modify ')
    tabControl.pack(expand=1, fill="both")
    tab4 = ttk.Frame(tabControl)
    tabControl.add(tab4, text=' ReacSpace ')
    tabControl.pack(expand=1, fill="both")
    tab5 = ttk.Frame(tabControl)
    tabControl.add(tab5, text=' ReacNetwork ')
    tabControl.pack(expand=1, fill="both")
    tab6 = ttk.Frame(tabControl)
    tabControl.add(tab6, text=' Package ')
    tabControl.pack(expand=1, fill="both")
    tab7 = ttk.Frame(tabControl)
    tabControl.add(tab7, text=' Setting ')
    tabControl.pack(expand=1, fill="both")
    tab8 = ttk.Frame(tabControl)
    tabControl.add(tab8, text=' About ')
    tabControl.pack(expand=1, fill="both")
    console_display = ConsoleDisplay(root)
    console_display.pack(side="bottom", fill="both", expand=True)
    print(label0)

    ####################### tab7设置 #########################
    global encode, elementorder,cuttype,cutvalue,fonts,bondslimit, phaseorder
    encode, elementorder, cuttype, cutvalue, fonts, bondslimit, phaseorder = tk.StringVar(),tk.StringVar(),tk.StringVar(),tk.StringVar(),tk.StringVar(),tk.StringVar(),tk.StringVar()
    if not os.path.exists(DEFAULT_PATH):
        print("# Error: default.txt in core folder was not found, please check it!")
    with open(DEFAULT_PATH, "r", encoding='utf-8') as text_file:
        content = text_file.read().strip()
    defaultdict = {item.split('=',1)[0].strip():item.split('=',1)[1] for item in content.split('\n$$$$\n') if item.strip() !=''}
    if not os.path.exists(LMPSETTING_PATH):
        dfset = pd.DataFrame({
            'item': list(defaultdict.keys()),
            'type': 'default',
            'value': list(defaultdict.values())})
        print("# Attention: default lmpsetting set file was created!")
        dfset.groupby(['item','type']).first().reset_index(drop=False).to_csv(LMPSETTING_PATH, encoding='utf-8-sig', index=False)
    else:
        dfset = pd.read_csv(LMPSETTING_PATH, header=0).dropna()
        print("# Attention: lmpsetting set in utils was loaded!")
    # # 读取目标路径下设置。
    dictpath = readlast(LMPSETTING_PATH)
    # fonts, 返回值fonts.get()
    combo(tab7, fonts, "Fonts:", 0, 0, listitem(readitem(dictpath,'fonts'),["Times New Roman", "Times New Roman, SimSun","SimSun"]), 30, 3, '')
    # encode，返回值encode.get()
    combo(tab7, encode, "       Encode:", 0, 6, listitem(readitem(dictpath,'encode'),["UTF-8","GBK",""]),9,1,'')
    # elementorder，返回值elementorder.get()
    combo(tab7, elementorder, "ElementOrder:", 2, 0, listitem(readitem(dictpath,'elementorder'),["{'Al':0,'C':1,'H':2,'N':3,'O':4}","{'C':0,'H':1,'N':2,'O':3}","{''}"]), 30, 3, '')
    # phaseorder，返回值phaseorder.get()
    combo(tab7, phaseorder, "   PhaseOrder:", 2, 4, listitem(readitem(dictpath,'phaseorder'),["ε, ε\', β, β\', γ, γ\', ζ, ζ\', x",""]), 35, 3, '')
    # bocutoff, 返回值cuttype.get(),cutvalue.get()
    combo2(tab7, "       BOCutoff:", 3, 4, cuttype, listitem(readitem(dictpath,'cuttype'),["Seperate","Single"]) , 9, 1, "readonly", cutvalue, listitem(readitem(dictpath,'cutvalue'),["","0.3,1.5"]), 9, 1, '')
    # 设置cutoff值
    submitwindow(tab7,"CutoffSet","660x210",120,9,3,7,LMPSETTING_PATH,'cutoff',9,'lightgray')
    # bondslimit，返回值bondslimit.get()
    combo(tab7, bondslimit, "BondsLimit:", 3, 0, listitem(readitem(dictpath,'bondslimit'),["{'Al':6,'C':4,'H':1,'N':3,'O':2}","{'C':4,'H':1,'N':3,'O':2}","{''}"]), 30, 3, '')    
    # Help6子窗口
    helpcontent7 = """  Program: path of lmpanalysis, such as /xx/xx/lmpanalysis
    avail for Modify-data, Package-ChemTraYzer.
  Encode: code of targe file to read, such as UTF-8, GBK, and etc.
  LMPSetting: set the path to save and load setting for all modules.
    Confirm: activate current path, if it is differ from default path.
  Elements: element order to sort species or reaction.
  BOCutoff: select the mode to set bocutoff and blcutoff.
    Seperate/Single: set the cutoff value with single data or not.
    CutffSet: cutoff value for every bonds should be set or changed.
        avail when 'Seperate' mode was selected, for Arrang-bonds/dumpbonds.
  Reset: reset values of all modules to default.
  Saveset: save set in 'Setting' module."""
    closewindow(tab7, "Help", "570x260", 380, 12, 8, 4, helpcontent7)
    updater = UltraSimpleUpdater(
        root=tab7,
        base_url="http://10.103.8.106:5005/Share/3 SimulationComputing/lmpanalysis/release/",
        username="group",
        password="asdf0455",
        current_version=version)
    updateRun = tk.Button(tab7, text="Updates", command=updater.check_and_update, width=9, bg='lightskyblue')
    updateRun.grid(row=8, column=2)
    # 参数重设为默认值
    def reset(lmpset0):
        if os.path.exists(lmpset0):
            dfset = pd.DataFrame({
                'item': list(defaultdict.keys()),
                'type': 'default',
                'value': list(defaultdict.values())})
            dfset.to_csv(lmpset0, encoding='utf-8-sig', index=False)
            print("# Attention: the lmpsetting file was reset to default values!")
            root.destroy()
            create_window(label0,news0)
        else:
            print("# Error: lmpsetting path is not exist, please check it!")
    resetRun = tk.Button(tab7, text="Reset", command=lambda:reset(LMPSETTING_PATH), width=9, bg='lightgray')
    resetRun.grid(row=8, column=5)
    def saveset(lmpset0):
        # 把当前设置写入dfset中，以备调用。
        if os.path.exists(lmpset0):
            dfset = pd.read_csv(lmpset0, header=0).dropna()
            tkset = [encode, element, cuttype, cutvalue, fonts]
            tkname = ['encode', 'element','cuttype','cutvalue','fonts']
            for n,i in enumerate(tkset):
                dfset = pd.concat([pd.DataFrame({'item':str(tkname[n]),'type':'last','value':i.get().strip()}, index=[3]),dfset], axis=0).groupby(['item','type']).first().reset_index(drop=False)
            dfset.to_csv(lmpset0, encoding='utf-8-sig', index=False)
        else:
            print("# Warning: lmpsetting in module 'Setting' is empty, current set would not be saved!")
    savesetRun = tk.Button(tab7, text="Saveset", command=lambda: saveset(LMPSETTING_PATH), width=9, fg='white', bg='blue')
    savesetRun.grid(row=8, column=7)
    # packetsRun = tk.Button(tab7, text="RunPackets", command=lambda: open_file(UTILS_DIR+'/packets.py'), width=9, fg='black', bg='lightblue')
    packetsRun = tk.Button(tab7, text="RunPackets", command=lambda: run_script(UTILS_DIR,"lmpanalysis",'packets.py'), width=9, fg='black', bg='lightblue')
    packetsRun.grid(row=8, column=0)    

    ####################### Tab1设置 #########################
    global timestep,thermostep,inpath,folders
    inpath,folders,export,timestep,thermostep,ignoredtime,read = tk.StringVar(),tk.StringVar(),tk.StringVar(),tk.StringVar(),tk.StringVar(),tk.StringVar(), tk.StringVar()
    # tab1 第0行设置
    combo(tab1,folders,"    Folders:",0,4,listitem(readitem(dictpath,'folders'),["","all"]),9,1,'')
    inpathunit(tab1,inpath,"Inpath:",0,0,24,2, readitem(dictpath,'inpath'), folders, "    Folders:",9,1,'')
    # read，export，返回值read.get(),export.get()
    combo(tab1,read,"           Read:",0,6,listitem(readitem(dictpath,'read'),["","ovito", "chemtrayzer", "reacnetgenerator","modify"]),18,2,'') 
    combo(tab1,export,"         Export:",1,6,listitem(readitem(dictpath,'export'),["data", ""]),18,2,'')
    # tab1 第1行设置
    # timestep，thermostep, 返回值timestep.get(), thermostep.get()
    combo(tab1, timestep, "Timestep(fs):", 1, 0, listitem(readitem(dictpath,'timestep'),["0.1","0.01","0.2","0.25",""]), 9, 1, '')
    combo(tab1, thermostep, "Thermostep:", 1, 2, listitem(readitem(dictpath,'thermostep'),["1000", "400", "500","2500", ""]), 9, 1, '')
    # ignore，返回值ignoredtime.get()
    combo(tab1, ignoredtime, "Ignore(ps):", 1, 4, listitem(readitem(dictpath,'ignoredtime'),["0","10"]), 9, 1, '')
    # tab1 第2行设置
    # Mode选择box，返回值checkselect(modecheck,[modelist01,modelist02,modelist03])
    modelist01 = ["Log", "Bonds", "Dump", "Cell", "Species", "POS"]
    modelist02 = ["atom", "neb", "RMSD", "chunk", "DumpBonds"]
    modelist03 = ["OVITO", "VARxMD", "ChemTraYzer", "ReacNet", "MS.xcd","General"]
    modecheck,modechecklabellist, modecheckbuttonlist = check(tab1,["Modes:","   ","   "],[2,3,4],[0,0,0],[modelist01,modelist02,modelist03])
    # 定义gridlist，用于后续clean grid。
    gridlist = []
    # tab1 第4行设置
    def arrangemodes(modelist, gridlist):
        clean(gridlist)
        # 获取目标文件字典。
        readpath = inpath.get().strip()+'/'+folders.get().strip()+'/'+read.get().strip()+'/'
        dictpath = readlast(LMPSETTING_PATH)
        filerule1 = readitem(dictpath,'filerule1')
        filelist = [i for i in filerule1.split('\n') if i.strip() !='']
        dictfile = {}
        for i in filelist:
            k, v = [j.strip().replace('filename','') for j in i.split(':')]
            dictfile[k] = v
        if 'Log' in modelist:
            global logdatas,supercell,logcheck,loglist
            logdatas,supercell = tk.StringVar(),tk.StringVar()
            # logdatas，返回值logdatas.get()
            logfiles = [f.replace('\\','/').replace('//','/') for f in glob.glob(readpath + dictfile['log'])]  # 模糊匹配文件名
            logf = open(logfiles[0], "r", encoding=encode.get())
            loglines = logf.read().splitlines() 
            line0, line1=[], []
            # 读取数据起始行和结束行。
            for i in range(len(loglines)):
                if re.split(r" +", loglines[i].strip())[0] == 'Step':line0+=[i]             # 数据起始行
                elif re.split(r" +", loglines[i].strip())[0] == 'Loop':line1+=[i]           # 数据终止行
            # 读取自定义log数据范围。
            # log选择box，返回值checkselect(logcheck,[loglist])
            loglist = [i for i in range(len(line0))]
            if len(loglist)<5:
                logcheck, logchecklabellist, logcheckbuttonlist = check(tab1,["LogDatas:"],[5],[0],[loglist])
                gridlist += logchecklabellist+ logcheckbuttonlist
            else:
                logdatas_label, logdatas_combo = combo(tab1, logdatas, "LogDatas:", 5, 0, listitem(readitem(dictpath,'logdatas'),["[x for x in range({})]".format(len(loglist))]), 48, 4, '')
                gridlist += [logdatas_label, logdatas_combo]
            # supercell，返回值supercell.get()
            supercell_label, supercell_combo = combo(tab1, supercell, "     SuperCell:", 5, 5, listitem(readitem(dictpath,'supercell'),["1,1,1", "2,2,2", "3,3,3", "4,4,4"]), 9, 1, '')
            gridlist += [supercell_label, supercell_combo]
        if 'DumpBonds' in modelist:
            global periodicity
            periodicity = tk.StringVar()
            periodicity_label, periodicity_combo = combo(tab1, periodicity, "   Periodicity:", 6, 4, listitem(readitem(dictpath,'periodicity'),["ppp","pps","sss",""]), 9, 1, '')
            gridlist += [periodicity_label, periodicity_combo]
        if ('Bonds' in modelist) or ('Dump' in modelist)or ('Cell' in modelist):
            global splitted
            splitted = tk.StringVar()
            splitted_label, splitted_combo = combo(tab1, splitted, "Splitted:", 3, 7, listitem(readitem(dictpath,'splitted'),["","Bonds","Dump","Both"]), 9, 1, 'Readonly')
            gridlist += [splitted_label, splitted_combo]
        if 'General' in modelist:
            global genread, gensepby, genheader
            genread, gensepby, genheader = tk.StringVar(),tk.StringVar(),tk.StringVar()
            if (inpath.get().strip() != '')&(folders.get().strip() != ''):
                filenamelist = [""] + filefilter(inpath.get().strip(), folders.get().strip(), read.get().strip())
            else:
                filenamelist = [""]
                print("# Attention: setting of inpath, Folders and Read could help to find files in targetpath!")
            genread_combo, gensepby_combo, genheader_combo =combo3(tab1, "", 5, 0, genread, listitem(readitem(dictpath,'generalread'),filenamelist),22,2,'', gensepby, listitem(readitem(dictpath,'gensepby'),["",":",",",";","\s+","tab","line"]), 9, 1, '', genheader, listitem(readitem(dictpath,'genheader'))+["","0","1","2"], 9, 1, '')
            # 预读取文件。
            def genmethod(inpath0, folder0, read0, file0, sepby, header0, gridlist):
                genpath = (inpath0 + '/'+folder0 +'/'+ read0 +'/'+ file0).replace('\\','/').replace('//','/')
                if genpath != '':
                    genfile = glob.glob(genpath)[0]
                    if os.path.exists(genfile):
                        global genmergetype, genmergeby, gennameby, genrename, genfilterby, genfilter
                        genmergetype, genmergeby, gennameby, genrename, genfilterby, genfilter = tk.StringVar(),tk.StringVar(),tk.StringVar(),tk.StringVar(),tk.StringVar(),tk.StringVar()
                        try: 
                            if file0.split('.')[-1] == 'csv':
                                # dfgen = pd.read_csv(genpath)
                                dfgen = autocode(genpath, 'pandas')
                            else:
                                with open(genpath,'rb') as f:
                                    result = chardet.detect(f.read(1000))       # 读取前1000字节
                                if header0 != '': headerset0 = int(header0)
                                else: headerset0 = None
                                # dfgen = pd.read_csv(genpath, header=headerset, sep='\s+', encoding=result['encoding'])
                                # dfgen = pd.read_csv(genpath, sep=sepby, encoding=encode.get(), header=None)
                                dfgen = autocode(genpath, 'pandas', head=headerset0, sep='\s+',)
                            gencolumn = [''] + dfgen.columns.tolist()
                        except: gencolumn = []
                        if len(gencolumn) > 0:
                            precolumn = [""]+['concat.x','concat.y']+gencolumn
                        else:
                            precolumn = [""]+['concat.x','concat.y']
                        genmerge_label, genmergetype_combo, genmergeby_combo = combo2(tab1, "Merge/Concat:", 5, 4, genmergetype, listitem(readitem(dictpath,'generalmergetype'),["","merge","concat"]), 9, 1, 'readonly', genmergeby, listitem(readitem(dictpath,'genmergeby'),precolumn), 9, 1, '')
                        genfilter_label, genfilterby_combo, genfilter_combo = combo2(tab1, "Filterby/Filter",6,0, genfilterby, listitem(readitem(dictpath,'generalfilterby'),["","dropna.x","dropna.y","dropna.xy","keepcolumns","delcolumns"]),22,2, 'readonly', genfilter, listitem(readitem(dictpath,'generalfilter'),["thresh.1","thresh.2","",":10","0:10"]), 9, 1, '')
                        genrename_label, gennameby_combo, genrename_combo = combo2(tab1, "OutputFile(s):", 6, 4, gennameby, listitem(readitem(dictpath,'generalnameby'),["suffix","replace","fullname"]),9,1, 'readonly', genrename, listitem(readitem(dictpath,'generalrename'),["modify"]+filenamelist), 22, 2, '')
                        gridlist += [genmerge_label, genmergetype_combo, genmergeby_combo, genfilter_label, genfilterby_combo, genfilter_combo, genrename_label, gennameby_combo, genrename_combo]
                    else:
                        print("# Warning: target file does not exist, please check it!")                
                else:
                    print("# Warning: generalread is empty, please input file to read!")
            general_button = tk.Button(tab1, text="Confirm",command=lambda: genmethod(inpath.get().strip(), folders.get().strip(), read.get().strip(), genread.get().strip(), gensepby.get().strip(), genheader.get().strip(), gridlist), width=9, bg='lightskyblue')
            general_button.grid(row = 5, column = 7)
            gridlist += [genread_combo, gensepby_combo, genheader_combo, general_button]
    arrange_button = tk.Button(tab1, text="Confirm",command=lambda: arrangemodes(checkselect(modecheck,[modelist01,modelist02,modelist03]), gridlist), width=9, bg='lightskyblue')
    arrange_button.grid(row = 2, column = 8)
    # tab1 第6行设置
    submitwindow(tab1,"FileRules","320x280",50,13,7,0, LMPSETTING_PATH,'filerule1',9,'lightgray')
    # Help子窗口。 
    helpcontent = """   Inpath: open target folders path.
    Folders: target folder(s) to analyze, * is acceptable!
    Export: folder to export analysis result, default data.
    Encode: select encoding of file(s) to read.
    Timesetp(fs): set or select the timestep of simulation.
    Ignore(ps): set or select the time to ignore at beginning.
    Modes: select analysis mode(s).
        Cell: stands for the box informations coming from dump file.
        Dumpbonds: bases on results of Bonds and Dump analysis.
        chunk: stands for the results of fix ave/chunk commnad.
        OVITO: arrange output data from OVITO.
            needs data folders in 'ovito' folder.
        VARxMD: needs reacslist.txt result of VARxMD. 
        ChemTraYzer: arrange the results of ChemTraYzer.
            needs data files in 'chemtrayzer' folder.
        ReacNet: arrange results of ReacNetGenerator. 
            needs data files in 'reacnet' folder.
    Read: set folder to read.
        Avail for all modes.
    LogDatas: set or select the pieces of log data to analyze.
        Avail for Log mode.
    Supercell: set of select the suppercell information for log.
        Avail for Log Mode.
    CutoffValues: cutoff threshold for filter of Bonds.
        Avail for Bonds Mode.
    FileRules: set the rule of filenames to read.
    ShowRules: show currently set file rules."""
    closewindow(tab1, "Help", "540x560", 420, 27, 7, 3, helpcontent)
    
    # 数据分析和输出
    def runarrange(stop_event):
        # 重新读取设置文件，以备调用。
        dictpath = readlast(LMPSETTING_PATH)
        filerule1 = readitem(dictpath,'filerule1')
        if checkselect(modecheck,[modelist01,modelist02,modelist03]) == []: 
            print('Error: Please select at lest one mode to analysis!')
        else:
            modelist = checkselect(modecheck,[modelist01,modelist02,modelist03])
            # 文件名读取，生成变量如logfilename等。
            filelist = [i for i in filerule1.split('\n') if i.strip() !='']
            dictfile = {}
            for i in filelist:
                k, v = [j.strip().replace('filename','') for j in i.split(':')]
                dictfile[k] = v
            # 读取设置文件操作。
            if (cuttype.get() == 'Single') & (cutvalue.get().strip() !=''):
                dictcutoff = {'bonds':[''],'bocutoff':[float(cutvalue.get().split(',')[0])],'blcutoff':[float(cutvalue.get().split(',')[1])]}
                dfcutoff = pd.DataFrame(dictcutoff)
            elif cuttype.get() == 'Seperate':
                cutoffread = readitem(dictpath,'cutoff')
                if cutoffread.strip() !='':
                    dfcutoff = pd.DataFrame(eval(cutoffread))
                else:
                    dfcutoff = pd.DataFrame(eval(cutoffdefault))
                    print("# Warning: cutoff set could not be read, default set would be loaded!")
            else:
                print("# Error: cutoff set was wrong, please check it!")
            rule = eval(elementorder.get())
            # 把当前设置写入dfset中，以备调用。
            if os.path.exists(LMPSETTING_PATH):
                dfset = pd.read_csv(LMPSETTING_PATH, header=0).dropna()
                tkset = [inpath,folders,read,export,timestep,thermostep,ignoredtime]
                tkname = ['inpath','folders','read','export','timestep','thermostep','ignoredtime']
                if 'Log' in modelist:
                    if bool(logdatas.get()) and bool(supercell.get()):
                        tkset += [logdatas, supercell]
                        tkname += ['logdatas', 'supercell']
                if 'DumpBonds' in modelist:
                    if bool(periodicity.get()):
                        tkset += [periodicity]
                        tkname += ['periodicity']
                if 'General' in modelist:
                    if bool(genread.get()):
                        tkset += [genread, gensepby, genheader]
                        tkname += ['genread', 'gensepby', 'genheader']
                for n,i in enumerate(tkset):    
                    dfset = pd.concat([pd.DataFrame({'item':str(tkname[n]),'type':'last','value':i.get().strip()}, index=[3]),dfset], axis=0).groupby(['item','type']).first().reset_index(drop=False)
                dfset.to_csv(LMPSETTING_PATH, encoding='utf-8-sig', index=False)
            else:
                print("# Warning: lmpsetting in module 'Setting' is empty, current set would not be saved!")
            # 数据文件夹读取
            if inpath.get().strip() != '':
                folderset = folderfilter(inpath.get().strip(), folders.get().strip())
                # @2024/6/8：去掉'dataallxx'文件夹
                folderset = [i for i in folderset if 'dataall' not in i]
            else: print('# Attention: Inpath is empty, please input a path!')
            readfolder = read.get().strip()
            targetfolder = export.get().strip()
            # 读取数据文件夹，确定读取路径readpath。
            if folderset != []:
                for folder in folderset:
                    # 建立输出数据文件夹，默认data。  @2024/2/8
                    if targetfolder != '': outpath = inpath.get().strip() +'/'+folder+'/'+targetfolder +'/'
                    else: outpath = inpath.get().strip() +'/'+folder+'/'
                    # 读取输入文件夹。                           @2024/2/8
                    if readfolder != '': readpath = inpath.get().strip() +'/'+folder+'/'+ readfolder +'/'
                    else: readpath = inpath.get().strip() +'/'+folder+'/'
                    readpath0 = inpath.get().strip() +'/'+folder+'/'
                    # 建立数据文件夹存放生成数据。
                    if not os.path.exists(outpath):
                        os.mkdir(outpath)
                        print('# Attention: {} folder has been bulided!'.format(targetfolder))
                    else:
                        print('# Attention: {} folder already exist, same files will be overwritten!'.format(targetfolder))
                    # 读取data文件，调用df_atoms()函数生成列表dfatoms
                    try:
                        # dfatoms格式type, mass, element。type指原子类型，element指元素名称。
                        datapath = glob.glob(readpath0 + dictfile['data'])[0]
                        dfatoms = pd.DataFrame(df_atoms(datapath))
                        dfatoms['type'] = dfatoms['type'].astype(int)
                        dfatoms = dfatoms[dfatoms['type']!=0]           # 去掉末尾空数据。@2024/2/9
                    except: 
                        print('# Warning: Data file could not be read, bonds, dump or species analysis may be aborted!')
                        modelist = [i for i in checkselect(modecheck,[modelist01,modelist02,modelist03]) if (i != 'Bonds')&(i != 'Species')]
                    if 'atom' in modelist:
                        try: 
                            print('# data of atoms are:')
                            print(dfatoms.columns.tolist())
                            dfatoms.to_csv(outpath + 'dataofatom.csv', encoding='utf-8-sig', index=False)
                        except: print(" # Warning: dfatom calcuation failed, please check data file name.")
                    if 'Log' in modelist:                            # log分析模块                
                        # logfiles = glob.glob(readpath + dictfile['log'])  # 模糊匹配文件名
                        logfiles = [f.replace('\\','/').replace('//','/') for f in glob.glob(readpath + dictfile['log'])]
                        for n, logfile in enumerate(logfiles):
                            logf = open(logfile, "r", encoding=encode.get())
                            loglines = logf.read().splitlines()                     # 去掉换行符'\n'，数据行前后都有空格
                            line0=[];line1=[]
                            # 读取数据起始行和结束行。
                            for i in range(len(loglines)):
                                if re.split(r" +", loglines[i].strip())[0] == 'Step':line0+=[i]             # 数据起始行
                                elif re.split(r" +", loglines[i].strip())[0] == 'Loop':line1+=[i]           # 数据终止行
                            # 读取自定义log数据范围。
                            if len(loglist)<5: lognums = checkselect(logcheck,[loglist])
                            else: lognums = eval(logdatas.get().strip())
                            # 判断是否完成log输出，区分完整数据和不完整数据。
                            dflog = pd.DataFrame()                              # 建立空表，后续填充
                            if len(line0)-len(line1) == 1:                      # 判断数据是否完整
                                print('# Warning: the calcution is not finished!')
                            if len(lognums) == 0: print('# Warning: lack of logdatas value, please select at least one')
                            else:
                                logcolumns = re.split(r" +", loglines[line0[lognums[0]]].strip())           # 提取第一组数据title为列名
                                # 判断是否完成log输出，区分完整数据和不完整数据。
                                dflog = pd.DataFrame()                              # 建立空表，后续填充
                                if len(line0)-len(line1) == 1:                      # 判断数据是否完整
                                    print('# Warning: the calcution is not finished!')
                                    line1 = line1+[len(loglines)-1]
                                for i in lognums:
                                    dflog0 = pd.DataFrame(re.split(r' +', k.strip()) for k in loglines[line0[i]+1:line1[i]] if len(re.split(r' +', k.strip()))==len(logcolumns))  # 建立新列表
                                    dflog = pd.concat([dflog,dflog0],axis=0)
                                dflog.columns=logcolumns
                                dflog = dflog.groupby('Step').first().reset_index()          # 去除重复值
                                if 'Press' in logcolumns:dflog['Press'] = dflog['Press'].astype(float)/10000
                                if supercell.get() != '':
                                    supercella,supercellb,supercellc = eval(supercell.get().split(',')[0].strip()),eval(supercell.get().split(',')[1].strip()),eval(supercell.get().split(',')[2].strip())
                                    if 'Cella' in logcolumns:dflog['Cella'] = dflog['Cella'].astype(float)/supercella
                                    if 'Cellb' in logcolumns:dflog['Cellb'] = dflog['Cellb'].astype(float)/supercellb
                                    if 'Cellc' in logcolumns:dflog['Cellc'] = dflog['Cellc'].astype(float)/supercellc
                                    if 'Volume' in logcolumns:
                                        dflog['Volume'] = dflog['Volume'].astype(float)/(supercella*supercellb*supercellc)
                                dflog=dflog.rename(columns={'Step':'frame'})
                                # @2024/6/10：修改为frame修正，而不是time修正。
                                if ignoredtime.get().strip() != '':
                                    dflog['frame'] = dflog['frame'].astype(int)-int(float(ignoredtime.get().strip())*1000/float(timestep.get().strip()))
                                dflog['frame'] = dflog['frame'].astype(int)
                                dflog = dflog.sort_values(by=['frame'], ascending=True)
                                dflog.insert(loc=1,column='time',value=round(dflog['frame']*float(timestep.get().strip())*0.001,3))  # 增加'time'列
                                if n ==0:
                                    print('# data of log are:')
                                    print(dflog.columns.tolist())
                                if len(logfiles) == 1: dflog.to_csv(outpath + 'dataoflog.csv', encoding='utf-8-sig', index=False)
                                else: dflog.to_csv(outpath + 'dataoflog.{}.csv'.format(logfile.replace(readpath,'').replace('log.','')), encoding='utf-8-sig', index=False)
                    if 'Bonds' in modelist:                          # bonds分析模块
                        # 分别读取未split和splitted的Bonds文件。
                        splitcheck = False
                        if splitted.get() == '':
                            bondsfiles = glob.glob(readpath + dictfile['bonds'])
                        elif splitted.get() in ['Bonds','Both']:
                            splitcheck = True
                            bondsfiles = glob.glob(readpath + dictfile['bonds']+'.*.split')
                            # @2024/5/22：增加文件排序，避免过多文件顺序错乱。
                            bondsfiles = sorted(bondsfiles, key=lambda x: int(x.split('.')[-2]))
                        # 逐一清洗各个bonds文件，最后合并为单一csv。
                        for n, bondsfile in enumerate(bondsfiles):
                            bondsf = open(bondsfile, "r", encoding=encode.get())                # 指定编码读取。
                            bondslines = bondsf.read().splitlines()                    # 去掉换行符'\n'
                            atomall = int(bondslines[2].split(' ')[4])
                            listid = []; listtype = []; bondslist = []
                            for i in range(7, atomall+7):                                   # 建立原子编号和类型字典，查原子编号对应类型dictidtype[id]。
                                match = re.findall('[+-\][0-9\.]+', bondslines[i])
                                listid += [int(match[0])]; listtype += [int(match[1])]
                            dictidtype = dict(zip(listid, listtype))
                            for i in range(len(bondslines)):
                                if 'Timestep' in bondslines[i]:               # 读取轨迹帧数
                                    frame = int(bondslines[i].split(' ')[2])
                                    # @2025/1/9: add data integrity testing.
                                    try:
                                        # match0 = re.findall('[+-\][0-9\.]+', bondslines[i+7+atomall-1])
                                        for j in range(i+7,i+7+atomall):                                # 整理键级数据
                                            match = re.findall('[+-\][0-9\.]+', bondslines[j])
                                            if int(match[2]) >0:
                                                bondslist += [[frame, int(match[0]), int(match[3+k]), int(match[1]),dictidtype[int(match[3+k])], float(match[3+int(match[2])+k+1])] for k in range(0, int(match[2]))]
                                            # 处理可能存在的单个原子情况。赋予空值np.nan，筛选空值行df[np.isnan(df['id2'])]。
                                            elif int(match[2]) ==0: bondslist += [[frame,int(match[0]),0,int(match[1]),0,0]]
                                    except:
                                        print("# Warning: bonds data at frame {} was incomplete, and would be ignored!".format(frame) )
                            dfbonds = pd.DataFrame(bondslist,columns = ['frame', 'id1','id2', 'type1','type2','bo'])
                            dfbonds['bonds'] = pd.merge(dfbonds['type1'], dfatoms[['type', 'element']], how='left', left_on='type1', right_on='type')['element'] + pd.merge(dfbonds['type2'], dfatoms[['type', 'element']],how='left', left_on='type2', right_on='type')['element']
                            dfbonds = dfbonds.groupby(['frame','id1','id2']).first().reset_index(drop=False)   # 去掉重复值
                            # @2024/3/9：增加对于单一键级、键长阈值适配。
                            if dfcutoff.loc[0,'bonds'] == '':
                                dfbonds[['bocutoff','blcutoff']] = dfcutoff.loc[0,'bocutoff'],dfcutoff.loc[0,'blcutoff']
                                # 对于单分子赋予缺失值。
                                dfbonds.loc[dfbonds['id2']==0,'bocutoff'] = np.nan
                                dfbonds.loc[dfbonds['id2']==0,'blcutoff'] = np.nan
                            else:
                                dfbonds= pd.merge(dfbonds, dfcutoff, how='left', on='bonds')
                            dfbonds['frame'] = dfbonds['frame'].astype(int) -int(ignoredtime.get())*1000/float(timestep.get())
                            dfbonds['frame'] = dfbonds['frame'].astype(int)
                            dfbonds.insert(loc=1,column='time', value=round(dfbonds['frame']*float(timestep.get())*0.001,3))
                            # dfbondsall = pd.concat([dfbondsall,dfbonds],axis=0)
                            # 逐个文件输出数据。
                            if len(bondsfiles) == 1:
                                dfbonds.to_csv(outpath +'dataofbonds.csv', encoding='utf-8-sig', index=False)
                            elif splitcheck:
                                dfbonds.to_csv(outpath + 'dataofbonds.split{}.csv'.format(n), encoding='utf-8-sig', index=False)
                            else:
                                bondname = bondsfile.replace(readpath,'').replace('.reax','').replace('.bof','')
                                dfbonds.to_csv(outpath + 'dataofbonds.{}.csv'.format(bondname), encoding='utf-8-sig', index=False)
                        print('# data of bonds file are:')
                        print(dfbonds.columns.tolist())
                        # print(dfbonds.tail())
                        # dfbondsall.to_csv(outpath + 'dataofbonds.csv', encoding='utf-8-sig', index=False)
                    if 'Dump' in modelist:
                        # 分别读取未split和splitted的Dump文件。
                        splitcheck = False
                        if splitted.get() == '':
                            dumpfiles = glob.glob(readpath + dictfile['dump'])
                        elif splitted.get() in ['Dump','Both']:
                            splitcheck = True
                            dumpfiles = glob.glob(readpath + dictfile['dump']+'.*.split')
                            # 逐一清洗各个dump文件，最后依次输出到同一csv文件。
                            # @2024/5/22：增加文件排序，避免过多文件顺序错乱。
                            dumpfiles = sorted(dumpfiles, key=lambda x: int(x.split('.')[-2]))
                        dumpfiles = [f.replace("\\","/") for f in dumpfiles]
                        for n, dumpfile in enumerate(dumpfiles):
                            dumpf = open(dumpfile, "r", encoding=encode.get())       # encoding="UTF-8"指定UTF-8编码读取。
                            dumplines = dumpf.read().splitlines()                    # 去掉换行符'\n'
                            # @2025/5/12：改为使用正则表达式匹配关键词。
                            pattern = re.compile(r'ITEM: TIMESTEP')
                            framelines = [i for i, line in enumerate(dumplines) if pattern.search(line)]
                            dumpcolumns = re.split(r' +', dumplines[framelines[0]+8])[2:]
                            # 循环遍历 framelist，读取数据并更新 DataFrame
                            # @2025/5/12：修改匹配轨迹含不同原子数。
                            dfdump, dfdump_list = pd.DataFrame(), []
                            for i in framelines:
                                frame0 = int(dumplines[i+1])
                                atomall = int(dumplines[i+3])
                                lines = dumplines[i+9:i+9+atomall]
                                data = [re.split(r' +', j) for j in lines]
                                # dfdump0 = pd.DataFrame(data, columns=range(len(data[0])))
                                dfdump0 = pd.DataFrame(data, columns = dumpcolumns)
                                dfdump0.insert(0, 'frame', frame0)
                                # dfdump_list.append(dfdump0)
                                dfdump = pd.concat([dfdump, dfdump0], ignore_index=True)
                            dfdump.rename(columns={'xu':'x','yu':'y','zu':'z'}, inplace = True)
                            # 检查空数据行，删除整个frame。@2025/1/10。
                            nullframelist = dfdump[dfdump.isna().any(axis=1)]['frame'].tolist()
                            if len(nullframelist)>0:
                                print("# Warning: dump data at frame(s) {} was incomplete, and would be ignored!".format(', '.join(nullframelist)))
                                dfdump = dfdump[~dfdump['frame'].isin(nullframelist)]
                            dfdump['frame'] = dfdump['frame']-int(ignoredtime.get())*1000/float(timestep.get())
                            dfdump['frame'] = dfdump['frame'].astype(int)
                            dfdump.insert(loc=1, column='time',value=round(dfdump['frame']*float(timestep.get())*0.001,3))
                            dfdump[['id','type']] = dfdump[['id','type']].astype(int)
                            dfdump = dfdump.sort_values(by=['frame','id'], ascending=True)
                            # 增加element列，为元素种类。
                            # @2024/7/2：增加条件，如dump中缺mass则从dfatom补充。
                            # @2025/5/6: 增加dfatom判断和计算。
                            if not 'dfatom' in locals():
                                datapath = glob.glob(readpath0 + dictfile['data'])[0]
                                dfatoms = pd.DataFrame(df_atoms(datapath))
                                dfatoms['type'] = dfatoms['type'].astype(int)
                                dfatoms = dfatoms[dfatoms['type']!=0]
                            if 'mass' not in dfdump.columns.tolist():
                                dfdump = pd.merge(dfdump,dfatoms, how='left',on='type')
                            else:
                                dfdump = pd.merge(dfdump,dfatoms[['type','element']], how='left',on='type')
                            if len(dumpfiles) == 1:
                                dfdump.to_csv(outpath +'dataofdump.csv', encoding='utf-8-sig', index=False)
                            elif splitcheck:
                                dfdump.to_csv(outpath + 'dataofdump.split{}.csv'.format(n), encoding='utf-8-sig', index=False)
                            else: 
                                dumpname = dumpfile.replace(readpath,'').replace('.trj','')
                                dfdump.to_csv(outpath + 'dataofdump.{}.csv'.format(dumpname), encoding='utf-8-sig', index=False)
                        print('# data of dump file are:')
                        print(dfdump.columns.tolist())
                    if 'DumpBonds' in modelist:
                        if os.path.exists(outpath +'dataofdump.csv') and os.path.exists(outpath +'dataofbonds.csv'):
                            dfdump = pd.read_csv(outpath +'dataofdump.csv', encoding=encode.get())
                            dfbonds = pd.read_csv(outpath +'dataofbonds.csv', encoding=encode.get())
                            dfdump1 = dfdump[['frame', 'id', 'x', 'y', 'z']].rename(columns={'id': 'id1', 'x': 'x1', 'y': 'y1', 'z': 'z1'}).astype(float)
                            dfdump2 = dfdump[['frame','id','x','y','z']].rename(columns={'id':'id2','x':'x2','y':'y2','z':'z2'}).astype(float)
                            dfdump1['id1',]=dfdump1['id1'].astype(int)
                            dfdump2['id2']=dfdump2['id2'].astype(int)
                            dfdumpbonds0 = pd.merge(dfbonds, dfdump1, how='left',on=['frame', 'id1'])
                            dfdumpbonds = pd.merge(dfdumpbonds0, dfdump2, how='left',on=['frame', 'id2']).dropna(axis=0)
                            # 进行成对原子间距离 (键长）计算，对于xyz格式可能出现超长键长，建议用xuyuzu格式。
                            if bool(periodicity.get()) & os.path.exists(outpath +'dataofcell.csv'):
                                ppp = periodicity.get().strip()
                                dfcell = pd.read_csv(outpath +'dataofcell.csv', encoding=encode.get())
                                if (len(ppp) == 3) &(bool(re.match(r'^[ps]+$', ppp))):   # 判断ppp输入为p或s。
                                    dfmerge = pd.merge(dfdumpbonds, dfcell, how='outer', on='frame').dropna()
                                    # @2024/4/10: 引入倾斜值校正的三方向距离公式。
                                    # xy, xz, yz为弧度值。
                                    dfmerge['x'] = dfmerge.apply(lambda x: x['a']-np.abs((x['x1']-x['x2'])-(x['y1']-x['y2'])*tan(x['xy'])-(x['z1']-x['z2'])*tan(x['xz'])) if (np.abs((x['x1']-x['x2'])-(x['y1']-x['y2'])*tan(x['xy'])-(x['z1']-x['z2'])*tan(x['xz']))>= x['a']*0.5)& (ppp[0]=='p') else np.abs((x['x1']-x['x2'])-(x['y1']-x['y2'])*tan(x['xy'])-(x['z1']-x['z2'])*tan(x['xz'])), axis=1)
                                    dfmerge['y'] = dfmerge.apply(lambda x: x['b']-np.abs((x['y1']-x['y2'])-(x['z1']-x['z2'])*tan(x['yz'])) if (np.abs((x['y1']-x['y2'])-(x['z1']-x['z2'])*tan(x['yz']))>= x['b']*0.5)& (ppp[1]=='p') else np.abs((x['y1']-x['y2'])-(x['z1']-x['z2'])*tan(x['yz'])), axis=1)
                                    dfmerge['z'] = dfmerge.apply(lambda x: x['c']-np.abs(x['z1']-x['z2']) if (np.abs(x['z1']-x['z2'])>= x['c']*0.5)& (ppp[2]=='p') else np.abs(x['z1']-x['z2']), axis=1)
                                    dfmerge['bl'] = np.sqrt(dfmerge['x']**2+dfmerge['y']**2+dfmerge['z']**2)
                                    dfdumpbonds = dfmerge.drop(['x', 'y', 'z', 'a', 'b', 'c', 'a0', 'b0', 'c0', 'xy', 'xz', 'yz'], axis=1)
                            else:
                                dfdumpbonds['bl'] = np.sqrt((dfdumpbonds['x1']-dfdumpbonds['x2'])**2+(dfdumpbonds['y1']-dfdumpbonds['y2'])**2+(dfdumpbonds['z1']-dfdumpbonds['z2'])**2)
                            print('# data of dumpbonds are:')
                            print(dfdumpbonds.columns.tolist())
                            dfdumpbonds[['frame', 'time', 'id1', 'id2', 'type1', 'type2', 'bonds', 'bo', 'bl', 'bocutoff', 'blcutoff', 'x1', 'y1', 'z1', 'x2', 'y2', 'z2']].to_csv(outpath+'dataofdumpbonds.csv', encoding='utf-8-sig', index=False)
                        else:
                            print('# Warning: DumpBonds mode stopped, it bases on modes or data of Bonds and Dump!')
                    if 'Cell' in modelist:                           # dump分析模块 (注意dump文件使用xu、yu、zu) 
                        if splitted.get() == '':
                            dumpfiles = glob.glob(readpath + dictfile['dump'])
                        elif splitted.get() in ['Dump','Both']:
                            dumpfiles = glob.glob(readpath + dictfile['dump']+'.*.split')
                            # @2024/5/22：增加文件排序，避免过多文件顺序错乱。
                            dumpfiles = sorted(dumpfiles, key=lambda x: int(x.split('.')[-2]))
                        # 逐一清洗各个dump文件，最后依次输出到同一csv文件。
                        dfcellall = pd.DataFrame()
                        for dumpfile in dumpfiles:
                            dumpf = open(dumpfile, "r", encoding=encode.get())       # encoding="UTF-8"指定UTF-8编码读取。
                            dumplines = dumpf.read().splitlines()                    # 去掉换行符'\n'
                            dfcell = dump_cell(dumplines)
                            dfcellall = pd.concat([dfcellall,dfcell],axis=0)
                        dfcellall['frame'] = dfcellall['frame'].astype(int)-float(ignoredtime.get())*1000/float(timestep.get())
                        dfcellall['frame'] = dfcellall['frame'].astype(int)
                        dfcellall.to_csv(outpath + 'dataofcell.csv', encoding='utf-8-sig', index=False)
                        print('# data of cell file are:')
                        print(dfcell.columns.tolist())                    
                    if 'Species' in modelist:                        # species分析模块
                        # @2013/11/19 修正species分析中pandas.groupyby()函数导致的分子丢失错误，删除无用代码。
                        # @2025/9/30: improve species analysis.
                        speciesfile = glob.glob(readpath + dictfile['species'])[0]
                        lines = autocode(speciesfile,'lines')
                        data0 = []
                        for n,i in enumerate(lines):
                            if n ==0 and i.split()[1]=='Timestep':
                                columns = i.split()[1:4]+['number','molecule']
                                pass
                            if i.split()[1]=='Timestep':
                                species = i.split()[4:]
                                frame, No_Moles, No_species = lines[n+1].split()[:3]
                                for j in range(int(No_species)):
                                    data0.append([frame, No_Moles, No_species,lines[n+1].split()[3+j],species[j]])
                        dfspecies = pd.DataFrame(data0,columns=columns)
                        dfspecies = dfspecies.rename(columns={'Timestep':'frame'})
                        dfspecies['frame'] = dfspecies['frame'].astype(int)-float(ignoredtime.get())*1000/float(timestep.get())
                        dfspecies['frame'] = dfspecies['frame'].astype(int)
                        dfspecies.insert(loc=1,column='time', value=round(dfspecies['frame']*float(timestep.get())*0.001,3))
                        dfspecies['molecule'] = dfspecies['molecule'].apply(lambda x:list_compound_nosub(x,rule))
                        dfspecies['weight'] = dfspecies['molecule'].apply(molecular_weight)
                        print('# data of species are:')
                        print(dfspecies.columns.tolist())
                        dfspecies.to_csv(outpath + 'dataofspecies.csv', encoding='utf-8-sig', index=False)
                    if 'POS' in modelist:
                        posfile = glob.glob(readpath + dictfile['pos'])[0]
                        posf = open(posfile, "r", encoding=encode.get())
                        lines = posf.readlines()
                        dfpos = pd.DataFrame()
                        for i, line in enumerate(lines):
                            if 'Timestep' in line:
                                # 读取轨迹数和坐标盒子范围。
                                frame = int(line.split()[1])
                                xlo, xhi = float(line.split()[7]),float(line.split()[9])
                                ylo, yhi = float(line.split()[11]),float(line.split()[13])
                                zlo, zhi = float(line.split()[15]),float(line.split()[17])
                                for j, line2 in enumerate(lines[i:], start=i):
                                    if line2.startswith('#'):
                                        data_lines = [line.replace('\t', ' ') for line in lines[i+2:j]]
                                        df0 = pd.DataFrame([k.split() for k in data_lines])
                                        df0['frame'] = int(frame-int(ignoredtime.get())*1000/float(timestep.get()))
                                        df0['time'] = round(df0['frame']*float(timestep.get())* 0.001, 3)  # 保留三位小数
                                        df0.columns = ['ID','Atom_Count','molecule','q','x','y','z','frame','time']
                                        # 把pos文件相对坐标转换为绝对坐标，重要！
                                        df0['x'] = df0['x'].apply(lambda x:(1 - float(x)) * xlo + float(x) * xhi)
                                        df0['y'] = df0['y'].apply(lambda x:(1 - float(x)) * ylo + float(x) * yhi)
                                        df0['z'] = df0['z'].apply(lambda x: (1 - float(x)) * zlo + float(x) * zhi)
                                        dfpos = pd.concat([dfpos, df0], axis=0)
                                        break
                        dfpos = dfpos[['frame','time', 'molecule', 'q', 'x', 'y', 'z']].reset_index(drop=True)
                        # 先用list_compound函数修改分子元素顺序及序号变下标，再用xx.translate(resub)恢复下标为正文。
                        dfpos['molecule'] = dfpos['molecule'].apply(lambda x:list_compound(x,rule).translate(resub))
                        dfpos['weight'] = dfpos['molecule'].apply(lambda x:molecular_weight(x))
                        print('# data of pos are:')
                        print(dfpos.columns.tolist())
                        print('# Attention: x, y and z stand for the center-of-mass coordinate of molecule.')
                        dfpos.to_csv(outpath + 'dataofpos.csv', encoding='utf-8-sig', index=False)
                    if 'neb' in modelist:
                        nebread = os.listdir(readpath); nebList = []
                        # 查找neb文件夹，命名格式nebxxx
                        for f in nebread:
                            if (os.path.isdir(readpath+f))&('neb' in f):
                                nebList.append(f)               # 判断目录是否是文件夹
                        for f in nebList:
                            nebread2 = os.listdir(readpath+f);nebList2 = []
                            for j in nebread2:
                                if 'log.lammps.' in j:nebList2.append(j)          # 判断目录是否是文件
                            listneb = [i.replace(nebfilename.replace('*',''),'') for i in nebList2 if nebfilename.replace('*','') in i ]
                            energylist = []
                            for i in listneb:
                                nebfile = glob.glob(readpath + f+'/'+nebfilename.replace('*',i))[0]
                                nebf = open(nebfile, "r", encoding=encode.get())                # encoding="UTF-8"指定UTF-8编码读取。
                                neblines = nebf.read().splitlines()                       # 每行末尾没有\n
                                energylist0 = []
                                for j in range(len(neblines)):
                                    if 'Minimization stats:' in neblines[j]:
                                        energylist0 += [float(re.split(' +|\t',neblines[j+3].strip())[-1])]
                                # 计算弛豫后与初始状态能量差dE。
                                energylist += [[int(i),energylist0[-1]-energylist0[0]]]
                            dfneb = pd.DataFrame(energylist, columns=['No','dE'])
                            dfneb['normalize']=dfneb['No']/dfneb['No'].max()
                            if nebList.index(f) == 0:
                                dfneb.to_excel(outpath+'dataofneb.xlsx', "{}".format(f.split('neb')[1]),index=False)
                                print('# data of neb are:')
                                print(dfneb.columns.tolist())                    
                            else:
                                with pd.ExcelWriter(outpath+'dataofneb.xlsx', mode='a', engine="openpyxl") as writer:
                                    dfneb.to_excel(writer, "{}".format(f.split('neb')[1]), index=False)
                    # @2024/5/29：新增rmsd清洗。
                    if 'RMSD' in modelist:
                        print("# Attention: msd file name format is msdxx.yy, where xx is element.")
                        msdfiles = glob.glob(readpath + dictfile['msd'])
                        if len(msdfiles) > 0:
                            dfall = pd.DataFrame()
                            msdfiles = [i.replace('\\','/') for i in msdfiles]
                            # 对文件（即元素排序）                            
                            msdfiles = sorted(msdfiles, key=lambda x: x.split('msd')[1].split('.')[0])
                            for msdfile in msdfiles:
                                df = pd.read_csv(msdfile, encoding="utf-8")
                                df.columns = ['data']
                                df[['frame','msd']] = df['data'].str.split(' ', expand=True)
                                df['element'] = msdfile.split('/')[-1].split('.')[0].split('msd')[1]
                                dfall = pd.concat([dfall,df[['frame','msd','element']]],axis=0)
                            dfall['frame'] = dfall['frame'].astype(int)-int(ignoredtime.get())*1000/float(timestep.get())
                            dfall['msd'] = dfall['msd'].astype(float)
                            dfall.insert(1,'time',round(dfall['frame']*float(timestep.get())*0.001,3))
                            dfall.insert(3,'rmsd',dfall['msd']**0.5)
                            print('# data of rmsd are:')
                            print(dfall.columns.tolist())
                            dfall.to_csv(outpath + 'dataofrmsd.csv', encoding='utf-8-sig', index=False)
                        else:
                            print("# Error: no msd file was found, please check it!")
                    if 'chunk' in modelist:
                        # chunk多文件读取。
                        chunkread = os.listdir(glob.glob(readpath)[0]); chunkfiles = []
                        for g in chunkread:
                            if  (os.path.isfile(glob.glob(readpath + g)[0])) & ('chunk' in g):
                                chunkfiles.append(g)
                        for k in chunkfiles:
                            chunkfile = glob.glob(readpath + k)[0]
                            chunkf = open(chunkfile, "r", encoding=encode.get())
                            chunklines = chunkf.read().splitlines()                    # 去掉换行符'\n'
                            titlelines = []
                            for i in range(10):
                                if '#' in chunklines[i]: titlelines +=[i]
                            if len(titlelines) == 3:
                                # 提取列名
                                titleframe = chunklines[titlelines[-2]].strip().split(' ')[1:]
                                titlechunk = chunklines[titlelines[-1]].strip().split(' ')[1:]
                                # 整理数据
                                dfck = pd.DataFrame([i.split(' ') for i in chunklines[titlelines[-1]+1:]])
                                dfck[[0,1]] = dfck[[0,1]].replace('', method='ffill')
                                dfck = dfck.dropna(axis=0).reset_index(drop=True)
                                dfck.columns = titleframe[:2] + titlechunk
                                dfck = dfck.rename(columns={'Timestep':'frame','Number-of-chunks':'nchunk'})
                                dfck[['frame','nchunk','Chunk']] = dfck[['frame','nchunk','Chunk']].astype(int)
                                dfck[titlechunk[1:]] = dfck[titlechunk[1:]].astype(float)
                                dfck['frame'] = dfck['frame']-int(ignoredtime.get())*1000/float(timestep.get())
                                dfck['frame'] = dfck['frame'].astype(int)
                                dfck.insert(loc=1, column='time', value = round(dfck['frame']*float(timestep.get())*0.001,3))
                                print('# data of {} are:'.format(k))
                                print(dfck.columns.tolist())
                                dfck.to_csv(outpath + 'dataof' + chunkfile.split('/')[-1].split('.')[0] + '.csv', encoding='utf-8-sig', index=False)
                            else:
                                print('# Error: the chunk data format is not recognizable, may be a misunderstanding under Linux!')
                    if 'OVITO' in modelist:
                        if 'ovito' in readfolder:
                            ovitoread = os.listdir(readpath);ovitodir=[];ovitofile=[]
                            for g in ovitoread:
                                if os.path.isdir(readpath + g): ovitodir.append(g)
                                elif os.path.isfile(readpath + g): ovitofile.append(g)
                            for k in ovitodir:                 # k为ovito数据文件夹
                                dfovitoall = pd.DataFrame()
                                # 提取列名信息
                                for h in os.listdir(readpath + k):
                                    if os.path.isfile(readpath + k+ '/'+h):
                                        ovitof0 = glob.glob(readpath + k+ '/'+h)[0]
                                        ovitof = open(ovitof0, "r", encoding=encode.get())                # encoding="UTF-8"指定UTF-8编码读取。
                                        ovitolines = ovitof.read().splitlines()                           # 去掉换行符'\n'
                                        linelist=''
                                        for i in range(len(ovitolines)-1):
                                            if (ovitolines[i][0] =='#') & (ovitolines[i+1][0] !='#'):
                                                for t in re.split(r'("[^"]*")',ovitolines[i][2:]):                      
                                                    if '"'in t:t=t.replace(' ','')[1:-1]
                                                    linelist += t
                                                columnslist=linelist.split(' ');break
                                # 建立数据表格
                                for h in os.listdir(readpath + k):
                                    if os.path.isfile(readpath + k + '/' + h):
                                        # 读取文件后缀为frame。
                                        frame = int(h.split('.')[1])*int(thermostep.get())
                                        ovitof0 = glob.glob(readpath + k+ '/'+h)[0]
                                        ovitof = open(ovitof0, "r", encoding=encode.get())                # encoding="UTF-8"指定UTF-8编码读取。
                                        ovitolines = ovitof.read().splitlines()                    # 去掉换行符'\n'
                                        dfovito = pd.DataFrame(re.split(r' +', j) for j in ovitolines)
                                        dfovito = dfovito[dfovito[0]!='#'].reset_index(drop=True)[list(range(len(columnslist)))]
                                        dfovito.columns=columnslist
                                        dfovito.insert(loc=0, column='frame', value=frame)
                                        dfovito['frame'] = dfovito['frame']-int(ignoredtime.get())*1000/float(timestep.get())
                                        dfovito.insert(loc=1, column='time',value=round(frame*float(timestep.get())*0.001,3))
                                        dfovitoall = pd.concat([dfovitoall,dfovito],axis=0)
                                dfovitoall[columnslist[0]] = dfovitoall[columnslist[0]].astype(float)
                                dfovitoall['frame'] = dfovitoall['frame'].astype(int)
                                dfovitoall=dfovitoall.sort_values(by=['frame',columnslist[0]], ascending=True)
                                print('{} data are:'.format(k))
                                print(dfovitoall.columns.tolist())
                                # 输出最大键长值。
                                if k =='bondlength':
                                    print('# Max Bond Length are:')
                                    for i in dfovitoall.columns[3:]:
                                        print('  '+i+': '+str('%.3f' % dfovitoall[dfovitoall[i]!=str(0)]['Length'].max())+' Å')
                                if ovitodir.index(k)==0:                                 # 删除上次分析生成汇总文件                 
                                    dfovitoall.to_excel(outpath+'dataofovito.xlsx', "{}".format(k),index=False)
                                else:
                                    with pd.ExcelWriter(outpath+'dataofovito.xlsx', mode='a', engine="openpyxl") as writer:
                                        dfovitoall.to_excel(writer, "{}".format(k), index=False)
                        else:
                            print("# Error: please set foldername containing 'ovito' to read for ovito analysis!")
                    # @2023/12/13：修改reactlist和productlist为reacts和products，并改为列表格式。
                    if 'VARxMD' in modelist:                         # react分析模块
                        reactfile = glob.glob(readpath + dictfile['varxmd'])[0]
                        reactf = open(reactfile, "r", encoding=encode.get())                # encoding="UTF-8"指定UTF-8编码读取。
                        reactlines = reactf.read().splitlines()        # 每行末尾没有\n
                        reactlist=[];reactlist+=[i for i in reactlines if ('Timestep' not in i)& (i!='')]
                        framelist=[];framelist+=[i for i in reactlines if 'Timestep' in i]
                        dfreact=pd.DataFrame();dfreactnet=pd.DataFrame     # 建立两个空列表
                        # 增加列表内容
                        dfreact['frame'] = pd.Series([re.split(r' +', i)[1].split('(')[0] for i in framelist]).astype(int)-int(ignoredtime.get())*1000/float(timestep.get())
                        dfreact['time']= round(dfreact['frame']*float(timestep.get())*0.001,3)
                        dfreact['endtime'] = (dfreact['frame']+int(thermostep.get()))*float(timestep.get())*0.001
                        dfreact['num'] = pd.Series([re.split(r' +', i)[1].split('=')[1] for i in reactlist]).astype(int)
                        dfreact['reacts0']=pd.DataFrame([' '.join(re.split(r' +', re.split('  ->  ', i)[0])[2:]) for i in reactlist])
                        dfreact['arrow'] = ' -> '
                        dfreact['products0']=pd.DataFrame([re.split('  ->  ',i)[1] for i in reactlist])
                        # 建立不含编号化合物列表
                        reactsnet=[];reactsnet+= [re.sub('[(]+[\d]+[)]', '', j) for j in dfreact['reacts0'].values.tolist()]
                        productsnet=[];productsnet+= [re.sub('[(]+[\d]+[)]', '', j) for j in dfreact['products0'].values.tolist()]          
                        dfreactnet0 = pd.concat([dfreact[['frame','time','endtime','num']],pd.DataFrame({'reacts0':reactsnet,'arrow':' -> ', 'products0':productsnet})],axis=1)
                        dfreactnet = dfreactnet0.groupby(['frame','time','endtime','reacts0','arrow','products0']).num.sum().reset_index(drop=False)[['frame','time','endtime','num','reacts0','arrow','products0']]
                        # 提取反应物列和生成物表。
                        dfreact['reacts']=dfreact['reacts0'].apply(lambda x:x.split(' + ')).apply(lambda x: [list_compound_nosub(i.strip(),rule)+'('+i.strip().split('(')[1] for i in x])
                        dfreact['products']=dfreact['products0'].apply(lambda x:x.split(' + ')).apply(lambda x: [list_compound_nosub(i.strip(),rule)+'('+i.strip().split('(')[1] for i in x])                      
                        dfreact['reaction']=(dfreact['reacts0']+dfreact['arrow']+dfreact['products0']).apply(lambda x: list_react_nosub([x],rule)[0])
                        dfreact = dfreact.sort_values(by=['frame', 'num'], ascending=[True, False]).reset_index(drop=False)[['frame', 'time', 'endtime', 'num', 'reacts', 'products', 'reaction']]
                        # 提取反应物和生成物 (无编号) 列表，并去除重复反应式。
                        dfreactnet['reacts'] = dfreactnet['reacts0'].apply(lambda x: x.split(
                            ' + ')).apply(lambda x: list(dict.fromkeys([list_compound_nosub(i.strip(),rule) for i in x])))
                        dfreactnet['products'] = dfreactnet['products0'].apply(lambda x: x.split(
                            ' + ')).apply(lambda x: list(dict.fromkeys([list_compound_nosub(i.strip(),rule) for i in x])))
                        # 定义筛选重复化学式函数
                        def sumformula(str0):
                            list1 =[]; list2=[]; 
                            for i in str0.split(' + '):
                                list1 += [i.lstrip('0123456789')]
                                list2 += re.findall(r'^\d', i) if re.findall(r'^\d', i)!=[] else ['1']
                            list2 = list(map(int, list2))
                            list3 = list(dict(Counter(list1)).keys())
                            list5=[]
                            for i in list3:
                                list4=[j for j,x in enumerate(list1) if x==i]
                                no = sum([list2[j] for j in list4])
                                list5 +=[str(no)+i if no !=1 else i]
                            return ' + '.join(list5[:])
                        listreaction0=[];listreaction1=[]
                        for j in dfreactnet['reacts0'].tolist():listreaction0+=[sumformula(j)]
                        for j in dfreactnet['products0'].tolist():listreaction1+=[sumformula(j)]
                        dfreactnet['reaction'] = (pd.DataFrame({'reacts0':listreaction0})['reacts0']+dfreactnet['arrow']+pd.DataFrame({'products0':listreaction1})['products0']).apply(lambda x: list_react_nosub([x],rule)[0])
                        dfreactnet1 = dfreactnet.groupby(['frame', 'reaction']).num.sum().reset_index(drop=True)
                        dfreactnet2 = dfreactnet[['frame','time','endtime','reacts0','products0','reacts','products','reaction']].groupby(['frame', 'reaction']).first().reset_index(drop=False)
                        dfreactnet = pd.concat([dfreactnet1,dfreactnet2],axis=1)
                        # 去掉反应物与产物分子式相同的反应。
                        dfreactnet=dfreactnet[dfreactnet['reacts0']!=dfreactnet['products0']].reset_index(drop=True)
                        dfreactnet = dfreactnet.sort_values(by=['frame', 'num'], ascending=[True, False]).reset_index(drop=False)[['frame', 'time', 'endtime', 'num', 'reacts', 'products', 'reaction']]
                        dfreact['frame'],dfreactnet['frame'] = dfreact['frame'].astype(int),dfreactnet['frame'].astype(int)
                        dfreact.to_csv(outpath+'dataofvarxmd.csv', encoding='utf-8-sig', index=False)
                        dfreactnet.to_csv(outpath+'dataofvarxmdnet.csv', encoding='utf-8-sig', index=False)
                        print('# data of varxmd are:')
                        print(dfreact.columns.tolist())
                        print('# data of varxmdnet are:')
                        print(dfreactnet.columns.tolist())
                    if 'ChemTraYzer' in modelist:                    # chem分析模块
                        # 根据正则表达式提取目标数据为列表，检索chemtrayzer文件夹。
                        if 'chemtrayzer' in readfolder:
                            chemread = os.listdir(readpath)
                            # 根据正则表达式文件名筛选目标文件。
                            chemfile = [s for s in chemread if all(substring in s for substring in chemtrayzerfilename.split('*'))]
                            # 从列表中区分每个生成数据。
                            if len(chemfile) != 0:
                                chemrate, chemreac, chemspec = '','',''           # 给文件名赋空值，用于后续判断文件存在。
                                for i in chemfile:
                                    if 'rate' in i: chemrate = i
                                    elif 'reac' in i: chemreac = i
                                    elif 'spec' in i: chemspec = i
                                dfrate = pd.read_csv(readpath + chemrate,sep=';',header=0,index_col=None, encoding=encode.get()).dropna(axis=0)
                                dfreac = pd.read_csv(readpath + chemreac,sep=';',header=0,index_col=None, encoding=encode.get()).dropna(axis=0)
                                dfspec0 = pd.read_csv(readpath + chemspec, sep=';',header=0, index_col=None, encoding=encode.get())
                                dfreac.insert(loc=0,column='frame',value=dfreac['t [steps]'].astype(int)-int(ignoredtime.get())*1000/float(timestep.get()))   # 增加'frame'列
                                dfreac.insert(loc=1,column='time',value=round(dfreac['frame']*float(timestep.get())*0.001,3))   # 增加'time'列
                                dfreac = dfreac.drop('t [steps]', axis=1).reset_index(drop=True)
                                # 合并dfreac各列R<ID>值为列表，
                                dfreac['num'] = dfreac.iloc[:, 2:].stack().groupby(level=0).apply(list)
                                dfreac['R<ID>'] = dfreac['num'].apply(lambda x: ['R'+str(i) for i in range(len(x)) if x[i] != '0'])
                                dfreac['num'] = dfreac['num'].apply(lambda x: [i for i in x if i not in ['0',0]])  # @2024/12/24：补充数字0识别。
                                dfreac = dfreac[['frame', 'time', 'num', 'R<ID>']][dfreac['num'].str.len() != 0]
                                # 拆分num和R<ID>为多行，对应同时存在多个反应情况。
                                dfreac = pd.DataFrame([[f, t, n, r] for f, t, N, R in dfreac.values for n,r in zip(N,R)], columns=dfreac.columns)
                                dfreac.to_csv("F:\\ganqiang\\test\\rdx\\data\\dfreac.csv")
                                dfrate.to_csv("F:\\ganqiang\\test\\rdx\\data\\dfrate.csv")
                                # 分析净反应次数，正反应减去逆反应。
                                # dfrate1 = dfrate[~dfrate['R<ID>'].str.contains('\*')].reset_index()
                                # dfrate2 = dfrate[dfrate['R<ID>'].str.contains('\*')].reset_index()
                                # dfrate2['N*'] = dfrate2['N']
                                # dfrate = pd.concat([dfrate1, dfrate2['N*']],axis=1).drop('index', axis=1)
                                # dfrate['Nnet']=dfrate['N']-dfrate['N*']
                                # dfrate.rename(columns={'N': 'sumpos', 'N*': 'sunrev', 'Nnet': 'sumnet', "Formula's":'reaction'}, inplace=True)
                                # # reac和rate数据融合为dfreac。
                                # dfreac = pd.merge(dfreac, dfrate, how='outer', on='R<ID>').dropna(axis=0).sort_values('frame', ascending=True)
                                # dfreac['num'] = dfreac['num'].astype(int)
                                # 拆分spec数据为dfspec和dfsmiles，之后重新合并为dfsepc。
                                dfsmiles = dfspec0.loc[0, :].dropna(axis=0).reset_index(drop=False)
                                dfsmiles.columns = ['S<ID>','SMILES']
                                dfspec = dfspec0.dropna(axis=0)
                                dfspec.insert(loc=0,column='frame',value=dfspec['t [steps]'].astype(int)-int(ignoredtime.get())*1000/float(timestep.get()))   # 增加'frame'列
                                dfspec.insert(loc=1, column='time', value=round(dfspec['frame']*float(timestep.get())*0.001,3))
                                dfspec = dfspec.drop('t [steps]', axis=1).reset_index(drop=True)
                                dfspec['num'] = dfspec.iloc[:, 2:].stack().groupby(level=0).apply(list)
                                dfspec['S<ID>'] = dfspec['num'].apply(lambda x: ['S'+str(i) for i in range(len(x)) if x[i] != '0'])
                                dfspec['num'] = dfspec['num'].apply(lambda x: [x[i] for i in range(len(x)) if x[i] != '0'])
                                dfspec = dfspec[['frame','time','num','S<ID>']][dfspec['num'].str.len()!=0]
                                # 拆分dfspec中num和S<ID>为多行，对应同时存在多个物种情况。
                                dfspec = pd.DataFrame([[f, t, n, s] for f, t, N, S in dfspec.values for n,s in zip(N,S)], columns=dfspec.columns)
                                dfspec = pd.merge(dfspec,dfsmiles,how='outer',on='S<ID>').dropna(axis=0)
                                # 从dfreac中提取化学式，加入dfspec中。
                                dfSIDcompound = pd.DataFrame()
                                dfSIDcompound['S<ID>'] = dfreac["S<ID>"].apply(lambda x: [i for i in x.split(' ') if (i != '+') & (i != "->")])
                                dfSIDcompound['molecule'] = dfreac["reaction"].apply(lambda x: [i for i in x.split(' ') if (i != '+') & (i != "->")])
                                dfSIDcompound = pd.DataFrame([[s,c] for S,C in dfSIDcompound.values for s,c in zip(S,C)], columns=dfSIDcompound.columns)
                                dfSIDcompound = dfSIDcompound.groupby('S<ID>').first().reset_index(drop=False)
                                dfspec = pd.merge(dfspec,dfSIDcompound,how='outer',on='S<ID>').dropna(axis=0).sort_values('frame', ascending=True).reset_index(drop=True)
                                dfspec = dfspec.groupby(['frame','S<ID>']).first().reset_index(drop=False)
                                # 输出dfreac和dfspec到excl文件。
                                # dfreac.to_excel(outpath + 'dataofchemtrayzer.xlsx', "reac",index=False)
                                # with pd.ExcelWriter(outpath + 'dataofchemtrayzer.xlsx', mode='a', engine="openpyxl") as writer:
                                #     dfspec.to_excel(writer, "spec", index=False)
                                dfreac.to_csv(outpath + 'dataofchemreac.csv', encoding='utf-8-sig', index=False)
                                dfspec.to_csv(outpath + 'dataofchemspec.csv', encoding='utf-8-sig', index=False)
                                print('# data of chemreac are:')
                                print(dfreac.columns.tolist())
                                print('# data of chemspec are:')
                                print(dfspec.columns.tolist())
                            else:
                                print("# Error: target file(s) is empty, please check 'chemtrayzer' folder and filerules!")
                        else:
                            print("# Error: please set foldername containing 'chemtrayzer' to read for ovito analysis!")
                    if 'ReacNet' in modelist:
                        if 'reacnet' in readfolder:
                            reacread = os.listdir(readpath)
                            # 根据正则表达式文件名筛选目标文件。
                            reacfile = [s for s in reacread if all(substring in s for substring in reacnetfilename.split('*'))]
                            # 从列表中区分每个生成数据。
                            if len(reacfile) != 0:
                                reacspecies, reacroute, reactable, reactionabcd, reaction, reacmoname = '','','','','',''           # 给文件名赋空值，用于后续判断文件存在。
                                for i in reacfile:
                                    if 'species' in i: reacspecies = i
                                    elif 'route' in i: reacroute = i
                                    elif 'table' in i: reactable = i
                                    elif 'reaction' in i:
                                        if 'reactionabcd' in i: reactionabcd = i
                                        else: reaction = i
                                    elif 'moname' in i: reacmoname = i
                                # 计算反应速率
                                try:
                                    cell = np.eye(3) * 3.7601e1  # in unit Angstrom
                                    # timestep = 0.1  # in unit fs
                                    rates = calculate_rate(readpath + reacspecies,readpath + reactionabcd, cell, float(timestep.get()))
                                    dfrate = pd.DataFrame.from_dict(rates, orient='index')
                                    dfrate = dfrate.reset_index(drop=False)
                                    dfrate.columns = ['reactionsmile','rate']
                                except:
                                    print('# Warning: Something wrong occurs when calculate reaction rates using species and reactionabcd files.')
                                # 设置目标分析文件
                                if reacmoname != '':
                                    dfmoname = pd.read_csv(readpath + reacmoname, sep=' ',header=None,index_col=None, encoding=encode.get())
                                    dfmoname.columns = ['moleculesmile', 'atomindex','atombond']
                                    dfmoname.insert(loc=1, column='molecule', value=dfmoname['moleculesmile'].apply(lambda x: smile2formula(x,rule)))
                                    dfmoname['idlist'] = dfmoname['atomindex'].apply(lambda x:[int(i)+1 for i in x.split(';')])
                                    dfmoname['bondlist'] = dfmoname['atombond'][dfmoname['atombond'].notnull()].apply(lambda x:[[int(j)+1 for j in i.split(',')[:-1]] for i in x.split(';')])
                                        ## x.split(';')报错'float' object has no attribute 'split'。
                                    dfmoname['bondnlist'] = dfmoname['atombond'][dfmoname['atombond'].notnull()].apply(lambda x:[int(i.split(',')[-1]) for i in x.split(';')])
                                    dfmoname = dfmoname.drop(columns=['atomindex', 'atombond'])
                                else: print('Warning: ' + reacmoname + "file is not exist, please check if it is in 'reacnet' folder")
                                if reaction != '':
                                    dfreaction = pd.read_csv(readpath + reaction, sep=' ', header=0, index_col=None, encoding=encode.get()).dropna(axis=0)
                                    dfreaction.columns = ['number','reactionsmile']
                                    dfreaction['reactsmile'] = dfreaction['reactionsmile'].apply(lambda x: x.split('->')[0])
                                    dfreaction['productsmile'] = dfreaction['reactionsmile'].apply(lambda x: x.split('->')[1])
                                    # @2023/12/13：与其他数据分析统一，把react和product改为列表reacts和products。
                                    dfreaction['reacts'] = dfreaction['reactsmile'].apply(lambda x: smile2formula(x,rule))
                                    dfreaction['products'] = dfreaction['productsmile'].apply(lambda x: smile2formula(x,rule))
                                    dfreaction['reaction'] = dfreaction['reacts']+' -> '+ dfreaction['products']
                                    dfreaction['reacts'] = dfreaction['reacts'].apply(lambda x: [x])
                                    dfreaction['products'] = dfreaction['products'].apply(lambda x: [x])
                                else: print('Warning: ' + reaction + "file is not exist, please check if it is in 'reacnet' folder")
                                if reactionabcd != '':
                                    try:
                                        dfreactionabcd = pd.read_csv(readpath + reactionabcd, sep=' ', header=0, index_col=None, encoding=encode.get()).dropna(axis=0)
                                        dfreactionabcd.columns = ['number','reactionsmile']
                                        dfreactionabcd['reactsmile'] = dfreactionabcd['reactionsmile'].apply(lambda x: x.split('->')[0])
                                        dfreactionabcd['productsmile'] = dfreactionabcd['reactionsmile'].apply(lambda x: x.split('->')[1])
                                        # @2023/12/13：与其他数据分析统一，把react和product改为列表reacts和products。
                                        dfreactionabcd['reacts'] = dfreactionabcd['reactsmile'].apply(lambda x: [smile2formula(i,rule) for i in x.split('+')])
                                        dfreactionabcd['products'] = dfreactionabcd['productsmile'].apply(lambda x: [smile2formula(i,rule) for i in x.split('+')])
                                        dfreactionabcd['reaction'] = dfreactionabcd['reacts'].apply(lambda x: ' + '.join(x))+' -> '+ dfreactionabcd['products'].apply(lambda x: ' + '.join(x))
                                        try:
                                            dfreactionabcd = pd.merge(dfreactionabcd,dfrate, how='left',on='reactionsmile')
                                        except:
                                            print('# Warning: Reaction rate was not calculated, and it would not be included in reactionabcd data!')
                                    except:
                                        dfreactionabcd = pd.DataFrame()
                                        print('# Warning: Reactionabcd file was not loaded, because of read error!')
                                else: print('# Warning: ' + reactionabcd + "file is not exist, please check if it is in 'reacnet' folder")
                                if reacspecies != '':
                                    speciesfile = glob.glob(readpath + reacspecies)[0]
                                    speciesf = open(speciesfile, "r", encoding=encode.get())
                                    specieslines = speciesf.read().splitlines()
                                    specieslist = []
                                    for j in range(len(specieslines)):
                                        frame = specieslines[j].split(' ')[1].split(':')[0]
                                        for k in range(len(specieslines[j].split(' '))):
                                            if (k*2+3)<len(specieslines[j].split(' ')):
                                                moleculesmile = specieslines[j].split(' ')[2+k*2]
                                                number = specieslines[j].split(' ')[3+k*2]
                                                specieslist += [[frame, moleculesmile, number]]
                                    dfspecies = pd.DataFrame(specieslist, columns=['frame', 'moleculesmile','number'])
                                    dfspecies['frame'] = dfspecies['frame'].astype(int)-int(ignoredtime.get())*1000/float(timestep.get())
                                    dfspecies['frame'] = dfspecies['frame'].astype(int)
                                    dfspecies.insert(loc=1, column='time', value=round(dfspecies['frame']*float(timestep.get())*0.001,3))
                                    dfspecies['molecule'] = dfspecies['moleculesmile'].apply(lambda x: smile2formula(x,rule))
                                else: print('# Warning: ' + reacspecies + "file is not exist, please check if it is in 'reacnet' folder")
                                if reacroute != '':
                                    routefile = glob.glob(readpath + reacroute)[0]
                                    routef = open(routefile, "r", encoding=encode.get())
                                    routelines = routef.read().splitlines()
                                    routelist = []
                                    for j in range(len(routelines)):
                                        atomid = routelines[j].split(' ')[1]
                                        elementid = routelines[j].split(' ')[2].split(':')[0]
                                        for k in range(len(routelines[j].split(' '))):
                                            if (k*3+4)<len(routelines[j].split(' ')):
                                                track = routelines[j].split(' ')[3+k*3]
                                                moleculesmile = routelines[j].split(' ')[4+k*3]
                                                routelist += [[atomid, elementid, track,moleculesmile]]
                                    dfroute = pd.DataFrame(routelist, columns=['id', 'element','track','moleculesmile'])
                                    # 用dfspecies中frame值，填充dfroute。
                                    framelist = list(set(dfspecies['frame'].astype(int).tolist()))
                                    framelist.sort()
                                    dfroute[['track','id']] = dfroute[['track','id']].astype(int)
                                    dfroute['frame'] = dfroute['track'].apply(lambda x: framelist[x]).astype(int)-int(ignoredtime.get())*1000/float(timestep.get())
                                    dfroute['molecule'] = dfroute['moleculesmile'].apply(lambda x: smile2formula(x,rule))
                                    dfroute = dfroute.sort_values(by=['frame','id'])
                                    dfroute.insert(loc=0, column='time', value=round(dfroute['frame']*float(timestep.get())*0.001,3))
                                    try:    
                                        dumpfile = glob.glob(outpath + dumpfilename2)[0].replace('\\','/')
                                        # dfdump = pd.read_csv(dumpfile, header=0,index_col=None, encoding="utf-8")
                                        dfdump = autocode(dfumpfile, 'pandas')
                                        dfdump[['frame','id','type']] = dfdump[['frame','id','type']].astype(int)
                                        dfdump[['time','x','y','z']] = dfdump[['time','x','y','z']].astype(float)
                                        dfroute = pd.merge(dfroute,dfdump[['frame','id','x','y','z']], how='left',on=['frame','id'])
                                    except:
                                        print('# Warning: {} file does not exist, route file will not merge with data of dump.'.format(dumpfilename2))
                                else:
                                    print('# Warning: ' + reacroute + "file is not exist, please check if it is in 'reacnet' folder")
                                # 自定义方法取代route数据。
                                try:
                                    dfmanual = pd.merge(dfroute,dfmoname,how='left',on=['moleculesmile','molecule'])
                                    dfmanual = dfmanual[dfmanual.apply(lambda x: x['id'] in x['idlist'], axis=1)].reset_index(drop=True)
                                    dfmanual['xyz'] = dfmanual.apply(lambda x: (x['x'], x['y'], x['z']), axis=1)
                                    dfmanual = dfmanual.groupby(['frame','id','element']).first().reset_index(drop=False)
                                    dfmanual['idlist'] = dfmanual['idlist'].apply(tuple)
                                    df1 = dfmanual[['frame','id','element','idlist','xyz']].groupby(['frame', 'idlist']).agg({'id': list, 'element': list,'xyz':list}).reset_index()
                                    ## 比较idlist和聚合后id，bool用于去除错误聚合数据。
                                    df1['bool'] = df1.apply(lambda row: np.array_equal(row['idlist'], row['id']), axis=1)
                                    dfmanual= dfmanual.drop(['id', 'element','x','y','z','xyz'], axis=1).groupby(['frame','idlist']).first().reset_index(drop=False)
                                    dfmanual = pd.merge(dfmanual,df1[['frame','idlist','element','xyz','bool']],how='left',on=['frame','idlist'])
                                    # 根据idlist存在交集判断发生反应，给予反应路径编号path。supported by PromptsZone
                                    # dfmanual['idlist'] = dfmanual['idlist'].apply(eval)  已设置为tuple值。
                                    # 定义函数用于比较两行之间的idlist是否存在交集，跳过相同frame数据。
                                    def has_intersection(row1, row2):
                                        if row1['frame'] == row2['frame']:
                                            # 如果 frame 相同，则跳过比较
                                            return False
                                        intersection = set(row1['idlist']) & set(row2['idlist'])
                                        return len(intersection) > 0
                                    # 初始化 path 列的值为 -1
                                    dfmanual['path'] = -1
                                    # 遍历所有行，依次确定每个反应路径的编号（从 0 开始）
                                    path_index = 0
                                    for i in range(len(dfmanual)):
                                        if dfmanual.loc[i, 'path'] == -1:
                                            # 如果当前行还没有被处理过，则将其加入到当前反应路径中
                                            dfmanual.loc[i, 'path'] = path_index
                                            for j in range(i+1, len(dfmanual)):
                                                if has_intersection(dfmanual.iloc[i], dfmanual.iloc[j]):
                                                    # 如果存在交集，则将 j 行归为该反应路径，并标记已处理过
                                                    dfmanual.loc[j, 'path'] = path_index
                                            # 处理完所有属于当前反应路径的行，进入下一个反应路径
                                            path_index += 1
                                    dfmanual[['frame','track','time','path','moleculesmile','molecule','idlist','element','xyzrange','xyz','bondlist','bondnlist']].to_excel(outpath+'dataofreacnetgenerator.xlsx', "manual",index=False)
                                    with pd.ExcelWriter(outpath+'dataofreacnetgenerator.xlsx', mode='a', engine="openpyxl") as writer:
                                        # 2024/12/16：增加if条件判断目标df是否存在且不为空。
                                        if 'dfreaction' in locals() and not dfreaction.empty:
                                            dfreaction.to_excel(writer, "reaction", index=False)
                                        if 'dfreactionabcd' in locals() and not dfreactionabcd.empty:
                                            dfreactionabcd.to_excel(writer, "reactionabcd", index=False)
                                        if 'dfspecies' in locals() and not dfspecies.empty:
                                            dfspecies.to_excel(writer, "species", index=False)
                                except:
                                    print('# Warning: manual analysis failled, please check moname and route datas!')
                                    dfmoname.to_excel(outpath +'dataofreacnetgenerator.xlsx', "moname",index=False)
                                    with pd.ExcelWriter(outpath +'dataofreacnetgenerator.xlsx', mode='a', engine="openpyxl") as writer:
                                        # 2024/12/16：增加if条件判断目标df是否存在且不为空。
                                        if 'dfroute' in locals() and not dfroute.empty:
                                            dfroute.to_excel(writer, "route", index=False)
                                        if 'dfreaction' in locals() and not dfreaction.empty:
                                            dfreaction.to_excel(writer, "reaction", index=False)
                                        if 'dfreactionabcd' in locals() and not dfreactionabcd.empty:
                                            dfreactionabcd.to_excel(writer, "reactionabcd", index=False)
                                        if 'dfspecies' in locals() and not dfspecies.empty:
                                            dfspecies.to_excel(writer, "species", index=False)
                            else:
                                print("Error: target file(s) is empty, please check 'reacnet' folder and filerules!")
                        else:
                            print("# Error: please set foldername containing 'reacnet' to read for ovito analysis!")
                    if 'MS.xcd' in modelist:
                        # 读取materials studio文件。
                        xcdfiles = glob.glob(readpath + dictfile['xcd'])
                        # @2024/7/22：过滤xcdfiles，只保留以下四个文件。
                        # targetfiles = ['Cell','Density','Energies','Temperature','MSD','Potential energy components','XRD']
                        # xcdfiles = [i for i in xcdfiles if any(j in i.split('/')[-1] for j in targetfiles)]
                        xcdfiles = [i for i in xcdfiles if '.xcd' in i.split('/')[-1]]
                        dfxcd,dfframe,dfxrd = pd.DataFrame(),pd.DataFrame(),pd.DataFrame()    # dfframe保存逐帧数据。
                        for xcdfile in xcdfiles:
                            f = open(xcdfile, "r", encoding='utf-8')                # 指定编码读取。
                            lines = f.read().splitlines()
                            for n,i in enumerate(lines):
                                # @2024/8/2：增加对XRD数据的单独判断。
                                if ('SERIES_2D UniqueID' in i)&((('XRD' in xcdfile)& ('Observed Reflections' not in i)) or ('XRD' not in xcdfile)):
                                    pattern = r'"(.*?)"'   # 匹配引号内容
                                    matches = re.findall(pattern, i)
                                    column,num = matches[1],int(matches[2])
                                    data = []
                                    for j in range(n+1,n+num+1):
                                        data.append(re.findall(pattern, lines[j])[0])
                                    df2 = pd.DataFrame([k.split(',') for k in data], columns=['time',column])
                                    df2['time'] = df2['time'].astype(float)
                                    if 'Potential energy components' in xcdfile:
                                        df2.insert(loc=0, column='frame', value= (df2['time']-1)*int(thermostep.get()))
                                        df2['time'] = round(df2['frame']*float(timestep.get())*0.001,3)
                                        if len(dfframe) == 0: dfframe = df2
                                        else: dfframe = pd.merge(dfframe,df2,on=['frame','time'],how='outer')
                                    elif 'XRD' in xcdfile:
                                        df2.columns = ['2theta',column.split()[0]]
                                        if len(dfxrd) == 0: dfxrd = df2
                                        else: dfxrd = pd.merge(dfxrd,df2,on='2theta',how='outer')
                                    else:
                                        if len(dfxcd) == 0: dfxcd = df2
                                        else: dfxcd = pd.merge(dfxcd,df2,on='time',how='outer')
                        # 分别输出dfxcd和dfframe。
                        if len(dfxcd) > 0:
                            dfxcd['time'] = dfxcd['time'].apply(lambda x: round(x,3))
                            dfxcd.to_csv(outpath + 'dataofmsxcd.csv', encoding='utf-8-sig', index=False)
                        if len(dfframe) > 0:
                            # 修正列名。
                            columns2 = [i.split(': Running average')[0] if ': Running average' in i else i for i in dfframe.columns.tolist()]
                            dfframe.columns = columns2
                            dfframe.to_csv(outpath + 'dataofmsframe.csv', encoding='utf-8-sig', index=False)
                        if len(dfxrd) > 0:
                            dfxrd.to_csv(outpath + 'dataofmsxrd.csv', encoding='utf-8-sig', index=False)
                        print('# data of MS.xcd file are:')
                        if len(dfxcd) > 0: print(dfxcd.columns.tolist())
                        if len(dfframe) > 0: print(dfframe.columns.tolist())
                        # print('****************************************************************************')
                    if 'General' in modelist:
                        if genread.get().strip() !='':
                            genfiles = glob.glob(readpath + genread.get().strip())
                            if len(genfiles)>0:
                                genfiles = [file.replace('\\','/') for file in genfiles]
                                dfall = pd.DataFrame()
                                for n, file in enumerate(genfiles):
                                    if file.split('.')[-1] == 'csv':
                                        # dfgen = pd.read_csv(file)
                                        dfgen = autocode(file, 'pandas')
                                    else:
                                        with open(file,'rb') as f:
                                            result = chardet.detect(f.read(1000))       # 读取前1000字节
                                        if genheader.get().strip() != '': headerset = int(genheader.get().strip())
                                        else: headerset = None
                                        # dfgen = pd.read_csv(file, header=headerset, sep='\s+', encoding=result['encoding'])
                                        dfgen = autocode(file, 'pandas', header=headerset, sep='\s+')
                                    # 读取输出路径。
                                    if (gennameby.get() == 'suffix')&(genrename.get().strip() != ''):
                                        outpath0 = outpath + '.'.join(file.split('/')[-1].split('.')[:-1])+'.'+genrename.get().strip()+'.' + file.split('.')[-1]
                                    elif (gennameby.get() == 'fullname')&(genrename.get().strip() != ''):
                                        if len(genfiles) > 1: outpath0 = outpath + '.'.join(genrename.get().strip().split('.')[:-1])+'.{}.'.format(i+1)+genrename.get().strip().split('.')[-1]
                                        else: outpath0 = outpath + genrename.get().strip()
                                    elif gennameby.get() == 'replace':
                                        outpath0 = outpath + file.split('/')[-1]
                                    # filter。  
                                    if genfilterby.get() != '':
                                        for n,file in enumerate(genfiles):
                                            if genfilterby.get() in ['dropna.x','dropna.y']:
                                                if genfilterby.get() == 'dropna.x':axisset = 0
                                                elif genfilterby.get() == 'dropna.y':axisset = 1
                                                if 'thresh' in genfilter.get().strip():
                                                    threshset = int(genfilter.get().strip().replace('thresh.'))
                                                    dfgen = dfgen.dropna(axis=axisset,thresh = threshset)
                                                else:
                                                    dfgen = dfgen.dropna(axis=axisset)
                                            elif genfilterby.get() == 'dropna.xy':
                                                if 'thresh' in genfilter.get().strip():
                                                    threshset = int(genfilter.get().strip().replace('thresh.'))
                                                    dfgen = dfgen.dropna(axis=0,thresh = threshset).dropna(axis=1,thresh = threshset)
                                                else:
                                                    dfgen = dfgen.dropna(axis=0).dropna(axis=1)
                                            elif genfilterby.get() in ['keepcolumns','delcolumns']:
                                                try:
                                                    targetlist = [i.strip() for i in genfilter.get().strip().split(':')]
                                                    if len(targetlist) > 0:
                                                        if (targetlist[0] == '')&(targetlist[1] != ''):
                                                            targets = dfgen.columns.tolist()[:int(targetlist[1])]
                                                        elif (targetlist[0] != '')&(targetlist[1] == ''):
                                                            targets = dfgen.columns.tolist()[int(targetlist[0]):]
                                                        elif (targetlist[0] != '')&(targetlist[1] != ''):
                                                            targets = dfgen.columns.tolist()[int(targetlist[0]):int(targetlist[1])]
                                                        if genfilterby.get() == 'keepcolumns':
                                                            dfgen = dfgen[targets]
                                                        else:
                                                            dfgen = df.drop(targets, axis=1)
                                                except:
                                                    print("# Error: filter operate failed, please check it!")
                                    # merge or concat。
                                    if (genmergetype.get() !='')&(genmergeby.get().strip() !=''):
                                        outpath0 = outpath + '.'.jion(file.replace('*','').split('.')[:-1]) + '.csv'
                                        if n == 0: dfall = dfgen
                                        else:
                                            if genmergetype.get() == 'merge':
                                                bylist = [i.strip() for i in genmergeby.get().strip().split(',')]
                                                dfall = pd.merge(dfall,dfgen, how='left',on = bylist)
                                            elif genmergetype.get() == 'concat':
                                                if genmergeby.get().strip() == 'concat.x':
                                                    dfall = pd.concat([dfall,dfgen],axis=1)
                                                elif genmergeby.get().strip() == 'concat.y':
                                                    dfall = pd.concat([dfall,dfgen],axis=0)
                                    else:
                                        if outpath0.split('.')[-1] != 'csv':
                                            outpaht0 = '.'.join(outpath0.split('.')[:-1]) + '.csv'
                                        dfgen.to_csv(outpath0, encoding='utf-8-sig', index=False)
                                if len(dfall)>0:
                                    dfall.to_csv(outpath0, encoding='utf-8-sig', index=False)
                    print('# Success: Arrange of {} folder finished with modes: {}.'.format(folder,', '.join(modelist)))
                    print('****************************************************************************')
            else:
                print('# Error: Folder(s) is empty, please set Folder(s) to read!')
    # RunButton 
    ButtonRun1 = tk.Button(tab1, text="Run", command=lambda: controller.thread_it(runarrange), width=9, fg='white', bg='blue')
    ButtonRun1.grid(row=7, column=8)

    ####################### Tab2设置 #########################
    dictpath = readlast(LMPSETTING_PATH)
    read2, export2,simulate, drawing = tk.StringVar(), tk.StringVar(), tk.StringVar(), tk.StringVar()
    # tab2 第0行设置
    # Dirpath设置，返回值inpath.get(),folders.get()
    combo(tab2,folders,"        Folders:",0,4,listitem(readitem(dictpath,'folders'),["","all"]),9,1,'')
    inpathunit(tab2,inpath,"Inpath:",0,0,24,2,readitem(dictpath,'inpath'),folders, "       Folders:",9,1,'')
    # in&out，返回值返回值read2.get(),export2.get()
    combo(tab2,read2,"          Read:",0,6,listitem(readitem(dictpath,'read2'),["data", "modify",""]),22,2,'')
    combo(tab2,export2,"        Export:",1,5,listitem(readitem(dictpath,'export2'),["analysis", "modify","data",""]),22,2,'')
    # tab2 第1行设置
    # simulate，返回值simulate.get()
    combo(tab2,simulate, "     Simulate:",1,2,listitem(readitem(dictpath,'simulate'),["","ReflectWall"]),22,2,'')
    # drawing，返回值drawing.get()
    combo(tab2, drawing, "Drawing:", 1, 0, listitem(readitem(dictpath,'drawing'),["MultiFig","Animation"]), 9, 1, 'readonly')
    # FileRule子窗口，返回列表值readitem(dictpath,'filerule2')
    submitwindow(tab2,"FileRules","320x380",50,18,10,0, LMPSETTING_PATH,'filerule2',9,'lightgray')
    filerule2 = readitem(dictpath,'filerule2')
    # check files in current path.
    filedict = {k.strip(): v.strip() for k, v in (i.split(':') for i in filerule2.split('\n') if i)}
    # 匹配simulate新增变量。
    gridlist = []
    def drawmethod(inpath, folders, read, filedict, core0, gridlist,drawing='MultiFig',simulate='None'):
        # addfig columns
        global addfig, plotx, plotxunit, analysisx, ploty, plotyunit, plotxlist, plotylist, analysisy, multidata, newparams, addfilterby, addfiltervalue, addfilterway, plottype, plotloc, plotcheck, plotchecklist, yerrortype, yerrorvalue, ylimitset, xsortset, legendsettype, legendsetvalue
        addfig,plotx,plotxunit,analysisx,ploty,plotyunit,analysisy, multidata, newparams, addfilterby, addfiltervalue, addfilterway, plottype, plotloc, yerrortype, yerrorvalue, ylimitset, xsortset, legendsettype, legendsetvalue = tk.StringVar(),tk.StringVar(),tk.StringVar(),tk.StringVar(),tk.StringVar(),tk.StringVar(),tk.StringVar(),tk.StringVar(),tk.StringVar(),tk.StringVar(),tk.StringVar(),tk.StringVar(),tk.StringVar(),tk.StringVar(),tk.StringVar(),tk.StringVar(),tk.StringVar(),tk.StringVar(),tk.StringVar(),tk.StringVar()
        if drawing == "MultiFig":
            clean(gridlist)
            global snsstyle0, palette0, marker0
            snsstyle0, palette0, marker0 = tk.StringVar(),tk.StringVar(),tk.StringVar()
            snsstyle_label, snsstyle_combo, palette_combo = combo2(tab2, "Sns&Palette:", 3, 0, snsstyle0, listitem(readitem(dictpath,'snsstyle'),["ticks","whitegrid","darkgrid","dark","white"]), 9, 1, 'readonly', palette0, listitem(readitem(dictpath,'pallette'),["tab10","tab20","tab20b","tab20c"]), 9, 1, '')
            marker_label, marker_combo = combo(tab2, marker0, "         Marker:", 3, 3, listitem(readitem(dictpath,'marker'),["o, s, D, *, p, v, ^, <, >, +,  x, h, H, d, |, -",""]), 34, 3, '')
            # plotset子窗口，返回列表值plotset
            plotset2_button = submitwindow(tab2,"PlotSet","740x350",120,17,3,7,LMPSETTING_PATH,'plotset2',9,'lightgray')                                                
            def addfigall(addfig, x, xunit, xanal, y, yunit, yanal, multi, newparam, filterby, filtervalue, filterway, yerrortype, yerrorvalue, plotloc, plotcheck, ylimit, xsort, legendtype, legendvalue):
                if (addfig != '')&(x != '')&(y != ''):
                    if ',' in multi: multiitems = '[{}]'.format(multi)
                    elif multi == '': multiitems = []
                    else: multiitems = [multi]
                    addfiglist = [i.strip() for i in addfig.split(',')]
                    ylist = ['{}'.format(i.strip()) for i in y.split(',')]
                    newparamlist = [i.strip() for i in newparam.split(',')]
                    filterbylist = [i.strip() for i in filterby.split(',')]
                    filterwaylist = [i.strip() for i in filterway.split(',')]
                    if 'between' in filterwaylist: filtervaluelist = [float(i.strip()) for i in filtervalue.split(',')]
                    else: filtervaluelist = [i.strip() for i in filtervalue.split(',')]
                    # @2025/4/1: add set to change [''] to [].
                    for i in [newparamlist, filterbylist, filtervaluelist, filterwaylist]:
                        if i == ['']: i.clear()
                    if yanal == '': yanal = []
                    elif ',' in yanal:
                        yanal = [float(y0) for y0 in yanal.replace(' ','').split(',')]
                    else: yanal = [yanal]
                    if xanal == '': xanal = []
                    elif ',' in xanal:
                        xanal = [float(x0) for x0 in xanal.replace(' ','').split(',')]
                    else: xanal = [xanal]
                    plotparams = {}
                    if yerrorvalue.strip() != '':
                        plotparams['yerror'] = [yerrortype, yerrorvalue]
                    if plotloc !='': plotparams['plotloc'] = plotloc
                    if 'Mark' in plotcheck: plotparams['mark'] = True
                    if ylimit != '': plotparams['ylimit'] = [float(y) for y in ylimit.split(',')]
                    if xsort != '': plotparams['xsort'] = xsort
                    if legendvalue != '': plotparams['legend'] = [legendtype, [v.strip() for v in legendvalue.split(',')]]
                    if len(filterbylist)+len(filtervaluelist)+len(filterwaylist)>0:
                        addfig0 = "{}, {}, {}, ['{}', '{}', {}], [{}, '{}', {}], [{},{},'', {}], [], {}".format(addfiglist, multiitems, newparamlist, x, xunit, xanal, str(ylist)[1:-1], yunit, yanal, filterbylist, filtervaluelist, filterwaylist, plotparams)
                    else:
                        addfig0 = "{}, {}, {}, ['{}', '{}', {}], [{}, '{}', {}], [], [], {}".format(addfiglist, multiitems, newparamlist, x, xunit, xanal, str(ylist)[1:-1], yunit, yanal, plotparams)
                    try:
                        if os.path.exists(LMPSETTING_PATH):
                            # dfset = pd.read_csv(LMPSETTING_PATH, header=0)
                            dfset = autocode(LMPSETTING_PATH, 'pandas')
                            try: addfig1 = dfset[(dfset['item']=='targetfig')&(dfset['type']=='last')]['value'].values[0]
                            except: addfig1 = ''
                            addfig1 = addfig1+"    "+addfig0+'\n'
                            addfig1 = ('\n'.join(list(dict.fromkeys(addfig1.split('\n'))))+'\n').replace('\n\n','\n')
                            dfset = pd.concat([pd.DataFrame({'item':'targetfig','type':'last','value':addfig1}, index=[3]),dfset], axis=0).groupby(['item','type']).first().reset_index(drop=False)
                            dfset.to_csv(LMPSETTING_PATH, encoding='utf-8-sig', index=False)
                            print('Add fig: '+addfig0)
                    except:
                        print("# Warning: add fig failed, please check LMPSetting!")
                        pass
                else: print("# Error: please set target file, x and y values!")
                if (xunit=='')or(yunit==''): print("# Warning: please set xunit and(or) yunit before Run!")
            addfig_button = tk.Button(tab2, text="AddFig", command=lambda: addfigall(addfig.get().strip(), plotx.get().strip(), plotxunit.get().strip(), analysisx.get().strip(), ploty.get().strip(), plotyunit.get().strip(), analysisy.get().strip(), multidata.get().strip(), newparams.get().strip(), addfilterby.get().strip(), addfiltervalue.get().strip(), addfilterway.get().strip(), yerrortype.get(), yerrorvalue.get(), plotloc.get(), checkselect(plotcheck,[plotchecklist]), ylimitset.get().strip(), xsortset.get(), legendsettype.get(), legendsetvalue.get().strip()), width=9, bg='lightskyblue')
            addfig_button.grid(row = 3, column = 8)
            # figscale = ["{'width':14,   'high':5.2,   'dpi':600,   'labelsize':16,   'ticksize':14,   'fontscale':1.5}","{'width':14,   'high':5.2,   'dpi':600,   'labelsize':20,   'ticksize':18,   'fontscale':1.5}","{'width':7,   'high':5.2,   'dpi':600,   'labelsize':16,   'ticksize':14,   'fontscale':1.5}"]
            # figscale_label, figscale_combo = combo(tab2, figscale0, "FigScale:", 4, 0, listitem(readitem(dictpath,'figscale'),figscale), 69, 7, '')
            if simulate == "ReflectWall":
                global density0, vimpact0
                density0, vimpact0 = tk.StringVar(), tk.StringVar()
                density_label, density_combo = combo(tab2, density0, "ρ0".translate(sub)+"(g/cm3):".translate(sup), 2, 0, listitem(readitem(dictpath,'rou'),["","2.04"]), 9, 1, '')
                vimpact_label, vimpact_combo = combo(tab2, vimpact0, "  Vimp(km/s):", 2, 2, listitem(readitem(dictpath,'vimpact'),["","-2","-4"]), 9, 1, '')
                gridlist += [density_label, density_combo, vimpact_label, vimpact_combo]
            gridlist += [plotset2_button, addfig_button, snsstyle_label, snsstyle_combo, palette_combo, marker_label, marker_combo]
            filedict2 ={}
            try:
                folderset = folderfilter(inpath, folders)
                if '*' in folders: folderset = [i for i in folderset if 'dataall' not in i]
                if read == '':readpath = inpath +'/'+folderset[0] + '/'
                else: readpath = inpath +'/'+folderset[0] + '/' + read +'/'
                for k, v in filedict.items():
                    if glob.glob(readpath + v):
                        if 'custom' not in k:
                            filedict2[k.split('filename')[0]] = glob.glob(readpath + v)[0].replace('\\','/')
                        else:
                            for cfile in glob.glob(readpath + v):
                                filedict2['.'.join(cfile.replace('\\','/').split('/')[-1].split('.')[:-1])] = cfile.replace('\\','/')
                filespreloadlist = ['']+list(filedict2.keys()) if filedict2 else ['']
            except:
                filespreloadlist = ['']
                print("# Warning: input path does not exist, please check it!")
            addfig_combo = combo(tab2,addfig, "", 5, 1, listitem(readitem(dictpath,'addfig'),filespreloadlist), 22, 2, "")
            plotxlist = ["time","Temp","bo","Position","Press"]
            plotxunitlist = ["Time/ps", "Temperature/K", "Position/Å","Pressure/atm"]
            plotylist = ["","TotEng","Density","Volume","Cella","number","rmsd","speedz","Temp","Press"]
            plotyunitlist = ["","Energy/(kcal/mol)", "Density/($\mathregular{g/cm^3}$)", "Volume/($\mathregular{Å^3}$)","Cell Length/Å", "Bond Length/Å","CED/($\mathregular{10^{26}kJ/cm^3}$)","Bonds Counts","Species Counts","Reaction Counts","RMSD/Å","Speed/(km/s)","Temperature/K","Pressure/atm"]
            analysisxlist = ['','0, 100','fun.x+2']
            analysisylist = ['','first', 'sum', 'cumsum','max', 'min', 'mean', 'std', 'describe','0, 100','fun.x+2']
            addfilterbylist = ["","bonds","changebonds","molecule","weight","reaction"]
            addfiltervaluelist = ["","CC, NN, CN","C6H6N12O12, NO2","C3H6N6O6, NO2","C3H6N12O12 -> C6H6N11O10 + NO2","222, 438"]
            addfilterwaylist = ["",'between', 'include', 'belong', 'intersect', 'subset', 'superset', 'consistent','hue']
            plotx_label, plotx_combo, plotxunit_combo, analysisx_combo = combo3(tab2, "     X-axisSet:", 5, 3, plotx, listitem(readitem(dictpath,'plotx'),plotxlist), 22, 2, "", plotxunit, listitem(readitem(dictpath,'plotxunit'),plotxunitlist), 22, 2, '', analysisx, listitem(readitem(dictpath,'analysisx'),analysisxlist), 9, 1, '')
            ploty_label, ploty_combo, plotyunit_combo, analysisy_combo = combo3(tab2, "Y-axisSet:", 6, 0, ploty, listitem(readitem(dictpath,'ploty'),plotylist), 61, 5, "", plotyunit, listitem(readitem(dictpath,'plotyunit'),plotyunitlist), 22, 2, '', analysisy, listitem(readitem(dictpath,'analysisy'),analysisylist), 9, 1, '')
            multidatalist = ["","'merge', ['frame'], 'left'",'concat','doubley','smoothed']
            if os.path.exists((core0 + '/addparameters.py').replace('//','/')):
                newf = open((core0 + '/addparameters.py').replace('//','/'), "r", encoding='utf-8')
                newlines = newf.read().splitlines()
                newparamslist = ['']+eval('['+[i for i in newlines if 'Parameters' in i][0].split('[')[1])
            else:
                newparamslist = ['','Time','tempset','speedz','mweight','rmsd','CED','changebonds']
            multidata_label, multidata_combo, newparams_combo = combo2(tab2, "Multi&New:", 7, 0, multidata, listitem(readitem(dictpath,'multidata'),multidatalist), 22, 2, "", newparams, listitem(readitem(dictpath,'newparams'),newparamslist), 9, 1, '')
            addfilter_label, addfilterby_combo, addfiltervalue_combo, addfilterway_combo = combo3(tab2, "   ThirdFilter:", 7, 4, addfilterby, listitem(readitem(dictpath,'addfilterby'),addfilterbylist), 9, 1, "", addfiltervalue, listitem(readitem(dictpath,'addfiltervalue'),addfiltervaluelist), 22, 2, '', addfilterway, listitem(readitem(dictpath,'addfilterway'),addfilterwaylist), 9, 1, '')
            # @2025/12/20: add fig parameters.
            loclist = ['best','left','right','upper right','upper left','lower left','lower right','upper center','lower center','center left','center right','center']
            plotparams_label, plottype_combo, plotloc_combo = combo2(tab2, "   PlotParams:", 8, 4, plottype, listitem(readitem(dictpath,'plottype'),['line']), 9, 1, "readonly", plotloc, listitem(readitem(dictpath,'plotloc'),loclist), 9, 1, 'readonly')
            yerror_label, yerrortype_combo, yerrorvalue_combo = combo2(tab2, "YErrorSet:", 8, 0, yerrortype, listitem(readitem(dictpath,'yerrortype'),['columns','suffix']), 9, 1, "readonly", yerrorvalue, listitem(readitem(dictpath,'yerrorvalue'),['','Cella_std','_mean','_max','_min','_first','_last','_sum','_std']), 22, 2, '')
            # # plot选择box，返回值checkselect(plotcheck,[plotchecklist])
            plotchecklist = ["Mark", "PlotSave"]
            plotcheck, plotchecklabellist, plotcheckbuttonlist = check(tab2,[""],[8],[6],[plotchecklist])
            legendset_label, legendsettype_combo, legendsetvalue_combo = combo2(tab2, "LegendSet:", 9, 0, legendsettype, listitem(readitem(dictpath,'legendsettype'),['list','remove','suffix']), 9, 1, "readonly", legendsetvalue, listitem(readitem(dictpath,'legendsetvalue'),['','_mean']), 35, 3, '')
            xsortset_label, xsortset_combo, ylimitset_combo = combo2(tab2, "Xsort&Ylimit:", 9, 5, xsortset, listitem(readitem(dictpath,'xsortset'),['','discend','nosort']), 9, 1, 'readonly', ylimitset, listitem(readitem(dictpath,'ylimit'),['','0, 100']), 22, 2, '')
            def addrefresh(dict1, file1):
                if file1 != '':
                    addfile = dict1[file1]
                    # dfadd = pd.read_csv(addfile)
                    dfadd = autocode(addfile,'pandas')
                    addlist = dfadd.columns.tolist()
                    if "time" in addlist:
                        plotxlist = ["time"] + [x for x in addlist if x != "time"]
                    else:
                        plotxlist = addlist
                    plotylist,addfilterbylist = addlist, [""]+addlist
                    if file1 == 'reacspace':
                        plotylist += ['changebonds','changenum']
                        addfilterbylist += ['changebonds','changenum']
                    plotx_label, plotx_combo, plotxunit_combo, analysisx_combo = combo3(tab2, "     X-axisSet:", 5, 3, plotx, listitem(readitem(dictpath,'plotx'),plotxlist), 22, 2, "", plotxunit, listitem(readitem(dictpath,'plotxunit'),plotxunitlist), 22, 2, '', analysisx, listitem(readitem(dictpath,'analysisx'),analysisxlist), 9, 1, '')
                    ploty_label, ploty_combo, plotyunit_combo, analysisy_combo = combo3(tab2, "Y-axisSet:", 6, 0, ploty, listitem(readitem(dictpath,'ploty'),plotylist), 61, 5, "", plotyunit, listitem(readitem(dictpath,'plotyunit'),plotyunitlist), 22, 2, '', analysisy, listitem(readitem(dictpath,'analysisy'),analysisylist), 9, 1, '')
                    addfilter_label, addfilterby_combo, addfiltervalue_combo, addfilterway_combo = combo3(tab2, "   ThirdFilter:", 7, 4, addfilterby, listitem(readitem(dictpath,'addfilterby'),addfilterbylist), 9, 1, "", addfiltervalue, listitem(readitem(dictpath,'addfiltervalue'),addfiltervaluelist), 22, 2, '', addfilterway, listitem(readitem(dictpath,'addfilterway'),addfilterwaylist), 9, 1, '')
                    yerror_label, yerrortype_combo, yerrorvalue_combo = combo2(tab2, "YErrorSet:", 8, 0, yerrortype, listitem(readitem(dictpath,'yerrortype'),['columns','suffix']), 9, 1, "readonly", yerrorvalue, listitem(readitem(dictpath,'yerrorvalue'),['','_std']+plotylist), 22, 2, '')
                    legendset_label, legendsettype_combo, legendsetvalue_combo = combo2(tab2, "LegendSet:", 9, 0, legendsettype, listitem(readitem(dictpath,'legendsettype'),['list','remove','suffix']), 9, 1, "readonly", legendsetvalue, listitem(readitem(dictpath,'legendsetvalue'),['','_mean','_max','_min','_first','_last','_sum','_std']+plotylist), 35, 3, '')
                else: print("# Warning: please select a file to load!")
            addrefresh_button = tk.Button(tab2, text="Refresh",command=lambda: addrefresh(filedict2,addfig.get().strip()), width=9, bg='lightskyblue')
            addrefresh_button.grid(row = 5, column = 0)
            gridlist += [addfig_combo, plotx_combo, plotxunit_combo, ploty_combo, plotyunit_combo, analysisy_combo, addfilter_label, addfilterby_combo, addfiltervalue_combo, addfilterway_combo, addrefresh_button, multidata_label, multidata_combo, newparams_combo]
            gridlist += [plotparams_label, plottype_combo, plotloc_combo, yerror_label, yerrortype_combo, yerrorvalue_combo, xsortset_label, ylimitset_combo, xsortset_label, xsortset_combo, legendset_label, legendsettype_combo, legendsetvalue_combo]+plotchecklabellist+plotcheckbuttonlist
        elif (drawing == "Animation") & (simulate != "ReflectWall"):
            clean(gridlist)
            global anitype0, aniunit0, anivalue0, interval0, drawstyle0, barscale0, scatterscale0
            # anitype0，返回值anitype0.get()
            anitype0, aniunit0, anivalue0, interval0, drawstyle0, barscale0, scatterscale0 = tk.StringVar(), tk.StringVar(), tk.StringVar(), tk.StringVar(), tk.StringVar(), tk.StringVar(), tk.StringVar()
            anitype_label, anitype_combo = combo(tab2,anitype0, "       AniType:",5,6,listitem(readitem(dictpath,'anitype'),["isograph","line","bar"]),9,1,'readonly')
            # timestep，返回值timestep.get()
            timestep_label, timestep_combo = combo(tab2, timestep, "Timestep(fs):", 3, 0, listitem(readitem(dictpath,'timestep'),["0.1","0.01","0.2","0.25",""]), 9, 1, '')
            rangeinter_label, aniunit_combo, anivalue_combo, interval_combo = combo3(tab2, "Range/Inter:", 3, 3, aniunit0, listitem(readitem(dictpath,'aniunit'),["","frame","time(ps)"]), 9, 1, "readonly", anivalue0, listitem(readitem(dictpath,'anivalue'),["","400, 60000"]), 9, 1,"", interval0, listitem(readitem(dictpath,'interval'),["50",""]),9,1,'')
            # figscale_label, figscale_combo = combo(tab2, figscale0, "FigScale:", 4, 0, listitem(readitem(dictpath,'figscale3'),["{'width':12,   'high':7,   'dpi':200,   'labelsize':20,   'ticksize':18}"]), 74, 7, '')
            drawstyle_label, drawstyle_combo = combo(tab2, drawstyle0, "DrawStyle:", 5, 0, listitem(readitem(dictpath,'drawstyle'),["rainbow","jet","turbo","viridis","plasma","YlOrBr","gnuplot","gnuplot2","brg","gist_rainbow",""]), 9, 1, '')
            barscale_label, barscale_combo = combo(tab2, barscale0, "     BarScale:", 5, 2, listitem(readitem(dictpath,'barscale'),["5","8","10",""]), 9, 1, '')
            scatterscale_label, scatterscale_combo = combo(tab2, scatterscale0, "     ScatterScale:", 5, 4, listitem(readitem(dictpath,'scatterscale'),["200","8","10",""]), 9, 1, '')
            gridlist += [timestep_label, timestep_combo, anitype_label, anitype_combo, rangeinter_label, aniunit_combo, anivalue_combo, interval_combo, drawstyle_label, drawstyle_combo,barscale_label, barscale_combo, scatterscale_label, scatterscale_combo]
        else:
            clean(gridlist)
            print("# Error: this 'Drawing' and 'Simulate' mode is not supported!")
    simulate_button = tk.Button(tab2, text="Confirm",command=lambda: drawmethod(inpath.get().strip(), folders.get().strip(), read2.get().strip(), filedict, SCRIPTS_DIR, gridlist, drawing.get(), simulate.get()), width=9, bg='lightskyblue')
    # simulate_button = tk.Button(tab2, text="Confirm", command=lambda in_path=inpath.get().strip(), folders_path=folders.get().strip(), read2_path=read2.get().strip(): drawmethod(in_path, folders_path, read2_path, filedict, SCRIPTS_DIR, gridlist, drawing.get(), simulate.get()), width=9, bg='lightskyblue')
    simulate_button.grid(row = 1, column = 8)
    # tab2 第2行设置
    # targetfig子窗口，返回列表值targetfig_value
    def targetfig_window():
        child_window = tk.Tk()
        child_window.title("TargetFig")
        child_window.geometry("1500x620")
        figexample = """MultiFig Examples:
    ['log'], [], [], ['time', 'Time/ps', []], ['TotEng', 'PotEng','Energy/(kcal/mol)', []], [], [], []
    ['log'], [], [], ['time', 'Time/ps', []], ['Density', 'Density/($\\mathregular{g/cm^3}$)', ['describe']], [], [], []
    ['log'], [], [], ['time', 'Time/ps', []], ['Volume', 'Volume/($\\mathregular{Å^3}$)', ['describe']], [], [], []
    ['log'], [], [], ['time', 'Time/ps', []], ['Cella', 'Cellb', 'Cellc', 'Cell Length/Å', ['describe']], [], [],[]
    ['log'], [], ['CED'], ['time', 'Time/ps', []], ['CED', 'CED/($\\mathregular{10^{26}kJ/cm^3}$)', []], [], [], []
    ['log', 'species'], ['merge', ['frame','time'], 'right'], [], ['time', 'Time/ps', []], ['number', 'Species Counts', []], [['molecule'], ['C3H6O6N6', 'NO2'], '', ['belong', 'hue']], [], []
    ['log'], ['concat'], [], ['time', 'Time/ps', []], ['Density', 'Density/$(\mathregular{g/cm^3}$)', []], [[],[],'fs',[]], [], []    
    ['bonds'],[],['num'],['time', 'Time/ps',[]],['num','Number of bonds',[]],[['bonds','time'],['CN','CH','NN'],'',['belong','hue']],[],[]
    ['bonds'],[],[],['time', 'Time/ps',[]],['bo','Min Bondorder',['min']],[['bonds'],['CN','CH','NN'],'',['belong','hue']],[],[]
    ['dump'], [], ['id2'],['time', 'Time/ps',[]],['x','Position/Å',[]],[['id2'],['1','2','3'],'',['belong','hue']],[],[]
    ['dump'], ['concat'], ['rmsd'],['time', 'Time/ps',[]],['rmsd','RMSD/Å',['first']],[['rmsd'],[],'',[]],[],[]
    ['dumpbonds.bl'],[],[],['time', 'Time/ps',[]],['bl','Max Bondlength/Å',['max']],[['bonds'],['CN','NN'],'',['belong','hue']],[],[]
    ['species'], [], [],['time', 'Time/ps',[]],['number', 'Species Counts',[]],[['molecule','time'],['O2'],'',['belong','hue']],[],[]
    ['pos'], [], ['num'],['time', 'Time/ps',[]],['num', 'Species Counts',['sum']],[['molecule','time'],['C3H6N6O6','NO2'],'',['belong','hue']],[],[]
    ['reacspecies'], [], ['num'],['time', 'Time/ps',[]],['num', 'Species Counts',['sum']],[['molecule','time'],['NO2','C3H6N6O6'],'',['belong','hue']],[],[]
    ['reacspecies'], [], ['num'], ['time', 'Time/ps', []], ['num', 'Species Counts', ['sum']], [['weight', 'time'], [0, 250], '', ['between', 'hue']], [], []
    ['reacspecies'], [], [], ['time', 'Time/ps', []], ['weight', 'Max Weight', ['max']], [], [], []
    ['reacspace'], [], ['num'], ['time', 'Time/ps', []], ['num', 'Reaction Counts', ['sum']], [['reaction', 'time'], ['4C6H6N12O12 -> C24H24N48O48','2C6H6N12O12 -> C12H12N24O24'], '', ['belong', 'hue']], [], ['mark']
    ['reacspace'], [], ['num'], ['time', 'Time/ps', []], ['num', 'Reaction Counts', ['sum']], [['products', 'time'], ['O2N', 'N2', 'H2O', 'O2'], '', ['intersect', 'hue']], [], []
    ['reacspace'], [], ['num'], ['time', 'Time/ps', []], ['num', 'Reaction Counts', ['sum']], [['products', 'time', 'reaction'], ['O2N'], '', ['intersect']], [], []
    ['reacspace'], [], [], ['time', 'Time/ps', []], ['products', 'Reaction Counts', []], [['products', 'time'], ['O2N'], '', ['intersect']], [], []
    ['reacspace'], [], ['changebonds'], ['time', 'Time/ps', []], ['changenum', 'Change Number', []], [['changebonds'],['NN','CN','NO'],'',['belong','hue']], [], []
    ['reacspace'], [], ['changebonds'], ['time', 'Time/ps', []], ['changenum', 'Change Number', ['cumsum']], [['changebonds'],['NN','CN','NO'],'',['belong','hue']], [], []
    ['reacspace'], [], ['changebonds'], ['time', 'Time/ps', []], ['changenum', 'Change Number', []], [['changebonds'],['NN'],'',['belong','hue']], [], []
    ['reacspace'], [], ['changebonds'], ['time', 'Time/ps', []], ['changenum', 'Change Number', []], [['changebonds'],['NN'],'',['belong','hue']], ['polyfit.4.line'], []
    ['reacspace'], [], ['changebonds'], ['time', 'Time/ps', []], ['changenum', 'Change Number', []], [['changebonds'],['NN'],'',['belong','hue']], ['lowess.line.0.9.0'], []
    ['reacspace'], [], ['changebonds'], ['time', 'Time/ps', []], ['changenum', 'Change Number', []], [['changebonds'],['NN'],'',['belong']], [], ['smooth.order.4.scatter']
    ['reacspace'], [], ['changebonds'], ['time', 'Time/ps', []], ['changenum', 'Change Number', []], [['changebonds'],['NN'],'',['belong']], [], ['smooth.convolve.20.line']
    ['ovitolength'],[],[],['time', 'Time/ps',[]],['C-N','C-H','N-N','Number of bonds', []],[['time'],[],'',['sum']],[],[]
    ['ovitovelocityz'],[],['speedz'],['Position', 'Position/Å',[0, 175]],['speedz','Speed/(km/s)', []],[['time'],[0.4,0.8,1.2,1.6,2.0],'ps',['belong','hue']],[],[]
    ['ovitovelocityz'],[],['speedz'],['time', 'Time/ps',[0,2.0]],['Position','Position/Å', [0, 175]],[['speedz'],[vimpact*0.55, vimpact*0.45],'',['between']],['polyfit',1,'wavefront'],['mark']
    ['varxmd'], [], [],['time', 'Time/ps',[]],['num', 'Reaction Counts',[]],[['reaction','time'],['C6H6O12N12 -> C6H6O10N11 + O2N','C6H6O10N11 + O2N -> C6H6O12N12'],'',['belong','sum','hue']],[],['mark']
    ['varxmd'], [], [], ['time', 'Time/ps', []], ['num', 'Reacts Counts', []], [['reacts', 'time'], ['C6H6N12O12', 'C12H12N24O24'], '', ['belong', 'sum', 'hue']], [], ['mark']
    ['varxmd'], [], [], ['time', 'Time/ps', []], ['num', 'Products Counts', []], [['products', 'time'], ['C6H6N12O12', 'C12H12N24O24'], '', ['belong', 'sum', 'hue']], [], ['mark']
    ['chemspec'], [], [],['time', 'Time/ps',[]],['num','Species number',[]],[['molecule','time'],['C6H6N12O12','H2O','CO2','NO2'],'',['belong','sum','hue']],[],[]
    ['chemreac'], [], [],['time', 'Time/ps',[]],['num','Reaction number',[]],[['reaction','time'],['C6H6O12N12 -> C6H6O10N11 + O2N','C6H6O10N11 + O2N -> C6H6O12N12'],'',['belong','sum','hue']],[],['mark']
    ['nebhop1end'], [], [],['normalize', 'Reaction coordinate',[]],['dE','dE',[]],[],[],['mark','smooth.order.3']
    ['stress'], ['concat'], [], ['strain', 'Strain', [0, 0.22]], ['stress', 'Stress/GPa', []], [], [], []
    ['chunk'], [], [], ['time', 'Time/ps', []], ['temp', 'Temperature/K', ['mean']], [], [], []
    ['msxcd'], [], [], ['temp', 'Temperature/K', []], ['Potential energy', 'Kinetic energy', 'Non-bond energy', 'Total energy','Energy/(kcal/mol)', []], [['time'],[0,400],'',['between']], [], []
    ['custom.dataofmsxrd.csv'], [], [], ['2theta', '2$\mathregular{\it{θ}}$', []], [ 'aDATNBI862', 'bDATNBI344', 'rDATNBI432', 'Intensity', []], [], [], []
    ['custom.abc.csv'], [], [], ['x', 'xunit', []], ['y', 'yunit', ["fun.x=='def'"]], [['z'], [], '', ['size', 'sep']], [], []
AnimationFig Examples:
    ['chunk', 'cell'], ['merge', ['frame'], 'left'], [], ['Coord2', 'Z/Å', ['fun.x.Coord2*x.c+x.c0']], ['Coord1', 'X/Å', ['fun.x.Coord1*x.a+x.a0']], [['Coord2', 'temp'], [0, 400], '', ['between']], [], [['temp', 'Temperature/K', 'np.linspace(200, 6000, 11)'], "'Frame: {}    $\\mathit{{T}}_{{\\mathit{{max}}}}$: {}K  $\\mathit{{T}}_{{\\mathit{{mean}}}}$: {}K'.format(frame, int(df['temp'].max()), int(df['temp'].mean()))", ['html', 'gif']]
    ['chunk','cell'], ['merge',['frame'],'left'], [],['Coord1', 'Z/Å',['fun.x.Coord1*x.c+x.c0']],['temp','Temperature/K',[]],[],[],[[],"'Frame: {}    $\\mathit{{T}}_{{\\mathit{{max}}}}$: {}K'.format(frame, int(df1['temp'].max()))",['html','gif']]
    ['reacspecies'], [], [], ['weight', 'Molecular Weight', []], ['frame', 'Number', []], [['weight', 'frame'], [], '', ['size', 'sep']], [], [], [[], "'Time: {} ps'.format(round(frame*0.25*0.001,4))", ['html', 'gif']]
    ['bonds'], [], [], ['bo', 'Bond Order', []], ['bonds', 'Bonds Number', []], [['bonds', 'frame'], ['CC'], '', ['belong', 'size', 'sep']], [], [], [[], "'CC Bonds: {} ps'.format(round(frame*0.01*0.001,4))", ['html', 'gif']]"""
        figlabel = tk.Text(child_window, width=1640,height=20,relief='flat',font=('Times New Roman',13))
        figlabel.insert(1.0, figexample)
        figlabel.configure(state='disabled')    # 使Text可复制。
        figlabel.pack()
        entry = tk.Text(child_window, width=1640, height=10, font=('Times New Roman',13))
        dictpath = readlast(LMPSETTING_PATH)
        if readitem(dictpath,'targetfig') == '': return_value = '# Please add fig to mapping!\n'
        else: return_value = readitem(dictpath,'targetfig')
        entry.insert(INSERT,return_value)   #在光标处插入
        def load_entry():
            readpath = (inpath.get().strip()+'/'+folders.get().strip()+'/'+export2.get().strip()+'/').replace('\\','/').replace('//','/')
            readpaths = [path.replace('\\', '/') for path in glob.glob(readpath)]
            if os.path.exists(readpaths[0]+'/targetfigset.txt'):
                with open(readpaths[0]+'/targetfigset.txt', 'r', encoding=encode.get()) as f:
                    entry.delete(1.0, tk.END)
                    entry.insert(1.0, '# Please add fig to mapping!\n'+f.read())
            else: print("# Warning: targetfigset.txt could not be found in target folder!")
        entry.pack()
        def clear_entry():
            entry.delete(1.0, tk.END)
            entry.insert(1.0, '# Please add fig to mapping!\n')
        # 创建按钮容器框架
        button_frame = tk.Frame(child_window)
        button_frame.pack(expand=True)
        load_button = tk.Button(button_frame, text="Load", command=load_entry, width=9, bg='honeydew')
        clear_button = tk.Button(button_frame, text="Clear", command=clear_entry, width=9, bg='bisque')
        submit_button = tk.Button(button_frame, text="Submit", command=lambda: submit(child_window, entry, return_value, LMPSETTING_PATH, 'targetfig'), bg='lightskyblue')
        # 调整按钮顺序，Clear在Submit左侧
        load_button.pack(side=tk.LEFT, padx=5)
        clear_button.pack(side=tk.LEFT, padx=5)
        submit_button.pack(side=tk.LEFT, padx=5)
        button_frame.pack(anchor=tk.CENTER)  # 在主窗口中居中
        child_window.wait_window()
    targetfig_button = tk.Button(tab2, text="TargetFig", command=targetfig_window, width=9, bg='lightskyblue')
    targetfig_button.grid(row = 10, column = 5)
    # 创建 Clear 按钮，与 TargetFig 并排
    def clear_targetfig_entry():
        # 读取现有数据
        if os.path.exists(LMPSETTING_PATH):
            # dfset = pd.read_csv(LMPSETTING_PATH, header=0)
            dfset = autocode(LMPSETTING_PATH, 'pandas')
        else:
            # 如果文件不存在，创建空的DataFrame
            dfset = pd.DataFrame(columns=['item', 'type', 'value'])
        # 检查是否已存在该设置项
        existing_mask = (dfset['item'] == 'targetfig') & (dfset['type'] == 'last')
        if existing_mask.any():
            # 更新现有记录
            dfset.loc[existing_mask, 'value'] = '# Please add fig to mapping!\n'
        else:
            # 添加新记录
            new_row = pd.DataFrame({'item': ['targetfig'], 'type': ['last'], 'value': ['# Please add fig to mapping!\n']})
            dfset = pd.concat([dfset, new_row], ignore_index=True)
        # 保存到CSV文件
        dfset.to_csv(LMPSETTING_PATH, index=False)
    clear_targetfig_button = tk.Button(tab2, text="Clear", command=clear_targetfig_entry, width=9, bg='bisque')
    clear_targetfig_button.grid(row=10, column=4)
    # figtips子窗口，无返回值。
    figtipscontent = """
    # Parameter format [data1, data2], ['merge', 'concat', ['frame'], mode], [newParameters], [x, xunit, [range]], [y1, y2, ..., yn, yunit, [range or static]], [[parament1, parament2, ...], [range], 'unit', [mods]], [function, args], [figParameters]
    #0 [data1, data2] or [data]: Data source.
        # Built-in files include ['log', 'bonds', 'dump', 'dumpbonds.bo', 'dumpbonds.bl', 'species', 'pos', 'ovitoxxx', 'varxmd', 'chemspec', 'chemreac', 'nebxxx', 'reacspecies', 'reacspace', 'stress', 'chunk']
        # Custom files: ['custom.xxx'], where xxx is the filename (including extension).
    #1 ['merge', 'concat', ['frame'], 'outer']: Data combination method:
        # 'merge': Data merging; ['frame']: Merge based on one or several columns; mode: Merging method: 'left', 'right', 'inner', 'outer';
        # 'concat': Concatenate data across folders and plot separately, do not use hue for this group.
    #2 [newParameters]: Predefined new parameters, see def newParameters in addparameters.py, can be customized or modified.
        # Universal: 'tempset' = 'time' * 10 + 298 (set step temperature)
        # newlog: 'CED', 'Time' = 'Time' * 0.001
        # newbonds:
        # newdump: 'rmsd', 'id2' = str('id'), 'weight', 'mweight'
        # newovito: 'speedz' = 'Volecity.Z' * 100
        # newreacspace: 'changebonds' and 'changenum', to fix changed bonds' type and num.
    #3 [x, xunit, [range]]; [y1, y2, ..., yn, yunit, [range]]: Set x, y, variable units, and data range
        # xunit, yunit: Units for x and y, used as plotting coordinate units;
        # [range]: Range represents the data range;
        # ['fun.xxxx']: Apply pandas function (lambda x: xxxx) to x or y, can perform operations such as value extraction, basic mathematical operations, etc. e.g., ["fun.x == 10"]
        # [static]: Only used for y value method, including: 'first', 'sum', 'max', 'min', 'mean', 'std', 'size' (number of data rows), describe (statistical analysis), invalid when third-party filtering is included.
    #4 [[parament1, parament2, ...], [range], 'unit', [mods]]: Data correction parameters:
        # Parameters: Split data based on Parameters (data column names) and/or select range, hue takes Parameters1; Parameters2, etc., are used for mods statistics
        # [range]: Select the range of parament data values;
        # 'unit': The data unit corresponding to the range, used for plotting the legend;
        # [modes]: Can contain multiple modes, including:
            # Filtering: 'between', 'include', 'belong', 'intersect', 'subset', 'superset', 'consistent';
                # 'hue' splits data.
    #5 [fitmethod, args1, args2]: Use function fitting and plot, export fitted data:
        # outliers remove: remove data that differ from other data seriously.
            # 'outliers.method.fastmode.thershold.ncore.visualize': remove outliers by zscore, mad and(or) iqr method.
                # mothod: filter mode to use, including: auto, zscore, mad, iqr
                # fastmode: if use fast mode, including: auto, yes, no
                # thershold: thershold for  zscore, mad and(or) iqr method, default 3.
                # ncore: number of core to use, default 4.
                # visulalize: if show filter result figs, defalut yes.
        # fitmethod: Use function method (choose one):
            # 'polyfit.n.printitem': np.polyfit polynomial fitting method, n represents the fitting order
                # printitem: custom output content, such as:
                    # 'Reflectfront': show wavefront function.
                    # 'line' or 'scatter': show original curve as line or scatter.
            # 'lowess.f.i', : Lowess non-polynomial fitting method, f (fitting accuracy 0~1) default 1./3, i (re-weighting based on residuals) default 0.
            # 'lowess.line.f.i': line stands for origin curve shown as line.
            # 'lowess.scatter.f.i', : scatter stands for origin curve shown as scatter.
        # reverse: data would be sorted by x discendingly.
    #6 [figParameters]: Independent plotting parameters:
        # For MultiFig:
            # 'mark': Use scatter plot (default line plot);
    """
    closewindow(tab2, "FigTips", "1340x660", 1300, 33, 10, 1, figtipscontent)
    # @2025/3/13：change to open addparameters.py
    Parameters_button = tk.Button(tab2, text="Parameters", command=lambda: open_file(SCRIPTS_DIR+'/addparameters.py'), width=9, bg='lightgray')
    Parameters_button.grid(row=10, column=3)
    # SmoothGUI button
    smoothgui_button = tk.Button(tab2, text="SmoothGUI", command=lambda: run_script(SCRIPTS_DIR, 'lmpanalysis','smoothGUI.py'), width=9, bg='deepskyblue')
    smoothgui_button.grid(row=10, column=2)
    # Help2子窗口。
    helpcontent2 = """    Inpath: open target folders path.
    Folders: target folder(s) to analyze, * is acceptable!
    Export: folder to export analysis result, default analysis.
    Read: folder created by arrange operation, default data.
    Simulate: add necessary Parameters for some special simulate mode, currently available include: 
        Dynamic: Parameters includes timestep and thermostep.
            Impact: Parameters includes ρ0(g/cm3), Vimpact(km/s).
    Drawing: Plot mode to select.
        MultiFig: default mode to draw multi figs, setting in Targetfig.
        Animation: draw move fig at format of html or gif.
    AnimateType: plot type for move fig to select.
        Range/Inter(ms): setting of frame range, and interval time of move fig.
    SnsStyle, Palette: draw style for Seaborn.
    Marker: marker style for plot if needed.
    FigScale: set figure size and font size.
    SubAdjust: set subplot adjust for multi fig.
    Refresh: load file content for selected file.
    AddFig: add fig to targetfig.
    TargetFig: set plot(s) to analysis and draw, most important content!
    PlotSave: save plot of 'MultiFig' or 'Single' mode if it is selected.
    FigTips: some explain for targetfig content.
    FileRules: set the rule of filenames to read.
    ShowRules: show currently set file rules (in dos window).
    """  # SviewGUI: show target csv or excel (sheet1) file, and try to draw it.
    closewindow(tab2, "Help", "740x450", 740, 22, 10, 6, helpcontent2)

    # mapping（）函数，用于run
    def runmapping(event):
        # 重新读取设置文件，以备调用。
        dictpath = readlast(LMPSETTING_PATH)
        filerule2 = readitem(dictpath,'filerule2')
        targetfig_value = readitem(dictpath,'targetfig')
        plotset2 = readitem(dictpath,'plotset2')
        # 文件名读取，生成变量如logfilename等。
        filelist = [i for i in filerule2.split('\n') if i.strip() !='']
        dictfile = {}
        for i in filelist:
            k, v = [j.strip().split('filename')[0] for j in i.split(':')]
            dictfile[k] = v
        rule = eval(elementorder.get())
        # 读取plotset绘图设置。
        drawingcheck = drawing.get()
        fontlist = [i.strip() for i in fonts.get().strip().split(',')]
        # 读取plotset2绘图设置。
        plotsetlist2 = [item.strip() for item in plotset2.split('\n')]
        multiscale = eval([item.split('multiscale:')[1] for item in plotsetlist2 if 'multiscale:' in item][0])
        subplotadjust = eval([item.split('subadjust:')[1] for item in plotsetlist2 if 'subadjust:' in item][0])
        singlescale = eval([item.split('singlescale:')[1] for item in plotsetlist2 if 'singlescale:' in item][0])
        doubleyscale = eval([item.split('doubleyscale:')[1] for item in plotsetlist2 if 'doubleyscale:' in item][0])
        figallscale = eval([item.split('figallscale:')[1] for item in plotsetlist2 if 'figallscale:' in item][0])
        aniscale = eval([item.split('aniscale:')[1] for item in plotsetlist2 if 'aniscale:' in item][0])
        # 分别读取MultiFig和Animation绘图设置。
        if drawingcheck == 'MultiFig':
            markerlist = [m.strip() for m in marker0.get().split(',')]
            styleset = snsstyle0.get().strip()
            # paletteset = palette0.get().strip()
            # 读取特殊模拟设置。
            if simulate.get() == 'Impact':
                global density, vimpact
                density = eval(density0.get())
                vimpact = eval(vimpact0.get())
        elif drawingcheck == 'Animation':
            timestep0 = float(timestep.get())
            markerlist = []                     # @2024/2/6：避免animation模拟报错。
            anitype = anitype0.get()
            aniunit = aniunit0.get()
            if anivalue0.get().strip() != '':
                # anivalue = eval(anivalue0.get())
                anivalue = anivalue0.get().strip().split(',')
            else: anivalue = ''
            intervalset = int(interval0.get())
            styleset = drawstyle0.get().strip()
            barscale = float(barscale0.get().strip())
            scatterscale = float(scatterscale0.get().strip())
        # 读取targetfig和plotsave设置
        targetfig = [list(eval(i.strip())) for i in targetfig_value.split('\n') if ('#' not in i) & (i.strip() != '')]
        plotsave = checkselect(plotcheck,[plotchecklist])
        # 把当前设置写入dfset中，以备调用。
        if os.path.exists(LMPSETTING_PATH):
            # dfset = pd.read_csv(LMPSETTING_PATH, header=0)
            dfset = autocode(LMPSETTING_PATH, 'pandas')
            tkset = [inpath, folders, read2, export2, simulate, drawing]
            tkname = ['inpath','folders','read2','export2','simulate','drawing']
            if drawing.get() == "MultiFig":
                tkset += [addfig, plotx, plotxunit, ploty, plotyunit, analysisy]
                tkname += ['addfig','plotx','plotxunit','ploty','plotyunit','analysisy']
                tkset += [snsstyle0, palette0, marker0]
                tkname += ['snsstyle', 'palette', 'marker']
            elif (drawing.get() == "Animation") & (simulate.get() != "ReflectWall"):
                tkset += [timestep, anitype0, aniunit0, anivalue0, interval0, drawstyle0, barscale0, scatterscale0]
                tkname += ['timestep', 'anitype', 'aniunit', 'anivalue', 'interval', 'drawstyle', 'barscale', 'scatterscale']
            for n,i in enumerate(tkset):
                dfset = pd.concat([pd.DataFrame({'item':str(tkname[n]),'type':'last','value':i.get().strip()}, index=[3]),dfset], axis=0).groupby(['item','type']).first().reset_index(drop=False)
            dfset.to_csv(LMPSETTING_PATH, encoding='utf-8-sig', index=False)
        # 数据文件夹读取，用folderfilter函数过滤。
        if inpath.get().strip() != '':
            folderset = folderfilter(inpath.get().strip(), folders.get().strip())
            # @2024/6/8：去掉'dataallxx'文件夹
            if '*' in folders.get().strip():
                folderset = [i for i in folderset if 'all' not in i]
            # 建立空字典dfalldict，用于收纳dfall，对应'concat'
            dfalldict ={}
            for i in range(len(targetfig)):
                if 'concat' in targetfig[i][1]:
                    dfalldict[str(i)] = pd.DataFrame()
            # 读取数据文件夹，确定读取路径readpath。
            readfolder = read2.get().strip()
            targetfolder = export2.get().strip()
            # 依次读取目标文件夹。
            if folderset != []:
                for folder in folderset:
                    if readfolder == '':
                        readpath = inpath.get().strip() +'/'+folder + '/'
                    else:
                        readpath = inpath.get().strip() +'/'+folder + '/' + readfolder +'/'
                    if targetfolder == '':
                        outpath = inpath.get() +'/'+folder + '/'
                    else:
                        outpath = inpath.get().strip() +'/'+folder + '/' + targetfolder + '/'
                        if not os.path.exists(outpath):
                            os.mkdir(outpath)
                            print('# {} folder has been bulided!'.format(targetfolder))
                        else:
                            print("# {} folder already exist, and it's content will be emptyed (except data)!".format(targetfolder))
                            for filename in os.listdir(outpath):
                                # @2024/2/27：保留data文件夹中文件不删除。
                                if filename != "data":
                                    # 保留上次mapping设置。
                                    if ('lastmappingset' not in filename) & ('targetfigset' not in filename):
                                        file_path = os.path.join(outpath, filename)
                                        try:
                                            if os.path.isfile(file_path) or os.path.islink(file_path):
                                                os.unlink(file_path)
                                            elif os.path.isdir(file_path):
                                                shutil.rmtree(file_path)
                                        except Exception as e:
                                            print(f"cannot delete file {file_path}: {e}")
                    # 处理分析数据子文件夹情况。
                    try:
                        # dfatoms = pd.read_csv(inpath.get()+'/'+folder+'/data/dataofatom.csv')
                        dfatoms = autocode(inpath.get()+'/'+folder+'/data/dataofatom.csv', 'pandas')
                    except:
                        dfatoms = pd.DataFrame()
                        print('# Attention: dataofatom could not be found, please check it!')
                    # 定义交叉绘图规则
                    if len(targetfig) > 0:
                        # 保存targetfig为文本。
                        with open(outpath + 'targetfigset.txt', 'w', encoding='utf-8') as f:
                            for i in targetfig: f.write('{}'.format(i).translate(resub).translate(resup)[1:-1]+'\n')    # 去掉可能生成的上下标。
                        # fig方法筛选，用于调用绘图设置。
                        # 预设doubley计数器，统计doubley数量。
                        doubleynum, doubleycheck = 0, sum(1 for sublist in targetfig for j in sublist[1] if j == 'doubley')/2
                        fignum = len(targetfig) - doubleycheck
                        if (drawingcheck == 'MultiFig') and (fignum > 1):
                            figscale = multiscale
                            fig, axes = plt.subplots(math.ceil(fignum/2), 2, figsize=(figscale['width'], math.ceil(fignum/2)*figscale['high']), dpi=figscale['dpi'])    # 设置多图行列和尺寸
                            plt.subplots_adjust(left=subplotadjust['left'], bottom=subplotadjust['bottom'], right=subplotadjust['right'], top=subplotadjust['top'], wspace=subplotadjust['wspace'], hspace=subplotadjust['hspace'])
                        # @2024/12/14：增加单图片匹配。
                        elif (drawingcheck == 'MultiFig') and (fignum == 1):
                            figscale = singlescale
                            fig, axes = plt.subplots(1, 1, figsize=(figscale['width'],figscale['high']), dpi=figscale['dpi'])    # 设置多图行列和尺寸
                            axes = [axes]
                        elif drawingcheck == 'Animation':
                            figscale = aniscale
                            fig = plt.figure(figsize=(figscale['width'], figscale['high']), dpi=figscale['dpi'])
                        # @2024/3/19：增加全局字体设置，可设置中英文混排，顺序中英。
                        if len(fontlist) == 1: labelfont = fontlist[0]
                        else: labelfont = fontlist[1]
                        config = {
                            "font.family": "serif",
                            "font.serif": [fontlist[0]],
                            "font.size": figscale['ticksize'],    # x,y,colorbar字号
                            "axes.unicode_minus": False,     # 解决Matplotlib负号显示为方框问题。
                            "mathtext.fontset": "stix",    # 设置LaTeX字体 
                            }
                        # rcParams.update(config)
                        # 数据整理
                        # @2025/5/21：预设输出数据。
                        dfdict, filterreport, fitreport, targetfigall = {}, '', '', []
                        for i in range(len(targetfig)):
                            # 导入一组或两组数据：
                            # @2025/4/23：改进customfile识别。
                            customfiledict = {'.'.join(file.replace('\\','/').split('/')[-1].split('.')[:-1]):file.replace('\\','/').split('/')[-1] for file in glob.glob(readpath + dictfile['custom'])}
                            dictfile.update(customfiledict)
                            if len(targetfig[i][0])>0:                            # 匹配数据类型
                                dfdict = preprocessing(list(set(targetfig[i][0])), dictfile, readpath, dfdict, rule)
                                if not all(len(dfdict[key]) > 0 for key in dfdict):
                                    print("# Error: imported file {} is empty, please check its!".format(' and '.join(targetfig[i][0])))
                                    continue
                                else:
                                    # 以下进行数据融合merge或拼接concat
                                    # @2025/4/23：基于改进filerules去掉custom。
                                    if len(targetfig[i][0]) == 1:
                                        df = dfdict[targetfig[i][0][0]]
                                    elif len(targetfig[i][0]) == 2:
                                        if targetfig[i][0][0] == targetfig[i][0][1]:
                                            df = dfdict[targetfig[i][0][0]]
                                        elif (targetfig[i][0][0] != targetfig[i][0][1]) & ('merge' in targetfig[i][1]):
                                            listmerge = []
                                            for j in targetfig[i][0]:listmerge.append(j)
                                            df = pd.merge(dfdict[listmerge[0]],dfdict[listmerge[1]], how=targetfig[i][1][-1], on=targetfig[i][1][1]).dropna(axis=0)
                                    elif len(targetfig[i][0]) > 2:
                                        print("# Error: import files should not be more than 2 files, please reset 'Targetfig' content!")
                                    # df.to_csv(outpath+'dataoftargetfigmerge{}.csv'.format(i+1), encoding='utf-8-sig', index=False, encoding='utf-8')
                                    # 新增变量值，依据manual.py中addparameter函数。
                                    # @2024/3/13：chang to load /scripts/addparameters.py.
                                    if (targetfig[i][2] != []) & (targetfig[i][2] != ['']):
                                        for j in range(len(targetfig[i][2])): 
                                            if targetfig[i][2][j] != 'changebonds':
                                                df[targetfig[i][2][j]] = addparameter(df, targetfig[i][2][j],rule,dfatoms)
                                            else:df = addparameter(df, targetfig[i][2][j],rule,dfatoms)
                                    # 筛选x，y值范围。
                                    # @2024/3/5：把x，y筛选置于第三方筛选之后。
                                    for j in range(3, 5):
                                        if targetfig[i][j][-1] != []:
                                            if len(targetfig[i][j][-1]) == 1:
                                                # 输出对y1,y2..yn统计结果。
                                                if 'describe' in targetfig[i][4][-1]:
                                                    # @2024/7/11 增加y值不存在提示。
                                                    if set(targetfig[i][4][:-2]).issubset(df.columns.tolist()):
                                                        df[targetfig[i][4][:-2]].describe().to_csv(outpath+'describeoftargetfit{}.csv'.format(i+1), index=True)
                                                    else:
                                                        print("# Warning: set y(s) does not exit in set data, please check it!")
                                                # 对x,y值应用函数调整。
                                                elif 'fun.' in targetfig[i][j][-1][0]:
                                                    # 修正该命令。@2024/3/18。
                                                    # @2025/8/1: repair error.
                                                    df[targetfig[i][j][0]]=df[targetfig[i][j][0]].apply(lambda x:eval(targetfig[i][j][-1][0].split('fun.')[1]))
                                            # # filter range for x, y, should be numeric.
                                            elif ('describe' not in targetfig[i][j][-1]) & (len(targetfig[i][j][-1]) == 2):
                                                df = df[df[targetfig[i][j][0]].between(targetfig[i][j][2][0], targetfig[i][j][2][1], inclusive="both")]                                    
                                            else:print("# Warning: Wrong in x,y value filter set, please check it!")
                                    # @2025/12/21: define plotparams.
                                    plotparams = targetfig[i][7]                                    
                                    # @2024/3/18：修正frame、time数据丢失错误。
                                    # @2024/1/12：修正多个y值选取错误。
                                    # @2025/11/25: add smoothed y values.
                                    # @2025/12/21: add yerror values.
                                    frametime = list(set(['frame','time'])&set(df.columns.tolist()))
                                    thirdlist = []
                                    if len(targetfig[i][5]) > 0: thirdlist = targetfig[i][5][0]
                                    setlist0 = list(dict.fromkeys([targetfig[i][3][0]] + thirdlist + targetfig[i][4][:-2] + frametime))
                                    if 'smoothed' in targetfig[i][1]:
                                        setlist0 = [targetfig[i][3][0]]+ thirdlist + targetfig[i][4][:-2]+[y0+'_smoothed' for y0 in targetfig[i][4][:-2]] + frametime
                                    if plotparams:
                                        if 'yerror' in plotparams:
                                            if plotparams['yerror'][0] == 'columns':
                                                error_cols = [error.strip() for error in plotparams['yerror'][1].split(',')]
                                            else:
                                                errors0 = [y_col+plotparams['yerror'][1] for y_col in targetfig[i][4][:-2]]
                                                errors1 = ['_'.join(y_col.split('_')[:-1])+plotparams['yerror'][1] for y_col in targetfig[i][4][:-2]]
                                                if len(set(errors0)&set(df.columns.tolist())) == len(targetfig[i][4][:-2]): error_cols = errors0
                                                elif len(set(errors1)&set(df.columns.tolist())) == len(targetfig[i][4][:-2]): error_cols = errors1
                                                else: error_cols =[]
                                            if error_cols: setlist0 += error_cols  
                                    setlist = [i for i in setlist0 if i in df.columns.tolist()]
                                    df = df[setlist]
                                    # @2025/4/26: move third part filter before x,y filter.
                                    if len(targetfig[i][5]) > 0:
                                        # 筛选df中出x，y和第三方值
                                        # @2024/5/29；增加交集过滤，避免报错。
                                        if len(targetfig[i][5][-1])>0:      # 定义筛选第三值方法，可同时使用。
                                            # @ 2023/12/3：为适应ReacSpace中物种分析，修改intersect，增加subset, superset, consistant。
                                            # @ 2023/12/12：修正intersect设置。
                                            # 修正输入的reacts,products,reaction列表中化学式顺序。
                                            # @2024/3/5：增加限定条件。
                                            # @2024/3/18：增加molecule输入分子式排序修正。
                                            # @2024/6/25：取消对于list列的变换操作，改为读入文件时设为list。
                                            if 'between' in targetfig[i][5][-1]:         # 范围筛选
                                                if len(targetfig[i][5][1]) == 2:
                                                    try: df = df[df[targetfig[i][5][0][0]].between(targetfig[i][5][1][0], targetfig[i][5][1][1], inclusive="both")]
                                                    except: print('# Error: between set should be operate for numeric data!')
                                                else:print('# Fig{}: Wrong in third part value range([a,b]) set!'.format(i+1))
                                            if 'include' in targetfig[i][5][-1]:         # 筛选包含list中所有值
                                                if targetfig[i][5][1] != []:
                                                    df = df[df[targetfig[i][5][0][0]].apply(lambda x: set(x) >= set(targetfig[i][5][1]))]
                                                else:
                                                    print('# Fig{}: Wrong in third part value list([a,b,c,..]) set!'.format(i+1))
                                            if 'belong' in targetfig[i][5][-1]:          # 筛选属于list中某值，粗略
                                                if len(targetfig[i][5][1])>0:
                                                    df = df[df[targetfig[i][5][0][0]].apply(lambda x: x in targetfig[i][5][1])]
                                                else:
                                                    print('# Fig{}: Wrong in third part value list([a,b,c,..]) set!'.format(i+1))
                                            if 'intersect' in targetfig[i][5][-1]:       # 筛选包含list中某值，粗略
                                                if len(targetfig[i][5][1])>0:
                                                    # @2023/12/3：匹配reacspace结果反应物和产物list。
                                                    df = df[df[targetfig[i][5][0][0]].apply(lambda x: set(x).intersection(set(targetfig[i][5][1])))!=set()]
                                                else:
                                                    print('# Fig{}: Wrong in third part value list([a,b,c,..]) set!'.format(i+1))
                                            if 'subset' in targetfig[i][5][-1]:  # 筛选目标为子集。
                                                df = df[df[targetfig[i][5][0][0]].apply(lambda x: set(x).issubset(set(targetfig[i][5][1])))]
                                            if 'supset' in targetfig[i][5][-1]:  # 筛选目标为超集。
                                                df = df[df[targetfig[i][5][0][0]].apply(lambda x: set(x).issuperset(set(targetfig[i][5][1])))]
                                            if 'consistent' in targetfig[i][5][-1]:  # 筛选目标列表一致。
                                                df = df[df[targetfig[i][5][0][0]].apply(lambda x: set(x) == (set(targetfig[i][5][1])))]
                                    # @2025/3/20: add cumulative sum for y.
                                    static = ['first','sum','cumsum','max','min','std','mean']
                                    intersection = list(set(targetfig[i][4][-1]) & set(static))
                                    # 设置初始绘图参数
                                    hueset = None; hue_orderset = None; legendset = 'auto' 
                                    # operate static calculation for y.
                                    if len(intersection) < 2:
                                        # @2024/4/10：保留有用数据。
                                        # @2024/7/11: 增加y值判断和过滤。
                                        if len(targetfig[i][5]) > 0:
                                            if (len(targetfig[i][5][0]) > 0)&(set(targetfig[i][4][:-2]).issubset(df.columns.tolist())):
                                                ylist = list(set(targetfig[i][4][:-2]+ [targetfig[i][3][0]] + targetfig[i][5][0]))
                                            else:
                                                print("# Warning: third filter item is empty or y(s) does not exit in data, please check it!")
                                        else:
                                            if set(targetfig[i][4][:-2]).issubset(set(df.columns.tolist())):
                                                ylist = targetfig[i][4][:-2]+ [targetfig[i][3][0]]   # 读取x,y或多个y。
                                            else:
                                                ylist = set(targetfig[i][4][:-2]).intersection(set(df.columns.tolist()))+ [targetfig[i][3][0]]
                                        # 增加frame, time输出。
                                        # @2025/8/26: remove frame addition.
                                        for l in ['frame', 'time']:
                                            if (l in df.columns.tolist()) & (l not in ylist): ylist += [l]
                                        # 进行统计提取。
                                        # @2024/4/10：将groupby(targetfig[i][3][0])改为groupby(targetfig[i][j][0])
                                        # @2024/7/21：将groupby(targetfig[i][j][0])改回groupby(targetfig[i][3][0])
                                        # @2025/3/23：add cumsum.
                                        # @2025/3/24: make static suitable for y only.
                                        if len(targetfig[i][5]) > 0:
                                            # @2025/3/24: add groupbylist.
                                            # @2025/8/26: suit for list type targetfig[i][5][0][0].
                                            groupbylist = list(set([targetfig[i][3][0]]+targetfig[i][5][0]))
                                            if 'hue' in targetfig[i][5][-1]:
                                                # set third part filter items.
                                                # @2025/4/26: repair third part filter.
                                                # @2025/11/29: repair zfilterlist for between set.
                                                dfconcat = pd.DataFrame()
                                                if len(targetfig[i][5][1]) > 0 and 'between' not in targetfig[i][5][-1]:
                                                    zfliterlist = targetfig[i][5][1]
                                                else:
                                                    if not isinstance(df[targetfig[i][5][0][0]].iloc[0], list):
                                                        zfliterlist = df[targetfig[i][5][0][0]].unique()
                                                    else:
                                                        zfliterlist = list(set(df[targetfig[i][5][0][0]].sum()))
                                                # @2025/3/23: repair bug from targetfig[i][4][0] to targetfig[i][5][0][0]
                                                # @2025/8/26: suit for list type targetfig[i][5][0][0].
                                                # @2025/11/8: import a new thirdfiter function from mapping.py.
                                                for zitem in zfliterlist:
                                                    if len(intersection)== 1:
                                                        k = intersection[0]
                                                        if k != 'cumsum':
                                                            df0 = thirdfilter(df, targetfig[i][5][0][0], zitem, k, groupbylist, ylist)
                                                        else:
                                                            df0 = df[df[targetfig[i][5][0][0]] == zitem].copy()
                                                            df0 = df0[ylist].groupby(groupbylist).sum().cumsum().reset_index(drop=False)
                                                    else:
                                                        df0 = df[df[targetfig[i][5][0][0]] == zitem].copy()
                                                    if not df0.empty:
                                                        hue_orderset = None
                                                        if targetfig[i][5][0][0] == 'reaction':
                                                            df0['hue'] = list_react2sub([zitem], rule)[0]
                                                            if len(targetfig[i][5][1]) > 0:
                                                                hue_orderset = list_react2sub(targetfig[i][5][1], rule)
                                                        elif targetfig[i][5][0][0] in ['reacts','products','molecule']:
                                                            df0['hue'] = list_compound(zitem, rule)
                                                            if len(targetfig[i][5][1]) > 0:
                                                                hue_orderset = [list_compound(i, rule) for i in targetfig[i][5][1]]
                                                        else:
                                                            df0['hue'] = zitem
                                                        dfconcat = pd.concat([dfconcat,df0],axis=0)
                                                df = dfconcat
                                            else:
                                                # @2025/4/26: remove third filter and reset groupby to targetfig[i][3][0]
                                                if k != 'cumsum':
                                                    df = thirdfilter(df, '', '', k, targetfig[i][3][0], ylist)
                                                else:
                                                    df = df[ylist].groupby(groupbylist).sum().cumsum().reset_index(drop=False)
                                        # no third part filter.
                                        else:
                                            if len(intersection)== 1:
                                                k = intersection[0]
                                                if k != 'cumsum':
                                                    df = thirdfilter(df, '', '', k, targetfig[i][3][0], ylist)
                                                else:
                                                    for y0 in targetfig[i][4][:-2]: df[y0] = df[y0].cumsum()
                                    # @2024/2/6：把else修改为elif，以免animation绘图报错。
                                    elif len(intersection) > 1:
                                        print('# Error: only one static key could be set for y value!')
                                    # @2024/6/22：增加对输出列表排序设置。
                                    # @2024/7/21：修改为基于x轴输出数据。
                                    # @2024/7/30：增加不排序和逆序选项。
                                    if len(df)>0:
                                        if plotparams:
                                            if 'xsort' in plotparams:
                                                if plotparams['xsort'] == 'discend':
                                                    df.sort_values(by = targetfig[i][3][0], ascending=False, inplace=True)   # 降序排列
                                            outliercheck = [i for i in targetfig[i][6] if 'outliers' in i]
                                            if len(outliercheck) == 1:
                                                [methodset, fastmodeset, thresholdset, ncoreset, visualizeset] = outliercheck[0].split('.')[1:]
                                                thresholdset, ncoreset = float(thresholdset), int(ncoreset)
                                                if len(targetfig[i][5]) > 0:
                                                    if ('hue' in targetfig[i][5][-1]) and len(targetfig[i][4][:-2]) == 1:
                                                        zfliterlist = df[targetfig[i][5][0][0]].unique()
                                                        dfall = pd.DataFrame()
                                                        for zitem in zfliterlist:
                                                            dfzfilter = df[df[targetfig[i][5][0][0]]==zitem]
                                                            dfzfilter, dfremoved, filterreport0 = remove_deviations(dfzfilter, time_col=targetfig[i][3][0],
                                                                            target_cols=targetfig[i][4][0],
                                                                            method=methodset, fast_mode=fastmodeset, threshold=thresholdset, n_jobs=ncoreset, visualize=visualizeset)                                                            
                                                            dfall = pd.concat([dfall, dfzfilter], axis=0)
                                                            filterreport += 'Fig{}:'.format(i+1) + filterreport0
                                                        df = dfall
                                                    else:
                                                        df, dfremoved, filterreport0 = remove_deviations(df, time_col=targetfig[i][3][0],
                                                                                    target_cols=targetfig[i][4][:-2],
                                                                                    method=methodset, fast_mode=fastmodeset, threshold=thresholdset, n_jobs=ncoreset, visualize=visualizeset)
                                                        filterreport += 'Fig{}:'.format(i+1) + filterreport0
                                                else:
                                                    df, dfremoved, filterreport0 = remove_deviations(df, time_col=targetfig[i][3][0],
                                                                                target_cols=targetfig[i][4][:-2],
                                                                                method=methodset, fast_mode=fastmodeset, threshold=thresholdset, n_jobs=ncoreset, visualize=visualizeset)
                                                    filterreport += 'Fig{}:'.format(i+1) + filterreport0
                                        else: df.sort_values(by = targetfig[i][3][0], inplace=True)
                                        # @2025/11/8: deal with error when counting bonds num for CC, NN, OO, HH, and etc.
                                        if targetfig[i][0][0]=='bonds' and targetfig[i][4][0] =='num':
                                            df['num'] *= df['bonds'].map(lambda x: 0.5 if len(set(x)) == 1 else 1)
                                        try: df.to_csv(outpath+'dataoftargetfig{}.csv'.format(i+1), encoding='utf-8-sig', index=False)
                                        except: df.to_csv(outpath+'dataoftargetfig{}.temp.csv'.format(i+1), encoding='utf-8-sig', index=False)
                                    else: print('# Warning: No data to output or draw!')
                                    # @2024/3/18：统一调整目标数据格式。
                                    # @2025/8/26： create a function to standardize df columns. at addparamenters.py
                                    df = standardize_df(df)
                                    # 跨文件夹数据汇总，用于'concat'命令绘图。
                                    # @2024/7/31：从绘图判断中移出。
                                    # @2025/9/5: change dfaalldict content.
                                    if 'concat' in targetfig[i][1]:
                                        df['folder']= folder
                                        dfalldict[str(i)] = pd.concat([dfalldict[str(i)],df],axis=0)
                                        targetfigall += [targetfig[i]]
                                    # 判断是否绘图并输出。  # @2023/12/19：修正逻辑，放置于绘图之前判断。
                                    if 'PlotSave' in plotsave:
                                        rcParams.update(config)
                                        # 增加全局绘图label字体设置。  @2024/2/7
                                        # @2025/3/2：直接默认字体。
                                        fontset = FontProperties(labelfont, size = figscale['labelsize'])
                                        sns.set_theme(style=styleset, font=fontlist[0], font_scale=figscale['fontscale'])
                                        if len(df) > 0:
                                            # @2024/5/26：设置y值
                                            # @2024/7/18：修正y值不存在提示。
                                            # @2025/11/24: add 'smoothed' data check.
                                            yset = list(set(targetfig[i][4][:-2]) & (set(df.columns.tolist())))
                                            if 'smoothed' in targetfig[i][1]:
                                                smoothlist = [y0 for y0 in targetfig[i][4][:-2] if 'smoothed' in y0]
                                                if len(smoothlist) ==0:
                                                    yset = list(set(targetfig[i][4][:-2]+[y0+'_smoothed' for y0 in targetfig[i][4][:-2]]) & (set(df.columns.tolist())))
                                                    if len(yset)<2: yset = []
                                            if len(yset)==0:
                                                print("# Warning: set y (or smoothed value) does not exit in data, please check it!")
                                            else:
                                                ylose = set(targetfig[i][4][:-2]) - (set(df.columns.tolist()))
                                                if len(ylose)>0:
                                                    print(f"# Warning: {ylose} does not exit in data, others would be drawn!")
                                            # @2024/7/31：增加绘图排序设置，seaborn默认x轴增值排序。
                                            # @2025/5/9: 修改以下set位置。
                                            sortset = True; markerset = False; locset = 'best';legendlabels = 'auto'
                                            if plotparams:
                                                # 绘图参数栏。
                                                if 'xsort' in plotparams:
                                                    if plotparams['xsort'] in ['discend','nosort']: sortset = False
                                                # 自定义legend位置。best：自动选择最佳位置。
                                                if 'plotloc' in plotparams: locset = plotparams['plotloc']
                                            if drawingcheck == 'MultiFig' and len(yset)>0:
                                                # extract red for doubley or smoothed drawing.
                                                palette00 = sns.color_palette(palette0.get().strip())
                                                if palette0.get().strip() =='tab10':
                                                    color0, colors = palette00[3], palette00[:3] + palette00[4:]
                                                elif palette0.get().strip() =='tab20':
                                                    color0, colors = palette00[6], palette00[:6] + palette00[7:]
                                                elif palette0.get().strip() =='tab20b':
                                                    color0, colors = doubleyscale['y2color'] if doubleyscale['y2color'] else 'red', palette00
                                                elif palette0.get().strip() =='tab20c':
                                                    color0, colors = palette00[4], palette00[:4] + palette00[5:]
                                                else: color0, colors = 'red', palette00
                                                # @2025/11/23: add doubely axis set.
                                                if 'doubley' in targetfig[i][1]: doubleynum += 1
                                                if ('doubley' not in targetfig[i][1]) or (doubleynum % 2 == 1):
                                                    if 'doubley' not in targetfig[i][1]:
                                                        icheck = i - doubleynum//2 - doubleynum%2     # 校正图片序号
                                                        if fignum <= 2: axlist = icheck % 2                # 对应图像个数小等于2和大等于2。
                                                        else: axlist = icheck//2, icheck % 2                    # 取商和余数
                                                        if 'mark' in plotparams: markerset = markerlist[:len(set(targetfig[i][4][:-2])&(set(df.columns.tolist())))]
                                                    else:
                                                        if 'mark' in plotparams: markerset = markerlist[1:][:len(set(targetfig[i][4][:-2])&(set(df.columns.tolist())))]
                                                        icheck = i - doubleynum//2 - doubleynum%2 + 1     # 校正图片序号
                                                        if fignum <= 2: axlist = icheck % 2                # 对应图像个数小等于2和大等于2。
                                                        else: axlist = icheck//2, icheck % 2                    # 取商和余数
                                                    axset = axes[axlist]    # change ax=axes[axlist] to ax=axset
                                                    axset.clear()
                                                    paletteset = palette0.get().strip()
                                                    colorset = None
                                                    if 'doubley' in targetfig[i][1]:
                                                        axlines, axlabels, legendset, oldaxis = [], [], None, axlist  # for doubley axis set.
                                                        # axlines, legendset, oldaxis = [], None, axlist  # for doubley axis set.
                                                        if doubleyscale['y1color']:
                                                            paletteset = doubleyscale['y1color'] if isinstance(doubleyscale['y1color'], list) else [doubleyscale['y1color']]
                                                        else:
                                                            paletteset = colors
                                                    else: axlabels = []
                                                elif ('doubley' in targetfig[i][1]) and (doubleynum % 2 == 0):
                                                    if 'mark' in plotparams: markerset = markerlist[0]
                                                    axset = axes[oldaxis].twinx()
                                                    if doubleyscale['y2color']: colorset = doubleyscale['y2color']
                                                    else: colorset = color0
                                                    legendset, paletteset=None, [colorset]
                                                    if doubleyscale['y2tickcolor']:y2tickcolor = doubleyscale['y2tickcolor']
                                                    else: y2tickcolor = colorset
                                                    if doubleyscale['y2labelcolor']:y2labelcolor = doubleyscale['y2labelcolor']
                                                    else: y2labelcolor = colorset
                                                    axset.tick_params(axis='y', colors=y2tickcolor)  # y轴刻度颜色
                                                    axset.tick_params(axis='y', which='minor', colors=y2tickcolor)   # 次级刻度
                                                    axset.yaxis.label.set_color(y2labelcolor)  # y轴标签颜色
                                                    axset.spines['right'].set_color(y2tickcolor)  # 右边框（如果有）
                                                if 'smoothed' in targetfig[i][1]:
                                                    yset = sorted(yset)
                                                    if len(yset)==2:
                                                        legendset = None
                                                        paletteset = [color0 if '_smoothed' in y else next((c for c in colors)) for y in yset]
                                                # 没有数据拟合情况
                                                if len(targetfig[i][6]) == 0:
                                                    # 判断是否设置hue值
                                                    if not targetfig[i][5] or 'hue' not in targetfig[i][5][-1]:
                                                        # @2025/11/24: smooth operation change to SmoothGUI subwindow.
                                                        # @2024/5/29：修改纵坐标为yset。
                                                        # @2024/7/11: 增加y值校验取其与数据列名交集。
                                                        if len(set(targetfig[i][4][:-2]).intersection(set(df.columns.tolist()))) >1:
                                                            df1=df.set_index(targetfig[i][3][0])[list(set(targetfig[i][4][:-2]).intersection(set(df.columns.tolist())))]
                                                        else:
                                                            df1=df.set_index(targetfig[i][3][0])[yset]
                                                        snsline = sns.lineplot(data=df1, linewidth=2.5, dashes=False, legend=legendset, markers=markerset, palette=paletteset, sort=sortset, errorbar=None, ax=axset)
                                                        # @2025/12/21: add error bar set.
                                                        if 'yerror' in plotparams:
                                                            y_cols = yset if len(set(targetfig[i][4][:-2]).intersection(set(df.columns.tolist()))) <= 1 else \
                                                                    list(set(targetfig[i][4][:-2]).intersection(set(df.columns.tolist())))
                                                            if plotparams['yerror'][0] == 'columns':
                                                                error_cols = [error.strip() for error in plotparams['yerror'][1].split(',')]
                                                            else:
                                                                errors0 = [y_col+plotparams['yerror'][1] for y_col in y_cols]
                                                                errors1 = ['_'.join(y_col.split('_')[:-1])+plotparams['yerror'][1] for y_col in y_cols]
                                                                if len(set(errors0)&set(df.columns.tolist())) == len(y_cols): error_cols =errors0
                                                                elif len(set(errors1)&set(df.columns.tolist())) == len(y_cols): error_cols =errors1
                                                                else: error_cols =[]
                                                            if len(error_cols) == len(y_cols):
                                                                for idx, (y_col, err_col) in enumerate(zip(y_cols, error_cols)):
                                                                    axset.errorbar(x=df[targetfig[i][3][0]], y=df[y_col], yerr=df[err_col], fmt='none',
                                                                        ecolor=snsline.get_lines()[idx % len(snsline.get_lines())].get_color(),
                                                                        capsize=5, elinewidth=1.2)
                                                            else: print(" # Warning: num of error data donot fit with num of y(s), please check it!")
                                                    else:
                                                        hueset = 'hue'
                                                        for yitem in yset:
                                                            snsline = sns.lineplot(data=df, x=targetfig[i][3][0], y=yitem, linewidth=2.5, dashes=False, hue=hueset, hue_order=hue_orderset, style = hueset,
                                                                        legend=legendset, markers=markerset, palette=paletteset, sort=sortset, errorbar=None, ax=axset)
                                                        # @2025/12/21: add error bar set.
                                                        if 'yerror' in plotparams:
                                                            if plotparams['yerror'][0] == 'columns':
                                                                err_cols = [error.strip() for error in plotparams['yerror'][1].split(',')]
                                                            else: 
                                                                errors0 = [y_col+plotparams['yerror'][1] for y_col in y_cols]
                                                                errors1 = ['_'.join(y_col.split('_'))[:-1]+plotparams['yerror'][1] for y_col in y_cols]
                                                                if len(set(errors0)&set(df.columns)) == len(y_cols): err_cols =errors0
                                                                elif len(set(errors1)&set(df.columns)) == len(y_cols): err_cols =errors1
                                                                else: err_cols =[]
                                                            if len(err_cols) >0:
                                                                hue_vals = df[hueset].unique() if hueset in df.columns else []
                                                                for hue_val in hue_vals:
                                                                    subset_df = df[df[hueset] == hue_val].sort_values(by=targetfig[i][3][0])  # 按x轴排序                                                
                                                                    line_color = None
                                                                    for line in axset.get_lines():
                                                                        # 检查线条的x数据是否与当前子集的x数据匹配（长度相同且值相近）
                                                                        if len(line.get_xdata()) == len(subset_df) and \
                                                                        np.allclose(np.sort(line.get_xdata()), np.sort(subset_df[targetfig[i][3][0]].values)) and \
                                                                        np.allclose(np.sort(line.get_ydata()), np.sort(subset_df[yitem].values)):
                                                                            line_color = line.get_color()
                                                                            break
                                                                    if line_color is not None:
                                                                        axset.errorbar(x=subset_df[targetfig[i][3][0]], y=subset_df[yitem], yerr=subset_df[err_cols[0]],
                                                                            fmt='none', ecolor=line_color, capsize=5, elinewidth=1.2)
                                                            else: print(" # Warning: error data for y donot exist, please check it!")
                                                # 进行数据拟合
                                                else:  # 根据def fitting拟合数据并绘图
                                                    fitcheck = [i for i in targetfig[i][6] if (('polyfit' in i) or ('lowess' in i))]
                                                    if len(fitcheck) == 1:
                                                        fitmethod = fitcheck[0].split('.')[0]
                                                        if fitmethod == 'polyfit':
                                                            if len(fitcheck[0].split('.')) == 2:
                                                                df, polyfit, R_square = fitting(df, targetfig[i][3][0], targetfig[i][4][0], 'polyfit', int(fitcheck[0].split('.')[1]))
                                                            elif len(fitcheck[0].split('.')) == 3:
                                                                df, polyfit, R_square = fitting(df, targetfig[i][3][0], targetfig[i][4][0], 'polyfit', int(fitcheck[0].split('.')[1]), fitcheck[0].split('.')[2])
                                                                if 'Reflectfront' in fitcheck[0]:
                                                                    # print("************************************")
                                                                    fitreport += 'Fig{}: Reflect wall results fitted by np.polyfit:'.format(i+1)+'\n'
                                                                    fitreport += 'a. Wavefront velocity:  {:.2f} km/s'.format(polyfit[1]*0.1+abs(vimpact))+'\n'
                                                                    fitreport += 'b. Wavefront pressure:  {:.2f} GPa'.format((polyfit[1]*0.1+abs(vimpact))*density*abs(vimpact))+'\n'
                                                                    fitreport += 'c. Fitting funciton and R^2:'+'   {}'.format(polyfit)+'     {:.4f}'.format(R_square)+'\n'
                                                                    sns.scatterplot(data=df, x=targetfig[i][3][0], y=targetfig[i][4][0], marker=markerset, ax=axset)            # ncol表示图例有几列
                                                                elif 'scatter' in fitcheck[0]:
                                                                    sns.scatterplot(data=df, x=targetfig[i][3][0], y=targetfig[i][4][0], marker=markerset, ax=axset) 
                                                                    fitreport += 'Fig{}: Results fitted by np.polyfit:'.format(i+1)+'\n'
                                                                    fitreport += 'a. Fitting funciton and R^2:   {}      {:.4f}'.format(polyfit, R_square)+'\n\n'
                                                                elif 'line' in fitcheck[0]:
                                                                    sns.lineplot(data=df, x=targetfig[i][3][0], y=targetfig[i][4][0], linewidth=2.5, marker=markerset, ax=axset)            # ncol表示图例有几列
                                                                    fitreport += 'Fig{}: Results fitted by np.polyfit:'.format(i+1)+'\n'
                                                                    fitreport += 'a. Fitting funciton and R^2:   {}      {:.4f}'.format(polyfit, R_square)+'\n\n'
                                                        elif fitmethod == 'lowess':
                                                            fset = float(fitcheck[0].split('.')[-2])
                                                            iset = float(fitcheck[0].split('.')[-1])
                                                            if 'line' in fitcheck[0]:
                                                                sns.lineplot(data=df, x=targetfig[i][3][0], y=targetfig[i][4][0], linewidth=2.5, marker=markerset, ax=axset)            # ncol表示图例有几列
                                                            elif 'scatter' in fitcheck[0]:
                                                                sns.scatterplot(data=df, x=targetfig[i][3][0], y=targetfig[i][4][0], marker=markerset, ax=axset) 
                                                            df = fitting(df, targetfig[i][3][0], targetfig[i][4][0], 'lowess', fset, iset)
                                                        df.to_csv(outpath+'dataoftargetfit{}.csv'.format(i+1), index=True)
                                                        sns.lineplot(data=df, x=targetfig[i][3][0], y=fitmethod+targetfig[i][4][0], linewidth=2.5, legend='auto', color='r', ax=axset)
                                                axset.xaxis.set_minor_locator(AutoMinorLocator(2))    # 2表示增加一个子刻度。
                                                axset.yaxis.set_minor_locator(AutoMinorLocator(2))
                                                # 设置legend，xy坐标轴标签和刻度的字体大小
                                                # @2024/3/19：增加刻度字体设置。
                                                # axset.legend(frameon=False, loc=locset, fontsize=figscale['labelsize'])
                                                axset.set_xlabel(targetfig[i][3][1], fontsize=figscale['labelsize'])
                                                axset.set_ylabel(targetfig[i][4][-2], fontsize=figscale['labelsize'])
                                                axset.tick_params(axis='both', labelsize=figscale['ticksize'])
                                                if 'ylimit' in plotparams: axset.set_ylim(plotparams['ylimit'][0], plotparams['ylimit'][1])
                                                # 解决matplotlib使用1e6显示图形。
                                                formatter = ticker.ScalarFormatter()
                                                formatter.set_scientific(False)
                                                axset.yaxis.set_major_formatter(formatter)
                                                # legend set.
                                                if (len(targetfig[i][5]) == 0) or ((len(targetfig[i][5]) > 0 and 'hue' not in targetfig[i][5][-1])):
                                                    if plotparams:
                                                        if 'legend' in plotparams:
                                                            if plotparams['legend'][0] == 'list': axlabels += plotparams['legend'][1]
                                                            elif plotparams['legend'][0] == 'remove': axlabels += [label.replace(plotparams['legend'][1][0],'') for label in targetfig[i][4][:-2]]
                                                            elif plotparams['legend'][0] == 'suffix': axlabels += [label+plotparams['legend'][1][0] for label in targetfig[i][4][:-2]]
                                                        else: axlabels+=targetfig[i][4][:-2]
                                                    else:
                                                        axlabels+=targetfig[i][4][:-2]
                                                elif len(targetfig[i][5]) > 0 and 'hue' in targetfig[i][5][-1]:
                                                    if len(targetfig[i][5][1])>0:
                                                        if targetfig[i][5][0][0] in ['reacts','products','reaction', 'molecule']:
                                                            axlabels+=list_react([targetfig[i][5][1][0]],rule)
                                                        else:
                                                            axlabels+=targetfig[i][5][1]
                                                    else:
                                                        legends = axset.get_legend()
                                                        if legends: axlabels = [text.get_text() for text in legends.get_texts()]                                                            
                                                        else: axlabels = []
                                                if len(targetfig[i][5]) > 0:
                                                    legendunit = targetfig[i][5][2].strip()
                                                    if legendunit and axlabels: axlabels = [axlabel+' '+legendunit for axlabel in axlabels]
                                                # doubleynum set
                                                if 'doubley' not in targetfig[i][1]:
                                                    if 'xsort' in plotparams:
                                                        if plotparams['xsort'] == 'discend': axset.invert_xaxis()
                                                    if 'smoothed' in targetfig[i][1] and len(yset)==2:
                                                        axset.legend(axset.lines, labels=['Original','Smoothed'], loc=locset, frameon=False, fontsize=figscale['labelsize'])
                                                    else:
                                                        if axlabels: axset.legend(frameon=False, labels=axlabels, loc=locset, fontsize=figscale['labelsize'])
                                                        else: axset.legend(frameon=False, loc=locset, fontsize=figscale['labelsize'])
                                                    plt.savefig(outpath+'figoftarget.png',bbox_inches='tight')
                                                    print('# Success: Fig{} has been saved to {} folder!'.format(i+1,targetfolder))
                                                else:
                                                    # 如果有yerror，只取原始数据线条，避免包含errorbar线条
                                                    if 'yerror' in plotparams:
                                                        expected_lines = len(yset) if not hueset else len(df[hueset].unique()) * len(yset)
                                                        axlines += axset.lines[:expected_lines]
                                                    else: axlines += axset.lines
                                                    if doubleynum % 2 == 0:
                                                        # doubley时，对第二个y轴执行invert，避免执行两次。
                                                        if 'xsort' in plotparams:
                                                            if plotparams['xsort'] == 'discend': axset.invert_xaxis()                                                        
                                                        # 确保在doubley模式中，图例的线条和标签正确匹配
                                                        # 在第二个y轴（右轴）时创建联合图例，但要确保颜色和标签匹配
                                                        axset.legend(axlines, axlabels, loc=locset, frameon=False, fontsize=figscale['labelsize'])
                                                        plt.savefig(outpath+'figoftarget.png',bbox_inches='tight')
                                                        print('# Success: Fig{} and Fig{} has been saved to {} folder!'.format(i, i+1,targetfolder))
                                            elif drawingcheck == 'Animation'  and len(yset)>0:
                                                if simulate.get() != 'manual':
                                                    framelist = list(df['frame'].unique())
                                                    thermostep0 = framelist[1] - framelist[0]
                                                    aniunit = aniunit0.get()
                                                    if anivalue != '':
                                                        if aniunit == 'frame':
                                                            # @2024/6/22：增加条件判断，允许输入为空
                                                            if anivalue[0].strip() == '': anivalue00 = framelist[0]
                                                            else: anivalue00 = int(anivalue[0].strip())
                                                            if anivalue[1].strip() == '': anivalue01 = framelist[-1]
                                                            else: anivalue01 = int(anivalue[1].strip())
                                                        elif aniunit == 'time(ps)':
                                                            if anivalue[0].strip() == '': anivalue00 = framelist[0]
                                                            else: anivalue00 = int(float(anivalue[0].strip())*1000/timestep0)
                                                            if anivalue[1].strip() == '': anivalue01 = framelist[-1]
                                                            else: anivalue01 = int(float(anivalue[1].strip())*1000/timestep0)
                                                        frameset = [anivalue00, anivalue01]
                                                    else:
                                                        frameset = [framelist[0], framelist[-1]]
                                                    # @2024/6/22：增加轨迹范围筛选。
                                                    df = df[df['frame'].between(frameset[0],frameset[1])]
                                                # @2024/2/27：将于不含frame或time数据设置为单帧。
                                                else:
                                                    frameset = [0,1]
                                                    framelist = [0,1]
                                                    thermostep0 = 1
                                                    df['frame'] = 0
                                                if (frameset[0]>=framelist[-1]) or (frameset[1]<=framelist[0]):
                                                    print("# Error: animation range set is out of range, please check 'Range/Inter(ms)' set!")
                                                else:
                                                    if frameset[0] < framelist[0]:
                                                        frameset[0] = framelist[0]
                                                    elif frameset[1] > framelist[-1]:
                                                        frameset[1] = framelist[-1]
                                                    if anitype == 'isograph':
                                                        items = [[targetfig[i][3][0],targetfig[i][3][1]],[targetfig[i][4][0],targetfig[i][4][1]],[targetfig[i][-1][0][0],targetfig[i][-1][0][1]]]
                                                        axislimit = [df[targetfig[i][3][0]].min(),df[targetfig[i][3][0]].max(),df[targetfig[i][4][0]].min(),df[targetfig[i][4][0]].max()]
                                                        isoset = eval(targetfig[i][-1][0][2])
                                                        figtitle = targetfig[i][-1][1]
                                                        fargslist = (fontset, items, axislimit, figtitle, isoset)
                                                    elif (anitype == 'bar') or (anitype == 'line'):
                                                        # @2024/3/18：增加x，y坐标最大值为数据的1.01倍。
                                                        # @2024/6/22：增加size情况适用脚本。
                                                        # @2024/7/18：补充targetfig[i][5]为[]情况，避免报错。
                                                        # @2025/9/5: remove size condition.
                                                        items = [[targetfig[i][3][0],targetfig[i][3][1]],[targetfig[i][4][0],targetfig[i][4][1]]]
                                                        axislimit = [df[targetfig[i][3][0]].min(),df[targetfig[i][3][0]].max()*1.02,df[targetfig[i][4][0]].min(),df[targetfig[i][4][0]].max()*1.02]
                                                        figtitle = targetfig[i][-1][1]
                                                        fargslist = (fontset, items, axislimit, figtitle, barscale)
                                                    ani = FuncAnimation(fig, animateupdate, frames=range(frameset[0], frameset[1]+thermostep0, thermostep0), fargs = (df, anitype) + fargslist, interval=intervalset, repeat = False)
                                                    # 事件处理，点击暂停，点击继续。
                                                    paused = False
                                                    fig.canvas.mpl_connect('button_press_event', toggle_pause)
                                                    outtype = targetfig[i][-1][-1]
                                                    if 'html' in outtype:
                                                        ani.save(outpath+'animationfig{}.html'.format(i+1), writer='html', dpi=figscale['dpi'])
                                                    if 'gif' in outtype:
                                                        ani.save(outpath+'animationfig{}.gif'.format(i+1), writer='pillow', dpi=figscale['dpi'])
                                                    # plt.show()   # 有了%matplotlib inline可省略
                                                print('# Fig{}: Animation Fig has been saved to {} folder!'.format(i+1,targetfolder))
                                            else:
                                                print('# Error: wrong drawing mode or no y was available in data, pelase check it!')
                                        else:
                                            print('# Attention: No data of Fig{} is selected, please check input data range!'.format(i+1))
                                    else: print("# Attention: 'PlotSave' button is not selected, target polt(s) would not be saved!")
                            else:
                                print('# Warning: Fig{} was skipped because no file(s) to be loaded!'.format(i+1))
                                continue                  # 当输入文件为空时跳过当前绘图，进入下一绘图。       
                        if filterreport !='':
                            with open(outpath+'filterreport.txt','w') as f: f.write(filterreport)
                        if fitreport !='':
                            with open(outpath+'fitreport.txt','w') as f: f.write(fitreport)                    
                    else: print('# Attention: Targetfig is empty, please insert it into "targetfig" button!')
                # 汇总concat输出绘图数据
                if len(targetfigall)>0:
                    # @2025/9/5: 删除文件夹（如果存在）并重新创建
                    dataall_path = inpath.get()+ "/dataall/"
                    if not os.path.exists(dataall_path):
                        # shutil.rmtree(dataall_path, ignore_errors=True)  # 强制删除，忽略错误（如文件夹不存在）
                        try: os.makedirs(dataall_path, exist_ok=True)         # 重新创建，exist_ok=True 避免重复创建时报错
                        except:
                            dataall_path = inpath.get()+ "/dataall1/"
                            os.makedirs(dataall_path, exist_ok=True)
                        print('# Attention: dataall folder has been bulided or rebuilded!')
                    # @2025/9/5: 保存targetfig为文本。
                    with open(dataall_path + 'targetfigset.txt', 'w', encoding='utf-8') as f:
                        for fig in targetfigall:
                            f.write('{}'.format(fig).translate(resub).translate(resup)[1:-1]+'\n')    # 去掉可能生成的上下标。
                        print('# Success: dataoffig{} has been saved to dataall folder'.format(i+1))
                    if plotparams:
                        # 绘图参数栏。
                        if 'xsort' in plotparams:
                            if plotparams['xsort'] == 'nosort': sortset = False
                        if 'PlotSave' in plotsave:
                            # @2025/3/3：改为单图绘制。
                            # @2025/9/5: change to multi fig.
                            # fig方法筛选，用于调用绘图设置。
                            if len(targetfigall)>1:
                                fig, axes = plt.subplots(math.ceil(len(targetfigall)/2), 2, figsize=(figscale['width'], math.ceil(len(targetfigall)/2)*figscale['high']), dpi=figscale['dpi'])    # 设置多图行列和尺寸
                                plt.subplots_adjust(left=subplotadjust['left'], bottom=subplotadjust['bottom'], right=subplotadjust['right'], top=subplotadjust['top'], wspace=subplotadjust['wspace'], hspace=subplotadjust['hspace'])
                            # @2024/12/14：增加单图片匹配。
                            elif len(targetfigall)==1:
                                fig, axes = plt.subplots(1, 1, figsize=(singlescale['width'],singlescale['high']), dpi=singlescale['dpi'])    # 设置多图行列和尺寸
                                axes = [axes]
                            dfallkeys = list(dfalldict.keys())
                            for i in range(len(targetfigall)):
                                if len(targetfigall) <= 2:axlist = i % 2                # 对应图像个数小等于2和大等于2。
                                else:axlist = int(i/2), i % 2
                                # @2025/9/5: read dfall data from dfalldict. 
                                dfall = dfalldict[dfallkeys[i]]
                                try: dfall['hue'] = dfall['folder'].str.extract('(\d+\.?\d*)').astype(float)
                                except: dfall['hue'] = dfall['folder']
                                if 'time' in dfall.columns: dfall = dfall.sort_values(by=['hue','time'],ascending=True).reset_index(drop=True)
                                else: dfall = dfall.sort_values(by='hue',ascending=True).reset_index(drop=True)                            
                                # 设置绘图参数
                                legendset2 = 'auto'
                                markerset2 = False
                                locset2 = 'best'
                                if figallscale['loc'].strip():
                                    locset2 = figallscale['loc'].strip()
                                if figallscale['mark']: 
                                    markerset2 = markerlist[0:dfall['hue'].nunique()]
                                # @2025/3/6：此处对于legend加单位进行处理，单位定义在targetfig[i][5][2]。
                                # @2025/12/27: 改为从plotset获取legendunit.
                                if figallscale['legendunit'].strip():
                                    dfall['hue'] = dfall['hue'].astype(str) + ' ' + figallscale['legendunit'].strip()
                                dfall.to_csv(dataall_path+"dataoffig{}.csv".format(i+1), encoding='utf-8-sig', index=False)
                                # @2024/5/26：改用yset代替targetfig[i][4][0]
                                # @2024/7/31: y值改为条件判断。
                                if markerset2:
                                    sns.lineplot(data=dfall, x = targetfigall[i][3][0], y = targetfigall[i][4][0], dashes=False, hue='hue', legend=legendset2, markers=markerset2, palette=paletteset, ax=axes[axlist])
                                else: 
                                    sns.lineplot(data=dfall, x = targetfigall[i][3][0], y = targetfigall[i][4][0], dashes=False, hue='hue', legend=legendset2, palette=paletteset, ax=axes[axlist])
                                # @2024/7/30：增加子刻度显示。
                                axes[axlist].xaxis.set_minor_locator(AutoMinorLocator(2))    # 2表示增加一个子刻度。
                                axes[axlist].yaxis.set_minor_locator(AutoMinorLocator(2))
                                axes[axlist].legend(frameon=False, loc=locset2, fontsize=figscale['labelsize'])
                                axes[axlist].set_xlabel(targetfigall[i][3][1], fontsize=figscale['labelsize'])
                                axes[axlist].set_ylabel(targetfigall[i][4][-2], fontsize=figscale['labelsize'])
                                # 解决matplotlib使用1e6显示图形。
                                formatter = ticker.ScalarFormatter()
                                formatter.set_scientific(False)
                                axes[axlist].yaxis.set_major_formatter(formatter)
                            plt.savefig(dataall_path +'figall.png', bbox_inches='tight')
                            print('# Success: Figalls have been saved to dataall folder!')
                # print('# Attention: Mapping of target fig(s) finished!')
                print('****************************************************************************')
            else:
                print('# Error: Folder(s) is empty, please set Folder(s) to read!')
        else:
            print('# Error: Inpath is empty, please input a path!')
    # RunButton
    ButtonRun2 = tk.Button(tab2, text="Run", command=lambda: controller.thread_it(runmapping), fg='white', bg='blue', width=9)
    ButtonRun2.grid(row=10, column=8)



    ####################### tab8设置 #########################
    about = """
    Software: LMPAnalysis
    Usage: a analysis tool for molecular dynamics software LAMMPS.
    Author: Gan Qiang
    Email: ganqiang@bit.edu.cn
    Institution: Beijing Institute of Technology

    Version: {}
    Date: {}
    (For Internal Use Only!)
    """.format(version, data)
    tk.Label(tab8, text=about).pack()

    # 加载
    root.mainloop()
    tab1.mainloop()
    tab2.mainloop()
    tab3.mainloop()
    tab4.mainloop()
    tab5.mainloop()
    tab6.mainloop()
    tab7.mainloop()
    tab8.mainloop()

if __name__ == "__main__":
    label0 = """LMPAnalysis: an analysis tool for molecular dynamics software LAMMPS."""
    news0 = """    LMPAnalysis
    Version: 2.8.4
    Date: 2026.1.4

    Attention:
    If an error is reported after updating, please press the Reset button.

    Update:
    @2026/1/4: ReacNetwork: repair some errors.
    @2025/12/31: Mapping: repair some errors."""
    messageshow('Messange','420x240',0,0,news0,'lightskyblue')
    create_window(label0,news0)