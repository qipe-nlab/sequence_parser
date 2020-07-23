from .pulse import Square, Gaussian, RaisedCos, FlatTop, Deriviative, Union, Adjoint
from .command import VirtualZ, ShiftFrequency, Delay
from .acquire import Acquire
from .trigger import Trigger

instruction_list = [
    Square, Gaussian, RaisedCos, FlatTop, Deriviative, Union, Adjoint,
    VirtualZ, ShiftFrequency, Delay,
    Acquire,
    Trigger
]

instruction_dict = {}
for instruction in instruction_list:
    instruction_dict[instruction.__name__] = instruction