import os

from assassyn.frontend import *
from assassyn.backend import elaborate, config
from assassyn import utils

from IF import Fetcher, FetcherImpl
from ID import Decoder
from EX import Executor
from MA import MemoryAcess
from WB import WriteBack

current_path = os.path.dirname(os.path.abspath(__file__))
workspace = os.path.join(current_path, ".workspace")

class Driver(Module):
    def __init__(self):
        super().__init__(ports={})
    
    @module.combinational
    def build(self, fetcher: Module):
        fetcher.async_called()

def build_cpu(depth_log):
    sys_name = "rv32i_cpu"
    sys = SysBuilder(sys_name)

    with sys:
        dcache = SRAM(width = 32, depth = 1 << depth_log, init_file = None)
        dcache.name = "dcache"
        icache = SRAM(width = 32, depth = 1 << depth_log, init_file = None)
        icache.name = "icache"

        reg_file = RegArray(Bits(32), 32)

        fetcher = Fetcher()
        fetcher_impl = FetcherImpl()
        decoder = Decoder()
        executor = Executor()
        memory_access = MemoryAcess()
        write_back = WriteBack()
        driver = Driver()

        write_back.build(
            reg_file = reg_file,
        )
        memory_access.build(
            write_back = write_back,
        )
        executor.build(
            memory_access = memory_access,
        )
        decoder.build(
            icache_out = icache.dout,
            executor = executor,
        )
        pc = fetcher.build()
        fetcher_impl.build(
            pc_reg = pc,
            decoder = decoder,
        )

        driver.build(
            fetcher=fetcher,
        )
    
    return sys

if __name__ == "__main__":
    sys_builder = build_cpu(depth_log=16)
    cfg = config(
        verilog=True,
        sim_threshold=10,
        resource_base="",
        idle_threshold=10,
    )
    simulator_path, verilog_path = elaborate(sys_builder, **cfg)

    print(f"Running simulation...")
    print(simulator_path)
    print(verilog_path)

    try:
        binary_path = utils.build_simulator(simulator_path)
        print(f"🔨 Building binary from: {binary_path}")
    except Exception as e:
        print(f"❌ Simulator build failed: {e}")
        raise e

    raw = utils.run_simulator(binary_path = binary_path)
    log_path = os.path.join(workspace, f"raw.log")
    with open(log_path, "w") as f:
        print(raw, file=f)

    print(f"Running simulation(verilog)...")
    raw = utils.run_verilator(verilog_path)
    log_path = os.path.join(workspace, f"verilalog_raw.log")
    with open(log_path, "w") as f:
        print(raw, file=f)

    print("Done.")