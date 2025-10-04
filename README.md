<div align="center">
<img src=".\image\logo.png" width="100" height="95" />

# PyGlimmer

**Python逆向工程集成工具**

[![Version](https://img.shields.io/badge/版本-1.1-blue.svg)](https://github.com/yoruak1/PyGlimmer)
[![Python](https://img.shields.io/badge/python-3.10+-green.svg)](https://www.python.org/)
[![公众号](https://img.shields.io/badge/公众号-夜秋的小屋-orange.svg)](https://github.com/yoruak1/PyGlimmer)

</div>

---

## PyGlimmer介绍

PyGlimmer是一款**专为PyInstaller打包应用程序分析而设计的综合性Python逆向工程集成工具**

### ✨ 核心功能

 **多引擎反编译**
- **uncompyle6** - Python字节码反编译器
- **decompyle3** - Python 3.7+字节码反编译器  
- **pycdc** - C++实现的Python反编译器
- **pydas** - Python字节码反汇编器
- **新增——PyLingual- PyLingual是一个CPython字节码反编译器，支持自3.6以来发布的所有Python版本（包括3.12等）**

**分析处理能力**

- **PyInstaller解包**: 提取和分析PyInstaller可执行文件
- **批量反编译**: 同时处理多个pyc文件
- **.pyc.encrypted解密**: 支持PyInstaller加密字节码
- **字节码分析**: 十六进制/文本/字节码查看
- **新增——检测python版本: 识别可执行文件打包时使用的Python版本**
- **新增——自动配置: 自动分析PyInstaller解包后的文件夹，智能识别和配置解密.pyc.encrypted所需的各种参数**

---

## 📋 系统要求

### 核心依赖

- **Python 3.10+**
- **附加工具**: uncompyle6, decompyle3, pycdc, pycdas,PyLingual,pyinstxtractor等

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

# 运行PyGlimmer
python main.py
```

###  🔧 基本使用

#### 单文件反编译
1. 选择 **"单文件反编译"** 标签页
2. 使用 **"浏览..."** 按钮选择PYC文件
3. 选择首选的反编译引擎
4. 点击 **"反编译"** 开始分析

<img src=".\image\img1.png" style="zoom:50%;" />

#### 批量反编译
1. 选择 **"批量反编译"** 标签页
2. 单独添加文件或选择整个文件夹
3. 选择首选的反编译引擎
4. 开始批量处理

<img src=".\image\img2.png" style="zoom:50%;" />

#### PyInstaller解包
1. 打开 **"PyInstaller解包"** 标签页
2. 选择打包的可执行文件
3. **自动检测打包时使用的Python版本**
4. 开始解包

<img src=".\image\img4.png" style="zoom:50%;" />

---

## 💡 高级功能

### pyc.encrypted解密
支持解密.pyc.encrypted：

- **PyInstaller < 4.0**: CFB模式解密
- **PyInstaller ≥ 4.0**: CTR模式解密
- **支持自动配置，分析PyInstaller解包后的文件夹，智能识别和配置解密.pyc.encrypted所需的各种参数**

<img src=".\image\img3.png" style="zoom:50%;" />

### PyLingual反编译
**PyLingual是一个CPython字节码反编译器，支持自3.6以来发布的所有Python版本（包括3.12等）**

<img src=".\image\img5.png" style="zoom:50%;" />

---

## 🎬 demo

### 功能演示

<video width="800" controls>
  <source src="./image/demo.mp4" type="video/mp4">
  您的浏览器不支持视频标签。请<a href="./image/demo.webm">点击此处下载演示视频</a>
</video>




---

## 🛠️ 输出结构

PyGlimmer将结果输出在专用文件夹中：

| 输出类型 | 文件夹 | 描述 |
|---------|--------|------|
| 反编译 | `extract/` | 转换的Python文件 |
| 解密 | `extract_de/` | 解密后的PYC文件 |
| 解包 | `[文件名]_extracted/` | PyInstaller解包后文件 |

---

## 📜 许可证

本项目采用GPL-3.0许可证 - 详情请参阅 [LICENSE](LICENSE) 文件。

---

## 🙏 感谢

### 反编译器
- **[uncompyle6](https://github.com/rocky/python-uncompyle6)** - Python字节码反编译器
- **[decompyle3](https://github.com/rocky/python-decompile3)** - Python 3.7+字节码反编译器  
- **[pycdc](https://github.com/zrax/pycdc)** - C++实现的Python反编译器
- **[pycdas](https://github.com/zrax/pycdc)** - Python字节码反汇编器
- **[PyLingual](https://github.com/syssec-utd/pylingual)** - PyLingual是一个CPython字节码反编译器，支持自3.6以来发布的所有Python版本。

### 解包工具
- **[pyinstxtractor](https://github.com/extremecoders-re/pyinstxtractor)** - PyInstaller解包工具

---

## 📋 参考

- [python逆向之pyc反编译与解密](https://blog.csdn.net/GalaxySpaceX/article/details/130591614)

---

## ⚠️ 免责声明

使用PyGlimmer即表示您：
- 已充分了解并同意遵守相关法律法规
- 承诺仅在合法授权范围内使用本工具
- 理解并承担因不当使用而产生的一切法律后果

**开发者不对用户的任何违法违规行为承担责任**

</div>
