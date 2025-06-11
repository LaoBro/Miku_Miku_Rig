from ..base import MMRPanelBase
from . import preset_core

class MMR_Arm_Panel(MMRPanelBase):
    bl_idname="MMR_PT_panel_12"
    bl_label = "Controller Preset"
    bl_space_type = 'VIEW_3D' # Moved from base if it's specific to this panel group

    def draw(self, context):
        layout = self.layout
        scene=context.scene
        mmr_property = scene.mmr_property
        mmr_preset = scene.mmr_preset
        row = layout.row()
        # Rig type field
        if mmr_property.quick_assign_mod:
            bone_type = preset_core.rigify_bone_type_list[mmr_property.quick_assign_index]
            bone_type_C=''
            if bone_type in preset_core.bone_translate_dict_C:
                bone_type_C = preset_core.bone_translate_dict_C[bone_type]
            row = layout.row()
            row.label(text="正在指定骨骼：")
            row.label(text=bone_type,translate =False)
            row = layout.row()
            row.label(text=bone_type_C,translate =False)
            layout.operator("mmr.qa_assign",text='Assign (Hot Key:A)')
            layout.operator("mmr.qa_assign_invert",text='Assign Invert (Hot Key:Alt+A)')
            layout.operator("mmr.qa_skip",text='Skip (Hot Key:S)')
            layout.operator("mmr.qa_end",text='End Quick Assign')
        else:
            row.prop(mmr_preset, 'rig_preset_name', text='preset')
            if mmr_preset.rig_preset_name not in preset_core.built_in_rig_dict_list or mmr_property.debug:
                row = layout.row()
                row.operator("mmr.add_preset")
                row.operator("mmr.delete_preset")
                row = layout.row()
                row.operator("mmr.read_preset")
                row.operator("mmr.overwrite_preset")
            else:
                row = layout.row()
                row.operator("mmr.add_preset")
                row.operator("mmr.read_preset")
            layout.operator("mmr.rig_preset",text='Generate Rig with Preset')
            ot=layout.operator("mmr.rig_preset",text='Generate Rig Without Preset')
            ot.read=False
            layout.operator("mmr.qa_start",text='Start Quick Assign')
            layout.prop(mmr_property, "extra_options1", toggle=True,text='Extra Options')
            if mmr_property.extra_options1:
                layout.prop(mmr_property,'bent_IK_bone',text="Bent IK bone")

class MMR_Bone_Panel(MMRPanelBase):
    bl_idname="MMR_PT_panel_11"
    bl_label = 'MMR Bone Type'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'bone'

    @classmethod
    def poll(cls, context):
        return context.active_bone

    def draw(self, context):
        pose_bone = context.active_pose_bone or \
                    context.active_object.pose.bones.get(context.active_bone.name, None)
        if pose_bone is None:
            return

        layout = self.layout

        c = layout.column()

        row = c.row(align=True)
        layout.prop(pose_bone.mmr_bone, 'bone_type', text='Bone Type',translate =False)
        layout.prop(pose_bone.mmr_bone, 'invert', text='Invert')
        layout.prop(pose_bone.mmr_bone, 'mass', text='Mass')

class MMR_Retarget_Panel(MMRPanelBase):
    bl_idname="MMR_PT_panel_13"
    bl_label = "Retarget" #菜单名
    bl_space_type = 'VIEW_3D' # Moved from base

    def draw(self, context):
        scene = context.scene
        mmr_property = scene.mmr_property
        mmr_preset = scene.mmr_preset
        layout = self.layout
        row = layout.row()
        row.prop(mmr_preset, 'retarget_preset_name', text='preset')
        if mmr_preset.retarget_preset_name not in preset_core.built_in_retarget_dict_list or mmr_property.debug:
            row = layout.row()
            row.operator("mmr.add_preset").preset_type='retarget'
            row.operator("mmr.delete_preset").preset_type='retarget'
            row = layout.row()
            row.operator("mmr.read_preset").preset_type='retarget'
            row.operator("mmr.overwrite_preset").preset_type='retarget'
        else:
            row = layout.row()
            row.operator("mmr.add_preset").preset_type='retarget'
            row.operator("mmr.read_preset").preset_type='retarget'
        layout.label(text="Select rigify controller then press the button")
        #row=layout.row()
        #row.label(text='Arm:',translate =False)
        #row.prop(mmr_property, 'IKFK_arm',expand=True)
        #row=layout.row()
        #row.label(text='Leg:',translate =False)
        #row.prop(mmr_property, 'IKFK_leg',expand=True)
        layout.operator("mmr.import_mixamo",text="Import FBX/BVH")
        layout.operator("mmr.import_vmd",text="Import VMD")
        layout.operator("mmr.export_vmd",text="Bake and export VMD animation")
        layout.prop(mmr_property, "extra_options2", toggle=True,text='Extra Options')
        if mmr_property.extra_options2:
            layout.prop(mmr_property,'fade_in_out',text="Fade in out")
            layout.prop(mmr_property,'auto_action_scale',text="Auto animation scale")
            if mmr_property.auto_action_scale==False:
                layout.prop(mmr_property,'action_scale',text="Animation scale")
            layout.prop(mmr_property,'lock_location',text="Lock animation location")
            layout.prop(mmr_property,'import_as_NLA_strip',text="Import as NLA strip")

CLASS_LIST=[
    MMR_Arm_Panel,
    MMR_Bone_Panel,
    MMR_Retarget_Panel,
]