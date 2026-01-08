# RISC-V 指令集分析

基于对 Assassyn 项目中 examples/minor-cpu/workloads/ 目录下的测试程序分析，以下是实现 RISC-V CPU 需要支持的指令列表。

## 基础指令 (RV32I 基础指令集)

### 算术指令
- `add` - 加法：`add rd, rs1, rs2`
- `addi` - 立即数加法：`addi rd, rs1, imm`
- `sub` - 减法：`sub rd, rs1, rs2`
- `sll` - 逻辑左移：`sll rd, rs1, rs2`
- `slli` - 立即数逻辑左移：`slli rd, rs1, imm`
- `srl` - 逻辑右移：`srl rd, rs1, rs2`
- `srli` - 立即数逻辑右移：`srli rd, rs1, imm`
- `sra` - 算术右移：`sra rd, rs1, rs2`（实际上没有）
- `srai` - 立即数算术右移：`srai rd, rs1, imm`

### 逻辑指令
- `and` - 按位与：`and rd, rs1, rs2`
- `andi` - 立即数按位与：`andi rd, rs1, imm`
- `or` - 按位或：`or rd, rs1, rs2`
- `ori` - 立即数按位或：`ori rd, rs1, imm`
- `xor` - 按位异或：`xor rd, rs1, rs2`（实际上没有）
- `xori` - 立即数按位异或：`xori rd, rs1, imm`

### 比较指令
- `slt` - 小于比较（有符号）：`slt rd, rs1, rs2`（实际上没有）
- `sltu` - 小于比较（无符号）：`sltu rd, rs1, rs2`

### 数据传输指令
- `lw` - 加载字：`lw rd, offset(rs1)`
- `sw` - 存储字：`sw rs2, offset(rs1)`
- `lbu` - 加载字节（无符号）：`lbu rd, offset(rs1)`
- `sb` - 存储字节：`sb rs2, offset(rs1)`

### 分支指令
- `beq` - 相等则分支：`beq rs1, rs2, offset`
- `bne` - 不相等则分支：`bne rs1, rs2, offset`
- `blt` - 小于则分支（有符号）：`blt rs1, rs2, offset`
- `bge` - 大于等于则分支（有符号）：`bge rs1, rs2, offset`
- `bltu` - 小于则分支（无符号）：`bltu rs1, rs2, offset`
- `bgeu` - 大于等于则分支（无符号）：`bgeu rs1, rs2, offset`

### 跳转指令
- `jal` - 跳转并链接：`jal rd, offset`
- `jalr` - 寄存器跳转并链接：`jalr rd, offset(rs1)`
- `auipc` - PC 相对高位立即数加载：`auipc rd, imm`
- `lui` - 高位立即数加载：`lui rd, imm`

### 系统指令
- `ebreak` - 断点
- `csrrw` - CSR 读写：`csrrw rd, csr, rs1`
- `csrrs` - CSR 读设置：`csrrs rd, csr, rs1`
- `csrc` - CSR 读清除：`csrc rd, csr, rs1`
- `csrrwi` - CSR 立即数读写：`csrrwi rd, csr, imm`
- `csrrsi` - CSR 立即数读设置：`csrrsi rd, csr, imm`
- `csrrci` - CSR 立即数读清除：`csrrci rd, csr, imm`

## 特殊寄存器 (CSR)

根据测试程序，需要访问以下 CSR：

- `mstatus` - 机器状态寄存器
- `mtvec` - 机器陷阱向量基地址寄存器
- `mepc` - 机器异常程序计数器
- `mcause` - 机器异常原因寄存器
- `mhartid` - 机器硬件线程 ID
- `mcycle` - 机器周期计数器
- `minstret` - 机器指令退休计数器

## 指令使用频率分析

基于测试程序分析，以下指令使用频率最高：

1. `lw`, `sw` - 内存访问指令（最频繁）
2. `addi` - 立即数加法（地址计算常用）
3. `beq`, `bne` - 条件分支（循环控制）
4. `jal`, `jalr` - 函数调用和返回
5. `lui`, `auipc` - 地址生成
6. `add`, `sub` - 算术运算
7. `slli`, `srli` - 移位操作
8. `and`, `or`, `xor` - 逻辑运算
9. `csrrw`, `csrrs` - 系统寄存器访问
10. `ecall`, `ebreak` - 系统调用和断点

## 实现优先级

基于使用频率和重要性，建议按以下优先级实现：

### 第一阶段（基础功能）
- 数据传输指令：`lw`, `sw`, `lbu`, `sb`
- 算术指令：`add`, `addi`, `sub`
- 分支指令：`beq`, `bne`
- 跳转指令：`jal`, `jalr`
- 地址生成：`lui`, `auipc`

### 第二阶段（完整指令集）
- 逻辑指令：`and`, `andi`, `or`, `ori`, `xor`, `xori`
- 移位指令：`sll`, `slli`, `srl`, `srli`, `sra`, `srai`
- 比较指令：`slt`, `sltu`, `slti`, `sltiu`
- 分支指令：`blt`, `bge`, `bltu`, `bgeu`
- 系统指令：`ecall`, `ebreak`, `csrrw`, `csrrs`, `csrc`

### 第三阶段（扩展功能）
- 乘法和除法指令：`mul`, `div`, `rem` 等
- 高级系统功能：完整 CSR 访问
- 中断和异常处理

## 测试程序使用的特定模式

1. **0to100.exe**：简单的累加循环，主要使用 `lw`, `add`, `bne`
2. **multiply.exe**：乘法函数实现，使用了 `mul` 指令和复杂循环
3. **vvadd.exe**：向量加法，使用了数组访问和循环结构

这些测试程序覆盖了 RISC-V 指令集的核心功能，是实现一个完整 RISC-V CPU 的良好起点。