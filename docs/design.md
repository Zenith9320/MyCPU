# 五级流水线 RISC-V CPU 设计文档

## 一、总体架构概述

本设计实现一个五级流水线（IF-ID-EX-MA-WB）的 RISC-V CPU，支持 RV32I 基础指令集。流水线各级之间通过 FIFO（深度为1）进行单向通信，实现基本的流水线控制。

### 1.1 流水线结构

```
Driver -> IF -> ID -> EX -> MA -> WB
   |       |      |      |      |      |
   v       v      v      v      v      v
         icache  reg_file  ALU  dcache  reg_file
         (PC更新需要分支信息)
```

### 1.2 模块间通信协议

每个模块通过 `async_called` 调用下游模块，传递 `Record` 结构体。所有 FIFO 深度设为 1，实现刚性级间寄存器。

**重要**：流水线是单向的，不能反向调用。分支跳转信息需要通过共享状态传递。

### 1.3 分支跳转处理机制

由于流水线是单向的，分支跳转信息不能直接从 EX 传递到 IF。解决方案：

1. **共享分支目标寄存器**：在顶层创建一个共享的分支目标寄存器
2. **分支标志寄存器**：记录当前周期是否需要跳转
3. **IF 阶段读取**：在 IF 阶段读取这些共享寄存器，决定是否跳转

```python
# 在 build_cpu 中创建共享状态
br_target = RegArray(Bits(32), 1, initializer=[0])
br_taken = RegArray(Bits(1), 1, initializer=[0])

# 将这些寄存器传递给 IF 和 EX
fetcher.build(decoder, icache, br_target, br_taken)
executor.build(memory_access, br_target, br_taken)
```

---

## 二、模块详细设计

### 2.1 IF (Instruction Fetch) - 取指阶段

#### 功能
- 维护程序计数器 PC
- 从指令缓存读取指令
- 处理分支跳转（读取共享的分支目标寄存器）
- 将 PC 和指令传递给 ID 阶段

#### 端口定义
```python
ports = {
    # 无输入端口（从 Driver 接收启动信号）
}
```

#### 输出给 ID 的数据结构
```python
if_to_id = Record(
    pc=Bits(32),        # 当前 PC 值
    instr=Bits(32),     # 取出的指令
    valid=Bits(1),      # 指令有效标志
)
```

#### 关键逻辑
1. **PC 更新逻辑**：
   - 默认：`PC = PC + 4`
   - 分支跳转时：`PC = br_target`（当 `br_taken == 1`）

2. **指令读取**：
   - 使用 PC 作为地址读取 icache
   - 需要一个周期的延迟（SRAM 特性）

3. **分支处理**：
   - 读取共享的 `br_target` 和 `br_taken` 寄存器
   - 如果 `br_taken == 1`，则更新 PC 为 `br_target`

4. **分支标志复位**：
   - 读取分支标志后，将其复位为 0（避免重复跳转）

#### 伪代码
```python
@module.combinational
def build(self, decoder: Module, icache: SRAM, br_target: RegArray, br_taken: RegArray):
    # PC 寄存器
    pc = RegArray(Bits(32), 1, initializer=[0])
    
    # 读取指令（需要提前一个周期）
    real_fetch = Bits(1)(1)
    icache.build(Bits(1)(0), real_fetch, pc[0][0:31], Bits(32)(0))
    
    # 读取分支信息（共享寄存器）
    current_br_taken = br_taken[0]
    current_br_target = br_target[0]
    
    # PC 更新逻辑
    next_pc = pc[0] + Bits(32)(4)
    pc_update = current_br_taken.select(current_br_target, next_pc)
    
    # 复位分支标志（避免重复跳转）
    (br_taken & self)[0] <= Bits(1)(0)
    
    # 传递给 ID
    if_to_id = if_to_id.bundle(
        pc=pc[0],
        instr=icache.rdata,
        valid=Bits(1)(1)
    )
    decoder.async_called(if_to_id=if_to_id)
    
    # 更新 PC
    (pc & self)[0] <= pc_update
```

---

### 2.2 ID (Instruction Decode) - 译码阶段

#### 功能
- 指令译码（解析操作码、寄存器号、立即数）
- 读取寄存器堆（rs1, rs2）
- 立即数生成和扩展
- 检测数据冒险（RAW）
- 传递译码信息给 EX 阶段

#### 端口定义
```python
ports = {
    "if_to_id": Port(if_to_id),  # 来自 IF 的 PC 和指令
}
```

