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
        log("WriteBack!")
        index, data = self.pop_all_ports(True)
        reg_file[index] = data