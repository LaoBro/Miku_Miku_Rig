import bpy

from . import preset
from . import rig
from . import retarget
from . import physics
from . import extra

modules_to_register = [preset, rig, retarget, physics, extra]

def register():
    for module in modules_to_register:
        for cls in module.CLASS_LIST:
            bpy.utils.register_class(cls)

def unregister():
    # Unregister in reverse order
    for module in reversed(modules_to_register):
        for cls in reversed(module.CLASS_LIST):
            bpy.utils.unregister_class(cls)