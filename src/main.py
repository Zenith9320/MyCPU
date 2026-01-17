import os
import shutil
import sys

from assassyn.frontend import *
from assassyn.backend import elaborate, config
from assassyn import utils

from .IF import Fetcher, FetcherImpl
from .ID import Decoder, DecoderImpl
from .EX import Executor
from .MA import MemoryAcess
from .WB import WriteBack
from .bypass import Bypass
from .memory_user import MemoryUser
from .debug import debug_log, set_debug_mode

current_path = os.path.dirname(os.path.abspath(__file__))
workspace = os.path.join(current_path, ".workspace")

def parse_verilog_hex(filepath):
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
    memory = {}
    
    for addr, bytes_list in data.items():
        for i, byte_val in enumerate(bytes_list):
            memory[addr + i] = byte_val
    
    return memory


def convert_to_hex_format(memory):
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
    with open(output_path, 'w') as f:
        for addr, word in words:
            # 格式：xxxxxxxx // address: 0x...
            f.write(f"{word:08x}\n")

def load_test_case(case_name, source_subdir="workloads"):

    current_file_path = os.path.abspath(__file__)
    src_dir = os.path.dirname(current_file_path)
    project_root = os.path.dirname(src_dir)

    source_dir = os.path.join(project_root, source_subdir)

    workspace_dir = os.path.join(src_dir, ".workspace")

    print(f"[*] Source Dir: {source_dir}")
    print(f"[*] Workspace : {workspace_dir}")

    if os.path.exists(workspace_dir):
        shutil.rmtree(workspace_dir)
    os.makedirs(workspace_dir)

    src_data = os.path.join(source_dir, f"testcases/{case_name}.data")
    src_exe = os.path.join(source_dir, f"testcases/{case_name}.exe")

    data = parse_verilog_hex(src_data)
    flat_memory = merge_to_flat_memory(data)
    words = convert_to_hex_format(flat_memory)
    write_hex_format(src_exe, words)

    dst_exe = os.path.join(workspace_dir, f"workload.exe")

    if os.path.exists(src_exe):
        shutil.copy(src_exe, dst_exe)
        print(f"  -> Copied Instruction: {case_name}.exe ==> workload.exe")
    else:
        raise FileNotFoundError(f"Test case not found: {src_exe}")


class Driver(Module):
    def __init__(self):
        super().__init__(ports={})
    
    @module.combinational
    def build(self, fetcher: Module):
        debug_log("Driver!")
        fetcher.async_called()

def build_cpu(depth_log):
    sys_name = "rv32i_cpu"
    Sys = SysBuilder(sys_name)

    ram_path = os.path.join(workspace, f"workload.exe")

    with Sys:
        cache = SRAM(width=32, depth=1 << depth_log, init_file=ram_path)
        cache.name = "cache"

        reg_file = RegArray(Bits(32), 32)

        branch_target = RegArray(Bits(32), 1)

        driver = Driver()
        fetcher = Fetcher()
        fetcher_impl = FetcherImpl()
        decoder = Decoder()
        decoder_impl = DecoderImpl()
        executor = Executor()
        memory_access = MemoryAcess()
        write_back = WriteBack()
        bypass = Bypass()
        memory_user = MemoryUser()

        wb_rd, wb_bypass_data = write_back.build(reg_file = reg_file)

        mem_rd, mem_bypass_data, mem_is_store = memory_access.build(
            write_back = write_back, sram_dout = cache.dout
        )

        ex_rd, ex_bypass_data, ex_is_store, ex_is_load, ex_width, ex_rs2 = executor.build(
            memory_access = memory_access,
            branch_target = branch_target
        )

        pre_ctrl, rs1, rs2 = decoder.build(
            icache_dout=cache.dout,
            reg_file=reg_file,
        )

        rs1_sel, rs2_sel, is_stall = bypass.build(
            rs1_addr = rs1,
            rs2_addr = rs2,
            ex_dest_addr = ex_rd,
            ex_is_load = ex_is_load,
            ex_is_store = ex_is_store,
            mem_dest_addr = mem_rd,
            mem_is_store = mem_is_store,
            wb_dest_addr = wb_rd,
        )

        decoder_impl.build(
            ctrl = pre_ctrl,
            executor = executor,
            rs1_ex_type = rs1_sel,
            rs2_ex_type = rs2_sel,
            if_stall = is_stall,
            ex_bypass = ex_bypass_data,
            mem_bypass = mem_bypass_data,
            wb_bypass = wb_bypass_data,
            branch_target_reg = branch_target,
        )

        pc_reg, last_pc_reg, rubbish = fetcher.build()
        if_addr = fetcher_impl.build(
            pc_reg = pc_reg,
            last_pc_reg = last_pc_reg,
            decoder = decoder,
            is_stall = is_stall,
            branch_target_reg = branch_target,
            rubbish=rubbish
        )

        memory_user.build(
            if_addr = if_addr, # fetcher 阶段的 pc
            mem_addr = ex_bypass_data, # alu_res, 这里也是旁路传来的内存地址
            ex_is_load = ex_is_load,
            ex_is_store = ex_is_store,
            wdata = ex_rs2,
            width = ex_width,
            sram = cache,
        )

        driver.build(
            fetcher = fetcher
        )
    
    return Sys

if __name__ == "__main__":

    if (len(sys.argv) >= 3):
        test_case = sys.argv[1]
        set_debug_mode(sys.argv[2].lower() in ['true', '1', 'yes'])
    else:
        raise Exception("Usage: python main.py <test_case_name> <debug_mode(True/False)>")

    load_test_case(test_case)

    sys_builder = build_cpu(depth_log=16)

    circ_path = os.path.join(workspace, f"circ.txt")
    with open(circ_path, "w") as f:
        print(sys_builder, file=f)

    print(f"Compiling system: {sys_builder.name}...")
    
    cfg = config(
        verilog=True,
        sim_threshold=5000000,
        resource_base="",
        idle_threshold=5000000,
    )
    simulator_path, verilog_path = elaborate(sys_builder, **cfg)

    print(simulator_path)
    print(verilog_path)

    try:
        binary_path = utils.build_simulator(simulator_path)
        print(f"Building binary from: {binary_path}")
    except Exception as e:
        print(f"Simulator build failed: {e}")
        raise e

    print("Running simulator...")

    raw = utils.run_simulator(binary_path = binary_path)
    log_path = os.path.join(workspace, f"raw.log")
    with open(log_path, "w") as f:
        print(raw, file=f)

    # print("Running verilator...")
    # raw = utils.run_verilator(verilog_path)
    # log_path = os.path.join(workspace, f"verilalog_raw.log")
    # with open(log_path, "w") as f:
    #     print(raw, file=f)

    print("Done.")