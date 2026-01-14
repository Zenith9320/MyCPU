from assassyn.frontend import *

class WriteBack(Module):
    def __init__(self):
        super().__init__(
            ports={
                "index": Port(Bits(5)),
                "data": Port(Bits(32)),
            }
        )

    @module.combinational
    def build(
        self,
        reg_file: RegArray,
    ):
        index, data = self.pop_all_ports(True)
        log(f"WB: Write data {data} to reg[{index}]")
        wb_bypass_value = data
        with Condition(index != Bits(5)(0)):
            reg_file[index] = data
        
        return index, wb_bypass_value
