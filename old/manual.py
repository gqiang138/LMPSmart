# -*- coding:utf-8 -*-
"""
本脚本用于lmpanalysis程序包通用函数和变量设置, 
    全部函数调用: form manual import *
    个别函数调用: form manual import xx,xx
Date = 2023.10.22

@2023/12/12：为解决list_react和list_react_nosub丢失分子数错误，修正脚本；
"""
#%%
import os,re,sys,glob,time,subprocess, chardet, platform, warnings,sys, logging, io, base64
import pandas as pd
import numpy as np
import xml.etree.ElementTree as ET
import statsmodels.api as sm
lowess = sm.nonparametric.lowess
from sklearn.metrics import r2_score
from openbabel.pybel import readfile, Outputfile
from rdkit import Chem, RDLogger 
from rdkit.Chem import Draw, AllChem, SDMolSupplier, MolFromMolBlock
from rdkit.Chem.Draw import MolDraw2DSVG, MolDraw2DCairo
from rdkit.Chem.MolStandardize import rdMolStandardize 
RDLogger.DisableLog('rdApp.*')  
from IPython.display import SVG, display
from collections import Counter
from typing import Union, List, Tuple
from PIL import Image, ImageDraw, ImageFont
import matplotlib.pyplot as plt
from scipy.spatial import cKDTree
from scipy.stats import norm, normaltest
from concurrent.futures import ThreadPoolExecutor
from tqdm.auto import tqdm
from io import BytesIO

# from ovito.io import import_file, export_file
# from ovito.modifiers import CalculateDisplacementsModifier, CoordinationAnalysisModifier, TimeAveragingModifier
sub = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")     # 定义一个数字变下标方法（勿删改），使用方法astring.translate(sub)。                                
# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#------------------通用模块和函数 ----------------#
# 定义元素原子量和元素名，之后用函数atom_type()分析字符串，返回元素种类。
weightatoms = {1:'H', 12:'C', 14:'N', 16:'O', 19:'F', 27:'Al', 28:'Si', 32:'S',56:'Fe', 64:'Cu',}
orderatoms = {1:'H',6:'C',7:'N',8:'O',9:'F',13:'Al',14:'Si', 16:'S',26:'Fe',29:'Cu',}

# 根据原子量返回元素符号。
def atom_type(str1):
    num = four_five(float(str1))
    if  num in weightatoms.keys():
        return weightatoms[num]
    else:
        return 'This element is not defined, please add it to weightatoms in manual.py!'
# 根据元素名词返回原子序号。   @ 2024/2/8
def atom_order(str1):
    newdict = {value: key for key, value in orderatoms.items()}
    if str1 in newdict.keys():
        return newdict[str1]
    else:
        return 'This element is not defined, please add it to orderatoms in manual.py!'
# 根据元素名词返回原子量，用于计算分子量。
def type_atom(str1):
    dicttype = {value:key for key,value in weightatoms.items()}
    if str1 in dicttype.keys():
        return dicttype[str1]
    else: return 'This element is not defined, please add it to weightatoms in manual.py!'
# 根据化学元素名称拆分字符串，返回元素列表。
def find_elements(input_string):
    element_pattern = re.compile(r'[A-Z][a-z]?')
    elements = element_pattern.findall(input_string)
    return elements
# example
# string = 'AlOCHHe'
# element_list = find_elements(string)
# print(element_list)

# 定义原子id、原子类型和原子量字典，用于data文件。
def df_atoms(datapath):
    datafile = glob.glob(datapath)[0]  # 模糊匹配文件名
    dataf = open(datafile, "r", encoding="utf-8")
    datalines = dataf.read().splitlines()                     # 去掉换行符'\n'，数据行前后都有空格
    for i in range(len(datalines)):         # 根据data文件生成元素编号列表dfatoms
        if datalines[i].strip() == 'Masses':
            for j in range(i, len(datalines)):
                if (datalines[j] == '') & (j>i+1):break
            dfatoms = pd.DataFrame((re.split(" +|\t",k.strip())[0:2] for k in datalines[i+2:j]),columns=['type','mass'])
    dfatoms['type'] = dfatoms['type'].astype(int)       # type指data文件中原子类型
    dfatoms['mass'] = dfatoms['mass'].apply(lambda x : four_five(float(x)))
    dfatoms['element'] = dfatoms['mass'].apply(lambda x : atom_type(x))      # type指元素符号
    dfatoms = pd.concat([dfatoms,pd.DataFrame({'type':[0],'mass':[0],'element':['']})],ignore_index=True)  # 增加空值行，对应未成键原子。
    return dfatoms[dfatoms['type'] !=0]
# datapath = input('拖入data文件：')
# df = df_atoms(datapath)
# print(df)
# 定义pandas排序函数，可根据数字字符混合的字符串中数字排序。
def dfsort(df0,str,mode):
    if mode == 'num':
        df0[str+'1'] = df0[str].apply(lambda x: float(re.findall(r"\d+\.?\d*",x)[0]))
        df0=df0.sort_values(by=[str+'1']).reset_index(drop=True).drop(str+'1', axis=1)
    elif mode =='str':
        df0=df0.sort_values(by=[str]).reset_index(drop=True)
    return df0

# 合并list中子list所有元素，order=2表示有二级list，order=3有三级list。
def merge_list(my_list,order):
    merged_list = []
    if len(my_list)>0:
        if order ==1:
            for item in my_list:
                # 检查是否为浮点数（如NaN）或 None，如果是则跳过
                if item is None or (isinstance(item, float) and pd.isna(item)):
                    continue
                merged_list.append(item)
        if order == 2:
            for sublist in my_list:
                # 检查sublist是否为浮点数（如NaN）或 None，如果是则跳过
                if sublist is None or (isinstance(sublist, float) and pd.isna(sublist)):
                    continue
                if isinstance(sublist, (list, tuple)) and len(sublist) > 0:
                    for item in sublist:
                        # 检查item是否为浮点数（如NaN）或 None，如果是则跳过
                        if item is None or (isinstance(item, float) and pd.isna(item)):
                            continue
                        merged_list.append(item)
        elif order ==3:
            for sublist in my_list:
                # 检查sublist是否为浮点数（如NaN）或 None，如果是则跳过
                if sublist is None or (isinstance(sublist, float) and pd.isna(sublist)):
                    continue
                if isinstance(sublist, (list, tuple)) and len(sublist) > 0:
                    for subsublist in sublist:
                        # 检查subsublist是否为浮点数（如NaN）或 None，如果是则跳过
                        if subsublist is None or (isinstance(subsublist, float) and pd.isna(subsublist)):
                            continue
                        if isinstance(subsublist, (list, tuple)) and len(subsublist) > 0:
                            for item in subsublist:
                                # 检查item是否为浮点数（如NaN）或 None，如果是则跳过
                                if item is None or (isinstance(item, float) and pd.isna(item)):
                                    continue
                                merged_list.append(item)
    return merged_list
# example
# mylist = [[1, 2, 3], [4, 5], [6, 7, 8, 9], [10]]
# print(merge_list(mylist,2))
# # [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
# mylist = [[[1, 2, 3], [4, 5], [6, 7, 8, 9], [10]],[[11, 12, 13], [14, 15], [16, 17, 18, 19], [20]]]
# print(merge_list(mylist,3))
# # [1, 2, 3, 4, 5, 6, 7, 8, 9, 10,11,12,13,14,15,16,17,18,19,20]

# 定义键级和键长阈值
# @ 2023.5.5 增加单原子键级和键长阈值0，匹配dataofbonds文件。
def cut_off():
    dictcutoff = {'bonds':['CC','CN','CO','CH','NN','NO','NH','OO','OH','HH',
                       'NC','OC','HC','ON','HN','HO','AlC','AlH','AlN','AlO','CAl','HAl','NAl','OAl','AlAl',
                       'C','N','O','H','Al'],
              'bocutoff':[0.55,0.30,0.65,0.40,0.55,0.40,0.55,0.65,0.40,0.55,
                        0.30,0.65,0.40,0.40,0.55,0.40,0.30,0.30,0.30,0.30,0.30,0.30,0.30,0.30,0.30,
                        0,0,0,0,0],
              'blcutoff':[1.8,2.1,1.9,1.5,2.1,1.5,3,3,3,3,
                        2.1, 1.9, 1.5, 1.5, 3, 3, 3.2, 2.0, 3.0, 2.8, 3.2, 2.0, 3.0, 2.8,2.8,
                        0,0,0,0,0]}
    dfcutoff = pd.DataFrame(dictcutoff)
    return dfcutoff

# 定义文件夹和文件过滤规则
# @ 2024/6/7：修改匹配多级文件读取，支持通配符*
# @2025/8/18: improve * support for filefilter.
def folderfilter(inpath, folder):
    filesread = os.listdir(inpath);dirList = []
    for f in filesread:
        if os.path.isdir(inpath + '/'+f):
            dirList.append(f)                            # 判断目录是否是文件夹
    if folder == 'all':
        if 'dataall' in dirList:
            dirList.remove('dataall')
        return dirList
    elif folder == '': return []
    else:
        folderlist =glob.glob(inpath +'/'+ folder)
        folderlist = [i.replace('\\', '/').replace(inpath+'/','') for i in folderlist if os.path.isdir(i)]
        return folderlist
def filefilter(inpath, folder, read):
    readpath = (inpath+'/'+folder+'/'+read+'/').replace('\\','/').replace('//','/')
    readpaths = [path.replace('\\', '/') for path in glob.glob(readpath)]
    try: 
        filesread = os.listdir(readpaths[0])
        fileList = []
        for f in filesread:
            if os.path.isfile(readpaths[0] + f):
                fileList.append(f)               # 判断目录是否是文件
        return fileList
    except: print("# Warining: target path does not exit, please check it!")
