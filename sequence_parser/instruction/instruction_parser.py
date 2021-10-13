import copy
from .pulse import Square, Gaussian, RaisedCos, FlatTop, Deriviative
from .command import VirtualZ, Delay, SetDetuning, ResetPhase
from .acquire import Acquire
from .trigger import Trigger
from .functional import Container, Union, Adjoint
from .align import _AddAlign, _DelAlign

def parse(obj):
    obj = copy.deepcopy(obj)
    setting = {
        "name" : obj.__class__.__name__,
        "params" : None,
        "insts" : {}
    }
    for key, inst in obj.insts.items():
        setting["insts"][key] = parse(inst)

    setting["params"] = obj.params
    return setting

def compose(setting):
    inputs = setting["params"]

    if len(setting["insts"]) == 1:
        inputs["pulse"] = compose(setting["insts"][0])
        
    elif len(setting["insts"]) > 1:
        inputs["inst_list"] = [compose(sub_setting) for sub_setting in setting["insts"].values()]

    obj = globals()[setting["name"]](**inputs)
    return obj