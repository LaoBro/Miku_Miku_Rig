import bpy

from . import preset
from . import rig
from . import retarget
from . import physics

Model_list=[preset,rig,retarget,physics]

def register():
    for Model in Model_list:
        for Class in Model.Class_list:
            bpy.utils.register_class(Class)

def unregister():
    for Model in Model_list:
        for Class in Model.Class_list:
            bpy.utils.unregister_class(Class)