# inpath = 'F:/ganqiang'
# folder = 'reacnetwork'
# read = '*'
# print(filefilter(inpath, folder, read))

# 定义四舍五入函数
def four_five(num):                # num为float格式
    num1, num2 = str(num).split('.')
    if float(str(0) + '.' + num2) >= 0.5:      # 四舍五入判断
        return int(num1)+1
    else: return int(num1)

# 定义原子id、原子类型和原子量字典，用于data,bonds,dump,dataofbonds文件。
# return atoms,lines,atomnum。
# 注意data模式返回的atoms为pandas列表。
# @2025/4/19：modify to output ids changed with time.
def atoms_idtype(datapath,filetype,codeset='utf-8'):
    file = glob.glob(datapath)[0]  # 模糊匹配文件名
    if filetype in ['bondsdata','dumpdata']:
        df0 = pd.read_csv(file)
    else:
        f = open(file, "r", encoding = codeset)
        lines = f.read().splitlines()                     # 去掉换行符'\n'，数据行前后都有空格
    dfid = pd.DataFrame()
    if filetype == 'data':
        for i in range(len(lines)):         # 根据data文件生成元素编号列表dfatoms
            if 'atoms' in lines[i].strip():
                atomnum = int(lines[i].strip().split(' ')[0])
            if lines[i].strip() == 'Masses':
                for j in range(i, len(lines)):
                    if (lines[j] == '') & (j>i+1):break
                atoms = pd.DataFrame((re.split(" +|\t",k.strip())[0:2] for k in lines[i+2:j]),columns=['type','mass'])
            if lines[i].strip() == 'Atoms':
                idline0, idline1 = i+2, i+2+atomnum
        atoms['type'] = atoms['type'].astype(int)
        atoms['mass'] = atoms['mass'].apply(lambda x : four_five(float(x)))
        atoms['element'] = atoms['mass'].apply(lambda x : atom_type(x))
        dfid = pd.DataFrame((re.split(" +|\t",k.strip())[0:2] for k in lines[idline0: idline1]),columns=['id','type'])
        dfid[['id','type']] = dfid[['id','type']].astype(int)
    elif filetype == 'bonds':
        atomnum = int(lines[2].split(' ')[4])
        idlist = []; typelist = []
        for i in range(7, atomnum+7):
            match = re.findall('[+-\][0-9\.]+', lines[i])
            idlist += [int(match[0])]; typelist += [int(match[1])]
        atoms = dict(zip(idlist, typelist))
    elif filetype == 'dump':
        atomnum = int(lines[3].strip())
        idlist, typelist = [], []
        for i in range(9, atomnum+9):
            match = re.findall('[+-\][0-9\.]+', lines[i])
            idlist += [int(match[0])]; typelist += [int(match[1])]
        atoms = dict(zip(idlist, typelist))
        for i in range(len(lines)):
            if lines[i].strip() == 'ITEM: TIMESTEP':
                frame = int(lines[i+1].strip())
                atomnum0 = int(lines[i+3].strip())
                idline0, idline1 = i+9, i+9+atomnum0
                dfid0 = pd.DataFrame((re.split(" +|\t",k.strip())[0:2] for k in lines[idline0: idline1]),columns=['id','type'])
                dfid0.insert(0,'frame',frame)
                dfid = pd.concat([dfid, dfid0],axis=0).reset_index(drop=True)
        dfid[['id','type']] = dfid[['id','type']].astype(int)
    elif filetype == 'bondsdata':
        idlist = df0['id1'].unique().astype(int).values.tolist()
        typelist = df0[['id1','type1']].groupby('id').first().values.tolist()
        elementlist = df0[['id1','bonds']].groupby('id1').first().apply(lambda x: x[0]).values.tolist()
        atomnum = len(idlist)
        atoms = dict(zip(idlist, elementlist))
    elif filetype == 'dumpdata':
        dfid = df0[['frame','id','type']]
        typelist = df0[['id','type']].groupby('id').first().reset_index(drop=False)
        atoms = typelist.set_index('id')['type'].to_dict()
        atomnum = len(atoms)
    return atoms, atomnum, dfid
# example
# idfilepath = input('请拖入id文件：')
# atoms,lines,atomnum = atoms_idtype(idfilepath,'id','utf-8')
# print(atoms)
# print(type(atoms))

# 定义smile转formula函数
# @2025/1/14：改进代码匹配不规范smiles，如"On1onoo1"
def smile2formula(smile, rule):
    smiles_lower = smile.lower()
    # 计算所有在 rule1 中定义的元素的出现次数
    element_counts = Counter(key for key in rule for i in range(len(smiles_lower)) if smiles_lower.startswith(key.lower(), i))
    # 生成字符串，只包含 rule1 中定义的元素，忽略下标1。
    element_str = ''.join([f'{key}{"" if count == 1 else count}' for key, count in element_counts.items() if count > 0])
    return element_str
# example
# str1 = '[H]C1([H])N(N(O)O)C([H])([H])N(N(=O)O)C([H])([H])N1N(=O)O'
# C3H6N6O6
# str1 = 'HHHHNCNCNOO'
# C2H4N3O2
# str1 = 'AlCHHAlAlAlAlAlAlAlAlAlNOOOOOOOOOAlAl'
# Al12C1H2N1O9
# rule1 = {'C':0,'H':1,'N':2,'O':3}
# rule1 = {'Al':0,'C':1,'H':2,'N':3,'O':4}
# print(smile2formula(str1,rule1))

# 定义从反应式中的分子式提取开头数字，以及末尾括号数字（匹配varxmd），改进list_react函数。  # @2023/12/12
def numsting(str):
    if str and str.strip():
        if str.strip()[0].isalpha() or str.strip()[0] == '1':
            return ''
        else:
            result = re.match(r'\D*(\d+)', str.strip())
            return result.group(1)
    else: return ''
def stringnum(str):
    # 使用正则表达式来提取字符串中最后的括号及其中的数字
    result = re.search(r'\((\d+)\)$', str.strip())
    if result:
        extracted = result.group(1)
        return '({})'.format(extracted)
    else:
        return ''
# 定义分子式排序和下标函数
def list_compound(str1,rule):
    list0 = re.findall('[A-Z][a-z]*[0-9]*',str1)
    newlist = sorted(list0, key=lambda x: rule[re.split("\d\d*", x)[0]])
    str2 = ''.join(j.translate(sub) for j in newlist)
    return str2
def list_compound_nosub(str1,rule):    # 无下标
    list0 = re.findall('[A-Z][a-z]*[0-9]*',str1)
    newlist = sorted(list0, key=lambda x: rule[re.split("\d\d*", x)[0]])
    str2 = ''.join(j for j in newlist)
    return str2
# example
# compound1 = '6000Al3001C6H6O12N12(100)'
# Al₃₀₀₁C₆H₆N₁₂O₁₂
# # compound1 = 'CCCCHHHHCCCOOONNN'
# rule1 = {"Al": 0, "C": 1, "H": 2, "N": 3, "O": 4}
# print(list_compound(compound1, rule1))

# 将分子式中数字转为<sub></sub>，用于生成图片legend下标。
def compound2sub(my_string):
# 使用正则表达式提取数学运算符和数字
    string = re.findall(r'[a-zA-Z]+', my_string)
    numbers = re.findall(r'\d+', my_string)
    # 匹配替换字符串中多组数字为<sub>num</sub>形式
    result = []
    if len(string) - len(numbers) == 0:
        for i in range(len(string)):
            result.append(f"{string[i]}<sub>{numbers[i]}</sub>")
    elif len(string) - len(numbers) == 1:
        for n, i in enumerate(range(len(string))):
            if n < len(string)-1:
                result.append(f"{string[i]}<sub>{numbers[i]}</sub>")
            else:
                result.append(f"{string[i]}")
    # 拼接替换后的结果
    result_str = ''.join(result)
    return result_str
# 示例字符串
# str1 = "C10Al100N200C300"
# print(compound2sub(str1))

# 注意：list_react和list_reac_nosub只处理list数据。
# 定义反应式排序和下标函数
def list_react(list1, rule):
    list2 = []
    for k in list1:
        processed_items = []
        for j in k.split(' '):
            if j not in ['->', '+', ',']:
                processed_item = numsting(j) + list_compound(j, rule) + stringnum(j)
                processed_items.append(processed_item)
            else:
                processed_items.append(j)
        list2.append(' '.join(processed_items))
    return list2
def list_react_nosub(list1, rule):
    list2 = []
    for k in list1:
        processed_items = []
        for j in k.split(' '):
            if j not in ['->', '+', ',']:
                processed_item = numsting(j) + list_compound_nosub(j, rule) + stringnum(j)
                processed_items.append(processed_item)
            else:
                processed_items.append(j)
        list2.append(' '.join(processed_items))
    return list2
def list_react2sub(list1, rule):
    list2 = []
    for k in list1:
        processed_items = []
        for j in k.split(' '):
            if j not in ['->', '+', ',']:
                processed_item = numsting(j) + compound2sub(list_compound_nosub(j, rule)) + stringnum(j)
                processed_items.append(processed_item)
            else:
                processed_items.append(j)
        list2.append(' '.join(processed_items))
    return list2
