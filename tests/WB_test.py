import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from assassyn.frontend import *
from tests.common import run_test_module
from src.WB import WriteBack
from src.utils import WbCtrlSignals


# --- Driver ---
class Driver(Module):
    def __init__(self):
        super().__init__(ports={})

    @module.combinational
    def build(self, dut: Module):
        # 测试向量: (rd, data, is_halt)
        # 覆盖各种情况：
        # 1. 正常写回（非零寄存器）
        # 2. 零寄存器保护（不写入 x0）
        # 3. 多次写回（覆盖测试）
        # 4. 旁路数据输出验证
        # 5. is_halt 信号测试
        vectors = [
            (1, 0x12345678, 0),  # Cyc 0: 写入 x1 = 0x12345678
            (2, 0x9ABCDEF0, 0),  # Cyc 1: 写入 x2 = 0x9ABCDEF0
            (0, 0xDEADBEEF, 0),  # Cyc 2: 尝试写入 x0（应该被忽略）
            (1, 0x11111111, 0),  # Cyc 3: 覆盖 x1 = 0x11111111
            (5, 0x22222222, 0),  # Cyc 4: 写入 x5 = 0x22222222
            (10, 0x33333333, 0), # Cyc 5: 写入 x10 = 0x33333333
            (31, 0xFFFFFFFF, 0), # Cyc 6: 写入 x31 = 0xFFFFFFFF
            (15, 0x00000000, 0), # Cyc 7: 写入 x15 = 0x00000000
            (20, 0x88888888, 0), # Cyc 8: 写入 x20 = 0x88888888
            (0, 0x00000001, 1),  # Cyc 9: 尝试写入 x0 且 is_halt=1（应该被忽略且暂停）
        ]

        cnt = RegArray(UInt(32), 1, initializer=[0])
        (cnt & self)[0] <= cnt[0] + UInt(32)(1)
        idx = cnt[0]

        rd, data, is_halt = Bits(5)(0), Bits(32)(0), Bits(1)(0)

        for i, v in enumerate(vectors):
            is_match = idx == UInt(32)(i)
            rd = is_match.select(Bits(5)(v[0]), rd)
            data = is_match.select(Bits(32)(v[1]), data)
            is_halt = is_match.select(Bits(1)(v[2]), is_halt)

        valid_test = idx < UInt(32)(len(vectors))
        with Condition(valid_test):
            ctrl = WbCtrlSignals.bundle(
                rd=rd,
                is_halt=is_halt,
            )
            call = dut.async_called(ctrl=ctrl, data=data)

        test_end_cycle = UInt(32)(len(vectors) + 2)

        with Condition(idx >= test_end_cycle):
            log("Driver: All vectors applied. Finishing simulation.")
            finish()

        return rd, data, is_halt


# --- Check ---
def check(output):
    print(">>> Verifying WriteBack Logic...")

    # 解析日志
    captured = []
    for line in output.split("\n"):
        if "WB: Write x" in line:
            parts = line.split()
            rd = int(parts[6][1:])  # 提取 x 后面的数字
            data = int(parts[8], 16)  # 提取十六进制数据
            captured.append((rd, data))
        elif "Driver: All vectors applied" in line:
            break

    print(f"Captured Writes: {[(f'x{rd}', f'0x{data:08x}') for rd, data in captured]}")

    # 预期的写回操作（不包括 x0）
    expected = [
        (1, 0x12345678),  # Cyc 0: 写入 x1
        (2, 0x9ABCDEF0),   # Cyc 1: 写入 x2
        # Cyc 2: x0 被忽略
        (1, 0x11111111),  # Cyc 3: 覆盖 x1
        (5, 0x22222222),  # Cyc 4: 写入 x5
        (10, 0x33333333), # Cyc 5: 写入 x10
        (31, 0xFFFFFFFF), # Cyc 6: 写入 x31
        (15, 0x00000000), # Cyc 7: 写入 x15
        (20, 0x88888888), # Cyc 8: 写入 x20
        # Cyc 9: x0 被忽略，且 is_halt=1
    ]

    print(f"Expected Writes: {[(f'x{rd}', f'0x{data:08x}') for rd, data in expected]}")

    # 验证写回操作
    if len(captured) != len(expected):
        print(f"❌ Error: Expected {len(expected)} writes, got {len(captured)}.")
        assert False, "Write count mismatch"

    for i, (exp_rd, exp_data) in enumerate(expected):
        if i >= len(captured):
            print(f"❌ Error: Missing write {i}: x{exp_rd} <= 0x{exp_data:08x}")
            assert False, "Missing write"

        act_rd, act_data = captured[i]

        if act_rd != exp_rd or act_data != exp_data:
            print(f"❌ Mismatch at write {i}:")
            print(f"   Expected: x{exp_rd} <= 0x{exp_data:08x}")
            print(f"   Actual:   x{act_rd} <= 0x{act_data:08x}")
            assert False, "Write mismatch"

    # 验证 x0 没有被写入
    x0_writes = [rd for rd, data in captured if rd == 0]
    if len(x0_writes) > 0:
        print(f"❌ Error: x0 was written {len(x0_writes)} times (should be 0).")
        assert False, "x0 should not be written"

    # 验证 x1 被覆盖
    x1_writes = [(data, idx) for idx, (rd, data) in enumerate(captured) if rd == 1]
    if len(x1_writes) != 2:
        print(f"❌ Error: x1 should be written twice, got {len(x1_writes)}.")
        assert False, "x1 overwrite count mismatch"
    if x1_writes[0][0] != 0x12345678:
        print(f"❌ Error: x1 first write should be 0x12345678, got 0x{x1_writes[0][0]:08x}.")
        assert False, "x1 first write mismatch"
    if x1_writes[1][0] != 0x11111111:
        print(f"❌ Error: x1 second write should be 0x11111111, got 0x{x1_writes[1][0]:08x}.")
        assert False, "x1 second write mismatch"

    # 验证 is_halt 信号（检查仿真是否正常结束）
    if "WB: Halt signal received, finishing simulation." not in output:
        print(f"❌ Error: Simulation did not complete properly.")
        assert False, "Simulation did not complete"

    print("✅ WriteBack Logic Passed:")
    print("  - All writes matched expected values.")
    print("  - x0 register protection verified.")
    print("  - Register overwrite verified.")
    print("  - Simulation completed successfully.")


# --- Top ---
if __name__ == "__main__":
    sys = SysBuilder("test_writeback")
    with sys:
        # 创建寄存器堆
        reg_file = RegArray(Bits(32), 32)

        # 创建 WB 模块
        writeback = WriteBack()

        # 创建 Driver
        driver = Driver()

        # 构建 WB 模块
        wb_rd, wb_bypass = writeback.build(reg_file)

        # 构建 Driver
        driver.build(writeback)

        # 暴露寄存器堆用于调试（可选）
        sys.expose_on_top(reg_file, kind="Output")

    run_test_module(sys, check)
