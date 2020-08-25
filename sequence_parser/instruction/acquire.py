from .instruction import Instruction

class Acquire(Instruction):
    def __init__(self, duration):
        super().__init__()
        self.params = {"duration" : duration}

    def _execute(self, port):
        duration = self.tmp_params["duration"]
        self.measurement_window = (port.position, port.position + duration)
        port._time_step(duration)

    def _acquire(self, port):
        port.measurement_windows.append(self.measurement_window)