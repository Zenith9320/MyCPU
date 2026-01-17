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

current_path = os.path.dirname(os.path.abspath(__file__))
workspace = os.path.join(current_path, ".workspace")

def init_memory(source_file):
    mem = {}
    with open(source_file, 'r') as f:
        lines = f.readlines()
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if line.startswith('@'):
                addr = int(line[1:], 16)
                i += 1
                if i < len(lines):
                    data_line = lines[i].strip()
                    data = int(data_line, 16)
                    mem[addr] = data
            i += 1
    return mem

def convert_format(input_file, output_file):
    data = {}
    current_addr = None
    with open(input_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith('@'):
                current_addr = int(line[1:], 16)
            else:
                if current_addr is not None:
                    bytes_data = [int(x, 16) for x in line.split()]
                    for i, byte in enumerate(bytes_data):
                        data[current_addr + i] = byte
                    current_addr += len(bytes_data)

    # Now group into 32-bit words, assuming little-endian
    words = {}
    for addr in sorted(data.keys()):
        word_addr = addr // 4
        offset = addr % 4
        if word_addr not in words:
            words[word_addr] = [0] * 4
        words[word_addr][offset] = data[addr]

    # Convert to big-endian hex
    with open(output_file, 'w') as f:
        for word_addr in sorted(words.keys()):
            word_bytes = words[word_addr]
            word_hex = ''.join(f'{b:02x}' for b in reversed(word_bytes))  # big-endian
            addr_hex = f'{word_addr:08x}'
            f.write(f'@{addr_hex}\n')
            f.write(f'{word_hex}\n')

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

    src_exe = os.path.join(source_dir, f"{case_name}.exe")

    dst_exe = os.path.join(workspace_dir, f"workload.exe")

    if os.path.exists(src_exe):
        # Parse workload.exe
        mem = {}
        with open(src_exe, 'r') as f:
            addr = 0
            for line in f:
                line = line.strip()
                if line and not line.startswith('//'):
                    data_str = line.split()[0]  # take first part before //
                    data = int(data_str, 16)
                    mem[addr] = data
                    addr += 1  # word address increment

        # Load converted.hex data
        init_data = init_memory('converted.hex')
        mem.update(init_data)

        # Write merged data to dst_exe
        with open(dst_exe, 'w') as f:
            for addr in sorted(mem.keys()):
                data = mem[addr]
                f.write(f'@{addr:08x}\n')
                f.write(f'{data:08x}\n')

        print(f"  -> Merged instructions and data: {case_name}.exe + converted.hex ==> workload.exe")
    else:
        raise FileNotFoundError(f"Test case not found: {src_exe}")


class Driver(Module):
    def __init__(self):
        super().__init__(ports={})
    
    @module.combinational
    def build(self, fetcher: Module):
        log("Driver!")
        fetcher.async_called()

def build_cpu(depth_log):
    sys_name = "rv32i_cpu"
    sys = SysBuilder(sys_name)

    ram_path = os.path.join(workspace, f"workload.exe")

    with sys:
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
    
    return sys

if __name__ == "__main__":

    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        convert_format(input_file, 'converted.hex')

    load_test_case("0to100")

    sys_builder = build_cpu(depth_log=16)

    circ_path = os.path.join(workspace, f"circ.txt")
    with open(circ_path, "w") as f:
        print(sys_builder, file=f)

    print(f"🚀 Compiling system: {sys_builder.name}...")
    
    cfg = config(
        verilog=True,
        sim_threshold=50000,
        resource_base="",
        idle_threshold=50000,
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

    print("Running verilator...")
    raw = utils.run_verilator(verilog_path)
    log_path = os.path.join(workspace, f"verilalog_raw.log")
    with open(log_path, "w") as f:
        print(raw, file=f)

    print("Done.")