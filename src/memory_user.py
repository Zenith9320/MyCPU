from assassyn.frontend import *

class MemoryUser(Downstream):
    def __init__(self):
        super().__init__()
    
    @downstream.combinational
    def build(
        self,
        if_addr: Value,
        mem_addr: Value,
        ex_is_load: Value,
        ex_is_store: Value,
        wdata: Value,
        width: Value,
        sram: SRAM
    ):
        if_addr_val = if_addr.optional(Bits(32)(0))
        mem_addr_val = mem_addr.optional(Bits(32)(0))
        ex_is_load_val = ex_is_load.optional(Bits(1)(0))
        ex_is_store_val = ex_is_store.optional(Bits(1)(0))
        wdata_val = wdata.optional(Bits(32)(0))
        width_val = width.optional(Bits(3)(1))

        need_write = RegArray(Bits(1), 1, initializer=[0])
        write_addr = RegArray(Bits(32), 1, initializer=[0])
        write_data = RegArray(Bits(32), 1, initializer=[0])
        write_width = RegArray(Bits(3), 1, initializer=[0])

        need_refresh = ex_is_store_val & ~need_write[0]
        need_write[0] <= need_refresh.select(Bits(1)(1), Bits(1)(0))
        write_addr[0] <= need_refresh.select(mem_addr_val, Bits(32)(0))
        write_data[0] <= need_refresh.select(wdata_val, Bits(32)(0))
        write_width[0] <= need_refresh.select(width_val, Bits(3)(1))

        we = need_write[0]
        re = ~we
        final_mem_addr = we.select(write_addr[0], mem_addr_val)
        is_from_ex = ex_is_load_val | ex_is_store_val | we
        final_addr = is_from_ex.select(final_mem_addr, if_addr_val)

        final_wdata = we.select(write_data[0], Bits(32)(0))
        final_width = we.select(write_width[0], Bits(3)(1))
        # 默认为 1 防止 select1hot 报错

        shamt = final_mem_addr[0:1].concat(Bits(3)(0)).bitcast(UInt(5))
        raw_mask = final_width.select1hot(
            Bits(32)(0x000000FF),
            Bits(32)(0x0000FFFF),
            Bits(32)(0xFFFFFFFF),
        )
        shifted_mask = raw_mask << shamt
        shifted_data = final_wdata << shamt
        sram_wdata = (sram.dout[0] & (~shifted_mask)) | (shifted_data & shifted_mask)

        sram_trunc_addr = (final_addr >> Bits(32)(2))[0:15]

        log("MemoryUser: Addr=0x{:x} WData=0x{:x} WE={} RE={}", final_addr, sram_wdata, we, re)
        sram.build(
            addr = sram_trunc_addr,
            wdata = sram_wdata,
            we = we,
            re = re,
        )
