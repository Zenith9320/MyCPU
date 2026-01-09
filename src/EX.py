from assassyn.frontend import *

class Executor(Module):
    def __init__(self):
        super().__init__(
            ports={
                "rs1": Port(Bits(32)),
                "rs2": Port(Bits(32)),
                "imm": Port(Bits(32))
            }
        )

    @module.combinational
    def build(
        self,
        memory_access: Module
    ):
        log("Executor!")
        rs1, rs2, imm = self.pop_all_ports(True)
        memory_access.async_called(alu_result = Bits(32)(0))
