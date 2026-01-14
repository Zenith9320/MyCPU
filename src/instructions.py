from .utils import *

instruction_table = [
    # RInst
    ('add', OP_R_TYPE, 0x0, 0, ALUOp.ADD, Op1Type.RS1, Op2Type.RS2, MemOp.NONE,
     MemWidth.WORD, Bits(1)(0), IF_WB.YES, BranchType.NO_BRANCH),
    ('sub', OP_R_TYPE, 0x0, 1, ALUOp.SUB, Op1Type.RS1, Op2Type.RS2, MemOp.NONE,
     MemWidth.WORD, Bits(1)(0), IF_WB.YES, BranchType.NO_BRANCH),
    ('sll', OP_R_TYPE, 0x1, 0, ALUOp.SLL, Op1Type.RS1, Op2Type.RS2, MemOp.NONE,
     MemWidth.WORD, Bits(1)(0), IF_WB.YES, BranchType.NO_BRANCH),
    ('slt', OP_R_TYPE, 0x2, 0, ALUOp.SLT, Op1Type.RS1, Op2Type.RS2, MemOp.NONE,
     MemWidth.WORD, Bits(1)(0), IF_WB.YES, BranchType.NO_BRANCH),
    ('sltu', OP_R_TYPE, 0x3, 0, ALUOp.SLTU, Op1Type.RS1, Op2Type.RS2, MemOp.NONE,
     MemWidth.WORD, Bits(1)(0), IF_WB.YES, BranchType.NO_BRANCH),
    ('xor', OP_R_TYPE, 0x4, 0, ALUOp.XOR, Op1Type.RS1, Op2Type.RS2, MemOp.NONE,
     MemWidth.WORD, Bits(1)(0), IF_WB.YES, BranchType.NO_BRANCH),
    ('srl', OP_R_TYPE, 0x5, 0, ALUOp.SRL, Op1Type.RS1, Op2Type.RS2, MemOp.NONE,
     MemWidth.WORD, Bits(1)(0), IF_WB.YES, BranchType.NO_BRANCH),
    ('sra', OP_R_TYPE, 0x5, 1, ALUOp.SRA, Op1Type.RS1, Op2Type.RS2, MemOp.NONE,
     MemWidth.WORD, Bits(1)(0), IF_WB.YES, BranchType.NO_BRANCH),
    ('or', OP_R_TYPE, 0x6, 0, ALUOp.OR, Op1Type.RS1, Op2Type.RS2, MemOp.NONE,
     MemWidth.WORD, Bits(1)(0), IF_WB.YES, BranchType.NO_BRANCH),
    ('and', OP_R_TYPE, 0x7, 0, ALUOp.AND, Op1Type.RS1, Op2Type.RS2, MemOp.NONE,
     MemWidth.WORD, Bits(1)(0), IF_WB.YES, BranchType.NO_BRANCH),

    # IInst(ALU)
    ('addi', OP_I_TYPE, 0x0, None, ALUOp.ADD, Op1Type.RS1, Op2Type.IMM, MemOp.NONE,
     MemWidth.WORD, Bits(1)(0), IF_WB.YES, BranchType.NO_BRANCH),
    ('slti', OP_I_TYPE, 0x2, None, ALUOp.SLT, Op1Type.RS1, Op2Type.IMM, MemOp.NONE,
     MemWidth.WORD, Bits(1)(0), IF_WB.YES, BranchType.NO_BRANCH),
    ('sltiu', OP_I_TYPE, 0x3, None, ALUOp.SLTU, Op1Type.RS1, Op2Type.IMM, MemOp.NONE,
     MemWidth.WORD, Bits(1)(0), IF_WB.YES, BranchType.NO_BRANCH),
    ('xori', OP_I_TYPE, 0x4, None, ALUOp.XOR, Op1Type.RS1, Op2Type.IMM, MemOp.NONE,
     MemWidth.WORD, Bits(1)(0), IF_WB.YES, BranchType.NO_BRANCH),
    ('ori', OP_I_TYPE, 0x6, None, ALUOp.OR, Op1Type.RS1, Op2Type.IMM, MemOp.NONE,
     MemWidth.WORD, Bits(1)(0), IF_WB.YES, BranchType.NO_BRANCH),
    ('andi', OP_I_TYPE, 0x7, None, ALUOp.AND, Op1Type.RS1, Op2Type.IMM, MemOp.NONE,
     MemWidth.WORD, Bits(1)(0), IF_WB.YES, BranchType.NO_BRANCH),
    ('slli', OP_I_TYPE, 0x1, None, ALUOp.SLL, Op1Type.RS1, Op2Type.IMM, MemOp.NONE,
     MemWidth.WORD, Bits(1)(0), IF_WB.YES, BranchType.NO_BRANCH),
    ('srli', OP_I_TYPE, 0x5, 0, ALUOp.SRL, Op1Type.RS1, Op2Type.IMM, MemOp.NONE,
     MemWidth.WORD, Bits(1)(0), IF_WB.YES, BranchType.NO_BRANCH),
    ('srai', OP_I_TYPE, 0x5, 1, ALUOp.SRA, Op1Type.RS1, Op2Type.IMM, MemOp.NONE,
     MemWidth.WORD, Bits(1)(0), IF_WB.YES, BranchType.NO_BRANCH),

    # load instructions
    ('lb', OP_LOAD, 0x0, None, ALUOp.ADD, Op1Type.RS1, Op2Type.IMM, MemOp.LOAD,
     MemWidth.BYTE, MemSign.SIGNED, IF_WB.YES, BranchType.NO_BRANCH),
    ('lh', OP_LOAD, 0x1, None, ALUOp.ADD, Op1Type.RS1, Op2Type.IMM, MemOp.LOAD,
     MemWidth.HALF, MemSign.SIGNED, IF_WB.YES, BranchType.NO_BRANCH),
    ('lw', OP_LOAD, 0x2, None, ALUOp.ADD, Op1Type.RS1, Op2Type.IMM, MemOp.LOAD,
     MemWidth.WORD, MemSign.SIGNED, IF_WB.YES, BranchType.NO_BRANCH),
    ('lbu', OP_LOAD, 0x4, None, ALUOp.ADD, Op1Type.RS1, Op2Type.IMM, MemOp.LOAD,
     MemWidth.BYTE, MemSign.UNSIGNED, IF_WB.YES, BranchType.NO_BRANCH),
    ('lhu', OP_LOAD, 0x5, None, ALUOp.ADD, Op1Type.RS1, Op2Type.IMM, MemOp.LOAD,
     MemWidth.HALF, MemSign.UNSIGNED, IF_WB.YES, BranchType.NO_BRANCH),

    # SInst
    ('sb', OP_STORE, 0x0, None, ALUOp.ADD, Op1Type.RS1, Op2Type.IMM, MemOp.STORE,
     MemWidth.BYTE, Bits(1)(0), IF_WB.NO, BranchType.NO_BRANCH),
    ('sh', OP_STORE, 0x1, None, ALUOp.ADD, Op1Type.RS1, Op2Type.IMM, MemOp.STORE,
     MemWidth.HALF, Bits(1)(0), IF_WB.NO, BranchType.NO_BRANCH),
    ('sw', OP_STORE, 0x2, None, ALUOp.ADD, Op1Type.RS1, Op2Type.IMM, MemOp.STORE,
     MemWidth.WORD, Bits(1)(0), IF_WB.NO, BranchType.NO_BRANCH),

    # BInst
    ('beq', OP_BRANCH, 0x0, None, ALUOp.SUB, Op1Type.RS1, Op2Type.RS2, MemOp.NONE,
     MemWidth.WORD, Bits(1)(0), IF_WB.NO, BranchType.BEQ),
    ('bne', OP_BRANCH, 0x1, None, ALUOp.SUB, Op1Type.RS1, Op2Type.RS2, MemOp.NONE,
     MemWidth.WORD, Bits(1)(0), IF_WB.NO, BranchType.BNE),
    ('blt', OP_BRANCH, 0x4, None, ALUOp.SLT, Op1Type.RS1, Op2Type.RS2, MemOp.NONE,
     MemWidth.WORD, Bits(1)(0), IF_WB.NO, BranchType.BLT),
    ('bge', OP_BRANCH, 0x5, None, ALUOp.SLT, Op1Type.RS1, Op2Type.RS2, MemOp.NONE,
     MemWidth.WORD, Bits(1)(0), IF_WB.NO, BranchType.BGE),
    ('bltu', OP_BRANCH, 0x6, None, ALUOp.SLTU, Op1Type.RS1, Op2Type.RS2, MemOp.NONE,
     MemWidth.WORD, Bits(1)(0), IF_WB.NO, BranchType.BLTU),
    ('bgeu', OP_BRANCH, 0x7, None, ALUOp.SLTU, Op1Type.RS1, Op2Type.RS2, MemOp.NONE,
     MemWidth.WORD, Bits(1)(0), IF_WB.NO, BranchType.BGEU),

    # JAL
    ('jal', OP_JAL, None, None, ALUOp.ADD, Op1Type.PC, Op2Type.CONST_4, MemOp.NONE,
     MemWidth.WORD, Bits(1)(0), IF_WB.YES, BranchType.JAL),

    # JALR
    ('jalr', OP_JALR, 0x0, None, ALUOp.ADD, Op1Type.PC, Op2Type.CONST_4, MemOp.NONE,
     MemWidth.WORD, Bits(1)(0), IF_WB.YES, BranchType.JALR),

    # LUI
    ('lui', OP_LUI, None, None, ALUOp.ADD, Op1Type.ZERO, Op2Type.IMM, MemOp.NONE,
     MemWidth.WORD, Bits(1)(0), IF_WB.YES, BranchType.NO_BRANCH),

    # AUIPC
    ('auipc', OP_AUIPC, None, None, ALUOp.ADD, Op1Type.PC, Op2Type.IMM, MemOp.NONE,
     MemWidth.WORD, Bits(1)(0), IF_WB.YES, BranchType.NO_BRANCH),

    # 系统级指令
    ('ecall', OP_SYSTEM, 0x0, 0, ALUOp.SYS, Op1Type.RS1, Op2Type.IMM, MemOp.NONE,
     MemWidth.WORD, Bits(1)(0), IF_WB.NO, BranchType.NO_BRANCH),
    ('ebreak', OP_SYSTEM, 0x0, 0, ALUOp.SYS, Op1Type.RS1, Op2Type.IMM, MemOp.NONE,
     MemWidth.WORD, Bits(1)(0), IF_WB.NO, BranchType.NO_BRANCH),
]