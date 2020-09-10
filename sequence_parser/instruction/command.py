import numpy as np
from .instruction import Instruction

class Command(Instruction):
    def __init__(self):
        super().__init__()

class Delay(Command):
    def __init__(self, duration):
        super().__init__()
        self.params = {"duration" : duration}

    def _execute(self, port):
        duration = self.tmp_params["duration"]
        port._time_step(duration)

class VirtualZ(Command):
    def __init__(self, phase):
        super().__init__()
        self.params = {"phase" : phase}

    def _execute(self, port):
        phase = self.tmp_params["phase"]
        port.phase -= phase

class ShiftFrequency(Command):
    def __init__(self, detuning):
        super().__init__()
        self.params = {"detuning" : detuning}

    def _execute(self, port):
        detuning = self.tmp_params["detuning"]
        port.detuning = detuning

class SetAbsolutePhase(Command):
    def __init__(self, phase):
        super().__init__()
        self.params = {"phase" : phase}

    def _execute(self, port):
        phase = self.tmp_params["phase"]
        charp_frequency = port.detuning
        port.phase = - phase - 2*np.pi*charp_frequency*port.position