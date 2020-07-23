from .instruction import Instruction

class Acquire(Instruction):
    def __init__(self, duration):
        super().__init__()
        self.type = "Acquire"
        self.name = "Acquire"
        self.duration = duration
        self.input_params = {"duration" : duration}

    def _execute(self, port):
        self.measurement_window = (port.position, port.position + self.duration)
        port.position += self.duration