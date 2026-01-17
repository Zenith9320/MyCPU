# MA (MemoryAccess) 模块文档

## 概述

[`MemoryAcess`](../src/MA.py:4) 模块是五级流水线 RISC-V CPU 中的**内存访问阶段**（Memory Access Stage）。它负责处理 Load/Store 指令的数据加载和符号扩展，并将结果传递给 WB 阶段。

该模块是 [`Module`](../docs/assassyn_zh.md:389) 类型的时序逻辑模块。

---

## 模块定义

```python
class MemoryAcess(Module):
    def __init__(self):
        super().__init__(
            ports={
                "ctrl": Port(MemCtrlSignals),
                "alu_result": Port(Bits(32)),
            }
        )
```

**类型**：[`Module`](../docs/assassyn_zh.md:389)（时序逻辑模块）

---

## 端口定义

| 端口名 | 类型 | 说明 |
|--------|------|------|
| [`ctrl`](../src/MA.py:8) | [`Port(MemCtrlSignals)`](../src/utils.py:84) | 内存访问控制信号 |
| [`alu_result`](../src/MA.py:9) | `Port(Bits(32))` | ALU 计算的内存地址 |

### MemCtrlSignals 结构

[`MemCtrlSignals`](../src/utils.py:84) 定义在 [`utils.py`](../src/utils.py:84) 中：

```python
MemCtrlSignals = Record(
    mem_op = Bits(3),      # 内存操作类型
    mem_width = Bits(3),   # 访问宽度
    mem_sign = Bits(2),    # 符号扩展标志
    rd = Bits(5),         # 目标寄存器地址
    is_halt = Bits(1),    # 是否暂停仿真
)
```

---

## build 方法参数

| 参数名 | 类型 | 说明 |
|--------|------|------|
| [`write_back`](../src/MA.py:16) | `Module` | WB 阶段模块 |
| [`sram_dout`](../src/MA.py:17) | `RegArray` | SRAM 数据输出 |

---

## 输出参数

| 参数名 | 类型 | 说明 |
|--------|------|------|
| [`ctrl.rd`](../src/MA.py:55) | `Bits(5)` | 目标寄存器地址 |
| [`final_data`](../src/MA.py:46) | `Bits(32)` | 最终数据（Load 结果或 ALU 结果） |
| [`is_store`](../src/MA.py:45) | `Bits(1)` | 是否为 Store 指令 |

---

## 核心逻辑

### 1. 弹出端口数据（第 19 行）

```python
ctrl, alu_result = self.pop_all_ports(True)
```

使用 [`pop_all_ports(True)`](../docs/assassyn_zh.md:668) 以阻塞模式读取端口数据。

### 2. 提取控制信号（第 20-22 行）

```python
mem_op = ctrl.mem_op
mem_width = ctrl.mem_width
mem_sign = ctrl.mem_sign
```

### 3. 字节/半字选择（第 24-28 行）

```python
raw_data = sram_dout[0].bitcast(Bits(32))

half_sel = alu_result[1:1].select(raw_data[16:31], raw_data[0:15])
byte_sel = alu_result[0:0].select(half_sel[8:15], half_sel[0:7])
```

根据地址的低 2 位选择对应的字节或半字。

### 4. 符号扩展（第 29-36 行）

```python
pad_bit_8 = mem_sign.select(Bits(1)(0), byte_sel[7:7])
pad_bit_16 = mem_sign.select(Bits(1)(0), half_sel[15:15])

padding_8 = pad_bit_8.select(Bits(24)(0xFFFFFF), Bits(24)(0x00000000))
padding_16 = pad_bit_16.select(Bits(16)(0xFFFF), Bits(16)(0x0000))

byte_extended = concat(padding_8, byte_sel)
half_extended = concat(padding_16, half_sel)
```

根据符号扩展标志进行符号扩展或零扩展。

### 5. 宽度选择（第 38-42 行）

```python
load_res = mem_width.select1hot(
    byte_extended,   # 字节
    half_extended,   # 半字
    raw_data        # 字
)
```

根据访问宽度选择对应的扩展数据。

### 6. Load/Store 判断（第 44-46 行）

```python
is_load = mem_op == MemOp.LOAD
is_store = mem_op == MemOp.STORE
final_data = is_load.select(load_res, alu_result)
```

如果是 Load 指令，使用加载的数据；否则使用 ALU 结果。

### 7. 发送到 WB 阶段（第 48-53 行）

```python
wb_ctrl = WbCtrlSignals.bundle(
    rd = ctrl.rd,
    is_halt = ctrl.is_halt,
)

write_back.async_called(ctrl = wb_ctrl, data = final_data)
```

准备写回控制信号并调用 WB 模块。

### 8. 返回输出（第 55 行）

```python
return ctrl.rd, final_data, is_store
```

---

## 数据流向

```
EX 阶段 ──→ ctrl ──→ MA 阶段
           alu_result

SRAM ──→ sram_dout ──→ MA 阶段
                         ↓
                    字节/半字选择
                    符号扩展
                    宽度选择
                         ↓
                    final_data ──→ WB 阶段
```

---

## 设计要点

1. **字节/半字支持**：根据地址选择对应的字节或半字
2. **符号扩展**：支持有符号和无符号加载
3. **Load/Store 区分**：Load 使用内存数据，Store 使用 ALU 结果
4. **数据传递**：将结果传递给 WB 阶段

---

## 相关文件

- [`src/MA.py`](../src/MA.py) - MA 模块实现
- [`src/utils.py`](../src/utils.py) - [`MemCtrlSignals`](../src/utils.py:84)、[`WbCtrlSignals`](../src/utils.py:79) 定义
- [`docs/assassyn_zh.md`](../docs/assassyn_zh.md) - Assassyn 语言文档

---

## 总结

[`MemoryAcess`](../src/MA.py:4) 模块负责：
1. **Load 数据处理**：字节/半字选择、符号扩展、宽度选择
2. **Store 数据传递**：将 ALU 结果传递给 WB 阶段
3. **WB 阶段调用**：准备写回控制信号并调用 WB 模块
4. **输出状态**：提供目标寄存器地址、最终数据和 Store 标志
