from assassyn.frontend import *
from .utils import *

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
            log("WB: Write x{} <= 0x{:x}", index, data)
            reg_file[index] = data
        with Condition(ctrl.is_halt == Bits(1)(1)):
            log("WB: Halt signal received, finishing simulation.")
            finish()

        return index, wb_bypass_value
