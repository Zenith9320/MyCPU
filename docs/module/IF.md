# IF (Instruction Fetch) 模块文档

## 概述

[`Fetcher`](../src/IF.py:5) 模块是五级流水线 RISC-V CPU 中的**取指阶段**（Instruction Fetch Stage）。它负责维护程序计数器（PC），处理流水线暂停和分支跳转，并调用解码阶段。

该模块包含 [`Fetcher`](../src/IF.py:5) 和 [`FetcherImpl`](../src/IF.py:17) 两个类，其中 [`Fetcher`](../src/IF.py:5) 负责 PC 寄存器的初始化，[`FetcherImpl`](../src/IF.py:17) 负责 PC 更新逻辑和调用 ID 阶段。

该模块是 [`Module`](../docs/assassyn_zh.md:389) 类型的时序逻辑模块。

---

## 模块定义

### Fetcher 类

```python
class Fetcher(Module):
    def __init__(self):
        super().__init__(ports={})
```

**类型**：[`Module`](../docs/assassyn_zh.md:389)（时序逻辑模块）

### FetcherImpl 类

```python
class FetcherImpl(Downstream):
    def __init__(self):
        super().__init__()
```

**类型**：[`Downstream`](../docs/assassyn_zh.md:...)（下游模块）

---

## 端口定义

### Fetcher 端口

无端口定义。

---

## build 方法参数

### Fetcher.build

无输入参数。

### FetcherImpl.build

| 参数名 | 类型 | 说明 |
|--------|------|------|
| [`pc_reg`](../src/IF.py:24) | `Array` | 存储 PC 的寄存器 |
| [`last_pc_reg`](../src/IF.py:25) | `Array` | 存储上一个周期 PC 的寄存器 |
| [`decoder`](../src/IF.py:26) | `Module` | async_call 的下一级模块 |
| [`is_stall`](../src/IF.py:27) | `Value` | 决定是否保持当前状态的变量 |
| [`branch_target_reg`](../src/IF.py:28) | `Array` | 存储可能存在的跳转指令的目标 PC 位置 |
| [`rubbish`](../src/IF.py:29) | `Value` | 占位用，无实际意义 |

---

## 输出参数

### Fetcher 输出

| 参数名 | 类型 | 说明 |
|--------|------|------|
| [`pc_reg`](../src/IF.py:11) | `RegArray` | PC 寄存器数组 |
| [`last_pc_reg`](../src/IF.py:12) | `RegArray` | 上一个周期 PC 寄存器数组 |
| [`pc_addr`](../src/IF.py:13) | `Bits(32)` | 当前 PC 地址 |

### FetcherImpl 输出

| 参数名 | 类型 | 说明 |
|--------|------|------|
| [`current_pc_addr`](../src/IF.py:65) | `Bits(32)` | 当前 PC 地址 |

---

## 核心逻辑

### 1. 暂停处理（第 31-37 行）

```python
valid_is_stall = is_stall.optional(Bits(1)(0))
rubbish_val = rubbish.optional(Bits(32)(0))

with Condition(valid_is_stall == Bits(1)(1)):
    debug_log("Stall in IF")

current_pc_addr = (valid_is_stall == Bits(1)(1)).select(last_pc_reg[0], pc_reg[0]).bitcast(Bits(32))
```

处理流水线暂停信号，如果暂停则使用上一个周期的 PC。

### 2. 分支目标处理（第 42-46 行）

```python
branch_target = branch_target_reg[0].bitcast(Bits(32))
current_pc_addr = (branch_target != Bits(32)(0)).select(branch_target, current_pc_addr)
with Condition(branch_target != Bits(32)(0)):
    debug_log("IF: Flush to 0x{:x}", branch_target)
```

如果 EX 阶段检测到分支预测错误，则更新 PC 为跳转目标地址。

### 3. PC 更新（第 47-50 行）

```python
next_pc_addr = (current_pc_addr.bitcast(UInt(32)) + UInt(32)(4)).bitcast(Bits(32))

pc_reg[0] <= next_pc_addr
last_pc_reg[0] <= current_pc_addr
```

预测下一条指令的 PC 地址（当前 PC + 4），并更新寄存器。这里我们进行了最无脑的分支预测，也就是都取not take的情况，此时PC=PC+4

### 4. 调用 ID 阶段（第 59-63 行）

```python
decoder.async_called(
    pc = current_pc_addr,
    next_pc = next_pc_addr,
    is_stall = valid_is_stall,
)
```

异步调用解码阶段，传递当前 PC、下一 PC 和暂停信号。

---

## 数据流向

```
IF 阶段 ──→ pc ──→ ID 阶段
            next_pc
            is_stall
```

---

## 设计要点

1. **PC 维护**：管理程序计数器，计算下一条指令地址
2. **暂停处理**：在流水线暂停时保持当前状态
3. **分支跳转**：响应分支预测错误，更新 PC 为跳转目标
4. **调试日志**：记录 PC 变化和分支跳转

---

## 相关文件

- [`src/IF.py`](../src/IF.py) - IF 模块实现
- [`docs/assassyn_zh.md`](../docs/assassyn_zh.md) - Assassyn 语言文档

---

## 总结

[`Fetcher`](../src/IF.py:5) 模块负责：
1. **PC 维护**：管理程序计数器，计算下一条指令地址
2. **暂停处理**：在流水线暂停时保持当前状态
3. **分支跳转**：响应分支预测错误，更新 PC 为跳转目标
4. **ID 阶段调用**：传递当前 PC 和下一 PC 给解码阶段