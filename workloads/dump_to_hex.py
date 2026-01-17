#!/usr/bin/env python3
import re
import sys
import os

def extract_32bit_instructions(file_path):
    """
    从.dump文件中提取所有32位指令（机器码为8个十六进制字符）
    
    参数:
        file_path: dump文件路径
    
    返回:
        列表，包含提取到的32位指令
    """
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"错误: 文件 '{file_path}' 不存在")
        return []
    except Exception as e:
        print(f"读取文件时出错: {e}")
        return []
    
    instructions = []
    in_text_section = False
    
    # 正则表达式匹配指令行，并捕获机器码部分
    # 机器码部分必须是8个十六进制字符（32位指令）
    instruction_pattern = re.compile(r'^\s+[0-9a-f]+:\s+([0-9a-f]{8})\s+(.+)$')
    
    for line in lines:
        line = line.rstrip('\n')
        
        # 检查是否进入.text段
        if 'Disassembly of section .text:' in line:
            in_text_section = True
            continue
        
        # 如果不在.text段，跳过
        if not in_text_section:
            continue
        
        # 跳过空行
        if not line.strip():
            continue
        
        # 跳过标签行（包含"<...>:"的行）
        if re.search(r'<[^>]+>:\s*$', line):
            continue
        
        # 跳过仅包含地址和冒号的行
        if re.match(r'^[0-9a-f]+\s*:\s*$', line):
            continue
        
        # 尝试匹配32位指令行
        match = instruction_pattern.match(line)
        if match:
            machine_code = match.group(1)  # 8位机器码
            instruction_text = match.group(2).strip()  # 指令文本
            
            # 去除可能的注释（如果存在）
            instruction_text = re.split(r'\s*//', instruction_text)[0].strip()
            
            # 将机器码和指令文本组合
            full_instruction = f"{machine_code}: {instruction_text}"
            instructions.append(full_instruction)
    
    return instructions

def extract_32bit_instructions_only_mnemonic(file_path):
    """
    从.dump文件中提取所有32位指令（仅指令助记符和操作数）
    
    参数:
        file_path: dump文件路径
    
    返回:
        列表，包含提取到的32位指令
    """
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"错误: 文件 '{file_path}' 不存在")
        return []
    except Exception as e:
        print(f"读取文件时出错: {e}")
        return []
    
    instructions = []
    in_text_section = False
    
    # 正则表达式匹配指令行，机器码必须是8个十六进制字符
    instruction_pattern = re.compile(r'^\s+[0-9a-f]+:\s+[0-9a-f]{8}\s+(.+)$')
    
    for line in lines:
        line = line.rstrip('\n')
        
        # 检查是否进入.text段
        if 'Disassembly of section .text:' in line:
            in_text_section = True
            continue
        
        # 如果不在.text段，跳过
        if not in_text_section:
            continue
        
        # 跳过空行
        if not line.strip():
            continue
        
        # 跳过标签行（包含"<...>:"的行）
        if re.search(r'<[^>]+>:\s*$', line):
            continue
        
        # 跳过仅包含地址和冒号的行
        if re.match(r'^[0-9a-f]+\s*:\s*$', line):
            continue
        
        # 尝试匹配32位指令行
        match = instruction_pattern.match(line)
        if match:
            instruction_text = match.group(1).strip()  # 指令文本
            
            # 去除可能的注释（如果存在）
            instruction_text = re.split(r'\s*//', instruction_text)[0].strip()
            instructions.append(instruction_text)
    
    return instructions

def write_instructions_to_file(instructions, output_path):
    """
    将指令列表写入文件
    
    参数:
        instructions: 指令列表
        output_path: 输出文件路径
    """
    try:
        with open(output_path, 'w') as f:
            for i, instr in enumerate(instructions, 1):
                f.write(f"{instr}\n")
        
        print(f"成功写入 {len(instructions)} 条32位指令到 '{output_path}'")
        return True
    except Exception as e:
        print(f"写入文件时出错: {e}")
        return False

def main():
    if len(sys.argv) < 3:
        print("用法: python extract_32bit_instructions.py <输入文件> <输出文件> [选项]")
        print("\n选项:")
        print("  --clean    仅提取指令助记符和操作数（不包含机器码）")
        print("  --hex      输出十六进制机器码（每行一个）")
        print("\n示例:")
        print("  python extract_32bit_instructions.py input.dump output.txt")
        print("  python extract_32bit_instructions.py input.dump instructions.txt --clean")
        print("  python extract_32bit_instructions.py input.dump machine_codes.txt --hex")
        return
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    # 检查输入文件是否存在
    if not os.path.exists(input_file):
        print(f"错误: 输入文件 '{input_file}' 不存在")
        return
    
    # 解析选项
    clean_mode = False
    hex_only_mode = False
    
    if len(sys.argv) > 3:
        for arg in sys.argv[3:]:
            if arg == '--clean':
                clean_mode = True
            elif arg == '--hex':
                hex_only_mode = True
    
    # 提取指令
    if hex_only_mode:
        # 仅提取十六进制机器码
        try:
            with open(input_file, 'r') as f:
                lines = f.readlines()
        except Exception as e:
            print(f"读取文件时出错: {e}")
            return
        
        machine_codes = []
        in_text_section = False
        
        # 正则表达式匹配机器码部分（8个十六进制字符）
        machine_code_pattern = re.compile(r'^\s+[0-9a-f]+:\s+([0-9a-f]{8})\s+')
        
        for line in lines:
            line = line.rstrip('\n')
            
            if 'Disassembly of section .text:' in line:
                in_text_section = True
                continue
            
            if not in_text_section:
                continue
            
            if not line.strip():
                continue
            
            # 跳过标签行
            if re.search(r'<[^>]+>:\s*$', line):
                continue
            
            # 跳过仅包含地址和冒号的行
            if re.match(r'^[0-9a-f]+\s*:\s*$', line):
                continue
            
            # 尝试匹配机器码
            match = machine_code_pattern.match(line)
            if match:
                machine_code = match.group(1)
                machine_codes.append(machine_code)
        
        # 写入文件
        if write_instructions_to_file(machine_codes, output_file):
            # 同时在屏幕上显示前几条
            print("\n前10条32位指令的机器码:")
            print("-" * 40)
            for i, code in enumerate(machine_codes[:10], 1):
                print(f"{i:3d}: {code}")
            if len(machine_codes) > 10:
                print(f"... 还有 {len(machine_codes) - 10} 条")
    
    elif clean_mode:
        # 仅提取指令助记符和操作数
        instructions = extract_32bit_instructions_only_mnemonic(input_file)
        if instructions:
            if write_instructions_to_file(instructions, output_file):
                # 同时在屏幕上显示前几条
                print("\n前10条32位指令:")
                print("-" * 40)
                for i, instr in enumerate(instructions[:10], 1):
                    print(f"{i:3d}: {instr}")
                if len(instructions) > 10:
                    print(f"... 还有 {len(instructions) - 10} 条")
    
    else:
        # 提取完整的指令（包含机器码）
        instructions = extract_32bit_instructions(input_file)
        if instructions:
            if write_instructions_to_file(instructions, output_file):
                # 同时在屏幕上显示前几条
                print("\n前10条32位指令:")
                print("-" * 40)
                for i, instr in enumerate(instructions[:10], 1):
                    print(f"{i:3d}: {instr}")
                if len(instructions) > 10:
                    print(f"... 还有 {len(instructions) - 10} 条")

if __name__ == "__main__":
    main()