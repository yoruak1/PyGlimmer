import os
import zlib
import tinyaes

MAGIC_HEADERS = {
    "2.7": b'\x03\xf3\x0d\x0a\0\0\0\0',
    "3.0": b'\x3b\x0c\x0d\x0a\0\0\0\0',
    "3.1": b'\x4f\x0c\x0d\x0a\0\0\0\0',
    "3.2": b'\x6c\x0c\x0d\x0a\0\0\0\0',
    "3.3": b'\x9e\x0c\x0d\x0a\0\0\0\0\0\0\0\0',
    "3.4": b'\xee\x0c\x0d\x0a\0\0\0\0\0\0\0\0',
    "3.5": b'\x17\x0d\x0d\x0a\0\0\0\0\0\0\0\0',
    "3.6": b'\x33\x0d\x0d\x0a\0\0\0\0\0\0\0\0',
    "3.7": b'\x42\x0d\x0d\x0a\0\0\0\0\0\0\0\0\0\0\0\0',
    "3.8": b'\x55\x0d\x0d\x0a\0\0\0\0\0\0\0\0\0\0\0\0',
    "3.9": b'\x61\x0d\x0d\x0a\0\0\0\0\0\0\0\0\0\0\0\0',
    "3.10": b'\x6f\x0d\x0d\x0a\0\0\0\0\0\0\0\0\0\0\0\0'
}

CRYPT_BLOCK_SIZE = 16

def decrypt_pyc_files(encrypted_files, key, python_version, output_dir=None):
    if python_version not in MAGIC_HEADERS:
        raise ValueError(f"不支持的Python版本: {python_version}。支持的版本有: {', '.join(MAGIC_HEADERS.keys())}")
    
    magic_header = MAGIC_HEADERS[python_version]
    success_count = 0
    failed_files = []
    
    for encrypted_file in encrypted_files:
        try:
            if not os.path.exists(encrypted_file):
                failed_files.append((encrypted_file, "文件不存在"))
                continue
                
            if output_dir:
                out_dir = output_dir
            else:
                out_dir = os.path.join(os.path.dirname(encrypted_file), "extract")
            
            if not os.path.exists(out_dir):
                os.makedirs(out_dir)
            
            base_name = os.path.basename(encrypted_file)
            if base_name.endswith('.pyc.encrypted'):
                output_name = base_name[:-10]
            else:
                output_name = base_name + ".decrypted"
            
            output_path = os.path.join(out_dir, output_name)
            
            with open(encrypted_file, 'rb') as inf, open(output_path, 'wb') as outf:
                iv = inf.read(CRYPT_BLOCK_SIZE)
                
                cipher = tinyaes.AES(key, iv)
                
                plaintext = zlib.decompress(cipher.CTR_xcrypt_buffer(inf.read()))
                
                outf.write(magic_header)
                
                outf.write(plaintext)
            
            success_count += 1
            
        except Exception as e:
            failed_files.append((encrypted_file, str(e)))
    
    return success_count, failed_files 