#### 输出给 EX 的数据结构
```python
id_to_ex = Record(
    # 控制信号
    opcode=Bits(7),          # 操作码
    rd=Bits(5),              # 目标寄存器
    rs1=Bits(5),             # 源寄存器1
    rs2=Bits(5),             # 源寄存器2
    
    # 数据
    pc=Bits(32),             # PC 值
    rs1_data=Bits(32),       # rs1 数据
    rs2_data=Bits(32),       # rs2 数据
    imm=Bits(32),            # 立即数
    
    # 控制标志
    is_load=Bits(1),         # 是否为 load 指令
    is_store=Bits(1),        # 是否为 store 指令
    is_branch=Bits(1),       # 是否为分支指令
    is_jump=Bits(1),         # 是否为跳转指令
    is_alu=Bits(1),          # 是否为 ALU 指令
    mem_write=Bits(1),       # 是否写内存
    mem_read=Bits(1),        # 是否读内存
    reg_write=Bits(1),       # 是否写寄存器
    
    # ALU 控制信号
    alu_op=Bits(4),          # ALU 操作码
    alu_src1=Bits(1),        # ALU 源操作数1选择 (0: rs1, 1: PC)
    alu_src2=Bits(1),        # ALU 源操作数2选择 (0: rs2, 1: imm)
    
    # 分支控制
    br_type=Bits(2),         # 分支类型 (00: beq, 01: bne, 10: bge)
    
    valid=Bits(1),           # 数据有效标志
)
```

#### 指令格式解析

**R-type**: `funct7[31:25] | rs2[24:20] | rs1[19:15] | funct3[14:12] | rd[11:7] | opcode[6:0]`
```python
opcode = instr[0:6]
rd = instr[7:11]
rs1 = instr[15:19]
rs2 = instr[20:24]
funct3 = instr[12:14]
funct7 = instr[25:31]
```

**I-type**: `imm[31:20] | rs1[19:15] | funct3[14:12] | rd[11:7] | opcode[6:0]`
```python
imm_i = instr[20:31]
imm = sign_extend(imm_i, 12)
```

**S-type**: `imm[11:5][31:25] | rs2[24:20] | rs1[19:15] | funct3[14:12] | imm[4:0][11:7] | opcode[6:0]`
```python
imm_s_11_5 = instr[25:31]
imm_s_4_0 = instr[7:11]
imm = sign_extend(concat(imm_s_11_5, imm_s_4_0), 12)
```

**B-type**: `imm[12|10:5][31:25] | rs2[24:20] | rs1[19:15] | funct3[14:12] | imm[4:1|11][11:7] | opcode[6:0]`
```python
imm_b_12 = instr[31:31]
imm_b_10_5 = instr[25:30]
imm_b_4_1 = instr[8:11]
imm_b_11 = instr[7:7]
imm = sign_extend(concat(imm_b_12, imm_b_11, imm_b_10_5, imm_b_4_1, Bits(1)(0)), 13)
```

**U-type**: `imm[31:12] | rd[11:7] | opcode[6:0]`
```python
imm_u = instr[12:31]
imm = concat(imm_u, Bits(12)(0))
```

**J-type**: `imm[20|10:1|11|19:12][31:12] | rd[11:7] | opcode[6:0]`
```python
imm_j_20 = instr[31:31]
imm_j_10_1 = instr[21:30]
imm_j_11 = instr[20:20]
imm_j_19_12 = instr[12:19]
imm = sign_extend(concat(imm_j_20, imm_j_11, imm_j_10_1, imm_j_19_12, Bits(1)(0)), 21)
```

#### 指令译码逻辑

| 指令 | opcode | funct3 | is_load | is_store | is_branch | is_jump | is_alu | mem_read | mem_write | reg_write | alu_op | alu_src1 | alu_src2 |
|------|--------|--------|---------|----------|-----------|---------|--------|----------|-----------|-----------|--------|----------|----------|
| add | 0110011 | 000 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 1 | 0000 | 0 | 0 |
| addi | 0010011 | 000 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 1 | 0000 | 0 | 1 |
| andi | 0010011 | 111 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 1 | 0011 | 0 | 1 |
| slli | 0010011 | 001 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 1 | 0100 | 0 | 1 |
| srai | 0010011 | 101 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 1 | 0101 | 0 | 1 |
| lw | 0000011 | 010 | 1 | 0 | 0 | 0 | 0 | 1 | 0 | 1 | 0000 | 0 | 1 |
| sw | 0100011 | 010 | 0 | 1 | 0 | 0 | 0 | 0 | 1 | 0 | 0000 | 0 | 1 |
| beq | 1100011 | 000 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0000 | 0 | 0 |
| bne | 1100011 | 001 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0001 | 0 | 0 |
| bge | 1100011 | 101 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0010 | 0 | 0 |
| jal | 1101111 | xxx | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0000 | 1 | 1 |
| jalr | 1100111 | 000 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0000 | 0 | 1 |
| lui | 0110111 | xxx | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 1 | 0110 | 0 | 1 |
| auipc | 0010111 | xxx | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 1 | 0111 | 1 | 1 |
| ebreak | 1110011 | 000 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0000 | 0 | 0 |

#### 数据冒险检测

**RAW（Read After Write）冒险定义**：
当前指令需要读取的寄存器（rs1, rs2）与前面指令正在写入的寄存器（rd）相同，但前面指令还未完成写回操作。

**可能触发数据冒险的指令**：

