# RISC-V 指令集分析

基于对 workloads 目录下的测试程序分析，以下是实现 RISC-V CPU 需要支持的指令列表。

## 基础指令（RV32I 基础指令集）

### 算术指令
- `add` - 加法：`add rd, rs1, rs2`
- `addi` - 立即数加法：`addi rd, rs1, imm`

### 逻辑指令
- `andi` - 立即数按位与：`andi rd, rs1, imm`

### 移位指令
- `slli` - 立即数逻辑左移：`slli rd, rs1, imm`
- `srai` - 立即数算术右移：`srai rd, rs1, imm`

### 数据传输指令
- `lw` - 加载字：`lw rd, offset(rs1)`
- `sw` - 存储字：`sw rs2, offset(rs1)`

### 分支指令
- `beq` - 相等则分支：`beq rs1, rs2, offset`
- `bne` - 不相等则分支：`bne rs1, rs2, offset`
- `bge` - 大于等于则分支：`bge rs1, rs2, offset`

### 跳转指令
- `jal` - 跳转并链接：`jal rd, offset`
- `jalr` - 寄存器跳转并链接：`jalr rd, offset(rs1)`

### 地址生成指令
- `lui` - 高位立即数加载：`lui rd, imm`
- `auipc` - PC相对高位立即数加载：`auipc rd, imm`

### 系统指令
- `ebreak` - 断点

## 伪指令（由基础指令组合而成）

- `j` - 跳转：`j offset`（实际上是 `jal zero, offset`）
- `jr` - 寄存器跳转：`jr rs`（实际上是 `jalr zero, 0(rs)`）
- `ret` - 返回：`ret`（实际上是 `jalr zero, 0(ra)`）
- `mv` - 移动寄存器：`mv rd, rs`（实际上是 `addi rd, rs, 0`）
- `li` - 加载立即数：`li rd, imm`（实际上是 `lui` 和 `addi` 的组合）
- `beqz` - 为零则分支：`beqz rs, offset`（实际上是 `beq rs, zero, offset`）
- `bnez` - 非零则分支：`bnez rs, offset`（实际上是 `bne rs, zero, offset`）

## 指令使用频率分析

基于测试程序分析，以下指令使用频率最高：

1. `lw`, `sw` - 内存访问指令（最频繁）
2. `addi` - 立即数加法（地址计算常用）
3. `add` - 加法运算
4. `beq`, `bne`, `bge` - 条件分支（循环控制）
5. `jal`, `jalr` - 函数调用和返回
6. `lui`, `auipc` - 地址生成
7. `slli`, `srai` - 移位操作
8. `andi` - 逻辑运算
9. `ebreak` - 系统断点

## 实现优先级

基于使用频率和重要性，建议按以下优先级实现：

### 第一阶段（基础功能）
- 数据传输指令：`lw`, `sw`
- 算术指令：`add`, `addi`
- 分支指令：`beq`, `bne`, `bge`
- 跳转指令：`jal`, `jalr`
- 地址生成：`lui`, `auipc`
- 系统指令：`ebreak`

### 第二阶段（完整指令集）
- 逻辑指令：`andi`
- 移位指令：`slli`, `srai`

## 测试程序使用的特定模式

1. **0to100.exe**：简单的累加循环，主要使用 `lui`, `addi`, `lw`, `add`, `bne`, `ebreak`
2. **multiply.exe**：乘法函数实现，使用了更复杂的指令集，包括 `auipc`, `jal`, `sw`, `andi`, `slli`, `srai` 等
3. **vvadd.exe**：向量加法，使用了数组访问和循环结构，指令集与 multiply.exe 类似但更简单

这些测试程序覆盖了 RISC-V 指令集的核心功能，是实现一个基础 RISC-V CPU 的良好起点。