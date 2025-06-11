import bpy
import os
import logging
from ..base import check_arm, apply_world_rotation_to_pose_bone, alert_error
from . import preset_core

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

    # 保存当前活动对象和模式，以便后续恢复
    original_active_object = bpy.context.view_layer.objects.active
    original_active_object_mode = original_active_object.mode if original_active_object else 'OBJECT'

    # 确保操作对象处于正确的初始模式（对象模式）
    if generated_rig_obj.mode != 'OBJECT':
        bpy.context.view_layer.objects.active = generated_rig_obj
        bpy.ops.object.mode_set(mode='OBJECT')
    if source_arm_obj.mode != 'OBJECT':
        bpy.context.view_layer.objects.active = source_arm_obj
        bpy.ops.object.mode_set(mode='OBJECT')

    # 从目标骨架（生成的骨架）获取骨骼名称
    target_rig_bone_names = list(generated_rig_obj.data.bones.keys()) # 在对象模式下安全访问
    # 从源MMD骨架获取姿态骨骼映射，用于读取初始变换
    source_arm_pose_bones_map = source_arm_obj.pose.bones # 在对象模式下安全访问

    index_list = []

    # 第一遍：识别匹配的骨骼并为编辑模式操作做准备
    for i, constraint_tuple in enumerate(constraint_data_list):
        to_bone_name_in_target_rig = constraint_tuple[0]
        from_bone_type_in_source = constraint_tuple[1]

        if from_bone_type_in_source not in source_arm_preset_dict:
            continue
        
        from_bone_name_in_source = source_arm_preset_dict[from_bone_type_in_source]

        if from_bone_name_in_source in source_arm_pose_bones_map and \
           to_bone_name_in_target_rig in target_rig_bone_names:
            match_bone_number += 1
            index_list.append(i)
            # 如果MMD骨骼是约束的一部分，则取消隐藏
            if from_bone_name_in_source in source_arm_obj.data.bones: # 检查是否存在于 data.bones 中
                 source_arm_obj.data.bones[from_bone_name_in_source].hide = False
    
    if not index_list: # 如果没有匹配的骨骼，则提前返回
        bpy.context.view_layer.objects.active = original_active_object # 恢复活动对象
        if original_active_object and original_active_object.mode != original_active_object_mode: bpy.ops.object.mode_set(mode=original_active_object_mode) # 恢复模式
        return 0

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
        source_pose_bone = source_arm_pose_bones_map.get(from_bone_name_in_source)
        if not source_pose_bone:
            print(f"警告: 在编辑模式准备阶段未找到源姿态骨骼 {from_bone_name_in_source}。")
            continue

        parent_bone.matrix = source_pose_bone.matrix # 世界空间矩阵
        parent_bone.tail = source_pose_bone.tail # 世界空间尾部
        
        parent_bone.parent = target_rig_edit_bones[to_bone_name_in_target_rig]
        # 清除 parent_bone 现有的集合
        for coll in list(parent_bone.collections): # 迭代副本以安全地取消链接
            coll.unassign(parent_bone)
        # 从目标骨骼复制集合
        for coll in target_rig_edit_bones[to_bone_name_in_target_rig].collections:
            coll.assign(parent_bone)

    # 退出 generated_rig_obj 的编辑模式，使其更改生效
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.view_layer.update() # 关键：更新依赖关系图，使新骨骼在姿态模式中可用

    # 切换到 source_arm_obj 以添加约束
    bpy.context.view_layer.objects.active = source_arm_obj
    bpy.ops.object.mode_set(mode='POSE')
    # 在姿态模式下为 source_arm_obj 获取最新的姿态骨骼
    source_arm_pose_bones_for_constraints = source_arm_obj.pose.bones

    for i in index_list:
        constraint_tuple = constraint_data_list[i]
        from_bone_type_str = constraint_data_list[i][1]
        rotation_flag = constraint_tuple[2]
        location_flag = constraint_tuple[3]

        from_bone_name_in_source = source_arm_preset_dict[from_bone_type_str]
        source_pose_bone_to_constrain = source_arm_pose_bones_for_constraints.get(from_bone_name_in_source)

        if not source_pose_bone_to_constrain:
            print(f"警告: 添加约束时未找到源姿态骨骼 {from_bone_name_in_source}。")
            continue

        constraints_obj = source_pose_bone_to_constrain.constraints
        # 清除之前由该脚本添加的同名约束
        for c in list(constraints_obj): # 遍历副本以允许安全删除
            if c.name.startswith("rel_"):
                constraints_obj.remove(c)
            
        parent_name_in_target_rig = from_bone_type_str + '_parent'

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
        
        # 在约束设置后隐藏 generated_rig_obj 中的父骨骼
        if parent_name_in_target_rig in generated_rig_obj.pose.bones:
            generated_rig_obj.pose.bones[parent_name_in_target_rig].bone.hide = True
        elif parent_name_in_target_rig in generated_rig_obj.data.bones: # 作为备选
            generated_rig_obj.data.bones[parent_name_in_target_rig].hide = True

    # 恢复原始活动对象和模式
    bpy.context.view_layer.objects.active = original_active_object
    if original_active_object and bpy.context.object.mode != original_active_object_mode:
        # 只有当真实模式与记录模式不同时才切换，避免不必要的模式切换
        if original_active_object.mode != original_active_object_mode :
            bpy.ops.object.mode_set(mode=original_active_object_mode)

    bpy.context.view_layer.update()
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
    #extra.set_min_ik_loop(mmd_arm, 10)

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
        mmr_bone = bone.mmr_bone
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
            apply_world_rotation_to_pose_bone(pose_bone_to_bend, next_bone, params[2], params[3])

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
        mmr_bone = bone.mmr_bone
        bone_type = mmr_bone.bone_type
        if bone_type != "None" and bone_type in current_rigify_edit_bones_names:
            rigify_edit_bone = rigify_arm.data.edit_bones[bone_type]
            if mmr_bone.invert:
                rigify_edit_bone.tail = bone.head
            else:
                rigify_edit_bone.tail = bone.tail

    for bone in mmd_arm.pose.bones:
        mmr_bone = bone.mmr_bone
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
    #current_rigify_edit_bones_names = list(rigify_arm.data.edit_bones.keys()) # 如果名称已更改，则刷新

    def _calculate_bone_rolls_for_types(edit_bones_map, bone_type_list, roll_calculation_type):
        bpy.ops.armature.select_all(action='DESELECT')
        selected_at_least_one = False
        for bone_name_key in bone_type_list:
            if bone_name_key in edit_bones_map:
                bone_to_roll = edit_bones_map[bone_name_key]
                bone_to_roll.select = True
                bone_to_roll.select_head = True # Needed for some roll calculations
                bone_to_roll.select_tail = True # Needed for some roll calculations
                selected_at_least_one = True
        if selected_at_least_one:
            bpy.ops.armature.calculate_roll(type=roll_calculation_type)
        bpy.ops.armature.select_all(action='DESELECT') # Clean up selection

    _calculate_bone_rolls_for_types(rigify_edit_bones, positive_z_bone_types, 'GLOBAL_POS_Z')
    _calculate_bone_rolls_for_types(rigify_edit_bones, positive_x_bone_types, 'GLOBAL_POS_X')
    _calculate_bone_rolls_for_types(rigify_edit_bones, negative_x_bone_types, 'GLOBAL_NEG_X')
    _calculate_bone_rolls_for_types(rigify_edit_bones, negative_y_bone_types, 'GLOBAL_NEG_Y')


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

    # 将IK拉伸设为0
    # set IK stretch to 0
    rig.pose.bones["upper_arm_parent.L"]["IK_Stretch"] = 0
    rig.pose.bones["upper_arm_parent.R"]["IK_Stretch"] = 0
    rig.pose.bones["thigh_parent.L"]["IK_Stretch"] = 0
    rig.pose.bones["thigh_parent.R"]["IK_Stretch"] = 0

    # 写入MMR骨骼预设
    rigify_preset = preset_core.preset_dict_dict['retarget']['Rigify']
    preset_core.apply_preset_data_to_pose(rig.pose, rigify_preset) # 从 set_bone_type 更改

    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')

    # 隐藏原骨架，把新骨架设为永远在前
    # hide old armature
    rig.show_in_front = True
    mmd_arm.hide_set(True)
    rig.name = mmd_arm.name + '_Rig'

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

    # 将轴心设为各自中点以方便操作
    # set transform pivot point to individual
    bpy.context.view_layer.objects.active = rig
    rig.select_set(True)
    bpy.context.scene.tool_settings.transform_pivot_point = 'INDIVIDUAL_ORIGINS'
    bpy.context.area.type = area
    logging.info(f"完成 匹配骨骼数:{match_bone_number}")
    alert_error("提示", f"完成 匹配骨骼数:{match_bone_number}")
    return True