| 前面指令 | 是否写寄存器 | 后面指令 | 是否读寄存器 | 是否触发冒险 |
|---------|------------|---------|------------|------------|
| add | 是 | add | 是 | 是 |
| addi | 是 | add | 是 | 是 |
| addi | 是 | addi | 是 | 是 |
| lw | 是 | add | 是 | 是 |
| lw | 是 | sw | 是 | 是 |
| lui | 是 | add | 是 | 是 |
| auipc | 是 | add | 是 | 是 |
| jal | 是 | add | 是 | 是 |
| jalr | 是 | add | 是 | 是 |
| sw | 否 | add | 是 | 否 |
| beq | 否 | add | 是 | 否 |
| bne | 否 | add | 是 | 否 |
| bge | 否 | add | 是 | 否 |
| ebreak | 否 | - | - | 否 |

**关键观察**：
1. **写寄存器的指令**：add, addi, andi, slli, srai, lw, lui, auipc, jal, jalr
2. **读寄存器的指令**：add, addi, andi, slli, srai, lw, sw, beq, bne, bge, jalr
3. **不写寄存器的指令**：sw, beq, bne, bge, ebreak
4. **不读寄存器的指令**：lui, auipc, jal, ebreak

**冒险场景示例**：

```assembly
# 场景1：EX 阶段冒险（1个周期延迟）
add  t0, t1, t2    # EX: 正在计算 t0
add  t3, t0, t4    # ID: 需要读取 t0，但 t0 还未写回 -> 冒险！

# 场景2：MA 阶段冒险（2个周期延迟）
lw   t0, 0(t1)     # MA: 正在读取内存
add  t2, t0, t3    # ID: 需要读取 t0，但 t0 还未从内存读出 -> 冒险！

# 场景3：连续冒险
add  t0, t1, t2    # EX
add  t3, t0, t4    # ID: 冒险（等待 EX 完成）
add  t5, t3, t6    # IF: 会被暂停，因为 ID 暂停了
```

**冒险检测逻辑**：

在 ID 阶段，需要检测当前指令的 rs1/rs2 是否与 EX 或 MA 阶段的 rd 相同：

```python
# 冒险检测逻辑
def hazard_detection(rs1, rs2, ex_rd, ex_reg_write, ma_rd, ma_reg_write, wb_rd, wb_reg_write):
    # EX 阶段冒险：当前指令需要读取的寄存器与 EX 阶段正在写入的寄存器相同
    ex_hazard_rs1 = ex_reg_write & (rs1 == ex_rd)
    ex_hazard_rs2 = ex_reg_write & (rs2 == ex_rd)
    ex_hazard = ex_hazard_rs1 | ex_hazard_rs2
    
    # MA 阶段冒险：当前指令需要读取的寄存器与 MA 阶段正在写入的寄存器相同
    ma_hazard_rs1 = ma_reg_write & (rs1 == ma_rd)
    ma_hazard_rs2 = ma_reg_write & (rs2 == ma_rd)
    ma_hazard = ma_hazard_rs1 | ma_hazard_rs2
    
    # WB 阶段通常不需要检测，因为寄存器写回是同步的，在下一个周期立即可用
    # 但如果需要更严格的检测，可以添加：
    # wb_hazard_rs1 = wb_reg_write & (rs1 == wb_rd)
    # wb_hazard_rs2 = wb_reg_write & (rs2 == wb_rd)
    # wb_hazard = wb_hazard_rs1 | wb_hazard_rs2
    
    return ex_hazard | ma_hazard
```

**NOP 指令定义**：

当检测到数据冒险时，需要向 EX 阶段发送 NOP 指令（气泡）：

```python
# NOP 指令（addi x0, x0, 0）
nop_signals = {
    'opcode': Bits(7)(0b0010011),
    'rd': Bits(5)(0),
    'rs1': Bits(5)(0),
    'rs2': Bits(5)(0),
    'pc': Bits(32)(0),
    'rs1_data': Bits(32)(0),
    'rs2_data': Bits(32)(0),
    'imm': Bits(32)(0),
    'is_load': Bits(1)(0),
    'is_store': Bits(1)(0),
    'is_branch': Bits(1)(0),
    'is_jump': Bits(1)(0),
    'is_alu': Bits(1)(0),
    'mem_write': Bits(1)(0),
    'mem_read': Bits(1)(0),
    'reg_write': Bits(1)(0),
    'alu_op': Bits(4)(0b0000),
    'alu_src1': Bits(1)(0),
    'alu_src2': Bits(1)(1),
    'br_type': Bits(2)(0b00),
    'valid': Bits(1)(0),  # 标记为无效
}
```

**冒险处理策略**：

1. **检测冒险**：在 ID 阶段检测当前指令是否与 EX 或 MA 阶段的指令存在数据依赖
2. **插入气泡**：如果检测到冒险，向 EX 阶段发送 NOP 指令
3. **保持当前指令**：当前指令在 ID 阶段停留，等待冒险解除
4. **暂停上游**：由于 FIFO 深度为 1，ID 阶段暂停会自动导致 IF 阶段暂停

#### 伪代码