# example
# reaction = ['C3H6O6N6 -> C3H6O2N4 + 2O2N', '1C3H6O6N6(0) -> 2C3H6O4N5(1) + 3O2N(2)']
# reaction = ['C3H6O6N6 -> C3H6O2N4 + 2O2N', ]
# reaction = 'C3H6O6N6 -> C3H6O2N4 + 2O2N'
# rule = {'C':0,'H':1,'N':2,'O':3}
# print(list_react2sub([reaction],rule)[0]) 

# 根据list2子集在list1二级子集情况，建立与list1相同格式list。
# 用途根据bonds文件成键情况，提取反应物和生成物中原子的成键情况。
def bondid_extract(list1,list2):
    # print('time00:'+time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
    newlist =[]     # 注意newlist需建立与list1对应子list结构。
    for i in range(len(list1)):
        newlist.append([]) 
        for j in range(len(list1[i])):
            newlist[i].append([])
            for k in list2:
                if set(k) < set(list1[i][j]):
                    newlist[i][j].append(k)
    return newlist
# example
# print(bondid_extract(reactid,idbondlist))

# 定义list拆分函数，用于Bondsdata和Dumpdata拆分。
# 生成一个包含子list的list。
def split_frame(list0, splitn):
    chunks = [list0[i:i+splitn] for i in range(0, len(list0), splitn)]
    return chunks
# list1 = [1000,3000,5000,7000,9000,11000]
# splitn = 5
# print(split_frame(list1, splitn))
    
# @2024/9/10：打开文件时自动匹配编码
def autocode0(path, readtype, head=0, sheetset=0, sepset = None):
    with open(path,'rb') as f:
        result = chardet.detect(f.read(5000))
    if readtype == 'pandas':
        if path.split('.')[-1] =='csv':
            if head == '': head=None
            try: df1 = pd.read_csv(path, header=head, sep=sepset, encoding='utf-8-sig', engine='python')
            except:df1 = pd.read_csv(path, header=head, sep=sepset, encoding='gbk', engine='python')
            else:df1 = pd.read_csv(path, header=head, sep=sepset, encoding=result['encoding'], engine='python')
        elif path.split('.')[-1] =='xlsx':
            if sheetset == 0: df1 = pd.read_excel(path, header=head)
            else:df1 = pd.read_excel(path, sheetname=sheetset, header=head)
        return df1
    elif readtype == 'lines':
        openf = open(path, "r", encoding=result['encoding'])
        lines = openf.read().splitlines()
        return lines
    elif readtype == 'read':
        openf = open(path, "r", encoding=result['encoding'])
        read = openf.read()
        return read
def autocode(path, readtype, head=0, sheetset=0, sepset=None):
    # 检测文件编码
    with open(path, 'rb') as f:
        result = chardet.detect(f.read(5000))
    if readtype == 'pandas':
        if path.split('.')[-1] == 'csv':
            if head == '': head = None
            # 定义要尝试的编码列表
            encodings = ['utf-8-sig', result['encoding']]
            # 尝试不同的编码读取文件
            for encoding in encodings:
                try:
                    if sepset:
                        df1 = pd.read_csv(path, header=head, sep=sepset, encoding=encoding, engine='python')
                    else:
                        df1 = pd.read_csv(path, header=head, encoding=encoding, engine='python')
                    break  # 如果成功读取，跳出循环
                except UnicodeDecodeError:
                    continue  # 如果失败，尝试下一个编码
                except Exception as e:
                    print(f"# Warning: Error reading file: {str(e)}")
                    raise
        elif path.split('.')[-1] == 'xlsx':
            if sheetset == 0:
                df1 = pd.read_excel(path, header=head)
            else:
                df1 = pd.read_excel(path, sheet_name=sheetset, header=head)
        return df1
    elif readtype == 'lines':
        with open(path, "r", encoding=result['encoding']) as f:
            lines = f.read().splitlines()
        return lines
    elif readtype == 'read':
        with open(path, "r", encoding=result['encoding']) as f:
            content = f.read()
        return content

# example
# df1 = autocode(path1, 'pandas')
    
#------------------Arrange模块和函数 ----------------#
# 计算分子量函数，调用type_atom函数
# @2024/12/26：增加识别下标数字。
def molecular_weight(formula):
    # 转换下标数字为普通数字
    subscript_map = {
        '₀': '0', '₁': '1', '₂': '2', '₃': '3', '₄': '4',
        '₅': '5', '₆': '6', '₇': '7', '₈': '8', '₉': '9'}
    # 替换下标数字
    for sub, num in subscript_map.items():
        formula = formula.replace(sub, num)
    # 从分子式中拆分元素名和数字
    elements = re.findall('([A-Z][a-z]*)(\d*)', formula)
    # 计算所有原子的摩尔质量并计算总分子量
    total_weight = 0
    for element, count in elements:
        weight = int(type_atom(element))
        if count:
            total_weight += float(count) * weight
        else:
            total_weight += weight
    return int(total_weight)
# example
# formula = 'C₃H₆N₆O₆'
# print(molecular_weight(formula))

# 定义从dump文件读取cell信息
def dump_cell(dumplines):
    framelist,celllist = [],[]                               # 提取轨迹数
    for i in range(len(dumplines)):
        if 'ITEM: TIMESTEP' in dumplines[i]:
            framelist += [int(dumplines[i+1].strip())]
        if 'ITEM: BOX BOUNDS'  in dumplines[i]:
            items = dumplines[i].split('ITEM: BOX BOUNDS')[1].split()
            if len(items) == 3:
                a = float(dumplines[i+1].split()[1]) - float(dumplines[i+1].split()[0])
                b = float(dumplines[i+2].split()[1]) - float(dumplines[i+2].split()[0])
                c = float(dumplines[i+3].split()[1]) - float(dumplines[i+3].split()[0])
                a0, b0, c0 = float(dumplines[i+1].split()[0]), float(dumplines[i+2].split()[0]), float(dumplines[i+3].split()[0])
                xy = xz = yz =0
                # @2024/6/17：xyz三个方向周期性
                px,py,pz = items[0],items[1],items[2]
            elif len(items) == 6:
                xy = float(dumplines[i+1].split()[2])
                xz = float(dumplines[i+2].split()[2])
                yz = float(dumplines[i+3].split()[2])
                a0 = float(dumplines[i+1].split()[0]) - min(0.0,xy,xz,xy+xz)
                b0 = float(dumplines[i+2].split()[0]) - min(0.0,yz)
                c0 = float(dumplines[i+3].split()[0])
                a = float(dumplines[i+1].split()[1]) - float(dumplines[i+1].split()[0]) - max(0.0,xy,xz,xy+xz) + min(0.0,xy,xz,xy+xz)
                b = float(dumplines[i+2].split()[1]) - float(dumplines[i+2].split()[0]) - max(0.0,yz) + min(0.0,yz)
                c = float(dumplines[i+3].split()[1]) - float(dumplines[i+3].split()[0])
                # @2024/6/17：xyz三个方向周期性
                px,py,pz = items[3],items[4],items[5]
            celllist += [[a,b,c,a0,b0,c0,xy,xz,yz,px,py,pz]]        
    dfcell = pd.DataFrame(celllist, columns=['a','b','c','a0','b0','c0','xy','xz','yz','px','py','pz'])
    dfcell.insert(0, 'frame',framelist)
    return dfcell
# example
# dumpfile = input('请拖入dump.trj文件：')
# dumpf = open(dumpfile, "r", encoding='utf-8')
# dumplines = dumpf.read().splitlines()
# dfcell = dump_cell(dumplines)
# print(dfcell)

#------------------Mapping模块和函数（可自定义） ----------------#
def open_file(path):
    if not os.path.isfile(path):
        print(f"file {path} is not exist.")
        return
    if platform.system().lower() == 'linux':
        try: subprocess.run(['xdg-open', path])
        except Exception as e: print(f"Cannot open file {path}: {e}")
    elif platform.system().lower() == 'windows':
        try: os.startfile(path)
        except Exception as e: print(f"Cannot open file{path}:{e}")
    else:
        print("System not supported.")
def fitting(dftarget,a,b,fitmethod,arg1,arg2=None):              # 定义拟合方法，用于['dump']
    if fitmethod=='polyfit':                                # 定义np.polyfit 多元拟合方法       
        # 拟合数据 np.polyfit(x,y,n)
        n = arg1
        coef = np.polyfit(dftarget[a],dftarget[b], n)
        polyfit = np.poly1d(coef)                          # 拟合函数a+bx，a=polyfit[0],b=polyfit[1]
        # 拟合度计算r2_score(y,polyfit(x)) 
        R_square = r2_score(dftarget[b], polyfit(dftarget[a]))                      # 拟合度计算r2 
        return pd.concat([dftarget.reset_index(),pd.DataFrame({'polyfit'+b:polyfit(dftarget[a])})],axis=1),polyfit,R_square
    if fitmethod=='lowess':               # 定义lowess非多项式拟合方法，用于各模块     
        # 算法的工作原理：假设输入数据有 N 个点，根据 x 值将 frac*N 最接近点取 （x_i，y_i） 并使用加权线性回归估计y_i，从而估计平滑y_i。（x_j，y_j）的权重是应用于abs（x_i-x_j）的三立方函数。
        f = arg1; i = arg2
        # f 使用多少比例的数据来拟合曲线(0~1, 值越大平滑的力度越大)
        # i 要执行的基于残差的重新加权数，默认0。
        lowessy = lowess(dftarget[b], dftarget[a], frac = f, it = i)[:,1]      # lowessy格式为nparray。
        dflowess = pd.DataFrame(lowessy)
        dflowess.columns = ['lowess'+ b]
        return pd.concat([dftarget,dflowess],axis=1)

