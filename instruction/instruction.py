class Instruction:
    def __init__(self):
        self.name = None
        self.type = None
        self.duration = None
        self.input_params = {}

    def __repr__(self):
        return f"{self.__class__.__name__}({self.input_params})"
        
    def __str__(self):
        return f"{self.__class__.__name__}({self.input_params})"

    def _execute(self, port):
        pass