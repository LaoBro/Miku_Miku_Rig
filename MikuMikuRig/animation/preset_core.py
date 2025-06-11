import os
import json
import bpy

mmd_bone_type_list=[
'None',
'Root','Center','torso',
'LowerBody','UpperBody0','UpperBody','UpperBody2','Neck','Head',
'Eye_L','Eye_R',
'Shoulder_L','Arm_L','ArmTwist_L','Elbow_L','HandTwist_L','Wrist_L',
'Thumb0_L','Thumb1_L','Thumb2_L',
'IndexFinger1_L','IndexFinger2_L','IndexFinger3_L',
'MiddleFinger1_L','MiddleFinger2_L','MiddleFinger3_L',
'RingFinger1_L','RingFinger2_L','RingFinger3_L',
'LittleFinger1_L','LittleFinger2_L','LittleFinger3_L',
'Shoulder_R','Arm_R','ArmTwist_R','Elbow_R','HandTwist_R','Wrist_R',
'Thumb0_R','Thumb1_R','Thumb2_R',
'IndexFinger1_R','IndexFinger2_R','IndexFinger3_R',
'MiddleFinger1_R','MiddleFinger2_R','MiddleFinger3_R',
'RingFinger1_R','RingFinger2_R','RingFinger3_R',
'LittleFinger1_R','LittleFinger2_R','LittleFinger3_R',
'Leg_L','Knee_L','Ankle_L','ToeTipIK_L',
'LegIK_L',
'LegTipEX_L',
'Leg_R','Knee_R','Ankle_R','ToeTipIK_R',
'LegIK_R',
'LegTipEX_R',
]

rigify_bone_type_list=[
'None',
'Root',
'spine','spine.001','spine.002','spine.003','spine.004','spine.006',
'eye.L','eye.R',
'shoulder.L','upper_arm.L','ArmTwist_L','forearm.L','HandTwist_L','hand.L',
'thumb.01.L','thumb.02.L','thumb.03.L',
'f_index.01.L','f_index.02.L','f_index.03.L',
'f_middle.01.L','f_middle.02.L','f_middle.03.L',
'f_ring.01.L','f_ring.02.L','f_ring.03.L',
'f_pinky.01.L','f_pinky.02.L','f_pinky.03.L',
'shoulder.R','upper_arm.R','ArmTwist_R','forearm.R','HandTwist_R','hand.R',
'thumb.01.R','thumb.02.R','thumb.03.R',
'f_index.01.R','f_index.02.R','f_index.03.R',
'f_middle.01.R','f_middle.02.R','f_middle.03.R',
'f_ring.01.R','f_ring.02.R','f_ring.03.R',
'f_pinky.01.R','f_pinky.02.R','f_pinky.03.R',
'thigh.L','shin.L','foot.L','toe.L',
'thigh.R','shin.R','foot.R','toe.R',
]

bone_translate_dict_C={
    'None': '无', 
    'Root': '根骨骼', 'Center': '中心（重定向用骨骼）', 'torso': '躯干控制器（重定向用骨骼）', 
    'spine': '下半身', 'spine.001': '上半身0（非必要骨骼）', 'spine.002': '上半身1', 'spine.003': '上半身2', 'spine.004': '脖子', 'spine.006': '头', 'LowerBody':'下半身',
    'eye.L': '左眼（非必要骨骼）', 'eye.R': '右眼（非必要骨骼）', 
    'shoulder.L': '左肩膀', 'upper_arm.L': '左大臂', 'ArmTwist_L': '左大臂扭转骨骼（非必要骨骼）', 'forearm.L': '左小臂', 'HandTwist_L': '左小臂扭转骨骼（ 非必要骨骼）', 'hand.L': '左手腕', 
    'thumb.01.L': '左手大拇指0', 'thumb.02.L': '左手大拇指1', 'thumb.03.L': '左手大拇指2', 
    'f_index.01.L': '左手食指1', 'f_index.02.L': '左手食指2', 'f_index.03.L': '左手食指3', 
    'f_middle.01.L': '左手中指1', 'f_middle.02.L': ' 左手中指2', 'f_middle.03.L': '左手中指3', 
    'f_ring.01.L': '左手无名指1', 'f_ring.02.L': '左手无名指2', 'f_ring.03.L': '左手无名指3', 
    'f_pinky.01.L': '左手小拇指1', 'f_pinky.02.L': '左手小拇指2', 'f_pinky.03.L': '左手小拇指3', 
    'shoulder.R': '右肩膀', 'upper_arm.R': '右大臂', 'ArmTwist_R': '右大臂扭转骨骼（非必要骨骼）', 'forearm.R': '右小臂', 'HandTwist_R': '右小臂扭转骨骼（非必要骨骼）', 'hand.R': '右手腕', 
    'thumb.01.R': '右手大拇指0', 'thumb.02.R': '右手大拇指1', 'thumb.03.R': '右手大拇指2', 
    'f_index.01.R': '右手食指1', 'f_index.02.R': '右手食指2', 'f_index.03.R': '右手食指3', 
    'f_middle.01.R': '右手中指1', 'f_middle.02.R': '右手中指2', 'f_middle.03.R': '右手中指3', 
    'f_ring.01.R': '右手无名指1', 'f_ring.02.R': '右手无名指2', 'f_ring.03.R': '右手无名指3', 
    'f_pinky.01.R': '右手小拇指1', 'f_pinky.02.R': '右手小拇指2', 'f_pinky.03.R': '右手小拇指3', 
    'thigh.L': '左大腿', 'shin.L': '左小腿', 'foot.L': '左脚掌', 'toe.L': '左脚尖（非必要骨骼）', 'LegIK_L': '左腿IK骨骼（重定向用骨骼）', 'ToeTipIK_L': '左脚掌IK骨骼（非必要骨骼）', 
    'thigh.R': '右大腿', 'shin.R': '右小 腿', 'foot.R': '右脚掌', 'toe.R': '右脚尖（非必要骨骼）', 'LegIK_R': '右腿IK骨骼（非必要骨骼）', 'ToeTipIK_R': '右脚掌IK骨骼（重定向用骨骼）'
    }