# def smooth(data, sm=1):
#     # 使用numpy的convolve函数进行卷积操作，实现滑动窗口平均。
#     # sm表示滑动窗口大小
#     if sm <= 1:
#         return data  # 如果sm小于等于1，直接返回原数据
#     else: 
#         # 计算平滑后的数据。mode='valid'确保卷积操作只在窗口完全覆盖数据时进行。
#         smooth_data = np.convolve(data, np.ones(sm)/sm, mode='valid')
#         # 为了保持数组长度不变，前后各补充(sm-1)//2个数据
#         pad_left = np.full((sm-1)//2, data[0])
#         pad_right = np.full((sm-1)//2, data[-1])
#         # 如果sm为偶数，需要再补充一个数据点
#         if sm % 2 == 0:
#             pad_right = np.append(pad_right, data[-1])
#         smooth_data = np.concatenate([pad_left, smooth_data, pad_right])
#         return list(smooth_data)



#%%
#------------------Modify模块和函数 ----------------#
# 定义filter模式atomid栏函数。
# @2023.9.5 定义函数
# @2025/4/24:修正代码
def atomidfilter(df1, type, value, filetype):
    if value !="":
        dfatomid = pd.DataFrame()
        if type == 'range':
            for i in eval(value):
                if len(i) !=0:
                    if filetype == 'ReacSpace':
                        df0 = df1[df1['idlist'].apply(lambda x: any(set(eval(x)).intersection(set(range(i[0],i[1])))))].reset_index(drop=True)
                    elif filetype == 'Dump':
                        df0 = df1[(df1['id']>= i[0])&(df1['id'] <= i[1])]
                    dfatomid = pd.concat([dfatomid,df0],axis=0).reset_index(drop=True)
        elif type == 'list':
            for i in eval(value):
                if len(i) !=0:
                    if filetype == 'ReacSpace':
                        df0 = df1[df1['idlist'].apply(lambda x: any(set(eval(x)).intersection(set(i))))].reset_index(drop=True)
                    elif filetype == 'Dump':
                        df0 = df1[(df1['id'].isin(i))]                    
                    dfatomid = pd.concat([dfatomid,df0],axis=0).reset_index(drop=True)
        elif type == 'math':
            for i in eval(value):
                if len(i) !=0:
                    if len(i) ==1:
                        # 使用正则表达式提取数学运算符和数字
                        operator = re.findall(r'[<>=]+', i)[0]
                        number = int(re.findall(r'\d+', i)[0])
                        if filetype == 'ReacSpace':
                            # df0 = df1[eval('df["idlist"]{0}{1}'.format(operator, number))].reset_index(drop=True)  有误，修改如下@2023.9.5
                            df0 = df1[eval('df1["idlist"].apply(lambda x: any(i {0}{1} for i in x))'.format(operator, number))].reset_index(drop=True)
                        elif filetype == 'Dump':
                            df0 = df1[eval('df1["id"].apply(lambda x: x {0}{1})'.format(operator, number))].reset_index(drop=True)
                        dfatomid = pd.concat([dfatomid,df0],axis=0).reset_index(drop=True)
                    elif len(i)==2:
                        operator1 = re.findall(r'[<>=]+', i[0])[0]
                        number1 = int(re.findall(r'\d+', i[0])[0])
                        operator2 = re.findall(r'[<>=]+', i[1])[0]
                        number2 = int(re.findall(r'\d+', i[1])[0])
                        cond1 = lambda x: any(eval('{0}{1}{2}'.format(i, operator1, number1)) for i in eval(x))
                        cond2 = lambda x: any(eval('{0}{1}{2}'.format(i, operator2, number2)) for i in eval(x))
                        if filetype == 'ReacSpace':
                            df0 = df1[df1["idlist"].apply(cond1) & df1["idlist"].apply(cond2)].reset_index(drop=True)
                        elif filetype == 'Dump':
                            df0 = df1[eval('df1["id"].apply(lambda x: (x{0}{1}) & (x{2}{3}))'.format(operator1, number1, operator2, number2))].reset_index(drop=True)
                        dfatomid = pd.concat([dfatomid,df0],axis=0).reset_index(drop=True)
        elif type == 'ReacSpecies':
            if len(eval(value)) != 0:
                speciesidlist = [item for sublist in df1['idlist'] for item in eval(sublist)]
                if filetype != 'Dump':
                    print('Error: the ReacSpeceis atomid filter mode is suitable for Dump file right now!')
                elif filetype == 'Dump':
                    df0 = df1[df1['id'].isin(speciesidlist)]
                dfatomid = df0
        return dfatomid
    else:
        return df1
# 定义filter模式xyzrange栏函数。
# @2023.9.5 定义函数
# @2025/4/2: add dump type check.
# @2025/4/6: repair xyzrange filter function.
def xyzrangefilter(df1, xrange, yrange, zrange, filetype):
    if filetype == 'Dump':
        dumpitems =['x','xu','y','yu','z','zu','q','vx','vy','vz']
        for i in df1.columns.tolist():
            if i in dumpitems:
                df1[i] = df1[i].astype(float)
    if xrange != '':
        dfxrange = pd.DataFrame()
        for i in eval(xrange):
            if len(i) !=0:
                if filetype == 'ReacSpace':
                    df0 = df1[~df1['xrange'].apply(lambda x: eval(x)[1] < i[0] or eval(x)[0] > i[1])].reset_index(drop=True)
                elif filetype == 'Dump':
                    for j in df1.columns:
                        if j in ['x','xu']:   # xs为归一化坐标不用，下同。
                            df0 = df1[df1[j].between(i[0],i[1])]
                dfxrange = pd.concat([dfxrange,df0],axis=0).reset_index(drop=True)
        if dfxrange.empty:
            print("Warning: {} data is empty in the xrange of {}!".format(filetype, xrange))
    else:dfxrange = df1
    if yrange != '':
        dfyrange = pd.DataFrame()
        for i in eval(yrange):
            if len(i) !=0:
                if filetype == 'ReacSpace':
                    df0 = dfxrange[~dfxrange['yrange'].apply(lambda x: eval(x)[1] < i[0] or eval(x)[0] > i[1])].reset_index(drop=True)
                elif filetype == 'Dump':
                    for j in df1.columns:
                        if j in ['y','yu']:
                            df0 = dfxrange[dfxrange[j].between(i[0],i[1])]
                dfyrange = pd.concat([dfyrange,df0],axis=0).reset_index(drop=True)
        if dfyrange.empty:
            print("Warning: {} data is empty in the yrange of {}!".format(filetype, yrange))
    else:dfyrange = dfxrange
    if zrange != '':
        dfzrange = pd.DataFrame()
        for i in eval(zrange):
            if len(i) !=0:
                if filetype == 'ReacSpace':
                    df0 = dfyrange[~dfyrange['zrange'].apply(lambda x: eval(x)[1] < i[0] or eval(x)[0] > i[1])].reset_index(drop=True)
                elif filetype == 'Dump':
                    for j in df1.columns:
                        if j in ['z','zu']:
                            df0 = dfyrange[dfyrange[j].between(i[0],i[1])]              
                dfzrange = pd.concat([dfzrange,df0],axis=0).reset_index(drop=True)
        if dfzrange.empty:
            print("Warning: {} data is empty in the zrange of {}!".format(filetype, zrange))
    else:dfzrange = dfyrange
    return dfzrange

# 定义filter模式xyzposition栏函数。
# @2023.9.5 定义函数
def xyzposfilter(df1, xyztype, xyzunit, xyzvalue, filetype):
    if xyztype != "":
        if xyztype == "center,r":
            if (xyzunit!="")&(xyzvalue!=""):
                center = eval(xyzunit)
                try:
                    r = float(xyzvalue)
                    if filetype == 'ReacSpecies':
                        points = df1[['x', 'y', 'z']].to_numpy()
                    elif filetype == 'Dump':
                        for j in [['x','y','z'], ['xu','yu','zu']]:
                            if set(j).issubset(df1.columns):
                                points = df1[j].to_numpy()
                    # 计算每个点到中心点的距离
                    distances = np.linalg.norm(points - center, axis=1)
                    # 筛选符合要求的点
                    dfxyz = df1[distances <= r].reset_index(drop=True)
                    if dfxyz.empty: print("Error: {} data is empty in the set of 'center,r'!".format(filetype))
                except:
                    print('Error: please set r value to filter!')
        elif xyztype == "center,r1,r2":
            if (xyzunit!="")&(xyzvalue!=""):
                center = eval(xyzunit)
                try:
                    r1 = eval(xyzvalue)[0]
                    r2 = eval(xyzvalue)[1]
                    # 将数据框转换为NumPy数组
                    if filetype == 'ReacSpecies':
                        points = df1[['x', 'y', 'z']].to_numpy()
                    elif filetype == 'Dump':
                        for j in [['x','y','z'], ['xu','yu','zu']]:
                            if set(j).issubset(df1.columns):
                                points = df1[j].to_numpy()
                    # 计算每个点到中心点的距离平方
                    distances_squared = np.sum((points - center) ** 2, axis=1)
                    # 根据半径r1和r2筛选符合要求的点
                    mask = (distances_squared >= r1**2) & (distances_squared <= r2**2)
                    dfxyz = df1[mask].reset_index(drop=True)
                    if dfxyz.empty: print("Error: {} data is empty in the set of 'center,r1,r2'!".format(filetype))
                except:
                    print('Error: please set r1 and r2 values to filter!')
    else: dfxyz = df1
    # dfxyz['frame'] = dfxyz['frame'].astype(int)
    # dfxyz['time'] = dfxyz['time'].astype(float)
    return dfxyz

