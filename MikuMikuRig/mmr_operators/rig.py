import bpy
import os
import logging
import mathutils
from bpy.types import Operator
from . import preset
from . import extra


def alert_error(title, message):
    """
    弹出一个错误提示窗口。

    :param title: 窗口标题。
    :param message: 窗口显示的错误信息。
    """
    def draw(self, context):
        self.layout.label(text=str(message))
    bpy.context.window_manager.popup_menu(draw, title=title, icon='ERROR')

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


def _apply_world_rotation_to_pose_bone(pose_bone_to_rotate, next_bone_in_chain, reference_axis_vector, angle_rad):
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


def load_pose():
    """从预定义的VPD文件中加载姿态。"""
    my_dir = os.path.dirname(os.path.realpath(__file__))
    vpd_file = os.path.join(my_dir, "MMR_Rig_pose.vpd")
    print(my_dir)
    print(vpd_file)
    bpy.ops.mmd_tools.import_vpd(
        filepath=vpd_file,
        files=[{"name": "MMR_Rig_pose.vpd"}],
        directory=my_dir
    )
    bpy.ops.object.mode_set(mode='OBJECT')


def add_constraint3(generated_rig_obj:bpy.types.Object, source_arm_obj:bpy.types.Object, constraint_data_list, source_arm_preset_dict):
    """
    为生成的Rigify骨架和源MMD骨架之间添加约束。
    此函数会创建父级骨骼，并将约束应用于源MMD骨架的骨骼，使其跟随生成的Rigify骨架中的对应父级骨骼。

    :param generated_rig_obj: 生成的Rigify骨架对象。
    :param source_arm_obj: 源MMD骨架对象。
    :param constraint_data_list: 包含约束信息的元组列表。每个元组格式为 (目标骨骼名, 源骨骼类型, 是否复制旋转, 是否复制位置)。
    :param source_arm_preset_dict: 源MMD骨骼类型到骨骼名称的映射字典。
    :return: 成功匹配并添加约束的骨骼数量。
    """
    match_bone_number = 0
    # 从目标骨架（生成的骨架）获取骨骼名称
    target_rig_bone_names = list(generated_rig_obj.data.bones.keys())
    # 从源MMD骨架获取姿态骨骼
    source_arm_pose_bones = source_arm_obj.pose.bones
    
    index_list = []
    
    # 第一遍：识别匹配的骨骼并为编辑模式操作做准备
    for i, constraint_tuple in enumerate(constraint_data_list):
        to_bone_name_in_target_rig = constraint_tuple[0]
        from_bone_type_in_source = constraint_tuple[1]

        if from_bone_type_in_source not in source_arm_preset_dict:
            continue
        
        from_bone_name_in_source = source_arm_preset_dict[from_bone_type_in_source]

        if from_bone_name_in_source in source_arm_pose_bones and \
           to_bone_name_in_target_rig in target_rig_bone_names:
            match_bone_number += 1
            index_list.append(i)
            # 如果MMD骨骼是约束的一部分，则取消隐藏
            if from_bone_name_in_source in source_arm_obj.data.bones: # 检查是否存在于 data.bones 中
                 source_arm_obj.data.bones[from_bone_name_in_source].hide = False

    # 将 generated_rig_obj 切换到编辑模式以添加辅助骨骼
    bpy.context.view_layer.objects.active = generated_rig_obj # 确保 generated_rig_obj 对于操作是活动的
    bpy.ops.object.mode_set(mode='EDIT')

    target_rig_edit_bones = generated_rig_obj.data.edit_bones
    for i in index_list:
        from_bone_type_str = constraint_data_list[i][1]
        from_bone_name_in_source = source_arm_preset_dict[from_bone_type_str]
        to_bone_name_in_target_rig = constraint_data_list[i][0]
        
        parent_name = from_bone_type_str + '_parent'
        parent_bone = target_rig_edit_bones.new(name=parent_name)

        # 从源MMD骨骼的姿态设置矩阵和尾部
        source_pose_bone = source_arm_pose_bones[from_bone_name_in_source]
        parent_bone.matrix = source_pose_bone.matrix # 世界空间矩阵
        parent_bone.tail = source_pose_bone.tail # 世界空间尾部
        
        parent_bone.parent = target_rig_edit_bones[to_bone_name_in_target_rig]
        # 清除 parent_bone 现有的集合
        for coll in list(parent_bone.collections): # 迭代副本以安全地取消链接
            coll.unassign(parent_bone)
        # 从目标骨骼复制集合
        for coll in target_rig_edit_bones[to_bone_name_in_target_rig].collections:
            coll.assign(parent_bone)

    bpy.context.view_layer.objects.active = source_arm_obj
    bpy.ops.object.mode_set(mode='POSE')

    for i in index_list:
        constraint_tuple = constraint_data_list[i]
        from_bone_type_str = constraint_data_list[i][1]
        rotation_flag = constraint_tuple[2]
        location_flag = constraint_tuple[3]
        
        from_bone_name_in_source = source_arm_preset_dict[from_bone_type_str]
        source_pose_bone_to_constrain = source_arm_pose_bones[from_bone_name_in_source]
        
        constraints_obj = source_pose_bone_to_constrain.constraints
        for c in constraints_obj:
            c.mute = True
            
        parent_name_in_target_rig = from_bone_type_str + '_parent'
        
        if parent_name_in_target_rig in generated_rig_obj.data.bones:
            generated_rig_obj.data.bones[parent_name_in_target_rig].hide = True

        if location_flag:
            if rotation_flag:
                copy_transforms_constraint = constraints_obj.new(type='COPY_TRANSFORMS')
                copy_transforms_constraint.target = generated_rig_obj
                copy_transforms_constraint.subtarget = parent_name_in_target_rig
                copy_transforms_constraint.name = "rel_transforms"
                copy_transforms_constraint.mix_mode = 'REPLACE'
                copy_transforms_constraint.owner_space = 'WORLD'
                copy_transforms_constraint.target_space = 'WORLD'
            else:
                copy_location_constraint = constraints_obj.new(type='COPY_LOCATION')
                copy_location_constraint.target = generated_rig_obj
                copy_location_constraint.subtarget = parent_name_in_target_rig
                copy_location_constraint.name = "rel_location"
        else:
            if rotation_flag:
                copy_rotation_constraint = constraints_obj.new(type='COPY_ROTATION')
                copy_rotation_constraint.target = generated_rig_obj
                copy_rotation_constraint.subtarget = parent_name_in_target_rig
                copy_rotation_constraint.name = "rel_rotation"
    return match_bone_number


