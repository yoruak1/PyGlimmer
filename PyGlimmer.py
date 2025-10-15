import sys
import os
import subprocess
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                           QLabel, QPushButton, QFileDialog, QTextEdit, QComboBox,
                           QCheckBox, QGroupBox, QMessageBox, QSplitter, QListWidget,
                           QProgressBar, QTabWidget, QLineEdit, QRadioButton, QButtonGroup,
                           QGraphicsDropShadowEffect, QFrame, QDialog)
from PyQt6.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt6.QtGui import QFont, QColor, QPalette, QPixmap, QIcon
import zlib
import dis
import marshal
import struct
import uuid
from contextlib import redirect_stdout
import re
import webbrowser
import ctypes

try:
    from Decryptor.decrypt_pyinstaller_lt4 import decrypt_pyc_files as decrypt_lt4
    from Decryptor.decrypt_pyinstaller_ge4 import decrypt_pyc_files as decrypt_ge4
    DECRYPTION_AVAILABLE = True
except ImportError:
    DECRYPTION_AVAILABLE = False

try:
    from PyInstExtractor.pyinstxtractor import PyInstArchive, normalize_path_for_display
    PYINSTALLER_EXTRACTOR_AVAILABLE = True
except ImportError:
    PYINSTALLER_EXTRACTOR_AVAILABLE = False

try:
    import pefile
    PEFILE_AVAILABLE = True
except ImportError:
    PEFILE_AVAILABLE = False

MAGIC_NUMBERS = {
    b'\x02\x99\x99\x00': "Python 1.0",
    b'\x03\x99\x99\x00': "Python 1.1",
    b'\x89\x2E\x0D\x0A': "Python 1.3",
    b'\x04\x17\x0D\x0A': "Python 1.4",
    b'\x99\x4E\x0D\x0A': "Python 1.5",
    b'\xFC\xC4\x0D\x0A': "Python 1.6",
    b'\x87\xC6\x0D\x0A': "Python 2.0",
    b'\x2A\xEB\x0D\x0A': "Python 2.1",
    b'\x2D\xED\x0D\x0A': "Python 2.2",
    b'\x3B\xF2\x0D\x0A': "Python 2.3",
    b'\x6D\xF2\x0D\x0A': "Python 2.4",
    b'\xB3\xF2\x0D\x0A': "Python 2.5",
    b'\xD1\xF2\x0D\x0A': "Python 2.6",
    b'\x03\xF3\x0D\x0A': "Python 2.7",
    b'\x3A\x0C\x0D\x0A': "Python 3.0",
    b'\x4E\x0C\x0D\x0A': "Python 3.1",
    b'\x6C\x0C\x0D\x0A': "Python 3.2",
    b'\x9E\x0C\x0D\x0A': "Python 3.3",
    b'\xEE\x0C\x0D\x0A': "Python 3.4",
    b'\x16\x0D\x0D\x0A': "Python 3.5",
    b'\x17\x0D\x0D\x0A': "Python 3.5.3",
    b'\x33\x0D\x0D\x0A': "Python 3.6",
    b'\x42\x0D\x0D\x0A': "Python 3.7",
    b'\x55\x0D\x0D\x0A': "Python 3.8",
    b'\x61\x0D\x0D\x0A': "Python 3.9",
    b'\x6F\x0D\x0D\x0A': "Python 3.10",
    b'\xA7\x0D\x0D\x0A': "Python 3.11",
    b'\xCB\x0D\x0D\x0A': "Python 3.12",
    b'\xF3\x0D\x0D\x0A': "Python 3.13",
}

def get_files_with_extension(directory, extensions, recursive=True):
    result_files = []
    
    if recursive:
        for root, dirs, files in os.walk(directory):
            for file in files:
                if any(file.endswith(ext) for ext in extensions):
                    result_files.append(os.path.join(root, file))
    else:
        for item in os.listdir(directory):
            full_path = os.path.join(directory, item)
            if os.path.isfile(full_path) and any(item.endswith(ext) for ext in extensions):
                result_files.append(full_path)
    
    return result_files


class AnimatedLogoFrame(QFrame):
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._scale_factor = 1.0
        self._opacity = 1.0
        
        self.scale_animation = QPropertyAnimation(self, b"scale_factor")
        self.scale_animation.setDuration(200)
        self.scale_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        self.opacity_animation = QPropertyAnimation(self, b"opacity_value")
        self.opacity_animation.setDuration(150)
        self.opacity_animation.setEasingCurve(QEasingCurve.Type.OutQuad)
    
    @pyqtProperty(float)
    def scale_factor(self):
        return self._scale_factor
    
    @scale_factor.setter
    def scale_factor(self, value):
        self._scale_factor = value
        self.update_transform()
    
    @pyqtProperty(float)
    def opacity_value(self):
        return self._opacity
    
    @opacity_value.setter
    def opacity_value(self, value):
        self._opacity = value
        self.update_opacity()
    
    def update_transform(self):
        try:
            if hasattr(self, 'original_size'):
                new_width = int(self.original_size.width() * self._scale_factor)
                new_height = int(self.original_size.height() * self._scale_factor)
                self.resize(new_width, new_height)
                
                if hasattr(self, 'parent') and self.parent():
                    margin_right = 10
                    margin_top = 5
                    parent_width = self.parent().width()
                    self.move(parent_width - new_width - margin_right, margin_top)
        except:
            pass
    
    def update_opacity(self):
        try:
            if hasattr(self, 'base_style'):
                brightness_factor = self._opacity
                
                if brightness_factor > 1.0:
                    intensity = min((brightness_factor - 1.0) * 2.0, 1.0)
                    
                    bright_style = self.base_style.replace(
                        "stop: 0 rgba(245, 167, 66, 100)",
                        f"stop: 0 rgba(255, 200, 120, {100 + int(intensity * 50)})"
                    ).replace(
                        "stop: 0.7 rgba(245, 167, 66, 60)",
                        f"stop: 0.7 rgba(255, 200, 120, {60 + int(intensity * 40)})"
                    ).replace(
                        "border: 2px solid rgba(245, 167, 66, 150)",
                        f"border: 3px solid rgba(255, 200, 120, {150 + int(intensity * 70)})"
                    )
                    
                    self.setStyleSheet(bright_style)
                else:
                    self.setStyleSheet(self.base_style)
        except:
            pass
    
    def enterEvent(self, event):
        try:
            self.scale_animation.setStartValue(self._scale_factor)
            self.scale_animation.setEndValue(1.1)
            self.scale_animation.start()
            
            self.opacity_animation.setStartValue(self._opacity)
            self.opacity_animation.setEndValue(1.3)
            self.opacity_animation.start()
        except:
            pass
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        try:
            self.scale_animation.setStartValue(self._scale_factor)
            self.scale_animation.setEndValue(1.0)
            self.scale_animation.start()
            
            self.opacity_animation.setStartValue(self._opacity)
            self.opacity_animation.setEndValue(1.0)
            self.opacity_animation.start()
        except:
            pass
        super().leaveEvent(event)

class PythonDecompilerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.batch_files = []
        self.batch_disasm_files = []
        self.encrypted_files = []
        self.batch_stop_flag = False
        self.batch_disasm_stop_flag = False
        
    def initUI(self):
        self.setWindowTitle('PyGlimmer  by: yoruaki  公众号：夜秋的小屋')
        self.setGeometry(100, 100, 1200, 900)
        
        logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "image", "logo.png")
        if os.path.exists(logo_path):
            self.setWindowIcon(QIcon(logo_path))
        
        self.set_style()
        self.add_logo()
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #F5A742;
                border-radius: 4px;
                padding: 5px;
            }
            QTabBar::tab {
                background-color: #FFF1DC;
                border: 1px solid #F5A742;
                border-bottom-color: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                padding: 6px 10px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #FFFFFF;
                border-bottom: none;
            }
            QTabBar::tab:!selected {
                margin-top: 2px;
            }
        """)
        
        single_tab = QWidget()
        single_layout = QVBoxLayout(single_tab)
        single_layout.setSpacing(10)
        
        file_section = QGroupBox("文件选择")
        file_section.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #F5A742;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        file_layout = QHBoxLayout()
        
        self.file_path_label = QLabel("未选择文件")
        self.browse_button = QPushButton("浏览...")
        self.browse_button.setStyleSheet(self.get_button_style())
        self.browse_button.clicked.connect(self.browse_file)
        
        file_layout.addWidget(self.file_path_label, 1)
        file_layout.addWidget(self.browse_button)
        file_section.setLayout(file_layout)
        
        decompiler_section = QGroupBox("反编译器选择")
        decompiler_section.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #F5A742;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        decompiler_layout = QVBoxLayout()
        
        self.decompiler_combo = QComboBox()
        self.decompiler_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #F5A742;
                border-radius: 4px;
                padding: 5px;
                background-color: #FFFFFF;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 15px;
                border-left-width: 1px;
                border-left-color: #F5A742;
                border-left-style: solid;
                border-top-right-radius: 3px;
                border-bottom-right-radius: 3px;
            }
        """)
        self.decompiler_combo.addItems(["uncompyle6", "decompyle3", "pycdc"])
        decompiler_layout.addWidget(self.decompiler_combo)
        
        self.save_checkbox = QCheckBox("将结果保存到.py文件")
        self.save_checkbox.setStyleSheet("""
            QCheckBox {
                spacing: 5px;
            }
            QCheckBox::indicator {
                width: 15px;
                height: 15px;
            }
            QCheckBox::indicator:unchecked {
                border: 2px solid #F5A742;
                border-radius: 8px;
                background-color: #FFFFFF;
            }
            QCheckBox::indicator:checked {
                border: 2px solid #F5A742;
                border-radius: 8px;
                background-color: #FF9966;
            }
        """)
        decompiler_layout.addWidget(self.save_checkbox)
        
        decompiler_section.setLayout(decompiler_layout)
        
        self.decompile_button = QPushButton("反编译")
        self.decompile_button.setStyleSheet(self.get_button_style())
        self.decompile_button.clicked.connect(self.decompile)
        self.decompile_button.setEnabled(False)
        
        results_section = QGroupBox("反编译结果")
        results_section.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #F5A742;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        results_layout = QVBoxLayout()
        
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setFont(QFont("Courier", 10))
        self.results_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #F5A742;
                border-radius: 4px;
                padding: 5px;
                background-color: #FFFFFF;
                color: #333333;
            }
        """)
        
        results_layout.addWidget(self.results_text)
        results_section.setLayout(results_layout)
        
        single_layout.addWidget(file_section)
        single_layout.addWidget(decompiler_section)
        single_layout.addWidget(self.decompile_button)
        single_layout.addWidget(results_section, 1)
        
        disasm_tab = QWidget()
        disasm_layout = QVBoxLayout(disasm_tab)
        disasm_layout.setSpacing(10)
        
        disasm_file_section = QGroupBox("文件选择")
        disasm_file_section.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #F5A742;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        disasm_file_layout = QHBoxLayout()
        
        self.disasm_file_path_label = QLabel("未选择文件")
        self.disasm_browse_button = QPushButton("浏览...")
        self.disasm_browse_button.setStyleSheet(self.get_button_style())
        self.disasm_browse_button.clicked.connect(self.browse_disasm_file)
        
        disasm_file_layout.addWidget(self.disasm_file_path_label, 1)
        disasm_file_layout.addWidget(self.disasm_browse_button)
        disasm_file_section.setLayout(disasm_file_layout)
        
        disasm_tool_section = QGroupBox("反汇编器选择")
        disasm_tool_section.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #F5A742;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        disasm_tool_layout = QVBoxLayout()
        
        self.disasm_tool_combo = QComboBox()
        self.disasm_tool_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #F5A742;
                border-radius: 4px;
                padding: 5px;
                background-color: #FFFFFF;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 15px;
                border-left-width: 1px;
                border-left-color: #F5A742;
                border-left-style: solid;
                border-top-right-radius: 3px;
                border-bottom-right-radius: 3px;
            }
        """)
        self.disasm_tool_combo.addItems(["dis模块", "pycdas"])
        disasm_tool_layout.addWidget(self.disasm_tool_combo)
        
        self.disasm_save_checkbox = QCheckBox("将结果保存到.txt文件")
        self.disasm_save_checkbox.setStyleSheet("""
            QCheckBox {
                spacing: 5px;
            }
            QCheckBox::indicator {
                width: 15px;
                height: 15px;
            }
            QCheckBox::indicator:unchecked {
                border: 2px solid #F5A742;
                border-radius: 8px;
                background-color: #FFFFFF;
            }
            QCheckBox::indicator:checked {
                border: 2px solid #F5A742;
                border-radius: 8px;
                background-color: #FF9966;
            }
        """)
        disasm_tool_layout.addWidget(self.disasm_save_checkbox)
        
        disasm_tool_section.setLayout(disasm_tool_layout)
        
        self.disasm_button = QPushButton("反汇编")
        self.disasm_button.setStyleSheet(self.get_button_style())
        self.disasm_button.clicked.connect(self.disassemble)
        self.disasm_button.setEnabled(False)
        
        disasm_results_section = QGroupBox("反汇编结果")
        disasm_results_section.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #F5A742;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        disasm_results_layout = QVBoxLayout()
        
        self.disasm_results_text = QTextEdit()
        self.disasm_results_text.setReadOnly(True)
        self.disasm_results_text.setFont(QFont("Courier", 10))
        self.disasm_results_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #F5A742;
                border-radius: 4px;
                padding: 5px;
                background-color: #FFFFFF;
                color: #333333;
            }
        """)
        
        disasm_results_layout.addWidget(self.disasm_results_text)
        disasm_results_section.setLayout(disasm_results_layout)
        
        disasm_layout.addWidget(disasm_file_section)
        disasm_layout.addWidget(disasm_tool_section)
        disasm_layout.addWidget(self.disasm_button)
        disasm_layout.addWidget(disasm_results_section, 1)
        
        batch_disasm_tab = QWidget()
        batch_disasm_layout = QVBoxLayout(batch_disasm_tab)
        batch_disasm_layout.setSpacing(10)
        
        batch_disasm_file_section = QGroupBox("批量文件选择")
        batch_disasm_file_section.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #F5A742;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        batch_disasm_file_layout = QVBoxLayout()
        
        batch_disasm_button_layout = QHBoxLayout()
        self.batch_disasm_browse_button = QPushButton("选择多个PYC文件...")
        self.batch_disasm_browse_button.setStyleSheet(self.get_button_style())
        self.batch_disasm_browse_button.clicked.connect(self.browse_batch_disasm_files)
        
        self.batch_disasm_browse_dir_button = QPushButton("选择文件夹...")
        self.batch_disasm_browse_dir_button.setStyleSheet(self.get_button_style())
        self.batch_disasm_browse_dir_button.clicked.connect(self.browse_batch_disasm_directory)
        
        self.batch_disasm_clear_button = QPushButton("清空列表")
        self.batch_disasm_clear_button.setStyleSheet(self.get_button_style())
        self.batch_disasm_clear_button.clicked.connect(self.clear_batch_disasm_files)
        
        batch_disasm_button_layout.addWidget(self.batch_disasm_browse_button)
        batch_disasm_button_layout.addWidget(self.batch_disasm_browse_dir_button)
        batch_disasm_button_layout.addWidget(self.batch_disasm_clear_button)
        
        self.batch_disasm_files_list = QListWidget()
        self.batch_disasm_files_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #F5A742;
                border-radius: 4px;
                padding: 5px;
                background-color: #FFFFFF;
            }
        """)
        
        batch_disasm_file_layout.addLayout(batch_disasm_button_layout)
        batch_disasm_file_layout.addWidget(QLabel("已选择的文件:"))
        batch_disasm_file_layout.addWidget(self.batch_disasm_files_list)
        
        batch_disasm_file_section.setLayout(batch_disasm_file_layout)
        
        batch_disasm_tool_section = QGroupBox("反汇编器选择")
        batch_disasm_tool_section.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #F5A742;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        batch_disasm_tool_layout = QVBoxLayout()
        
        self.batch_disasm_tool_combo = QComboBox()
        self.batch_disasm_tool_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #F5A742;
                border-radius: 4px;
                padding: 5px;
                background-color: #FFFFFF;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 15px;
                border-left-width: 1px;
                border-left-color: #F5A742;
                border-left-style: solid;
                border-top-right-radius: 3px;
                border-bottom-right-radius: 3px;
            }
        """)
        self.batch_disasm_tool_combo.addItems(["dis模块", "pycdas"])
        batch_disasm_tool_layout.addWidget(self.batch_disasm_tool_combo)
        
        
        batch_disasm_tool_section.setLayout(batch_disasm_tool_layout)
        
        batch_disasm_progress_section = QGroupBox("反汇编进度")
        batch_disasm_progress_section.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #F5A742;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        batch_disasm_progress_layout = QVBoxLayout()
        
        self.batch_disasm_progress_bar = QProgressBar()
        self.batch_disasm_progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #F5A742;
                border-radius: 4px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #F5A742;
            }
        """)
        self.batch_disasm_progress_bar.setValue(0)
        
        self.batch_disasm_progress_label = QLabel("就绪")
        
        batch_disasm_progress_layout.addWidget(self.batch_disasm_progress_bar)
        batch_disasm_progress_layout.addWidget(self.batch_disasm_progress_label)
        
        batch_disasm_progress_section.setLayout(batch_disasm_progress_layout)
        
        batch_disasm_buttons_layout = QHBoxLayout()
        
        self.batch_disasm_button = QPushButton("批量反汇编")
        self.batch_disasm_button.setStyleSheet(self.get_button_style())
        self.batch_disasm_button.clicked.connect(self.batch_disassemble)
        self.batch_disasm_button.setEnabled(False)
        
        self.batch_disasm_stop_button = QPushButton("终止")
        self.batch_disasm_stop_button.setStyleSheet("""
            QPushButton {
                background-color: #FF6B6B;
                color: white;
                border-radius: 5px;
                padding: 5px 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FF5252;
            }
            QPushButton:pressed {
                background-color: #E53935;
            }
            QPushButton:disabled {
                background-color: #D3D3D3;
                color: #A9A9A9;
            }
        """)
        self.batch_disasm_stop_button.clicked.connect(self.stop_batch_disassemble)
        self.batch_disasm_stop_button.setEnabled(False)
        
        batch_disasm_buttons_layout.addWidget(self.batch_disasm_button)
        batch_disasm_buttons_layout.addWidget(self.batch_disasm_stop_button)
        
        batch_disasm_layout.addWidget(batch_disasm_file_section)
        batch_disasm_layout.addWidget(batch_disasm_tool_section)
        batch_disasm_layout.addWidget(batch_disasm_progress_section)
        batch_disasm_layout.addLayout(batch_disasm_buttons_layout)
        
        batch_tab = QWidget()
        batch_layout = QVBoxLayout(batch_tab)
        batch_layout.setSpacing(10)
        
        batch_file_section = QGroupBox("批量文件选择")
        batch_file_section.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #F5A742;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        batch_file_layout = QVBoxLayout()
        
        batch_button_layout = QHBoxLayout()
        self.batch_browse_button = QPushButton("选择多个PYC文件...")
        self.batch_browse_button.setStyleSheet(self.get_button_style())
        self.batch_browse_button.clicked.connect(self.browse_batch_files)
        
        self.batch_browse_dir_button = QPushButton("选择文件夹...")
        self.batch_browse_dir_button.setStyleSheet(self.get_button_style())
        self.batch_browse_dir_button.clicked.connect(self.browse_batch_directory)
        
        self.batch_clear_button = QPushButton("清空列表")
        self.batch_clear_button.setStyleSheet(self.get_button_style())
        self.batch_clear_button.clicked.connect(self.clear_batch_files)
        
        batch_button_layout.addWidget(self.batch_browse_button)
        batch_button_layout.addWidget(self.batch_browse_dir_button)
        batch_button_layout.addWidget(self.batch_clear_button)
        
        self.batch_files_list = QListWidget()
        self.batch_files_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #F5A742;
                border-radius: 4px;
                padding: 5px;
                background-color: #FFFFFF;
            }
        """)
        
        batch_file_layout.addLayout(batch_button_layout)
        batch_file_layout.addWidget(QLabel("已选择的文件:"))
        batch_file_layout.addWidget(self.batch_files_list)
        
        batch_file_section.setLayout(batch_file_layout)
        
        batch_decompiler_section = QGroupBox("反编译器选择")
        batch_decompiler_section.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #F5A742;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        batch_decompiler_layout = QVBoxLayout()
        
        self.batch_decompiler_combo = QComboBox()
        self.batch_decompiler_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #F5A742;
                border-radius: 4px;
                padding: 5px;
                background-color: #FFFFFF;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 15px;
                border-left-width: 1px;
                border-left-color: #F5A742;
                border-left-style: solid;
                border-top-right-radius: 3px;
                border-bottom-right-radius: 3px;
            }
        """)
        self.batch_decompiler_combo.addItems(["uncompyle6", "decompyle3", "pycdc"])
        batch_decompiler_layout.addWidget(self.batch_decompiler_combo)
        
        batch_decompiler_section.setLayout(batch_decompiler_layout)
        
        progress_section = QGroupBox("反编译进度")
        progress_section.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #F5A742;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        progress_layout = QVBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #F5A742;
                border-radius: 4px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #F5A742;
            }
        """)
        self.progress_bar.setValue(0)
        
        self.progress_label = QLabel("就绪")
        
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.progress_label)
        
        progress_section.setLayout(progress_layout)
        
        batch_buttons_layout = QHBoxLayout()
        
        self.batch_decompile_button = QPushButton("批量反编译")
        self.batch_decompile_button.setStyleSheet(self.get_button_style())
        self.batch_decompile_button.clicked.connect(self.batch_decompile)
        self.batch_decompile_button.setEnabled(False)
        
        self.batch_stop_button = QPushButton("终止")
        self.batch_stop_button.setStyleSheet("""
            QPushButton {
                background-color: #FF6B6B;
                color: white;
                border-radius: 5px;
                padding: 5px 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FF5252;
            }
            QPushButton:pressed {
                background-color: #E53935;
            }
            QPushButton:disabled {
                background-color: #D3D3D3;
                color: #A9A9A9;
            }
        """)
        self.batch_stop_button.clicked.connect(self.stop_batch_decompile)
        self.batch_stop_button.setEnabled(False)
        
        batch_buttons_layout.addWidget(self.batch_decompile_button)
        batch_buttons_layout.addWidget(self.batch_stop_button)
        
        batch_layout.addWidget(batch_file_section)
        batch_layout.addWidget(batch_decompiler_section)
        batch_layout.addWidget(progress_section)
        batch_layout.addLayout(batch_buttons_layout)
        
        decrypt_tab = QWidget()
        decrypt_layout = QVBoxLayout(decrypt_tab)
        decrypt_layout.setSpacing(10)
        
        decrypt_section = QGroupBox("解密设置")
        decrypt_section.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #F5A742;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        decrypt_settings_layout = QVBoxLayout()
        
        self.auto_detect_button = QPushButton("自动配置")
        self.auto_detect_button.setStyleSheet(self.get_button_style())
        self.auto_detect_button.clicked.connect(self.auto_detect_decrypt_settings)
        decrypt_settings_layout.addWidget(self.auto_detect_button)
        
        key_layout = QHBoxLayout()
        key_layout.addWidget(QLabel("解密密钥:"))
        self.decrypt_key_input = QLineEdit()
        self.decrypt_key_input.setPlaceholderText("输入PyInstaller加密密钥")
        self.decrypt_key_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #F5A742;
                border-radius: 4px;
                padding: 5px;
                background-color: #FFFFFF;
            }
        """)
        key_layout.addWidget(self.decrypt_key_input)
        decrypt_settings_layout.addLayout(key_layout)
        
        python_version_layout = QHBoxLayout()
        python_version_layout.addWidget(QLabel("Python版本:"))
        self.python_version_combo = QComboBox()
        self.python_version_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #F5A742;
                border-radius: 4px;
                padding: 5px;
                background-color: #FFFFFF;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 15px;
                border-left-width: 1px;
                border-left-color: #F5A742;
                border-left-style: solid;
                border-top-right-radius: 3px;
                border-bottom-right-radius: 3px;
            }
        """)
        self.python_version_combo.addItems(["2.7", "3.0", "3.1", "3.2", "3.3", "3.4", "3.5", "3.6", "3.7", "3.8", "3.9", "3.10", "3.11", "3.12", "3.13"])
        self.python_version_combo.setCurrentText("3.8")
        python_version_layout.addWidget(self.python_version_combo)
        decrypt_settings_layout.addLayout(python_version_layout)
        
        pyinstaller_version_layout = QVBoxLayout()
        pyinstaller_version_layout.addWidget(QLabel("PyInstaller版本:"))
        
        pyinstaller_radio_layout = QHBoxLayout()
        self.pyinstaller_version_group = QButtonGroup(self)
        
        self.pyinstaller_lt4_radio = QRadioButton("PyInstaller < 4.0 (使用PyCrypto/CFB模式)")
        self.pyinstaller_ge4_radio = QRadioButton("PyInstaller >= 4.0 (使用TinyAES/CTR模式)")
        
        radio_style = """
            QRadioButton {
                spacing: 5px;
            }
            QRadioButton::indicator {
                width: 15px;
                height: 15px;
            }
            QRadioButton::indicator:unchecked {
                border: 2px solid #F5A742;
                border-radius: 8px;
                background-color: #FFFFFF;
            }
            QRadioButton::indicator:checked {
                border: 2px solid #F5A742;
                border-radius: 8px;
                background-color: #FF9966;
            }
        """
        self.pyinstaller_lt4_radio.setStyleSheet(radio_style)
        self.pyinstaller_ge4_radio.setStyleSheet(radio_style)
        
        self.pyinstaller_version_group.addButton(self.pyinstaller_lt4_radio, 1)
        self.pyinstaller_version_group.addButton(self.pyinstaller_ge4_radio, 2)
        
        self.pyinstaller_lt4_radio.setChecked(True)
        
        pyinstaller_radio_layout.addWidget(self.pyinstaller_lt4_radio)
        pyinstaller_radio_layout.addWidget(self.pyinstaller_ge4_radio)
        
        pyinstaller_version_layout.addLayout(pyinstaller_radio_layout)
        decrypt_settings_layout.addLayout(pyinstaller_version_layout)
        
        decrypt_section.setLayout(decrypt_settings_layout)
        
        encrypted_files_section = QGroupBox("选择加密PYC文件")
        encrypted_files_section.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #F5A742;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        encrypted_files_layout = QVBoxLayout()
        
        encrypted_button_layout = QHBoxLayout()
        self.encrypted_browse_button = QPushButton("选择.pyc.encrypted文件...")
        self.encrypted_browse_button.setStyleSheet(self.get_button_style())
        self.encrypted_browse_button.clicked.connect(self.browse_encrypted_files)
        
        self.encrypted_browse_dir_button = QPushButton("选择文件夹...")
        self.encrypted_browse_dir_button.setStyleSheet(self.get_button_style())
        self.encrypted_browse_dir_button.clicked.connect(self.browse_encrypted_directory)
        
        self.encrypted_clear_button = QPushButton("清空列表")
        self.encrypted_clear_button.setStyleSheet(self.get_button_style())
        self.encrypted_clear_button.clicked.connect(self.clear_encrypted_files)
        
        encrypted_button_layout.addWidget(self.encrypted_browse_button)
        encrypted_button_layout.addWidget(self.encrypted_browse_dir_button)
        encrypted_button_layout.addWidget(self.encrypted_clear_button)
        
        self.encrypted_files_list = QListWidget()
        self.encrypted_files_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #F5A742;
                border-radius: 4px;
                padding: 5px;
                background-color: #FFFFFF;
            }
        """)
        
        encrypted_files_layout.addLayout(encrypted_button_layout)
        encrypted_files_layout.addWidget(QLabel("已选择的加密文件:"))
        encrypted_files_layout.addWidget(self.encrypted_files_list)
        
        encrypted_files_section.setLayout(encrypted_files_layout)
        
        decrypt_progress_section = QGroupBox("解密进度")
        decrypt_progress_section.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #F5A742;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        decrypt_progress_layout = QVBoxLayout()
        
        self.decrypt_progress_bar = QProgressBar()
        self.decrypt_progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #F5A742;
                border-radius: 4px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #F5A742;
            }
        """)
        self.decrypt_progress_bar.setValue(0)
        
        self.decrypt_progress_label = QLabel("就绪")
        
        decrypt_progress_layout.addWidget(self.decrypt_progress_bar)
        decrypt_progress_layout.addWidget(self.decrypt_progress_label)
        
        decrypt_progress_section.setLayout(decrypt_progress_layout)
        
        self.decrypt_button = QPushButton("解密PYC文件")
        self.decrypt_button.setStyleSheet(self.get_button_style())
        self.decrypt_button.clicked.connect(self.decrypt_pyc_files)
        self.decrypt_button.setEnabled(False)
        
        decrypt_layout.addWidget(decrypt_section)
        decrypt_layout.addWidget(encrypted_files_section)
        decrypt_layout.addWidget(decrypt_progress_section)
        decrypt_layout.addWidget(self.decrypt_button)
        
        
        pyinstaller_tab = QWidget()
        pyinstaller_layout = QVBoxLayout(pyinstaller_tab)
        pyinstaller_layout.setSpacing(10)
        
        pyinstaller_file_section = QGroupBox("选择PyInstaller打包的可执行文件")
        pyinstaller_file_section.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #F5A742;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        pyinstaller_file_layout = QHBoxLayout()
        
        self.pyinstaller_file_label = QLabel("未选择文件")
        self.pyinstaller_browse_button = QPushButton("浏览...")
        self.pyinstaller_browse_button.setStyleSheet(self.get_button_style())
        self.pyinstaller_browse_button.clicked.connect(self.browse_pyinstaller_file)
        
        pyinstaller_file_layout.addWidget(self.pyinstaller_file_label, 1)
        pyinstaller_file_layout.addWidget(self.pyinstaller_browse_button)
        pyinstaller_file_section.setLayout(pyinstaller_file_layout)
        
        version_detect_section = QGroupBox("Python版本检测")
        version_detect_section.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #F5A742;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        version_detect_layout = QVBoxLayout()
        
        detect_button_layout = QHBoxLayout()
        self.detect_python_version_button = QPushButton("检测Python版本")
        self.detect_python_version_button.setStyleSheet(self.get_button_style())
        self.detect_python_version_button.clicked.connect(self.detect_python_version)
        self.detect_python_version_button.setEnabled(False)
        
        detect_button_layout.addWidget(self.detect_python_version_button)
        detect_button_layout.addStretch()
        
        self.detected_version_label = QLabel("未检测")
        self.detected_version_label.setStyleSheet("""
            QLabel {
                padding: 8px;
                background-color: #FFFFFF;
                border: 1px solid #F5A742;
                border-radius: 4px;
                color: #333333;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 10pt;
            }
        """)
        
        version_detect_layout.addLayout(detect_button_layout)
        version_detect_layout.addWidget(QLabel("检测到的Python版本:"))
        version_detect_layout.addWidget(self.detected_version_label)
        
        version_detect_section.setLayout(version_detect_layout)
        
        version_tip_label = QLabel("建议使用和程序相同的Python版本进行解包，以获得最佳结果！")
        version_tip_label.setStyleSheet("""
            color: #F5A742;
            font-weight: bold;
            padding: 5px;
            background-color: #FFF8EE;
            border: 1px dashed #F5A742;
            border-radius: 4px;
        """)
        
        pyinstaller_progress_section = QGroupBox("解包进度")
        pyinstaller_progress_section.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #F5A742;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        pyinstaller_progress_layout = QVBoxLayout()
        
        self.pyinstaller_progress_bar = QProgressBar()
        self.pyinstaller_progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #F5A742;
                border-radius: 4px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #F5A742;
            }
        """)
        self.pyinstaller_progress_bar.setValue(0)
        
        self.pyinstaller_progress_label = QLabel("就绪")
        
        pyinstaller_progress_layout.addWidget(self.pyinstaller_progress_bar)
        pyinstaller_progress_layout.addWidget(self.pyinstaller_progress_label)
        pyinstaller_progress_section.setLayout(pyinstaller_progress_layout)
        
        self.extract_pyinstaller_button = QPushButton("解包PyInstaller程序")
        self.extract_pyinstaller_button.setStyleSheet(self.get_button_style())
        self.extract_pyinstaller_button.clicked.connect(self.extract_pyinstaller)
        self.extract_pyinstaller_button.setEnabled(False)
        
        pyinstaller_results_section = QGroupBox("解包结果")
        pyinstaller_results_section.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #F5A742;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        pyinstaller_results_layout = QVBoxLayout()
        
        self.pyinstaller_results_text = QTextEdit()
        self.pyinstaller_results_text.setReadOnly(True)
        self.pyinstaller_results_text.setFont(QFont("Courier", 10))
        self.pyinstaller_results_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #F5A742;
                border-radius: 4px;
                padding: 5px;
                background-color: #FFFFFF;
                color: #333333;
            }
        """)
        
        pyinstaller_results_layout.addWidget(self.pyinstaller_results_text)
        pyinstaller_results_section.setLayout(pyinstaller_results_layout)
        
        pyinstaller_layout.addWidget(pyinstaller_file_section)
        pyinstaller_layout.addWidget(version_detect_section)
        pyinstaller_layout.addWidget(version_tip_label)
        pyinstaller_layout.addWidget(pyinstaller_progress_section)
        pyinstaller_layout.addWidget(self.extract_pyinstaller_button)
        pyinstaller_layout.addWidget(pyinstaller_results_section, 1)
        
        pyarmor_tab = QWidget()
        pyarmor_layout = QVBoxLayout(pyarmor_tab)
        pyarmor_layout.setSpacing(10)
        
        pyarmor_file_section = QGroupBox("选择Pyarmor加密的目录")
        pyarmor_file_section.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #F5A742;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        pyarmor_file_layout = QHBoxLayout()
        
        self.pyarmor_file_label = QLabel("未选择目录")
        self.pyarmor_browse_dir_button = QPushButton("选择目录")
        self.pyarmor_browse_dir_button.setStyleSheet(self.get_button_style())
        self.pyarmor_browse_dir_button.clicked.connect(self.browse_pyarmor_directory)
        
        pyarmor_file_layout.addWidget(self.pyarmor_file_label, 1)
        pyarmor_file_layout.addWidget(self.pyarmor_browse_dir_button)
        pyarmor_file_section.setLayout(pyarmor_file_layout)
        
        pyarmor_version_detect_section = QGroupBox("Python版本检测")
        pyarmor_version_detect_section.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #F5A742;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        pyarmor_version_detect_layout = QVBoxLayout()
        
        pyarmor_detect_button_layout = QHBoxLayout()
        self.detect_pyarmor_python_version_button = QPushButton("检测Python版本")
        self.detect_pyarmor_python_version_button.setStyleSheet(self.get_button_style())
        self.detect_pyarmor_python_version_button.clicked.connect(self.detect_pyarmor_python_version)
        self.detect_pyarmor_python_version_button.setEnabled(False)
        
        pyarmor_detect_button_layout.addWidget(self.detect_pyarmor_python_version_button)
        pyarmor_detect_button_layout.addStretch()
        
        self.detected_pyarmor_version_label = QLabel("未检测")
        self.detected_pyarmor_version_label.setStyleSheet("""
            QLabel {
                padding: 8px;
                background-color: #FFFFFF;
                border: 1px solid #F5A742;
                border-radius: 4px;
                color: #333333;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 10pt;
            }
        """)
        
        pyarmor_version_detect_layout.addLayout(pyarmor_detect_button_layout)
        pyarmor_version_detect_layout.addWidget(QLabel("检测到的Python版本:"))
        pyarmor_version_detect_layout.addWidget(self.detected_pyarmor_version_label)
        
        pyarmor_version_detect_section.setLayout(pyarmor_version_detect_layout)
        
        pyarmor_tip_label = QLabel("支持Pyarmor 8.0-9.1.x版本，Python 3.7-3.13。")
        pyarmor_tip_label.setStyleSheet("""
            color: #F5A742;
            font-weight: bold;
            padding: 5px;
            background-color: #FFF8EE;
            border: 1px dashed #F5A742;
            border-radius: 4px;
        """)
        
        pyarmor_header_section = QGroupBox("头部修复选项")
        pyarmor_header_section.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #F5A742;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        pyarmor_header_layout = QVBoxLayout()
        
        self.pyarmor_header_fix_checkbox = QCheckBox("自动检测并修复缺失的PY000000头部")
        self.pyarmor_header_fix_checkbox.setChecked(True)
        self.pyarmor_header_fix_checkbox.setStyleSheet("""
            QCheckBox {
                spacing: 5px;
            }
            QCheckBox::indicator {
                width: 15px;
                height: 15px;
            }
            QCheckBox::indicator:unchecked {
                border: 2px solid #F5A742;
                border-radius: 8px;
                background-color: #FFFFFF;
            }
            QCheckBox::indicator:checked {
                border: 2px solid #F5A742;
                border-radius: 8px;
                background-color: #FF9966;
            }
        """)
        
        
        pyarmor_header_layout.addWidget(self.pyarmor_header_fix_checkbox)
        pyarmor_header_section.setLayout(pyarmor_header_layout)
        
        pyarmor_progress_section = QGroupBox("解包进度")
        pyarmor_progress_section.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #F5A742;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        pyarmor_progress_layout = QVBoxLayout()
        
        self.pyarmor_progress_bar = QProgressBar()
        self.pyarmor_progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #F5A742;
                border-radius: 4px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #F5A742;
            }
        """)
        self.pyarmor_progress_bar.setValue(0)
        
        self.pyarmor_progress_label = QLabel("就绪")
        
        pyarmor_progress_layout.addWidget(self.pyarmor_progress_bar)
        pyarmor_progress_layout.addWidget(self.pyarmor_progress_label)
        pyarmor_progress_section.setLayout(pyarmor_progress_layout)
        
        self.unpack_pyarmor_button = QPushButton("解包Pyarmor程序")
        self.unpack_pyarmor_button.setStyleSheet(self.get_button_style())
        self.unpack_pyarmor_button.clicked.connect(self.unpack_pyarmor)
        self.unpack_pyarmor_button.setEnabled(False)
        
        pyarmor_results_section = QGroupBox("解包结果")
        pyarmor_results_section.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #F5A742;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        pyarmor_results_layout = QVBoxLayout()
        
        self.pyarmor_results_text = QTextEdit()
        self.pyarmor_results_text.setReadOnly(True)
        self.pyarmor_results_text.setFont(QFont("Courier", 10))
        self.pyarmor_results_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #F5A742;
                border-radius: 4px;
                padding: 5px;
                background-color: #FFFFFF;
                color: #333333;
            }
        """)
        
        pyarmor_results_layout.addWidget(self.pyarmor_results_text)
        pyarmor_results_section.setLayout(pyarmor_results_layout)
        
        pyarmor_layout.addWidget(pyarmor_file_section)
        pyarmor_layout.addWidget(pyarmor_version_detect_section)
        pyarmor_layout.addWidget(pyarmor_tip_label)
        pyarmor_layout.addWidget(pyarmor_header_section)
        pyarmor_layout.addWidget(pyarmor_progress_section)
        pyarmor_layout.addWidget(self.unpack_pyarmor_button)
        pyarmor_layout.addWidget(pyarmor_results_section, 1)

        magic_fix_tab = QWidget()
        magic_fix_layout = QVBoxLayout(magic_fix_tab)
        magic_fix_layout.setSpacing(10)
        
        magic_file_section = QGroupBox("选择需要修复的PYC文件")
        magic_file_section.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #F5A742;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        magic_file_layout = QHBoxLayout()
        
        self.magic_file_label = QLabel("未选择文件")
        self.magic_browse_button = QPushButton("浏览...")
        self.magic_browse_button.setStyleSheet(self.get_button_style())
        self.magic_browse_button.clicked.connect(self.browse_magic_file)
        
        magic_file_layout.addWidget(self.magic_file_label, 1)
        magic_file_layout.addWidget(self.magic_browse_button)
        magic_file_section.setLayout(magic_file_layout)
        
        magic_decompiler_section = QGroupBox("反编译器选择")
        magic_decompiler_section.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #F5A742;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        magic_decompiler_layout = QVBoxLayout()
        
        self.magic_decompiler_combo = QComboBox()
        self.magic_decompiler_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #F5A742;
                border-radius: 4px;
                padding: 5px;
                background-color: #FFFFFF;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 15px;
                border-left-width: 1px;
                border-left-color: #F5A742;
                border-left-style: solid;
                border-top-right-radius: 3px;
                border-bottom-right-radius: 3px;
            }
        """)
        self.magic_decompiler_combo.addItems(["pycdc", "uncompyle6", "decompyle3"])
        magic_decompiler_layout.addWidget(self.magic_decompiler_combo)
        
        pycdc_tip_label = QLabel("对于>3.8版本的pyc，请在修复后自行使用pylingual反编译或dis/pycdas反汇编")
        pycdc_tip_label.setStyleSheet("""
            color: #F5A742;
            font-weight: bold;
            padding: 5px;
            background-color: #FFF8EE;
            border: 1px dashed #F5A742;
            border-radius: 4px;
        """)
        magic_decompiler_layout.addWidget(pycdc_tip_label)
        
        magic_decompiler_section.setLayout(magic_decompiler_layout)
        
        magic_options_section = QGroupBox("修复选项")
        magic_options_section.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #F5A742;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        magic_options_layout = QVBoxLayout()
        
        self.magic_autodetect_checkbox = QCheckBox("自动检测错误类型")
        self.magic_autodetect_checkbox.setStyleSheet("""
            QCheckBox {
                spacing: 5px;
            }
            QCheckBox::indicator {
                width: 15px;
                height: 15px;
            }
            QCheckBox::indicator:unchecked {
                border: 2px solid #F5A742;
                border-radius: 8px;
                background-color: #FFFFFF;
            }
            QCheckBox::indicator:checked {
                border: 2px solid #F5A742;
                border-radius: 8px;
                background-color: #FF9966;
            }
        """)
        self.magic_autodetect_checkbox.setChecked(True)
        magic_options_layout.addWidget(self.magic_autodetect_checkbox)
        
        magic_type_group = QGroupBox("错误类型")
        magic_type_layout = QVBoxLayout()
        
        self.magic_type_group = QButtonGroup(self)
        
        self.magic_type_wrong = QRadioButton("错误的魔数头（替换前4字节）")
        self.magic_type_missing = QRadioButton("缺失魔数头（半缺失:4字节，全缺失:py3.0-3.2:8字节/py3.3-3.6:12字节/py3.7+:16字节）")
        
        radio_style = """
            QRadioButton {
                spacing: 5px;
            }
            QRadioButton::indicator {
                width: 15px;
                height: 15px;
            }
            QRadioButton::indicator:unchecked {
                border: 2px solid #F5A742;
                border-radius: 8px;
                background-color: #FFFFFF;
            }
            QRadioButton::indicator:checked {
                border: 2px solid #F5A742;
                border-radius: 8px;
                background-color: #FF9966;
            }
        """
        self.magic_type_wrong.setStyleSheet(radio_style)
        self.magic_type_missing.setStyleSheet(radio_style)
        
        self.magic_type_group.addButton(self.magic_type_wrong, 1)
        self.magic_type_group.addButton(self.magic_type_missing, 2)
        
        self.magic_type_wrong.setChecked(True)
        
        magic_type_layout.addWidget(self.magic_type_wrong)
        magic_type_layout.addWidget(self.magic_type_missing)
        
        magic_type_group.setLayout(magic_type_layout)
        magic_type_group.setEnabled(False)
        
        self.magic_autodetect_checkbox.toggled.connect(lambda checked: magic_type_group.setEnabled(not checked))
        
        magic_options_layout.addWidget(magic_type_group)
        
        self.magic_save_checkbox = QCheckBox("保存修复后的文件")
        self.magic_save_checkbox.setStyleSheet("""
            QCheckBox {
                spacing: 5px;
            }
            QCheckBox::indicator {
                width: 15px;
                height: 15px;
            }
            QCheckBox::indicator:unchecked {
                border: 2px solid #F5A742;
                border-radius: 8px;
                background-color: #FFFFFF;
            }
            QCheckBox::indicator:checked {
                border: 2px solid #F5A742;
                border-radius: 8px;
                background-color: #FF9966;
            }
        """)
        self.magic_save_checkbox.setChecked(True)
        magic_options_layout.addWidget(self.magic_save_checkbox)
        
        magic_options_section.setLayout(magic_options_layout)
        
        magic_progress_section = QGroupBox("修复进度")
        magic_progress_section.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #F5A742;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        magic_progress_layout = QVBoxLayout()
        
        self.magic_progress_bar = QProgressBar()
        self.magic_progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #F5A742;
                border-radius: 4px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #F5A742;
            }
        """)
        self.magic_progress_bar.setValue(0)
        
        self.magic_progress_label = QLabel("就绪")
        
        magic_progress_layout.addWidget(self.magic_progress_bar)
        magic_progress_layout.addWidget(self.magic_progress_label)
        
        magic_progress_section.setLayout(magic_progress_layout)
        
        magic_version_section = QGroupBox("修复结果版本")
        magic_version_section.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #F5A742;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        magic_version_layout = QVBoxLayout()
        
        version_detect_layout = QHBoxLayout()
        version_detect_layout.addWidget(QLabel("检测到的Python版本:"))
        
        self.magic_detected_version_label = QLabel("未检测")
        self.magic_detected_version_label.setStyleSheet("""
            QLabel {
                padding: 8px;
                background-color: #FFFFFF;
                border: 1px solid #F5A742;
                border-radius: 4px;
                color: #333333;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 10pt;
            }
        """)
        
        version_detect_layout.addWidget(self.magic_detected_version_label)
        magic_version_layout.addLayout(version_detect_layout)
        
        magic_version_section.setLayout(magic_version_layout)
        
        self.magic_fix_button = QPushButton("修复魔数头")
        self.magic_fix_button.setStyleSheet(self.get_button_style())
        self.magic_fix_button.clicked.connect(self.fix_magic_number)
        self.magic_fix_button.setEnabled(False)
        
        magic_results_section = QGroupBox("修复结果")
        magic_results_section.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #F5A742;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        magic_results_layout = QVBoxLayout()
        
        self.magic_results_text = QTextEdit()
        self.magic_results_text.setReadOnly(True)
        self.magic_results_text.setFont(QFont("Courier", 10))
        self.magic_results_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #F5A742;
                border-radius: 4px;
                padding: 5px;
                background-color: #FFFFFF;
                color: #333333;
            }
        """)
        
        magic_results_layout.addWidget(self.magic_results_text)
        magic_results_section.setLayout(magic_results_layout)
        
        magic_fix_layout.addWidget(magic_file_section)
        magic_fix_layout.addWidget(magic_decompiler_section)
        magic_fix_layout.addWidget(magic_options_section)
        magic_fix_layout.addWidget(magic_progress_section)
        magic_fix_layout.addWidget(magic_version_section)
        magic_fix_layout.addWidget(self.magic_fix_button)
        magic_fix_layout.addWidget(magic_results_section, 1)
        
        stego_tab = QWidget()
        stego_layout = QVBoxLayout(stego_tab)
        stego_layout.setSpacing(10)
        
        stego_file_section = QGroupBox("选择PYC文件")
        stego_file_section.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #F5A742;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        stego_file_layout = QHBoxLayout()
        
        self.stego_file_label = QLabel("未选择文件")
        self.stego_browse_button = QPushButton("浏览...")
        self.stego_browse_button.setStyleSheet(self.get_button_style())
        self.stego_browse_button.clicked.connect(self.browse_stego_file)
        
        stego_file_layout.addWidget(self.stego_file_label, 1)
        stego_file_layout.addWidget(self.stego_browse_button)
        stego_file_section.setLayout(stego_file_layout)
        
        self.stego_execute_button = QPushButton("提取隐藏数据")
        self.stego_execute_button.setStyleSheet(self.get_button_style())
        self.stego_execute_button.clicked.connect(self.execute_stego_operation)
        self.stego_execute_button.setEnabled(False)
        
        stego_results_section = QGroupBox("执行结果")
        stego_results_section.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #F5A742;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        stego_results_layout = QVBoxLayout()
        
        self.stego_results_text = QTextEdit()
        self.stego_results_text.setReadOnly(True)
        self.stego_results_text.setFont(QFont("Courier", 10))
        self.stego_results_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #F5A742;
                border-radius: 4px;
                padding: 5px;
                background-color: #FFFFFF;
                color: #333333;
            }
        """)
        
        stego_results_layout.addWidget(self.stego_results_text)
        stego_results_section.setLayout(stego_results_layout)
        
        stego_layout.addWidget(stego_file_section)
        stego_layout.addWidget(self.stego_execute_button)
        stego_layout.addWidget(stego_results_section, 1)
        
        pylingual_tab = QWidget()
        pylingual_layout = QVBoxLayout(pylingual_tab)
        pylingual_layout.setSpacing(10)
        
        pylingual_file_section = QGroupBox("文件选择")
        pylingual_file_section.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #F5A742;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        pylingual_file_layout = QHBoxLayout()
        
        self.pylingual_file_path_label = QLabel("未选择文件")
        self.pylingual_browse_button = QPushButton("浏览...")
        self.pylingual_browse_button.setStyleSheet(self.get_button_style())
        self.pylingual_browse_button.clicked.connect(self.browse_pylingual_file)
        
        pylingual_file_layout.addWidget(self.pylingual_file_path_label, 1)
        pylingual_file_layout.addWidget(self.pylingual_browse_button)
        pylingual_file_section.setLayout(pylingual_file_layout)
        
        pylingual_website_label = QLabel('<a href="https://pylingual.io" style="color: #F5A742; text-decoration: none;">在线使用 PyLingual: https://pylingual.io</a>')
        pylingual_website_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pylingual_website_label.setOpenExternalLinks(True)
        pylingual_website_label.setCursor(Qt.CursorShape.PointingHandCursor)
        pylingual_website_label.setStyleSheet("""
            QLabel {
                font-size: 10pt;
                font-weight: bold;
                font-family: '微软雅黑', Arial, sans-serif;
                padding: 5px;
                border-radius: 6px;
                background-color: #FFF8F0;
                border: 2px solid #F5A742;
                margin: 5px 0px;
            }
            QLabel:hover {
                background-color: #FFF0E6;
                border: 2px solid #FF9966;
            }
        """)
        
        pylingual_options_section = QGroupBox("选项")
        pylingual_options_section.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #F5A742;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        pylingual_options_layout = QVBoxLayout()
        
        self.pylingual_save_checkbox = QCheckBox("将结果保存到.py文件")
        self.pylingual_save_checkbox.setStyleSheet("""
            QCheckBox {
                spacing: 5px;
            }
            QCheckBox::indicator {
                width: 15px;
                height: 15px;
            }
            QCheckBox::indicator:unchecked {
                border: 2px solid #F5A742;
                border-radius: 8px;
                background-color: #FFFFFF;
            }
            QCheckBox::indicator:checked {
                border: 2px solid #F5A742;
                border-radius: 8px;
                background-color: #FF9966;
            }
        """)
        
        pylingual_options_layout.addWidget(self.pylingual_save_checkbox)
        pylingual_options_section.setLayout(pylingual_options_layout)
        
        self.pylingual_decompile_button = QPushButton("反编译")
        self.pylingual_decompile_button.setStyleSheet(self.get_button_style())
        self.pylingual_decompile_button.clicked.connect(self.pylingual_decompile)
        self.pylingual_decompile_button.setEnabled(False)
        
        self.pylingual_results_tab_widget = QTabWidget()
        self.pylingual_results_tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #F5A742;
                border-radius: 4px;
                padding: 5px;
            }
            QTabBar::tab {
                background-color: #FFF1DC;
                border: 1px solid #F5A742;
                border-bottom-color: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                padding: 6px 10px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #FFFFFF;
                border-bottom: none;
            }
            QTabBar::tab:!selected {
                margin-top: 2px;
            }
        """)
        
        progress_widget = QWidget()
        progress_layout = QVBoxLayout(progress_widget)
        
        self.pylingual_progress_text = QTextEdit()
        self.pylingual_progress_text.setReadOnly(True)
        self.pylingual_progress_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #F5A742;
                border-radius: 4px;
                padding: 5px;
                background-color: #FFFFFF;
                color: #333333;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 9pt;
            }
        """)
        
        progress_layout.addWidget(self.pylingual_progress_text)
        
        result_widget = QWidget()
        result_layout = QVBoxLayout(result_widget)
        
        self.pylingual_results_text = QTextEdit()
        self.pylingual_results_text.setReadOnly(True)
        self.pylingual_results_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #F5A742;
                border-radius: 4px;
                padding: 5px;
                background-color: #FFFFFF;
                color: #333333;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 10pt;
            }
        """)
        
        result_layout.addWidget(self.pylingual_results_text)
        
        self.pylingual_results_tab_widget.addTab(progress_widget, "处理进度")
        self.pylingual_results_tab_widget.addTab(result_widget, "反编译结果")
        
        pylingual_layout.addWidget(pylingual_file_section)
        pylingual_layout.addWidget(pylingual_website_label)
        pylingual_layout.addWidget(pylingual_options_section)
        pylingual_layout.addWidget(self.pylingual_decompile_button)
        pylingual_layout.addWidget(self.pylingual_results_tab_widget, 1)
        
        self.tab_widget.addTab(single_tab, "反编译")
        self.tab_widget.addTab(batch_tab, "批量反编译")
        self.tab_widget.addTab(pylingual_tab, "PyLingual反编译")
        self.tab_widget.addTab(disasm_tab, "反汇编")
        self.tab_widget.addTab(batch_disasm_tab, "批量反汇编")
        self.tab_widget.addTab(pyinstaller_tab, "PyInstaller解包")
        self.tab_widget.addTab(pyarmor_tab, "Pyarmor解包")
        self.tab_widget.addTab(decrypt_tab, "PYC解密")
        self.tab_widget.addTab(magic_fix_tab, "PYC魔数头修复")
        self.tab_widget.addTab(stego_tab, "PYC隐写")
        
        main_layout.addWidget(self.tab_widget)
    
    def get_button_style(self):
        return """
            QPushButton {
                background-color: #F5A742;
                color: white;
                border-radius: 5px;
                padding: 5px 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #F7B95B;
            }
            QPushButton:pressed {
                background-color: #E09536;
            }
            QPushButton:disabled {
                background-color: #D3D3D3;
                color: #A9A9A9;
            }
        """
        
    def set_style(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #FFF8EE;
            }
            QWidget {
                background-color: #FFF8EE;
                color: #333333;
                font-family: '微软雅黑', Arial, sans-serif;
                font-size: 10pt;
            }
            QLabel {
                color: #333333;
            }
        """)
        
    def add_logo(self):
        self.logo_frame = AnimatedLogoFrame(self)
        self.logo_frame.setObjectName("logoFrame")
        
        logo_size = 75
        frame_size = logo_size + 10
        self.logo_frame.setFixedSize(frame_size, frame_size)
        
        self.logo_frame.original_size = QSize(frame_size, frame_size)
        
        self.logo_frame.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self.logo_label = QLabel(self.logo_frame)
        self.logo_label.setObjectName("logoLabel")
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.logo_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.logo_label.mousePressEvent = self.logo_clicked
        
        self.logo_frame.logo_label = self.logo_label
        
        self.logo_label.move(5, 5)
        self.logo_label.setFixedSize(logo_size, logo_size)
        
        logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "image", "logo.png")
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            pixmap = pixmap.scaled(logo_size, logo_size,
                                  Qt.AspectRatioMode.KeepAspectRatio,
                                  Qt.TransformationMode.SmoothTransformation)
            self.logo_label.setPixmap(pixmap)
            
            base_style = """
                #logoFrame {
                    background: qradialgradient(
                        cx: 0.5, cy: 0.5, radius: 0.8, 
                        fx: 0.5, fy: 0.5, 
                        stop: 0 rgba(245, 167, 66, 100), 
                        stop: 0.7 rgba(245, 167, 66, 60), 
                        stop: 1 rgba(245, 167, 66, 0)
                    );
                    border: 2px solid rgba(245, 167, 66, 150);
                    border-radius: """ + str(frame_size//2) + """px;
                }
                #logoLabel {
                    background-color: transparent;
                    opacity: 1.0;
                }
            """
            
            self.logo_frame.base_style = base_style
            self.logo_frame.setStyleSheet(base_style)
            
            shadow = QGraphicsDropShadowEffect(self)
            shadow.setBlurRadius(15)
            shadow.setColor(QColor(0, 0, 0, 40))
            shadow.setOffset(2, 2)
            self.logo_label.setGraphicsEffect(shadow)
            
            self.logo_frame.setParent(self)
            self.resizeEvent = self.on_resize
            self.position_logo()
    
    def logo_clicked(self, event):
        self.show_about_dialog()
    
    def on_resize(self, event):
        self.position_logo()
        super().resizeEvent(event)
    
    def position_logo(self):
        margin_right = 10
        margin_top = 5
        self.logo_frame.move(self.width() - self.logo_frame.width() - margin_right, margin_top)
        self.logo_frame.raise_()
    
    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择PYC文件", "", "Python字节码文件 (*.pyc);;所有文件 (*)"
        )
        
        if file_path:
            self.file_path_label.setText(normalize_path_for_display(file_path))
            self.decompile_button.setEnabled(True)
    
    def browse_pylingual_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择PYC文件", "", "Python字节码文件 (*.pyc);;所有文件 (*)"
        )
        
        if file_path:
            self.pylingual_file_path_label.setText(normalize_path_for_display(file_path))
            self.pylingual_decompile_button.setEnabled(True)
    
    def browse_batch_files(self):
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "选择多个PYC文件", "", "Python字节码文件 (*.pyc);;所有文件 (*)"
        )
        
        if file_paths:
            self.batch_files.extend(file_paths)
            self.update_batch_files_list()
            self.batch_decompile_button.setEnabled(len(self.batch_files) > 0)
            self.batch_stop_button.setEnabled(False)
    
    def browse_batch_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "选择包含PYC文件的文件夹")
        
        if directory:
            self.batch_base_dir = directory
            pyc_files = get_files_with_extension(directory, ['.pyc'])
            if pyc_files:
                self.batch_files.extend(pyc_files)
                self.update_batch_files_list()
                self.batch_decompile_button.setEnabled(len(self.batch_files) > 0)
                self.batch_stop_button.setEnabled(False)
                self.show_info("文件查找结果", f"在所选文件夹中找到 {len(pyc_files)} 个PYC文件")
            else:
                self.show_info("文件查找结果", "在所选文件夹中未找到PYC文件")
    
    def browse_encrypted_files(self):
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "选择加密的PYC文件", "", "加密的PYC文件 (*.pyc.encrypted);;所有文件 (*)"
        )
        
        if file_paths:
            self.encrypted_files.extend(file_paths)
            self.update_encrypted_files_list()
            self.decrypt_button.setEnabled(len(self.encrypted_files) > 0 and DECRYPTION_AVAILABLE)
    
    def browse_encrypted_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "选择包含加密PYC文件的文件夹")
        
        if directory:
            self.encrypted_base_dir = directory
            encrypted_files = get_files_with_extension(directory, ['.pyc.encrypted'])
            if encrypted_files:
                self.encrypted_files.extend(encrypted_files)
                self.update_encrypted_files_list()
                self.decrypt_button.setEnabled(len(self.encrypted_files) > 0 and DECRYPTION_AVAILABLE)
                self.show_info("文件查找结果", f"在所选文件夹中找到 {len(encrypted_files)} 个加密的PYC文件")
            else:
                self.show_info("文件查找结果", "在所选文件夹中未找到加密的PYC文件")
                self.decrypt_button.setEnabled(False)
    
    def clear_batch_files(self):
        self.batch_files.clear()
        self.update_batch_files_list()
        self.batch_decompile_button.setEnabled(False)
    
    def clear_encrypted_files(self):
        self.encrypted_files.clear()
        self.update_encrypted_files_list()
        self.decrypt_button.setEnabled(False)
    
    def update_batch_files_list(self):
        self.batch_files_list.clear()
        for file_path in self.batch_files:
            self.batch_files_list.addItem(normalize_path_for_display(file_path))
    
    def update_encrypted_files_list(self):
        self.encrypted_files_list.clear()
        for file_path in self.encrypted_files:
            self.encrypted_files_list.addItem(normalize_path_for_display(file_path))
    
    def decompile(self):
        pyc_file = self.file_path_label.text()
        if not os.path.exists(pyc_file):
            self.show_error("文件未找到", "所选文件不存在。")
            return
        
        decompiler = self.decompiler_combo.currentText()
        save_output = self.save_checkbox.isChecked()
        
        try:
            result = self.run_decompiler(pyc_file, decompiler)
            self.results_text.setText(result)
            
            if save_output and result:
                decompile_output_dir = os.path.join(os.path.dirname(pyc_file), "decompile_output")
                if not os.path.exists(decompile_output_dir):
                    os.makedirs(decompile_output_dir)
                
                output_filename = os.path.basename(os.path.splitext(pyc_file)[0]) + '.py'
                output_file = os.path.join(decompile_output_dir, output_filename)
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(result)
                self.show_info("文件已保存", f"输出已保存到 {normalize_path_for_display(output_file)}")
                
        except Exception as e:
            self.show_error("反编译错误", str(e))
    
    def pylingual_decompile(self):
        pyc_file = self.pylingual_file_path_label.text()
        if not os.path.exists(pyc_file):
            self.show_error("文件未找到", "所选文件不存在。")
            return
        
        save_output = self.pylingual_save_checkbox.isChecked()
        
        self.pylingual_progress_text.clear()
        self.pylingual_results_text.clear()
        
        self.pylingual_results_tab_widget.setCurrentIndex(0)
        
        self.pylingual_decompile_button.setEnabled(False)
        self.pylingual_decompile_button.setText("正在处理...")
        
        try:
            self.pylingual_progress_text.append("开始PyLingual反编译...")
            self.pylingual_progress_text.append(f"文件: {normalize_path_for_display(pyc_file)}")
            self.pylingual_progress_text.append("=" * 50)
            QApplication.processEvents()
            
            result = self.run_pylingual_with_progress(pyc_file)
            
            if result:
                self.pylingual_results_text.setText(result)
                self.pylingual_progress_text.append("\n✓ 反编译完成!")
                
                self.pylingual_results_tab_widget.setCurrentIndex(1)
                
                if save_output:
                    decompile_output_dir = os.path.join(os.path.dirname(pyc_file), "decompile_output")
                    if not os.path.exists(decompile_output_dir):
                        os.makedirs(decompile_output_dir)
                    
                    output_filename = os.path.basename(os.path.splitext(pyc_file)[0]) + '.py'
                    output_file = os.path.join(decompile_output_dir, output_filename)
                    
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(result)
                    
                    self.pylingual_progress_text.append(f"✓ 文件已保存到: {normalize_path_for_display(output_file)}")
                    self.show_info("文件已保存", f"输出已保存到 {normalize_path_for_display(output_file)}")
            else:
                self.pylingual_progress_text.append("\n✗ 反编译失败: 未获得结果")
                self.show_error("反编译失败", "PyLingual未能成功反编译该文件")
                
        except Exception as e:
            self.pylingual_progress_text.append(f"\n✗ 反编译出错: {str(e)}")
            self.show_error("反编译错误", str(e))
        
        finally:
            self.pylingual_decompile_button.setEnabled(True)
            self.pylingual_decompile_button.setText("反编译")
    
    def stop_batch_decompile(self):
        self.batch_stop_flag = True
        self.progress_label.setText("正在终止...")
        self.batch_stop_button.setEnabled(False)
    
    def batch_decompile(self):
        if not self.batch_files:
            self.show_error("没有文件", "请先选择要反编译的PYC文件。")
            return
        
        self.batch_stop_flag = False
        
        self.batch_decompile_button.setEnabled(False)
        self.batch_stop_button.setEnabled(True)
        
        decompiler = self.batch_decompiler_combo.currentText()
        total_files = len(self.batch_files)
        success_count = 0
        failed_files = []
        
        self.progress_bar.setValue(0)
        self.progress_label.setText("正在反编译...")
        
       
        if hasattr(self, 'batch_base_dir'):
            extract_base_dir = os.path.join(os.path.dirname(self.batch_base_dir), "decompile_output")
        else:
            extract_base_dir = os.path.join(os.path.dirname(self.batch_files[0]), "decompile_output")
        
        for i, pyc_file in enumerate(self.batch_files):
            if self.batch_stop_flag:
                self.progress_label.setText("已终止")
                break
                
            try:
                self.progress_label.setText(f"正在反编译 ({i+1}/{total_files}): {normalize_path_for_display(os.path.basename(pyc_file))}")
                QApplication.processEvents()
                
                if not os.path.exists(pyc_file):
                    failed_files.append((pyc_file, "文件不存在"))
                    continue
                
                result = self.run_decompiler(pyc_file, decompiler)
                if result:
                    if hasattr(self, 'batch_base_dir'):
                        rel_path = os.path.relpath(os.path.dirname(pyc_file), self.batch_base_dir)
                        if rel_path == '.':
                            rel_path = ''
                        output_dir = os.path.join(extract_base_dir, rel_path)
                    else:
                        output_dir = extract_base_dir
                    
                    if not os.path.exists(output_dir):
                        os.makedirs(output_dir)
                    
                    output_filename = os.path.basename(os.path.splitext(pyc_file)[0]) + '.py'
                    output_file = os.path.join(output_dir, output_filename)
                    
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(result)
                    success_count += 1
                else:
                    failed_files.append((pyc_file, "反编译结果为空"))
            
            except Exception as e:
                failed_files.append((pyc_file, str(e)))
            
            finally:
                
                progress = int((i + 1) / total_files * 100)
                self.progress_bar.setValue(progress)
                QApplication.processEvents()
        
        
        self.batch_decompile_button.setEnabled(True)
        self.batch_stop_button.setEnabled(False)
        
        if self.batch_stop_flag:
            self.progress_label.setText("已终止")
            self.show_info("批量反编译终止", f"已处理 {success_count}/{total_files} 个文件后终止。")
        else:
            self.progress_label.setText("反编译完成")
            if failed_files:
                error_message = f"成功: {success_count}/{total_files}\n\n失败的文件:\n"
                for file_path, error in failed_files:
                    error_message += f"- {normalize_path_for_display(os.path.basename(file_path))}: {error}\n"
                self.show_error("批量反编译结果", error_message)
            else:
                result_msg = f"批量反编译完成！\n成功: {success_count}, 失败: {len(failed_files)}"
                if success_count > 0:
                    result_msg += f"\n\n输出目录: {normalize_path_for_display(extract_base_dir)}"
                self.show_info("批量反编译完成", result_msg)
    
    def decrypt_pyc_files(self):
        if not self.encrypted_files:
            self.show_error("没有文件", "请先选择要解密的PYC文件。")
            return
        
        key = self.decrypt_key_input.text()
        if not key:
            self.show_error("密钥错误", "请输入解密密钥。")
            return
        
        key_bytes = key.encode('utf-8')
        python_version = self.python_version_combo.currentText()
        use_lt4 = self.pyinstaller_lt4_radio.isChecked()
        
        total_files = len(self.encrypted_files)
        success_count = 0
        failed_files = []
        
        self.decrypt_progress_bar.setValue(0)
        self.decrypt_progress_label.setText("正在解密...")
        QApplication.processEvents()
        
        if hasattr(self, 'encrypted_base_dir'):
            extract_base_dir = os.path.join(os.path.dirname(self.encrypted_base_dir), "extract_de")
        else:
            extract_base_dir = os.path.join(os.path.dirname(self.encrypted_files[0]), "extract_de")
        
        try:
            if use_lt4:
                from Decryptor.decrypt_pyinstaller_lt4 import MAGIC_HEADERS
                from Crypto.Cipher import AES
                CRYPT_BLOCK_SIZE = 16
            else:
                import tinyaes
                from Decryptor.decrypt_pyinstaller_ge4 import MAGIC_HEADERS
                CRYPT_BLOCK_SIZE = 16
        except ImportError as e:
            error_msg = "解密 PyInstaller < 4.0 文件需要 pycryptodome 库。" if use_lt4 else "解密 PyInstaller >= 4.0 文件需要 tinyaes 库。"
            self.show_error("依赖缺失", error_msg)
            self.decrypt_progress_label.setText("解密中止")
            return
        
        def process_single_file(encrypted_file):
            try:
                if not os.path.exists(encrypted_file):
                    return False, "文件不存在"
                
                if hasattr(self, 'encrypted_base_dir'):
                    rel_path = os.path.relpath(os.path.dirname(encrypted_file), self.encrypted_base_dir)
                    if rel_path == '.':
                        rel_path = ''
                    output_dir = os.path.join(extract_base_dir, rel_path)
                else:
                    output_dir = extract_base_dir
                
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)
                
                base_name = os.path.basename(encrypted_file)
                if base_name.endswith('.pyc.encrypted'):
                    output_name = base_name[:-10]
                else:
                    output_name = base_name + ".decrypted"
                
                output_path = os.path.join(output_dir, output_name)
                
                with open(encrypted_file, 'rb') as inf, open(output_path, 'wb') as outf:
                    iv = inf.read(CRYPT_BLOCK_SIZE)
                    
                    if use_lt4:
                        cipher = AES.new(key_bytes, AES.MODE_CFB, iv)
                        plaintext = zlib.decompress(cipher.decrypt(inf.read()))
                    else:
                        cipher = tinyaes.AES(key_bytes, iv)
                        plaintext = zlib.decompress(cipher.CTR_xcrypt_buffer(inf.read()))
                    
                    magic_header = MAGIC_HEADERS[python_version]
                    outf.write(magic_header)
                    
                    outf.write(plaintext)
                
                return True, None
                
            except Exception as e:
                return False, str(e)
        
        for i, encrypted_file in enumerate(self.encrypted_files):
            self.decrypt_progress_label.setText(f"正在解密 ({i+1}/{total_files}): {normalize_path_for_display(os.path.basename(encrypted_file))}")
            QApplication.processEvents()
            
            success, error = process_single_file(encrypted_file)
            
            if success:
                success_count += 1
            else:
                failed_files.append((encrypted_file, error))
            
            progress = int((i + 1) / total_files * 100)
            self.decrypt_progress_bar.setValue(progress)
            QApplication.processEvents()
        
        self.decrypt_progress_label.setText("解密完成")
        
        if failed_files:
            error_message = f"成功: {success_count}/{total_files}\n\n失败的文件:\n"
            for file_path, error in failed_files:
                error_message += f"- {normalize_path_for_display(os.path.basename(file_path))}: {error}\n"
            self.show_error("解密结果", error_message)
        else:
            self.show_info("解密结果", f"所有{total_files}个文件都已成功解密。")
    
    def run_decompiler(self, pyc_file, decompiler):
        if decompiler == "uncompyle6":
            return self.run_uncompyle6(pyc_file)
        elif decompiler == "decompyle3":
            return self.run_decompyle3(pyc_file)
        elif decompiler == "pycdc":
            return self.run_pycdc(pyc_file)
        elif decompiler == "pylingual":
            return self.run_pylingual(pyc_file)
        else:
            raise ValueError(f"未知的反编译器: {decompiler}")
    
    def run_uncompyle6(self, pyc_file):
        try:
            import uncompyle6
            from io import StringIO
            
            out_buffer = StringIO()
            uncompyle6.main.decompile_file(pyc_file, out_buffer)
            return out_buffer.getvalue()
        except ImportError:
            return self.run_as_subprocess(["uncompyle6", pyc_file])
    
    def run_decompyle3(self, pyc_file):
        try:
            import decompyle3
            from io import StringIO
            
            out_buffer = StringIO()
            decompyle3.main.decompile_file(pyc_file, out_buffer)
            return out_buffer.getvalue()
        except ImportError:
            return self.run_as_subprocess(["decompyle3", pyc_file])
    
    def run_pycdc(self, pyc_file):
        pycdc_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Decompiler", "pycdc")
        return self.run_as_subprocess([pycdc_path, pyc_file])
    
    
    def run_pylingual(self, pyc_file):
        try:
            import tempfile
            import shutil
            
            with tempfile.TemporaryDirectory() as temp_dir:
                cmd = ["pylingual", "-o", temp_dir, pyc_file]
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    encoding='utf-8',
                    errors='replace',
                    check=True,
                    shell=True
                )
                
                import glob
                py_files = glob.glob(os.path.join(temp_dir, "*.py"))
                
                if py_files:
                    with open(py_files[0], 'r', encoding='utf-8') as f:
                        return f.read()
                else:
                    return result.stderr if result.stderr else result.stdout
                    
        except subprocess.CalledProcessError as e:
            if e.stderr:
                raise Exception(e.stderr)
            else:
                raise Exception(f"pylingual执行失败，退出代码 {e.returncode}")
        except FileNotFoundError:
            raise Exception("找不到pylingual命令。请确保它已安装并添加到PATH中。")
        except Exception as e:
            raise Exception(f"pylingual执行出错: {str(e)}")
    
    def run_pylingual_with_progress(self, pyc_file):
        try:
            import tempfile
            import threading
            import time
            
            with tempfile.TemporaryDirectory() as temp_dir:
                self.pylingual_progress_text.append("创建临时工作目录...")
                QApplication.processEvents()
                
                cmd = ["pylingual", "-o", temp_dir, pyc_file]
                
                self.pylingual_progress_text.append(f"执行命令: {' '.join(cmd)}")
                self.pylingual_progress_text.append("正在启动PyLingual...")
                QApplication.processEvents()
                
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    encoding='utf-8',
                    errors='replace',
                    shell=True,
                    universal_newlines=True,
                    bufsize=1
                )
                
                output_lines = []
                while True:
                    line = process.stdout.readline()
                    if line:
                        line = line.strip()
                        if line:
                            self.pylingual_progress_text.append(line)
                            output_lines.append(line)
                            QApplication.processEvents()
                    
                    if process.poll() is not None:
                        break
                
                remaining_output = process.stdout.read()
                if remaining_output:
                    for line in remaining_output.strip().split('\n'):
                        if line.strip():
                            self.pylingual_progress_text.append(line.strip())
                            output_lines.append(line.strip())
                    QApplication.processEvents()
                
                return_code = process.wait()
                
                if return_code == 0:
                    self.pylingual_progress_text.append("PyLingual执行完成，正在查找输出文件...")
                    QApplication.processEvents()
                    
                    import glob
                    py_files = glob.glob(os.path.join(temp_dir, "*.py"))
                    
                    if py_files:
                        self.pylingual_progress_text.append(f"找到输出文件: {os.path.basename(py_files[0])}")
                        QApplication.processEvents()
                        
                        with open(py_files[0], 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        self.pylingual_progress_text.append("成功读取反编译结果")
                        return content
                    else:
                        self.pylingual_progress_text.append("警告: 未找到生成的.py文件")
                        return '\n'.join(output_lines) if output_lines else "未获得输出"
                else:
                    raise Exception(f"pylingual执行失败，退出代码 {return_code}")
                    
        except subprocess.TimeoutExpired:
            self.pylingual_progress_text.append("错误: PyLingual执行超时")
            raise Exception("PyLingual执行超时")
        except FileNotFoundError:
            self.pylingual_progress_text.append("错误: 找不到pylingual命令")
            raise Exception("找不到pylingual命令。请确保它已安装并添加到PATH中。")
        except Exception as e:
            self.pylingual_progress_text.append(f"错误: {str(e)}")
            raise Exception(f"pylingual执行出错: {str(e)}")
    
    def run_as_subprocess(self, cmd):
        try:
            result = subprocess.run(cmd, capture_output=True, encoding='utf-8', errors='replace', check=True)
            return result.stdout
        except subprocess.CalledProcessError as e:
            if e.stderr:
                raise Exception(e.stderr)
            else:
                raise Exception(f"命令 {' '.join(cmd)} 执行失败，退出代码 {e.returncode}")
        except FileNotFoundError:
            raise Exception(f"找不到命令 {cmd[0]}。请确保它已安装并添加到PATH中。")
    
    def show_error(self, title, message):
        QMessageBox.critical(self, title, message)
    
    def show_info(self, title, message):
        QMessageBox.information(self, title, message)
    
    def browse_disasm_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择PYC文件", "", "Python字节码文件 (*.pyc);;所有文件 (*)"
        )
        
        if file_path:
            self.disasm_file_path_label.setText(normalize_path_for_display(file_path))
            self.disasm_button.setEnabled(True)
    
    def disassemble(self):
        pyc_file = self.disasm_file_path_label.text()
        if not os.path.exists(pyc_file):
            self.show_error("文件未找到", "所选文件不存在。")
            return
        
        disasm_tool = self.disasm_tool_combo.currentText()
        
        try:
            self.disasm_results_text.clear()
            
            if disasm_tool == "dis模块":
                python_version_warning = self.check_python_version_compatibility(pyc_file)
                if python_version_warning:
                    reply = QMessageBox.question(
                        self,
                        "Python版本兼容性提示",
                        f"{python_version_warning}\n\n是否继续使用dis模块反汇编？",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.No
                    )
                    if reply == QMessageBox.StandardButton.No:
                        return
                
                result = self.run_dis_disassembly(pyc_file)
            elif disasm_tool == "pycdas":
                result = self.run_pycdas_disassembly(pyc_file)
            else:
                self.show_error("未知工具", f"未知的反汇编工具: {disasm_tool}")
                return
            
            self.disasm_results_text.setText(result)
            
            if self.disasm_save_checkbox.isChecked():
                self.save_disasm_result(pyc_file, result, disasm_tool)
                
        except Exception as e:
            self.show_error("反汇编错误", f"反汇编过程中发生错误: {str(e)}")
    
    def check_python_version_compatibility(self, pyc_file):
        try:
            with open(pyc_file, 'rb') as f:
                magic_bytes = f.read(4)
            
            current_version = f"{sys.version_info.major}.{sys.version_info.minor}"
            
            if magic_bytes in MAGIC_NUMBERS:
                pyc_version = MAGIC_NUMBERS[magic_bytes]
                
                if "Python" in pyc_version:
                    pyc_version_num = pyc_version.replace("Python ", "").strip()
                    
                    if pyc_version_num != current_version:
                        return (f"版本不匹配警告：\n"
                               f"• PYC文件版本: {pyc_version}\n"
                               f"• 当前Python版本: Python {current_version}\n\n"
                               f"建议使用与PYC文件相同版本的Python来获得最佳反汇编结果。\n"
                               f"版本不匹配可能导致反汇编失败或结果不准确。")
                else:
                    return (f"无法确定PYC文件的Python版本。\n"
                           f"当前Python版本: Python {current_version}\n\n"
                           f"建议确保使用正确的Python版本进行反汇编。")
            else:
                return (f"未知的魔数头，无法确定Python版本。\n"
                       f"当前Python版本: Python {current_version}\n\n"
                       f"dis模块可能无法正确解析此文件。")
                
        except Exception:
            return "无法读取文件魔数头，建议检查文件格式。"
        
        return None
    
    def run_dis_disassembly(self, pyc_file):
        with open(pyc_file, 'rb') as f:
            file_data = f.read()
            file_size = len(file_data)
            
            common_offsets = [0, 4, 8, 12, 16]
            success = False
            result = ""
            
            for offset in common_offsets:
                success, result, used_offset = self._try_dis_parse_with_offset(file_data, offset)
                if success:
                    break
            
            if not success:
                for offset in range(20, min(200, file_size), 4):
                    if offset not in common_offsets:
                        success, result, used_offset = self._try_dis_parse_with_offset(file_data, offset)
                        if success:
                            break
            
            if success:
                return result
            else:
                return "无法解析文件。可能原因：\n1. 文件格式不是有效的Python字节码\n2. 文件已被严重损坏或修改\n3. 需要尝试不同的偏移量或使用其他工具"
    
    def _try_dis_parse_with_offset(self, file_data, offset):
        try:
            if offset >= len(file_data):
                return False, "", offset
                
            data = file_data[offset:]
            
            code = marshal.loads(data)
            

            import io
            buffer = io.StringIO()
            
            with redirect_stdout(buffer):
                dis.dis(code)
            
            disassembly = buffer.getvalue()
            
            return True, disassembly, offset
        except Exception:
            return False, "", offset
    
    def run_pycdas_disassembly(self, pyc_file):
        try:
            pycdas_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Disasm", "pycdas")
            
            if not os.path.exists(pycdas_path) and not os.path.exists(pycdas_path + ".exe"):
                return f"错误: 找不到pycdas工具\n路径: {pycdas_path}\n请确保pycdas已正确安装在Disasm文件夹中。"
            
            result = self.run_as_subprocess([pycdas_path, pyc_file])
            
            return result
            
        except Exception as e:
            return f"pycdas反汇编失败: {str(e)}"
    
    def save_disasm_result(self, pyc_file, result, tool_name):
        try:
            base_name = os.path.splitext(pyc_file)[0]
            tool_suffix = "dis" if tool_name == "dis模块" else "pycdas"
            output_file = f"{base_name}_{tool_suffix}_disasm.txt"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(result)
            
            self.show_info("保存成功", f"反汇编结果已保存到: {normalize_path_for_display(output_file)}")
            
        except Exception as e:
            self.show_error("保存失败", f"保存反汇编结果时发生错误: {str(e)}")
    
    def browse_batch_disasm_files(self):
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "选择多个PYC文件", "", "Python字节码文件 (*.pyc);;所有文件 (*)"
        )
        
        if file_paths:
            self.batch_disasm_files.extend(file_paths)
            self.update_batch_disasm_files_list()
            self.batch_disasm_button.setEnabled(len(self.batch_disasm_files) > 0)
            self.batch_disasm_stop_button.setEnabled(False)
    
    def browse_batch_disasm_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "选择包含PYC文件的文件夹")
        
        if directory:
            pyc_files = get_files_with_extension(directory, ['.pyc'])
            if pyc_files:
                self.batch_disasm_files.extend(pyc_files)
                self.batch_disasm_base_dir = directory
                self.update_batch_disasm_files_list()
                self.batch_disasm_button.setEnabled(len(self.batch_disasm_files) > 0)
                self.batch_disasm_stop_button.setEnabled(False)
                self.show_info("文件查找结果", f"在所选文件夹中找到 {len(pyc_files)} 个PYC文件")
            else:
                self.show_info("文件查找结果", "在所选文件夹中未找到PYC文件")
    
    def clear_batch_disasm_files(self):
        self.batch_disasm_files.clear()
        self.update_batch_disasm_files_list()
        self.batch_disasm_button.setEnabled(False)
    
    def update_batch_disasm_files_list(self):
        self.batch_disasm_files_list.clear()
        for file_path in self.batch_disasm_files:
            self.batch_disasm_files_list.addItem(normalize_path_for_display(file_path))
    
    def batch_disassemble(self):
        if not self.batch_disasm_files:
            self.show_error("文件未选择", "请先选择要反汇编的PYC文件。")
            return
        
        disasm_tool = self.batch_disasm_tool_combo.currentText()
        
        self.batch_disasm_stop_flag = False
        self.batch_disasm_button.setEnabled(False)
        self.batch_disasm_stop_button.setEnabled(True)
        
        total_files = len(self.batch_disasm_files)
        success_count = 0
        failed_files = []
        
        self.batch_disasm_progress_bar.setValue(0)
        self.batch_disasm_progress_label.setText("正在反汇编...")
        
        if hasattr(self, 'batch_disasm_base_dir'):
            disasm_base_dir = os.path.join(os.path.dirname(self.batch_disasm_base_dir), "disasm_output")
        else:
            disasm_base_dir = os.path.join(os.path.dirname(self.batch_disasm_files[0]), "disasm_output")
        
        try:
            for i, pyc_file in enumerate(self.batch_disasm_files):
                if self.batch_disasm_stop_flag:
                    self.batch_disasm_progress_label.setText("已终止")
                    break
                
                try:
                    self.batch_disasm_progress_label.setText(f"正在反汇编 ({i+1}/{total_files}): {normalize_path_for_display(os.path.basename(pyc_file))}")
                    QApplication.processEvents()
                    
                    if not os.path.exists(pyc_file):
                        failed_files.append((pyc_file, "文件不存在"))
                        continue
                    
                    if disasm_tool == "dis模块":
                        result = self.run_dis_disassembly(pyc_file)
                    elif disasm_tool == "pycdas":
                        result = self.run_pycdas_disassembly(pyc_file)
                    else:
                        failed_files.append((pyc_file, "不支持的反汇编工具"))
                        continue
                    
                    if result:
                        if hasattr(self, 'batch_disasm_base_dir'):
                            rel_path = os.path.relpath(os.path.dirname(pyc_file), self.batch_disasm_base_dir)
                            if rel_path == '.':
                                rel_path = ''
                            output_dir = os.path.join(disasm_base_dir, rel_path)
                        else:
                            output_dir = disasm_base_dir
                        
                        if not os.path.exists(output_dir):
                            os.makedirs(output_dir)
                        
                        base_name = os.path.splitext(os.path.basename(pyc_file))[0]
                        tool_suffix = "dis" if disasm_tool == "dis模块" else "pycdas"
                        output_filename = f"{base_name}_{tool_suffix}_disasm.txt"
                        output_file = os.path.join(output_dir, output_filename)
                        
                        with open(output_file, 'w', encoding='utf-8') as f:
                            f.write(result)
                        
                        success_count += 1
                    else:
                        failed_files.append((pyc_file, "反汇编结果为空"))
                    
                except Exception as e:
                    failed_files.append((pyc_file, str(e)))
                
                finally:
                    progress = int((i + 1) / total_files * 100)
                    self.batch_disasm_progress_bar.setValue(progress)
                    QApplication.processEvents()
            
            if self.batch_disasm_stop_flag:
                self.batch_disasm_progress_label.setText("已终止")
                self.show_info("批量反汇编终止", f"操作已终止。成功: {success_count}, 失败: {len(failed_files)}")
            else:
                self.batch_disasm_progress_label.setText("完成")
                result_msg = f"批量反汇编完成！\n成功: {success_count}, 失败: {len(failed_files)}"
                if success_count > 0:
                    result_msg += f"\n\n输出目录: {normalize_path_for_display(disasm_base_dir)}"
                if failed_files:
                    result_msg += f"\n\n失败的文件:\n"
                    for file_path, error in failed_files[:5]:
                        result_msg += f"• {normalize_path_for_display(os.path.basename(file_path))}: {error}\n"
                    if len(failed_files) > 5:
                        result_msg += f"... 还有 {len(failed_files) - 5} 个文件失败"
                
                self.show_info("批量反汇编完成", result_msg)
                
        except Exception as e:
            self.show_error("批量反汇编错误", f"批量反汇编过程中发生错误: {str(e)}")
        finally:
            self.batch_disasm_button.setEnabled(True)
            self.batch_disasm_stop_button.setEnabled(False)
    
    def stop_batch_disassemble(self):
        self.batch_disasm_stop_flag = True
        self.batch_disasm_progress_label.setText("正在终止...")
    
    def browse_pyarmor_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "选择包含Pyarmor加密文件的目录")
        
        if directory:
            self.pyarmor_file_label.setText(normalize_path_for_display(directory))
            self.unpack_pyarmor_button.setEnabled(True)
            self.detect_pyarmor_python_version_button.setEnabled(True)
    
    def detect_pyarmor_python_version(self):
        target_path = self.pyarmor_file_label.text()
        if not os.path.exists(target_path) or not os.path.isdir(target_path):
            self.show_error("目录错误", "请先选择一个有效的目录。")
            return
        
        if not PEFILE_AVAILABLE:
            self.show_error("依赖缺失", "检测Python版本需要pefile库。请安装: pip install pefile")
            return
        
        try:
            pyd_files = []
            for root, dirs, files in os.walk(target_path):
                for file in files:
                    if file.endswith('.pyd'):
                        pyd_files.append(os.path.join(root, file))
            
            if not pyd_files:
                self.detected_pyarmor_version_label.setText("未找到pyd文件")
                return
            
            pyd_file = pyd_files[0]
            python_version = self.analyze_pyd_file(pyd_file)
            
            if python_version:
                self.detected_pyarmor_version_label.setText(python_version)
            else:
                self.detected_pyarmor_version_label.setText("检测失败")
                
        except Exception as e:
            self.detected_pyarmor_version_label.setText("检测出错")
            self.show_error("检测错误", f"检测Python版本时发生错误: {str(e)}")
    
    def analyze_pyd_file(self, pyd_file_path):
        try:
            pe = pefile.PE(pyd_file_path)
            
            if hasattr(pe, 'DIRECTORY_ENTRY_IMPORT'):
                for entry in pe.DIRECTORY_ENTRY_IMPORT:
                    dll_name = entry.dll.decode('utf-8').lower()
                    
                    if dll_name.startswith('python') and dll_name.endswith('.dll'):
                        version_part = dll_name.replace('python', '').replace('.dll', '')
                        if version_part.isdigit() and len(version_part) >= 2:
                            major = version_part[0]
                            minor = version_part[1:]
                            return f"Python {major}.{minor}"
            
            data = pe.get_memory_mapped_image()
            
            import re
            python_patterns = [
                rb'python(\d)(\d+)',
                rb'Python (\d)\.(\d+)',
                rb'PYTHON(\d)(\d+)'
            ]
            
            for pattern in python_patterns:
                matches = re.findall(pattern, data, re.IGNORECASE)
                if matches:
                    major, minor = matches[0]
                    return f"Python {major.decode()}.{minor.decode()}"
            
            return None
            
        except Exception as e:
            print(f"分析pyd文件时出错: {e}")
            return None
    
    def unpack_pyarmor(self):
        target_path = self.pyarmor_file_label.text()
        if not os.path.exists(target_path):
            self.show_error("目录未找到", "所选目录不存在。")
            return
        
        if not os.path.isdir(target_path):
            self.show_error("路径错误", "请选择一个目录，而不是文件。")
            return
        
        try:
            self.pyarmor_results_text.clear()
            self.pyarmor_progress_bar.setValue(0)
            self.pyarmor_progress_label.setText("正在解包...")
            self.unpack_pyarmor_button.setEnabled(False)
            
            header_fix_enabled = self.pyarmor_header_fix_checkbox.isChecked()
            
            if header_fix_enabled:
                self.pyarmor_progress_label.setText("正在检测头部缺失...")
                fixed_files = self.detect_and_fix_pyarmor_headers(target_path)
                if fixed_files:
                    self.pyarmor_results_text.append(f"✓ 检测到 {len(fixed_files)} 个文件缺失Py000000头部，已自动修复:")
                    for file_path in fixed_files:
                        self.pyarmor_results_text.append(f"  - {normalize_path_for_display(os.path.basename(file_path))}")
                    self.pyarmor_results_text.append("")
                else:
                    self.pyarmor_results_text.append("✓ 未发现缺失Py000000头部的文件\n")
            
            self.pyarmor_progress_bar.setValue(20)
            
            shot_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Pyarmor_Unpack", "oneshot", "shot.py")
            
            if not os.path.exists(shot_script):
                self.show_error("工具未找到", f"找不到Pyarmor解包工具: {shot_script}")
                self.unpack_pyarmor_button.setEnabled(True)
                return
            
            oneshot_dir = os.path.dirname(shot_script)
            pyarmor_1shot = os.path.join(oneshot_dir, "pyarmor-1shot.exe")
            if not os.path.exists(pyarmor_1shot):
                pyarmor_1shot = os.path.join(oneshot_dir, "pyarmor-1shot")
                if not os.path.exists(pyarmor_1shot):
                    self.show_error("工具未找到", f"找不到pyarmor-1shot可执行文件: {pyarmor_1shot}")
                    self.unpack_pyarmor_button.setEnabled(True)
                    return
            
            cmd = ["python", shot_script, target_path]
            
            self.pyarmor_progress_bar.setValue(40)
            self.pyarmor_progress_label.setText("正在执行解包...")
            
            result = self.run_as_subprocess(cmd)
            
            self.pyarmor_progress_bar.setValue(80)
            
            self.pyarmor_results_text.setText(result)
            
            self.pyarmor_progress_bar.setValue(100)
            self.pyarmor_progress_label.setText("解包完成")
            
            if ".1shot." in result:
                self.show_info("解包成功", "Pyarmor解包完成！生成的文件名包含'.1shot.'标识。")
            elif "error" in result.lower() or "failed" in result.lower():
                self.show_error("解包可能失败", "解包过程中可能出现错误，请查看详细输出。")
            else:
                self.show_info("解包完成", "Pyarmor解包过程已完成，请查看输出结果。")
                
        except Exception as e:
            self.show_error("Pyarmor解包失败", f"解包过程中发生错误: {str(e)}")
        finally:
            self.unpack_pyarmor_button.setEnabled(True)
            if self.pyarmor_progress_bar.value() != 100:
                self.pyarmor_progress_bar.setValue(0)
                self.pyarmor_progress_label.setText("就绪")

    def detect_and_fix_pyarmor_headers(self, target_path):
        fixed_files = []
        
        try:
            for root, dirs, files in os.walk(target_path):
                for file in files:
                    if file.endswith('.py'):
                        file_path = os.path.join(root, file)
                        
                        try:
                            with open(file_path, 'rb') as f:
                                content = f.read()
                            
                            if self.is_missing_pyarmor_header(content):
                                if self.fix_pyarmor_header(file_path, content):
                                    fixed_files.append(file_path)
                        
                        except Exception as e:
                            continue
            
            return fixed_files
        
        except Exception as e:
            return []
    
    def is_missing_pyarmor_header(self, content):
        try:
            content_str = content.decode('utf-8', errors='ignore')
        except:
            return False
        
        if '__pyarmor__' not in content_str:
            return False
        
        import re
        pattern = r'__pyarmor__\([^,]+,\s*[^,]+,\s*b"([^"]*)"'
        match = re.search(pattern, content_str)
        
        if not match:
            return False
        
        byte_string = match.group(1)
        
        if not byte_string.startswith('PY000000'):
            return True
        
        return False
    
    def fix_pyarmor_header(self, file_path, content):
        try:
            content_str = content.decode('utf-8', errors='ignore')
            
            import re
            pattern = r'(__pyarmor__\([^,]+,\s*[^,]+,\s*b")([^"]*)"'
            match = re.search(pattern, content_str)
            
            if not match:
                return False
            
            prefix = match.group(1)
            byte_string = match.group(2)
            
            fixed_byte_string = 'PY000000' + byte_string
            
            fixed_content_str = content_str.replace(
                prefix + byte_string + '"',
                prefix + fixed_byte_string + '"'
            )
            
            with open(file_path, 'w', encoding='utf-8', newline='') as f:
                f.write(fixed_content_str)
            
            return True
        
        except Exception as e:
            return False

    def browse_stego_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择PYC文件", "", "PYC文件 (*.pyc);;所有文件 (*)"
        )
        
        if file_path:
            self.stego_file_label.setText(normalize_path_for_display(file_path))
            self.stego_execute_button.setEnabled(True)
            self.stego_results_text.clear()

    def execute_stego_operation(self):
        file_path = self.stego_file_label.text()
        if not os.path.exists(file_path):
            self.show_error("文件未找到", "所选文件不存在。")
            return
        
        try:
            self.stego_results_text.clear()
            self.stego_execute_button.setEnabled(False)
            
            stego_exe = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stegosaurus", "stegosaurus.exe")
            
            if not os.path.exists(stego_exe):
                self.show_error("工具未找到", f"找不到stegosaurus.exe工具: {stego_exe}")
                self.stego_execute_button.setEnabled(True)
                return
            
            cmd = [stego_exe, "-x", file_path]
            
            self.stego_results_text.append(f"执行命令: {' '.join(cmd)}")
            self.stego_results_text.append("-" * 50)
            
            result = self.run_as_subprocess(cmd)
            
            if result:
                self.stego_results_text.append("执行结果:")
                self.stego_results_text.append(result)
            else:
                self.stego_results_text.append("执行完成，无输出结果")
                
        except Exception as e:
            self.show_error("PYC隐写提取失败", f"提取过程中发生错误: {str(e)}")
        finally:
            self.stego_execute_button.setEnabled(True)

    def browse_pyinstaller_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择PyInstaller打包的可执行文件", "", "可执行文件 (*.exe);;所有文件 (*)"
        )
        
        if file_path:
            self.pyinstaller_file_label.setText(normalize_path_for_display(file_path))
            self.extract_pyinstaller_button.setEnabled(True)
            self.detect_python_version_button.setEnabled(True)
            self.pyinstaller_results_text.clear()
            self.pyinstaller_progress_label.setText("就绪")
            self.detected_version_label.setText("未检测")
    
    def detect_python_version(self):
        exe_file = self.pyinstaller_file_label.text()
        if not os.path.exists(exe_file):
            self.show_error("文件未找到", "所选文件不存在。")
            return
        
        try:
            self.detected_version_label.setText("正在检测...")
            QApplication.processEvents()
            
            with open(exe_file, 'rb') as f:
                content = f.read()
            
            text_content = content.decode('utf-8', errors='ignore')
            
            version_patterns = [
                r'python(\d)(\d+)\.dll',
                
                r'libpython(\d)\.(\d+)\.so',
            ]
            
            detected_versions = []
            
            import re
            for pattern in version_patterns:
                matches = re.finditer(pattern, text_content, re.IGNORECASE)
                for match in matches:
                    if len(match.groups()) == 1:
                        version = match.group(1)
                    elif len(match.groups()) == 2:
                        major, minor = match.groups()
                        
                        version = f"{major}.{minor}"
                    else:
                        continue
                    
                    if self.is_valid_python_version(version):
                        detected_versions.append(version)
            
            
            unique_versions = list(set(detected_versions))
            
            if unique_versions:
                best_version = self.select_best_version(unique_versions)
                result_text = f"Python {best_version}"
                
                if len(unique_versions) > 1:
                    other_versions = [v for v in unique_versions if v != best_version]
                    result_text += f" (其他可能版本: {', '.join(other_versions)})"
                
                self.detected_version_label.setText(result_text)
            else:
                self.detected_version_label.setText("未检测到版本信息")
                
        except Exception as e:
            self.detected_version_label.setText("检测失败")
            self.show_error("版本检测错误", f"检测Python版本时出错: {str(e)}")
    
    def parse_version_number(self, number_str):
        try:
            if len(number_str) == 2:
                return f"{number_str[0]}.{number_str[1]}"
            elif len(number_str) == 3:
                return f"{number_str[0]}.{number_str[1:]}"
            elif len(number_str) == 4:
                return f"{number_str[0]}.{number_str[1:3]}.{number_str[3]}"
            else:
                return None
        except (IndexError, ValueError):
            return None
    
    def is_valid_python_version(self, version):
        try:
            parts = version.split('.')
            if len(parts) < 2:
                return False
            
            major = int(parts[0])
            minor = int(parts[1])
            
            if major == 2:
                return minor == 7
            elif major == 3:
                return 0 <= minor <= 15
            else:
                return False
                
        except (ValueError, IndexError):
            return False
    
    def select_best_version(self, versions):
        if not versions:
            return None
        
        def version_key(v):
            try:
                parts = v.split('.')
                major = int(parts[0])
                minor = int(parts[1])
                patch = int(parts[2]) if len(parts) > 2 else 0
                return (major, minor, patch)
            except:
                return (0, 0, 0)
        
        sorted_versions = sorted(versions, key=version_key, reverse=True)
        
        for version in sorted_versions:
            if version.startswith('3.'):
                return version
        
        return sorted_versions[0]
    
    def update_pyinstaller_status(self, message):
        if '\\' in message:
            parts = message.split(': ', 1)
            if len(parts) > 1 and ('\\' in parts[1] or '/' in parts[1]):
                message = parts[0] + ': ' + normalize_path_for_display(parts[1])
        
        current_text = self.pyinstaller_results_text.toPlainText()
        if current_text:
            self.pyinstaller_results_text.setText(current_text + "\n" + message)
        else:
            self.pyinstaller_results_text.setText(message)
        
        if message.startswith('[+]'):
            self.pyinstaller_progress_label.setText(message.strip())
            
            if "Extracting files:" in message or "Extracting PYZ contents:" in message:
                try:
                    progress_str = message.split('(')[-1].split('%')[0]
                    progress = int(progress_str)
                    self.pyinstaller_progress_bar.setValue(progress)
                except:
                    pass
        
        scrollbar = self.pyinstaller_results_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
        QApplication.processEvents()
    
    def extract_pyinstaller(self):
        if not PYINSTALLER_EXTRACTOR_AVAILABLE:
            self.show_error("模块未找到", "PyInstExtractor模块未找到，无法使用解包功能。")
            return
            
        exe_path = self.pyinstaller_file_label.text()
        if not os.path.exists(exe_path):
            self.show_error("文件未找到", "所选文件不存在。")
            return
        
        self.pyinstaller_results_text.clear()
        
        self.pyinstaller_progress_bar.setValue(0)
        
        self.extract_pyinstaller_button.setEnabled(False)
        
        try:
            archive = PyInstArchive(exe_path)
            archive.set_status_callback(self.update_pyinstaller_status)
            
            if archive.open():
                if archive.checkFile():
                    if archive.getCArchiveInfo():
                        archive.parseTOC()
                        extraction_dir = archive.extractFiles()
                        archive.close()
                        
                        self.update_pyinstaller_status(f"\n[+] 解包成功！文件保存在: {normalize_path_for_display(extraction_dir)}")
                        
                        reply = QMessageBox.question(
                            self,
                            "解包完成",
                            f"PyInstaller程序解包完成！\n文件已保存到: {normalize_path_for_display(extraction_dir)}\n\n是否打开输出目录？",
                            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                            QMessageBox.StandardButton.Yes
                        )
                        
                        if reply == QMessageBox.StandardButton.Yes:
                            if sys.platform == 'win32':
                                os.startfile(extraction_dir)
                            elif sys.platform == 'darwin':
                                subprocess.run(['open', extraction_dir])
                            else:
                                subprocess.run(['xdg-open', extraction_dir])
                        
                        return
                
                archive.close()
            
            self.update_pyinstaller_status("\n[!] 解包失败，请检查选择的文件是否是有效的PyInstaller打包程序。")
            
        except Exception as e:
            self.update_pyinstaller_status(f"\n[!] 解包过程中发生错误: {str(e)}")
        
        finally:
            self.extract_pyinstaller_button.setEnabled(True)

    def show_about_dialog(self):
        about_dialog = QDialog(self)
        about_dialog.setWindowTitle("关于")
        about_dialog.setFixedSize(600, 300)
        
        dialog_layout = QHBoxLayout(about_dialog)
        
        left_layout = QVBoxLayout()
        left_logo_label = QLabel()
        left_logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "image", "logo.png")
        if os.path.exists(left_logo_path):
            pixmap = QPixmap(left_logo_path)
            pixmap = pixmap.scaled(120, 120, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            left_logo_label.setPixmap(pixmap)
            left_logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        github_label = QLabel('<a href="https://github.com/yoruak1" style="color: #F5A742; text-decoration: none;">https://github.com/yoruak1</a>')
        github_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        github_label.setOpenExternalLinks(True)
        github_label.setCursor(Qt.CursorShape.PointingHandCursor)
        github_label.setStyleSheet("""
            QLabel {
                font-size: 12pt;
                font-weight: bold;
                font-family: '微软雅黑', Arial, sans-serif;
                letter-spacing: 1px;
                padding: 8px;
                border-radius: 8px;
                background-color: white;
                border: 3px solid #F5A742;
                margin: 10px;
            }
            QLabel:hover {
                background-color: #FFF8F0;
                border: 3px solid #FF9966;
            }
        """)
        
        left_layout.addWidget(left_logo_label)
        left_layout.addWidget(github_label)
        left_layout.addStretch()
        
        right_layout = QVBoxLayout()
        right_logo_label = QLabel()
        right_logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "image", "logo_2.png")
        if os.path.exists(right_logo_path):
            pixmap = QPixmap(right_logo_path)
            pixmap = pixmap.scaled(120, 120, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            right_logo_label.setPixmap(pixmap)
            right_logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        wechat_label = QLabel("公众号：夜秋的小屋")
        wechat_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        wechat_label.setStyleSheet("""
            color: #F5A742;
            font-size: 12pt;
            font-weight: bold;
            font-family: '微软雅黑', Arial, sans-serif;
            letter-spacing: 1px;
            padding: 8px;
            border-radius: 8px;
            background-color: white;
            border: 3px solid #F5A742;
            margin: 10px;
        """)
        
        right_layout.addWidget(right_logo_label)
        right_layout.addWidget(wechat_label)
        right_layout.addStretch()
        
        dialog_layout.addLayout(left_layout)
        dialog_layout.addSpacing(20)
        dialog_layout.addLayout(right_layout)
        
        about_dialog.setStyleSheet("""
            QDialog {
                background-color: #FFF8EE;
                border: 2px solid #F5A742;
                border-radius: 10px;
            }
        """)
        
        about_dialog.exec()

    def auto_detect_decrypt_settings(self):
        directory = QFileDialog.getExistingDirectory(self, "选择PyInstaller解包后的文件夹")
        if not directory:
            return
        
        self.decrypt_progress_label.setText("正在扫描文件夹...")
        self.decrypt_progress_bar.setValue(10)
        QApplication.processEvents()
        
        crypto_key_files = []
        archive_files = []
        magic_number = None
        
        for root, _, files in os.walk(directory):
            for filename in files:
                if filename.endswith('.pyc'):
                    full_path = os.path.join(root, filename)
                    
                    try:
                        with open(full_path, 'rb') as f:
                            file_header = f.read(4)
                            if file_header in MAGIC_NUMBERS and magic_number is None:
                                magic_number = file_header
                            
                            f.seek(0)
                            content = f.read().decode('latin-1', errors='ignore').lower()
                            
                            if 'crypto_key' in content and full_path not in crypto_key_files:
                                crypto_key_files.append(full_path)
                            
                            if 'archive' in content and 'pyinstaller' in content and full_path not in archive_files:
                                archive_files.append(full_path)
                    except:
                        continue
        
        self.decrypt_progress_bar.setValue(30)
        self.decrypt_progress_label.setText("正在分析文件...")
        QApplication.processEvents()
        
        key = None
        for key_file in crypto_key_files:
            try:
                decompiler = "uncompyle6"
                result = self.run_decompiler(key_file, decompiler)
                
                if result:
                    lines = result.splitlines()
                    key_found = False
                    
                    for i, line in enumerate(lines):
                        if 'crypto_key' in line.lower():
                            for j in range(i, min(i+5, len(lines))):
                                if '=' in lines[j]:
                                    possible_key = lines[j].split('=')[1].strip()
                                    possible_key = possible_key.strip("'\" ")
                                    if possible_key and not possible_key.startswith(('(', '{')):
                                        key = possible_key
                                        key_found = True
                                        break
                            if key_found:
                                break
                    
                    if not key_found:
                        result_text = '\n'.join(lines)
                        key_patterns = [
                            r"crypto_key\s*=\s*['\"]([^'\"]+)['\"]",
                            r"key\s*=\s*['\"]([^'\"]+)['\"]",
                            r"key\s*=\s*b['\"]([^'\"]+)['\"]"
                        ]
                        
                        for pattern in key_patterns:
                            matches = re.findall(pattern, result_text)
                            if matches:
                                key = matches[0]
                                key_found = True
                                break
            except:
                continue
            
            if key:
                break
        
        self.decrypt_progress_bar.setValue(60)
        QApplication.processEvents()
        
        is_lt4 = True
        for arch_file in archive_files:
            try:
                result = self.run_decompiler(arch_file, decompiler)
                
                if result:
                    result_lower = result.lower()
                    
                    ctr_patterns = ['mode_ctr', 'aes.ctr', '.ctrmode', 'tinyaes']
                    cfb_patterns = ['mode_cfb', 'aes.cfb', '.cfbmode', 'pycrypto']
                    
                    has_ctr = any(pattern in result_lower for pattern in ctr_patterns)
                    has_cfb = any(pattern in result_lower for pattern in cfb_patterns)
                    
                    if has_ctr:
                        is_lt4 = False
                        break
                    elif has_cfb:
                        is_lt4 = True
                        break
            except:
                continue
        
        self.decrypt_progress_bar.setValue(90)
        QApplication.processEvents()
        
        if key:
            self.decrypt_key_input.setText(key)
        
        if magic_number and magic_number in MAGIC_NUMBERS:
            python_version = MAGIC_NUMBERS[magic_number]
            version_number = python_version.replace("Python ", "")
            found = False
            for i in range(self.python_version_combo.count()):
                if self.python_version_combo.itemText(i) == version_number:
                    self.python_version_combo.setCurrentIndex(i)
                    found = True
                    break
            
            if not found and version_number.startswith("3."):
                major, minor = version_number.split('.')
                for i in range(self.python_version_combo.count()):
                    combo_version = self.python_version_combo.itemText(i)
                    if combo_version.startswith(f"{major}."):
                        self.python_version_combo.setCurrentIndex(i)
                        break
        
        if is_lt4:
            self.pyinstaller_lt4_radio.setChecked(True)
        else:
            self.pyinstaller_ge4_radio.setChecked(True)
        
        self.decrypt_progress_bar.setValue(100)
        self.decrypt_progress_label.setText("识别完成")
        
        results = []
        results.append("自动识别解密设置结果:")
        results.append("-" * 30)
        
        if key:
            results.append(f"✓ 加密密钥: {key}")
        else:
            results.append("✗ 未找到加密密钥")
        
        if magic_number and magic_number in MAGIC_NUMBERS:
            python_version = MAGIC_NUMBERS[magic_number]
            results.append(f"✓ Python版本: {python_version}")
        else:
            results.append("✗ 未能识别Python版本")
        
        if is_lt4:
            results.append(f"✓ PyInstaller版本: < 4.0 (使用CFB模式加密)")
            results.append("  解密将使用PyCrypto/PyCryptodome库")
        else:
            results.append(f"✓ PyInstaller版本: >= 4.0 (使用CTR模式加密)")
            results.append("  解密将使用TinyAES库")
        
        results.append("-" * 30)
        results.append(f"扫描文件夹: {normalize_path_for_display(directory)}")
        
        
        if not DECRYPTION_AVAILABLE:
            results.append("\n警告: 缺少解密所需的库，解密功能不可用")
            results.append("请安装必要的库: pip install pycryptodome tinyaes")
            
        QMessageBox.information(self, "自动识别结果", "\n".join(results))
        
        if key and magic_number in MAGIC_NUMBERS:
            self.decrypt_button.setEnabled(True)
        
        if key:
            encrypted_files = get_files_with_extension(directory, ['.pyc.encrypted'])
            if encrypted_files:
                self.encrypted_base_dir = directory
                
                self.encrypted_files.extend(encrypted_files)
                self.update_encrypted_files_list()
                self.decrypt_button.setEnabled(True)
                self.show_info("文件查找结果", f"在文件夹中找到 {len(encrypted_files)} 个加密的PYC文件")
            else:
                pyz_dirs = []
                for root, dirs, _ in os.walk(directory):
                    for dirname in dirs:
                        if dirname.endswith('_extracted'):
                            pyz_dirs.append(os.path.join(root, dirname))
                
                if pyz_dirs:
                    encrypted_total = 0
                    
                    self.encrypted_files = []
                    
                    for pyz_dir in pyz_dirs:
                        encrypted_in_dir = get_files_with_extension(pyz_dir, ['.encrypted'])
                        if encrypted_in_dir:
                            if encrypted_total == 0:
                                self.encrypted_base_dir = pyz_dir
                            
                            self.encrypted_files.extend(encrypted_in_dir)
                            encrypted_total += len(encrypted_in_dir)
                    
                    if encrypted_total > 0:
                        self.update_encrypted_files_list()
                        self.decrypt_button.setEnabled(True)
                        self.show_info("文件查找结果", f"在PYZ提取目录中找到 {encrypted_total} 个加密文件")

    def browse_magic_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择需要修复的PYC文件", "", "Python字节码文件 (*.pyc);;所有文件 (*)"
        )
        
        if file_path:
            self.magic_file_label.setText(normalize_path_for_display(file_path))
            self.magic_fix_button.setEnabled(True)
            self.magic_detected_version_label.setText("未检测")
            self.magic_results_text.clear()
    
    def analyze_file_structure(self, content):
        try:
            if len(content) < 16:
                self.magic_results_text.append("文件过小，可能完全缺失头部")
                return "missing"
            
            
            header_16 = content[:16]
            
            if header_16[:12] == b'\x00' * 12:
                self.magic_results_text.append("检测到开头12字节全为00，判断为缺失4字节魔数头")
                return "missing"
            elif header_16[:8] == b'\x00' * 8:
                self.magic_results_text.append("检测到开头8字节全为00，判断为缺失4字节魔数头")
                return "missing"
            elif header_16[:4] == b'\x00' * 4:
                self.magic_results_text.append("检测到开头4字节全为00，判断为缺失4字节魔数头")
                return "missing"
            
            if len(content) >= 4 and content[3] == 0x0A:
                self.magic_results_text.append("检测到疑似魔数格式（第4字节为0x0A），判断为错误的魔数头")
                return "wrong"
            
            marshal_signatures = [b'c', b's', b't', b'N', b'T', b'F', b'(', b'[', b'{']
            for i in range(min(16, len(content))):
                if content[i:i+1] in marshal_signatures:
                    self.magic_results_text.append(f"在位置{i}检测到marshal数据特征，可能完全缺失头部")
                    return "missing"
            
            header_4 = content[:4]
            non_zero_count = sum(1 for b in header_4 if b != 0)
            if non_zero_count >= 2:
                self.magic_results_text.append("检测到前4字节有非零数据，判断为错误的魔数头")
                return "wrong"
            
            self.magic_results_text.append("无法明确判断，默认为缺失魔数头")
            return "missing"
            
        except Exception as e:
            self.magic_results_text.append(f"文件结构分析出错: {str(e)}，默认为缺失魔数头")
            return "missing"
    
    def fix_magic_number(self):
        pyc_file = self.magic_file_label.text()
        if not os.path.exists(pyc_file):
            self.show_error("文件未找到", "所选文件不存在。")
            return
        
        self.magic_results_text.clear()
        self.magic_detected_version_label.setText("检测中...")
        decompiler = self.magic_decompiler_combo.currentText()
        autodetect = self.magic_autodetect_checkbox.isChecked()
        save_file = self.magic_save_checkbox.isChecked()
        
        try:
            self.magic_results_text.append("首先尝试直接反编译原文件...")
            result = self.run_decompiler(pyc_file, decompiler)
            if result and len(result.strip()) > 0 and "Error" not in result and "error" not in result:
                with open(pyc_file, 'rb') as f:
                    file_header = f.read(4)
                    if file_header in MAGIC_NUMBERS:
                        detected_version = MAGIC_NUMBERS[file_header]
                        self.magic_detected_version_label.setText(f"原文件正常: {detected_version}")
                    else:
                        self.magic_detected_version_label.setText("原文件正常: 未知版本")
                
                self.magic_results_text.append("原文件可以直接反编译，不需要修复魔数头！")
                self.magic_results_text.append("\n反编译结果:\n" + result)
                return
            else:
                self.magic_results_text.append("原文件无法直接反编译，需要修复魔数头。")
        except Exception as e:
            self.magic_results_text.append(f"原文件反编译出错: {str(e)}")
            self.magic_results_text.append("继续尝试修复魔数头...")
        
        with open(pyc_file, 'rb') as f:
            original_content = f.read()
        
        error_type = None
        if autodetect:
            file_header = original_content[:4]
            if file_header in MAGIC_NUMBERS:
                self.magic_results_text.append(f"检测到文件已有魔数头: {' '.join('%02X' % b for b in file_header)}")
                self.magic_results_text.append(f"对应Python版本: {MAGIC_NUMBERS[file_header]}")
                self.magic_results_text.append("判断为魔数头错误，将尝试替换为不同的魔数头。")
                error_type = "wrong"
            else:
                self.magic_results_text.append(f"检测到文件头: {' '.join('%02X' % b for b in file_header)}")
                self.magic_results_text.append("无法识别的魔数头，进行进一步分析...")
                
                error_type = self.analyze_file_structure(original_content)
        else:
            error_type = "wrong" if self.magic_type_wrong.isChecked() else "missing"
            self.magic_results_text.append(f"使用手动选择的错误类型: {'错误的魔数头' if error_type == 'wrong' else '缺失16字节魔数头'}")
        
        py3_magic_headers = {}
        for magic, version in MAGIC_NUMBERS.items():
            if version.startswith("Python 3."):
                minor_ver = float(version.replace("Python 3.", ""))
                if 0 <= minor_ver <= 13:
                    py3_magic_headers[magic] = version
        
        sorted_magic_headers = sorted(py3_magic_headers.items(),
                                     key=lambda x: float(x[1].replace("Python 3.", "")))
        
        self.magic_progress_bar.setValue(0)
        self.magic_progress_label.setText("开始尝试修复...")
        
        success = False
        success_magic = None
        success_content = None
        success_python_version = None
        self.magic_results_text.append("\n开始尝试不同的魔数头:\n")
        
        total_attempts = len(sorted_magic_headers)
        for i, (magic, version) in enumerate(sorted_magic_headers):
            progress = int((i + 1) / total_attempts * 100)
            self.magic_progress_bar.setValue(progress)
            self.magic_progress_label.setText(f"正在尝试 {version}...")
            QApplication.processEvents()
            
            self.magic_results_text.append(f"尝试 {version} 魔数头: {' '.join('%02X' % b for b in magic)}")
            
            fixed_content = None
            if error_type == "wrong":
                fixed_content = magic + original_content[4:]
            else:
                
                header_size = 16 if float(version.replace("Python 3.", "")) >= 7 else (12 if float(version.replace("Python 3.", "")) >= 3 else 8)
                expected_zeros = header_size - 4
                
                if len(original_content) >= expected_zeros:
                    if original_content[:expected_zeros] == b'\0' * expected_zeros:
                        fixed_content = magic + original_content
                        self.magic_results_text.append(f"  检测到只缺失4字节魔数，直接添加魔数头")
                    else:
                        if float(version.replace("Python 3.", "")) >= 7:
                            fixed_content = magic + b'\0' * 4 + b'\0' * 8 + original_content
                        elif float(version.replace("Python 3.", "")) >= 3:
                            fixed_content = magic + b'\0' * 4 + b'\0' * 4 + original_content
                        else:
                            fixed_content = magic + b'\0' * 4 + original_content
                        self.magic_results_text.append(f"  检测到完全缺失头部，添加完整{header_size}字节头部")
                else:
                    if float(version.replace("Python 3.", "")) >= 7:
                        fixed_content = magic + b'\0' * 4 + b'\0' * 8 + original_content
                    elif float(version.replace("Python 3.", "")) >= 3:
                        fixed_content = magic + b'\0' * 4 + b'\0' * 4 + original_content
                    else:
                        fixed_content = magic + b'\0' * 4 + original_content
                    self.magic_results_text.append(f"  文件过小，添加完整头部")
            
            temp_file = pyc_file + ".temp"
            with open(temp_file, 'wb') as f:
                f.write(fixed_content)
            
            try:
                result = self.run_decompiler(temp_file, decompiler)
                if result and len(result.strip()) > 0 and "Error" not in result and "error" not in result:
                    self.magic_results_text.append(f"✓ 使用 {version} 魔数头反编译成功!\n")
                    success = True
                    success_magic = magic
                    success_content = fixed_content
                    success_python_version = version
                    break
                else:
                    self.magic_results_text.append(f"✗ 使用 {version} 魔数头反编译失败\n")
            except Exception as e:
                self.magic_results_text.append(f"✗ 反编译出错: {str(e)}\n")
            finally:
                try:
                    os.remove(temp_file)
                except:
                    pass
        
        if success:
            self.magic_progress_bar.setValue(100)
            self.magic_progress_label.setText("修复成功!")
            
            self.magic_detected_version_label.setText(f"{success_python_version}")
            
            self.magic_results_text.append(f"修复成功! 正确的魔数头对应版本: {success_python_version}")
            self.magic_results_text.append(f"魔数值: {' '.join('%02X' % b for b in success_magic)}")
            
            if save_file:
                output_dir = os.path.join(os.path.dirname(pyc_file), "fixed")
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)
                
                fixed_file = os.path.join(output_dir, os.path.basename(pyc_file))
                with open(fixed_file, 'wb') as f:
                    f.write(success_content)
                
                self.magic_results_text.append(f"\n修复后的文件已保存到: {normalize_path_for_display(fixed_file)}")
                
                try:
                    result = self.run_decompiler(fixed_file, decompiler)
                    
                    if result:
                        py_file = os.path.splitext(fixed_file)[0] + '.py'
                        with open(py_file, 'w', encoding='utf-8') as f:
                            f.write(result)
                        self.magic_results_text.append(f"反编译的Python源代码已保存到: {normalize_path_for_display(py_file)}")
                        
                        self.magic_results_text.append("\n反编译结果:\n" + result)
                except Exception as e:
                    self.magic_results_text.append(f"反编译时出错: {str(e)}")
        else:
            self.magic_progress_bar.setValue(100)
            self.magic_progress_label.setText("修复失败")
            
            self.magic_detected_version_label.setText("修复失败")
            
            self.magic_results_text.append("尝试了所有Python 3.0-3.13的魔数头，但都无法成功反编译。")

def main():
    app = QApplication(sys.argv)
    
    if sys.platform == 'win32':
        app_id = 'yoruaki.pyglimmer.1.2'
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
        except Exception as e:
            print(f"设置应用程序ID时出错: {e}")
    
    logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "image", "logo.png")
    if os.path.exists(logo_path):
        app.setWindowIcon(QIcon(logo_path))
        
    window = PythonDecompilerApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()