import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from assassyn.frontend import *
from tests.common import run_test_module
from src.bypass import Bypass
from src.utils import Rs1Type, Rs2Type


# --- BypassWrapper ---
class BypassWrapper(Module):
    def __init__(self):
        super().__init__(
            ports={
                "rs1_addr": Port(Bits(5)),
                "rs2_addr": Port(Bits(5)),
                "ex_dest_addr": Port(Bits(5)),
                "ex_is_load": Port(Bits(1)),
                "ex_is_store": Port(Bits(1)),
                "mem_dest_addr": Port(Bits(5)),
                "mem_is_store": Port(Bits(1)),
                "wb_dest_addr": Port(Bits(5)),
            }
        )

    @module.combinational
    def build(self):
        # 从端口弹出数据
        rs1_addr, rs2_addr, ex_dest_addr, ex_is_load, ex_is_store, mem_dest_addr, mem_is_store, wb_dest_addr = self.pop_all_ports(False)

        # log("BypassWrapper: rs1_addr={}, rs2_addr={}, ex_dest_addr={}, ex_is_load={}, ex_is_store={}, mem_dest_addr={}, mem_is_store={}, wb_dest_addr={}",
        #    rs1_addr, rs2_addr, ex_dest_addr, ex_is_load, ex_is_store, mem_dest_addr, mem_is_store, wb_dest_addr)

        return rs1_addr, rs2_addr, ex_dest_addr, ex_is_load, ex_is_store, mem_dest_addr, mem_is_store, wb_dest_addr


