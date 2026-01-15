# WB (WriteBack) 模块文档

## 概述

[`WriteBack`](../src/WB.py:4) 模块是五级流水线 RISC-V CPU 中的**写回阶段**（Write Back Stage）。它负责将执行结果写回通用寄存器堆，并提供旁路数据供前序阶段使用。

该模块是 [`Module`](../docs/assassyn_zh.md:389) 类型的时序逻辑模块，拥有独立的端口定义和时钟域。

---

## 模块定义

```python
class WriteBack(Module):
    def __init__(self):
        super().__init__(
            ports={
                "ctrl": Port(WbCtrlSignals),
                "data": Port(Bits(32)),
            }
        )
```

**类型**：[`Module`](../docs/assassyn_zh.md:389)（时序逻辑模块）

**特点**：
- 有端口定义（[`Port`](../docs/assassyn_zh.md:589)）
- 使用 [`@module.combinational`](../docs/assassyn_zh.md:406) 装饰器
- 可以包含状态（本模块无状态）
- 有独立的时钟域

---

## 端口定义

| 端口名 | 类型 | 说明 |
|--------|------|------|
| [`ctrl`](../src/WB.py:8) | [`Port(WbCtrlSignals)`](../src/utils.py:79) | 写回控制信号 |
| [`data`](../src/WB.py:9) | `Port(Bits(32))` | 要写回的数据 |

### WbCtrlSignals 结构

[`WbCtrlSignals`](../src/utils.py:79) 定义在 [`utils.py`](../src/utils.py:79) 中：

```python
WbCtrlSignals = Record(
    rd = Bits(5),      # 目标寄存器地址
    is_halt = Bits(1), # 是否暂停仿真
)
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `rd` | `Bits(5)` | 目标寄存器地址（x0-x31） |
| `is_halt` | `Bits(1)` | 暂停仿真标志 |

---

## build 方法参数

| 参数名 | 类型 | 说明 |
|--------|------|------|
| [`reg_file`](../src/WB.py:16) | `RegArray` | 通用寄存器堆（32个32位寄存器） |

**注意**：[`reg_file`](../src/WB.py:16) 不是通过端口传入的，而是通过外部引用共享的。

---

## 输出参数

| 参数名 | 类型 | 说明 |
|--------|------|------|
| [`index`](../src/WB.py:19) | `Bits(5)` | 写回的目标寄存器地址 |
| [`wb_bypass_value`](../src/WB.py:20) | `Bits(32)` | 写回数据（用于旁路） |

---

## 核心逻辑

### 1. 弹出端口数据（第 18 行）

```python
ctrl, data = self.pop_all_ports(True)
```

**说明**：
- 使用 [`pop_all_ports(True)`](../docs/assassyn_zh.md:668) 以阻塞模式读取端口数据
- `True` 参数表示如果 FIFO 为空，模块会暂停等待
- 返回 [`ctrl`](../src/WB.py:19)（控制信号）和 [`data`](../src/WB.py:20)（写回数据）

### 2. 提取目标寄存器地址（第 19 行）

```python
index = ctrl.rd
```

**说明**：
- 从控制信号中提取目标寄存器地址
- [`index`](../src/WB.py:19) 是一个 5 位的地址，范围 0-31

### 3. 设置旁路数据（第 20 行）

```python
wb_bypass_value = data
```

**说明**：
- 将写回数据保存为旁路值
- 该值会被传递给 [`Bypass`](bypass.md) 模块，供 ID 阶段的指令使用
- 实现了从 WB 阶段到 ID 阶段的数据旁路

### 4. 条件写回（第 21-22 行）

```python
with Condition(index != Bits(5)(0)):
    reg_file[index] = data
```

**说明**：
- 使用 [`Condition`](../docs/assassyn_zh.md:691) 控制写回操作
- 只有当目标寄存器不是 x0 时才执行写回
- x0 是零寄存器，只读且始终为 0，因此不能写入

**为什么需要条件判断**：
- RISC-V 规范规定 x0 寄存器是硬连线为 0 的
- 写入 x0 是无效操作，且可能破坏硬件设计
- 通过条件判断避免不必要的写操作

### 5. 返回输出（第 24 行）

```python
return index, wb_bypass_value
```

**说明**：
- 返回目标寄存器地址 [`index`](../src/WB.py:19)，供 [`Bypass`](bypass.md) 模块检测数据依赖
- 返回旁路数据 [`wb_bypass_value`](../src/WB.py:20)，供前序阶段使用

---

## 数据流向

```
流水线阶段：  IF      ID      EX      MEM     WB
                                      ↓       ↓
                                      Data    WriteBack
                                      Ctrl    Module
                                              ↓
                                        ┌─────────────┐
                                        │ 提取 rd 地址 │
                                        │ 设置旁路数据 │
                                        │ 检查非 x0    │
                                        └─────────────┘
                                              ↓
                                        写入寄存器堆
                                              ↓
                                        更新旁路寄存器
```

---

## 旁路机制

WB 阶段的旁路数据流向：

```
WB 阶段
  ↓
wb_bypass_value (32位数据)
  ↓
wb_bypass_reg (旁路寄存器)
  ↓
Bypass 模块
  ↓
ID 阶段（选择数据源）
  ↓
EX 阶段（使用数据）
```

**作用**：
- 允许 ID 阶段的指令直接使用 WB 阶段即将写回的数据
- 避免因等待寄存器堆更新而产生的流水线暂停
- 提高流水线效率

---

## 零寄存器处理

RISC-V 架构中的 x0 寄存器（零寄存器）：

| 特性 | 说明 |
|------|------|
| 地址 | 0 (`Bits(5)(0)`) |
| 值 | 始终为 0 |
| 可写性 | 只读（硬连线） |
| 用途 | 常数零、丢弃结果 |

**代码处理**：
```python
with Condition(index != Bits(5)(0)):
    reg_file[index] = data
