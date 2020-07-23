from .__init__ import instruction_dict

def generate_setting_from_instruction(instruction):
    setting = {
        "type" : instruction.type,
        "name" : instruction.name,
        "input_params" : instruction.input_params
    }
    return setting

def generate_instruction_from_setting(setting):
    inst_name = setting["name"]
    input_params = setting["input_params"]
    # if inst_name in ["FlatTop", "Deriviative"]:
    #     compiled_input_params = generate_instruction_from_setting(input_params["pulse_setting"])
    #     input_params["pulse_setting"] = compiled_input_params
    # elif inst_name in ["Union", "Adjoint"]:
    #     compiled_input_params = []
    #     for pulse_setting in input_params["pulse_setting_list"]:
    #         compiled_input_params.append(generate_instruction_from_setting(pulse_setting))
    #     input_params["pulse_setting_list"] = compiled_input_params
    Instruction = instruction_dict[inst_name]
    instruction = Instruction(**input_params)
    return instruction