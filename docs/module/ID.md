# ID (Instruction Decode) 模块文档

## 概述

[`Decoder`](../src/ID.py:18) 模块是五级流水线 RISC-V CPU 中的**解码阶段**（Instruction Decode Stage）。它负责从指令缓存中获取指令，解码指令类型，读取源寄存器数据，并处理旁路逻辑以解决数据冒险。

该模块包含 [`Decoder`](../src/ID.py:18) 和 [`DecoderImpl`](../src/ID.py:126) 两个类，其中 [`Decoder`](../src/ID.py:18) 负责指令解码，[`DecoderImpl`](../src/ID.py:126) 负责旁路处理和调用 EX 阶段。

该模块是 [`Module`](../docs/assassyn_zh.md:389) 类型的时序逻辑模块。

---

## 模块定义

### Decoder 类

```python
class Decoder(Module):
    def __init__(self):
        super().__init__(
            ports={
                "pc": Port(Bits(32)),
                "next_pc": Port(Bits(32)),
                "is_stall": Port(Bits(1)),
            }
        )
```

**类型**：[`Module`](../docs/assassyn_zh.md:389)（时序逻辑模块）

### DecoderImpl 类

```python
class DecoderImpl(Downstream):
    def __init__(self):
        super().__init__()
```

**类型**：[`Downstream`](../docs/assassyn_zh.md:...)（下游模块）

---

## 端口定义

### Decoder 端口

| 端口名 | 类型 | 说明 |
|--------|------|------|
| [`pc`](../src/ID.py:22) | `Port(Bits(32))` | 当前指令 PC |
| [`next_pc`](../src/ID.py:23) | `Port(Bits(32))` | 预测的下一指令 PC |
| [`is_stall`](../src/ID.py:24) | `Port(Bits(1))` | 是否暂停流水线 |

---

## build 方法参数

### Decoder.build

| 参数名 | 类型 | 说明 |
|--------|------|------|
| [`icache_dout`](../src/ID.py:29) | `Array` | 指令缓存 |
| [`reg_file`](../src/ID.py:29) | `Array` | 寄存器文件 |

### DecoderImpl.build

| 参数名 | 类型 | 说明 |
|--------|------|------|
| [`ctrl`](../src/ID.py:133) | `Record` | 解码控制信号 |
| [`executor`](../src/ID.py:134) | `Module` | EX 阶段模块 |
| [`rs1_ex_type`](../src/ID.py:135) | `Bits(4)` | rs1 旁路类型 |
| [`rs2_ex_type`](../src/ID.py:136) | `Bits(4)` | rs2 旁路类型 |
| [`if_stall`](../src/ID.py:137) | `Bits(1)` | IF 阶段暂停信号 |
| [`ex_bypass`](../src/ID.py:138) | `Value` | EX-MEM 旁路数据 |
| [`mem_bypass`](../src/ID.py:139) | `Value` | MEM-WB 旁路数据 |
| [`wb_bypass`](../src/ID.py:140) | `Value` | WB 旁路数据 |
| [`branch_target_reg`](../src/ID.py:141) | `Array` | 分支目标寄存器 |

---

## 输出参数

### Decoder 输出

| 参数名 | 类型 | 说明 |
|--------|------|------|
| [`ctrl`](../src/ID.py:107) | `DecoderSignals` | 解码后的控制信号 |
| [`rs1`](../src/ID.py:124) | `Bits(5)` | rs1 寄存器地址 |
| [`rs2`](../src/ID.py:124) | `Bits(5)` | rs2 寄存器地址 |

---

## 核心逻辑

### 1. 弹出端口数据（第 31 行）

```python
pc_addr, next_pc_addr, is_stall = self.pop_all_ports(False)
```

使用 [`pop_all_ports(False)`](../docs/assassyn_zh.md:668) 以非阻塞模式读取端口数据。

### 2. 指令获取和处理（第 32-41 行）

```python
icache_instruction = icache_dout[0].bitcast(Bits(32))
instruction = (is_stall == Bits(1)(0)).select(icache_instruction, last_inst_reg[0])
instruction = (instruction == Bits(32)(0)).select(Bits(32)(0x00000013), instruction)
```

获取指令缓存中的指令，如果暂停则使用上一条指令，并将无效指令（0）转换为 NOP。

### 3. 指令字段解析（第 50-56 行）

```python
opcode = instruction[0:6]
rd = instruction[7:11]
funct3 = instruction[12:14]
rs1 = instruction[15:19]
rs2 = instruction[20:24]
bit30 = instruction[30:30]
imm_i, imm_s, imm_b, imm_u, imm_j = get_imm(instruction)
```

