# RIISV-V 指令集介绍

本文档介绍 RIISV-V 指令集的格式和作用。RIISV-V 是基于 RISC-V 架构的指令集变体，支持标准的 RISC-V 指令。指令按类型分组，每条指令包括其格式描述和功能说明。

## 指令格式概述

RIISV-V 指令遵循 RISC-V 的标准格式：

- **R-Type**: 用于寄存器-寄存器操作。格式：`opcode(7) | rd(5) | funct3(3) | rs1(5) | rs2(5) | funct7(7)`
- **I-Type**: 用于立即数操作和加载。格式：`opcode(7) | rd(5) | funct3(3) | rs1(5) | imm[11:0](12)`
- **S-Type**: 用于存储。格式：`opcode(7) | imm[4:0](5) | funct3(3) | rs1(5) | rs2(5) | imm[11:5](7)`
- **B-Type**: 用于分支。格式：`opcode(7) | imm[11](1) | imm[4:1](4) | funct3(3) | rs1(5) | rs2(5) | imm[10:5](6) | imm[12](1)`
- **U-Type**: 用于大立即数。格式：`opcode(7) | rd(5) | imm[31:12](20)`
- **J-Type**: 用于跳转。格式：`opcode(7) | rd(5) | imm[19:12](8) | imm[11](1) | imm[10:1](10) | imm[20](1)`

## R-Type 指令 (寄存器-寄存器操作)

### add
- **格式**: R-Type (opcode: 0110011, funct3: 000, funct7: 0000000)
- **作用**: 将 rs1 和 rs2 的值相加，结果写入 rd。`rd = rs1 + rs2`

### sub
- **格式**: R-Type (opcode: 0110011, funct3: 000, funct7: 0100000)
- **作用**: 将 rs1 减去 rs2 的值，结果写入 rd。`rd = rs1 - rs2`

### sll
- **格式**: R-Type (opcode: 0110011, funct3: 001, funct7: 0000000)
- **作用**: 将 rs1 左移 rs2 的低 5 位，结果写入 rd。`rd = rs1 << rs2[4:0]`

### slt
- **格式**: R-Type (opcode: 0110011, funct3: 010, funct7: 0000000)
- **作用**: 如果 rs1 < rs2 (有符号比较)，则 rd = 1，否则 rd = 0。`rd = (rs1 < rs2) ? 1 : 0`

### sltu
- **格式**: R-Type (opcode: 0110011, funct3: 011, funct7: 0000000)
- **作用**: 如果 rs1 < rs2 (无符号比较)，则 rd = 1，否则 rd = 0。`rd = (rs1 < rs2) ? 1 : 0`

### xor
- **格式**: R-Type (opcode: 0110011, funct3: 100, funct7: 0000000)
- **作用**: 将 rs1 和 rs2 进行异或运算，结果写入 rd。`rd = rs1 ^ rs2`

### srl
- **格式**: R-Type (opcode: 0110011, funct3: 101, funct7: 0000000)
- **作用**: 将 rs1 右移 rs2 的低 5 位 (逻辑移位)，结果写入 rd。`rd = rs1 >> rs2[4:0]`

### sra
- **格式**: R-Type (opcode: 0110011, funct3: 101, funct7: 0100000)
- **作用**: 将 rs1 右移 rs2 的低 5 位 (算术移位)，结果写入 rd。`rd = rs1 >>> rs2[4:0]`

### or
- **格式**: R-Type (opcode: 0110011, funct3: 110, funct7: 0000000)
- **作用**: 将 rs1 和 rs2 进行或运算，结果写入 rd。`rd = rs1 | rs2`

### and
- **格式**: R-Type (opcode: 0110011, funct3: 111, funct7: 0000000)
- **作用**: 将 rs1 和 rs2 进行与运算，结果写入 rd。`rd = rs1 & rs2`

## I-Type 指令 (立即数操作)

### addi
- **格式**: I-Type (opcode: 0010011, funct3: 000)
- **作用**: 将 rs1 和 12 位立即数相加，结果写入 rd。`rd = rs1 + imm`

### slti
- **格式**: I-Type (opcode: 0010011, funct3: 010)
- **作用**: 如果 rs1 < imm (有符号比较)，则 rd = 1，否则 rd = 0。`rd = (rs1 < imm) ? 1 : 0`

### sltiu
- **格式**: I-Type (opcode: 0010011, funct3: 011)
- **作用**: 如果 rs1 < imm (无符号比较)，则 rd = 1，否则 rd = 0。`rd = (rs1 < imm) ? 1 : 0`

### xori
- **格式**: I-Type (opcode: 0010011, funct3: 100)
- **作用**: 将 rs1 和立即数进行异或运算，结果写入 rd。`rd = rs1 ^ imm`

### ori
- **格式**: I-Type (opcode: 0010011, funct3: 110)
- **作用**: 将 rs1 和立即数进行或运算，结果写入 rd。`rd = rs1 | imm`

### andi
- **格式**: I-Type (opcode: 0010011, funct3: 111)
- **作用**: 将 rs1 和立即数进行与运算，结果写入 rd。`rd = rs1 & imm`

