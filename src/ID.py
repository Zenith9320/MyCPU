from assassyn.frontend import *
from .instructions import *
from .debug import debug_log

# 从指令中提取立即数
def get_imm(inst):
    sign = inst[31:31]
    pad_bits_20 = sign.select(Bits(20)(0xFFFFF), Bits(20)(0))
    pad_bits_19 = sign.select(Bits(19)(0x7FFFF), Bits(19)(0))
    pad_bits_11 = sign.select(Bits(11)(0x7FF), Bits(11)(0))
    imm_i = concat(pad_bits_20, inst[20:31])
    imm_s = concat(pad_bits_20, inst[25:31], inst[7:11])
    imm_b = concat(pad_bits_19, inst[31:31], inst[7:7], inst[25:30], inst[8:11], Bits(1)(0))
    imm_u = concat(inst[12:31], Bits(12)(0))
    imm_j = concat(pad_bits_11, inst[31:31], inst[12:19], inst[20:20], inst[21:30], Bits(1)(0))
    return imm_i, imm_s, imm_b, imm_u, imm_j

class Decoder(Module):
    def __init__(self):
        super().__init__(
            ports={
                "pc": Port(Bits(32)),
                "next_pc": Port(Bits(32)),
                "is_stall": Port(Bits(1)),
            }
        )
    
    @module.combinational
    def build(self, icache_dout: Array, reg_file: Array):
        debug_log("Decoder!")
        pc_addr, next_pc_addr, is_stall = self.pop_all_ports(False)
        icache_instruction = icache_dout[0].bitcast(Bits(32))
        last_inst_reg = RegArray(Bits(32), 1, initializer=[0])
        #真正要处理的指令，默认先保持不动
        instruction = (is_stall == Bits(1)(0)).select(icache_instruction, last_inst_reg[0])
        #如果需要修改instruction，即不bubble，就需要修改last_inst_reg和instruction
        with Condition(is_stall == Bits(1)(0)):
            last_inst_reg[0] <= icache_instruction
        
        #第一条指令PC不是有效地址，输出是0，但是这不是合法RISC-V指令，需要转成NOP：addi x0, x0, 0
        instruction = (instruction == Bits(32)(0)).select(Bits(32)(0x00000013), instruction)
        
        debug_log("ID: Fetching Instruction=0x{:x} at PC=0x{:x}", instruction, pc_addr)

        is_halt_inst = ((instruction == Bits(32)(0x00000073)) | (instruction == Bits(32)(0x00100073)) | (instruction == Bits(32)(0xFE000FA3)))

        with Condition(is_halt_inst == Bits(1)(1)):
            debug_log("ID : HALT INSTRUCTION")

        opcode = instruction[0:6]
        rd = instruction[7:11]
        funct3 = instruction[12:14]
        rs1 = instruction[15:19]
        rs2 = instruction[20:24]
        bit30 = instruction[30:30]
        imm_i, imm_s, imm_b, imm_u, imm_j = get_imm(instruction)

        match = Bits(1)(0)

        alu_op = Bits(12)(0)
        imm_type = Bits(6)(0)
        op1_type = Bits(3)(0)
        op2_type = Bits(3)(0)
        branch_type = Bits(9)(0)
        mem_op = Bits(3)(0)
        mem_width = Bits(3)(0)
        mem_sign = Bits(1)(0)
        if_wb = Bits(2)(0)
        imm = Bits(32)(0)

        for inst_entry in instruction_table:
            match = opcode == inst_entry[1]
            if inst_entry[2] is not None:
                match &= funct3 == Bits(3)(inst_entry[2])
            if inst_entry[3] is not None:
                match &= bit30 == Bits(1)(inst_entry[3])
            alu_op |= match.select(inst_entry[4], Bits(12)(0))
            imm_type |= match.select(inst_entry[-1], Bits(6)(0))
            op1_type |= match.select(inst_entry[5], Bits(3)(0))
            op2_type |= match.select(inst_entry[6], Bits(3)(0))
            branch_type |= match.select(inst_entry[-2], Bits(9)(0))
            mem_op |= match.select(inst_entry[7], Bits(3)(0))
            mem_width |= match.select(inst_entry[8], Bits(3)(0))
            mem_sign |= match.select(inst_entry[9], Bits(1)(0))
            if_wb |= match.select(inst_entry[-3], Bits(2)(0))

        # with Condition(imm_type == Bits(6)(0)):
        #     log("ID: Unknown instruction 0x{:x} at PC=0x{:x}, treat as NOP", instruction, pc_addr)
        #     finish()
        
        alu_op = (alu_op == Bits(12)(0)).select(ALUOp.NOP, alu_op)
        op1_type = (op1_type == Bits(3)(0)).select(Op1Type.RS1, op1_type)
        op2_type = (op2_type == Bits(3)(0)).select(Op2Type.RS2, op2_type)
        imm_type = (imm_type == Bits(6)(0)).select(Bits(6)(1), imm_type)
        mem_width = (mem_width == Bits(3)(0)).select(MemWidth.WORD, mem_width)

        imm = imm_type.select1hot(Bits(32)(0), imm_i, imm_s, imm_b, imm_u, imm_j)
        rs1_data = reg_file[rs1]
        rs2_data = reg_file[rs2]

        debug_log("ID: rs1=x{}, rs1_data=0x{:x}, rs2=x{}, rs2_data=0x{:x}, if_wb={}", rs1, rs1_data, rs2, rs2_data, if_wb)

        rd2 = (if_wb == IF_WB.YES).select(rd, Bits(5)(0))
        
        debug_log("rd={}", rd2)

        ctrl = DecoderSignals.bundle(
            alu_op = alu_op,
            branch_type = branch_type,
            op1_type = op1_type,
            op2_type = op2_type,
            cur_pc = pc_addr,
            predicted_pc = next_pc_addr,
            mem_op = mem_op,
            mem_width = mem_width,
            mem_sign = mem_sign,
            rd = rd2,
            is_halt = is_halt_inst,
            rs1_data = rs1_data,
            rs2_data = rs2_data,
            imm = imm,
        )

        return ctrl, rs1, rs2