built_in_rig_dict_list=['None','MMD_JP','MMD_EN','VRoid']
built_in_retarget_dict_list=['None','mixamo','Rigify','FBX动捕','BVH动捕']

my_dir = os.path.dirname(os.path.realpath(__file__))
json_path = os.path.join(my_dir, "preset.json")

preset_dict_dict = {
    'rig': {},
    'retarget': {}
}

def get_preset_data_from_pose(pose):
    """从活动骨架的姿态骨骼中提取MMR骨骼属性数据"""
    data = {}
    for bone in pose.bones:
        # 仅当骨骼类型被设置时才保存（不为None或空字符串）
        if bone.mmr_bone.bone_type and bone.mmr_bone.bone_type != 'None':
            data[bone.name] = [
                bone.mmr_bone.bone_type,
                bone.mmr_bone.invert,
                bone.mmr_bone.mass
            ]
    return data

def apply_preset_data_to_pose(pose, preset_data):
    """将预设数据应用到活动骨架的姿态骨骼上"""
    for bone in pose.bones:
        if bone.name in preset_data:
            values = preset_data[bone.name]
            bone.mmr_bone.bone_type = values[0]
            bone.mmr_bone.invert = values[1]
            if len(values) > 2:
                bone.mmr_bone.mass = values[2]
            else:
                # 如果预设中没有质量信息（可能来自旧版预设），则设为默认值
                bone.mmr_bone.mass = 1
        else:
             # 如果骨骼不在预设中，则重置其MMR属性
            bone.mmr_bone.bone_type = 'None'
            bone.mmr_bone.invert = False
            bone.mmr_bone.mass = 1
    
def read_json(preset_type):
    global preset_dict_dict
    if os.path.exists(json_path):
        with open(json_path, 'r',encoding='utf-8') as f:
            preset_dict_dict=json.load(f)
    else:
        with open(json_path, 'w') as f:
            json.dump(preset_dict_dict, f, indent=4, ensure_ascii=False)

def write_json(preset_type):
    with open(json_path, "w", encoding='utf-8') as f:
        json.dump(preset_dict_dict, f, indent=4)

def add_preset(name,preset,preset_type='rig'):
    preset_dict=preset_dict_dict[preset_type]
    if name and name not in preset_dict: #确保名称不为空
        preset_dict[name]=preset
        write_json(preset_type)

def delete_preset(name,preset_type='rig'):
    preset_dict=preset_dict_dict[preset_type]
    if name and name in preset_dict:
        del preset_dict[name]
        write_json(preset_type)

def overwrite_preset(name,preset,preset_type='rig'):
    preset_dict=preset_dict_dict[preset_type]
    if name and name in preset_dict:
        preset_dict[name]=preset
        write_json(preset_type)

def get_rig_preset_item(self,context):
    # 懒加载
    if not preset_dict_dict['rig']:
        read_json('rig')
    preset_items=[]
    for name in sorted(preset_dict_dict['rig'].keys()):
        preset_items.append((name,name,''))
    return(preset_items)

def get_retarget_preset_item(self,context):
    # 懒加载
    if not preset_dict_dict['retarget']:
        read_json('retarget')
    preset_items=[]    
    for name in sorted(preset_dict_dict['retarget'].keys()):
        preset_items.append((name,name,''))
    return(preset_items)

def set_keymap():
    wm = bpy.context.window_manager
    #kc= wm.keyconfigs['Blender user']
    kc= wm.keyconfigs.user
    km = kc.keymaps['3D View']
    for kmi in km.keymap_items:
        if kmi.type=='S' and kmi.shift==False and kmi.ctrl==False and kmi.alt==False:
            kmi.active=False
    km = kc.keymaps['Pose']
    for kmi in km.keymap_items:
        if kmi.type=='A' and kmi.shift==False and kmi.ctrl==False:
            kmi.active=False
    kmi = km.keymap_items.new('mmr.qa_assign', 'A', 'PRESS')
    kmi = km.keymap_items.new('mmr.qa_assign_invert', 'A', 'PRESS',alt=True)
    kmi = km.keymap_items.new('mmr.qa_skip', 'S', 'PRESS')

def reset_keymap():
    wm = bpy.context.window_manager
    #kc= wm.keyconfigs['Blender user']
    kc= wm.keyconfigs.user
    km = kc.keymaps['Pose']
    for kmi in km.keymap_items:
        if kmi.type=='A' and kmi.shift==False and kmi.ctrl==False:
            kmi.active=True
        if kmi.idname=='mmr.qa_assign' or kmi.idname== 'mmr.qa_assign_invert' or kmi.idname=='mmr.qa_skip':
            km.keymap_items.remove(kmi)
    km = kc.keymaps['3D View']
    for kmi in km.keymap_items:
        if kmi.type=='S' and kmi.shift==False and kmi.ctrl==False and kmi.alt==False:
            kmi.active=True

def QA_End(context):
    scene=context.scene
    mmr_property=scene.mmr_property
    mmr_property.quick_assign_mod=False
    mmr_property.quick_assign_index=1
    reset_keymap()
