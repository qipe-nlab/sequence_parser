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

class SetDetuning(Command):
    def __init__(self, detuning):
        super().__init__()
        self.params = {"detuning" : detuning}

    def _execute(self, port):
        detuning = self.tmp_params["detuning"]
        port.detuning = detuning

class ResetPhase(Command):
    """Reset the accumulated phase.
    The current time will be used as the phase origin for the following pulses.
    """
    def __init__(self, phase=0):
        super().__init__()
        self.params = {"phase" : phase}

    def _execute(self, port):
        phase = self.tmp_params["phase"]
        if_freq = port.if_freq + port.detuning
        port.phase = - phase - 2*np.pi*if_freq*port.position