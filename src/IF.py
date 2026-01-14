from assassyn.frontend import *
from .utils import *

class Fetcher(Module):
    def __init__(self):
        super().__init__(ports={})
    
    @module.combinational
    def build(self):
        pc_reg = RegArray(UInt(32), 1, initializer=[0])
        last_pc_reg = RegArray(UInt(32), 1, initializer=[0])
        return pc_reg, last_pc_reg

class Fetcher(DownStream):
    def __init__(self):
        super().__init__()

    @downstream.combinational
    def build(
        self,
        pc_reg : Array,             #存储pc的寄存器
        last_pc_reg : Array,        #存储上一个周期pc的寄存器
        decoder : Module,           #async_call的下一级模块
        is_stall : Value,           #决定是否保持当前状态的变量
        branch_target_reg : Array,  #存储可能存在的跳转指令的目标pc位置
    ):
        valid_is_stall = is_stall.optional(Bits(1)(0))

        with Condition(valid_is_stall == Bits(1)(1)):
            log("Stall in IF")
        
        if valid_is_stall == True:
            current_pc_addr = last_pc_reg[0]
        else:
            current_pc_addr = pc_reg[0]
        
        #如果EX或者MA阶段得到了跳转指令的目标位置，就需要flush
        branch_target = branch_target_reg[0]
        if_flush = (branch_target != Bits(32)(0))
        
        if if_flush == True:
            current_pc_addr = branch_target
            log("IF: Flush to 0x{:x}", current_pc_addr)
        
        



