from instruction.command import Command

"""
User can specify the order of instructions within the range of the with syntax
(This feature is not supported in the current version)

Usage example:

    class Sequence:
        def ...

        def align(self, port, align):
            return _AlignManager(self, port, align)

    seq = Sequence()
    seq.add(hoge, port)
    with seq.align(port, align="left"):
        seq.add(hoge, port)
    seq.add(hoge, port)
"""

class _AlignManager:
    def __init__(self, sequence, port, align):
        self.sequence = sequence
        self.port = port
        self.align = align

    def __enter__(self):
        self.sequence.add(_AddAlign(self.align), self.port)

    def __exit__(self, exception_type, exception_value, traceback):
        self.sequence.add(_DelAlign(), self.port)

class _AddAlign(Command):
    def __init__(self, align):
        super().__init__()
        self.name = "AddAlign"
        self.duration = 0
        self.align = align

    def _execute(self, port):
        port.align_array.append(self.align)

class _DelAlign(Command):
    def __init__(self):
        super().__init__()
        self.name = "DelAlign"
        self.duration = 0

    def _execute(self, port):
        last_align = port.align_array.pop()