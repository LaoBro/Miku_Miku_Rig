from types import prepare_class
import bpy
import os
import json

#骨骼枚举属性部分

bone_type_list=[
['None'],
['LowerBody','UpperBody','UpperBody2','Neck','Head'],
['Shoulder_L','Arm_L','Elbow_L','HandTwist_L','Wrist_L'],
['Thumb0_L','Thumb1_L','Thumb2_L'],
['IndexFinger1_L','IndexFinger2_L','IndexFinger3_L'],
['MiddleFinger1_L','MiddleFinger2_L','MiddleFinger3_L'],
['RingFinger1_L','RingFinger2_L','RingFinger3_L'],
['LittleFinger1_L','LittleFinger2_L','LittleFinger3_L'],
['Leg_L','Knee_L','Ankle_L','ToeTipIK_L'],
['LegIK_L'],
['LegTipEX_L'],
['Shoulder_R','Arm_R','Elbow_R','HandTwist_R','Wrist_R'],
['Thumb0_R','Thumb1_R','Thumb2_R'],
['IndexFinger1_R','IndexFinger2_R','IndexFinger3_R'],
['MiddleFinger1_R','MiddleFinger2_R','MiddleFinger3_R'],
['RingFinger1_R','RingFinger2_R','RingFinger3_R'],
['LittleFinger1_R','LittleFinger2_R','LittleFinger3_R'],
['Leg_R','Knee_R','Ankle_R','ToeTipIK_R'],
['LegIK_R'],
['LegTipEX_R'],
]

bone_type_name_list=[]
for x in bone_type_list:
    for y in x:
        bone_type_name_list.append(y)

bpy.types.PoseBone.mmr_bone_type=bpy.props.EnumProperty(
        items=[
            (name, name, '') for name in bone_type_name_list
        ],
        description=('Choose the bone type you want to use'),
        default = 0
    )

#骨架枚举属性部分

my_dir = os.path.dirname(os.path.realpath(__file__))
json_path = os.path.join(my_dir, "preset.json")
preset_name_list=[]
preset_dict_list=[]

def get_bone_type(pose):
    preset_dict={}
    for bone in pose.bones:
        if bone.mmr_bone_type!='None':
            preset_dict[bone.name]=bone.controller_type
    return(preset_dict)
    
def read_json():
    preset_list=[]
    if os.path.exists(json_path):
        with open(json_path, 'r',encoding='utf-8') as f:
            preset_list=json.load(f)
    else:
        with open(json_path, 'w') as f:
            json.dump([], f, indent=4)
    return(preset_list)

def write_json(preset_list):
    with open(json_path, "w", encoding='utf-8') as f:
        json.dump(preset_list, f, indent=4)

def read_preset():
    global preset_name_list
    global preset_dict_list
    preset_list=read_json()
    print(preset_list)
    preset_name_list=[preset[0] for preset in preset_list]
    preset_dict_list=[preset[1] for preset in preset_list]

def write_preset():
    preset_len=len(preset_name_list)
    preset_list=[(preset_name_list[i],preset_dict_list[i]) for i in range(preset_len)]
    print(preset_list)
    write_json(preset_list)


def add_preset(name,dict):
    if name not in preset_name_list:
        preset_name_list.append(name)
        preset_dict_list.append(dict)
        write_preset()

def delete_preset(name):
    if name in preset_name_list:
        index=preset_name_list.index(name)
        del preset_name_list[index]
        del preset_dict_list[index]
        write_preset()

def get_preset_item(self,context):
    preset_items=[('None','None','')]
    for name in preset_name_list:
        preset_items.append((name,name,''))
    return(preset_items)

read_preset()
#print(preset_name_list)
#print(preset_dict_list)

#操作器部分

class OT_Add_Preset(bpy.types.Operator):
    bl_idname = "mmr.add_preset" # python 提示
    bl_label = "Add Preset"
    bl_options = {'REGISTER', 'UNDO'}

    name:bpy.props.StringProperty(default='',description="新预设名称")


    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self,context):
        obj = context.object
        pose=obj.pose
        preset_dict=get_bone_type(pose)
        add_preset(self.name,preset_dict)
        return{"FINISHED"}

class OT_Delete_Preset(bpy.types.Operator):
    bl_idname = "mmr.delete_preset" # python 提示
    bl_label = "Delete Preset"
    bl_options = {'REGISTER', 'UNDO'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self,context):
        scene=context.scene
        mmr_property=scene.mmr_property
        delete_preset(mmr_property.preset_name_list)
        return{"FINISHED"}

#UI菜单部分

class MMR_Arm_Panel(bpy.types.Panel):
    bl_idname="MMR_PT_panel_12"
    bl_label = "MMR Arm Panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"
    

    @classmethod
    def poll(cls, context):
        if not context.object:
            return False
        return context.object.type == 'ARMATURE' and context.active_object.data.get("rig_id") is None

    def draw(self, context):
        C = context
        layout = self.layout
        obj = context.object
        scene=context.scene
        mmr_property=scene.mmr_property

        if obj.mode in {'POSE', 'OBJECT'}:

            row = layout.row()
            # Rig type field

            col = layout.column(align=True)
            col.active = (not 'rig_id' in C.object.data)

            col.separator()
            row = col.row()
            #row.operator("pose.rigify_generate", text="Generate Rig", icon='POSE_HLT')
            row.prop(mmr_property, 'preset_name_list', text='preset')
            row.operator("mmr.add_preset")
            row.operator("mmr.delete_preset")


class MMR_Bone_Panel(bpy.types.Panel):
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
        row.prop(pose_bone, 'mmr_bone_type', text='mmr_bone_type')
        row.prop_search(pose_bone, "mmr_bone_type", pose_bone, "mmr_bone_type", text="Rig type")

Class_list=[MMR_Bone_Panel,MMR_Arm_Panel,OT_Add_Preset,OT_Delete_Preset]
