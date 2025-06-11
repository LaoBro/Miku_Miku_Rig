import bpy
import bmesh
from bpy.types import Operator
from . import rig
from ..base import alert_error

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
    if not rig.check_arm():
        return
    for bone in arm.pose.bones:
        for c in bone.constraints:
            if c.type == 'IK':
                if c.iterations < min_ik_loop:
                    c.iterations = min_ik_loop
    return True

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
        set_min_ik_loop(context.view_layer.objects.active, mmr_property.min_ik_loop)
        return {"FINISHED"}

class OT_Hide_Skirt(Operator):
    """
    根据选定的MMD刚体隐藏裙子的操作器。
    """
    bl_idname = "mmr.hide_skirt" # python 提示
    bl_label = "Interface"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        hide_skirt()
        return {"FINISHED"}

class OT_Decorate_MMD_Arm(Operator):
    """
    美化MMD骨架的操作器，调整骨骼连接、轴向、IK限制等。
    """
    bl_idname = "mmr.decorate_mmd_arm" # python 提示
    bl_label = "Interface"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        rig.decorate_mmd_arm(context)
        return {"FINISHED"}

CLASS_LIST = [OT_Set_Min_IK_Loop, OT_Hide_Skirt, OT_Decorate_MMD_Arm]