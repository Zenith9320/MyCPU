from assassyn.frontend import *
from enum import Enum

# opcode 常量
# decode 阶段可以直接使用

OP_R_TYPE = Bits(7)(0b0110011)
OP_I_TYPE = Bits(7)(0b0010011)
OP_LOAD = Bits(7)(0b0000011)
OP_STORE = Bits(7)(0b0100011)
OP_BRANCH = Bits(7)(0b1100011)
OP_JAL = Bits(7)(0b1101111)
OP_JALR = Bits(7)(0b1100111)
OP_LUI = Bits(7)(0b0110111)
OP_AUIPC = Bits(7)(0b0010111)
OP_SYSTEM = Bits(7)(0b1110011)

class ImmType:
    R = Bits(6)(0b000001)
    I = Bits(6)(0b000010)
    S = Bits(6)(0b000100)
    B = Bits(6)(0b001000)
    U = Bits(6)(0b010000)
    J = Bits(6)(0b100000)

# ex 阶段

class ALUOp:
    ADD = Bits(12)(0b000000000001)
    SUB = Bits(12)(0b000000000010)
    SLL = Bits(12)(0b000000000100)
    SLT = Bits(12)(0b000000001000)
    SLTU = Bits(12)(0b000000010000)
    XOR = Bits(12)(0b000000100000)
    SRL = Bits(12)(0b000001000000)
    SRA = Bits(12)(0b000010000000)
    OR = Bits(12)(0b000100000000)
    AND = Bits(12)(0b001000000000)
    SYS = Bits(12)(0b010000000000)
    NOP = Bits(12)(0b100000000000)

class BranchType:
    NONE = Bits(9)(0b000000001)
    BEQ = Bits(9)(0b000000010)
    BNE = Bits(9)(0b000000100)
    BLT = Bits(9)(0b000001000)
    BGE = Bits(9)(0b000010000)
    BLTU = Bits(9)(0b000100000)
    BGEU = Bits(9)(0b001000000)
    JAL = Bits(9)(0b010000000)
    JALR = Bits(9)(0b100000000)

class Op1Type:
    RS1 = Bits(3)(0b001)
    PC = Bits(3)(0b010)
    ZERO = Bits(3)(0b100)

class Op2Type:
    RS2 = Bits(3)(0b001)
    IMM = Bits(3)(0b010)
    FOUR = Bits(3)(0b100)

# mem 阶段

class MemOp:
    NONE = Bits(3)(0b001)
    LOAD = Bits(3)(0b010)
    STORE = Bits(3)(0b100)

class MemWidth:
    BYTE = Bits(3)(0b001)
    HALF = Bits(3)(0b010)
    WORD = Bits(3)(0b100)

class MemSign:
    SIGNED = Bits(2)(0b01)
    UNSIGNED = Bits(2)(0b10)

WbCtrlSignals = Record(
    rd = Bits(5),
    is_halt = Bits(1),
)

MemCtrlSignals = Record(
    mem_op = Bits(3),
    mem_width = Bits(3),
    mem_sign = Bits(2),
    rd = Bits(5),
    is_halt = Bits(1),
)

ExCtrlSignals = Record(
    alu_op = Bits(12),
    branch_type = Bits(9),
    op1_type = Bits(3),
    op2_type = Bits(3),
    predicted_pc = Bits(32),
    mem_op = Bits(3),
    mem_width = Bits(3),
    mem_sign = Bits(2),
    rd = Bits(5),
    is_halt = Bits(1),
)

# bypass 阶段

class Rs1Type:
    NONE = Bits(4)(0b0001)
    EX = Bits(4)(0b0010)
    MEM = Bits(4)(0b0100)
    WB = Bits(4)(0b1000)

class Rs2Type:
    NONE = Bits(4)(0b0001)
    EX = Bits(4)(0b0010)
    MEM = Bits(4)(0b0100)
    WB = Bits(4)(0b1000)

# writeback 阶段
class IF_WB:
    YES = Bits(2)(0b01)
    No = Bits(2)(0b10)