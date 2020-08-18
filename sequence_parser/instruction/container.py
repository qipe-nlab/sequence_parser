from .instruction import Instruction
from .pulse.pulse import Pulse

class Container(Instruction):
    def __init__(self, inst):
        super().__init__()
        self.params = {"inst" : inst}

    def _fix_variable(self):
        self.inst = self.params["inst"].value
        self.inst._fix_variable()

        self._execute = self.inst._execute
        if isinstance(self.inst, Pulse):
            self._write = self.inst._write