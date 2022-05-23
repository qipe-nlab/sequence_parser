import copy
from .pulse import *
from .command import *
from .acquire import *
from .trigger import *
from .functional import *
from .align import *

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