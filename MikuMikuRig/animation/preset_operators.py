# pyright: reportInvalidTypeForm=false
import bpy
from bpy.types import Operator
from bpy.props import BoolProperty, StringProperty
from..base import check_arm
from . import preset_core, rig_core

class OT_Add_Preset(Operator):
    bl_idname = "mmr.add_preset" # python 提示
    bl_label = "Add Preset"
    bl_options = {'REGISTER', 'UNDO'}

    name: StringProperty(default='',description="新预设名称")
    preset_type: StringProperty(default='rig',description="预设类型")

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.prop(self,'name',text="Preset Name")

    def execute(self,context):
        if check_arm()==False:
            return{"CANCELLED"}
        if not self.name.strip():
            self.report({'WARNING'}, "预设名称不能为空")
            return {"CANCELLED"}
        active_obj = context.active_object
        pose = active_obj.pose
        preset_data = preset_core.get_preset_data_from_pose(pose)
        preset_core.add_preset(self.name, preset_data, self.preset_type)
        return{"FINISHED"}

class OT_Delete_Preset(Operator):
    bl_idname = "mmr.delete_preset" # python 提示
    bl_label = "Delete Preset"
    bl_options = {'REGISTER', 'UNDO'}

    preset_type: StringProperty(default='rig',description="预设类型")

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.label(text="真的要删除预设吗？")

    def execute(self,context):
        scene=context.scene
        mmr_preset = scene.mmr_preset
        if self.preset_type == 'rig':
            name = mmr_preset.rig_preset_name
        elif self.preset_type == 'retarget':
            name = mmr_preset.retarget_preset_name
        if not name:
            self.report({'WARNING'}, "没有选择要删除的预设")
            return {"CANCELLED"}
        preset_core.delete_preset(name, self.preset_type)
        return{"FINISHED"}

class OT_Read_Preset(Operator):
    bl_idname = "mmr.read_preset" # python 提示
    bl_label = "Read Preset"
    bl_options = {'REGISTER', 'UNDO'}

    preset_type: StringProperty(default='rig',description="预设类型")

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.label(text="真的要读取预设吗？")

    def execute(self,context):
        scene=context.scene
        mmr_preset=scene.mmr_preset
        if check_arm()==False:
            return{"CANCELLED"}
        active_obj = context.active_object
        pose = active_obj.pose
        preset_dict = preset_core.preset_dict_dict[self.preset_type]
        if self.preset_type == 'rig':
            name = mmr_preset.rig_preset_name
        elif self.preset_type == 'retarget':
            name = mmr_preset.retarget_preset_name
        if not name or name not in preset_dict:
            self.report({'WARNING'}, f"预设 '{name}' 未找到")
            return {"CANCELLED"}
        preset_data = preset_dict[name]
        preset_core.apply_preset_data_to_pose(pose, preset_data)
        return{"FINISHED"}

class OT_Overwrite_Preset(Operator):
    bl_idname = "mmr.overwrite_preset" # python 提示
    bl_label = "Overwrite Preset"
    bl_options = {'REGISTER', 'UNDO'}

    preset_type: StringProperty(default='rig',description="预设类型")

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.label(text="真的要覆盖预设吗？")

    def execute(self,context):
        scene=context.scene
        mmr_preset=scene.mmr_preset
        if check_arm()==False:
            return{"CANCELLED"}
        active_obj = context.active_object
        pose = active_obj.pose
        preset_data = preset_core.get_preset_data_from_pose(pose)
        
        if self.preset_type == 'rig':
            name = mmr_preset.rig_preset_name
        elif self.preset_type == 'retarget':
            name = mmr_preset.retarget_preset_name
        if not name:
            self.report({'WARNING'}, "没有选择要覆盖的预设")
            return {"CANCELLED"}
        preset_core.overwrite_preset(name, preset_data, self.preset_type)
        return{"FINISHED"}

class OT_Rig_Preset(Operator):
    bl_idname = "mmr.rig_preset" # python 提示
    bl_label = "Rig Preset"
    bl_options = {'REGISTER', 'UNDO'}

    read: BoolProperty(default=True,description="读取预设")

    def execute(self,context):
        scene=context.scene
        mmr_preset=scene.mmr_preset
        if check_arm()==False:
            return{"CANCELLED"}
        active_obj = context.active_object
        pose = active_obj.pose
        if self.read:
            preset_dict = preset_core.preset_dict_dict['rig']
            preset_name = mmr_preset.rig_preset_name
            if preset_name and preset_name in preset_dict:
                preset_data = preset_dict[preset_name]
                preset_core.apply_preset_data_to_pose(pose, preset_data)
            else:
                self.report({'WARNING'}, f"预设 '{preset_name}' 未找到，将不应用预设生成控制器。")
        rig_core.RIG2(context)
        return{"FINISHED"}