```python
@module.combinational
def build(self, executor: Module, reg_file: RegArray, ex_to_ma: Record, ma_to_wb: Record):
    # 获取 IF 传递的数据
    if_to_id = self.pop_all_ports(True)
    pc = if_to_id.pc
    instr = if_to_id.instr
    
    # 指令译码
    opcode = instr[0:6]
    rd = instr[7:11]
    rs1 = instr[15:19]
    rs2 = instr[20:24]
    funct3 = instr[12:14]
    funct7 = instr[25:31]
    
    # 读取寄存器堆
    rs1_data = reg_file[rs1]
    rs2_data = reg_file[rs2]
    
    # 立即数生成（根据指令类型）
    imm = generate_imm(instr, opcode)
    
    # 控制信号生成
    control_signals = generate_control(opcode, funct3, funct7)
    
    # 获取 EX 和 MA 阶段的写回信息（用于冒险检测）
    # 注意：这些信息需要从 EX 和 MA 阶段传递回来
    # 可以通过在 build_cpu 中创建共享寄存器来实现
    ex_rd = ex_rd_reg[0]  # EX 阶段的 rd
    ex_reg_write = ex_reg_write_reg[0]  # EX 阶段的 reg_write
    ma_rd = ma_rd_reg[0]  # MA 阶段的 rd
    ma_reg_write = ma_reg_write_reg[0]  # MA 阶段的 reg_write
    
    # 数据冒险检测
    hazard = hazard_detection(rs1, rs2, ex_rd, ex_reg_write, ma_rd, ma_reg_write)
    
    # 准备当前指令的数据
    id_to_ex_current = id_to_ex.bundle(
        pc=pc,
        rd=rd,
        rs1=rs1,
        rs2=rs2,
        rs1_data=rs1_data,
        rs2_data=rs2_data,
        imm=imm,
        **control_signals,
        valid=Bits(1)(1)
    )
    
    # 准备 NOP 指令的数据
    id_to_ex_nop = id_to_ex.bundle(
        pc=Bits(32)(0),
        rd=Bits(5)(0),
        rs1=Bits(5)(0),
        rs2=Bits(5)(0),
        rs1_data=Bits(32)(0),
        rs2_data=Bits(32)(0),
        imm=Bits(32)(0),
        opcode=Bits(7)(0b0010011),
        is_load=Bits(1)(0),
        is_store=Bits(1)(0),
        is_branch=Bits(1)(0),
        is_jump=Bits(1)(0),
        is_alu=Bits(1)(0),
        mem_write=Bits(1)(0),
        mem_read=Bits(1)(0),
        reg_write=Bits(1)(0),
        alu_op=Bits(4)(0b0000),
        alu_src1=Bits(1)(0),
        alu_src2=Bits(1)(1),
        br_type=Bits(2)(0b00),
        valid=Bits(1)(0)  # 标记为无效
    )
    
    # 根据冒险情况选择发送的数据
    # 如果有冒险，发送 NOP；否则发送当前指令
    id_to_ex_send = hazard.select(id_to_ex_nop, id_to_ex_current)
    
    # 始终调用 executor（保持流水线流动）
    executor.async_called(id_to_ex=id_to_ex_send)
    
    # 更新共享的写回信息寄存器（供下一周期冒险检测使用）
    # 这些寄存器在 build_cpu 中创建
    (ex_rd_reg & self)[0] <= rd
    (ex_reg_write_reg & self)[0] <= control_signals['reg_write']
```

**关键点**：
1. **始终调用 executor**：无论是否有冒险，都要调用 executor.async_called()，保持流水线流动
2. **选择发送的数据**：有冒险时发送 NOP（valid=0），无冒险时发送当前指令（valid=1）
3. **保持当前指令**：当前指令在 ID 阶段停留，不会推进到 EX 阶段
4. **共享写回信息**：需要在顶层创建共享寄存器来存储 EX 和 MA 阶段的写回信息
5. **自动暂停上游**：由于 FIFO 深度为 1，ID 阶段不消费数据会导致 IF 阶段自动暂停

**顶层共享寄存器设计**：

```python
# 在 build_cpu 中创建共享寄存器
ex_rd_reg = RegArray(Bits(5), 1, initializer=[0])
ex_reg_write_reg = RegArray(Bits(1), 1, initializer=[0])
ma_rd_reg = RegArray(Bits(5), 1, initializer=[0])
ma_reg_write_reg = RegArray(Bits(1), 1, initializer=[0])

# 将这些寄存器传递给 ID、EX、MA 阶段
decoder.build(executor, reg_file, ex_rd_reg, ex_reg_write_reg, ma_rd_reg, ma_reg_write_reg)
executor.build(memory_access, br_target, br_taken, ex_rd_reg, ex_reg_write_reg)
memory_access.build(write_back, dcache, ma_rd_reg, ma_reg_write_reg)
```

**EX 阶段更新共享寄存器**：

```python
# 在 EX 阶段的 build 方法中
# 更新 EX 阶段的写回信息
(ex_rd_reg & self)[0] <= id_to_ex.rd
(ex_reg_write_reg & self)[0] <= id_to_ex.reg_write
```

**MA 阶段更新共享寄存器**：

```python
# 在 MA 阶段的 build 方法中
# 更新 MA 阶段的写回信息
(ma_rd_reg & self)[0] <= ex_to_ma.rd
(ma_reg_write_reg & self)[0] <= ex_to_ma.reg_write
```

