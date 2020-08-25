from .instruction import Instruction
from .pulse import Pulse
from .acquire import Acquire

class Container(Instruction):
    def __init__(self, inst=None):
        super().__init__()
        if inst is not None:
            self.params = {"inst" : inst}

    def _fix_variable(self):
        self.inst = self.params["inst"].value
        self.inst._fix_variable()

class Functional(Instruction):
    def __init__(self):
        super().__init__()

    def _execute(self, port):
        pass

    def _write(self, port):
        pass

    def _acquire(self, port):
        pass

class Union(Functional):
    def __init__(
        self,
        inst_list,
    ):
        super().__init__()
        self.params = {}
        self.insts = dict(zip(range(len(inst_list)), inst_list))

    def _execute(self, port):
        position = port.position
        duration = []
        for inst in self.insts.values():
            inst._execute(port)
            duration.append(port.position - position)
            port.position = position
        port.position += max(duration)

    def _write(self, port):
        for inst in self.insts.values():
            if isinstance(inst, (Pulse, Functional)):
                inst._write(port)

    def _acquire(self, port):
        for inst in self.insts.values():
            if isinstance(inst, (Acquire, Functional)):
                inst._acquire(port)

class Adjoint(Functional):
    def __init__(
        self,
        inst_list,
    ):
        super().__init__()
        self.params = {}
        self.insts = dict(zip(range(len(inst_list)), inst_list))

    def _execute(self, port):
        for inst in self.insts.values():
            inst._execute(port)

    def _write(self, port):
        for inst in self.insts.values():
            if isinstance(inst, Pulse):
                inst._write(port)

    def _acquire(self, port):
        for inst in self.insts.values():
            if isinstance(inst, Acquire):
                inst._acquire(port)