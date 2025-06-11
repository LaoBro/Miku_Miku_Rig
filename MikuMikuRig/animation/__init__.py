import bpy
from bpy.props import PointerProperty
from . import panels, preset_operators, retarget_operators, property

modules_to_register = [property, preset_operators, retarget_operators, panels]

def register():
    for module in modules_to_register:
        for cls in module.CLASS_LIST:
            bpy.utils.register_class(cls)

    bpy.types.PoseBone.mmr_bone = PointerProperty(type = property.MMR_bone)
    bpy.types.Scene.mmr_preset = PointerProperty(type = property.MMR_preset)

def unregister():
    # 以相反顺序注销
    del bpy.types.PoseBone.mmr_bone
    del bpy.types.Scene.mmr_preset

    for module in reversed(modules_to_register):
        for cls in reversed(module.CLASS_LIST):
            bpy.utils.unregister_class(cls)