---

### 2.3 EX (Execute) - 执行阶段

#### 功能
- ALU 运算（加减、逻辑、移位）
- 分支条件判断
- 计算跳转目标地址
- 计算内存访问地址
- 更新共享的分支目标寄存器
- 传递结果给 MA 阶段

#### 端口定义
```python
ports = {
    "id_to_ex": Port(id_to_ex),  # 来自 ID 的译码信息
}
```

#### 输出给 MA 的数据结构
```python
ex_to_ma = Record(
    # 数据
    alu_result=Bits(32),    # ALU 结果
    rs2_data=Bits(32),      # rs2 数据（用于 store）
    rd=Bits(5),             # 目标寄存器
    
    # 控制标志
    is_load=Bits(1),        # 是否为 load 指令
    is_store=Bits(1),       # 是否为 store 指令
    mem_write=Bits(1),      # 是否写内存
    mem_read=Bits(1),       # 是否读内存
    reg_write=Bits(1),      # 是否写寄存器
    
    valid=Bits(1),          # 数据有效标志
)
```

#### ALU 操作码定义

| alu_op | 操作 | 描述 |
|--------|------|------|
| 0000 | ADD | 加法 |
| 0001 | SUB | 减法 |
| 0010 | AND | 按位与 |
| 0011 | OR | 按位或 |
| 0100 | XOR | 按位异或 |
| 0101 | SLL | 逻辑左移 |
| 0110 | SRL | 逻辑右移 |
| 0111 | SRA | 算术右移 |
| 1000 | LUI | 加载高位立即数 |
| 1001 | AUIPC | PC 相对高位立即数 |

#### ALU 操作数选择

```python
# ALU 源操作数1
alu_src1 = alu_src1_signal.select(pc, rs1_data)

# ALU 源操作数2
alu_src2 = alu_src2_signal.select(imm, rs2_data)
```

#### 分支条件判断

```python
# beq: rs1 == rs2
beq_taken = (rs1_data == rs2_data)

# bne: rs1 != rs2
bne_taken = (rs1_data != rs2_data)

# bge: rs1 >= rs2 (有符号)
bge_taken = (rs1_data.bitcast(Int(32)) >= rs2_data.bitcast(Int(32)))

# 分支跳转
branch_taken = br_type.select1hot(beq_taken, bne_taken, bge_taken)
```

#### 跳转目标计算

```python
# jal: PC + imm
jal_target = pc + imm

# jalr: rs1 + imm
jalr_target = rs1_data + imm

# 分支目标
branch_target = pc + imm
```

#### 分支信息更新

```python
# 判断是否需要跳转
if id_to_ex.is_jump:
    if id_to_ex.opcode == Bits(7)(0b1101111):  # jal
        taken = Bits(1)(1)
        target = jal_target
    else:  # jalr
        taken = Bits(1)(1)
        target = jalr_target
elif id_to_ex.is_branch:
    taken = branch_taken
    target = branch_target
else:
    taken = Bits(1)(0)
    target = Bits(32)(0)

# 更新共享的分支目标寄存器
(br_target & self)[0] <= target
(br_taken & self)[0] <= taken
```

#### 伪代码
```python
@module.combinational
def build(self, memory_access: Module, br_target: RegArray, br_taken: RegArray):
    # 获取 ID 传递的数据
    id_to_ex = self.pop_all_ports(True)
    
    # ALU 操作数选择
    alu_a = id_to_ex.alu_src1.select(id_to_ex.pc, id_to_ex.rs1_data)
    alu_b = id_to_ex.alu_src2.select(id_to_ex.imm, id_to_ex.rs2_data)
    
    # ALU 运算
    alu_result = id_to_ex.alu_op.select1hot(
        alu_a + alu_b,                    # ADD
        alu_a - alu_b,                    # SUB
        alu_a & alu_b,                    # AND
        alu_a | alu_b,                    # OR
        alu_a ^ alu_b,                    # XOR
        alu_a << alu_b[0:4],             # SLL
        alu_a >> alu_b[0:4],             # SRL
        (alu_a.bitcast(Int(32)) >> alu_b[0:4]).bitcast(Bits(32)),  # SRA
        id_to_ex.imm,                     # LUI
        id_to_ex.pc + id_to_ex.imm        # AUIPC
    )
    
    # 分支条件判断
    beq_taken = (id_to_ex.rs1_data == id_to_ex.rs2_data)
    bne_taken = (id_to_ex.rs1_data != id_to_ex.rs2_data)
    bge_taken = (id_to_ex.rs1_data.bitcast(Int(32)) >= id_to_ex.rs2_data.bitcast(Int(32)))
    
    branch_taken = id_to_ex.br_type.select1hot(beq_taken, bne_taken, bge_taken)
    
    # 跳转目标计算
    jal_target = id_to_ex.pc + id_to_ex.imm
    jalr_target = id_to_ex.rs1_data + id_to_ex.imm
    branch_target = id_to_ex.pc + id_to_ex.imm
    
    # 判断是否需要跳转
    if id_to_ex.is_jump:
        if id_to_ex.opcode == Bits(7)(0b1101111):  # jal
            taken = Bits(1)(1)
            target = jal_target
        else:  # jalr
            taken = Bits(1)(1)
            target = jalr_target
    elif id_to_ex.is_branch:
        taken = branch_taken
        target = branch_target
    else:
        taken = Bits(1)(0)
        target = Bits(32)(0)
    
    # 更新共享的分支目标寄存器（供 IF 阶段读取）
    (br_target & self)[0] <= target
    (br_taken & self)[0] <= taken
    
    # 传递给 MA
    ex_to_ma = ex_to_ma.bundle(
        alu_result=alu_result,
        rs2_data=id_to_ex.rs2_data,
        rd=id_to_ex.rd,
        is_load=id_to_ex.is_load,
        is_store=id_to_ex.is_store,
        mem_write=id_to_ex.mem_write,
        mem_read=id_to_ex.mem_read,
        reg_write=id_to_ex.reg_write,
        valid=id_to_ex.valid
    )
    memory_access.async_called(ex_to_ma=ex_to_ma)
```