class OT_QA_Start(Operator):
    bl_idname = "mmr.qa_start" # python 提示
    bl_label = "QA Start"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self,context):
        scene=context.scene
        mmr_property=scene.mmr_property
        if check_arm()==False:
            return{"CANCELLED"}
        mmr_property.quick_assign_mod=True
        mmr_property.quick_assign_index=1
        preset_core.set_keymap()
        
        bpy.ops.object.mode_set(mode = 'POSE')
        bpy.ops.pose.select_all(action='DESELECT')
        first_bone=context.view_layer.objects.active.data.bones[0]
        first_bone.select=True
        context.view_layer.objects.active.data.bones.active=first_bone

        return{"FINISHED"}

class OT_QA_End(Operator):
    bl_idname = "mmr.qa_end" # python 提示
    bl_label = "QA End"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self,context):
        preset_core.QA_End(context)
        
        return{"FINISHED"}

class OT_QA_Assign(Operator):
    bl_idname = "mmr.qa_assign" # python 提示
    bl_label = "QA Assign"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self,context):
        scene=context.scene
        mmr_property=scene.mmr_property
        if mmr_property.quick_assign_mod==False:
            return{"FINISHED"}

        pose_bone = context.active_pose_bone or \
                    context.active_object.pose.bones.get(context.active_bone.name, None)
        if pose_bone is None:
            return{"FINISHED"}

        bone=pose_bone.bone
        if len(bone.children)!=0:
            child_bone=bone.children[0]
            bone.select=False
            child_bone.select=True
            context.view_layer.objects.active.data.bones.active=child_bone

        bone_type=preset_core.rigify_bone_type_list[mmr_property.quick_assign_index]

        pose_bone.mmr_bone.bone_type = bone_type
        pose_bone.mmr_bone.invert = False

        mmr_property.quick_assign_index+=1
        if mmr_property.quick_assign_index >= len(preset_core.rigify_bone_type_list):
            preset_core.QA_End(context)
        
        return{"FINISHED"}

class OT_QA_Assign_Invert(Operator):
    bl_idname = "mmr.qa_assign_invert" # python 提示
    bl_label = "QA Assign Invert"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self,context):
        scene=context.scene
        mmr_property=scene.mmr_property
        if mmr_property.quick_assign_mod==False:
            return{"FINISHED"}

        pose_bone = context.active_pose_bone or \
                    context.active_object.pose.bones.get(context.active_bone.name, None)
        if pose_bone is None:
            return{"FINISHED"}

        bone=pose_bone.bone
        if len(bone.children)!=0:
            child_bone=bone.children[0]
            bone.select=False
            child_bone.select=True
            context.view_layer.objects.active.data.bones.active=child_bone

        bone_type=preset_core.rigify_bone_type_list[mmr_property.quick_assign_index]

        pose_bone.mmr_bone.bone_type = bone_type
        pose_bone.mmr_bone.invert = True

        mmr_property.quick_assign_index+=1
        if mmr_property.quick_assign_index >= len(preset_core.rigify_bone_type_list):
            preset_core.QA_End(context)
        
        return{"FINISHED"}

class OT_QA_Skip(Operator):
    bl_idname = "mmr.qa_skip" # python 提示
    bl_label = "QA Skip"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self,context):
        scene=context.scene
        mmr_property=scene.mmr_property

        pose_bone = context.active_pose_bone or \
                    context.active_object.pose.bones.get(context.active_bone.name, None)

        bone=pose_bone.bone
        bone.select=False
        bone.select=True

        if mmr_property.quick_assign_mod==False:
            return{"FINISHED"}
        mmr_property.quick_assign_index+=1
        if mmr_property.quick_assign_index >= len(preset_core.rigify_bone_type_list):
            preset_core.QA_End(context)

        return{"FINISHED"}

CLASS_LIST = [
    OT_Add_Preset,
    OT_Delete_Preset,
    OT_Read_Preset,
    OT_Overwrite_Preset,
    OT_Rig_Preset,
    OT_QA_Start,
    OT_QA_End,
    OT_QA_Assign,
    OT_QA_Assign_Invert,
    OT_QA_Skip
]