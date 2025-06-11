import bpy
import bmesh
from ..base import alert_error, check_arm, apply_world_rotation_to_pose_bone

def hide_skirt():
    """
    根据选定的MMD刚体，自动隐藏关联MMD模型上的裙子部分。
    它通过创建一个顶点组并使用遮罩修改器来实现。
    """
    context = bpy.context
    selected_objects = context.selected_objects
    
    mmd_rigid_bodies = [
        obj for obj in selected_objects
        if hasattr(obj, 'mmd_rigid') and obj.mmd_rigid.name != '' and obj.mmd_rigid.type != '0'
    ]

    if not mmd_rigid_bodies:
        alert_error("提示", "所选物体中没有有效的MMD刚体")
        return False

    first_rigid_body = mmd_rigid_bodies[0]
    # MMD刚体通常被父级到一个代表骨骼的空物体，该空物体又被父级到模型根节点（另一个空物体）
    mmd_bone_empty = first_rigid_body.parent
    if not mmd_bone_empty or not mmd_bone_empty.parent:
        alert_error("错误", "无法确定MMD刚体的父级骨骼或模型根节点。")
        return False
    mmd_model_root = mmd_bone_empty.parent
    mmd_arm = None
    mmd_mesh_object = None

    # 在MMD模型根节点下查找骨架及其关联的网格
    for child in mmd_model_root.children:
        if child.type == 'ARMATURE':
            mmd_arm = child
            # 查找由此骨架变形的网格
            for mesh_candidate in mmd_arm.children:
                if mesh_candidate.type == 'MESH':
                    for modifier in mesh_candidate.modifiers:
                        if modifier.type == 'ARMATURE' and modifier.object == mmd_arm:
                            mmd_mesh_object = mesh_candidate
                            break
                    if mmd_mesh_object:
                        break
            # 如果找不到带有特定骨架修改器的网格，则选择第一个子网格作为后备
            if not mmd_mesh_object and mmd_arm.children:
                for mesh_candidate in mmd_arm.children:
                    if mesh_candidate.type == 'MESH':
                        mmd_mesh_object = mesh_candidate
                        break
            break

    if not mmd_arm:
        alert_error("错误", "在模型层级中找不到骨架对象。")
        return False
    if not mmd_mesh_object:
        alert_error("提示", "所选刚体没有对应网格模型或骨架没有子网格。")
        return False

    bpy.ops.object.select_all(action='DESELECT')
    context.view_layer.objects.active = first_rigid_body
    bpy.ops.mmd_tools.rigid_body_select(properties={'collision_group_number'})

    bones_list = []
    for obj in context.selected_objects: # 由 mmd_tools.rigid_body_select 选中的物体
        if hasattr(obj, 'mmd_rigid'):
            mmd_rigid_prop = obj.mmd_rigid
            if mmd_rigid_prop.name != '' and mmd_rigid_prop.type != '0':
                if mmd_rigid_prop.bone in mmd_arm.pose.bones:
                    bones_list.append(mmd_arm.pose.bones[mmd_rigid_prop.bone])
                else:
                    print(f"警告: 刚体 '{obj.name}' 关联的骨骼 '{mmd_rigid_prop.bone}' 在骨架 '{mmd_arm.name}' 中未找到。")

    #写入形变权重或骨骼约束
    #准备阶段
    hide_vertex_group = None
    if 'mmd_hide_skirt' in mmd_mesh_object.vertex_groups.keys():
        hide_vertex_group = mmd_mesh_object.vertex_groups.get('mmd_hide_skirt')
    else:
        hide_vertex_group = mmd_mesh_object.vertex_groups.new(name='mmd_hide_skirt')
    to_index = hide_vertex_group.index
    mmd_mesh_data = mmd_mesh_object.data
    mmd_bm = bmesh.new()
    mmd_bm.from_mesh(mmd_mesh_data)

    mmd_bm.verts.layers.deform.verify()
    deform_layer = mmd_bm.verts.layers.deform.active

    for bone in bones_list:
        name = bone.name

        from_vertex_group = mmd_mesh_object.vertex_groups.get(name)
        if not from_vertex_group:
            print(f"警告: 骨骼 '{name}' 对应的顶点组未在网格 '{mmd_mesh_object.name}' 上找到。")
            continue
        from_index = from_vertex_group.index

        for vert in mmd_bm.verts:
            deform_vert = vert[deform_layer]
            if from_index not in deform_vert:
                continue
            
            source_weight = deform_vert[from_index]
            if source_weight > 0.0:
                current_target_weight = deform_vert.get(to_index, 0.0)
                deform_vert[to_index] = min(current_target_weight + source_weight, 1.0) # 添加权重并确保不超过1.0（钳制）

    mmd_bm.to_mesh(mmd_mesh_data)
    mmd_bm.free()
    mmd_mesh_data.update()

    modifier_name = 'mmd_hide_skirt'
    if modifier_name not in mmd_mesh_object.modifiers:
        mod = mmd_mesh_object.modifiers.new(name=modifier_name, type='MASK')
        mod.vertex_group = hide_vertex_group.name
        mod.invert_vertex_group = True
    else:
        mod = mmd_mesh_object.modifiers[modifier_name]
        if mod.type == 'MASK':
            mod.vertex_group = hide_vertex_group.name # 确保设置正确
            mod.invert_vertex_group = True
        else:
            print(f"警告: 对象 '{mmd_mesh_object.name}' 上已存在名为 '{modifier_name}' 的修改器，但类型不是 MASK。")
    return True

def set_min_ik_loop(arm:bpy.types.Object, min_ik_loop=10):
    """
    设置骨架中所有IK约束的最小迭代次数。

    :param arm: 要修改的骨架对象。
    :param min_ik_loop: 要设置的最小IK迭代次数。
    """
    if not check_arm():
        return
    for bone in arm.pose.bones:
        for c in bone.constraints:
            if c.type == 'IK':
                if c.iterations < min_ik_loop:
                    c.iterations = min_ik_loop
    return True

def decorate_mmd_arm(context:bpy.types.Context):
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
        apply_world_rotation_to_pose_bone(pose_bone_to_bend, next_bone, params[2], params[3])

    # 开启自动IK
    bpy.context.object.pose.use_auto_ik = True
    # 设置各自中心
    bpy.context.scene.tool_settings.transform_pivot_point = 'INDIVIDUAL_ORIGINS'
