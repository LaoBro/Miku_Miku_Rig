import bpy
import bmesh
from bpy.types import Operator
from . import rig

def alert_error(title,message):
    def draw(self,context):
        self.layout.label(text=str(message))
    bpy.context.window_manager.popup_menu(draw,title=title,icon='ERROR')

def hide_skirt():

    select_obj=bpy.context.selected_objects
    mmd_mesh_object=None
    mmd_arm=None
    mmd_parent=None
    select_rigid_body=[]
    select_mesh=[]

    for obj in select_obj:
        if obj.type=="MESH":
            for m in obj.modifiers:
                if m.type=='ARMATURE':
                    select_mesh.append(obj)
                    break
            if hasattr(obj,'mmd_rigid'):
                if obj.mmd_rigid.name != ''and obj.mmd_rigid.type != '0':
                    select_rigid_body.append(obj)

    if len(select_rigid_body)==0:
                    alert_error("提示","所选物体中没有MMD刚体")
                    return(False)

    mmd_parent=select_rigid_body[0].parent.parent

    for obj in mmd_parent.children:
        if obj.type=="ARMATURE":
            mmd_arm=obj
            mmd_mesh_object=mmd_arm.children[0]
    if mmd_mesh_object == None:
        alert_error("提示","所选刚体没有对应网格模型")
        return(False)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active=select_rigid_body[0]
    bpy.ops.mmd_tools.rigid_body_select(properties={'collision_group_number'})

    bones_list=[]

    for obj in bpy.context.selected_objects:
        if hasattr(obj,'mmd_rigid'):
            mmd_rigid=obj.mmd_rigid
            if mmd_rigid.name != ''and mmd_rigid.type != '0':
                bone=mmd_arm.pose.bones[obj.mmd_rigid.bone]
                bones_list.append(bone)


    #写入形变权重或骨骼约束
    #Add weight or constrain
    #准备阶段
    # preparation
    hide_vertex_group=None
    if 'mmd_hide_skirt' in mmd_mesh_object.vertex_groups.keys():
        hide_vertex_group=mmd_mesh_object.vertex_groups['mmd_hide_skirt']
    else:
        hide_vertex_group=mmd_mesh_object.vertex_groups.new(name='mmd_hide_skirt')
    to_index = hide_vertex_group.index
    mmd_mesh = mmd_mesh_object.data
    mmd_bm = bmesh.new()
    mmd_bm.from_mesh(mmd_mesh)

    mmd_bm.verts.layers.deform.verify()
    deform_layer = mmd_bm.verts.layers.deform.active

    for bone in bones_list:
        name=bone.name

        from_vertex_group = mmd_mesh_object.vertex_groups[name]
        from_index = from_vertex_group.index

        for vert in mmd_bm.verts:
            deform_vert = vert[deform_layer]
            if from_index not in deform_vert:
                continue

            deform_vert[to_index] = deform_vert.get(to_index, 0.0) + deform_vert[from_index]

    mmd_bm.to_mesh(mmd_mesh)
    mmd_bm.free()

    if 'mmd_hide_skirt' not in mmd_mesh_object.modifiers.keys():

        mod=mmd_mesh_object.modifiers.new('mmd_hide_skirt','MASK')
        mod.vertex_group = hide_vertex_group.name
        mod.invert_vertex_group = True

def set_min_ik_loop(arm,min_ik_loop=10):
    if rig.check_arm(arm)==False:
        return
    for bone in arm.pose.bones:
        for c in bone.constraints:
            if c.type=='IK':
                if c.iterations < min_ik_loop:
                    c.iterations=min_ik_loop
    return(True)

class OT_Set_Min_IK_Loop(Operator):
    bl_idname = "mmr.set_min_ik_loop" # python 提示
    bl_label = "Interface"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self,context):
        scene=context.scene
        mmr_property=scene.mmr_property
        set_min_ik_loop(context.view_layer.objects.active,mmr_property.min_ik_loop)
        return{"FINISHED"}

class OT_Hide_Skirt(Operator):
    bl_idname = "mmr.hide_skirt" # python 提示
    bl_label = "Interface"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self,context):
        hide_skirt()
        return{"FINISHED"}

Class_list=[OT_Set_Min_IK_Loop,OT_Hide_Skirt]