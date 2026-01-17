#!/usr/bin/env python3
"""
十六进制文件转换为 Verilog hex 格式
输入格式: 每行一个32位十六进制数，如 00020137
输出格式: Verilog hex memory 格式
"""

import sys
import os
from pathlib import Path

def hex_to_verilog_hex(input_file, output_file, words_per_line=4, byte_order='little'):
    """
    将十六进制文件转换为 Verilog hex 格式
    
    Args:
        input_file: 输入文件名
        output_file: 输出文件名
        words_per_line: 每行显示多少个字节（默认为4）
        byte_order: 字节序，'little' 小端或 'big' 大端
    """
    try:
        # 读取输入文件
        with open(input_file, 'r') as f:
            lines = [line.strip() for line in f if line.strip()]
        
        # 检查是否有空文件
        if not lines:
            print("警告: 输入文件为空")
            return False
        
        # 处理每一行
        hex_data = []
        line_number = 0
        
        for line in lines:
            line_number += 1
            hex_str = line.strip()
            
            # 移除可能的 '0x' 前缀
            if hex_str.startswith(('0x', '0X')):
                hex_str = hex_str[2:]
            
            # 检查长度是否为8（32位）
            if len(hex_str) != 8:
                hex_str = hex_str[:8]  # 取最前面 8 位
            
            hex_data.append(hex_str)
        
        # 转换为字节并写入输出文件
        with open(output_file, 'w') as f:
            address = 0
            
            for i in range(0, len(hex_data), words_per_line):
                # 写入地址行
                f.write(f"@{address:08X}\n")
                
                # 写入数据行
                line_bytes = []
                
                for j in range(words_per_line):
                    if i + j < len(hex_data):
                        hex_value = hex_data[i + j]
                        
                        # 将32位十六进制分成4个字节
                        if byte_order == 'little':  # 小端序
                            bytes_list = [
                                hex_value[6:8],  # 最低字节
                                hex_value[4:6],
                                hex_value[2:4],
                                hex_value[0:2]   # 最高字节
                            ]
                        else:  # 大端序
                            bytes_list = [
                                hex_value[0:2],  # 最高字节
                                hex_value[2:4],
                                hex_value[4:6],
                                hex_value[6:8]   # 最低字节
                            ]
                        
                        line_bytes.extend(bytes_list)
                
                # 写入字节，用空格分隔
                f.write(" ".join(line_bytes) + "\n")
                
                # 更新地址（每行4个字节 * words_per_line）
                address += 4 * words_per_line
        
        print(f"转换完成: {len(hex_data)} 个32位字已写入 {output_file}")
        return True
        
    except FileNotFoundError:
        print(f"错误: 找不到文件 {input_file}")
        return False
    except Exception as e:
        print(f"错误: 转换过程中发生异常: {e}")
        return False

def batch_convert_directory(input_dir, output_dir, extension=".hex"):
    """
    批量转换目录中的所有十六进制文件
    
    Args:
        input_dir: 输入目录
        output_dir: 输出目录
        extension: 要处理的文件扩展名
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
    # 创建输出目录
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 查找所有符合条件的文件
    input_files = list(input_path.glob(f"*{extension}"))
    
    if not input_files:
        print(f"在 {input_dir} 中未找到 {extension} 文件")
        return
    
    print(f"找到 {len(input_files)} 个文件，开始批量转换...")
    
    success_count = 0
    for input_file in input_files:
        output_file = output_path / f"{input_file.stem}_verilog.hex"
        
        print(f"正在转换: {input_file.name} -> {output_file.name}")
        
        if hex_to_verilog_hex(str(input_file), str(output_file)):
            success_count += 1
    
    print(f"\n批量转换完成: {success_count}/{len(input_files)} 个文件转换成功")

def main():
    """主函数"""
    # 命令行参数处理
    if len(sys.argv) < 2:
        print("使用说明:")
        print("  1. 单个文件转换:")
        print("     python hex_to_verilog.py input.hex [output.hex]")
        print("  2. 批量目录转换:")
        print("     python hex_to_verilog.py -d input_dir output_dir")
        print("  3. 交互式模式:")
        print("     python hex_to_verilog.py")
        print()
        
        # 交互式模式
        print("=== 十六进制转 Verilog hex 格式工具 ===")
        
        mode = input("选择模式 (1=单文件, 2=批量目录): ").strip()
        
        if mode == "1":
            input_file = input("输入文件名: ").strip()
            output_file = input("输出文件名 [默认: output.hex]: ").strip()
            if not output_file:
                output_file = "output.hex"
            
            words_per_line = input("每行字节数 [默认: 4]: ").strip()
            words_per_line = int(words_per_line) if words_per_line else 4
            
            byte_order = input("字节序 (1=小端, 2=大端) [默认: 1]: ").strip()
            byte_order = 'little' if byte_order != '2' else 'big'
            
            hex_to_verilog_hex(input_file, output_file, words_per_line, byte_order)
            
        elif mode == "2":
            input_dir = input("输入目录: ").strip()
            output_dir = input("输出目录 [默认: output]: ").strip()
            if not output_dir:
                output_dir = "output"
            
            batch_convert_directory(input_dir, output_dir)
        
        else:
            print("无效的选择")
    
    elif len(sys.argv) == 2:
        # 单个文件转换，使用默认输出文件名
        input_file = sys.argv[1]
        output_file = "output.hex"
        hex_to_verilog_hex(input_file, output_file)
    
    elif len(sys.argv) == 3:
        # 单个文件转换，指定输出文件名
        input_file = sys.argv[1]
        output_file = sys.argv[2]
        hex_to_verilog_hex(input_file, output_file)
    
    elif len(sys.argv) == 4 and sys.argv[1] == "-d":
        # 批量目录转换
        input_dir = sys.argv[2]
        output_dir = sys.argv[3]
        batch_convert_directory(input_dir, output_dir)
    
    else:
        print("参数错误！")
        print("用法: python hex_to_verilog.py [input.hex] [output.hex]")
        print("或: python hex_to_verilog.py -d input_dir output_dir")

if __name__ == "__main__":
    # 如果需要创建示例文件，取消下面一行的注释
    # create_sample_input()
    
    main()