# @2025/5/20：add calcuation for trj file.
def calcuate_trj(file_path, frames, type0='trj', frametype='list', cutoff=5.0, filterneighbor=2):
    if type0 == 'trj':
        with open(file_path, "r") as f: lines = f.read().splitlines()
        columnlist = [lines[8].split()[2:] if 'ITEM: ATOMS' in lines[8] else None][0]
        framedict = {int(lines[i+1]):i+1 for i, line in enumerate(lines) if line.startswith("ITEM: TIMESTEP")}
        if frames and frames != '':
            framelist = []
            if frametype == 'list':
                if isinstance(frames,list):
                    framelist = [frame for frame in frames if frame in framedict.keys()]
            elif frametype == 'range':
                if len(frames) == 2:
                    framelist = [frame for frame in framedict.keys() if frames[0]<=frame<=frames[1]]
            elif frametype == 'int':
                if isinstance(frames,int):
                    framelist = [frame for frame in framedict.keys() if frame == frames]
            # else: print("# Warning: filter setting is not supported, please check it!")
        else:
            framelist = [int(lines[i+1]) for i, line in enumerate(lines) if line.startswith("ITEM: TIMESTEP")]
        contentall = ''
        if len(framelist) >0: 
            for frame in framelist:  # 假设第9行开始是原子数据
                frameline = framedict[frame]
                atoms = int(lines[frameline+2])
                data = np.array([line.split() for line in lines[frameline+8:frameline+8+atoms]], dtype='U')
                dfdump = pd.DataFrame(data, columns=columnlist)                
                if set(['x','y','z']).issubset(set(columnlist)): 
                    xyzset = ['x','y','z']
                elif set(['xu','yu','zu']).issubset(set(columnlist)):
                    xyzset = ['xu','yu','zu']
                else:
                    xyzset = []
                    print("# Warning: x,y,z columns not found, please check it!")
                if len(xyzset) > 0:
                    dfdump[xyzset] = dfdump[xyzset].astype(float)
                    positions = dfdump[xyzset].values
                    tree = cKDTree(positions)  # , boxsize=box_size（考虑周期性边界）
                    neighbor_counts = tree.query_ball_point(positions, r=cutoff, return_length=True)
                    dfdump['neighbor'] = neighbor_counts
                    if filterneighbor != '' and filterneighbor > 0:
                        dfdump = dfdump[dfdump['neighbor']>=filterneighbor]
                    content = '\n'.join(lines[frameline-1:frameline+2])+'\n{}\n'.format(len(dfdump))+'\n'.join(lines[frameline+3:frameline+7])
                    contentall += content + '\n' + lines[8]+ ' neighbor' + '\n' + dfdump.to_string(index=False, header=False) + '\n'
        return contentall
    elif type0 == 'csv':
        # dfdump0 = pd.read_csv(file_path)
        dfdump0 = file_path
        framelist0 = dfdump0['frame'].unique()
        if frames and frames != '':
            framelist = []
            if (frametype == 'list') & isinstance(frames,list):
                framelist = [frame for frame in frames if frame in framelist0]
            elif (frametype == 'range') & (len(frames) == 2):
                framelist = [frame for frame in framelist0 if frames[0]<=frame<=frames[1]]
            elif (frametype == 'int' ) & isinstance(frames, int):
                framelist = [frame if frames in framelist0 else None]
            else: print("# Warning: filter setting is not supported, please check it!")
        else: framelist = framelist0
        if len(framelist) >0:
            dfdumpall = pd.DataFrame()
            for frame in framelist:
                dfdump = dfdump0[dfdump0['frame'] == frame].copy()
                positions = dfdump[['x', 'y', 'z']].values
                tree = cKDTree(positions)
                neighbor_counts = tree.query_ball_point(positions, r=cutoff, return_length=True)
                dfdump['neighbor'] = neighbor_counts
                if filterneighbor != '' and filterneighbor > 0:
                    dfdump = dfdump[dfdump['neighbor']>=filterneighbor]
                dfdumpall = pd.concat([dfdumpall, dfdump], ignore_index=True)
        return dfdumpall
# example for trj
# path = "F:\\rensu\\three\\try\\45\\9\\modify\\dump.wave.trj"
# content = calcuate_trj(path, None, 'csv','int', 5.0, 3)
# with open("F:\\rensu\\three\\try\\45\\9\\modify\\dump3.wave.trj", "w") as f:
#     f.write(content)
# example for csv
# path = "F:\\rensu\\three\\try\\45\\9\\modify\\dataofdump.csv"
# content = calcuate_trj(path, None, 'csv','', 5.0, 3)
# content.to_csv("F:\\rensu\\three\\try\\45\\9\\modify\\dataofdump.wave3.csv", index=False)

#------------------ReacSpace模块和函数 ----------------#
# 根据两个list的多个子list中元素相关性，对子list分类。
# 程序1：仅输出一个列表，list=[[反应1所有分子],[反应2所有分子],...]，具体结果可以使用 print(fun3(list1,list2)) 查看
# 程序1使用时仅需调用fun3即可
    #print(fun3(list1,list2))
# 程序2：输出两个列表，list1=[[反应1反应物],[反应2反应物],...]，list2=[[反应1生成物],[反应2生成物],...]，具体结果可以使用
    #a=fun3(list1,list2)
    #list1=fun4(list1,a)
    #list2=fun4(list2,a)
    #print(list1),print(list2)
# 定义函数reacsplit调研程序2，使用方法：
    # list1 = [[70, 73, 74], [81, 66, 67, 82], [22, 23, 24, 25, 26, 27, 29, 30, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42]]
    # list2 = [[35, 36, 41, 42, 26, 27, 30], [66, 67, 70, 73, 74, 81, 82], [33, 34, 37, 38, 39, 40, 22, 23, 24, 25, 29]]
    # list1,list2=reacsplit(list1,list2)
def reacsplit(list1,list2):
    def fun2(list1,list2):                   # fun2用于将原列表中fun1已输出分子踢掉。
        list3=[]
        m=0
        for k in list2:
                for i in list1:
                    if k not in i:
                        m+=1    
                if m==len(list1):
                    list3.append(k)
                m=0
        return list3 
    def fun1(list1,list2,list4):             # fun1用于输出一个化学反应。
        list3=[]
        for i in range(len(list1)):
            a=list1[i]
            for j in range(len(list2)):
                b=list2[j]
                if list3 == []: 
                    if list(set(a) & set(b))!=[]  :
                        list3.append(b)
                        list3.append(a)
                else:
                    for k in range(len(list3)):
                        c=list3[k]
                        if list(set(a) & set(c))!=[]  and a not in list3:
                            list3.append(a)
                        elif list(set(c) & set(b))!=[]  and b not in list3:
                            list3.append(b)
        if list3 not in list4 and list3!=[]:
            list4.append(list3)
        return list4
    def fun3(list1,list2):                    # fun3用于循环fun1与fun2直至输出完所有化学反应。
        list3=[]
        for i in range(100):
            a=list1
            list3=fun1(list1,list2,list3)
            list1=fun2(list3,list1)
            if a==list1:
                break
        return list3
    def fun4(list1,list2):               #fun4用于根据fun3结果将不同化学反应的反应物与生成物分类，若想单独使用fun4,只需将fun3嵌套进fun4即可,
        list3=[]                          #或者想达到相同效果，只需单独使用fun2与fun1,并循环fun2将结果放入一个列表即可。
        for i in list2:
            list4=[]
            for j in list1:
                if j in i:
                    list4.append(j)
            list3.append(list4)
        return list3
    a=fun3(list1,list2)
    list1=fun4(list1,a)
    list2=fun4(list2,a)
    return list1,list2

# 检查是否为空、NaN 或空字符串
# @2024/9/18：对空字符串识别不了
def empty_or_nan(value):
    if value is None: return True
    if isinstance(value, float) and np.isnan(value):
        return True
    if isinstance(value, str) and value.strip() == "":
        return True  # 识别空字符串（包括只包含空格的字符串）
    return False

# 定义时间范围筛选函数。
# @2024/3/5：将eval步骤改为value判断之后，避免eval('')报错。
def timerange(df, format, unit, value):
    if value != "":
        df1 = pd.DataFrame()                    # 建立空pandas列表。
        for i in eval(value):
            if (len(i) != 0) & (format == "range"):
                if len(i) == 2:
                    if unit == "frames":
                        df0 = df[df['frame'].between(i[0],i[1])]
                    elif unit == "time(ps)":
                        df0 = df[df['time'].between(i[0],i[1])]
                else:
                    print("# Error: please set the correct format of time range!")
            elif (len(i) != 0) & (format == "list"):
                if unit == "frames":
                    df0 = df[df['frame'].isin(i)]
                elif unit == "time(ps)":
                    df0 = df[df['time'].isin(i)]
            elif (len(i) != 0) & (format == "math"):
                if len(i) ==1:
                    # 使用正则表达式提取数学运算符和数字
                    operator = re.findall(r'[<>=]+', i)[0]
                    number = int(re.findall(r'\d+', i)[0])
                    if unit == "frames":
                        df0 = df[eval('df["frame"]{0}{1}'.format(operator, number))]
                    elif unit == "time(ps)":
                        df0 = df[eval('df["time"]{0}{1}'.format(operator, number))]
                elif len(i)==2:
                    operator1 = re.findall(r'[<>=]+', i[0])[0]
                    number1 = int(re.findall(r'\d+', i[0])[0])
                    operator2 = re.findall(r'[<>=]+', i[1])[0]
                    number2 = int(re.findall(r'\d+', i[1])[0])
                    cond1 = lambda x: any(eval('{0}{1}{2}'.format(i, operator1, number1)) for i in eval(x))
                    cond2 = lambda x: any(eval('{0}{1}{2}'.format(i, operator2, number2)) for i in eval(x))
                    if unit == "frames":
                        df0 = df[df['frame'].apply(cond1) & df['frame'].apply(cond2)]
                    elif unit == "time(ps)":
                        df0 = df[df['time'].apply(cond1) & df['time'].apply(cond2)]
                elif len(i)>2:
                    print("# Error: the math unit don't support condition >2!")
            df1 = pd.concat([df1,df0],axis=0)
    else:df1 = df
    return df1.reset_index(drop=True)
