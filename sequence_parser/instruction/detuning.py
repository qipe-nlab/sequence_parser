import numpy as np
from .command import Command

class _DetuningManager:
    global start_position
    start_position = None
    
    def __init__(self, sequence, port, detuning):
        self.sequence = sequence
        self.port = port
        self.detuning = detuning

    def __enter__(self):
        self.sequence.add(_AddDetuning(self.detuning), self.port)

    def __exit__(self, exception_type, exception_value, traceback):
        self.sequence.add(_DelDetuning(self.detuning), self.port)

class _AddDetuning(Command):
    def __init__(self, detuning):
        super().__init__()
        self.params = {"detuning" : detuning}

    def _execute(self, port):
        global start_position
        start_position = port.position
        detuning = self.tmp_params["detuning"]
        port.phase -= 2*np.pi*detuning*start_position
        port.detuning = detuning

class _DelDetuning(Command):
    def __init__(self, detuning):
        super().__init__()
        self.params = {"detuning" : detuning}

    def _execute(self, port):
        global start_position
        end_position = port.position 
        detuning = self.tmp_params["detuning"]
        port.phase += 2*np.pi*detuning*end_position
        port.detuning = 0
