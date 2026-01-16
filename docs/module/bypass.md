# Bypass 模块文档

## 概述

[`Bypass`](../src/bypass.py:4) 模块是五级流水线 RISC-V CPU 中的**数据冒险检测与旁路控制单元**。它负责检测流水线中的数据依赖关系，并决定是否需要暂停流水线（Stall）或使用旁路（Forwarding）技术来消除数据冒险。

该模块是一个 [`Downstream`](../docs/assassyn_zh.md:482) 类型的纯组合逻辑模块，不包含任何状态存储，其输出完全由当前周期的输入决定。

---

## 模块定义

```python
class Bypass(Downstream):
    def __init__(self):
        super().__init__()
```

**类型**：[`Downstream`](../docs/assassyn_zh.md:482)（纯组合逻辑模块）

**特点**：
- 无状态存储（无 [`RegArray`](../docs/assassyn_zh.md:275)）
- 使用 [`@downstream.combinational`](../docs/assassyn_zh.md:493) 装饰器
- 输出即时响应，无时钟延迟

---

## 输入参数

| 参数名 | 类型 | 说明 |
|--------|------|------|
| [`rs1_addr`](../src/bypass.py:11) | `Value` | 当前 ID 阶段指令的源寄存器 1 地址（rs1） |
| [`rs2_addr`](../src/bypass.py:12) | `Value` | 当前 ID 阶段指令的源寄存器 2 地址（rs2） |
| [`ex_dest_addr`](../src/bypass.py:13) | `Value` | EX 阶段指令的目标寄存器地址（rd） |
| [`ex_is_load`](../src/bypass.py:14) | `Value` | EX 阶段是否为 Load 指令 |
| [`ex_is_store`](../src/bypass.py:15) | `Value` | EX 阶段是否为 Store 指令 |
| [`mem_dest_addr`](../src/bypass.py:16) | `Value` | MEM 阶段指令的目标寄存器地址（rd） |
| [`mem_is_store`](../src/bypass.py:17) | `Value` | MEM 阶段是否为 Store 指令 |
| [`wb_dest_addr`](../src/bypass.py:18) | `Value` | WB 阶段指令的目标寄存器地址（rd） |

**注意**：所有输入参数均为 [`Value`](../docs/assassyn_zh.md:235) 类型，表示可能包含无效数据（流水线气泡）。

---

## 输出参数

| 参数名 | 类型 | 说明 |
|--------|------|------|
| [`rs1_ex_type`](../src/bypass.py:42) | `Bits(4)` | rs1 的旁路类型选择信号 |
| [`rs2_ex_type`](../src/bypass.py:46) | `Bits(4)` | rs2 的旁路类型选择信号 |
| [`is_stall`](../src/bypass.py:38) | `Bits(1)` | 流水线暂停信号（1=暂停，0=继续） |

---

## 旁路类型定义

旁路类型使用**独热码**表示，定义在 [`utils.py`](../src/utils.py:109) 中：

| 类型 | 独热码 | 说明 | 优先级 |
|------|--------|------|--------|
| [`Rs1Type.EX`](../src/utils.py:111) / [`Rs2Type.EX`](../src/utils.py:116) | `0b0010` | 从 EX 阶段旁路（最新数据） | 最高 |
| [`Rs1Type.MEM`](../src/utils.py:112) / [`Rs2Type.MEM`](../src/utils.py:117) | `0b0100` | 从 MEM 阶段旁路 | 高 |
| [`Rs1Type.WB`](../src/utils.py:113) / [`Rs2Type.WB`](../src/utils.py:118) | `0b1000` | 从 WB 阶段旁路 | 中 |
| [`Rs1Type.NONE`](../src/utils.py:110) / [`Rs2Type.NONE`](../src/utils.py:115) | `0b0001` | 无旁路，使用寄存器堆原始值 | 最低 |

**优先级顺序**：EX > MEM > WB > NONE

---

## 核心逻辑

### 1. Value 处理（第 20-27 行）

由于输入参数为 [`Value`](../docs/assassyn_zh.md:235) 类型，需要使用 [`.optional()`](../docs/assassyn_zh.md:242) 方法处理可能无效的数据：

```python
rs1_addr_val = rs1_addr.optional(Bits(5)(0))
ex_dest_addr_val = ex_dest_addr.optional(Bits(5)(0))
# ... 其他参数类似处理
```

**作用**：如果输入无效（流水线气泡），则返回默认值 `0`。

### 2. 零寄存器检测（第 31-32 行）

```python
rs1_is_zero = rs1_addr_val == Bits(5)(0)
rs2_is_zero = rs2_addr_val == Bits(5)(0)
```

