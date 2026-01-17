#!/usr/bin/env python3
"""
将 verilog hex format 转换为纯十六进制格式

输入格式 (verilog hex format):
@00000000
37 01 02 00 EF 10 00 04 13 05 F0 0F ...
@00001000
...

输出格式 (纯十六进制):
37010200
ef100004
1305f00f
...
"""

import sys
import re
from pathlib import Path


def parse_verilog_hex(filepath):
    """
    解析 verilog hex format 文件
    
    返回: dict {address: [bytes]}
    """
    data = {}
    current_addr = None
    current_bytes = []
    
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            
            # 空行跳过
            if not line:
                continue
            
            # 地址标记 @xxxxxxxx
            if line.startswith('@'):
                # 保存之前的地址段
                if current_addr is not None and current_bytes:
                    data[current_addr] = current_bytes
                
                # 解析新地址
                addr_str = line[1:]
                current_addr = int(addr_str, 16)
                current_bytes = []
            else:
                # 数据行：空格分隔的字节
                bytes_list = line.split()
                for b in bytes_list:
                    current_bytes.append(int(b, 16))
        
        # 保存最后一个地址段
        if current_addr is not None and current_bytes:
            data[current_addr] = current_bytes
    
    return data


def merge_to_flat_memory(data):
    """
    将分段数据合并为平坦的内存映像
    
    返回: dict {address: byte}
    """
    memory = {}
    
    for addr, bytes_list in data.items():
        for i, byte_val in enumerate(bytes_list):
            memory[addr + i] = byte_val
    
    return memory


def convert_to_hex_format(memory):
    """
    将内存映像转换为纯十六进制格式
    
    返回: list of (address, word32)
    """
    # 指令替换映射（停机指令转换）
    INSTRUCTION_REPLACEMENTS = {
        0x0ff00513: 0xfe000fa3,  # addi a0, zero, -1 -> c.sw zero, -8(sp)
    }
    
    # 找到最小和最大地址
    if not memory:
        return []
    
    min_addr = min(memory.keys())
    max_addr = max(memory.keys())
    
    # 按字对齐（4字节）
    min_addr = min_addr & ~0x3
    max_addr = (max_addr + 3) & ~0x3
    
    # 生成32位字列表
    words = []
    for addr in range(min_addr, max_addr, 4):
        # 小端序：低字节在低地址
        word = 0
        for i in range(4):
            byte_addr = addr + i
            if byte_addr in memory:
                word |= (memory[byte_addr] & 0xFF) << (i * 8)

        # 应用指令替换
        if word in INSTRUCTION_REPLACEMENTS:
            word = INSTRUCTION_REPLACEMENTS[word]

        words.append((addr, word))
    
    return words


def write_hex_format(output_path, words):
    """
    写入纯十六进制格式文件
    """
    with open(output_path, 'w') as f:
        for addr, word in words:
            # 格式：xxxxxxxx // address: 0x...
            f.write(f"{word:08x}\n")


def main():
    if len(sys.argv) < 2:
        print("用法: python convert_hex.py <input_file> [output_file]")
        print("示例: python convert_hex.py array_test1.data array_test1.exe")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    # 默认输出文件名：将 .data 改为 .exe
    output_file = str('test.exe')
    
    # 解析输入文件
    print(f"读取输入文件: {input_file}")
    data = parse_verilog_hex(input_file)
    print(f"找到 {len(data)} 个地址段")
    
    # 合并为平坦内存
    memory = merge_to_flat_memory(data)
    print(f"总字节数: {len(memory)}")
    
    # 转换为32位字格式
    words = convert_to_hex_format(memory)
    print(f"生成 {len(words)} 个32位字")
    
    # 写入输出文件
    write_hex_format(output_file, words)
    print(f"输出文件: {output_file}")
    print("转换完成!")


if __name__ == "__main__":
    main()
