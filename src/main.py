import os
import shutil

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
    # dst_mem = os.path.join(workspace_dir, f"workload.data")

    print(f"!!! SRC: {src_exe}, DST: {dst_exe}")

    if os.path.exists(src_exe):
        shutil.copy(src_exe, dst_exe)
        print(f"  -> Copied Instruction: {case_name}.exe ==> workload.exe")
    else:
        raise FileNotFoundError(f"Test case not found: {src_exe}")

    # with open(dst_mem, "w") as f:
    #    pass

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
    print("!!! RAM Path: ", ram_path)

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

        ex_rd, ex_bypass_data, ex_is_load, ex_is_store, ex_width, ex_rs2 = executor.build(
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

    load_test_case("0to100")

    sys_builder = build_cpu(depth_log=16)

    circ_path = os.path.join(workspace, f"circ.txt")
    with open(circ_path, "w") as f:
        print(sys_builder, file=f)

    print(f"🚀 Compiling system: {sys_builder.name}...")
    
    cfg = config(
        verilog=True,
        sim_threshold=100000,
        resource_base="",
        idle_threshold=100000,
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