**作用**：检测源寄存器是否为 x0（零寄存器）。x0 寄存器是只读的，始终返回 0，因此不需要旁路。

### 3. 流水线暂停检测（第 38 行）

```python
is_stall = ex_is_store_val | ex_is_load_val | mem_is_store_val
```

**暂停条件**：
- EX 阶段是 Load 指令：Load 指令需要访问内存，数据在 MEM 阶段才能获取
- EX 阶段是 Store 指令：Store 指令需要访问内存，会占用内存端口
- MEM 阶段是 Store 指令：Store 指令正在访问内存

**原因**：这些情况下，当前周期的内存操作会与后续指令的内存访问冲突，必须暂停流水线。

### 4. 旁路类型选择（第 40-46 行）

#### rs1 旁路选择逻辑：

```python
# 步骤 1: 检查是否需要从 WB 阶段旁路
rs1_wb_type = ((rs1_addr_val == wb_dest_addr_val) & (~rs1_is_zero)).select(Rs1Type.WB, Rs1Type.NONE)

# 步骤 2: 检查是否需要从 MEM 阶段旁路（优先级高于 WB）
rs1_mem_type = ((rs1_addr_val == mem_dest_addr_val) & (~rs1_is_zero)).select(Rs1Type.MEM, rs1_wb_type)

# 步骤 3: 检查是否需要从 EX 阶段旁路（优先级最高）
rs1_ex_type = ((rs1_addr_val == ex_dest_addr_val) & (~rs1_is_zero)).select(Rs1Type.EX, rs1_mem_type)
```

#### rs2 旁路选择逻辑：

```python
# 步骤 1: 检查是否需要从 WB 阶段旁路
rs2_wb_type = ((rs2_addr_val == wb_dest_addr_val) & (~rs2_is_zero)).select(Rs2Type.WB, Rs2Type.NONE)

# 步骤 2: 检查是否需要从 MEM 阶段旁路（优先级高于 WB）
rs2_mem_type = ((rs2_addr_val == mem_dest_addr_val) & (~rs2_is_zero)).select(Rs2Type.MEM, rs2_wb_type)

# 步骤 3: 检查是否需要从 EX 阶段旁路（优先级最高）
rs2_ex_type = ((rs2_addr_val == ex_dest_addr_val) & (~rs2_is_zero)).select(Rs2Type.EX, rs2_mem_type)
```

**逻辑说明**：
1. **条件判断**：`(rs_addr == dest_addr) & (~rs_is_zero)`
   - 源寄存器地址等于某阶段的目标寄存器地址
   - 源寄存器不是零寄存器

2. **优先级实现**：使用嵌套的 [`.select()`](../docs/assassyn_zh.md:823) 实现
   - 如果匹配 EX 阶段，返回 EX
   - 否则检查 MEM 阶段
   - 否则检查 WB 阶段
   - 否则返回 NONE

3. **为什么 EX 优先级最高**：EX 阶段产生的数据是最新的，应该优先使用

---

## 数据冒险类型

### 1. RAW (Read After Write) 冒险

当前指令需要读取一个寄存器，而之前的指令正在写入该寄存器。

**示例**：
```
add x1, x2, x3    # EX 阶段，目标寄存器 x1
sub x4, x1, x5    # ID 阶段，源寄存器 x1
```

**处理**：通过旁路技术，直接将 EX 阶段的 ALU 结果传递给 ID 阶段，无需等待。

### 2. Load-Use 冒险

当前指令需要读取一个寄存器，而之前的 Load 指令正在从内存加载该寄存器的值。

**示例**：
```
lw x1, 0(x2)      # EX 阶段，Load 指令
add x3, x1, x4    # ID 阶段，需要 x1 的值
```

**处理**：Load 指令的数据在 MEM 阶段才能获取，无法通过旁路解决，必须暂停流水线。

### 3. 结构冒险（内存冲突）

当 Load/Store 指令在 EX 或 MEM 阶段时，会占用内存端口，导致后续的 Load/Store 指令无法访问内存。

**处理**：检测到 EX 或 MEM 阶段有 Store 指令时，暂停流水线。

---

## 旁路数据流向

```
流水线阶段：  IF      ID      EX      MEM     WB
                     ↓       ↓       ↓       ↓
                     rs1     ALU     Memory  Writeback
                     rs2     Result  Result  Register
                              ↓       ↓       ↓
                              └───────┴───────┘
                                      ↓
                              Bypass 模块检测依赖
                                      ↓
                    ┌─────────────────┴─────────────────┐
                    ↓                                   ↓
              选择旁路数据                          暂停流水线
                    ↓                                   ↓
              EX/MEM/WB → ID                       Stall IF/ID
```

