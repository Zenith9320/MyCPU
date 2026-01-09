from assassyn.frontend import *

class Fetcher(Module):
    def __init__(self):
        super().__init__(ports={})
    
    @module.combinational
    def build(
        self, 
        decoder: module,
    ):
        pc = RegArray(UInt(32), 1, initializer=[0])
        log("Fetcher!")
        (pc & self)[0] <= pc[0] + UInt(32)(4)
        decoder.async_called(pc = pc[0].bitcast(Bits(32)))