# smile or rxn to svg
def drawmol(smile,type):
    if type == 'smile':
        mol = Chem.MolFromSmiles(smile)
        if mol is not None:
            # return Draw.MolToImage(mol)
            d = Draw.MolDraw2DSVG(300, 300)
            d.DrawMolecule(mol) 
            d.FinishDrawing()  
            svg = d.GetDrawingText()
            return svg
    elif type == 'rxn':
        react2view(smile)
# smi = 'C1N(CN(CN1N(=O)=O)N(=O)=O)N(=O)=O'
# intype = 'smile'
# img = drawmol(smi,intype)
# print(img)

# 标准化SMILES字符串，来源网络@2024/8/27
def smile_std(smiles0, smilimit=500):
    try:
        mol0 = Chem.MolFromSmiles(smiles0)
        if mol0 is None: return smiles0
        if mol0.GetNumAtoms() < smilimit:
            AllChem.Compute2DCoords(mol0)
            smiles0 = Chem.MolToSmiles(mol0, canonical=True)
            try: Chem.SanitizeMol(mol0, sanitizeOps=Chem.SANITIZE_ALL)  # 标准化分子，^排除该选项。 ^Chem.SANITIZE_ADJUSTHS
            except: pass
        else: pass
    except: pass
    return smiles0
# smilist = ['N(=O)[O]','C1N(C[N]C[N]1)N(=O)=O','C1[N]CN(C[N]1)N(=O)=O','[C@H]12[C@@H]3N([C@@H]4[C@H](N1N(=O)=O)N([C@H]([C@@H](N3N(=O)=O)N2N(=O)=O)N4N(=O)=O)N(=O)=O)N(OON(N1[C@H]2[C@H]3N([C@H]4[C@@H]1N([C@@H]([C@H](N3N(=O)=O)N2N(=O)=O)N4N(=O)=O)N(=O)=O)N(=O)=O)[O])[O]']
# for i in smilist:
#     print(smile_std(i))


# 合并pandas函数 @2024/9/23。
# @2024/12/19：修正简化代码。
def filterconcat(df1, df2):
    if not df1.empty and not df2.empty:
        df = pd.concat([df1, df2]).drop_duplicates(keep='first')
    elif not df1.empty:
        df = df1
    elif not df2.empty:
        df = df2
    else:
        df = pd.DataFrame()
    return df.sort_values(by='frame', ascending=True)

#------------------package模块和函数 ----------------#
# 将分子中所有化学键包含原子编号从1开始排序
def reset_bondid(idbondlist):
    all_numbers = [num for sublist in idbondlist for num in sublist]
    # 排序并获取唯一的数字
    unique_numbers = sorted(set(all_numbers))
    # 创建数字到连续数字的映射
    number_mapping = {num: i+1 for i, num in enumerate(unique_numbers)}
    # 修改子列表中的数字
    reset_idbondlist = [[number_mapping[num] for num in sublist] for sublist in idbondlist]
    return reset_idbondlist
# example
# idbondlist = [[27, 30], [41, 26], [24, 39], [34, 29], [26, 42], [22, 23], [33, 29], [27, 22], [24, 25], [35, 30], [25, 29], [24, 23], [36, 30], [26, 27], [37, 22], [24, 40], [28, 31], [25, 26], [38, 22], [32, 28], [28, 23]]
# print(reset_bondid(idbondlist))
# result = [[6, 9], [20, 5], [3, 18], [13, 8], [5, 21], [1, 2], [12, 8], [6, 1], [3, 4], [14, 9], [4, 8], [3, 2], [15, 9], [5, 6], [16, 1], [3, 19], [7, 10], [4, 5], [17, 1], [11, 7], [7, 2]]

def rdkit_convert(
    input_data: Union[str, bytes, List[str]],
    input_format: str,
    output_format: str,
    **kwargs) -> Union[str, bytes, List[Tuple[str, bool]]]:
    """
    RDKit 分子/反应格式转换函数
    参数:
        input_data: 输入数据（SMILES/RSMI/SDF/RXN 等字符串或列表）
        input_format: 输入格式（'smiles', 'rsmi', 'sdf', 'mol', 'inchi', 'inchikey','fasta', 'pdb', 'rxn'）
        output_format: 输出格式（'smiles', 'sdf', 'mol', 'inchi', 'inchikey', 'png', 'svg', '3d'）
        kwargs: 额外参数（图像尺寸、是否显示原子编号等）
    返回:
        转换后的数据（字符串/字节流），或带状态的列表 [(result, success)]
    """
    # 支持的所有格式
    SUPPORTED_INPUTS = {'smiles', 'rsmi', 'sdf', 'mol', 'inchi', 'inchikey', 'fasta', 'pdb', 'rxn'}
    SUPPORTED_OUTPUTS = {'smiles', 'sdf', 'mol', 'inchi', 'inchikey', 'png', 'svg', '3d'}
    # 检查格式合法性
    if input_format.lower() not in SUPPORTED_INPUTS:
        raise ValueError(f"Unsupported input format: {input_format}. Choose from: {SUPPORTED_INPUTS}")
    if output_format.lower() not in SUPPORTED_OUTPUTS:
        raise ValueError(f"Unsupported output format: {output_format}. Choose from: {SUPPORTED_OUTPUTS}")
    # 批量处理模式
    # print(input_data, type(input_data))
    if isinstance(input_data, list):
        results = []
        for item in input_data:
            try:
                result = convert_single_input(item, input_format, output_format, **kwargs)
                results.append((result, True))
            except Exception as e:
                # print("# Warning: convert failed: " +item)
                # logger.warning(f"转换失败: {str(e)}")
                results.append((item, False))
        return results
    # 单输入处理
    else: return convert_single_input(input_data, input_format, output_format, **kwargs)
def rsmi_rxn(rsmi):
    reactants_part, products_part = rsmi.split(">>")
    reactant_mols = [Chem.MolFromSmiles(smi) for smi in reactants_part.split('.') if smi.strip()]
    product_mols = [Chem.MolFromSmiles(smi) for smi in products_part.split('.') if smi.strip()]
    """合并相同分子并统计数量，返回 (去重分子列表, 数量统计)"""
    # 用SMILES作为唯一标识（相同结构视为同一分子）
    def merge_duplicate(mols):
        smi_counter = Counter()
        mol_dict = {}
        for mol in mols:
            if mol is None: continue
            smi = Chem.MolToSmiles(mol)
            smi_counter[smi] += 1
            if smi not in mol_dict:
                mol_dict[smi] = mol
        unique_mols = list(mol_dict.values())
        counts = [smi_counter[smi] for smi in mol_dict.keys()]
        return unique_mols, counts
    unique_reactants, reactant_counts = merge_duplicate(reactant_mols)
    unique_products, product_counts = merge_duplicate(product_mols)
    rxn = AllChem.ChemicalReaction()
    for mol in unique_reactants: rxn.AddReactantTemplate(mol)
    for mol in unique_products: rxn.AddProductTemplate(mol)
    return rxn, reactant_counts, product_counts
def convert_single_input(
    input_data: Union[str, bytes],
    input_format: str,
    output_format: str,
    **kwargs) -> Union[str, bytes]:
    """处理单个输入（分子或反应）"""
    # 检查是否为反应式
    if input_format == 'rsmi' and '>>' in input_data:
        return convert_reaction(input_data, 'rsmi', output_format, **kwargs)
    elif input_format == 'rxn':
        return convert_reaction(input_data, 'rxn', output_format, **kwargs)
    else:
        return convert_single_molecule(input_data, input_format, output_format, **kwargs)
def add_coefficient_annotations(image_data, reactant_counts, product_counts, width=1200, height=400):
    """
    在图像上添加系数标注。
    参数:
    image_data (str or bytes): 图像数据，SVG格式为字符串，PNG格式为字节。
    reactant_counts (list of int): 反应物的计数。
    product_counts (list of int): 产物的计数。
    width (int): 图像宽度。
    height (int): 图像高度。
    返回:
    str or bytes: 带有系数标注的图像数据。
    """
    if isinstance(image_data, str):
        # SVG格式
        insert_pos = image_data.find('</svg>')
        if insert_pos < 0: return image_data
        annotations = []
        mol_width = width / (len(reactant_counts) + len(product_counts) + 2)
        for items in [reactant_counts, product_counts]:
            for i, count in enumerate(items):
                if items == reactant_counts: x = i * mol_width + mol_width
                else: x = width * 0.6 + i * mol_width - mol_width * 0.1
                y = height * 0.95
                if count > 1:
                    annotations.append(
                        f'<text x="{x:.1f}" y="{y:.1f}" font-family="times new roman" '
                        f'font-size="25" fill="black">({count})</text>')     #  font-weight="bold"
        return image_data[:insert_pos] + '\n' + '\n'.join(annotations) + '\n' + image_data[insert_pos:]
    elif isinstance(image_data, bytes):
        # PNG格式
        img = Image.open(io.BytesIO(image_data))
        draw = ImageDraw.Draw(img)
        font_path = os.getcwd()+"\\utils\\fonts\\TimesNewRoman.ttf"  # 替换为您的字体文件路径
        font_size = 25
        font = ImageFont.truetype(font_path, font_size)
        mol_width = width / (len(reactant_counts) + len(product_counts) + 2)
        for items in [reactant_counts, product_counts]:
            for i, count in enumerate(items):
                if count > 1:
                    if items == reactant_counts: x = i * mol_width + mol_width
                    else: x = width * 0.6 + i * mol_width - mol_width * 0.1
                    y = height * 0.90
                    draw.text((x, y), f"({count})", font=font, fill="black")
        output = io.BytesIO()
        img.save(output, format="PNG")
        return output.getvalue()
    else: raise ValueError("Unsupported image data type. Expected str (SVG) or bytes (PNG).")
