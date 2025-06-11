from bpy.types import Operator
from . import _core
class OT_Set_Min_IK_Loop(Operator):
    """
    设置骨架中IK约束的最小迭代次数的操作器。
    """
    bl_idname = "mmr.set_min_ik_loop" # python 提示
    bl_label = "Interface"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        mmr_property = scene.mmr_property
        _core.set_min_ik_loop(context.view_layer.objects.active, mmr_property.min_ik_loop)
        return {"FINISHED"}

class OT_Hide_Skirt(Operator):
    """
    根据选定的MMD刚体隐藏裙子的操作器。
    """
    bl_idname = "mmr.hide_skirt" # python 提示
    bl_label = "Interface"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        _core.hide_skirt()
        return {"FINISHED"}

class OT_Decorate_MMD_Arm(Operator):
    """
    美化MMD骨架的操作器，调整骨骼连接、轴向、IK限制等。
    """
    bl_idname = "mmr.decorate_mmd_arm" # python 提示
    bl_label = "Interface"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        _core.decorate_mmd_arm(context)
        return {"FINISHED"}
    
CLASS_LIST = [OT_Set_Min_IK_Loop, OT_Hide_Skirt, OT_Decorate_MMD_Arm]