---

### 2.4 MA (Memory Access) - 访存阶段

#### 功能
- 访问数据缓存（load/store）
- 传递 ALU 结果给 WB 阶段
- 处理 load 指令的数据读取

#### 端口定义
```python
ports = {
    "ex_to_ma": Port(ex_to_ma),  # 来自 EX 的执行信息
}
```

#### 输出给 WB 的数据结构
```python
ma_to_wb = Record(
    # 数据
    data=Bits(32),          # 要写回的数据
    rd=Bits(5),             # 目标寄存器
    
    # 控制标志
    reg_write=Bits(1),      # 是否写寄存器
    
    valid=Bits(1),          # 数据有效标志
)
```

#### 内存访问逻辑

```python
# load: 从 dcache 读取数据
if is_load:
    mem_addr = alu_result
    dcache.build(Bits(1)(0), Bits(1)(1), mem_addr, Bits(32)(0))
    data = dcache.rdata

# store: 向 dcache 写入数据
if is_store:
    mem_addr = alu_result
    dcache.build(Bits(1)(1), Bits(1)(0), mem_addr, rs2_data)
    data = alu_result  # store 不需要写回，但需要传递 rd

# 其他指令: 直接传递 ALU 结果
else:
    data = alu_result
```

#### 伪代码
```python
@module.combinational
def build(self, write_back: Module, dcache: SRAM):
    # 获取 EX 传递的数据
    ex_to_ma = self.pop_all_ports(True)
    
    # 默认数据为 ALU 结果
    data = ex_to_ma.alu_result
    
    # load 指令：读取内存
    with Condition(ex_to_ma.is_load):
        dcache.build(Bits(1)(0), Bits(1)(1), ex_to_ma.alu_result, Bits(32)(0))
        data = dcache.rdata
    
    # store 指令：写入内存
    with Condition(ex_to_ma.is_store):
        dcache.build(Bits(1)(1), Bits(1)(0), ex_to_ma.alu_result, ex_to_ma.rs2_data)
    
    # 传递给 WB
    ma_to_wb = ma_to_wb.bundle(
        data=data,
        rd=ex_to_ma.rd,
        reg_write=ex_to_ma.reg_write,
        valid=ex_to_ma.valid
    )
    write_back.async_called(ma_to_wb=ma_to_wb)
```

---

### 2.5 WB (Write Back) - 写回阶段

#### 功能
- 将结果写回寄存器堆
- 处理 ebreak 指令（终止仿真）

#### 端口定义
```python
ports = {
    "ma_to_wb": Port(ma_to_wb),  # 来自 MA 的访存信息
}
```

#### 伪代码
```python
@module.combinational
def build(self, reg_file: RegArray):
    # 获取 MA 传递的数据
    ma_to_wb = self.pop_all_ports(True)
    
    # 写回寄存器堆
    with Condition(ma_to_wb.reg_write):
        # rd != 0 (x0 是只读寄存器)
        with Condition(ma_to_wb.rd != Bits(5)(0)):
            reg_file[ma_to_wb.rd] = ma_to_wb.data
    
    # 检测 ebreak 指令
    # ebreak 的 opcode 是 1110011
    # 在 ID 阶段会检测到，传递到 WB
    with Condition(ma_to_wb.is_ebreak):
        log("EBREAK detected!")
        finish()
```

---

## 三、数据通路设计

### 3.1 寄存器堆

```python
reg_file = RegArray(Bits(32), 32)
```

- 32 个 32 位通用寄存器
- 同步写入，异步读取
- x0 (zero) 寄存器始终为 0

### 3.2 指令缓存和数据缓存

```python
icache = SRAM(width=32, depth=1 << 16, init_file="workload.exe")
dcache = SRAM(width=32, depth=1 << 16, init_file="workload.data")
```

- 64KB 大小
- 32 位数据宽度
- 异步读取，同步写入

### 3.3 分支跳转共享状态

