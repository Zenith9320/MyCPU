from assassyn.frontend import *
from utils import Rs1Type, Rs2Type

class Bypass(Downstream):
    def __init__(self):
        super().__init__()
    
    @module.combinational
    def build(
        self,
        rs1_addr: Value,
        rs2_addr: Value,
        ex_dest_addr: Value,
        ex_is_load: Value,
        ex_is_store: Value,
        mem_dest_addr: Value,
        mem_is_store: Value,
        wb_dest_addr: Value,
    ):
        rs1_addr_val = rs1_addr.optional(Bits(5)(0))
        rs2_addr_val = rs2_addr.optional(Bits(5)(0))
        ex_dest_addr_val = ex_dest_addr.optional(Bits(5)(0))
        ex_is_load_val = ex_is_load.optional(Bits(1)(0))
        ex_is_store_val = ex_is_store.optional(Bits(1)(0))
        mem_dest_addr_val = mem_dest_addr.optional(Bits(5)(0))
        mem_is_store_val = mem_is_store.optional(Bits(1)(0))
        wb_dest_addr_val = wb_dest_addr.optional(Bits(5)(0))

        log(f"Bypass: rs1={rs1_addr_val}, rs2={rs2_addr_val}, ex_dest={ex_dest_addr_val}, ex_is_load={ex_is_load_val}, ex_is_store={ex_is_store_val}, mem_dest={mem_dest_addr_val}, wb_dest={wb_dest_addr_val}")

        rs1_is_zero = rs1_addr_val == Bits(5)(0)
        rs2_is_zero = rs2_addr_val == Bits(5)(0)

        # 可能的 stall 情况
        # ex load, ex store, 本周期会占用 memory, 故而要 stall
        # mem store 本周期也要占用 memory, 也要 stall

        is_stall = ex_is_store_val | ex_is_load_val | mem_is_store_val

        rs1_wb_type = ((rs1_addr_val == wb_dest_addr_val) & (~rs1_is_zero)).select(Rs1Type.WB, Rs1Type.NONE)
        rs1_mem_type = ((rs1_addr_val == mem_dest_addr_val) & (~rs1_is_zero)).select(Rs1Type.MEM, rs1_wb_type)
        rs1_ex_type = ((rs1_addr_val == ex_dest_addr_val) & (~rs1_is_zero)).select(Rs1Type.EX, rs1_mem_type)

        rs2_wb_type = ((rs2_addr_val == wb_dest_addr_val) & (~rs2_is_zero)).select(Rs2Type.WB, Rs2Type.NONE)
        rs2_mem_type = ((rs2_addr_val == mem_dest_addr_val) & (~rs2_is_zero)).select(Rs2Type.MEM, rs2_wb_type)
        rs2_ex_type = ((rs2_addr_val == ex_dest_addr_val) & (~rs2_is_zero)).select(Rs2Type.EX, rs2_mem_type)

        log(f"Bypass Result: rs1_type={rs1_ex_type}, rs2_type={rs2_ex_type}, is_stall={is_stall}")

        return rs1_ex_type, rs2_ex_type, is_stall
