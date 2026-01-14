from assassyn.frontend import *
from utils import BranchType, ExCtrlSignals,MemOp, MemCtrlSignals, WbCtrlSignals

class Executor(Module):
    def __init__(self):
        super().__init__(
            ports={
                "ctrl": Port(ExCtrlSignals),
                "pc": Port(Bits(32)),
                "rs1": Port(Bits(32)),
                "rs2": Port(Bits(32)),
                "imm": Port(Bits(32))
            }
        )

    @module.combinational
    def build(
        self,
        memory_access: Module,
        branch_target: RegArray
    ):
        ctrl, pc, rs1, rs2, imm = self.pop_all_ports(True)
        log(f"Input: pc={pc}, rs1={rs1}, rs2={rs2}, imm={imm}")

        alu_op1 = ctrl.op1_type.select1hot(
            rs1, pc, Bits(32)(0)
        )
        alu_op2 = ctrl.op2_type.select1hot(
            rs2, imm, Bits(32)(4)
        )

        op1_signed = alu_op1.bitcase(Int(32))
        op2_signed = alu_op2.bitcase(Int(32))

        add_res = op1_signed + op2_signed.bitcase(Int(32))
        sub_res = op1_signed - op2_signed.bitcase(Int(32))
        and_res = alu_op1 & alu_op2
        or_res = alu_op1 | alu_op2
        xor_res = alu_op1 ^ alu_op2
        sll_res = alu_op1 << alu_op2[0:4]
        srl_res = alu_op1 >> alu_op2[0:4]
        sra_res = (op1_signed >> alu_op2[0:4]).bitcase(Bits(32))
        slt_res = (op1_signed < op2_signed).bitcase(Bits(32))
        sltu_res = (alu_op1 < alu_op2).bitcase(Bits(32))

        alu_res = ctrl.alu_op.select1hot(
            add_res,
            sub_res,
            sll_res,
            slt_res,
            sltu_res,
            xor_res,
            srl_res,
            sra_res,
            or_res,
            and_res,
            alu_op2,
        )
    
        # jal 和 jalr 计算跳转地址
        is_jalr = ctrl.branch_type == BranchType.JALR
        is_jal = ctrl.branch_type == BranchType.JAL
        target_base = is_jalr.select(rs1, pc)

        imm_signed = imm.bitcase(Int(32))
        target_base_signed = target_base.bitcase(Int(32))
        raw_calc_target = (target_base_signed + imm_signed).bitcase(Bits(32))
        calc_target = is_jalr.select(
            concat(raw_calc_target[0:31], Bits(1)(0)),
            raw_calc_target
        )

        # branch
        is_taken = Bits(1)(0)
        is_branch = ctrl.branch_type != BranchType.NONE

        is_eq = alu_res == Bits(32)(0)
        is_lt = alu_res[0:0] == Bits(1)(1)

        is_taken_eq = (ctrl.BranchType.BEQ == ctrl.branch_type) & is_eq
        is_taken_ne = (ctrl.BranchType.BNE == ctrl.branch_type) & (~is_eq)
        is_taken_lt = (ctrl.BranchType.BLT == ctrl.branch_type) & is_lt
        is_taken_ge = (ctrl.BranchType.BGE == ctrl.branch_type) & (~is_lt)
        is_taken_ltu = (ctrl.BranchType.BLTU == ctrl.branch_type) & is_lt
        is_taken_geu = (ctrl.BranchType.BGEU == ctrl.branch_type) & (~is_lt)

        is_taken = is_branch & (
            is_taken_eq |
            is_taken_ne |
            is_taken_lt |
            is_taken_ge |
            is_taken_ltu |
            is_taken_geu |
            is_jal |
            is_jalr
        )

        is_flush = branch_target[0] != Bits(32)(0)
        next_pc = is_flush.select(
            Bits(32)(0),
            is_branch.select(
                is_taken.select(
                    calc_target,
                    pc.bitcase(UInt(32)) + Bits(32)(4)
                ),
                ctrl.predicted_next_pc
            )
        )

        branch_miss = next_pc != ctrl.predicted_next_pc
        branch_target[0] = branch_miss.select(
            next_pc,
            Bits(32)(0)
        )

        rd = is_flush.select(
            Bits(5)(0),
            ctrl.rd
        )
        is_halt = is_flush.select(
            Bits(1)(0),
            ctrl.is_halt
        )
        mem_opcode = is_flush.select(
            MemOp.NONE,
            ctrl.mem_op
        )

        mem_ctrl = MemCtrlSignals.bundle(
            mem_opcode = mem_opcode,
            mem_width = ctrl.mem_width,
            mem_sign = ctrl.mem_sign,
            rd = rd,
            is_halt = is_halt
        )

        memory_access.async_called(ctrl = mem_ctrl, alu_result = alu_res)

        is_store = mem_opcode == MemOp.STORE
        is_load = mem_opcode == MemOp.LOAD
        mem_width = ctrl.mem_width

        return rd, alu_res, is_store, is_load, mem_width, rs2
