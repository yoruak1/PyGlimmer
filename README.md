# PyGlimmer —— 针对PyInstaller打包程序的解包、反编译、解密工具

一个能够助力你Python逆向的工具，具有对PyInstaller打包的程序进行解包、反编译Python字节码（pyc）文件、解密.pyc.encrypted文件等多种功能

<img src=".\image\im1.png" style="zoom:50%;" />

## ✨ 功能特性

- 反编译pyc文件，可实时查看反编译结果或将结果输出到同名py文件中，支持四种不同的反编译器：
  - uncompyle6

  - decompyle3

  - pycdc

  - pycdas

    <img src=".\image\im2.png" style="zoom:100%;" />

- 批量反编译pyc文件，允许一次性选择多个pyc文件或整个文件夹：

  <img src=".\image\im3.png" style="zoom:50%;" />

- PYC解密功能：
  - 支持PyInstaller加密过的pyc文件解密

  - 分别支持PyInstaller < 4.0版本(CFB模式)和≥ 4.0版本(CTR模式)两种解密方式

    <img src=".\image\im4.png" style="zoom:50%;" />

- PyInstaller解包功能：
  - 在原版的pyinstxtractor.py中，当检测到执行解包工具的Python版本与打包程序的Python版本不匹配时，会直接跳过对PYZ-00.pyz文件的解包，而在本工具中我修改了这一点，即使版本不一致，也会对PYZ-00.pyz尝试解包操作。（不过仍然建议使用和程序相同的Python版本进行解包，以获得最佳结果!）

    <img src=".\image\im7.png" style="zoom:50%;" />

- 字节码/十六进制/文本内容查看功能：
  - 支持调用dis模块查看pyc文件的字节码

  - 支持对pyc文件的十六进制和文本内容查看

    <img src=".\image\im5.png" style="zoom:50%;" />

- 输出：
  - 反编译结果保存在"extract"文件夹
  - 解密结果保存在"extract_de"文件夹
  - 解包结果保存在"程序名_extracted"文件夹

## 🔧环境要求

- Python 3.10+
- PyQt6 6.9.0

## 🚀安装与使用

1.克隆此仓库

2.安装所需依赖：

```
pip install -r requirements.txt
```

3.运行应用程序：

```
python main.py
```

## 📋 参考

- https://blog.csdn.net/GalaxySpaceX/article/details/130591614