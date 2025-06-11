import bpy
import logging
import mathutils

def alert_error(title,message):
        """
        弹出一个错误提示窗口。

        :param title: 窗口标题。
        :param message: 窗口显示的错误信息。
        """
        def draw(self, context):
            self.layout.label(text=str(message))
        bpy.context.window_manager.popup_menu(draw,title=title,icon='ERROR')

def check_arm():
    """检查活动对象是否为有效的骨架，并确保Rigify插件已启用。"""
    arm = bpy.context.view_layer.objects.active

    if 'rigify' not in bpy.context.preferences.addons.keys():
        logging.info("检测到未开启rigify，已自动开启")
        alert_error("提示", "检测到未开启rigify，已自动开启")
        bpy.ops.preferences.addon_enable(module="rigify")

    if arm is None:
        logging.info("未选择骨骼！")
        alert_error("提示", "未选择骨骼！")
        return False

    elif arm.type != 'ARMATURE':
        logging.info("所选对象不是骨骼！")
        alert_error("提示", "所选对象不是骨骼！")
        return False

    return True

def apply_world_rotation_to_pose_bone(pose_bone_to_rotate:bpy.types.PoseBone, next_bone_in_chain, reference_axis_vector, angle_rad):
    """
    将世界空间中的旋转应用于指定的姿态骨骼，用于预弯曲骨骼链。
    旋转轴垂直于当前骨骼指向下一个骨骼的向量以及参考轴向量。

    :param pose_bone_to_rotate: 需要旋转的姿态骨骼。
    :param next_bone_in_chain: 骨骼链中的下一个姿态骨骼，用于确定骨骼方向。
    :param reference_axis_vector: 一个世界空间向量，用于与骨骼方向叉乘得到旋转轴。
    :param angle_rad: 旋转角度（弧度）。
    """
    bone_vector = next_bone_in_chain.head - pose_bone_to_rotate.head
    rotation_axis_world = bone_vector.cross(reference_axis_vector)
    
    world_rotation_matrix = mathutils.Matrix.Rotation(angle_rad, 4, rotation_axis_world)
    local_delta_matrix = pose_bone_to_rotate.matrix.inverted() @ world_rotation_matrix @ pose_bone_to_rotate.matrix
    pose_bone_to_rotate.rotation_mode = 'QUATERNION'
    pose_bone_to_rotate.rotation_quaternion = local_delta_matrix.to_quaternion()
    return True


class MMRPanelBase(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "MMR"