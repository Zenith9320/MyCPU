from .utils import *

instruction_table = [
    # RInst
    ('add', OP_R_TYPE, 0x0, 0, ALUOp.ADD, Op1Type.RS1, Op2Type.RS2, MemOp.NONE,
     MemWidth.WORD, Bits(1)(0), IF_WB.YES, BranchType.NONE, ImmType.R),
    ('sub', OP_R_TYPE, 0x0, 1, ALUOp.SUB, Op1Type.RS1, Op2Type.RS2, MemOp.NONE,
     MemWidth.WORD, Bits(1)(0), IF_WB.YES, BranchType.NONE, ImmType.R),
    ('sll', OP_R_TYPE, 0x1, 0, ALUOp.SLL, Op1Type.RS1, Op2Type.RS2, MemOp.NONE,
     MemWidth.WORD, Bits(1)(0), IF_WB.YES, BranchType.NONE, ImmType.R),
    ('slt', OP_R_TYPE, 0x2, 0, ALUOp.SLT, Op1Type.RS1, Op2Type.RS2, MemOp.NONE,
     MemWidth.WORD, Bits(1)(0), IF_WB.YES, BranchType.NONE, ImmType.R),
    ('sltu', OP_R_TYPE, 0x3, 0, ALUOp.SLTU, Op1Type.RS1, Op2Type.RS2, MemOp.NONE,
     MemWidth.WORD, Bits(1)(0), IF_WB.YES, BranchType.NONE, ImmType.R),
    ('xor', OP_R_TYPE, 0x4, 0, ALUOp.XOR, Op1Type.RS1, Op2Type.RS2, MemOp.NONE,
     MemWidth.WORD, Bits(1)(0), IF_WB.YES, BranchType.NONE, ImmType.R),
    ('srl', OP_R_TYPE, 0x5, 0, ALUOp.SRL, Op1Type.RS1, Op2Type.RS2, MemOp.NONE,
     MemWidth.WORD, Bits(1)(0), IF_WB.YES, BranchType.NONE, ImmType.R),
    ('sra', OP_R_TYPE, 0x5, 1, ALUOp.SRA, Op1Type.RS1, Op2Type.RS2, MemOp.NONE,
     MemWidth.WORD, Bits(1)(0), IF_WB.YES, BranchType.NONE, ImmType.R),
    ('or', OP_R_TYPE, 0x6, 0, ALUOp.OR, Op1Type.RS1, Op2Type.RS2, MemOp.NONE,
     MemWidth.WORD, Bits(1)(0), IF_WB.YES, BranchType.NONE, ImmType.R),
    ('and', OP_R_TYPE, 0x7, 0, ALUOp.AND, Op1Type.RS1, Op2Type.RS2, MemOp.NONE,
     MemWidth.WORD, Bits(1)(0), IF_WB.YES, BranchType.NONE, ImmType.R),

    # IInst(ALU)
    ('addi', OP_I_TYPE, 0x0, None, ALUOp.ADD, Op1Type.RS1, Op2Type.IMM, MemOp.NONE,
     MemWidth.WORD, Bits(1)(0), IF_WB.YES, BranchType.NONE, ImmType.I),
    ('slti', OP_I_TYPE, 0x2, None, ALUOp.SLT, Op1Type.RS1, Op2Type.IMM, MemOp.NONE,
     MemWidth.WORD, Bits(1)(0), IF_WB.YES, BranchType.NONE, ImmType.I),
    ('sltiu', OP_I_TYPE, 0x3, None, ALUOp.SLTU, Op1Type.RS1, Op2Type.IMM, MemOp.NONE,
     MemWidth.WORD, Bits(1)(0), IF_WB.YES, BranchType.NONE, ImmType.I),
    ('xori', OP_I_TYPE, 0x4, None, ALUOp.XOR, Op1Type.RS1, Op2Type.IMM, MemOp.NONE,
     MemWidth.WORD, Bits(1)(0), IF_WB.YES, BranchType.NONE, ImmType.I),
    ('ori', OP_I_TYPE, 0x6, None, ALUOp.OR, Op1Type.RS1, Op2Type.IMM, MemOp.NONE,
     MemWidth.WORD, Bits(1)(0), IF_WB.YES, BranchType.NONE, ImmType.I),
    ('andi', OP_I_TYPE, 0x7, None, ALUOp.AND, Op1Type.RS1, Op2Type.IMM, MemOp.NONE,
     MemWidth.WORD, Bits(1)(0), IF_WB.YES, BranchType.NONE, ImmType.I),
    ('slli', OP_I_TYPE, 0x1, None, ALUOp.SLL, Op1Type.RS1, Op2Type.IMM, MemOp.NONE,
     MemWidth.WORD, Bits(1)(0), IF_WB.YES, BranchType.NONE, ImmType.I),
    ('srli', OP_I_TYPE, 0x5, 0, ALUOp.SRL, Op1Type.RS1, Op2Type.IMM, MemOp.NONE,
     MemWidth.WORD, Bits(1)(0), IF_WB.YES, BranchType.NONE, ImmType.I),
    ('srai', OP_I_TYPE, 0x5, 1, ALUOp.SRA, Op1Type.RS1, Op2Type.IMM, MemOp.NONE,
     MemWidth.WORD, Bits(1)(0), IF_WB.YES, BranchType.NONE, ImmType.I),

    # load instructions
    ('lb', OP_LOAD, 0x0, None, ALUOp.ADD, Op1Type.RS1, Op2Type.IMM, MemOp.LOAD,
     MemWidth.BYTE, MemSign.SIGNED, IF_WB.YES, BranchType.NONE, ImmType.I),
    ('lh', OP_LOAD, 0x1, None, ALUOp.ADD, Op1Type.RS1, Op2Type.IMM, MemOp.LOAD,
     MemWidth.HALF, MemSign.SIGNED, IF_WB.YES, BranchType.NONE, ImmType.I),
    ('lw', OP_LOAD, 0x2, None, ALUOp.ADD, Op1Type.RS1, Op2Type.IMM, MemOp.LOAD,
     MemWidth.WORD, MemSign.SIGNED, IF_WB.YES, BranchType.NONE, ImmType.I),
    ('lbu', OP_LOAD, 0x4, None, ALUOp.ADD, Op1Type.RS1, Op2Type.IMM, MemOp.LOAD,
     MemWidth.BYTE, MemSign.UNSIGNED, IF_WB.YES, BranchType.NONE, ImmType.I),
    ('lhu', OP_LOAD, 0x5, None, ALUOp.ADD, Op1Type.RS1, Op2Type.IMM, MemOp.LOAD,
     MemWidth.HALF, MemSign.UNSIGNED, IF_WB.YES, BranchType.NONE, ImmType.I),

    # SInst
    ('sb', OP_STORE, 0x0, None, ALUOp.ADD, Op1Type.RS1, Op2Type.IMM, MemOp.STORE,
     MemWidth.BYTE, Bits(1)(0), IF_WB.NO, BranchType.NONE, ImmType.S),
    ('sh', OP_STORE, 0x1, None, ALUOp.ADD, Op1Type.RS1, Op2Type.IMM, MemOp.STORE,
     MemWidth.HALF, Bits(1)(0), IF_WB.NO, BranchType.NONE, ImmType.S),
    ('sw', OP_STORE, 0x2, None, ALUOp.ADD, Op1Type.RS1, Op2Type.IMM, MemOp.STORE,
     MemWidth.WORD, Bits(1)(0), IF_WB.NO, BranchType.NONE, ImmType.S),

    # BInst
    ('beq', OP_BRANCH, 0x0, None, ALUOp.SUB, Op1Type.RS1, Op2Type.RS2, MemOp.NONE,
     MemWidth.WORD, Bits(1)(0), IF_WB.NO, BranchType.BEQ, ImmType.B),
    ('bne', OP_BRANCH, 0x1, None, ALUOp.SUB, Op1Type.RS1, Op2Type.RS2, MemOp.NONE,
     MemWidth.WORD, Bits(1)(0), IF_WB.NO, BranchType.BNE, ImmType.B),
    ('blt', OP_BRANCH, 0x4, None, ALUOp.SLT, Op1Type.RS1, Op2Type.RS2, MemOp.NONE,
     MemWidth.WORD, Bits(1)(0), IF_WB.NO, BranchType.BLT, ImmType.B),
    ('bge', OP_BRANCH, 0x5, None, ALUOp.SLT, Op1Type.RS1, Op2Type.RS2, MemOp.NONE,
     MemWidth.WORD, Bits(1)(0), IF_WB.NO, BranchType.BGE, ImmType.B),
    ('bltu', OP_BRANCH, 0x6, None, ALUOp.SLTU, Op1Type.RS1, Op2Type.RS2, MemOp.NONE,
     MemWidth.WORD, Bits(1)(0), IF_WB.NO, BranchType.BLTU, ImmType.B),
    ('bgeu', OP_BRANCH, 0x7, None, ALUOp.SLTU, Op1Type.RS1, Op2Type.RS2, MemOp.NONE,
     MemWidth.WORD, Bits(1)(0), IF_WB.NO, BranchType.BGEU, ImmType.B),

    # JAL
    ('jal', OP_JAL, None, None, ALUOp.ADD, Op1Type.PC, Op2Type.FOUR, MemOp.NONE,
     MemWidth.WORD, Bits(1)(0), IF_WB.YES, BranchType.JAL, ImmType.J),

    # JALR
    ('jalr', OP_JALR, 0x0, None, ALUOp.ADD, Op1Type.PC, Op2Type.FOUR, MemOp.NONE,
     MemWidth.WORD, Bits(1)(0), IF_WB.YES, BranchType.JALR, ImmType.I),

    # LUI
    ('lui', OP_LUI, None, None, ALUOp.ADD, Op1Type.ZERO, Op2Type.IMM, MemOp.NONE,
     MemWidth.WORD, Bits(1)(0), IF_WB.YES, BranchType.NONE, ImmType.U),

    # AUIPC
    ('auipc', OP_AUIPC, None, None, ALUOp.ADD, Op1Type.PC, Op2Type.IMM, MemOp.NONE,
     MemWidth.WORD, Bits(1)(0), IF_WB.YES, BranchType.NONE, ImmType.U),

    # 系统级指令
    ('ecall', OP_SYSTEM, 0x0, 0, ALUOp.SYS, Op1Type.RS1, Op2Type.IMM, MemOp.NONE,
     MemWidth.WORD, Bits(1)(0), IF_WB.NO, BranchType.NONE, ImmType.I),
    ('ebreak', OP_SYSTEM, 0x0, 0, ALUOp.SYS, Op1Type.RS1, Op2Type.IMM, MemOp.NONE,
     MemWidth.WORD, Bits(1)(0), IF_WB.NO, BranchType.NONE, ImmType.I),
]