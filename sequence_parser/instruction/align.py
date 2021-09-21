from .command import Command, Delay

class _AlignManager:
    def __init__(self, sequence, port, mode):
        self.sequence = sequence
        self.port = port
        self.mode = mode

    def __enter__(self):
        self.sequence.add(_AddAlign(self.mode), self.port)

    def __exit__(self, exception_type, exception_value, traceback):
        self.sequence.add(_DelAlign(), self.port)

class _AddAlign(Command):
    def __init__(self, mode):
        super().__init__()
        self.mode = mode
        self.params = {"mode" : mode}

    def _execute(self, port):
        align_mode = (self.mode, [])
        port.align_modes.append(align_mode)

class _DelAlign(Command):
    def __init__(self):
        super().__init__()
        self.params = {}

    def _execute(self, port):
        mode, dur_list = port.align_modes.pop()

        if port.align_modes[-1][0] == "sequential":
            if mode == "sequential":
                port.align_modes[-1][1].append(sum(dur_list))

            if mode == "left":
                port.position += max(dur_list)
                port.align_modes[-1][1].append(max(dur_list))

        if port.align_modes[-1][0] == "left":
            if mode == "sequential":
                port.position -= sum(dur_list)
                port.align_modes[-1][1].append(sum(dur_list))

            if mode == "left":
                port.align_modes[-1][1].append(max(dur_list))
