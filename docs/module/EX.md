# EX (Executor) 模块文档

## 概述

[`Executor`](../src/EX.py:4) 模块是五级流水线 RISC-V CPU 中的**执行阶段**（Execute Stage）。它负责执行 ALU 运算、分支判断、跳转地址计算，并将结果传递给 MEM 阶段。

该模块是 [`Module`](../docs/assassyn_zh.md:389) 类型的时序逻辑模块。

---

## 模块定义

```python
class Executor(Module):
    def __init__(self):
        super().__init__(
            ports={
                "ctrl": Port(ExCtrlSignals),
                "pc": Port(Bits(32)),
                "rs1": Port(Bits(32)),
                "rs2": Port(Bits(32)),
                "imm": Port(Bits(32))
            }
        )
```

**类型**：[`Module`](../docs/assassyn_zh.md:389)（时序逻辑模块）

---

## 端口定义

| 端口名 | 类型 | 说明 |
|--------|------|------|
| [`ctrl`](../src/EX.py:8) | [`Port(ExCtrlSignals)`](../src/utils.py:92) | 执行阶段控制信号 |
| [`pc`](../src/EX.py:9) | `Port(Bits(32))` | 当前指令 PC |
| [`rs1`](../src/EX.py:10) | `Port(Bits(32))` | 源寄存器 1 数据 |
| [`rs2`](../src/EX.py:11) | `Port(Bits(32))` | 源寄存器 2 数据 |
| [`imm`](../src/EX.py:12) | `Port(Bits(32))` | 立即数 |

### ExCtrlSignals 结构

[`ExCtrlSignals`](../src/utils.py:92) 定义在 [`utils.py`](../src/utils.py:92) 中：

```python
ExCtrlSignals = Record(
    alu_op = Bits(12),      # ALU 操作码
    branch_type = Bits(9),   # 分支类型
    op1_type = Bits(3),     # 操作数 1 类型
    op2_type = Bits(3),     # 操作数 2 类型
    predicted_pc = Bits(32), # 预测的下一 PC
    mem_op = Bits(3),       # 内存操作类型
    mem_width = Bits(3),     # 访问宽度
    mem_sign = Bits(2),     # 符号扩展标志
    rd = Bits(5),          # 目标寄存器地址
    is_halt = Bits(1),     # 是否暂停仿真
    rs1_data = Bits(32),   # rs1 数据（用于旁路）
    rs2_data = Bits(32),   # rs2 数据（用于旁路）
)
```

---

## build 方法参数

| 参数名 | 类型 | 说明 |
|--------|------|------|
| [`memory_access`](../src/EX.py:19) | `Module` | MEM 阶段模块 |
| [`branch_target`](../src/EX.py:20) | `RegArray` | 分支目标寄存器 |

---

## 输出参数

| 参数名 | 类型 | 说明 |
|--------|------|------|
| [`rd`](../src/EX.py:116) | `Bits(5)` | 目标寄存器地址 |
| [`alu_res`](../src/EX.py:46) | `Bits(32)` | ALU 运算结果 |
| [`is_store`](../src/EX.py:139) | `Bits(1)` | 是否为 Store 指令 |
| [`is_load`](../src/EX.py:140) | `Bits(1)` | 是否为 Load 指令 |
| [`mem_width`](../src/EX.py:141) | `Bits(3)` | 内存访问宽度 |
| [`rs2`](../src/EX.py:143) | `Bits(32)` | rs2 数据（用于 Store） |

---

## 核心逻辑

### 1. 弹出端口数据（第 22 行）

```python
ctrl, pc, rs1, rs2, imm = self.pop_all_ports(True)
```

使用 [`pop_all_ports(True)`](../docs/assassyn_zh.md:668) 以阻塞模式读取端口数据。

### 2. ALU 操作数选择（第 25-30 行）

```python
alu_op1 = ctrl.op1_type.select1hot(rs1, pc, Bits(32)(0))
alu_op2 = ctrl.op2_type.select1hot(rs2, imm, Bits(32)(4))
```

根据操作数类型选择 ALU 输入。

### 3. ALU 运算（第 32-58 行）

执行各种 ALU 运算：

```python
op1_signed = alu_op1.bitcast(Int(32))
op2_signed = alu_op2.bitcast(Int(32))

add_res = op1_signed + op2_signed
sub_res = op1_signed - op2_signed
and_res = alu_op1 & alu_op2
or_res = alu_op1 | alu_op2
xor_res = alu_op1 ^ alu_op2
sll_res = alu_op1 << alu_op2[0:4]
srl_res = alu_op1 >> alu_op2[0:4]
sra_res = (op1_signed >> alu_op2[0:4]).bitcast(Bits(32))
slt_res = (op1_signed < op2_signed).bitcast(Bits(32))
sltu_res = (alu_op1 < alu_op2).bitcast(Bits(32))

alu_res = ctrl.alu_op.select1hot(
    add_res, sub_res, sll_res, slt_res, sltu_res,
    xor_res, srl_res, sra_res, or_res, and_res, alu_op2
)
```

