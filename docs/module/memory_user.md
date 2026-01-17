# MemoryUser 模块文档

## 概述

[`MemoryUser`](../src/memory_user.py:3) 模块是五级流水线 RISC-V CPU 中的**内存访问控制单元**。它负责协调 IF 阶段（取指）和 MEM 阶段（访存）对数据内存的访问，处理 Store 指令的延迟写入，并支持字节/半字/字访问。

该模块是 [`Downstream`](../docs/assassyn_zh.md:482) 类型的纯组合逻辑模块。

---

## 模块定义

```python
class MemoryUser(Downstream):
    def __init__(self):
        super().__init__()
```

**类型**：[`Downstream`](../docs/assassyn_zh.md:482)（纯组合逻辑模块）

---

## build 方法参数

| 参数名 | 类型 | 说明 |
|--------|------|------|
| [`if_addr`](../src/memory_user.py:10) | `Value` | IF 阶段的指令地址 |
| [`mem_addr`](../src/memory_user.py:11) | `Value` | MEM 阶段的数据地址 |
| [`ex_is_load`](../src/memory_user.py:12) | `Value` | EX 阶段是否为 Load 指令 |
| [`ex_is_store`](../src/memory_user.py:13) | `Value` | EX 阶段是否为 Store 指令 |
| [`wdata`](../src/memory_user.py:14) | `Value` | 要写入的数据 |
| [`width`](../src/memory_user.py:15) | `Value` | 访问宽度（字节/半字/字） |
| [`sram`](../src/memory_user.py:16) | `SRAM` | 数据内存 SRAM |

---

## 核心逻辑

### 1. Value 处理（第 18-23 行）

使用 [`.optional()`](../docs/assassyn_zh.md:242) 处理可能无效的输入数据。

### 2. Store 延迟写入（第 25-34 行）

Store 指令在 EX 阶段检测到，但实际写入需要在下一周期完成。使用 [`RegArray`](../docs/assassyn_zh.md:275) 存储写状态：

```python
need_write = RegArray(Bits(1), 1, initializer=[0])
write_addr = RegArray(Bits(32), 1, initializer=[0])
write_data = RegArray(Bits(32), 1, initializer=[0])
write_width = RegArray(Bits(3), 1, initializer=[0])

need_refresh = ex_is_store_val & ~need_write[0]
need_write[0] <= need_refresh.select(Bits(1)(1), Bits(1)(0))
write_addr[0] <= need_refresh.select(mem_addr_val, Bits(32)(0))
write_data[0] <= need_refresh.select(wdata_val, Bits(32)(0))
write_width[0] <= need_refresh.select(width_val, Bits(3)(0))
```

**作用**：
- 当检测到 Store 指令且当前没有写操作时，设置写标志
- 保存地址、数据和宽度供下一周期使用

### 3. 地址和数据选择（第 36-43 行）

```python
we = need_write[0]
re = ~we
final_mem_addr = we.select(write_addr[0], mem_addr_val)
is_from_ex = ex_is_load_val | ex_is_store_val | we
final_addr = is_from_ex.select(final_mem_addr, if_addr_val)

final_wdata = we.select(write_data[0], Bits(32)(0))
final_width = we.select(write_width[0], Bits(32)(1))
```

**逻辑**：
- 写使能（we）来自延迟写入标志
- 读使能（re）是写使能的反
- 如果有写操作，使用延迟的写地址；否则使用 MEM 阶段地址
- 如果来自 EX 阶段（Load/Store），使用 MEM 地址；否则使用 IF 地址
- 写数据和宽度根据写使能选择

### 4. 访问掩码处理（第 46-54 行）

处理字节/半字/字访问的掩码：

```python
shamt = final_mem_addr[0:1].concat(Bits(3)(0)).bitcast(UInt(5))
raw_mask = final_width.select1hot(
    Bits(32)(0x000000FF),   # 字节
    Bits(32)(0x0000FFFF),   # 半字
    Bits(32)(0xFFFFFFFF),   # 字
)
shifted_mask = raw_mask << shamt
shifted_data = final_wdata << shamt
sram_wdata = (sram.dout[0] & (~shifted_mask)) | (shifted_data & shifted_mask)
```

**作用**：
- 根据地址的低 2 位计算移位量
- 根据访问宽度选择掩码
- 将掩码和数据移位到正确位置
- 使用读-修改-写模式只修改目标字节/半字

### 5. SRAM 访问（第 56-62 行）

```python
sram_trunc_addr = (final_addr >> Bits(32)(2))[0:15]
sram.build(
    addr = sram_trunc_addr,
    wdata = sram_wdata,
    we = we,
    re = re,
)
```

**说明**：
- 地址右移 2 位转换为字地址
- 调用 [`sram.build()`](../docs/assassyn_zh.md:342) 进行读写操作

---

## 数据流向

```
IF 阶段 ──→ if_addr ──┐
                     │
                     ├─→ final_addr ─→ SRAM
                     │
EX 阶段 ──→ mem_addr ─┘
           ex_is_load
           ex_is_store
           wdata
           width
           │
           ├─→ 延迟写入状态 ─→ final_wdata ─→ SRAM
           │
           └─→ final_width ─→ 掩码生成 ─→ SRAM
```

---

## 设计要点

1. **Store 延迟写入**：Store 指令在 EX 阶段检测，实际写入在下一周期
2. **IF/MEM 冲突处理**：通过优先级选择地址，避免冲突
3. **字节/半字支持**：使用掩码实现部分字写入
4. **读-修改-写**：只修改目标字节/半字，保留其他字节

---

## 相关文件

- [`src/memory_user.py`](../src/memory_user.py) - MemoryUser 模块实现
- [`docs/assassyn_zh.md`](../docs/assassyn_zh.md) - Assassyn 语言文档

---

## 总结

[`MemoryUser`](../src/memory_user.py:3) 模块负责：
1. **协调 IF/MEM 访问**：处理取指和访存的地址冲突
2. **Store 延迟写入**：使用寄存器延迟 Store 指令的写入
3. **字节/半字支持**：通过掩码实现部分字访问
4. **SRAM 接口**：提供统一的 SRAM 读写接口