def convert_reaction(
    input_data: Union[str, bytes],
    input_format: str,
    output_format: str,
    **kwargs) -> bytes:
    """处理化学反应式转换为图像（PNG/SVG）,断键红色、成键绿色"""
    # 解析反应
    if input_format == 'rsmi':
        rxn, reactant_counts, product_counts = rsmi_rxn(input_data)
    elif input_format == 'rxn':
        if isinstance(input_data, bytes):
            input_data = input_data.decode('utf-8')
        rxn = AllChem.ReactionFromRxnBlock(input_data)
        reactant_counts, product_counts = [],[]
    else: raise ValueError("反应输入格式必须为 'rsmi' 或 'rxn'")
    if rxn is None:  raise ValueError("无法解析反应式（可能格式无效）")
     # 获取反应中心信息
    reacting_atoms = set()
    reacting_bonds = []
    for i in range(rxn.GetNumReactantTemplates()):
        mol = rxn.GetReactantTemplate(i)
        reacting_atoms.update(atom.GetAtomMapNum() for atom in mol.GetAtoms() if atom.GetAtomMapNum())
        reacting_bonds.extend((bond.GetBeginAtom().GetAtomMapNum(), 
                              bond.GetEndAtom().GetAtomMapNum()) 
                             for bond in mol.GetBonds() 
                             if bond.GetBeginAtom().GetAtomMapNum() and bond.GetEndAtom().GetAtomMapNum())
    # 绘制反应
    width = kwargs.get('width', 800)
    height = kwargs.get('height', 300)
    if output_format == 'png':
        drawer = MolDraw2DCairo(width, height)
    elif output_format == 'svg':
        drawer = MolDraw2DSVG(width, height)
    else:
        raise ValueError("反应式仅支持输出为 'png' 或 'svg'")
    # 设置绘图选项
    drawer.drawOptions().highlightColour = (0, 1, 0)  # 默认绿色（成键）
    drawer.DrawReaction(rxn, highlightByReactant=False)  # 先绘制基本结构
    # 单独绘制断键（红色）
    drawer.drawOptions().highlightColour = (1, 0, 0)  # 红色
    for bond in reacting_bonds:
        # 检查这个键是否在产物中不存在（即断键）
        found_in_products = False
        for i in range(rxn.GetNumProductTemplates()):
            mol = rxn.GetProductTemplate(i)
            for pbond in mol.GetBonds():
                begin_map = pbond.GetBeginAtom().GetAtomMapNum()
                end_map = pbond.GetEndAtom().GetAtomMapNum()
                if (begin_map == bond[0] and end_map == bond[1]) or (begin_map == bond[1] and end_map == bond[0]):
                    found_in_products = True
                    break
            if found_in_products:
                break
        if not found_in_products:
            # 绘制断键标记
            drawer.SetColour((1, 0, 0))
            drawer.DrawLine(bond[0], bond[1])
    drawer.FinishDrawing()
    # 处理输出
    if output_format == 'png':
        png_bytes = drawer.GetDrawingText()
        img_data = add_coefficient_annotations(png_bytes, reactant_counts, product_counts, width, height)
        return img_data
    elif output_format == 'svg':
        svg_str = drawer.GetDrawingText()
        img_data = add_coefficient_annotations(svg_str, reactant_counts, product_counts, width, height).encode('utf-8')
        return img_data
def convert_single_molecule(
    input_data: Union[str, bytes],
    input_format: str,
    output_format: str,
    **kwargs) -> Union[str, bytes]:
    """处理单个分子转换（原有逻辑）"""
    mol = None
    if input_format == 'smiles': mol = Chem.MolFromSmiles(input_data)
    elif input_format in ('sdf', 'mol'):
        if isinstance(input_data, bytes): input_data = input_data.decode('utf-8')
        mol = Chem.MolFromMolBlock(input_data)
    elif input_format == 'inchi': mol = Chem.MolFromInchi(input_data)
    elif input_format == 'inchikey': mol = Chem.MolFromInchi(Chem.inchi.InchiToInchiKey(input_data))
    elif input_format == 'fasta': mol = Chem.MolFromFASTA(input_data)
    elif input_format == 'pdb': mol = Chem.MolFromPDBBlock(input_data)
    if mol is None: raise ValueError("无法解析输入分子（可能格式无效）")
    # 预处理
    # if kwargs.get('add_hs', False): mol = Chem.AddHs(mol)
    # if kwargs.get('sanitize', True): Chem.SanitizeMol(mol)
    mol.UpdatePropertyCache(strict=False)  # 粗略估算键级
    Chem.SanitizeMol(mol, Chem.SANITIZE_PROPERTIES)
    if kwargs.get('generate_2d', False): AllChem.Compute2DCoords(mol)
    if output_format == '3d': AllChem.EmbedMolecule(mol, randomSeed=kwargs.get('random_seed', 42))
    # 转换为目标格式
    if output_format == 'smiles': return Chem.MolToSmiles(mol, **kwargs)
    elif output_format in ('sdf', 'mol'): return Chem.MolToMolBlock(mol, **kwargs)
    elif output_format == 'inchi': return Chem.MolToInchi(mol, **kwargs)
    elif output_format == 'inchikey': return Chem.MolToInchiKey(mol, **kwargs)
    elif output_format == 'png':
        drawer = MolDraw2DCairo(kwargs.get('width', 300), kwargs.get('height', 300))
        drawer.DrawMolecule(mol)
        drawer.FinishDrawing()
        return drawer.GetDrawingText()
    elif output_format == 'svg':
        drawer = MolDraw2DSVG(kwargs.get('width', 300), kwargs.get('height', 300))
        drawer.DrawMolecule(mol)
        drawer.FinishDrawing()
        return drawer.GetDrawingText().encode('utf-8')
    elif output_format == '3d': return Chem.MolToMolBlock(mol)
    else: raise ValueError("未知的输出格式请求")
# 示例1: 反应 SMILES → PNG
# rsmi = "CCO.C>>C=O"
# rsmi = 'C1N(CN(CN1N(=O)=O)N(=O)=O)N(=O)=O>>C1[N]C[N]C[N]1.N(=O)[O].N(=O)[O].N(=O)[O]'
# png_data = rdkit_convert(rsmi, 'rsmi', 'png')
# with open(os.getcwd()+"\\images\\reaction.png", "wb") as f:
#     f.write(png_data)
# 示例2: 混合批量转换
# mixed_inputs = ['N(=O)[O].N(=O)[O].N(=O)[O].[H]C1([H])NC([H])([H])NC([H])([H])N1>>[H]C1([H])N([N+](=O)[O-])C([H])([H])N([N+](=O)[O-])C([H])([H])N1[N+](=O)[O-]', 'N(=O)[O].N(=O)[O].N(=O)[O].[H]C1([H])NC([H])([H])NC([H])([H])N1>>[H]C1([H])N([N+](=O)[O-])C([H])([H])N([N+](=O)[O-])C([H])([H])N1[N+](=O)[O-]', 'N(=O)[O].N(=O)[O].N(=O)[O].[H]C1([H])NC([H])([H])NC([H])([H])N1>>[H]C1([H])N([N+](=O)[O-])C([H])([H])N([N+](=O)[O-])C([H])([H])N1[N+](=O)[O-]', 'N(=O)[O].N(=O)[O].N(=O)[O].[H]C1([H])NC([H])([H])NC([H])([H])N1>>[H]C1([H])N([N+](=O)[O-])C([H])([H])N([N+](=O)[O-])C([H])([H])N1[N+](=O)[O-]', 'N(=O)[O].N(=O)[O].N(=O)[O].[H]C1([H])NC([H])([H])NC([H])([H])N1>>[H]C1([H])N([N+](=O)[O-])C([H])([H])N([N+](=O)[O-])C([H])([H])N1[N+](=O)[O-]', 'N(=O)[O].N(=O)[O].[H]C1([H])NC([H])([H])N([N+](=O)[O-])C([H])([H])N1>>[H]C1([H])N([N+](=O)[O-])C([H])([H])N([N+](=O)[O-])C([H])([H])N1[N+](=O)[O-]', 'N(=O)[O].N(=O)[O].[H]C1([H])NC([H])([H])N([N+](=O)[O-])C([H])([H])N1>>[H]C1([H])N([N+](=O)[O-])C([H])([H])N([N+](=O)[O-])C([H])([H])N1[N+](=O)[O-]', 'N(=O)[O].N(=O)[O].[H]C1([H])NC([H])([H])N([N+](=O)[O-])C([H])([H])N1>>[H]C1([H])N([N+](=O)[O-])C([H])([H])N([N+](=O)[O-])C([H])([H])N1[N+](=O)[O-]', 'N(=O)[O].N(=O)[O].N(=O)[O].[H]C1([H])NC([H])([H])NC([H])([H])N1>>[H]C1([H])N([N+](=O)[O-])C([H])([H])N([N+](=O)[O-])C([H])([H])N1[N+](=O)[O-]', 'N(=O)[O].N(=O)[O].N(=O)[O].[H]C1([H])NC([H])([H])NC([H])([H])N1>>[H]C1([H])N([N+](=O)[O-])C([H])([H])N([N+](=O)[O-])C([H])([H])N1[N+](=O)[O-]', 'N(=O)[O].N(=O)[O].[H]C1([H])NC([H])([H])N([N+](=O)[O-])C([H])([H])N1>>[H]C1([H])N([N+](=O)[O-])C([H])([H])N([N+](=O)[O-])C([H])([H])N1[N+](=O)[O-]', 'N(=O)[O].[H]C1([H])NC([H])([H])N([N+](=O)[O-])C([H])([H])N1[N+](=O)[O-]>>[H]C1([H])N([N+](=O)[O-])C([H])([H])N([N+](=O)[O-])C([H])([H])N1[N+](=O)[O-]', 'N(=O)[O].N(=O)[O].N(=O)[O].[H]C1([H])NC([H])([H])NC([H])([H])N1>>[H]C1([H])N([N+](=O)[O-])C([H])([H])N([N+](=O)[O-])C([H])([H])N1[N+](=O)[O-]', 'N(=O)[O].N(=O)[O].[H]C1([H])NC([H])([H])N([N+](=O)[O-])C([H])([H])N1>>[H]C1([H])N([N+](=O)[O-])C([H])([H])N([N+](=O)[O-])C([H])([H])N1[N+](=O)[O-]', 'N(=O)[O].[H]C1([H])NC([H])([H])N([N+](=O)[O-])C([H])([H])N1[N+](=O)[O-]>>[H]C1([H])N([N+](=O)[O-])C([H])([H])N([N+](=O)[O-])C([H])([H])N1[N+](=O)[O-]']
# results = rdkit_convert(mixed_inputs, 'rsmi', 'png', width=1200, height=400)
# for i, (data, success) in enumerate(results):
#     if success:
#         with open(f"output_{i}.png", "wb") as f:
#             f.write(data)
#     else:
#         print(f"跳过无效输入: {mixed_inputs[i]}")



