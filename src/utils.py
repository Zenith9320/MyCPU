from assassyn.frontend import *

class Rs1Type(Enum):
    NONE: Bits(4)(0b0001)
    EX: Bits(4)(0b0010)
    MEM: Bits(4)(0b0100)
    WB: Bits(4)(0b1000)

class Rs2Type(Enum):
    NONE: Bits(4)(0b0001)
    EX: Bits(4)(0b0010)
    MEM: Bits(4)(0b0100)
    WB: Bits(4)(0b1000)