class DecoderImpl(Downstream):
    def __init__(self):
        super().__init__()
    
    @downstream.combinational
    def build(
        self,
        ctrl: Record,
        executor: Module,
        rs1_ex_type: Bits(4),
        rs2_ex_type: Bits(4),
        if_stall: Bits(1),
        ex_bypass: Value,           # EX-MEM 旁路寄存器的数据（上条指令结果）
        mem_bypass: Value,          # MEM-WB 旁路寄存器的数据 (上上条指令结果)
        wb_bypass: Value,           # WB 旁路寄存器的数据 (当前写回数据)
        branch_target_reg: Array,
    ):
        if_flush = branch_target_reg[0] != Bits(32)(0)
        if_nop = if_flush | if_stall

        rd = if_nop.select(Bits(5)(0), ctrl.rd)
        if_halt = if_nop.select(Bits(1)(0), ctrl.is_halt)
        mem_op = if_nop.select(MemOp.NONE, ctrl.mem_op)
        alu_op = if_nop.select(ALUOp.NOP, ctrl.alu_op)
        branch_type = if_nop.select(BranchType.NONE, ctrl.branch_type)

        ex_bypass_val = ex_bypass.optional(Bits(32)(0))
        mem_bypass_val = mem_bypass.optional(Bits(32)(0))
        wb_bypass_val = wb_bypass.optional(Bits(32)(0))

        fwd_from_ex_to_mem = ex_bypass_val
        fwd_from_mem_to_wb = mem_bypass_val
        fwd_after_wb = wb_bypass_val

        rs1_data = rs1_ex_type.select1hot(
            ctrl.rs1_data, fwd_from_ex_to_mem, fwd_from_mem_to_wb, fwd_after_wb
        )

        rs2_data = rs2_ex_type.select1hot(
            ctrl.rs2_data, fwd_from_ex_to_mem, fwd_from_mem_to_wb, fwd_after_wb
        )

        debug_log("DecoderImpl: rs_ex_type={}, rs1_data=0x{:x}, rs_2_ex_type={}, rs2_data=0x{:x}, rd={}", rs1_ex_type, rs1_data, rs2_ex_type, rs2_data, rd)

        ctrl_signals = ExCtrlSignals.bundle(
            alu_op = alu_op,
            branch_type = branch_type,
            op1_type = ctrl.op1_type,
            op2_type = ctrl.op2_type,
            predicted_pc = ctrl.predicted_pc,
            mem_op = mem_op,
            mem_width = ctrl.mem_width,
            mem_sign = ctrl.mem_sign,
            rd = rd,
            is_halt = ctrl.is_halt,
            rs1_data = rs1_data,
            rs2_data = rs2_data,
        )

        executor.async_called(
            ctrl = ctrl_signals,
            pc = ctrl.cur_pc,
            rs1 = rs1_data,
            rs2 = rs2_data,
            imm = ctrl.imm,
        )