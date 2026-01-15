from assassyn.frontend import *
from .utils import *

class MemoryAcess(Module):
    def __init__(self):
        super().__init__(
            ports={
                "ctrl": Port(MemCtrlSignals),
                "alu_result": Port(Bits(32)),
            }
        )

    @module.combinational
    def build(
        self,
        write_back: Module,
        sram_dout: RegArray
    ):
        ctrl, alu_result = self.pop_all_ports(True)
        mem_op = ctrl.mem_op
        mem_width = ctrl.mem_width
        mem_sign = ctrl.mem_sign

        raw_data = sram_dout[0].bitcast(Bits(32))

        half_sel = alu_result[1:1].select(raw_data[16:31], raw_data[0:15])
        byte_sel = alu_result[0:0].select(half_sel[8:15], half_sel[0:7])

        pad_bit_8 = mem_sign.select(Bits(1)(0), byte_sel[7:7])
        pad_bit_16 = mem_sign.select(Bits(1)(0), half_sel[15:15])
        
        padding_8 = pad_bit_8.select(Bits(24)(0xFFFFFF), Bits(24)(0x00000000))
        padding_16 = pad_bit_16.select(Bits(16)(0xFFFF), Bits(16)(0x0000))

        byte_extended = concat(padding_8, byte_sel)
        half_extended = concat(padding_16, half_sel)

        load_res = mem_width.select1hot(
            byte_extended,
            half_extended,
            raw_data
        )

        is_load = mem_op == MemOp.LOAD
        is_store = mem_op == MemOp.STORE
        final_data = is_load.select(load_res, alu_result)

        wb_ctrl = WbCtrlSignals.bundle(
            rd = ctrl.rd,
            is_halt = ctrl.is_halt,
        )

        write_back.async_called(ctrl = wb_ctrl, data = final_data)

        return ctrl.rd, final_data, is_store