---

## 使用示例

在 ID 阶段的实现中，Bypass 模块被调用：

```python
# 调用 Bypass 模块
rs1_type, rs2_type, stall_if = bypass.build(
    rs1_addr=pre_pkt.rs1,
    rs2_addr=pre_pkt.rs2,
    ex_dest_addr=ex_rd,
    ex_is_load=ex_is_load,
    ex_is_store=ex_is_store,
    mem_dest_addr=mem_rd,
    mem_is_store=mem_is_store,
    wb_dest_addr=wb_rd,
)

# 根据 rs1_type 选择数据源
real_rs1 = rs1_type.select1hot(
    rs1,              # Rs1Type.NONE: 原始值
    ex_bypass[0],     # Rs1Type.EX: EX 阶段旁路
    mem_bypass[0],    # Rs1Type.MEM: MEM 阶段旁路
    wb_bypass[0],     # Rs1Type.WB: WB 阶段旁路
)

# 根据 rs2_type 选择数据源
real_rs2 = rs2_type.select1hot(
    rs2,              # Rs2Type.NONE: 原始值
    ex_bypass[0],     # Rs2Type.EX: EX 阶段旁路
    mem_bypass[0],    # Rs2Type.MEM: MEM 阶段旁路
    wb_bypass[0],     # Rs2Type.WB: WB 阶段旁路
)

# 根据 stall_if 暂停流水线
wait_until(stall_if == Bits(1)(0))
```

---

## 调试日志

模块包含两个日志输出，用于调试：

```python
# 输入日志
log(f"Bypass: rs1={rs1_addr_val}, rs2={rs2_addr_val}, ex_dest={ex_dest_addr_val}, ex_is_load={ex_is_load_val}, ex_is_store={ex_is_store_val}, mem_dest={mem_dest_addr_val}, wb_dest={wb_dest_addr_val}")

# 输出日志
log(f"Bypass Result: rs1_type={rs1_ex_type}, rs2_type={rs2_ex_type}, is_stall={is_stall}")
```

**日志格式**：
- 输入：显示所有源寄存器地址和各阶段目标寄存器地址
- 输出：显示旁路类型选择结果和暂停信号

---

## 设计要点

### 1. 纯组合逻辑

Bypass 模块是 [`Downstream`](../docs/assassyn_zh.md:482) 类型，不包含任何状态存储。这意味着：
- 输出完全由当前周期的输入决定
- 无时钟延迟，即时响应
- 适合实现需要快速反馈的冒险检测逻辑

### 2. 优先级设计

旁路优先级为 EX > MEM > WB > NONE，这是因为：
- EX 阶段的数据是最新的，应该优先使用
- MEM 阶段的数据次新
- WB 阶段的数据已经写回寄存器堆，可以直接读取

### 3. 零寄存器处理

x0 寄存器是只读的，始终返回 0，因此：
- 不需要旁路
- 不需要暂停
- 直接使用常量 0

### 4. Value 类型处理

使用 [`.optional()`](../docs/assassyn_zh.md:242) 方法处理可能无效的输入，确保：
- 流水线气泡不会导致错误
- 无效数据有默认值
- 逻辑始终有效

---

## 限制与注意事项

1. **Load-Use 冒险无法通过旁路解决**：必须暂停流水线
2. **内存冲突需要暂停**：Store 指令会占用内存端口
3. **不支持多周期指令**：乘除法等指令需要额外的处理
4. **不支持乱序执行**：本设计是顺序执行的流水线

---

## 相关文件

- [`src/bypass.py`](../src/bypass.py) - Bypass 模块实现
- [`src/utils.py`](../src/utils.py) - 旁路类型定义（[`Rs1Type`](../src/utils.py:109)、[`Rs2Type`](../src/utils.py:115)）
- [`src/ID.py`](../src/ID.py) - ID 阶段实现（调用 Bypass 模块）
- [`docs/assassyn_zh.md`](../docs/assassyn_zh.md) - Assassyn 语言文档

---

## 总结

[`Bypass`](../src/bypass.py:4) 模块是五级流水线 CPU 中的关键组件，负责：
1. **检测数据依赖**：比较源寄存器地址与各阶段目标寄存器地址
2. **选择旁路数据**：根据优先级选择最新的数据源
3. **控制流水线暂停**：检测 Load-Use 冒险和内存冲突

通过旁路技术，大部分 RAW 冒险可以在不暂停流水线的情况下解决，显著提高了 CPU 的性能。
