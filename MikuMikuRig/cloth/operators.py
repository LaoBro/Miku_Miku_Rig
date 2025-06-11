import bpy
from bpy.types import Operator
from . import _core

class OT_Convert_Rigid_Body_To_Cloth(Operator):
    """
    将MMD刚体转换为布料的操作器。
    """
    bl_idname = "mmr.convert_rigid_body_to_cloth" # python 提示
    bl_label = "Interface"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        _core.convert_rigid_body_to_cloth(context)
        return {"FINISHED"}


class OT_Rigid_Body_mass_Multiply(Operator):
    """
    将所有MMD刚体的质量乘以一个系数的操作器。
    """
    bl_idname = "mmr.rigid_body_mass_multiply" # python 提示
    bl_label = "Interface"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        mmr_property = context.scene.mmr_property
        for obj in bpy.data.objects:
            if hasattr(obj, 'mmd_rigid') and obj.rigid_body: # Ensure rigid_body component exists
                if obj.mmd_rigid.name != '' and obj.mmd_rigid.type != '0':
                    # Apply the mass multiplication factor directly.
                    obj.rigid_body.mass *= mmr_property.mass_multiply_rate
                    obj.rigid_body.mass *= mmr_property.mass_multiply_rate
                    obj.rigid_body.mass *= mmr_property.mass_multiply_rate
        return {"FINISHED"}

CLASS_LIST = (
    OT_Convert_Rigid_Body_To_Cloth,
    OT_Rigid_Body_mass_Multiply,
)