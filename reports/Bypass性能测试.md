# CPU Bypass性能报告

## 1. 基本信息

**CPU架构**：五级流水(IF->ID->EX->MA->WB) 

**语言使用**：Assassyn

**CPU支持指令集**：RISC-V RV32IM

**CPU支持指令**：

| 指令类型 | 指令名称                                                     |
| -------- | ------------------------------------------------------------ |
| 算术指令 | add, sub, sll, slt, sltu, xor, srl, sra, or, and             |
| 立即数指令 | addi, slti, sltiu, xori, ori, andi, slli, srli, srai, lui, auipc         |
| 访存指令 | lb, lh, lw, lbu, lhu, sb, sh, sw                             |
| 分支指令 | beq, bne, blt, bge, bltu, bgeu                               |
| 跳转指令 | jal, jalr                                                    |
| 系统指令 | ecall, ebreak

**bypass机制**：

支持以下三种bypass机制：

*EX Bypass*：EX 阶段的计算结果直接传入 ID

*MA Bypass*：MA 阶段load的结果直接传入 ID

*WB Bypass*：WB 阶段alu的结果直接传入 ID

三个Bypassing都将 Value 传入 DecoderImpl 来根据bypass.py的结果选择数据的来源，然后把具体数据传入 Executor

## 2. 测试数据

### (1) 0to100.exe

计算 0 到 100 的和，结果为 5050

### (2) vvadd.exe

计算向量之和，结果为一个数组

### (3) multiply.exe

计算向量乘积

## 3. 计算方式

性能提升周期数 = ( EX Bypass 使用次数 * 3 + MA Bypass 使用次数 * 2 + WB Bypass 使用次数 * 1 )

## 4. 测试结果
| 工作负载  | 有 Bypass 周期数 | 无 Bypass 周期数 | 性能提升 | 提升百分比 |
|--------- |-----------------|-----------------|-----------|------------|
| 0to100   | **2056**         | 4208           | **2152**  | **51.14%** |
| multiply | **xx**          | xx              | **xx**    | **xx.xx%** |
| vvadd    | **xx**          | xx              | **xx**    | **xx.xx%** |

## 5.具体数据

### (1) 0to100
| 对象                        | 数值     |
|-----------------------------|---------|
| 总执行周期数                 | 2056    |
| EX Bypass 使用次数           | 513     |
| MA Bypass 使用次数           | 204     |
| WB Bypass 使用次数           | 205     |
| 总 Bypass 使用次数           | 922     |
| 无bypass周期数               | 4208    |
| 性能提升周期数               | 2152     |
| 性能提升百分比               | 51.14%  |


### (2) vvadd
| 对象                        | 数值     |
|-----------------------------|---------|
| 总执行周期数                 | 7553    |
| EX Bypass 使用次数           | 3006    |
| MA Bypass 使用次数           | 1205    |
| WB Bypass 使用次数           | 204     |
| 总 Bypass 使用次数           | 4415    |
| 无bypass周期数               | 19185   |
| 性能提升周期数               | 11632   |
| 性能提升百分比               | 60.63%  |

### (3) multiply
| 对象                        | 数值     |
|-----------------------------|---------|
| 总执行周期数                 | 429     |
| EX Bypass 使用次数           | 165    |
| MA Bypass 使用次数           | 64     |
| WB Bypass 使用次数           | 13     |
| 总 Bypass 使用次数           | 242    |
| 无bypass周期数               | 1494   |
| 性能提升周期数               | 1065    |
| 性能提升百分比               | 71.29%  |

## 6. 总结

Bypass作为五级流水的一种常用优化方式，能够有效降低计算相对密集的指令的周期数，平均能够减少占据无优化情况下总周期数60%左右的bubble，但是上述计算采用的是上界，并不是实际的bubble数量，实际优化周期数可能会略小，但是Bypass优化的效果是显著的