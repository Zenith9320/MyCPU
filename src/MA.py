from assassyn.frontend import *

class MemoryAcess(Module):
    def __init__(self):
        super().__init__(
            ports={
                "alu_result": Port(Bits(32)),
            }
        )

    @module.combinational
    def build(
        self,
        write_back: Module
    ):
        log("MemoryAcess!")
        alu_result = self.pop_all_ports(True)
        write_back.async_called(index = Bits(5)(0), data = Bits(32)(0))