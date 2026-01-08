from assassyn.frontend import *

class Executor(Module):
    def __init__(self):
        super().__init__()

    @module.combinational
    def build(
        self,
        memory_access: Module
    ):
        memory_access.async_called()
