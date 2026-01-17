import os
import subprocess

def run_test(test_name, answer):
    """运行单个测试用例"""
    # 切换到工作目录
    base_dir = os.path.expanduser("~/assassyn/mycpu")
    os.chdir(base_dir)
    
    # 运行测试命令
    cmd = ["python3", "-m", "src.main", test_name, "False"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"[ERROR] 测试 {test_name} 执行失败: {result.stderr}")
        return False
    
    # 读取结果
    log_path = "src/.workspace/raw.log"
    try:
        with open(log_path, "r") as f:
            lines = f.readlines()
            if len(lines) < 11:
                print(f"[ERROR] 日志文件格式异常")
                return False
            
            output = lines[10].strip().split()[-1]
            output_int = int(output, 0)  # 自动检测进制
            answer_int = int(answer, 0)

            output_int %= 256
            
            if output_int == answer_int:
                print(f"[PASS] {test_name}: {output} % 256 == {answer}")
                return True
            else:
                print(f"[FAIL] {test_name}: {output} != {answer}")
                return False
    except Exception as e:
        print(f"[ERROR] 处理 {test_name} 时出错: {e}")
        return False

if __name__ == "__main__":
    test_file = "workloads_answers.txt"
    
    try:
        with open(test_file, "r") as f:
            tests = []
            for i, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                    
                parts = line.split()
                if len(parts) >= 2:
                    tests.append((parts[0], parts[1]))
                else:
                    print(f"[WARN] 第 {i} 行格式错误: {line}")
            
            # 只运行前18个测试
            for i, (test_name, answer) in enumerate(tests[:18], 1):
                print(f"\n{'='*40}")
                print(f"测试 {i}: {test_name}")
                run_test(test_name, answer)
                
    except FileNotFoundError:
        print(f"[ERROR] 找不到测试文件: {test_file}")
    except Exception as e:
        print(f"[ERROR] 程序异常: {e}")