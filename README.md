<div align="center">
<img src=".\image\logo.png" width="100" height="95" />

# PyGlimmer

**Python逆向工程集成工具**

[![Version](https://img.shields.io/badge/版本-1.2-blue.svg)](https://github.com/yoruak1/PyGlimmer)
[![Python](https://img.shields.io/badge/python-3.8+-green.svg)](https://www.python.org/)
[![公众号](https://img.shields.io/badge/公众号-夜秋的小屋-orange.svg)](https://github.com/yoruak1/PyGlimmer)

</div>

---

## PyGlimmer介绍

PyGlimmer是一款**专为PyInstaller、Pyarmor打包应用程序及pyc字节码分析而设计的综合性Python逆向工程集成工具**

### ✨ 核心功能

 **多引擎反编译**
- **uncompyle6** - Python字节码反编译器
- **decompyle3** - Python 3.7+字节码反编译器  
- **pycdc** - C++实现的Python反编译器
- **pydas** - Python字节码反汇编器
- **PyLingual- PyLingual是一个CPython字节码反编译器，支持自3.6以来发布的所有Python版本（包括3.12、3.13等）**
- 等

**分析处理能力**

- **PyInstaller解包**: 提取和分析PyInstaller可执行文件
- **批量反编译**: 同时处理多个pyc文件
- **.pyc.encrypted解密**: 支持PyInstaller加密字节码
- **字节码分析**: 十六进制/文本/字节码查看
- **检测python版本: 识别可执行文件打包时使用的Python版本**
- **自动配置: 自动分析PyInstaller解包后的文件夹，智能识别和配置解密.pyc.encrypted所需的各种参数**
- **PYC魔数头修复**
- **PYC隐写**
- 等

---

## 📋 系统要求

### 核心依赖

- **Python 3.8+**
- **附加工具**: uncompyle6,decompyle3,Pycdc,Pycdas,PyLingual,Pyinstxtractor,stegosaurus,Pyarmor-Static-Unpack-1shot等

---

## 🚀 快速开始

### 安装

```bash
# 克隆仓库
git clone https://github.com/yoruak1/PyGlimmer.git
cd PyGlimmer

# 安装依赖
pip install -r requirements.txt

# 可选-安装PyLingual-https://github.com/syssec-utd/pylingual
# pylingual本地大概有2-3G太大了，所以师傅们如果需要则可以自行安装，并将pylingual.exe的路径加入环境变量

# 运行PyGlimmer
python PyGlimmer.py
```

###  🔧 基本使用

#### 反编译

可选择反编译器：uncompyle6、decompyle3、pycdc

<img src=".\image\P1.png" style="zoom:50%;" />

#### 反汇编

可选择反汇编器：python自带dis模块、pycdas

<img src=".\image\P2.png" style="zoom:50%;" />

#### PyInstaller解包
使用PyInstExtractor解包PyInstaller打包程序

<img src=".\image\P4.png" style="zoom:50%;" />

#### Pyarmor解包

使用Pyarmor-Static-Unpack-1shot解包Pyarmor打包程序

<img src=".\image\P5.png" style="zoom:50%;" />

---

## 💡 高级功能

### pyc.encrypted解密
支持解密.pyc.encrypted：

- **PyInstaller < 4.0**: CFB模式解密
- **PyInstaller ≥ 4.0**: CTR模式解密
- **支持自动配置，分析PyInstaller解包后的文件夹，智能识别和配置解密.pyc.encrypted所需的各种参数**

<img src=".\image\P6.png" style="zoom:50%;" />

### PyLingual反编译
**PyLingual是一个CPython字节码反编译器，支持自3.6以来发布的所有Python版本（包括3.12、3.13等）**

<img src=".\image\P3.png" style="zoom:50%;" />

### PYC魔数头修复

**支持修复使用了错误版本的魔数头和缺少对应版本的魔数头两种情况**

<img src=".\image\P7.png" style="zoom:50%;" />

### PYC隐写

使用stegosaurus提取隐藏于pyc文件中的信息

<img src=".\image\P8.png" style="zoom:50%;" />

****

---

## 🎬 demo

### 功能演示

<img src="./image/demo.gif" width="800" alt="PyGlimmer功能演示" />


---

## 🛠️ 输出结构

PyGlimmer将结果输出在专用文件夹中：

| 输出类型 | 文件夹 | 描述 |
|---------|--------|------|
| 反编译 | `decompile_output/` | 反编译后Python文件 |
| 反汇编 | `disasm_output/` | 反汇编后的字节码指令列表 |
| PYC解密 | `extract_de/` | 解密后的PYC文件 |
| PYC魔数头修复 | `fixed/` | 修复后的PYC文件 |
| PyInstaller解包 | `[文件名]_extracted/` | PyInstaller解包后文件 |

---

## 📜 许可证

本项目采用GPL-3.0许可证 - 详情请参阅 [LICENSE](LICENSE) 文件。

---

## 🙏 感谢

### 反编译/反汇编器
- **[uncompyle6](https://github.com/rocky/python-uncompyle6)** - Python字节码反编译器
- **[decompyle3](https://github.com/rocky/python-decompile3)** - Python 3.7+字节码反编译器  
- **[pycdc](https://github.com/zrax/pycdc)** - C++实现的Python反编译器
- **[pycdas](https://github.com/zrax/pycdc)** - Python字节码反汇编器
- **[PyLingual](https://github.com/syssec-utd/pylingual)** - PyLingual是一个CPython字节码反编译器，支持自3.6以来发布的所有Python版本。

### 解包工具
- **[pyinstxtractor](https://github.com/extremecoders-re/pyinstxtractor)** - PyInstaller解包工具
- **[Pyarmor-Static-Unpack-1shot](https://github.com/Lil-House/Pyarmor-Static-Unpack-1shot)** - Pyarmor解包工具

### 其他

- **[stegosaurus](https://github.com/AngelKitty/stegosaurus)** - pyc隐写工具

---

## 📋 参考

- [python逆向之pyc反编译与解密](https://blog.csdn.net/GalaxySpaceX/article/details/130591614)

---

## 💖 支持项目

如果各位师傅觉得工具不错，点点⭐Star吧！ 🙏

您的支持是我持续更新的最大动力！💪

---

## ⚠️ 免责声明

使用PyGlimmer即表示您：
- 已充分了解并同意遵守相关法律法规
- 承诺仅在合法授权范围内使用本工具
- 理解并承担因不当使用而产生的一切法律后果

**开发者不对用户的任何违法违规行为承担责任**

</div>