### 4. JAL/JALR 跳转地址计算（第 60-71 行）

```python
is_jalr = ctrl.branch_type == BranchType.JALR
is_jal = ctrl.branch_type == BranchType.JAL
target_base = is_jalr.select(rs1, pc)

imm_signed = imm.bitcast(Int(32))
target_base_signed = target_base.bitcast(Int(32))
raw_calc_target = (target_base_signed + imm_signed).bitcast(Bits(32))
calc_target = is_jalr.select(
    concat(raw_calc_target[0:31], Bits(1)(0)),
    raw_calc_target
)
```

计算 JAL 和 JALR 指令的跳转目标地址。

### 5. 分支判断（第 73-96 行）

```python
is_taken = Bits(1)(0)
is_branch = ctrl.branch_type != BranchType.NONE

is_eq = alu_res == Bits(32)(0)
is_lt = alu_res[0:0] == Bits(1)(1)

is_taken_eq = (ctrl.BranchType.BEQ == ctrl.branch_type) & is_eq
is_taken_ne = (ctrl.BranchType.BNE == ctrl.branch_type) & (~is_eq)
is_taken_lt = (ctrl.BranchType.BLT == ctrl.branch_type) & is_lt
is_taken_ge = (ctrl.BranchType.BGE == ctrl.branch_type) & (~is_lt)
is_taken_ltu = (ctrl.BranchType.BLTU == ctrl.branch_type) & is_lt
is_taken_geu = (ctrl.BranchType.BGEU == ctrl.branch_type) & (~is_lt)

is_taken = is_branch & (
    is_taken_eq | is_taken_ne | is_taken_lt | is_taken_ge |
    is_taken_ltu | is_taken_geu | is_jal | is_jalr
)
```

判断分支是否应该跳转。

### 6. 分支预测和冲刷（第 98-114 行）

```python
is_flush = branch_target[0] != Bits(32)(0)
next_pc = is_flush.select(
    Bits(32)(0),
    is_branch.select(
        is_taken.select(calc_target, pc.bitcast(UInt(32)) + Bits(32)(4)),
        ctrl.predicted_next_pc
    )
)

branch_miss = next_pc != ctrl.predicted_next_pc
branch_target[0] = branch_miss.select(next_pc, Bits(32)(0))
```

处理分支预测错误，更新分支目标寄存器。

### 7. 冲刷处理（第 116-127 行）

```python
rd = is_flush.select(Bits(5)(0), ctrl.rd)
is_halt = is_flush.select(Bits(1)(0), ctrl.is_halt)
mem_opcode = is_flush.select(MemOp.NONE, ctrl.mem_op)
```

如果需要冲刷，将目标寄存器设置为 x0。

### 8. 发送到 MEM 阶段（第 129-137 行）

```python
mem_ctrl = MemCtrlSignals.bundle(
    mem_opcode = mem_opcode,
    mem_width = ctrl.mem_width,
    mem_sign = ctrl.mem_sign,
    rd = rd,
    is_halt = is_halt
)

memory_access.async_called(ctrl = mem_ctrl, alu_result = alu_res)
```

准备 MEM 阶段控制信号并调用 MEM 模块。

### 9. 返回输出（第 139-143 行）

```python
is_store = mem_opcode == MemOp.STORE
is_load = mem_opcode == MemOp.LOAD
mem_width = ctrl.mem_width

return rd, alu_res, is_store, is_load, mem_width, rs2
```

---

## 数据流向

```
ID 阶段 ──→ ctrl ──→ EX 阶段
           pc
           rs1
           rs2
           imm
                     ↓
               ALU 操作数选择
               ALU 运算
               分支判断
               跳转地址计算
                     ↓
               alu_res ──→ MEM 阶段
               branch_target ──→ IF 阶段
```

---

## 设计要点

1. **ALU 运算**：支持加、减、逻辑、移位、比较等运算
2. **分支判断**：支持 BEQ、BNE、BLT、BGE、BLTU、BGEU
3. **跳转指令**：支持 JAL 和 JALR
4. **分支预测**：检测预测错误并更新分支目标
5. **冲刷处理**：将被冲刷指令的 rd 设置为 x0

---

## 相关文件

- [`src/EX.py`](../src/EX.py) - EX 模块实现
- [`src/utils.py`](../src/utils.py) - [`ExCtrlSignals`](../src/utils.py:92)、[`MemCtrlSignals`](../src/utils.py:84) 定义
- [`docs/assassyn_zh.md`](../docs/assassyn_zh.md) - Assassyn 语言文档

---

## 总结

[`Executor`](../src/EX.py:4) 模块负责：
1. **ALU 运算**：执行各种算术和逻辑运算
2. **分支判断**：判断分支是否应该跳转
3. **跳转地址计算**：计算 JAL/JALR 的跳转目标
4. **分支预测处理**：检测预测错误并更新分支目标
5. **MEM 阶段调用**：准备 MEM 阶段控制信号并调用 MEM 模块
6. **输出状态**：提供目标寄存器地址、ALU 结果、Load/Store 标志等