def RIG2(context:bpy.types.Context):
    """
    主要的Rigify骨架生成函数。
    根据选定的MMD骨架和MMR属性设置，生成一个Rigify控制器骨架，并自动匹配和约束骨骼。

    :param context: Blender的上下文对象。
    :return: 如果成功生成骨架则返回True，否则返回False。
    """
    # 属性准备阶段
    area = bpy.context.area.type
    context.area.type = 'VIEW_3D'

    mmd_arm = context.view_layer.objects.active
    extra.set_min_ik_loop(mmd_arm, 10)

    scene = context.scene
    mmr_property = scene.mmr_property

    my_dir = os.path.dirname(os.path.realpath(__file__))
    rigify_blend_file = os.path.join(my_dir, "MMR_Rig.blend")

    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    context.view_layer.objects.active = mmd_arm
    mmd_arm.select_set(True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    # 检查骨架
    if not check_arm():
        return False

    # 生成字典
    unconnect_bone_types = ['spine']
    preset_dict = {}
    bpy.ops.object.mode_set(mode='EDIT')
    for bone in mmd_arm.pose.bones:
        bone_name = bone.name
        mmr_bone:preset.MMR_bone = bone.mmr_bone
        if mmr_bone.bone_type != 'None':
            preset_dict[mmr_bone.bone_type] = bone_name
        if mmr_bone.bone_type in unconnect_bone_types:
            mmd_arm.data.edit_bones[bone_name].use_connect = False

    bpy.ops.object.mode_set(mode='OBJECT')

    # 为Rigify生成添加骨骼弯曲
    rotate_params_list = [
        ['forearm.L', 'hand.L', (0, 1, 0), -0.2618],
        ['forearm.R', 'hand.R', (0, 1, 0), -0.2618],
    ]
    if mmr_property.bent_IK_bone:
        for params in rotate_params_list:
            if not (params[0] in preset_dict and params[1] in preset_dict):
                continue
            pose_bone_to_bend = mmd_arm.pose.bones[preset_dict[params[0]]]
            next_bone = mmd_arm.pose.bones[preset_dict[params[1]]]
            _apply_world_rotation_to_pose_bone(pose_bone_to_bend, next_bone, params[2], params[3])

    # 导入metarig骨骼
    # import metarig armature
    rigify_arm_name = "MMR_Rig_relative3"

    with bpy.data.libraries.load(rigify_blend_file) as (data_from, data_to):
        data_to.objects = [rigify_arm_name]

    rigify_arm:bpy.types.Object = data_to.objects[0]
    context.collection.objects.link(rigify_arm)

    # 检测手指弯曲
    mmd_pose_bones = mmd_arm.pose.bones
    rigify_pose_bones = rigify_arm.pose.bones
    finger_name1 = preset_dict['f_index.01.L']
    finger_name2 = preset_dict['f_index.02.L']
    finger_name3 = preset_dict['f_index.03.L']
    finger_bone1 = mmd_pose_bones[finger_name1]
    finger_bone2 = mmd_pose_bones[finger_name2]
    finger_bone3 = mmd_pose_bones[finger_name3]
    finger_v1 = finger_bone2.head - finger_bone1.head
    finger_v2 = finger_bone3.head - finger_bone2.head
    finger_angle = finger_v1.angle(finger_v2)
    print(f'finger angle={finger_angle}')
    bent_finger = finger_angle > 0.26
    if bent_finger:
        finger_types = ['f_index.01.L', 'f_middle.01.L', 'f_ring.01.L', 'f_pinky.01.L',
                        'f_index.01.R', 'f_middle.01.R', 'f_ring.01.R', 'f_pinky.01.R',
                        'thumb.01.L', 'thumb.01.R']
        for bone_type_name in finger_types:
            pose_bone = rigify_pose_bones[bone_type_name]
            pose_bone.rigify_parameters.primary_rotation_axis = 'automatic'
    # 检测手臂弯曲
    arm_name1 = preset_dict['upper_arm.L']
    arm_name2 = preset_dict['forearm.L']
    arm_name3 = preset_dict['hand.L']
    arm_bone1 = mmd_pose_bones[arm_name1]
    arm_bone2 = mmd_pose_bones[arm_name2]
    arm_bone3 = mmd_pose_bones[arm_name3]
    arm_v1 = arm_bone2.head - arm_bone1.head
    arm_v2 = arm_bone3.head - arm_bone2.head
    arm_angle = arm_v1.angle(arm_v2) # 校正后的打印语句:
    print(f'arm angle={arm_angle}')
    bent_arm = arm_angle > 0.26
    if bent_arm:
        arm_types = ['upper_arm.L', 'upper_arm.R']
        for bone_type_name in arm_types:
            pose_bone = rigify_pose_bones[bone_type_name]
            pose_bone.rigify_parameters.primary_rotation_axis = 'automatic'

    # 自动缩放
    mmd_spine_head_z = mmd_arm.pose.bones[preset_dict['spine.006']].head[2]
    mmd_scale_z = mmd_arm.scale[2]
    rigify_spine_head_z = rigify_arm.pose.bones['spine.006'].head[2]
    rigify_scale_z = rigify_arm.scale[2]
    scale_factor = (mmd_spine_head_z * mmd_scale_z) / (rigify_spine_head_z * rigify_scale_z)
    rigify_arm.scale *= scale_factor

    bpy.ops.object.select_all(action='DESELECT')
    context.view_layer.objects.active = rigify_arm
    rigify_arm.select_set(True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.armature.select_all(action='DESELECT')

    if "thumb.01.L" not in preset_dict:
        rigify_arm.data.edit_bones.remove(rigify_arm.data.edit_bones["thumb.03.L"])
        rigify_arm.data.edit_bones["thumb.02.L"].name='thumb.03.L'
        rigify_arm.data.edit_bones["thumb.01.L"].name='thumb.02.L'

    if "thumb.01.R" not in preset_dict:
        rigify_arm.data.edit_bones.remove(rigify_arm.data.edit_bones["thumb.03.R"])
        rigify_arm.data.edit_bones["thumb.02.R"].name='thumb.03.R'
        rigify_arm.data.edit_bones["thumb.01.R"].name = 'thumb.02.R'

    current_rigify_edit_bones_names = list(rigify_arm.data.edit_bones.keys())

    # 新骨骼匹配方法
    for bone in mmd_arm.pose.bones:
        mmr_bone:preset.MMR_bone = bone.mmr_bone
        bone_type = mmr_bone.bone_type
        if bone_type != "None" and bone_type in current_rigify_edit_bones_names:
            rigify_edit_bone = rigify_arm.data.edit_bones[bone_type]
            if mmr_bone.invert:
                rigify_edit_bone.tail = bone.head
            else:
                rigify_edit_bone.tail = bone.tail

    for bone in mmd_arm.pose.bones:
        mmr_bone:preset.MMR_bone = bone.mmr_bone
        bone_type = mmr_bone.bone_type
        if bone_type != "None" and bone_type in current_rigify_edit_bones_names:
            rigify_edit_bone = rigify_arm.data.edit_bones[bone_type]
            if mmr_bone.invert:
                rigify_edit_bone.head = bone.tail
            else:
                rigify_edit_bone.head = bone.head

    # 修正部分骨骼
    rigify_edit_bones = rigify_arm.data.edit_bones
    rigify_edit_bones["spine.003"].tail = rigify_edit_bones["spine.004"].head
    if rigify_edit_bones["spine"].tail == rigify_edit_bones["spine.002"].head:
        rigify_edit_bones["spine"].tail[2] -= 0.01
    if rigify_edit_bones["spine.001"].tail == rigify_edit_bones["spine.003"].head:
        rigify_edit_bones["spine.001"].tail[2] -= 0.01

    rigify_edit_bones["spine.006"].tail = rigify_edit_bones["spine.006"].head.copy() # 确保它是一个新的向量
    rigify_edit_bones["spine.006"].tail[2] += rigify_edit_bones["spine.004"].length * 3
    if rigify_edit_bones["spine.004"].tail == rigify_edit_bones["spine.006"].head:
        rigify_edit_bones["spine.004"].tail[2] -= 0.01

    f_middle_l_head = rigify_edit_bones["f_middle.01.L"].head
    f_ring_l_head = rigify_edit_bones["f_ring.01.L"].head
    rigify_edit_bones["hand.L"].tail = (f_middle_l_head + f_ring_l_head) / 2

    f_middle_r_head = rigify_edit_bones["f_middle.01.R"].head
    f_ring_r_head = rigify_edit_bones["f_ring.01.R"].head
    rigify_edit_bones["hand.R"].tail = (f_middle_r_head + f_ring_r_head) / 2

    if 'ToeTipIK_L' in preset_dict and "toe.L" not in preset_dict:
        rigify_edit_bones["toe.L"].head = mmd_arm.pose.bones[preset_dict['ToeTipIK_L']].head
    if 'ToeTipIK_R' in preset_dict and "toe.R" not in preset_dict:
        rigify_edit_bones["toe.R"].head = mmd_arm.pose.bones[preset_dict['ToeTipIK_R']].head

    rigify_edit_bones["toe.L"].tail = rigify_edit_bones["toe.L"].head.copy()
    rigify_edit_bones["toe.L"].tail[1] -= rigify_edit_bones["foot.L"].length / 2

    rigify_edit_bones["toe.R"].tail = rigify_edit_bones["toe.R"].head.copy()
    rigify_edit_bones["toe.R"].tail[1] -= rigify_edit_bones["foot.R"].length / 2

    rigify_edit_bones["heel.02.L"].head = rigify_edit_bones["foot.L"].head.copy()
    rigify_edit_bones["heel.02.L"].head[2] = rigify_edit_bones["foot.L"].tail[2]
    rigify_edit_bones["heel.02.L"].tail = rigify_edit_bones["heel.02.L"].head.copy()
    rigify_edit_bones["heel.02.L"].tail[0] += rigify_edit_bones["foot.L"].length / 10
    rigify_edit_bones["heel.02.L"].head[0] -= rigify_edit_bones["foot.L"].length / 10

    rigify_edit_bones["heel.02.R"].head = rigify_edit_bones["foot.R"].head.copy()
    rigify_edit_bones["heel.02.R"].head[2] = rigify_edit_bones["foot.R"].tail[2]
    rigify_edit_bones["heel.02.R"].tail = rigify_edit_bones["heel.02.R"].head.copy()
    rigify_edit_bones["heel.02.R"].tail[0] -= rigify_edit_bones["foot.R"].length / 10
    rigify_edit_bones["heel.02.R"].head[0] += rigify_edit_bones["foot.R"].length / 10

    extend_bone_types = ['thumb.03.L', 'f_index.03.L', 'f_middle.03.L', 'f_ring.03.L', 'f_pinky.03.L',
                         'thumb.03.R', 'f_index.03.R', 'f_middle.03.R', 'f_ring.03.R', 'f_pinky.03.R']
    for bone_type_name in extend_bone_types:
        edit_bone = rigify_edit_bones[bone_type_name]
        parent_edit_bone = edit_bone.parent
        edit_bone.tail = parent_edit_bone.tail * 2 - parent_edit_bone.head

    # 匹配眼睛骨骼
    invert_eyes = False
    if 'eye.L' in preset_dict and 'eye.R' in preset_dict:
        eye_l_edit = rigify_edit_bones['eye.L']
        mmd_eye_l_pose = mmd_arm.pose.bones[preset_dict['eye.L']]
        eye_l_edit.head[2] = mmd_eye_l_pose.head[2]
        eye_l_edit.head[0] = max(mmd_eye_l_pose.head[0], mmd_eye_l_pose.tail[0])
        eye_l_edit.head[1] = min(mmd_eye_l_pose.head[1], mmd_eye_l_pose.tail[1])
        eye_l_edit.tail = eye_l_edit.head.copy()
        eye_l_edit.tail[1] -= 0.1

        eye_r_edit = rigify_edit_bones['eye.R']
        mmd_eye_r_pose = mmd_arm.pose.bones[preset_dict['eye.R']]
        eye_r_edit.head[2] = mmd_eye_r_pose.head[2]
        eye_r_edit.head[0] = min(mmd_eye_r_pose.head[0], mmd_eye_r_pose.tail[0])
        eye_r_edit.head[1] = min(mmd_eye_r_pose.head[1], mmd_eye_r_pose.tail[1])
        eye_r_edit.tail = eye_r_edit.head.copy()
        eye_r_edit.tail[1] -= 0.1

        if eye_l_edit.head[0] < eye_r_edit.head[0]: # 检查X坐标是否交换
            # 如果左眼在右眼的右侧（负X通常是左侧），则交换名称
            temp_name = eye_l_edit.name
            eye_l_edit.name = eye_r_edit.name
            eye_r_edit.name = temp_name
            invert_eyes = True

    # 修正骨骼轴向
    positive_z_bone_types = [
        'shoulder.L','shoulder.R',

        'f_index.01.L','f_index.02.L','f_index.03.L',
        'f_middle.01.L','f_middle.02.L','f_middle.03.L',
        'f_ring.01.L','f_ring.02.L','f_ring.03.L',
        'f_pinky.01.L','f_pinky.02.L','f_pinky.03.L',

        'f_index.01.R','f_index.02.R','f_index.03.R',
        'f_middle.01.R','f_middle.02.R','f_middle.03.R',
        'f_ring.01.R','f_ring.02.R','f_ring.03.R',
        'f_pinky.01.R','f_pinky.02.R','f_pinky.03.R',
    ]
    positive_x_bone_types = [

    ]
    negative_x_bone_types = [

    ]
    negative_y_bone_types = [
        'hand.L','upper_arm.L','forearm.L','hand.R','upper_arm.R','forearm.R',
        'thumb.01.L','thumb.02.L','thumb.03.L',
        'thumb.01.R','thumb.02.R','thumb.03.R',
    ]

    bpy.ops.armature.select_all(action='DESELECT')
    rigify_arm.data.show_axes = True
    current_rigify_edit_bones_names = list(rigify_arm.data.edit_bones.keys()) # 如果名称已更改，则刷新

    for bone_type_name in positive_z_bone_types:
        if bone_type_name in current_rigify_edit_bones_names:
            rigify_edit_bones[bone_type_name].select = True
            rigify_edit_bones[bone_type_name].select_head = True
            rigify_edit_bones[bone_type_name].select_tail = True

    bpy.ops.armature.calculate_roll(type='GLOBAL_POS_Z')
    bpy.ops.armature.select_all(action='DESELECT')

    for bone_type_name in positive_x_bone_types:
        if bone_type_name in current_rigify_edit_bones_names:
            rigify_edit_bones[bone_type_name].select = True
            rigify_edit_bones[bone_type_name].select_head = True
            rigify_edit_bones[bone_type_name].select_tail = True

    bpy.ops.armature.calculate_roll(type='GLOBAL_POS_X')
    bpy.ops.armature.select_all(action='DESELECT')

    for bone_type_name in negative_x_bone_types:
        if bone_type_name in current_rigify_edit_bones_names:
            rigify_edit_bones[bone_type_name].select = True
            rigify_edit_bones[bone_type_name].select_head = True
            rigify_edit_bones[bone_type_name].select_tail = True

    bpy.ops.armature.calculate_roll(type='GLOBAL_NEG_X')
    bpy.ops.armature.select_all(action='DESELECT')

    for bone_type_name in negative_y_bone_types:
        if bone_type_name in current_rigify_edit_bones_names:
            rigify_edit_bones[bone_type_name].select = True
            rigify_edit_bones[bone_type_name].select_head = True
            rigify_edit_bones[bone_type_name].select_tail = True

    bpy.ops.armature.calculate_roll(type='GLOBAL_NEG_Y')

    # 生成控制器
    if mmr_property.debug:
        bpy.context.area.type = area
        return

    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    context.view_layer.objects.active = rigify_arm
    rigify_arm.select_set(True)

    bpy.ops.pose.rigify_generate()
    rig = context.view_layer.objects.active # 这是生成的骨架

    # 删除无用骨架
    bpy.data.objects.remove(rigify_arm, do_unlink=True)

    # 开始调整生成的控制器
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active=mmd_arm
    rig.select_set(True)

    # 肩膀联动

    if mmr_property.auto_shoulder:
        bpy.ops.object.mode_set(mode='EDIT')
        auto_shoulder_l_edit = rig.data.edit_bones.new(name='auto_shoulder_L') # 已修正拼写错误
        auto_shoulder_l_edit.head = rig.data.edit_bones['shoulder.L'].head
        auto_shoulder_l_edit.tail = rig.data.edit_bones['shoulder.L'].tail
        auto_shoulder_l_edit.roll = rig.data.edit_bones['shoulder.L'].roll
        auto_shoulder_l_edit.parent = rig.data.edit_bones['upper_arm_ik.L']

        auto_shoulder_r_edit = rig.data.edit_bones.new(name='auto_shoulder_R') # 已修正拼写错误
        auto_shoulder_r_edit.head = rig.data.edit_bones['shoulder.R'].head
        auto_shoulder_r_edit.tail = rig.data.edit_bones['shoulder.R'].tail
        auto_shoulder_r_edit.roll = rig.data.edit_bones['shoulder.R'].roll
        auto_shoulder_r_edit.parent = rig.data.edit_bones['upper_arm_ik.R']

        bpy.ops.object.mode_set(mode='POSE')
        shoulder_l_pose = rig.pose.bones["shoulder.L"]
        auto_shoulder_l_pose = rig.pose.bones["auto_shoulder_L"]
        shoulder_l_constraint = shoulder_l_pose.constraints.new('COPY_ROTATION')
        shoulder_l_constraint.name = 'MMR_auto_shoulder'
        shoulder_l_constraint.target = rig
        shoulder_l_constraint.subtarget = 'auto_shoulder_L'
        shoulder_l_constraint.influence = 0.5
        auto_shoulder_l_limit = auto_shoulder_l_pose.constraints.new('LIMIT_ROTATION')
        auto_shoulder_l_limit.name = 'MMR_auto_shoulder'
        auto_shoulder_l_limit.use_limit_x = True
        auto_shoulder_l_limit.min_x = -0.35
        auto_shoulder_l_limit.max_x = 1.57
        auto_shoulder_l_limit.owner_space = 'LOCAL_WITH_PARENT'
        # 将 "auto_shoulder_L" 骨骼分配到与 "ORG-shoulder.L" 骨骼相同的骨骼集合中
        source_collections_bone_l = rig.data.bones["ORG-shoulder.L"]
        target_bone_data_l = auto_shoulder_l_pose.bone
        # 清除目标骨骼现有的集合
        for coll in list(target_bone_data_l.collections):
            coll.unassign(target_bone_data_l)
        # 链接源骨骼的集合到目标骨骼
        for coll in source_collections_bone_l.collections:
            coll.assign(target_bone_data_l)



        shoulder_r_pose = rig.pose.bones["shoulder.R"]
        auto_shoulder_r_pose = rig.pose.bones["auto_shoulder_R"]
        shoulder_r_constraint = shoulder_r_pose.constraints.new('COPY_ROTATION')
        shoulder_r_constraint.name = 'MMR_auto_shoulder'
        shoulder_r_constraint.target = rig
        shoulder_r_constraint.subtarget = 'auto_shoulder_R'
        shoulder_r_constraint.influence = 0.5
        auto_shoulder_r_limit = auto_shoulder_r_pose.constraints.new('LIMIT_ROTATION')
        auto_shoulder_r_limit.name = 'MMR_auto_shoulder'
        auto_shoulder_r_limit.use_limit_x = True
        auto_shoulder_r_limit.min_x = -0.35
        auto_shoulder_r_limit.max_x = 1.57
        auto_shoulder_r_limit.owner_space = 'LOCAL_WITH_PARENT'
        # 将 "auto_shoulder_R" 骨骼分配到与 "ORG-shoulder.R" 骨骼相同的骨骼集合中
        source_collections_bone_r = rig.data.bones["ORG-shoulder.R"]
        target_bone_data_r = auto_shoulder_r_pose.bone
        # 清除目标骨骼现有的集合
        for coll in list(target_bone_data_r.collections):
            coll.unassign(target_bone_data_r)
        # 链接源骨骼的集合到目标骨骼
        for coll in source_collections_bone_r.collections:
            coll.assign(target_bone_data_r)

    # 上半身控制器
    if mmr_property.upper_body_controller:
        bpy.ops.object.mode_set(mode='EDIT')
        center_edit = rig.data.edit_bones.new(name='Center')
        center_edit.head = rig.data.edit_bones['root'].head
        center_edit.tail = rig.data.edit_bones['root'].tail
        center_edit.roll = rig.data.edit_bones['root'].roll
        center_edit.length = rig.data.edit_bones['root'].length / 3
        center_edit.head[2] = center_edit.tail[2] = rig.data.edit_bones['shin_fk.L'].head[2]

        '''Groove=rig.data.edit_bones.new(name='Groove')
        Groove.head=rig.data.edit_bones['root'].head
        Groove.tail=rig.data.edit_bones['root'].tail
        Groove.roll=rig.data.edit_bones['root'].roll
        Groove.length=rig.data.edit_bones['root'].length/3
        if 'Groove' in preset_dict:
            Groove.head[2]=Groove.tail[2]=mmd_bones[preset_dict['Groove']].head[2]
        else:
            Groove.head[2]=Groove.tail[2]=rig.data.edit_bones['shin_fk.L'].head[2]'''

        rig.data.edit_bones['MCH-torso.parent'].parent = center_edit
        rig.data.edit_bones['MCH-hand_ik.parent.L'].parent = center_edit
        rig.data.edit_bones['MCH-hand_ik.parent.R'].parent = center_edit
        #Groove.parent=Center
        center_edit.parent = rig.data.edit_bones['root']

        bpy.ops.object.mode_set(mode='POSE')
        ''' Groove=rig.pose.bones["Groove"]
        Groove.custom_shape = bpy.data.objects["WGT-rig_root"]
        Groove.mmd_bone.name_j='グルーブ'''
        rig.pose.bones["upper_arm_parent.L"]["IK_parent"] = 0
        rig.pose.bones["upper_arm_parent.R"]["IK_parent"] = 0
        rig.pose.bones["torso"]["torso_parent"] = 0
        #Groove.bone.layers = rig.data.bones["torso"].layers
        #Groove.bone_group = rig.pose.bone_groups['Special']
        center_pose = rig.pose.bones["Center"]
        #Center.mmd_bone.name_j='センター'
        center_pose.custom_shape = rig.pose.bones["root"].custom_shape

        # 将 "Center" 骨骼分配到与 "torso" 骨骼相同的骨骼集合中
        source_collections_bone = rig.data.bones["torso"]
        target_bone_data = center_pose.bone # 这是 rig.data.bones["Center"]
        # 清除目标骨骼现有的集合
        for coll in list(target_bone_data.collections): # 遍历副本以安全地取消链接
            coll.unassign(target_bone_data)
        # 链接源骨骼的集合到目标骨骼
        for coll in source_collections_bone.collections:
            coll.assign(target_bone_data)
    else:
        #rig.pose.bones['MCH-torso.parent'].mmd_bone.name_j='グルーブ'
        pass

    # 添加约束
    # add constraint

    constraints_data = [
        ("DEF-upper_arm.L","upper_arm.L",True,True),
        ("DEF-upper_arm.R","upper_arm.R",True,True),
        ("DEF-forearm.L","forearm.L",True,True),
        ("DEF-forearm.R","forearm.R",True,True),
        ("DEF-shoulder.L","shoulder.L",True,True),
        ("DEF-shoulder.R","shoulder.R",True,True),
        ("DEF-hand.L","hand.L",True,True),
        ("DEF-hand.R","hand.R",True,True),
        ("DEF-upper_arm.L.001","ArmTwist_L",True,False),
        ("DEF-upper_arm.R.001","ArmTwist_R",True,False),
        ("DEF-forearm.L.001","HandTwist_L",True,False),
        ("DEF-forearm.R.001","HandTwist_R",True,False),

        ("DEF-thigh.L","thigh.L",True,True),
        ("DEF-thigh.R","thigh.R",True,True),
        ("DEF-shin.L","shin.L",True,True),
        ("DEF-shin.R","shin.R",True,True),

        ("DEF-foot.L","foot.L",True,True),
        ("DEF-foot.R","foot.R",True,True),
        ("DEF-foot.L","LegIK_L",True,True),
        ("DEF-foot.R","LegIK_R",True,True),
        ("DEF-toe.L","toe.L",True,False),
        ("DEF-toe.R","toe.R",True,False),
        ("DEF-foot.L","ToeTipIK_L",False,True),
        ("DEF-foot.R","ToeTipIK_R",False,True),

        ("spine_fk.003","spine.003",True,True),
        ("spine_fk.002","spine.002",True,True),
        ("spine_fk.001","spine.001",True,True),

        ("spine_fk","spine",True,True),
        ("torso","Center",True,True),
        ("DEF-spine.004","spine.004",True,True),
        ("DEF-spine.006","spine.006",True,True),
        ("root","ParentNode",True,True),

        ("DEF-thumb.01.L","thumb.01.L",True,True),
        ("DEF-thumb.01.R","thumb.01.R",True,True),
        ("DEF-thumb.02.L","thumb.02.L",True,True),
        ("DEF-thumb.02.R","thumb.02.R",True,True),
        ("DEF-thumb.03.L","thumb.03.L",True,True),
        ("DEF-thumb.03.R","thumb.03.R",True,True),

        ("DEF-f_index.01.L","f_index.01.L",True,True),
        ("DEF-f_index.01.R","f_index.01.R",True,True),
        ("DEF-f_index.02.L","f_index.02.L",True,True),
        ("DEF-f_index.02.R","f_index.02.R",True,True),
        ("DEF-f_index.03.L","f_index.03.L",True,True),
        ("DEF-f_index.03.R","f_index.03.R",True,True),

        ("DEF-f_middle.01.L","f_middle.01.L",True,True),
        ("DEF-f_middle.01.R","f_middle.01.R",True,True),
        ("DEF-f_middle.02.L","f_middle.02.L",True,True),
        ("DEF-f_middle.02.R","f_middle.02.R",True,True),
        ("DEF-f_middle.03.L","f_middle.03.L",True,True),
        ("DEF-f_middle.03.R","f_middle.03.R",True,True),

        ("DEF-f_ring.01.L","f_ring.01.L",True,True),
        ("DEF-f_ring.01.R","f_ring.01.R",True,True),
        ("DEF-f_ring.02.L","f_ring.02.L",True,True),
        ("DEF-f_ring.02.R","f_ring.02.R",True,True),
        ("DEF-f_ring.03.L","f_ring.03.L",True,True),
        ("DEF-f_ring.03.R","f_ring.03.R",True,True),

        ("DEF-f_pinky.01.L","f_pinky.01.L",True,True),
        ("DEF-f_pinky.01.R","f_pinky.01.R",True,True),
        ("DEF-f_pinky.02.L","f_pinky.02.L",True,True),
        ("DEF-f_pinky.02.R","f_pinky.02.R",True,True),
        ("DEF-f_pinky.03.L","f_pinky.03.L",True,True),
        ("DEF-f_pinky.03.R","f_pinky.03.R",True,True),
    ]

    if invert_eyes:
        constraints_data.append(("ORG-eye.L", "eye.R", True, False))
        constraints_data.append(("ORG-eye.R", "eye.L", True, False))
    else:
        constraints_data.append(("ORG-eye.L", "eye.L", True, False))
        constraints_data.append(("ORG-eye.R", "eye.R", True, False))

    # 使用参数调用 add_constraint3
    # mmd_arm 是原始骨架，rig 是生成的骨架。
    match_bone_number = add_constraint3(rig, mmd_arm, constraints_data, preset_dict)

    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode='POSE') # 将骨架设置为姿态模式以更改属性

    bpy.ops.object.mode_set(mode = 'POSE')
    
    # 修正rigifyIK控制器范围限制
    rig.pose.bones["MCH-shin_ik.L"].use_ik_limit_x = True
    rig.pose.bones["MCH-shin_ik.R"].use_ik_limit_x = True
    rig.pose.bones["MCH-shin_ik.L"].ik_min_x = -0.0174533
    rig.pose.bones["MCH-shin_ik.R"].ik_min_x = -0.0174533

    '''rig.pose.bones["MCH-forearm_ik.L"].use_ik_limit_z = True
    rig.pose.bones["MCH-forearm_ik.R"].use_ik_limit_z = True
    rig.pose.bones["MCH-forearm_ik.L"].ik_max_z = 0
    rig.pose.bones["MCH-forearm_ik.R"].ik_min_z = 0'''

    # 极向目标开关
    # pole target
    #rig.pose.bones["MCH-forearm_ik.L"].constraints["IK.001"].pole_angle = 3.14159
    if mmr_property.pole_target:
        rig.pose.bones["thigh_parent.L"]["pole_vector"] = 1
        rig.pose.bones["thigh_parent.R"]["pole_vector"] = 1
        rig.pose.bones["upper_arm_parent.L"]["pole_vector"] = 1
        rig.pose.bones["upper_arm_parent.R"]["pole_vector"] = 1

    # 将IK拉伸设为0
    # set IK stretch to 0
    rig.pose.bones["upper_arm_parent.L"]["IK_Stretch"] = 0
    rig.pose.bones["upper_arm_parent.R"]["IK_Stretch"] = 0
    rig.pose.bones["thigh_parent.L"]["IK_Stretch"] = 0
    rig.pose.bones["thigh_parent.R"]["IK_Stretch"] = 0

    # 捩骨约束
    # Twist constrains
    '''if 'HandTwist_L' in preset_dict:
        c1=mmd_arm.pose.bones[preset_dict['HandTwist_L']].constraints.new(type='COPY_ROTATION')
        c1.target=rig
        c1.subtarget='ORG-hand.L'
        c1.mix_mode = 'BEFORE'
        c1.target_space = 'LOCAL'
        c1.owner_space = 'LOCAL'
        c1.influence = 0.5
        c2=mmd_arm.pose.bones[preset_dict['HandTwist_L']].constraints.new(type='DAMPED_TRACK')
        c2.target=rig
        c2.subtarget='ORG-hand.L'
        mmd_arm.data.bones[preset_dict['HandTwist_L']].hide=False

    if 'HandTwist_R' in preset_dict:
        c1=mmd_arm.pose.bones[preset_dict['HandTwist_R']].constraints.new(type='COPY_ROTATION')
        c1.target=rig
        c1.subtarget='ORG-hand.R'
        c1.mix_mode = 'BEFORE'
        c1.target_space = 'LOCAL'
        c1.owner_space = 'LOCAL'
        c1.influence = 0.5
        c2=mmd_arm.pose.bones[preset_dict['HandTwist_R']].constraints.new(type='DAMPED_TRACK')
        c2.target=rig
        c2.subtarget='ORG-hand.R'
        mmd_arm.data.bones[preset_dict['HandTwist_R']].hide=False

    if 'ArmTwist_L' in preset_dict:
        c1=mmd_arm.pose.bones[preset_dict['ArmTwist_L']].constraints.new(type='COPY_ROTATION')
        c1.target=rig
        c1.subtarget='ORG-forearm.L'
        c1.mix_mode = 'BEFORE'
        c1.target_space = 'LOCAL'
        c1.owner_space = 'LOCAL'
        c2=mmd_arm.pose.bones[preset_dict['ArmTwist_L']].constraints.new(type='DAMPED_TRACK')
        c2.target=rig
        c2.subtarget='ORG-forearm.L'
        mmd_arm.data.bones[preset_dict['ArmTwist_L']].hide=False

    if 'ArmTwist_R' in preset_dict:
        c1=mmd_arm.pose.bones[preset_dict['ArmTwist_R']].constraints.new(type='COPY_ROTATION')
        c1.target=rig
        c1.subtarget='ORG-forearm.R'
        c1.mix_mode = 'BEFORE'
        c1.target_space = 'LOCAL'
        c1.owner_space = 'LOCAL'
        c2=mmd_arm.pose.bones[preset_dict['ArmTwist_R']].constraints.new(type='DAMPED_TRACK')
        c2.target=rig
        c2.subtarget='ORG-forearm.R'
        mmd_arm.data.bones[preset_dict['ArmTwist_R']].hide=False'''

    # 写入MMR骨骼预设
    rigify_preset=preset.preset_dict_dict['retarget']['Rigify']
    preset.apply_preset_data_to_pose(rig.pose, rigify_preset) # 从 set_bone_type 更改

    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')

    # 隐藏原骨架，把新骨架设为永远在前
    # hide old armature
    rig.show_in_front = True
    mmd_arm.hide_set(True)
    rig.name = mmd_arm.name + '_Rig'

    # 缩小root控制器
    # reduce size
    '''if bpy.app.version[0]>=3:
        rig.pose.bones["root"].custom_shape_scale = 0.4
    else:
        rig.pose.bones["root"].custom_shape_scale_xyz=(0.4,0.4,0.4)'''

    # 已弃用，隐藏部分控制器
    """rig.data.layers[1] = False
    rig.data.layers[2] = False
    rig.data.layers[4] = False
    rig.data.layers[6] = False
    rig.data.layers[8] = False
    rig.data.layers[9] = False
    rig.data.layers[11] = False
    rig.data.layers[12] = False
    rig.data.layers[14] = False
    rig.data.layers[15] = False
    rig.data.layers[17] = False
    rig.data.layers[18] = False
    if 'eye.L' not in preset_dict or 'eye.R' not in preset_dict:
        rig.data.layers[0] = False"""

    # 锁定移动的骨骼列表
    lock_location_bone_names = [
        "upper_arm_ik.L","upper_arm_ik.R","thigh_ik.L","thigh_ik.R","hips","chest","neck","head","shoulder.L","shoulder.R","thumb.01_master.L","thumb.01_master.R",
        "thumb.02_master.L","thumb.02_master.R","f_index.01_master.L","f_index.01_master.R","f_middle.01_master.L","f_middle.01_master.R",
        "f_ring.01_master.L","f_ring.01_master.R","f_pinky.01_master.L","f_pinky.01_master.R"
        ]
    # 隐藏的骨骼列表
    hide_bone_names = [
        'upper_arm_parent.L','upper_arm_parent.R','thigh_parent.L','thigh_parent.R','master_eye.L','master_eye.R',
        'ear.L','ear.R','nose_master','teeth.T','teeth.B','tongue_master','jaw_master'
        ]
    # 锁定缩放的骨骼列表
    lock_scale_bone_names = [
        "root","torso","foot_ik.L","foot_ik.R","toe.L","toe.R","hand_ik.L","hand_ik.R","upper_arm_ik.L","upper_arm_ik.R","thigh_ik.L","thigh_ik.R",
        "hips","chest","neck","head","shoulder.L","shoulder.R"
        ]
    for bone_name in lock_location_bone_names:
        if bone_name in rig.data.bones:
            rig.pose.bones[bone_name].lock_location = [True, True, True]
    for bone_name in lock_scale_bone_names:
        if bone_name in rig.data.bones:
            rig.pose.bones[bone_name].lock_scale = [True, True, True]
    for bone_name in hide_bone_names:
        if bone_name in rig.data.bones:
            rig.data.bones[bone_name].hide = True

    # 替换实心控制器
    # replace controller
    '''bpy.ops.object.select_all(action='DESELECT')
    if mmr_property.solid_rig:
        solid_rig_list=[]
        solid_rig_blend_file = os.path.join(my_dir, "Solid_Rig.blend")
        with bpy.data.libraries.load(solid_rig_blend_file) as (data_from, data_to):
            data_to.objects = data_from.objects
        for obj in data_to.objects:
            solid_rig_list.append(obj.name)
            bpy.data.collections["WGTS_rig"].objects.link(obj)

        bpy.context.view_layer.objects.active=rig
        bpy.ops.object.mode_set(mode = 'POSE')
        bpy.context.object.pose.bones["Ankle_ik_L"].custom_shape = bpy.data.objects["WGT-rig_Ankle_ik_L_solid"]
        for bone in rig.pose.bones:
            if bone.custom_shape !=None:
                solid_name=bone.custom_shape.name+"_solid"
                if solid_name in solid_rig_list:
                    bone.custom_shape=bpy.data.objects[solid_name]
        rig.display_type = 'SOLID'
        rig.show_in_front = False
        bpy.ops.object.mode_set(mode = 'OBJECT')'''

    # 将轴心设为各自中点以方便操作
    # set transform pivot point to individual
    bpy.context.view_layer.objects.active = rig
    rig.select_set(True)
    bpy.context.scene.tool_settings.transform_pivot_point = 'INDIVIDUAL_ORIGINS'
    bpy.context.area.type = area
    logging.info(f"完成 匹配骨骼数:{match_bone_number}")
    alert_error("提示", f"完成 匹配骨骼数:{match_bone_number}")
    return True


def decorate_mmd_arm(context):
    """
    美化MMD骨架，调整骨骼连接、轴向、IK限制等，使其更适合在Blender中进行动画制作。

    :param context: Blender的上下文对象。
    """
    if check_arm() is False:
        return

    mmd_arm = context.view_layer.objects.active

    pose_bones = mmd_arm.pose.bones
    edit_bones = mmd_arm.data.edit_bones
    mmd_jp_to_blender_name_dict = {}

    # 生成字典
    for pose_bone in pose_bones:
        name_j = pose_bone.mmd_bone.name_j
        mmd_jp_to_blender_name_dict[name_j] = pose_bone.name

    primary_bone_list=[
        '全ての親','センター','グルーブ','下半身','上半身','上半身2','首','頭',
        '腰','グルーブ2','グルーブ','センター2',
        '左足','左足ＩＫ','左ひざ',
        '右足','右足ＩＫ','右ひざ',
        '左足IK親','右足IK親',
        '左肩','左腕','左ひじ','左手首',
        '右肩','右腕','右ひじ','右手首',
        '左肩P','左腕捩','左手捩',
        '右肩P','右腕捩','右手捩',
    ]
    def set_bone_layer(bone_data, layer_index):
        bone_data.layers[layer_index] = True
        for i in range(32):
            if i != layer_index:
                bone_data.layers[i] = False

    def connect_bone_chain(bone_chain_jp):
        if bone_chain_jp[0] in mmd_jp_to_blender_name_dict:
            chain_length = len(bone_chain_jp)
            for i in range(chain_length - 1):
                if bone_chain_jp[i+1] in mmd_jp_to_blender_name_dict:
                    child_bone_name = mmd_jp_to_blender_name_dict[bone_chain_jp[i]]
                    parent_bone_name = mmd_jp_to_blender_name_dict[bone_chain_jp[i+1]]
                    child_edit_bone = edit_bones[child_bone_name]
                    parent_edit_bone = edit_bones[parent_bone_name]
                    child_edit_bone.parent = parent_edit_bone
                    parent_edit_bone.tail = child_edit_bone.head
                    child_edit_bone.use_connect = True
                else:
                    return
        else:
            return
    bone_chain_list=[
        ['左手首','左手捩','左ひじ','左腕捩','左腕'],
        ['右手首','右手捩','右ひじ','右腕捩','右腕'],
        ['頭','首','上半身2','上半身']
    ]
    arm_bone_dict={
        '頭':(None,(None,None),(None,None),(None,None)),
        '首':(None,(None,None),(None,None),(None,None)),
        '上半身２':(None,(None,None),(None,None),(None,None)),
        '上半身':(None,(None,None),(None,None),(None,None)),
        '左肩':(None,(None,None),(None,None),(None,None)),
        '右肩':(None,(None,None),(None,None),(None,None)),
        '左手捩':(None,None,(None,None),None),
        '左腕捩':(None,None,(None,None),None),
        '右手捩':(None,None,(None,None),None),
        '右腕捩':(None,None,(None,None),None),
        '左腕':(-2.463,(None,None),None,(None,None)),
        '右腕':(-0.679,(None,None),None,(None,None)),
        '左ひじ':(-2.48,None,None,(-0.001,None)),
        '右ひじ':(-0.66,None,None,(-0.001,None)),
        '左手首':(None,(None,None),None,(None,None)),
        '右手首':(None,(None,None),None,(None,None)),
    }

    def extend_bone_tail(edit_bone_to_extend):
        parent_edit_bone = edit_bone_to_extend.parent
        if parent_edit_bone: # 检查父骨骼是否存在
            bone_vector = edit_bone_to_extend.head - parent_edit_bone.head
            edit_bone_to_extend.tail = edit_bone_to_extend.head + bone_vector
            edit_bone_to_extend.roll = parent_edit_bone.roll
    extend_bone_list=[
        '左親指２',
        '左人指３',
        '左中指３',
        '左薬指３',
        '左小指３',
        '右親指２',
        '右人指３',
        '右中指３',
        '右薬指３',
        '右小指３',
    ]
    bpy.ops.object.mode_set(mode='EDIT')

    for name_j, blender_name in mmd_jp_to_blender_name_dict.items():
        # current_pose_bone = pose_bones[blender_name] # Unused
        current_edit_bone = edit_bones[blender_name]

        # 延长骨骼
        if name_j in extend_bone_list:
            extend_bone_tail(current_edit_bone)

        # 断开先骨骼
        if '先' in name_j:
            current_edit_bone.use_connect = False

        # 对称轴向
        if '左' in name_j:
            name_j_r = name_j.replace('左', '右')
            if name_j_r in mmd_jp_to_blender_name_dict:
                edit_bone_r = edit_bones[mmd_jp_to_blender_name_dict[name_j_r]]
                edit_bone_r.roll = -current_edit_bone.roll

        # 设置特定轴向
        if name_j in arm_bone_dict:
            bone_setting = arm_bone_dict[name_j]
            current_edit_bone.roll = bone_setting[0] or current_edit_bone.roll

    # 链接骨骼
    for bone_chain in bone_chain_list:
        connect_bone_chain(bone_chain)

    # 修改手掌骨骼
    def adjust_hand_bone(hand_name_jp, finger1_name_jp, finger2_name_jp):
        if hand_name_jp in mmd_jp_to_blender_name_dict and \
           finger1_name_jp in mmd_jp_to_blender_name_dict and \
           finger2_name_jp in mmd_jp_to_blender_name_dict:
            hand_edit_bone = edit_bones[mmd_jp_to_blender_name_dict[hand_name_jp]]
            finger1_edit_bone = edit_bones[mmd_jp_to_blender_name_dict[finger1_name_jp]]
            finger2_edit_bone = edit_bones[mmd_jp_to_blender_name_dict[finger2_name_jp]]
            hand_edit_bone.tail = (finger1_edit_bone.head + finger2_edit_bone.head) / 2

    adjust_hand_bone('左手首', '左中指１', '左薬指１')
    adjust_hand_bone('右手首', '右中指１', '右薬指１')

    bpy.ops.object.mode_set(mode='OBJECT')

    # 设置层可见性
    #mmd_arm.data.layers[0]=True
    # 设置骨骼族颜色
    bone_group_color_map = {
        'Root':'THEME09',
        'センター':'THEME09',
        'ＩＫ':'THEME02',
        'IK':'THEME02',
        '上半身':'THEME04',
        '腕':'THEME03',
        '指':'THEME04',
        '足':'THEME03',
        '体(下)':'THEME04',
        '下半身':'THEME04',
    }

    # 已弃用设置骨骼组颜色
    """for bone_group in mmd_arm.pose.bone_groups:
        group_name = bone_group.name
        if group_name in bone_group_color_map:
            bone_group.color_set = bone_group_color_map[group_name]"""

    # 已弃用设置骨骼层
    for pose_bone in pose_bones:
        bone_data = pose_bone.bone
        name_j = pose_bone.mmd_bone.name_j

        """if pose_bone.bone_group and pose_bone.bone_group.name in bone_group_color_map:
            set_bone_layer(bone_data, 0)
        else:
            set_bone_layer(bone_data, 1)"""

        # 设置IK限制
        if name_j in arm_bone_dict:
            pose_bone.lock_location = [False, False, False]
            pose_bone.ik_stiffness_x = 0.1
            pose_bone.ik_stiffness_y = 0.1
            pose_bone.ik_stiffness_z = 0.1
            bone_setting = arm_bone_dict[name_j]

            if bone_setting[1]:
                pose_bone.lock_ik_x = False
                pose_bone.ik_min_x = bone_setting[1][0] or pose_bone.ik_min_x
                pose_bone.ik_max_x = bone_setting[1][1] or pose_bone.ik_max_x
            else:
                pose_bone.lock_ik_x = True
            if bone_setting[2]:
                pose_bone.lock_ik_y = False
                pose_bone.ik_min_y = bone_setting[2][0] or pose_bone.ik_min_y
                pose_bone.ik_max_y = bone_setting[2][1] or pose_bone.ik_max_y
            else:
                pose_bone.lock_ik_y = True
            if bone_setting[3]:
                pose_bone.lock_ik_z = False
                pose_bone.ik_min_z = bone_setting[3][0] or pose_bone.ik_min_z
                pose_bone.ik_max_z = bone_setting[3][1] or pose_bone.ik_max_z
            else:
                pose_bone.lock_ik_z = True

    # 为装饰设置骨骼弯曲
    world_rotate_params_list = [
        ['左ひじ', '左腕', (0, 1, 0), 0.2618],
        ['右ひじ', '右腕', (0, 1, 0), 0.2618],
    ]
    for params in world_rotate_params_list:
        if not (params[0] in mmd_jp_to_blender_name_dict and params[1] in mmd_jp_to_blender_name_dict):
            continue
        pose_bone_to_bend = pose_bones[mmd_jp_to_blender_name_dict[params[0]]]
        next_bone = pose_bones[mmd_jp_to_blender_name_dict[params[1]]]
        _apply_world_rotation_to_pose_bone(pose_bone_to_bend, next_bone, params[2], params[3])

    # 开启自动IK
    bpy.context.object.pose.use_auto_ik = True
    # 设置各自中心
    bpy.context.scene.tool_settings.transform_pivot_point = 'INDIVIDUAL_ORIGINS'

CLASS_LIST = []