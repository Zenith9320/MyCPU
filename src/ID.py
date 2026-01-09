from assassyn.frontend import *

class Decoder(Module):
    def __init__(self):
        super().__init__(
            ports={
                "pc": Port(Bits(32)),
            }
        )
    
    @module.combinational
    def build(
        self, 
        executor: Module,
    ):
        log("Decoder!")
        pc = self.pop_all_ports(True)
        executor.async_called(rs1 = Bits(32)(0), rs2 = Bits(32)(0), imm = Bits(32)(0))
