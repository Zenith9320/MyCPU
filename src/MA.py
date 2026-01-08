from assassyn.frontend import *

class MemoryAcess(Module):
    def __init__(self):
        super().__init__()

    @module.combinational
    def build(
        self,
        write_back: Module
    ):
        write_back.async_called()