# --- Driver ---
class Driver(Module):
    def __init__(self):
        super().__init__(ports={})

    @module.combinational
    def build(self, dut: Module):
        # 测试向量: (rs1, rs2, ex_dest, ex_is_load, ex_is_store, mem_dest, mem_is_store, wb_dest)
        # 覆盖各种情况：
        # 1. 无旁路：rs1/rs2 不匹配任何阶段的目标寄存器
        # 2. WB旁路：rs1/rs2匹配 WB阶段的目标寄存器
        # 3. MEM旁路：rs1/rs2匹配 MEM阶段的目标寄存器
        # 4. EX旁路：rs1/rs2匹配 EX阶段的目标寄存器
        # 5. 零寄存器：rs1/rs2 为 x0时不旁路
        # 6. 暂停信号：EX/MEM阶段有 Load/Store 时暂停
        # 7. 优先级：EX > MEM > WB > NONE
        vectors = [
            # Cyc 0: 无旁路
            (1, 2, 3, 0, 0, 4, 0, 5),  # rs1=1, rs2=2, ex=3, mem=4, wb=5 -> 无匹配

            # Cyc 1: WB旁路（rs1 匹配 wb）
            (5, 2, 3, 0, 0, 4, 0, 5),  # rs1=5 匹配 wb=5 -> WB

            # Cyc 2: MEM旁路（rs1 匹配 mem）
            (1, 2, 3, 0, 0, 1, 0, 5),  # rs1=1 匹配 mem=1 -> MEM

            # Cyc 3: EX旁路（rs1 匹配 ex）
            (1, 2, 1, 0, 0, 4, 0, 5),  # rs1=1 匹配 ex=1 -> EX

            # Cyc 4: 零寄存器（rs1=x0，不旁路）
            (0, 2, 3, 0, 0, 4, 0, 5),  # rs1=0 -> NONE（即使匹配 wb）

            # Cyc 5: rs2 WB旁路
            (1, 5, 3, 0, 0, 4, 0, 5),  # rs2=5 匹配 wb=5 -> WB

            # Cyc 6: rs2 MEM旁路
            (1, 2, 3, 0, 0, 2, 0, 5),  # rs2=2 匹配 mem=2 -> MEM

            # Cyc 7: rs2 EX旁路
            (1, 3, 3, 0, 0, 4, 0, 5),  # rs2=3 匹配 ex=3 -> EX

            # Cyc 8: 零寄存器（rs2=x0，不旁路）
            (1, 0, 3, 0, 0, 4, 0, 5),  # rs2=0 -> NONE（即使匹配 wb）

            # Cyc 9: 暂停（EX Load）
            (1, 2, 3, 1, 0, 4, 0, 5),  # ex_is_load=1 -> stall

            # Cyc 10: 暂停（EX Store）
            (1, 2, 3, 0, 1, 4, 0, 5),  # ex_is_store=1 -> stall

            # Cyc 11: 暂停（MEM Store）
            (1, 2, 3, 0, 0, 4, 1, 5),  # mem_is_store=1 -> stall

            # Cyc 12: 优先级 EX > MEM（rs1 同时匹配 ex 和 mem）
            (1, 2, 1, 0, 0, 1, 0, 5),  # rs1=1 匹配 ex=1 和 mem=1 -> EX（优先级更高）

            # Cyc 13: 优先级 MEM > WB（rs1 同时匹配 mem 和 wb）
            (1, 2, 3, 0, 0, 1, 0, 1),  # rs1=1 匹配 mem=1 和 wb=1 -> MEM（优先级更高）

            # Cyc 14: 无旁路（rs1/rs2 不匹配）
            (10, 20, 30, 0, 0, 25, 0, 31),  # rs1=10, rs2=20, ex=30, mem=25, wb=31 -> 无匹配
        ]

        cnt = RegArray(UInt(32), 1, initializer=[0])
        (cnt & self)[0] <= cnt[0] + UInt(32)(1)
        idx = cnt[0]

        rs1, rs2, ex_dest, ex_is_load, ex_is_store, mem_dest, mem_is_store, wb_dest = \
            Bits(5)(0), Bits(5)(0), Bits(5)(0), Bits(1)(0), Bits(1)(0), Bits(5)(0), Bits(1)(0), Bits(5)(0)

        for i, v in enumerate(vectors):
            is_match = idx == UInt(32)(i)
            rs1 = is_match.select(Bits(5)(v[0]), rs1)
            rs2 = is_match.select(Bits(5)(v[1]), rs2)
            ex_dest = is_match.select(Bits(5)(v[2]), ex_dest)
            ex_is_load = is_match.select(Bits(1)(v[3]), ex_is_load)
            ex_is_store = is_match.select(Bits(1)(v[4]), ex_is_store)
            mem_dest = is_match.select(Bits(5)(v[5]), mem_dest)
            mem_is_store = is_match.select(Bits(1)(v[6]), mem_is_store)
            wb_dest = is_match.select(Bits(5)(v[7]), wb_dest)

        valid_test = idx < UInt(32)(len(vectors))
        with Condition(valid_test):
            # log("Driver: Applying vector #{}: rs1={}, rs2={}, ex_dest={}, ex_is_load={}, ex_is_store={}, mem_dest={}, mem_is_store={}, wb_dest={}", idx, rs1, rs2, ex_dest, ex_is_load, ex_is_store, mem_dest, mem_is_store, wb_dest)
            call = dut.async_called(
                rs1_addr=rs1,
                rs2_addr=rs2,
                ex_dest_addr=ex_dest,
                ex_is_load=ex_is_load,
                ex_is_store=ex_is_store,
                mem_dest_addr=mem_dest,
                mem_is_store=mem_is_store,
                wb_dest_addr=wb_dest,
            )

        test_end_cycle = UInt(32)(len(vectors) + 2)

        with Condition(idx >= test_end_cycle):
            log("Driver: All vectors applied. Finishing simulation.")
            finish()

        return rs1, rs2, ex_dest, ex_is_load, ex_is_store, mem_dest, mem_is_store, wb_dest


