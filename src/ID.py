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
        icache_out: RegArray,
        executor: Module
    ):
        pc = self.pop_all_ports(True)
        # do sth with icache(sram)
        # so that next tick you get the correct inst
        # decode it, and then call EX
        executor.async_called()
