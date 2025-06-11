import bpy
from . import operators, panels

modules_to_register = [operators, panels]

def register():
    for module in modules_to_register:
        for cls in module.CLASS_LIST:
            bpy.utils.register_class(cls)

def unregister():
    # 以相反顺序注销
    for module in reversed(modules_to_register):
        for cls in reversed(module.CLASS_LIST):
            bpy.utils.unregister_class(cls)