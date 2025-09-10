import os
import sys
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes
import base64

def encrypt_file(input_file, key_file, output_file):
    # 读取密钥文件
    with open(key_file, 'r') as f:
        key_content = f.read().strip()
    
    # 确保密钥长度为16, 24或32字节(AES要求)
    key = key_content.encode('utf-8')
    if len(key) not in [16, 24, 32]:
        # 如果密钥长度不符合要求，使用SHA256哈希并截取适当长度
        from Crypto.Hash import SHA256
        h = SHA256.new()
        h.update(key)
        key = h.digest()[:32]  # 使用32字节密钥(AES-256)
    
    # 读取待加密文件
    with open(input_file, 'rb') as f:
        plaintext = f.read()
    
    # 生成随机初始化向量(IV)
    iv = get_random_bytes(16)
    
    # 创建AES加密器
    cipher = AES.new(key, AES.MODE_CBC, iv)
    
    # 加密数据
    ciphertext = cipher.encrypt(pad(plaintext, AES.block_size))
    
    # 将IV和密文一起保存
    with open(output_file, 'wb') as f:
        f.write(iv)
        f.write(ciphertext)
    
    print(f"文件已加密并保存到: {output_file}")

def decrypt_file(input_file, key_file, output_file):
    # 读取密钥文件
    with open(key_file, 'r') as f:
        key_content = f.read().strip()
    
    # 确保密钥长度为16, 24或32字节
    key = key_content.encode('utf-8')
    if len(key) not in [16, 24, 32]:
        from Crypto.Hash import SHA256
        h = SHA256.new()
        h.update(key)
        key = h.digest()[:32]
    
    # 读取加密文件
    with open(input_file, 'rb') as f:
        iv = f.read(16)  # 前16字节是IV
        ciphertext = f.read()  # 剩余部分是密文
    
    # 创建AES解密器
    cipher = AES.new(key, AES.MODE_CBC, iv)
    
    # 解密数据
    try:
        decrypted_data = unpad(cipher.decrypt(ciphertext), AES.block_size)
        
        # 保存解密后的文件
        with open(output_file, 'wb') as f:
            f.write(decrypted_data)
        
        print(f"文件已解密并保存到: {output_file}")
    except ValueError:
        print("解密失败: 可能是密钥不正确或文件已损坏")

def main():
    if len(sys.argv) != 4:
        print("用法: python run.py <输入文件> <密钥文件> <输出文件>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    key_file = sys.argv[2]
    output_file = sys.argv[3]
    
    # 检查文件是否存在
    if not os.path.exists(input_file):
        print(f"错误: 输入文件 '{input_file}' 不存在")
        sys.exit(1)
    
    if not os.path.exists(key_file):
        print(f"错误: 密钥文件 '{key_file}' 不存在")
        sys.exit(1)
    
    # 根据文件扩展名判断是加密还是解密
    if input_file.endswith('.enc'):
        decrypt_file(input_file, key_file, output_file)
    else:
        encrypt_file(input_file, key_file, output_file)

if __name__ == "__main__":
    main()