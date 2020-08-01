import copy
from ..variable import Variable

class Instruction:
    def __init__(self):
        self.variables = []
        self.params = {}
        self.insts = {}
        self.indent = 0

    def __repr__(self):
        space = " "*10*self.indent
        print_str = ""
        print_str += space + f"* {self.__class__.__name__}\n"
        print_str += space + "     parameters\n"
        for key, value in self.params.items():
            print_str += space + f"          {key}".ljust(20)
            print_str += ":".center(4)
            print_str += f"{value}".ljust(20) + "\n"
        print_str += "-"*100 + "\n"
        for key, value in self.insts.items():
            value.indent = self.indent + 1
            print_str += value.__repr__()
        return print_str

    def __str__(self):
        return self.__repr__()

    def _execute(self, port):
        pass

    def _get_variable(self):
        for inst in self.insts.values():
            inst._get_variable()
            self.variables += inst.variables
        for value in self.params.values():
            if isinstance(value, Variable):
                self.variables.append(value)

    def _fix_variable(self):
        self.tmp_params = {}
        for inst in self.insts.values():
            inst._fix_variable()
        for key, value in self.params.items():
            if isinstance(value, Variable):
                self.tmp_params[key] = value.value
            else:
                self.tmp_params[key] = value