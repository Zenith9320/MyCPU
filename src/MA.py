from assassyn.frontend import *

class MemoryAcess(Module):
    def __init__(self):
        super().__init__(
            ports={}
        )

    @module.combinational
    def build(
        self,
        write_back: Module
    ):
        log("MemoryAcess!")
        write_back.async_called()