解析指令的各个字段，并提取立即数。

### 4. 指令匹配和解码（第 71-86 行）

```python
for inst_entry in instruction_table:
    match = opcode == inst_entry[1]
    if inst_entry[2] is not None:
        match &= funct3 == Bits(3)(inst_entry[2])
    if inst_entry[3] is not None:
        match &= bit30 == Bits(1)(inst_entry[3])
    alu_op |= match.select(inst_entry[4], Bits(12)(0))
    # ... 其他字段
```

根据指令表匹配指令类型，设置 ALU 操作、分支类型、内存操作等。

### 5. 默认值处理（第 91-95 行）

```python
alu_op = (alu_op == Bits(12)(0)).select(ALUOp.NOP, alu_op)
op1_type = (op1_type == Bits(3)(0)).select(Op1Type.RS1, op1_type)
# ...
```

为未匹配的字段设置默认值。

### 6. 立即数选择和寄存器读取（第 97-99 行）

```python
imm = imm_type.select1hot(Bits(32)(0), imm_i, imm_s, imm_b, imm_u, imm_j)
rs1_data = reg_file[rs1]
rs2_data = reg_file[rs2]
```

根据立即数类型选择立即数，并读取源寄存器数据。

### 7. 控制信号生成（第 107-122 行）

```python
ctrl = DecoderSignals.bundle(
    alu_op = alu_op,
    # ... 其他字段
)
```

生成解码控制信号。

### DecoderImpl 逻辑

### 8. 冲刷和暂停处理（第 143-150 行）

```python
if_flush = branch_target_reg[0] != Bits(32)(0)
if_nop = if_flush | if_stall
rd = if_nop.select(Bits(5)(0), ctrl.rd)
# ...
```

处理分支冲刷和暂停，将相关信号设置为 NOP。

### 9. 旁路数据准备（第 152-158 行）

```python
ex_bypass_val = ex_bypass.optional(Bits(32)(0))
mem_bypass_val = mem_bypass.optional(Bits(32)(0))
wb_bypass_val = wb_bypass.optional(Bits(32)(0))
```

获取旁路数据。

### 10. 旁路选择（第 160-166 行）

```python
rs1_data = rs1_ex_type.select1hot(
    ctrl.rs1_data, fwd_from_ex_to_mem, fwd_from_mem_to_wb, fwd_after_wb
)
rs2_data = rs2_ex_type.select1hot(
    ctrl.rs2_data, fwd_from_ex_to_mem, fwd_from_mem_to_wb, fwd_after_wb
)
```

根据旁路类型选择 rs1 和 rs2 的数据。

### 11. 调用 EX 阶段（第 199-205 行）

```python
executor.async_called(
    ctrl = ctrl_signals,
    pc = ctrl.cur_pc,
    rs1 = rs1_data,
    rs2 = rs2_data,
    imm = ctrl.imm,
)
```

准备 EX 控制信号并异步调用 EX 模块。

---

## 数据流向

```
IF 阶段 ──→ pc ──→ ID 阶段
            next_pc
            is_stall
                      ↓
                指令获取
                指令解码
                寄存器读取
                旁路处理
                      ↓
                ctrl ──→ EX 阶段
                rs1_data
                rs2_data
                imm
```

---

## 设计要点

1. **指令解码**：支持完整的 RISC-V 指令集解码
2. **立即数提取**：支持 I、S、B、U、J 五种立即数格式
3. **旁路处理**：解决流水线中的数据冒险
4. **暂停和冲刷**：处理分支预测错误和流水线暂停
5. **HALT 检测**：识别仿真结束指令

---

## 相关文件

- [`src/ID.py`](../src/ID.py) - ID 模块实现
- [`src/instructions.py`](../src/instructions.py) - 指令表定义
- [`src/utils.py`](../src/utils.py) - [`DecoderSignals`](../src/utils.py:...) 定义
- [`docs/assassyn_zh.md`](../docs/assassyn_zh.md) - Assassyn 语言文档

---

## 总结

[`Decoder`](../src/ID.py:18) 模块负责：
1. **指令获取**：从指令缓存读取当前指令
2. **指令解码**：解析指令字段，确定操作类型
3. **立即数处理**：提取和格式化立即数
4. **寄存器读取**：获取源操作数数据
5. **旁路逻辑**：解决数据冒险，提供最新数据
6. **控制信号生成**：为 EX 阶段准备完整的控制信息
7. **流水线控制**：处理暂停、冲刷和分支预测