#!/usr/bin/env python3
"""
从 workloads/testcases 中提取所有测试数据的正确答案

对于每组测试数据（由 .c, .data, .dump 组成），
从 .c 文件的倒数第二行提取正确答案（return judgeResult % Mod; 注释中的内容）
"""

import os
import re
from pathlib import Path
from collections import defaultdict


def extract_answer_from_c(c_file_path):
    """
    从 .c 文件中提取正确答案
    
    正确答案在倒数第二行，格式为：
    return judgeResult % Mod; // <answer> 或
    return judgeResult; // <answer>
    """
    try:
        with open(c_file_path, 'r') as f:
            lines = f.readlines()
        
        if len(lines) < 2:
            return None
        
        # 倒数第二行（去掉最后的空行）
        second_last_line = lines[-2].strip()
        
        # 匹配格式1：return judgeResult % Mod; // <answer>
        match = re.search(r'return\s+judgeResult\s*%\s*Mod\s*;\s*//\s*(\d+)', second_last_line)
        
        if match:
            return match.group(1)
        
        # 匹配格式2：return judgeResult; // <answer>
        match = re.search(r'return\s+judgeResult\s*;\s*//\s*(\d+)', second_last_line)
        
        if match:
            return match.group(1)
        
        return None
    except Exception as e:
        print(f"读取文件 {c_file_path} 时出错: {e}")
        return None


def find_testcases(testcases_dir):
    """
    找到所有测试数据组
    
    返回: dict {testcase_name: {c_file, data_file, dump_file}}
    """
    testcases = {}
    
    # 遍历目录中的所有文件
    for file_path in Path(testcases_dir).iterdir():
        if not file_path.is_file():
            continue
        
        # 获取文件名和扩展名
        stem = file_path.stem
        suffix = file_path.suffix
        
        # 跳过 io.inc 文件
        if stem == 'io':
            continue
        
        # 初始化测试用例条目
        if stem not in testcases:
            testcases[stem] = {}
        
        # 记录文件
        if suffix == '.c':
            testcases[stem]['c'] = str(file_path)
        elif suffix == '.data':
            testcases[stem]['data'] = str(file_path)
        elif suffix == '.dump':
            testcases[stem]['dump'] = str(file_path)
    
    # 只保留包含完整三件套的测试用例
    complete_testcases = {}
    for name, files in testcases.items():
        if 'c' in files and 'data' in files and 'dump' in files:
            complete_testcases[name] = files
    
    return complete_testcases


def main():
    # 设置 testcases 目录路径
    script_dir = Path(__file__).parent
    testcases_dir = script_dir / 'testcases'
    
    if not testcases_dir.exists():
        print(f"错误: 目录 {testcases_dir} 不存在")
        return
    
    # 找到所有测试数据组
    print(f"扫描目录: {testcases_dir}")
    testcases = find_testcases(testcases_dir)
    print(f"找到 {len(testcases)} 个完整的测试数据组\n")
    
    # 提取正确答案
    answers = []
    for name, files in sorted(testcases.items()):
        answer = extract_answer_from_c(files['c'])
        if answer:
            answers.append((name, answer))
            print(f"{name}: {answer}")
        else:
            print(f"{name}: 无法提取答案")
    
    # 写入答案文件
    output_file = script_dir / 'testcases_answers.txt'
    with open(output_file, 'w') as f:
        f.write("# 测试数据正确答案\n")
        f.write("# 格式: <测试名称> <正确答案>\n")
        f.write("#\n")
        for name, answer in answers:
            f.write(f"{name} {answer}\n")
    
    print(f"\n答案已写入: {output_file}")
    print(f"共提取 {len(answers)} 个测试数据的答案")


if __name__ == "__main__":
    main()