# @2023/12/31：新增函数调用openbabel转换格式。
def babelconversion(inpath: str, outpath: str, input_format="xyz", output_format="sdf", overwrite=True, parament=None) -> None:
    """
    Convert a molecular file from one format to another using Open Babel.
    Args:
        input_file (str): The path to the input file.
        output_file (str): The path to the output file.
        input_format (str, optional): The format of the input file. Defaults to "xyz".
        output_format (str, optional): The format of the output file. Defaults to "sdf".
        overwrite (bool, optional): Whether to overwrite existing files. Defaults to False.
    Raises:
        ValueError: If the input or output format is not supported by Open Babel.
        IOError: If the input file cannot be read or the output file cannot be written.
    Returns:
        None
    """
    try:
        molecules = readfile(input_format, inpath)
        # print(molecules)
    except ValueError as e:
        print(f"# Error: Error reading input file: {e}")
        return
    if not overwrite and os.path.exists(outpath):
        response = input(f"The file {outpath} already exists. Overwrite? (y/n)")
        if response.lower() != "y":
            print("Operation canceled.")
            return
        else:
            os.remove(outpath)  # 删除已有的同名文件
    try:
        outpath_writer = Outputfile(output_format, outpath, overwrite=overwrite)
    except ValueError as e:
        print(f"Error creating output file: {e}")
        return
    for n, molecule in enumerate(molecules):
        try:
            if output_format != 'png':
                outpath_writer.write(molecule)
            else:
                molecule.draw(show=False, filename = outpath.replace('.png','.{}.png'.format(n)))
        except IOError as e:
            print(f"Error writing molecule {n}: {e}")
    outpath_writer.close()
    # print(f"# Success: molecule(s) or file(s) converted!")
# @2024/1/17:新增ovito计算函数。
def calculate_msd(frame, data):
    #读取原子位移，存入到变量displacement_magnitudes
    displacement_magnitudes = data.particles['Displacement Magnitude']
    #带入公式，计算msd
    msd = np.sum(displacement_magnitudes ** 2) / len(displacement_magnitudes)
    rmsd = np.sqrt(msd)
    #以上计算结果存入到全局变量MSD中
    data.attributes["MSD"] = msd
    data.attributes["RMSD"] = rmsd
def ovitopip(dumpfile, outpath, modes, caldict, encode):
    #添加管道修饰，以轨迹文件的第一帧为基础，计算原子位移
    pipeline = import_file(dumpfile)
    pipeline.modifiers.append(CalculateDisplacementsModifier())
    # 读取轨迹数信息。
    dumplines = open(dumpfile, "r", encoding=encode).read().splitlines()
    framelist = []
    for n,i in enumerate(dumplines):
        if 'ITEM: TIMESTEP' in i:
            framelist.append(int(dumplines[n+1]))
    ovitoout = {}
    if "RDF" in modes:
        atomorder = caldict['atomorder']
        timestep = caldict['timestep']
        rdfcutoff = caldict['cutoff']
        rdfbins = caldict['bins']
        #添加rdf计算修饰命令，截断为5埃米，bin个数为200:
        pipeline.modifiers.append(CoordinationAnalysisModifier(cutoff = rdfcutoff, number_of_bins = rdfbins, partial =True))
        #对计算结果进行时间平均
        pipeline.modifiers.append(TimeAveragingModifier(operate_on='table:coordination-rdf'))
        #rdf计算输出方法：使用自带命令输出到rdf.txt
        export_file(pipeline, outpath+"rdf.txt", "txt/table", key="coordination-rdf[average]", multiple_frames = True)
        # 生成rdf数据后处理。
        rdflines = open(outpath+"rdf.txt", "r").read().splitlines()+['# Radial distribution function']
        nlist = [n for n, i in enumerate(rdflines) if '# Radial distribution function' in i]
        nrange = [nlist[i:i+2] for i in range(0, len(nlist), 2)]
        dfrdf = pd.DataFrame()
        for n,i in enumerate(nrange):
            df0 = pd.DataFrame(j.split() for j in rdflines[i[0]+2:i[1]])
            df0.insert(0,'frame',framelist[n])
            dfrdf = pd.concat([dfrdf,df0],axis=0).reset_index(drop=True)
        if len(atomorder) !=0:
            columnset = ["Pair separation distance"]+[atomorder[int(i.split('-')[0])+ -1]+'-'+atomorder[int(i.split('-')[1])+ -1] for i in rdflines[1].split()[4:]]
        else:
            columnset = ["Pair separation distance"]+rdflines[1].split()[4:]
        dfrdf.columns = ['frame']+columnset
        dfrdf.insert(1, 'time', dfrdf['frame']*timestep*0.001)
        ovitoout['rdf'] = dfrdf
    if ("MSD" in modes) or ("RMSD" in modes):
        #将以上自定义的msd计算函数添加到管道修饰中
        pipeline.modifiers.append(calculate_msd)
        #计算的每一帧msd导出到msd.txt文件，文件共两列：步数、MSD
        export_file(pipeline, outpath+"msd.txt", format = "txt/attr",columns = ["Timestep", "MSD","RMSD"],multiple_frames = True)
        # msd和rmsd数据后处理。
        dfmsd = pd.read_csv(outpath+"msd.txt", sep=' ', header=0, names=["frame", "MSD", "RMSD", "del"]).drop("del",axis=1)
        ovitoout['msd'] = dfmsd
    return ovitoout
# dumpfile = "F:/ganqiang/test/rdx/dump.trj"
# outpath = "F:\\ganqiang\\test\\rdx\\"
# modes = ["RDF", "MSD"]
# caldict = {'timestep':0.2,
#            'atomorder':['H','C','O','N'],
#            'cutoff':5.0,
#            'bins':200}
# encode = 'utf-8'
# ovitoout = ovitopip(dumpfile, outpath, modes, caldict, encode)
# print(ovitoout['rdf'])

# 检查当前conda中是否包含目标环境。  @2024/2/7
def check_conda(environment_name):
    result = subprocess.run(['conda', 'env', 'list'], stdout=subprocess.PIPE, text=True)
    env_list = result.stdout.split('\n')
    for env in env_list:
        if environment_name in env:
            return True
    return False

#------------------Setting模块和函数 ----------------#
def readsetting(items):
    lmpsetting, cuttype, cutvalue, encodedefault, elementdefault, cutoffdefault= items
    if lmpsetting != '':
        try:
            dfset = pd.read_csv((lmpsetting +'/lmpsetting.csv').replace('//','/'), header=0, index_col=None).dropna()
        except:
            dfset = pd.DataFrame()    # 建立空pandas列表。
            dfset['item'] = ['encode','element','cutoff']
            dfset['type'] = ['default','default','default']
            dfset['value'] = [encodedefault, elementdefault, cutoffdefault]
            print("# Warning: loading lmpsetting failed, manual set would not be loaded!")
    else:
        dfset = pd.DataFrame()    # 建立空pandas列表。
        dfset['item'] = ['encode','element','cutoff']
        dfset['type'] = ['default','default','default']
        dfset['value'] = [encodedefault, elementdefault, cutoffdefault]
        print("# Warning: lmpsetting is empty, default set would be loaded!")
    return dfset