# --- Check ---
def check(output):
    print(">>> Verifying Bypass Logic...")

    # 解析日志
    captured = []
    for line in output.split("\n"):
        if "Bypass" in line and "Result:" in line:
            # 提取 rs1_type, rs2_type, is_stall
            parts = line.split()
            rs1_type_str = None
            rs2_type_str = None
            is_stall_str = None
            for part in parts:
                if "rs1_type=" in part:
                    rs1_type_str = part.split("=")[1]
                elif "rs2_type=" in part:
                    rs2_type_str = part.split("=")[1]
                elif "is_stall=" in part:
                    is_stall_str = part.split("=")[1]
            if rs1_type_str and rs2_type_str and is_stall_str:
                captured.append((rs1_type_str, rs2_type_str, is_stall_str))

    print(f"Captured: {captured}")

    # 预期的旁路类型和暂停信号
    # Rs1Type/Rs2Type: NONE=0b0001, EX=2, MEM=4, WB=8
    expected = [
        ("1", "1", "false"),  # Cyc 0: 无旁路
        ("8", "1", "false"),  # Cyc 1: rs1 WB
        ("4", "1", "false"),  # Cyc 2: rs1 MEM
        ("2", "1", "false"),  # Cyc 3: rs1 EX
        ("1", "1", "false"),  # Cyc 4: rs1 零寄存器
        ("1", "8", "false"),  # Cyc 5: rs2 WB
        ("1", "4", "false"),  # Cyc 6: rs2 MEM
        ("1", "2", "false"),  # Cyc 7: rs2 EX
        ("1", "1", "false"),  # Cyc 8: rs2 零寄存器
        ("1", "1", "true"),  # Cyc 9: EX Load -> stall
        ("1", "1", "true"),  # Cyc 10: EX Store -> stall
        ("1", "1", "true"),  # Cyc 11: MEM Store -> stall
        ("2", "1", "false"),  # Cyc 12: 优先级 EX > MEM
        ("4", "1", "false"),  # Cyc 13: 优先级 MEM > WB
        ("1", "1", "false"),  # Cyc 14: 无旁路
    ]

    print(f"Expected: {expected}")

    # 验证旁路类型和暂停信号
    if len(captured) != len(expected):
        print(f"❌ Error: Expected {len(expected)} results, got {len(captured)}.")
        assert False, "Result count mismatch"

    for i, (exp_rs1, exp_rs2, exp_stall) in enumerate(expected):
        if i >= len(captured):
            print(f"❌ Error: Missing result {i}.")
            assert False, "Missing result"

        act_rs1, act_rs2, act_stall = captured[i]

        if act_rs1 != exp_rs1 or act_rs2 != exp_rs2 or act_stall != exp_stall:
            print(f"❌ Mismatch at result {i}:")
            print(f"   Expected: rs1_type={exp_rs1}, rs2_type={exp_rs2}, is_stall={exp_stall}")
            print(f"   Actual:   rs1_type={act_rs1}, rs2_type={act_rs2}, is_stall={act_stall}")
            assert False, "Result mismatch"

    # 验证零寄存器不旁路
    zero_bypass = [(i, rs1, rs2) for i, (rs1, rs2, stall) in enumerate(captured)
                  if (rs1 != "1" and i in [4, 8]) or (rs2 != "1" and i in [4, 8])]
    if len(zero_bypass) > 0:
        print(f"❌ Error: Zero register should not bypass, but got: {zero_bypass}")
        assert False, "Zero register bypass error"

    # 验证优先级
    # Cyc 12: rs1=1 匹配 ex=1 和 mem=1，应该选择 EX
    if captured[12][0] != "2":
        print(f"❌ Error: Priority test failed. Expected EX (2), got {captured[12][0]}")
        assert False, "Priority test failed"

    # Cyc 13: rs1=1 匹配 mem=1 和 wb=1，应该选择 MEM
    if captured[13][0] != "4":
        print(f"❌ Error: Priority test failed. Expected MEM (4), got {captured[13][0]}")
        assert False, "Priority test failed"

    # 验证暂停信号
    stall_cases = [9, 10, 11]  # Cyc 9, 10, 11 应该暂停
    for i in stall_cases:
        if captured[i][2] != "true":
            print(f"❌ Error: Stall test failed at cycle {i}. Expected true, got {captured[i][2]}")
            assert False, "Stall test failed"

    # 验证非暂停情况
    non_stall_cases = [0, 1, 2, 3, 4, 5, 6, 7, 8, 12, 13, 14]  # 其他周期不应该暂停
    for i in non_stall_cases:
        if captured[i][2] != "false":
            print(f"❌ Error: Non-stall test failed at cycle {i}. Expected false, got {captured[i][2]}")
            assert False, "Non-stall test failed"

    print("✅ Bypass Logic Passed:")
    print("  - All bypass types matched expected values.")
    print("  - Zero register protection verified.")
    print("  - Priority (EX > MEM > WB) verified.")
    print("  - Stall signal verified.")
    print("  - Non-stall cases verified.")


# --- Top ---
if __name__ == "__main__":
    sys = SysBuilder("test_bypass")
    with sys:
        # 创建 Bypass 模块（必须在 sys 上下文中实例化）
        bypass = Bypass()

        # 创建 BypassWrapper 模块
        wrapper = BypassWrapper()

        # 创建 Driver
        driver = Driver()

        driver.build(wrapper)

        rs1_addr, rs2_addr, ex_dest_addr, ex_is_load, ex_is_store, mem_dest_addr, mem_is_store, wb_dest_addr = wrapper.build()

        rs1_type, rs2_type, is_stall = bypass.build(
            rs1_addr=rs1_addr,
            rs2_addr=rs2_addr,
            ex_dest_addr=ex_dest_addr,
            ex_is_load=ex_is_load,
            ex_is_store=ex_is_store,
            mem_dest_addr=mem_dest_addr,
            mem_is_store=mem_is_store,
            wb_dest_addr=wb_dest_addr,
        )

    run_test_module(sys, check)
