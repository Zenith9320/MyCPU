import os
import shutil

from assassyn.frontend import *
from assassyn.backend import elaborate, config
from assassyn import utils

from IF import Fetcher
from ID import Decoder
from EX import Executor
from MA import MemoryAcess
from WB import WriteBack
from bypass import Bypass

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
    src_data = os.path.join(source_dir, f"{case_name}.data")

    dst_ins = os.path.join(workspace_dir, f"workload.exe")
    dst_mem = os.path.join(workspace_dir, f"workload.data")

    if os.path.exists(src_exe):
        shutil.copy(src_exe, dst_ins)
        print(f"  -> Copied Instruction: {case_name}.exe ==> workload.exe")
    else:
        raise FileNotFoundError(f"Test case not found: {src_exe}")

    if os.path.exists(src_data):
        shutil.copy(src_data, dst_mem)
        print(f"  -> Copied Memory Data: {case_name}.data ==> workload.data")
    else:
        with open(dst_mem, "w") as f:
            pass
        print(f"  -> No .data found, created empty: workload.data")

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

    ram_path = os.path.join(workspace, f"workload.data")

    with sys:
        cache = SRAM(width=32, depth=1 << depth_log, init_file=ram_path)
        cache.name = "cache"

        reg_file = RegArray(Bits(32), 32)

        driver = Driver()
        fetcher = Fetcher()
        decoder = Decoder()
        executor = Executor()
        memory_access = MemoryAcess()
        write_back = WriteBack()
        bypass = Bypass()

        write_back.build(reg_file)
        memory_access.build(write_back)
        executor.build(memory_access)
        decoder.build(executor)
        fetcher.build(decoder)
        driver.build(fetcher)
    
    return sys

if __name__ == "__main__":

    load_test_case("0to100")

    sys_builder = build_cpu(depth_log=16)
    cfg = config(
        verilog=True,
        sim_threshold=10,
        resource_base="",
        idle_threshold=10,
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