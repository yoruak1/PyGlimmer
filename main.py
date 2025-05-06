import sys
import os
import subprocess
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                           QLabel, QPushButton, QFileDialog, QTextEdit, QComboBox,
                           QCheckBox, QGroupBox, QMessageBox, QSplitter, QListWidget,
                           QProgressBar, QTabWidget, QLineEdit, QRadioButton, QButtonGroup,
                           QGraphicsDropShadowEffect, QFrame, QDialog)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QColor, QPalette, QPixmap, QIcon
import zlib
import dis
import marshal
import struct
import uuid

try:
    from Decryptor.decrypt_pyinstaller_lt4 import decrypt_pyc_files as decrypt_lt4
    from Decryptor.decrypt_pyinstaller_ge4 import decrypt_pyc_files as decrypt_ge4
    DECRYPTION_AVAILABLE = True
except ImportError:
    DECRYPTION_AVAILABLE = False

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

def normalize_path_for_display(path):
    return path.replace('\\', '/')

class PyInstArchive:
    PYINST20_COOKIE_SIZE = 24
    PYINST21_COOKIE_SIZE = 24 + 64
    MAGIC = b'MEI\014\013\012\013\016'

    def __init__(self, path):
        self.filePath = path
        self.pycMagic = b'\0' * 4
        self.barePycList = []
        self.extractionDir = ""
        self.status_callback = None

    def set_status_callback(self, callback):
        self.status_callback = callback

    def status(self, msg):
        if self.status_callback:
            self.status_callback(msg)
        else:
            print(msg)

    def open(self):
        try:
            self.fPtr = open(self.filePath, 'rb')
            self.fileSize = os.stat(self.filePath).st_size
        except:
            self.status('[!] Error: Could not open {0}'.format(self.filePath))
            return False
        return True

    def close(self):
        try:
            self.fPtr.close()
        except:
            pass

    def checkFile(self):
        self.status('[+] Processing {0}'.format(self.filePath))

        searchChunkSize = 8192
        endPos = self.fileSize
        self.cookiePos = -1

        if endPos < len(self.MAGIC):
            self.status('[!] Error : File is too short or truncated')
            return False

        while True:
            startPos = endPos - searchChunkSize if endPos >= searchChunkSize else 0
            chunkSize = endPos - startPos

            if chunkSize < len(self.MAGIC):
                break

            self.fPtr.seek(startPos, os.SEEK_SET)
            data = self.fPtr.read(chunkSize)

            offs = data.rfind(self.MAGIC)

            if offs != -1:
                self.cookiePos = startPos + offs
                break

            endPos = startPos + len(self.MAGIC) - 1

            if startPos == 0:
                break

        if self.cookiePos == -1:
            self.status('[!] Error : Missing cookie, unsupported pyinstaller version or not a pyinstaller archive')
            return False

        self.fPtr.seek(self.cookiePos + self.PYINST20_COOKIE_SIZE, os.SEEK_SET)

        if b'python' in self.fPtr.read(64).lower():
            self.status('[+] Pyinstaller version: 2.1+')
            self.pyinstVer = 21
        else:
            self.pyinstVer = 20
            self.status('[+] Pyinstaller version: 2.0')

        return True

    def getCArchiveInfo(self):
        try:
            if self.pyinstVer == 20:
                self.fPtr.seek(self.cookiePos, os.SEEK_SET)
                (magic, lengthofPackage, toc, tocLen, pyver) = \
                struct.unpack('!8siiii', self.fPtr.read(self.PYINST20_COOKIE_SIZE))

            elif self.pyinstVer == 21:
                self.fPtr.seek(self.cookiePos, os.SEEK_SET)
                (magic, lengthofPackage, toc, tocLen, pyver, pylibname) = \
                struct.unpack('!8sIIii64s', self.fPtr.read(self.PYINST21_COOKIE_SIZE))

        except:
            self.status('[!] Error : The file is not a pyinstaller archive')
            return False

        self.pymaj, self.pymin = (pyver//100, pyver%100) if pyver >= 100 else (pyver//10, pyver%10)
        self.status('[+] Python version: {0}.{1}'.format(self.pymaj, self.pymin))

        tailBytes = self.fileSize - self.cookiePos - (self.PYINST20_COOKIE_SIZE if self.pyinstVer == 20 else self.PYINST21_COOKIE_SIZE)
        self.overlaySize = lengthofPackage + tailBytes
        self.overlayPos = self.fileSize - self.overlaySize
        self.tableOfContentsPos = self.overlayPos + toc
        self.tableOfContentsSize = tocLen

        self.status('[+] Length of package: {0} bytes'.format(lengthofPackage))
        return True

    def parseTOC(self):
        self.fPtr.seek(self.tableOfContentsPos, os.SEEK_SET)

        self.tocList = []
        parsedLen = 0

        while parsedLen < self.tableOfContentsSize:
            (entrySize, ) = struct.unpack('!i', self.fPtr.read(4))
            nameLen = struct.calcsize('!iIIIBc')

            (entryPos, cmprsdDataSize, uncmprsdDataSize, cmprsFlag, typeCmprsData, name) = \
            struct.unpack( \
                '!IIIBc{0}s'.format(entrySize - nameLen), \
                self.fPtr.read(entrySize - 4))

            try:
                name = name.decode("utf-8").rstrip("\0")
            except UnicodeDecodeError:
                newName = str(uuid.uuid4())
                self.status('[!] Warning: File name {0} contains invalid bytes. Using random name {1}'.format(name, newName))
                name = newName
            
            if name.startswith("/"):
                name = name.lstrip("/")

            if len(name) == 0:
                name = str(uuid.uuid4())
                self.status('[!] Warning: Found an unamed file in CArchive. Using random name {0}'.format(name))

            self.tocList.append( \
                                CTOCEntry(                      \
                                    self.overlayPos + entryPos, \
                                    cmprsdDataSize,             \
                                    uncmprsdDataSize,           \
                                    cmprsFlag,                  \
                                    typeCmprsData,              \
                                    name                        \
                                ))

            parsedLen += entrySize
        self.status('[+] Found {0} files in CArchive'.format(len(self.tocList)))

    def _writeRawData(self, filepath, data):
        nm = filepath.replace('\\', os.path.sep).replace('/', os.path.sep).replace('..', '__')
        nmDir = os.path.dirname(nm)
        if nmDir != '' and not os.path.exists(nmDir):
            os.makedirs(nmDir)

        with open(nm, 'wb') as f:
            f.write(data)

    def extractFiles(self):
        self.status('[+] Beginning extraction...please standby')
        self.extractionDir = os.path.join(os.path.dirname(self.filePath), os.path.basename(self.filePath) + '_extracted')

        if not os.path.exists(self.extractionDir):
            os.mkdir(self.extractionDir)

        os.chdir(self.extractionDir)

        for i, entry in enumerate(self.tocList):
            self.fPtr.seek(entry.position, os.SEEK_SET)
            data = self.fPtr.read(entry.cmprsdDataSize)

            if entry.cmprsFlag == 1:
                try:
                    data = zlib.decompress(data)
                except zlib.error:
                    self.status('[!] Error : Failed to decompress {0}'.format(entry.name))
                    continue
                try:
                    assert len(data) == entry.uncmprsdDataSize
                except:
                    self.status('[!] Warning: Decompressed size mismatch for {0}'.format(entry.name))

            if entry.typeCmprsData == b'd' or entry.typeCmprsData == b'o':
                continue

            basePath = os.path.dirname(entry.name)
            if basePath != '':
                if not os.path.exists(basePath):
                    os.makedirs(basePath)

            if entry.typeCmprsData == b's':
                self.status('[+] Possible entry point: {0}.pyc'.format(entry.name))

                if self.pycMagic == b'\0' * 4:
                    self.barePycList.append(entry.name + '.pyc')
                self._writePyc(entry.name + '.pyc', data)

            elif entry.typeCmprsData == b'M' or entry.typeCmprsData == b'm':
                if data[2:4] == b'\r\n':
                    if self.pycMagic == b'\0' * 4: 
                        self.pycMagic = data[0:4]
                    self._writeRawData(entry.name + '.pyc', data)

                else:
                    if self.pycMagic == b'\0' * 4:
                        self.barePycList.append(entry.name + '.pyc')

                    self._writePyc(entry.name + '.pyc', data)

            else:
                self._writeRawData(entry.name, data)

                if entry.typeCmprsData == b'z' or entry.typeCmprsData == b'Z':
                    self._extractPyz(entry.name)
                    
            if i % 10 == 0 or i == len(self.tocList) - 1:
                progress = int((i + 1) / len(self.tocList) * 100)
                self.status(f"[+] Extracting files: {i+1}/{len(self.tocList)} ({progress}%)")

        self._fixBarePycs()
        
        self.status(f"[+] Extraction complete! Files extracted to: {self.extractionDir}")
        return self.extractionDir

    def _fixBarePycs(self):
        for pycFile in self.barePycList:
            try:
                with open(pycFile, 'r+b') as pycFile:
                    pycFile.write(self.pycMagic)
            except:
                pass

    def _writePyc(self, filename, data):
        with open(filename, 'wb') as pycFile:
            pycFile.write(self.pycMagic)

            if self.pymaj >= 3 and self.pymin >= 7:
                pycFile.write(b'\0' * 4)
                pycFile.write(b'\0' * 8)

            else:
                pycFile.write(b'\0' * 4)
                if self.pymaj >= 3 and self.pymin >= 3:
                    pycFile.write(b'\0' * 4)

            pycFile.write(data)

    def _extractPyz(self, name):
        dirName =  name + '_extracted'
        if not os.path.exists(dirName):
            os.mkdir(dirName)

        with open(name, 'rb') as f:
            pyzMagic = f.read(4)
            try:
                assert pyzMagic == b'PYZ\0'
            except:
                self.status(f'[!] Warning: {name} is not a valid PYZ archive')
                return

            pyzPycMagic = f.read(4)

            if self.pycMagic == b'\0' * 4:
                self.pycMagic = pyzPycMagic

            elif self.pycMagic != pyzPycMagic:
                self.pycMagic = pyzPycMagic
                self.status('[!] Warning: pyc magic of files inside PYZ archive are different from those in CArchive')

            pymaj = sys.version_info.major
            pymin = sys.version_info.minor
            if self.pymaj != pymaj or self.pymin != pymin:
                self.status(f'[!] Warning: This script is running in Python {pymaj}.{pymin} but the archive was built with Python {self.pymaj}.{self.pymin}')
                self.status('[!] Attempting to extract PYZ contents anyway...')

            (tocPosition, ) = struct.unpack('!i', f.read(4))
            f.seek(tocPosition, os.SEEK_SET)

            try:
                toc = marshal.load(f)
            except:
                self.status('[!] Unmarshalling FAILED. Cannot extract {0}. Extracting remaining files.'.format(name))
                return

            self.status('[+] Found {0} files in PYZ archive'.format(len(toc)))

            if type(toc) == list:
                toc = dict(toc)

            for i, key in enumerate(toc.keys()):
                (ispkg, pos, length) = toc[key]
                f.seek(pos, os.SEEK_SET)
                fileName = key

                try:
                    fileName = fileName.decode('utf-8')
                except:
                    pass

                fileName = fileName.replace('..', '__').replace('.', os.path.sep)

                if ispkg == 1:
                    filePath = os.path.join(dirName, fileName, '__init__.pyc')

                else:
                    filePath = os.path.join(dirName, fileName + '.pyc')

                fileDir = os.path.dirname(filePath)
                if not os.path.exists(fileDir):
                    os.makedirs(fileDir)

                try:
                    data = f.read(length)
                    data = zlib.decompress(data)
                except:
                    self.status('[!] Error: Failed to decompress {0}, probably encrypted. Extracting as is.'.format(filePath))
                    open(filePath + '.encrypted', 'wb').write(data)
                else:
                    self._writePyc(filePath, data)
                
                if i % 20 == 0 or i == len(toc.keys()) - 1:
                    progress = int((i + 1) / len(toc.keys()) * 100)
                    self.status(f"[+] Extracting PYZ contents: {i+1}/{len(toc.keys())} ({progress}%)")

class CTOCEntry:
    def __init__(self, position, cmprsdDataSize, uncmprsdDataSize, cmprsFlag, typeCmprsData, name):
        self.position = position
        self.cmprsdDataSize = cmprsdDataSize
        self.uncmprsdDataSize = uncmprsdDataSize
        self.cmprsFlag = cmprsFlag
        self.typeCmprsData = typeCmprsData
        self.name = name

class PythonDecompilerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.batch_files = []
        self.encrypted_files = []
        
    def initUI(self):
        self.setWindowTitle('PyGlimmer  By: yoruaki  公众号：夜秋的小屋')
        self.setGeometry(100, 100, 900, 700)
        
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
        self.decompiler_combo.addItems(["uncompyle6", "decompyle3", "pycdc", "pycdas"])
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
        self.batch_decompiler_combo.addItems(["uncompyle6", "decompyle3", "pycdc", "pycdas"])
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
        
        self.batch_decompile_button = QPushButton("批量反编译")
        self.batch_decompile_button.setStyleSheet(self.get_button_style())
        self.batch_decompile_button.clicked.connect(self.batch_decompile)
        self.batch_decompile_button.setEnabled(False)
        
        batch_layout.addWidget(batch_file_section)
        batch_layout.addWidget(batch_decompiler_section)
        batch_layout.addWidget(progress_section)
        batch_layout.addWidget(self.batch_decompile_button)
        
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
        self.python_version_combo.addItems(["2.7", "3.0", "3.1", "3.2", "3.3", "3.4", "3.5", "3.6", "3.7", "3.8", "3.9", "3.10"])
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
        
        bytecode_tab = QWidget()
        bytecode_layout = QVBoxLayout(bytecode_tab)
        bytecode_layout.setSpacing(10)
        
        bytecode_file_section = QGroupBox("选择PYC文件")
        bytecode_file_section.setStyleSheet("""
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
        bytecode_file_layout = QHBoxLayout()
        
        self.bytecode_file_label = QLabel("未选择文件")
        self.bytecode_browse_button = QPushButton("浏览...")
        self.bytecode_browse_button.setStyleSheet(self.get_button_style())
        self.bytecode_browse_button.clicked.connect(self.browse_bytecode_file)
        
        bytecode_file_layout.addWidget(self.bytecode_file_label, 1)
        bytecode_file_layout.addWidget(self.bytecode_browse_button)
        bytecode_file_section.setLayout(bytecode_file_layout)
        
        bytecode_mode_section = QGroupBox("显示模式")
        bytecode_mode_section.setStyleSheet("""
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
        bytecode_mode_layout = QHBoxLayout()
        
        self.bytecode_mode_group = QButtonGroup(self)
        
        self.bytecode_mode_radio = QRadioButton("查看字节码")
        self.hex_mode_radio = QRadioButton("查看十六进制")
        self.text_mode_radio = QRadioButton("查看文本内容")
        
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
        
        self.bytecode_mode_radio.setStyleSheet(radio_style)
        self.hex_mode_radio.setStyleSheet(radio_style)
        self.text_mode_radio.setStyleSheet(radio_style)
        
        self.bytecode_mode_group.addButton(self.bytecode_mode_radio, 1)
        self.bytecode_mode_group.addButton(self.hex_mode_radio, 2)
        self.bytecode_mode_group.addButton(self.text_mode_radio, 3)
        
        self.bytecode_mode_radio.setChecked(True)
        
        bytecode_mode_layout.addWidget(self.bytecode_mode_radio)
        bytecode_mode_layout.addWidget(self.hex_mode_radio)
        bytecode_mode_layout.addWidget(self.text_mode_radio)
        
        bytecode_mode_section.setLayout(bytecode_mode_layout)
        
        self.show_bytecode_button = QPushButton("显示内容")
        self.show_bytecode_button.setStyleSheet(self.get_button_style())
        self.show_bytecode_button.clicked.connect(self.show_bytecode)
        self.show_bytecode_button.setEnabled(False)
        
        bytecode_results_section = QGroupBox("查看结果")
        bytecode_results_section.setStyleSheet("""
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
        bytecode_results_layout = QVBoxLayout()
        
        self.bytecode_results_text = QTextEdit()
        self.bytecode_results_text.setReadOnly(True)
        self.bytecode_results_text.setFont(QFont("Courier", 10))
        self.bytecode_results_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #F5A742;
                border-radius: 4px;
                padding: 5px;
                background-color: #FFFFFF;
                color: #333333;
            }
        """)
        
        bytecode_results_layout.addWidget(self.bytecode_results_text)
        bytecode_results_section.setLayout(bytecode_results_layout)
        
        bytecode_layout.addWidget(bytecode_file_section)
        bytecode_layout.addWidget(bytecode_mode_section)
        bytecode_layout.addWidget(self.show_bytecode_button)
        bytecode_layout.addWidget(bytecode_results_section, 1)
        
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
        pyinstaller_layout.addWidget(version_tip_label)
        pyinstaller_layout.addWidget(pyinstaller_progress_section)
        pyinstaller_layout.addWidget(self.extract_pyinstaller_button)
        pyinstaller_layout.addWidget(pyinstaller_results_section, 1)
        
        self.tab_widget.addTab(single_tab, "单文件反编译")
        self.tab_widget.addTab(batch_tab, "批量反编译")
        self.tab_widget.addTab(decrypt_tab, "PYC解密")
        self.tab_widget.addTab(bytecode_tab, "字节码/十六进制/文本内容查看")
        self.tab_widget.addTab(pyinstaller_tab, "PyInstaller解包")
        
        main_layout.addWidget(self.tab_widget)
        
        about_button = QPushButton("关于")
        about_button.setStyleSheet(self.get_button_style())
        about_button.clicked.connect(self.show_about_dialog)
        
        about_button.setFixedHeight(30)
        about_button.setMaximumWidth(150)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(about_button)
        
        main_layout.addLayout(button_layout)
    
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
        self.logo_frame = QFrame(self)
        self.logo_frame.setObjectName("logoFrame")
        
        logo_size = 75
        frame_size = logo_size + 10
        self.logo_frame.setFixedSize(frame_size, frame_size)
        
        self.logo_label = QLabel(self.logo_frame)
        self.logo_label.setObjectName("logoLabel")
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.logo_label.move(5, 5)
        self.logo_label.setFixedSize(logo_size, logo_size)
        
        logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "image", "logo.png")
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            pixmap = pixmap.scaled(logo_size, logo_size, 
                                  Qt.AspectRatioMode.KeepAspectRatio, 
                                  Qt.TransformationMode.SmoothTransformation)
            self.logo_label.setPixmap(pixmap)
            
            self.logo_frame.setStyleSheet("""
                #logoFrame {
                    background: qradialgradient(
                        cx: 0.5, cy: 0.5, radius: 0.8, 
                        fx: 0.5, fy: 0.5, 
                        stop: 0 rgba(255, 248, 238, 180), 
                        stop: 0.7 rgba(255, 248, 238, 120), 
                        stop: 1 rgba(255, 248, 238, 0)
                    );
                    border-radius: """ + str(frame_size//2) + """px;
                }
                #logoLabel {
                    background-color: transparent;
                    opacity: 0.9;
                }
            """)
            
            shadow = QGraphicsDropShadowEffect(self)
            shadow.setBlurRadius(15)
            shadow.setColor(QColor(0, 0, 0, 40))
            shadow.setOffset(2, 2)
            self.logo_label.setGraphicsEffect(shadow)
            
            self.logo_frame.setParent(self)
            self.resizeEvent = self.on_resize
            
            self.position_logo()
    
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
    
    def browse_batch_files(self):
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "选择多个PYC文件", "", "Python字节码文件 (*.pyc);;所有文件 (*)"
        )
        
        if file_paths:
            self.batch_files.extend(file_paths)
            self.update_batch_files_list()
            self.batch_decompile_button.setEnabled(len(self.batch_files) > 0)
    
    def browse_batch_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "选择包含PYC文件的文件夹")
        
        if directory:
            self.batch_base_dir = directory
            pyc_files = get_files_with_extension(directory, ['.pyc'])
            if pyc_files:
                self.batch_files.extend(pyc_files)
                self.update_batch_files_list()
                self.batch_decompile_button.setEnabled(len(self.batch_files) > 0)
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
                extract_dir = os.path.join(os.path.dirname(pyc_file), "extract")
                if not os.path.exists(extract_dir):
                    os.makedirs(extract_dir)
                
                output_filename = os.path.basename(os.path.splitext(pyc_file)[0]) + '.py'
                output_file = os.path.join(extract_dir, output_filename)
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(result)
                self.show_info("文件已保存", f"输出已保存到 {normalize_path_for_display(output_file)}")
                
        except Exception as e:
            self.show_error("反编译错误", str(e))
    
    def batch_decompile(self):
        if not self.batch_files:
            self.show_error("没有文件", "请先选择要反编译的PYC文件。")
            return
        
        decompiler = self.batch_decompiler_combo.currentText()
        total_files = len(self.batch_files)
        success_count = 0
        failed_files = []
        
        self.progress_bar.setValue(0)
        self.progress_label.setText("正在反编译...")
        
       
        if hasattr(self, 'batch_base_dir'):
            extract_base_dir = os.path.join(os.path.dirname(self.batch_base_dir), "extract")
        else:
            extract_base_dir = os.path.join(os.path.dirname(self.batch_files[0]), "extract")
        
        for i, pyc_file in enumerate(self.batch_files):
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
        
        
        self.progress_label.setText("反编译完成")
        
        if failed_files:
            error_message = f"成功: {success_count}/{total_files}\n\n失败的文件:\n"
            for file_path, error in failed_files:
                error_message += f"- {normalize_path_for_display(os.path.basename(file_path))}: {error}\n"
            self.show_error("批量反编译结果", error_message)
        else:
            self.show_info("批量反编译结果", f"所有{total_files}个文件都已成功反编译。")
    
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
        elif decompiler == "pycdas":
            return self.run_pycdas(pyc_file)
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
    
    def run_pycdas(self, pyc_file):
        pycdas_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Decompiler", "pycdas")
        return self.run_as_subprocess([pycdas_path, pyc_file])
    
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
    
    def browse_bytecode_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择PYC文件", "", "Python字节码文件 (*.pyc);;所有文件 (*)"
        )
        
        if file_path:
            self.bytecode_file_label.setText(normalize_path_for_display(file_path))
            self.show_bytecode_button.setEnabled(True)
    
    def show_bytecode(self):
        pyc_file = self.bytecode_file_label.text()
        if not os.path.exists(pyc_file):
            self.show_error("文件未找到", "所选文件不存在。")
            return
        
        try:
            self.bytecode_results_text.clear()
            
            if self.bytecode_mode_radio.isChecked():
                result = self.parse_pyc_bytecode(pyc_file)
                self.bytecode_results_text.setText(result)
            elif self.hex_mode_radio.isChecked():
                result = self.hex_dump_pyc_file(pyc_file)
                self.bytecode_results_text.setText(result)
            else:
                result = self.text_dump_pyc_file(pyc_file)
                self.bytecode_results_text.setText(result)
                
        except Exception as e:
            self.show_error("文件解析错误", str(e))
    
    def parse_pyc_bytecode(self, pyc_file):
        with open(pyc_file, 'rb') as f:
            file_data = f.read()
            file_size = len(file_data)
            
            output = []
            output.append(f"文件: {normalize_path_for_display(os.path.basename(pyc_file))}")
            output.append(f"文件大小: {file_size} 字节")
            
            if len(file_data) >= 4:
                magic_bytes = file_data[:4]
                magic_hex = ' '.join(f'{b:02X}' for b in magic_bytes)
                output.append(f"魔数: {magic_hex}")
                
                if magic_bytes in MAGIC_NUMBERS:
                    python_version = MAGIC_NUMBERS[magic_bytes]
                    output.append(f"推测的Python版本: {python_version}")
                else:
                    output.append("未知的Python版本魔数")
            
            common_offsets = [0, 4, 8, 12, 16]
            success = False
            
            for offset in common_offsets:
                success, result, used_offset = self._try_parse_with_offset(file_data, offset)
                if success:
                    output.append(f"使用偏移量: {used_offset} 字节解析成功")
                    break
            
            if not success:
                output.append("尝试扩展偏移量范围...")
                for offset in range(20, min(200, file_size), 4):
                    if offset not in common_offsets:
                        success, result, used_offset = self._try_parse_with_offset(file_data, offset)
                        if success:
                            output.append(f"使用偏移量: {used_offset} 字节解析成功")
                            break
            
            if success:
                output.append("\n字节码反汇编:")
                output.append(result)
            else:
                output.append("\n无法解析文件。可能原因：")
                output.append("1. 文件格式不是有效的Python字节码")
                output.append("2. 文件已被严重损坏或修改")
            
            return "\n".join(output)
    
    def _try_parse_with_offset(self, file_data, offset):
        try:
            if offset >= len(file_data):
                return False, "", offset
                
            data = file_data[offset:]
            
            code = marshal.loads(data)
            
            import io
            buffer = io.StringIO()
            
            from contextlib import redirect_stdout
            with redirect_stdout(buffer):
                dis.dis(code)
            
            disassembly = buffer.getvalue()
            
            return True, disassembly, offset
        except Exception:
            return False, "", offset
    
    def _hex_dump(self, data):
        hex_str = []
        offset = 0
        while offset < len(data):
            chunk = data[offset:offset+16]
            hex_part = ' '.join(f'{b:02X}' for b in chunk)
            ascii_part = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in chunk)
            
            hex_str.append(f"{offset:04X}: {hex_part:<48} {ascii_part}")
            offset += 16
        
        return '\n'.join(hex_str)
    
    def hex_dump_pyc_file(self, pyc_file):
        with open(pyc_file, 'rb') as f:
            file_data = f.read()
            file_size = len(file_data)
            
            output = []
            output.append(f"文件: {normalize_path_for_display(os.path.basename(pyc_file))}")
            output.append(f"文件大小: {file_size} 字节")
            
            if len(file_data) >= 4:
                magic_bytes = file_data[:4]
                magic_hex = ' '.join(f'{b:02X}' for b in magic_bytes)
                output.append(f"魔数: {magic_hex}")
                
                if magic_bytes in MAGIC_NUMBERS:
                    python_version = MAGIC_NUMBERS[magic_bytes]
                    output.append(f"推测的Python版本: {python_version}")
                else:
                    output.append("未知的Python版本魔数")
            
            output.append("\n十六进制:")
            
            hex_dump = self._hex_dump(file_data)
            output.append(hex_dump)
            
            return "\n".join(output)
    
    def text_dump_pyc_file(self, pyc_file):
        with open(pyc_file, 'rb') as f:
            file_data = f.read()
            file_size = len(file_data)
            
            output = []
            output.append(f"文件: {normalize_path_for_display(os.path.basename(pyc_file))}")
            output.append(f"文件大小: {file_size} 字节")
            
            if len(file_data) >= 4:
                magic_bytes = file_data[:4]
                magic_hex = ' '.join(f'{b:02X}' for b in magic_bytes)
                output.append(f"魔数: {magic_hex}")
                
                if magic_bytes in MAGIC_NUMBERS:
                    python_version = MAGIC_NUMBERS[magic_bytes]
                    output.append(f"推测的Python版本: {python_version}")
                else:
                    output.append("未知的Python版本魔数")
            
            output.append("\n文本内容:")
            
            text_content = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in file_data)
            output.append(text_content)
            
            return "\n".join(output)

    def browse_pyinstaller_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择PyInstaller打包的可执行文件", "", "可执行文件 (*.exe);;所有文件 (*)"
        )
        
        if file_path:
            self.pyinstaller_file_label.setText(normalize_path_for_display(file_path))
            self.extract_pyinstaller_button.setEnabled(True)
            self.pyinstaller_results_text.clear()
            self.pyinstaller_progress_label.setText("就绪")
    
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
        
        github_label = QLabel("https://github.com/yoruak1")
        github_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        github_label.setStyleSheet("""
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
        
        wechat_label = QLabel("绿泡泡公众号：夜秋的小屋")
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

def main():
    app = QApplication(sys.argv)
    
    logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "image", "logo.png")
    if os.path.exists(logo_path):
        app.setWindowIcon(QIcon(logo_path))
        
    window = PythonDecompilerApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 