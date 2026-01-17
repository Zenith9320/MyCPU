from assassyn.frontend import *
from .utils import *
from .debug import debug_log

class WriteBack(Module):
    def __init__(self):
        super().__init__(
            ports={
                "ctrl": Port(WbCtrlSignals),
                "data": Port(Bits(32)),
            }
        )

    @module.combinational
    def build(
        self,
        reg_file: RegArray,
    ):
        ctrl, data = self.pop_all_ports(True)
        index = ctrl.rd
        wb_bypass_value = data
        with Condition(index != Bits(5)(0)):
            debug_log("WB: Write x{} <= 0x{:x}", index, data)
            reg_file[index] = data
        with Condition(ctrl.is_halt == Bits(1)(1)):
            debug_log("Halt signal received, finishing simulation.")
            for i in range(32):
                log("Register x{} = 0x{:x}", Bits(5)(i), reg_file[i])
            finish()

        return index, wb_bypass_value
