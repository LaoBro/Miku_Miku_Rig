# pyright: reportInvalidTypeForm=false
import bpy
from bpy.props import BoolProperty, IntProperty, FloatProperty, EnumProperty, PointerProperty, StringProperty
from . import preset_core

class MMR_bone(bpy.types.PropertyGroup):
    bone_type: StringProperty(
        name="Bone Type",
        description='Choose the bone type you want to use'
    )
    invert: BoolProperty(
        name="Invert",
        default=False,
        description="Invert bone direction for preset matching"
    )
    mass: FloatProperty(
        name="Mass",
        default=0.0,
        description="Bone mass for physics simulation",
        min=0.0
    )

class MMR_preset(bpy.types.PropertyGroup):
    rig_preset_name: EnumProperty(
        items=preset_core.get_rig_preset_item,
        description=('Choose the preset you want to use'),
    )
    retarget_preset_name: EnumProperty(
        items=preset_core.get_retarget_preset_item,
        description=('Choose the preset you want to use'),
    )

CLASS_LIST = [
    MMR_bone,
    MMR_preset
]


def register():
    bpy.utils.register_class(MMR_preset)
    bpy.utils.register_class(MMR_bone)
    bpy.types.PoseBone.mmr_bone = PointerProperty(type=MMR_bone)
    bpy.types.Scene.mmr_preset = PointerProperty(type=MMR_preset)
    #初始化预设
    #preset_core.read_json('rig')
    #preset_core.read_json('retarget')


def unregister():
    del bpy.types.PoseBone.mmr_bone
    del bpy.types.Scene.mmr_preset
    bpy.utils.unregister_class(MMR_preset)
    bpy.utils.unregister_class(MMR_bone)
    