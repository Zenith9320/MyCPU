from assassyn.frontend import *
from utils import MemOp, MemWidth, MemSign, MemCtrlSignals

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

        with Condition(mem_op == MemOp.NONE):
            log("Memory Access: NONE")
        with Condition(mem_op == MemOp.LOAD):
            log("Memory Access: LOAD")
        with Condition(mem_op == MemOp.STORE):
            log("Memory Access: STORE")
        
        with Condition(mem_width == MemWidth.BYTE):
            log(" - Width: BYTE")
        with Condition(mem_width == MemWidth.HALF):
            log(" - Width: HALF")
        with Condition(mem_width == MemWidth.WORD):
            log(" - Width: WORD")

        with Condition(mem_sign == MemSign.SIGNED):
            log(" - Sign: SIGNED")
        with Condition(mem_sign == MemSign.UNSIGNED):
            log(" - Sign: UNSIGNED")

        raw_data = sram_dout[0].bitcast(Bits(32))

        half_sel = alu_result[1:1].select(raw_data[16:31], raw_data[0:15])



        write_back.async_called(index = Bits(5)(0), data = Bits(32)(0))