import os
import sys
import struct
import zlib
import marshal
import uuid


def normalize_path_for_display(path):
    """标准化路径显示格式"""
    return path.replace('\\', '/')


class CTOCEntry:
    """目录条目类，用于存储PyInstaller归档中的文件信息"""
    
    def __init__(self, position, cmprsdDataSize, uncmprsdDataSize, cmprsFlag, typeCmprsData, name):
        self.position = position
        self.cmprsdDataSize = cmprsdDataSize
        self.uncmprsdDataSize = uncmprsdDataSize
        self.cmprsFlag = cmprsFlag
        self.typeCmprsData = typeCmprsData
        self.name = name


class PyInstArchive:
    """PyInstaller归档解包器"""
    
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
        """设置状态回调函数"""
        self.status_callback = callback

    def status(self, msg):
        """输出状态信息"""
        if self.status_callback:
            self.status_callback(msg)
        else:
            print(msg)

    def open(self):
        """打开PyInstaller文件"""
        try:
            self.fPtr = open(self.filePath, 'rb')
            self.fileSize = os.stat(self.filePath).st_size
        except:
            self.status('[!] Error: Could not open {0}'.format(self.filePath))
            return False
        return True

    def close(self):
        """关闭文件句柄"""
        try:
            self.fPtr.close()
        except:
            pass

    def checkFile(self):
        """检查文件是否为有效的PyInstaller归档"""
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
        """获取CArchive信息"""
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
        """解析目录表"""
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
        """写入原始数据到文件"""
        nm = filepath.replace('\\', os.path.sep).replace('/', os.path.sep).replace('..', '__')
        nmDir = os.path.dirname(nm)
        if nmDir != '' and not os.path.exists(nmDir):
            os.makedirs(nmDir)

        with open(nm, 'wb') as f:
            f.write(data)

    def extractFiles(self):
        """提取所有文件"""
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
        """修复裸pyc文件的魔数头"""
        for pycFile in self.barePycList:
            try:
                with open(pycFile, 'r+b') as pycFile:
                    pycFile.write(self.pycMagic)
            except:
                pass

    def _writePyc(self, filename, data):
        """写入pyc文件，添加正确的魔数头"""
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
        """提取PYZ归档文件"""
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


def extract_pyinstaller(exe_path, status_callback=None):
    """
    便捷函数：解包PyInstaller程序
    
    参数:
        exe_path: PyInstaller打包的exe文件路径
        status_callback: 状态回调函数，用于显示进度信息
    
    返回:
        成功时返回解包目录路径，失败时返回None
    """
    try:
        archive = PyInstArchive(exe_path)
        if status_callback:
            archive.set_status_callback(status_callback)
        
        if archive.open():
            if archive.checkFile():
                if archive.getCArchiveInfo():
                    archive.parseTOC()
                    extraction_dir = archive.extractFiles()
                    archive.close()
                    return extraction_dir
            
            archive.close()
        
        return None
        
    except Exception as e:
        if status_callback:
            status_callback(f"[!] 解包过程中发生错误: {str(e)}")
        return None


if __name__ == "__main__":
    """命令行使用示例"""
    if len(sys.argv) != 2:
        print("用法: python pyinstxtractor.py <PyInstaller程序路径>")
        sys.exit(1)
    
    exe_path = sys.argv[1]
    if not os.path.exists(exe_path):
        print(f"错误: 文件 {exe_path} 不存在")
        sys.exit(1)
    
    result = extract_pyinstaller(exe_path)
    if result:
        print(f"解包成功！文件保存在: {result}")
    else:
        print("解包失败！")