```python
br_target = RegArray(Bits(32), 1, initializer=[0])
br_taken = RegArray(Bits(1), 1, initializer=[0])
```

- `br_target`：分支目标地址，由 EX 阶段更新，IF 阶段读取
- `br_taken`：分支跳转标志，由 EX 阶段更新，IF 阶段读取并复位

---

## 四、指令执行流程

### 4.1 add rd, rs1, rs2

| 阶段 | 操作 |
|------|------|
| IF | PC -> icache, PC+4 |
| ID | 解析指令，读取 rs1, rs2 |
| EX | alu_result = rs1 + rs2 |
| MA | 无操作 |
| WB | reg_file[rd] = alu_result |

### 4.2 addi rd, rs1, imm

| 阶段 | 操作 |
|------|------|
| IF | PC -> icache, PC+4 |
| ID | 解析指令，读取 rs1，生成 imm |
| EX | alu_result = rs1 + imm |
| MA | 无操作 |
| WB | reg_file[rd] = alu_result |

### 4.3 lw rd, offset(rs1)

| 阶段 | 操作 |
|------|------|
| IF | PC -> icache, PC+4 |
| ID | 解析指令，读取 rs1，生成 imm |
| EX | alu_result = rs1 + imm (内存地址) |
| MA | data = dcache[alu_result] |
| WB | reg_file[rd] = data |

### 4.4 sw rs2, offset(rs1)

| 阶段 | 操作 |
|------|------|
| IF | PC -> icache, PC+4 |
| ID | 解析指令，读取 rs1, rs2，生成 imm |
| EX | alu_result = rs1 + imm (内存地址) |
| MA | dcache[alu_result] = rs2 |
| WB | 无操作 |

### 4.5 beq rs1, rs2, offset

| 阶段 | 操作 |
|------|------|
| IF | PC -> icache, PC+4 |
| ID | 解析指令，读取 rs1, rs2，生成 imm |
| EX | condition = (rs1 == rs2), br_target = PC + imm, 更新 br_target 和 br_taken |
| MA | 无操作 |
| WB | 无操作 |
| IF | 下一周期读取 br_taken，如果为 1 则 PC = br_target |

### 4.6 jal rd, offset

| 阶段 | 操作 |
|------|------|
| IF | PC -> icache, PC+4 |
| ID | 解析指令，生成 imm |
| EX | alu_result = PC + 4, br_target = PC + imm, 更新 br_target 和 br_taken |
| MA | 无操作 |
| WB | reg_file[rd] = alu_result |
| IF | 下一周期读取 br_taken，如果为 1 则 PC = br_target |

### 4.7 lui rd, imm

| 阶段 | 操作 |
|------|------|
| IF | PC -> icache, PC+4 |
| ID | 解析指令，生成 imm (imm[31:12] << 12) |
| EX | alu_result = imm |
| MA | 无操作 |
| WB | reg_file[rd] = alu_result |

### 4.8 auipc rd, imm

| 阶段 | 操作 |
|------|------|
| IF | PC -> icache, PC+4 |
| ID | 解析指令，生成 imm |
| EX | alu_result = PC + imm |
| MA | 无操作 |
| WB | reg_file[rd] = alu_result |

---

## 五、冒险处理

### 5.1 数据冒险 (RAW)

**定义**：
当前指令需要读取的寄存器（rs1, rs2）与前面指令正在写入的寄存器（rd）相同，但前面指令还未完成写回操作。

**检测**：
在 ID 阶段检测当前指令的 rs1/rs2 是否与 EX 或 MA 阶段的 rd 相同，且这些指令会写寄存器。

**解决策略**：
1. **检测冒险**：在 ID 阶段检测当前指令是否与 EX 或 MA 阶段的指令存在数据依赖
2. **插入气泡**：如果检测到冒险，向 EX 阶段发送 NOP 指令（valid=0）
3. **保持当前指令**：当前指令在 ID 阶段停留，等待冒险解除
4. **暂停上游**：由于 FIFO 深度为 1，ID 阶段不消费数据会导致 IF 阶段自动暂停

**关键实现要点**：
- **始终调用 executor**：无论是否有冒险，都要调用 executor.async_called()，保持流水线流动
- **NOP 指令定义**：addi x0, x0, 0，所有控制信号设为 0，valid 设为 0
- **共享写回信息**：在顶层创建共享寄存器存储 EX 和 MA 阶段的写回信息
- **自动暂停机制**：利用 FIFO 的反压机制实现上游暂停

**冒险场景总结**：

| 冒险类型 | 前面指令 | 后面指令 | 延迟周期 | 处理方式 |
|---------|---------|---------|---------|---------|
| EX-EX | add t0, t1, t2 | add t3, t0, t4 | 1 | 插入 1 个气泡 |
| MA-EX | lw t0, 0(t1) | add t2, t0, t3 | 2 | 插入 2 个气泡 |
| MA-MA | lw t0, 0(t1) | lw t2, 0(t0) | 2 | 插入 2 个气泡 |

**优化方向**：
后续可以通过前递（Forwarding）技术来减少气泡，直接将 EX 或 MA 阶段的结果前递给 ID 阶段。

