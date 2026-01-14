from assassyn.frontend import *

class MemoryUser(Downstream):
    def __init__(self):
        super().__init__()
    
    @module.combinational
    def build(
        self,
        if_addr: Value,
        mem_addr: Value,
        re: Value,
        we: Value,
        wdata: Value,
        width: Value,
        sram: SRAM
    ):
        if_addr_val = if_addr.optional(Bits(32)(0))
        mem_addr_val = mem_addr.optional(Bits(32)(0))
        re_val = re.optional(Bits(1)(0))
        we_val = we.optional(Bits(1)(0))
        wdata_val = wdata.optional(Bits(32)(0))
        width_val = width.optional(Bits(2)(0))

        # todo: implement memory access logic