### slli
- **格式**: I-Type (opcode: 0010011, funct3: 001)
- **作用**: 将 rs1 左移立即数的低 5 位，结果写入 rd。`rd = rs1 << imm[4:0]`

### srli
- **格式**: I-Type (opcode: 0010011, funct3: 101, imm[11:5]: 0000000)
- **作用**: 将 rs1 右移立即数的低 5 位 (逻辑移位)，结果写入 rd。`rd = rs1 >> imm[4:0]`

### srai
- **格式**: I-Type (opcode: 0010011, funct3: 101, imm[11:5]: 0100000)
- **作用**: 将 rs1 右移立即数的低 5 位 (算术移位)，结果写入 rd。`rd = rs1 >>> imm[4:0]`

## 加载指令 (Load)

### lb
- **格式**: I-Type (opcode: 0000011, funct3: 000)
- **作用**: 从内存地址 rs1 + imm 加载 1 字节 (有符号扩展)，写入 rd。`rd = mem[rs1 + imm] (signed byte)`

### lh
- **格式**: I-Type (opcode: 0000011, funct3: 001)
- **作用**: 从内存地址 rs1 + imm 加载 2 字节 (有符号扩展)，写入 rd。`rd = mem[rs1 + imm] (signed halfword)`

### lw
- **格式**: I-Type (opcode: 0000011, funct3: 010)
- **作用**: 从内存地址 rs1 + imm 加载 4 字节 (有符号扩展)，写入 rd。`rd = mem[rs1 + imm] (signed word)`

### lbu
- **格式**: I-Type (opcode: 0000011, funct3: 100)
- **作用**: 从内存地址 rs1 + imm 加载 1 字节 (无符号扩展)，写入 rd。`rd = mem[rs1 + imm] (unsigned byte)`

### lhu
- **格式**: I-Type (opcode: 0000011, funct3: 101)
- **作用**: 从内存地址 rs1 + imm 加载 2 字节 (无符号扩展)，写入 rd。`rd = mem[rs1 + imm] (unsigned halfword)`

## 存储指令 (Store)

### sb
- **格式**: S-Type (opcode: 0100011, funct3: 000)
- **作用**: 将 rs2 的低 8 位存储到内存地址 rs1 + imm。`mem[rs1 + imm] = rs2[7:0]`

### sh
- **格式**: S-Type (opcode: 0100011, funct3: 001)
- **作用**: 将 rs2 的低 16 位存储到内存地址 rs1 + imm。`mem[rs1 + imm] = rs2[15:0]`

### sw
- **格式**: S-Type (opcode: 0100011, funct3: 010)
- **作用**: 将 rs2 的 32 位存储到内存地址 rs1 + imm。`mem[rs1 + imm] = rs2`

## 分支指令 (Branch)

### beq
- **格式**: B-Type (opcode: 1100011, funct3: 000)
- **作用**: 如果 rs1 == rs2，则跳转到 PC + imm。`if (rs1 == rs2) PC = PC + imm`

### bne
- **格式**: B-Type (opcode: 1100011, funct3: 001)
- **作用**: 如果 rs1 != rs2，则跳转到 PC + imm。`if (rs1 != rs2) PC = PC + imm`

### blt
- **格式**: B-Type (opcode: 1100011, funct3: 100)
- **作用**: 如果 rs1 < rs2 (有符号)，则跳转到 PC + imm。`if (rs1 < rs2) PC = PC + imm`

### bge
- **格式**: B-Type (opcode: 1100011, funct3: 101)
- **作用**: 如果 rs1 >= rs2 (有符号)，则跳转到 PC + imm。`if (rs1 >= rs2) PC = PC + imm`

### bltu
- **格式**: B-Type (opcode: 1100011, funct3: 110)
- **作用**: 如果 rs1 < rs2 (无符号)，则跳转到 PC + imm。`if (rs1 < rs2) PC = PC + imm`

### bgeu
- **格式**: B-Type (opcode: 1100011, funct3: 111)
- **作用**: 如果 rs1 >= rs2 (无符号)，则跳转到 PC + imm。`if (rs1 >= rs2) PC = PC + imm`

## 跳转指令 (Jump)

### jal
- **格式**: J-Type (opcode: 1101111)
- **作用**: 无条件跳转到 PC + imm，并将 PC + 4 写入 rd。`rd = PC + 4; PC = PC + imm`

### jalr
- **格式**: I-Type (opcode: 1100111, funct3: 000)
- **作用**: 无条件跳转到 rs1 + imm，并将 PC + 4 写入 rd。`rd = PC + 4; PC = rs1 + imm`

## U-Type 指令 (大立即数)

### lui
- **格式**: U-Type (opcode: 0110111)
- **作用**: 将 20 位立即数左移 12 位加载到 rd 的高位，低位清零。`rd = imm << 12`

### auipc
- **格式**: U-Type (opcode: 0010111)
- **作用**: 将 PC + (imm << 12) 写入 rd。`rd = PC + (imm << 12)`

## 系统指令 (System)

### ecall
- **格式**: I-Type (opcode: 1110011, funct3: 000, imm: 000000000000)
- **作用**: 环境调用，触发系统调用或异常。

### ebreak
- **格式**: I-Type (opcode: 1110011, funct3: 000, imm: 000000000001)
- **作用**: 断点指令，用于调试。