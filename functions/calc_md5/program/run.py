import argparse
import hashlib
import os
import sys
from datetime import datetime

def calculate_hashes(file_path):
    """
    计算文件的三种哈希值（MD5, SHA-1, SHA-256）
    使用分块读取处理大文件
    返回包含文件信息和哈希值的字典
    """
    if not os.path.exists(file_path):
        sys.exit(f"错误: 文件 '{file_path}' 不存在")
    
    try:
        # 获取文件基本信息
        file_size = os.path.getsize(file_path)
        mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
        
        # 初始化哈希对象
        hash_md5 = hashlib.md5()
        hash_sha1 = hashlib.sha1()
        hash_sha256 = hashlib.sha256()
        
        # 读取文件并更新哈希
        with open(file_path, "rb") as f:
            # 显示进度提示（处理大文件时）
            if file_size > 1024 * 1024:  # >1MB文件显示进度
                print(f"正在处理 {os.path.basename(file_path)} ({file_size/1024/1024:.2f} MB)...")
            
            # 分块读取（10MB/块）
            chunk_size = 10 * 1024 * 1024
            bytes_processed = 0
            
            while chunk := f.read(chunk_size):
                hash_md5.update(chunk)
                hash_sha1.update(chunk)
                hash_sha256.update(chunk)
                bytes_processed += len(chunk)
                
                # 显示进度条（仅当文件大于1MB时）
                if file_size > 1024 * 1024:
                    percent = bytes_processed / file_size * 100
                    sys.stdout.write(f"\r进度: [{percent:.1f}%]")
                    sys.stdout.flush()
        
        # 完成进度条显示
        if file_size > 1024 * 1024:
            print("\r", end="")
        
        return {
            "file_name": os.path.basename(file_path),
            "file_path": os.path.abspath(file_path),
            "file_size": file_size,
            "last_modified": mod_time.strftime("%Y-%m-%d %H:%M:%S"),
            "md5": hash_md5.hexdigest(),
            "sha1": hash_sha1.hexdigest(),
            "sha256": hash_sha256.hexdigest()
        }
    
    except PermissionError:
        sys.exit(f"错误: 没有权限读取文件 '{file_path}'")
    except Exception as e:
        sys.exit(f"处理文件时出错: {str(e)}")

def save_results_to_file(data, output_path):
    """将哈希结果保存到指定文件"""
    try:
        # 确保输出目录存在
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            
        with open(output_path, "w") as f:
            f.write(f"文件哈希校验报告\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("-" * 60 + "\n")
            f.write(f"文件名: {data['file_name']}\n")
            f.write(f"完整路径: {data['file_path']}\n")
            f.write(f"文件大小: {data['file_size']:,} 字节\n")
            f.write(f"最后修改: {data['last_modified']}\n")
            f.write("-" * 60 + "\n")
            f.write(f"MD5:    {data['md5']}\n")
            f.write(f"SHA-1:  {data['sha1']}\n")
            f.write(f"SHA-256: {data['sha256']}\n")
            f.write("-" * 60 + "\n")
        
        print(f"\n结果已保存到: {os.path.abspath(output_path)}")
    
    except Exception as e:
        sys.exit(f"写入输出文件时出错: {str(e)}")

def main():
    # 设置命令行参数解析器
    parser = argparse.ArgumentParser(
        description="计算文件的三种哈希值（MD5、SHA-1、SHA-256）并保存结果",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    # 使用两个位置参数（输入文件和输出文件）
    parser.add_argument("input_file", help="要计算哈希值的文件路径")
    parser.add_argument("output_file", help="保存哈希结果的输出文件路径")
    
    args = parser.parse_args()
    
    # 计算哈希值
    file_data = calculate_hashes(args.input_file)
    
    # 在控制台显示结果
    print("\n文件哈希计算结果:")
    print(f"文件名:    {file_data['file_name']}")
    print(f"大小:      {file_data['file_size']:,} 字节")
    print(f"最后修改:  {file_data['last_modified']}")
    print(f"MD5:      {file_data['md5']}")
    print(f"SHA-1:    {file_data['sha1']}")
    print(f"SHA-256:  {file_data['sha256']}")
    
    # 保存结果到文件
    save_results_to_file(file_data, args.output_file)

if __name__ == "__main__":
    main()