import numpy as np
from .instruction import Instruction

class Command(Instruction):
    def __init__(self):
        super().__init__()
        self.type = "Command"

class Delay(Command):
    def __init__(self, duration):
        super().__init__()
        self.name = "Delay"
        self.duration = duration
        self.input_params = {"duration" : duration}

    def _execute(self, port):
        port.position += self.duration

class VirtualZ(Command):
    def __init__(self, phase):
        super().__init__()
        self.name = "VirtualZ"
        self.duration = 0
        self.phase = phase
        self.input_params = {"phase" : phase}

    def _execute(self, port):
        port.phase -= self.phase

class ShiftFrequency(Command):
    def __init__(self, detuning):
        super().__init__()
        self.name = "ShiftFrequency"
        self.duration = 0
        self.detuning = detuning
        self.input_params = {"detuning" : detuning}

    def _execute(self, port):
        port.detuning = self.detuning

class SetAbsolutePhase(Command):
    def __init__(self, phase):
        super().__init__()
        self.name = "SetAbsolutePhase"
        self.duration = 0
        self.phase = phase
        self.input_params = {"phase" : phase}

    def _execute(self, port):
        charp_frequency = port.SIDEBAND_FREQ
        port.phase = self.phase - 2*np.pi*charp_frequency*port.position
