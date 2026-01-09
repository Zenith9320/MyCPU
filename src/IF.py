from assassyn.frontend import *

class Fetcher(Module):
    def __init__(self):
        super().__init__(
            ports={}
        )
    
    @module.combinational
    def build(self):
        pc = RegArray(UInt(32), 1, initializer=[0])
        return pc
    
class FetcherImpl(Downstream):
    def __init__(self):
        super().__init__()

    @downstream.combinational
    def build(
        self,
        pc_reg: RegArray,
        decoder: Module,
    ):
        log("Fetcher!")
        pc_reg[0] <= pc_reg[0] + UInt(32)(4)
        log("{}", pc_reg[0])
        decoder.async_called(pc = Bits(32)(0))