```

**效果**：
- 当 `index == 0` 时，不执行写操作
- 保证了 x0 寄存器的只读特性
- 避免了无效的写操作

---

## 使用示例

在主模块中，WB 模块的构建和使用：

```python
# 实例化 WB 模块
writeback = WriteBack()

# 构建 WB 模块
wb_rd = writeback.build(reg_file)

# 在 MEM 阶段调用 WB 模块
class MemoryAccess(Module):
    @module.combinational
    def build(self, writeback: Module, ...):
        # ... MEM 阶段逻辑 ...

        # 准备写回控制信号
        wb_ctrl = WbCtrlSignals.bundle(
            rd=rd_addr,
            is_halt=Bits(1)(0),
        )

        # 准备写回数据
        wb_data = load_data  # Load 指令的数据

        # 发送到 WB 阶段
        wb_call = writeback.async_called(
            ctrl=wb_ctrl,
            data=wb_data,
        )
        wb_call.bind.set_fifo_depth(ctrl=1, data=1)
```

---

## 与其他模块的交互

### 1. 与寄存器堆的交互

```python
reg_file[index] = data
```

- 写入数据到寄存器堆
- 使用组合逻辑赋值（`=`），立即生效

### 2. 与 Bypass 模块的交互

```python
# WB 模块返回
return index, wb_bypass_value

# Bypass 模块接收
wb_dest_addr = wb_rd  # 目标寄存器地址
wb_bypass_reg[0] = wb_bypass_value  # 旁路数据
```

- 提供目标寄存器地址供依赖检测
- 提供旁路数据供前序阶段使用

### 3. 与 MEM 阶段的交互

```python
# MEM 阶段发送数据到 WB
wb_call = writeback.async_called(ctrl=wb_ctrl, data=wb_data)
```

- MEM 阶段通过 [`async_called`](../docs/assassyn_zh.md:623) 调用 WB 模块
- 数据通过 FIFO 传递

---

## 设计要点

### 1. 阻塞模式读取

```python
ctrl, data = self.pop_all_ports(True)
```

- 使用阻塞模式确保数据有效
- 如果 MEM 阶段没有发送数据，WB 模块会暂停
- 保证了写回操作的时序正确性

### 2. 组合逻辑写回

```python
reg_file[index] = data
```

- 使用组合逻辑赋值（`=`）而非时序赋值（`<=`）
- 数据在当前周期立即写入寄存器堆
- 允许同一周期内的后续指令读取新值

### 3. 条件保护

```python
with Condition(index != Bits(5)(0)):
    reg_file[index] = data
```

- 防止写入零寄存器
- 符合 RISC-V 规范
- 避免硬件错误

### 4. 旁路数据输出

```python
wb_bypass_value = data
return index, wb_bypass_value
```

- 提供旁路数据供前序阶段使用
- 实现数据冒险的旁路解决
- 提高流水线效率

---

## 时序图

```
时钟周期：    T1        T2        T3        T4        T5
IF 阶段：   Inst1     Inst2     Inst3     Inst4     Inst5
ID 阶段：             Inst1     Inst2     Inst3     Inst4
EX 阶段：                       Inst1     Inst2     Inst3
MEM 阶段：                                Inst1     Inst2
WB 阶段：                                          Inst1
                                                     ↓
                                               写回寄存器堆
                                               提供旁路数据
```

**说明**：
- 指令 Inst1 在 T5 周期进入 WB 阶段
- 在 T5 周期，Inst1 的结果写回寄存器堆
- 同时，Inst1 的结果作为旁路数据提供给 ID 阶段的 Inst4

---

## 调试技巧

### 添加日志输出

```python
@module.combinational
def build(self, reg_file: RegArray):
    ctrl, data = self.pop_all_ports(True)
    index = ctrl.rd
    wb_bypass_value = data

    # 添加日志
    with Condition(index != Bits(5)(0)):
        log("WB: Write x{} <= 0x{:x}", index, data)
        reg_file[index] = data

    return index, wb_bypass_value
```

**日志输出示例**：
```
WB: Write x5 <= 0x00000010
WB: Write x6 <= 0x00000014
```

---

## 限制与注意事项

1. **零寄存器不能写入**：x0 寄存器是只读的
2. **组合逻辑写回**：写回操作在当前周期立即生效
3. **阻塞模式**：如果 MEM 阶段没有数据，WB 模块会暂停
4. **无状态存储**：WB 模块本身不包含任何寄存器

---

## 相关文件

- [`src/WB.py`](../src/WB.py) - WB 模块实现
- [`src/utils.py`](../src/utils.py) - [`WbCtrlSignals`](../src/utils.py:79) 定义
- [`src/bypass.py`](../src/bypass.py) - Bypass 模块（使用 WB 的旁路数据）
- [`src/MA.py`](../src/MA.py) - MA 模块（调用 WB 模块）
- [`docs/assassyn_zh.md`](../docs/assassyn_zh.md) - Assassyn 语言文档

---

## 总结

[`WriteBack`](../src/WB.py:4) 模块是五级流水线 CPU 的最后一个阶段，负责：

1. **写回寄存器堆**：将执行结果写入目标寄存器
2. **保护零寄存器**：防止写入 x0 寄存器
3. **提供旁路数据**：将写回数据提供给前序阶段使用
4. **输出目标地址**：供 [`Bypass`](bypass.md) 模块检测数据依赖

通过旁路机制，WB 阶段的数据可以直接被 ID 阶段的指令使用，避免了因等待寄存器堆更新而产生的流水线暂停，显著提高了 CPU 的性能。
