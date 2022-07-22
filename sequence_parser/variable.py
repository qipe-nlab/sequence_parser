import itertools
import numpy as np

class Variable:
    def __init__(self, name, value_array, unit):
        self.name = name
        self.value_array = np.asarray(value_array)
        self.unit = unit
        self.size = self.value_array.size

    def __repr__(self):
        return f"Variable ({self.name})"
        
    def __str__(self):
        return f"Variable ({self.name})"

    def _set_value(self, idx):
        self.value = self.value_array[idx]

class Variables:
    def __init__(self, variable_list=None):
        self.variable_list = []
        self.variable_name_list = []
        self.variable_size_list = []
        if variable_list is not None:
            for variable in variable_list:
                self.add(variable)
            self.compile()

    def add(self, variable):
        """Add new variable into self.variable_list
        Args:
            variable (list): [Variable1, Variable2, ...]
        """
        if isinstance(variable, Variable):
            variable = [variable]

        tmp_var_name_list = []
        tmp_var_size_list = []
        for var in variable:
            if var.name in self.variable_name_list:
                raise Exception(f"{var.name} is already used in the variable name")
            tmp_var_name_list.append(var.name)
            tmp_var_size_list.append(var.size)
        
        if len(set(tmp_var_size_list)) != 1:
            raise Exception("zipped variables must have same size")

        self.variable_name_list += tmp_var_name_list
        self.variable_size_list.append(tmp_var_size_list[0])
        self.variable_list.append(variable)

    def call(self, variables):
        """Combine the variable_list with the other Variables
        Args:
            variables (Variables): variables
        """
        for variable in variables.variable_list:
            self.add(variable)

    def compile(self):
        """Compile the variables
        
        """
        sweep_axis = [tuple(range(i)) for i in self.variable_size_list]
        sweep_index = list(itertools.product(*sweep_axis))

        self.update_command_list = []
        tmp_var = dict(zip(self.variable_name_list, [None]*len(self.variable_name_list)))
        for tmp_index in sweep_index:
            update_command = {}
            for variable, idx in zip(self.variable_list, tmp_index):
                for var in variable:
                    if tmp_var[var.name] != var.value_array[idx]:
                        tmp_var[var.name] = var.value_array[idx]
                        update_command[var.name] = idx
            self.update_command_list.append(update_command)
