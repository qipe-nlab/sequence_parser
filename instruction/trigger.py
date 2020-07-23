from .instruction import Instruction

class Trigger(Instruction):
    def __init__(self, align="left"):
        super().__init__()
        self.type = "Trigger"
        self.name = "Trigger"
        self.duration = 0
        self.align = align
        self.trigger_index = None
        self.input_params = {"align" : align}