### 5.2 控制冒险 (分支)

**检测**：在 EX 阶段判断分支条件

**解决**：
- 采用"预测不跳转"策略
- 如果分支跳转，则：
  1. 更新共享的 `br_target` 和 `br_taken` 寄存器
  2. IF 阶段在下一周期读取这些寄存器，决定是否跳转
  3. 由于流水线延迟，会有 2 个周期的分支惩罚

**分支惩罚分析**：

```
周期 | IF     | ID     | EX     | MA     | WB
-----|--------|--------|--------|--------|-----
1    | beq    | -      | -      | -      | -
2    | inst1  | beq    | -      | -      | -
3    | inst2  | inst1  | beq    | -      | -
4    | target | inst2  | inst1  | beq    | -
5    | inst3  | target | inst2  | inst1  | beq
```

- 如果 beq 不跳转：inst1, inst2, inst3 正常执行
- 如果 beq 跳转：inst1, inst2 被清空（插入气泡），从 target 开始执行
- 分支惩罚：2 个周期（inst1 和 inst2）

**优化方向**：
后续可以通过分支预测（Branch Prediction）技术来减少分支惩罚。

### 5.3 结构冒险

本设计采用哈佛架构（独立的指令缓存和数据缓存），不存在结构冒险。

### 5.4 WAW 和 WAR 冒险

**WAW（Write After Write）**：
- 定义：后面指令写寄存器的结果覆盖前面指令写寄存器的结果
- 本设计：由于寄存器写回是同步的，且所有写寄存器的指令都按顺序执行，不存在 WAW 冒险

**WAR（Write After Read）**：
- 定义：后面指令写寄存器覆盖了前面指令还未读取的值
- 本设计：由于读寄存器是在 ID 阶段，写寄存器是在 WB 阶段，且流水线是顺序执行的，不存在 WAR 冒险

---

## 六、特殊指令处理

### 6.1 ebreak

- 在 ID 阶段识别（opcode = 1110011）
- 传递到 WB 阶段
- 调用 `finish()` 终止仿真

### 6.2 伪指令

伪指令由汇编器转换为基本指令，CPU 不需要特殊处理：
- `j offset` -> `jal x0, offset`
- `jr rs` -> `jalr x0, 0(rs)`
- `ret` -> `jalr x0, 0(ra)`
- `mv rd, rs` -> `addi rd, rs, 0`
- `li rd, imm` -> `lui` + `addi`

---

## 七、实现优先级

### 第一阶段（基础功能）
1. 实现 IF 阶段：PC 管理、指令读取
2. 实现 ID 阶段：基本指令译码（add, addi, lui, auipc）
3. 实现 EX 阶段：基本 ALU 运算
4. 实现 MA 阶段：内存访问（lw, sw）
5. 实现 WB 阶段：寄存器写回
6. 测试：0to100.exe

### 第二阶段（分支跳转）
1. 实现共享的分支目标寄存器
2. 实现 IF 阶段的分支跳转逻辑
3. 实现分支指令（beq, bne, bge）
4. 实现跳转指令（jal, jalr）
5. 测试：multiply.exe

### 第三阶段（完整指令集）
1. 实现逻辑指令（andi）
2. 实现移位指令（slli, srai）
3. 实现 ebreak
4. 测试：vvadd.exe

---

## 八、测试验证

### 8.1 测试用例

1. **0to100.exe**：简单的累加循环
   - 测试基本算术运算、内存访问、分支
   - 预期输出：0 到 100 的累加和

2. **multiply.exe**：乘法函数实现
   - 测试复杂指令集、函数调用
   - 预期输出：乘法结果

3. **vvadd.exe**：向量加法
   - 测试数组访问、循环结构
   - 预期输出：向量加法结果

### 8.2 验证方法

1. 在关键阶段添加 `log()` 输出
2. 对比仿真输出与预期结果
3. 使用 Verilator 进行波形验证

---

## 九、注意事项

1. **类型转换**：算术运算需要使用 `.bitcast()` 转换为 `Int` 或 `UInt`
2. **位操作**：注意 Assassyn 的位切片是 `[low:high]`（闭区间）
3. **SRAM 延迟**：SRAM 读取需要一个周期，需要提前发送读取请求
4. **FIFO 深度**：所有 FIFO 深度设为 1，实现刚性流水线
5. **寄存器 x0**：x0 寄存器是只读的，始终为 0
6. **分支预测**：采用"预测不跳转"策略，简化实现
7. **冒险处理**：先实现暂停机制，后续可优化为前递
8. **单向流水线**：不能反向调用，分支信息通过共享状态传递
9. **分支标志复位**：IF 阶段读取分支标志后需要复位，避免重复跳转

---

## 十、总结

本设计实现了一个完整的五级流水线 RISC-V CPU，支持 RV32I 基础指令集。通过模块化的设计，每个阶段职责清晰，便于实现和调试。设计考虑了数据冒险和控制冒险的处理，确保流水线的正确执行。关键创新是使用共享的分支目标寄存器来处理分支跳转，避免了反向调用的问题，符合 Assassyn 的单向流水线架构。
