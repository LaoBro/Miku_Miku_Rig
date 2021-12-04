import bpy
import os
import logging
import numpy as np
from bpy.types import Operator

def alert_error(title,message):
    def draw(self,context):
        self.layout.label(text=str(message))
    bpy.context.window_manager.popup_menu(draw,title=title,icon='ERROR')

def check_arm():
    
    arm=bpy.context.view_layer.objects.active

    if 'rigify' not in bpy.context.preferences.addons.keys():
        logging.info("检测到未开启rigify，已自动开启")
        alert_error("提示","检测到未开启rigify，已自动开启")
        bpy.ops.preferences.addon_enable(module="rigify")

    if arm==None:
        logging.info("未选择骨骼！")
        alert_error("提示","未选择骨骼！")
        return(False)

    elif arm.type!='ARMATURE':
        logging.info("所选对象不是骨骼！")
        alert_error("提示","所选对象不是骨骼！")
        return(False) 

    return (True)

def load_pose():
    my_dir = os.path.dirname(os.path.realpath(__file__))
    vpd_file = os.path.join(my_dir, "MMR_Rig_pose.vpd")
    print(my_dir)
    print(vpd_file)
    bpy.ops.mmd_tools.import_vpd(filepath=vpd_file, files=[{"name":"MMR_Rig_pose.vpd", "name":"MMR_Rig_pose.vpd"}], directory=my_dir)
    bpy.ops.object.mode_set(mode = 'OBJECT')

def add_constraint2(constraint_List):

    index_list=[]
    bpy.ops.object.mode_set(mode = 'POSE')

    for i,tuple in enumerate(constraint_List):
        To=tuple[0]
        From=tuple[1]
        rotation=tuple[2]
        location=tuple[3]
        if From in mmd_bones_list and To in rig_bones_list:
            if rotation:
                index_list.append(i)
            elif location:
                COPY_LOCATION=mmd_arm.pose.bones[From].constraints.new(type='COPY_LOCATION')
                COPY_LOCATION.target = rig
                COPY_LOCATION.subtarget = To
                COPY_LOCATION.name="rel_location"
            mmd_arm.data.bones[From].hide=False

    bpy.ops.object.mode_set(mode = 'EDIT')

    for i in index_list:
        From = constraint_List[i][1]
        To = constraint_List[i][0]
        parent_name=From + '_parent'
        parent_bone=rig.data.edit_bones.new(name=parent_name)
        parent_bone.head=mmd_arm2.data.edit_bones[From].head
        parent_bone.tail=mmd_arm2.data.edit_bones[From].tail
        parent_bone.roll=mmd_arm2.data.edit_bones[From].roll
        parent_bone.parent=rig.data.edit_bones[To]

    bpy.ops.object.mode_set(mode = 'POSE')

    for i in index_list:
        From = constraint_List[i][1]
        To = constraint_List[i][0]
        location=constraint_List[i][3]
        con= mmd_arm.pose.bones[From].constraints
        for c in con:
            c.mute=True
        parent_name=From + '_parent'
        rig.data.bones[parent_name].hide=True
        if location:
            COPY_TRANSFORMS=con.new(type='COPY_TRANSFORMS')
            COPY_TRANSFORMS.target = rig
            COPY_TRANSFORMS.subtarget = parent_name
            COPY_TRANSFORMS.name="rel_transforms"
            COPY_TRANSFORMS.mix_mode = 'REPLACE'
            COPY_TRANSFORMS.owner_space = 'WORLD'
            COPY_TRANSFORMS.target_space = 'WORLD'
        else:
            COPY_TRANSFORMS=con.new(type='COPY_ROTATION')
            COPY_TRANSFORMS.target = rig
            COPY_TRANSFORMS.subtarget = parent_name
            COPY_TRANSFORMS.name="rel_rotation"

def add_constraint3(constraint_List,preset_dict):

    index_list=[]
    bpy.ops.object.mode_set(mode = 'POSE')

    for i,tuple in enumerate(constraint_List):
        To=tuple[0]
        From=tuple[1]
        rotation=tuple[2]
        location=tuple[3]

        if From not in preset_dict:
            continue

        From=preset_dict[From]

        if From in mmd_bones_list and To in rig_bones_list:
            if rotation:
                index_list.append(i)
            elif location:
                COPY_LOCATION=mmd_arm.pose.bones[From].constraints.new(type='COPY_LOCATION')
                COPY_LOCATION.target = rig
                COPY_LOCATION.subtarget = To
                COPY_LOCATION.name="rel_location"
            mmd_arm.data.bones[From].hide=False

    bpy.ops.object.mode_set(mode = 'EDIT')

    for i in index_list:
        From = preset_dict[constraint_List[i][1]]
        From1=constraint_List[i][1]
        To = constraint_List[i][0]
        parent_name=From1 + '_parent'
        parent_bone=rig.data.edit_bones.new(name=parent_name)
        parent_bone.head=mmd_arm2.data.edit_bones[From].head
        parent_bone.tail=mmd_arm2.data.edit_bones[From].tail
        parent_bone.roll=mmd_arm2.data.edit_bones[From].roll
        parent_bone.parent=rig.data.edit_bones[To]

    bpy.ops.object.mode_set(mode = 'POSE')

    for i in index_list:
        From = preset_dict[constraint_List[i][1]]
        From1=constraint_List[i][1]
        To = constraint_List[i][0]
        location=constraint_List[i][3]
        con= mmd_arm.pose.bones[From].constraints
        for c in con:
            c.mute=True
        parent_name=From1 + '_parent'
        rig.data.bones[parent_name].hide=True
        if location:
            COPY_TRANSFORMS=con.new(type='COPY_TRANSFORMS')
            COPY_TRANSFORMS.target = rig
            COPY_TRANSFORMS.subtarget = parent_name
            COPY_TRANSFORMS.name="rel_transforms"
            COPY_TRANSFORMS.mix_mode = 'REPLACE'
            COPY_TRANSFORMS.owner_space = 'WORLD'
            COPY_TRANSFORMS.target_space = 'WORLD'
        else:
            COPY_TRANSFORMS=con.new(type='COPY_ROTATION')
            COPY_TRANSFORMS.target = rig
            COPY_TRANSFORMS.subtarget = parent_name
            COPY_TRANSFORMS.name="rel_rotation"


def RIG(context):

    #属性准备阶段
    global mmd_arm
    global mmd_arm2
    global rig
    global mmd_bones_list
    global rig_bones_list

    mmd_arm=context.view_layer.objects.active

    scene=context.scene
    mmr_property=scene.mmr_property

    my_dir = os.path.dirname(os.path.realpath(__file__))
    rigify_blend_file = os.path.join(my_dir, "MMR_Rig.blend")

    bpy.ops.object.mode_set(mode = 'OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    context.view_layer.objects.active=mmd_arm
    mmd_arm.select_set(True)

    #检查骨架并翻译
    if check_arm()==False:
        return{False}
    bpy.ops.mmd_tools.translate_mmd_model(dictionary='INTERNAL', types={'BONE'}, modes={'MMD', 'BLENDER'})

    #建立骨骼关系字典
    mmd_bones_dict_j={}
    mmd_bones_dict_e={}
    for bone in mmd_arm.pose.bones:
        bone.bone.hide=True
        if bone.mmd_bone.name_e not in mmd_bones_dict_e:
            mmd_bones_dict_e[bone.mmd_bone.name_e]=bone.name
        if bone.mmd_bone.name_j not in mmd_bones_dict_j:
            mmd_bones_dict_j[bone.mmd_bone.name_j]=bone.name

    load_pose()
    bpy.ops.object.select_all(action='DESELECT')

    #替换特殊名称骨骼
    mmd_bones_list=mmd_arm.data.bones.keys()
    if "UpperBodyB" in mmd_bones_list:
        mmd_arm.data.bones["UpperBodyB"].name="UpperBody2"
        mmd_bones_list=mmd_arm.data.bones.keys()


    #生成第二套骨骼
    mmd_arm2=mmd_arm.copy()
    context.collection.objects.link(mmd_arm2)
    mmd_arm2.data=mmd_arm.data.copy()
    context.view_layer.objects.active=mmd_arm2
    bpy.ops.object.mode_set(mode = 'POSE')
    bpy.ops.pose.armature_apply(selected=False)
    bpy.ops.object.mode_set(mode = 'OBJECT')


    #导入metarig骨骼
    #import metarig armature
    rigify_arm_name="MMR_Rig_relative"
    
    with bpy.data.libraries.load(rigify_blend_file) as (data_from, data_to):
        data_to.objects = [rigify_arm_name]

    rigify_arm=data_to.objects[0]
    context.collection.objects.link(rigify_arm)

    bpy.context.view_layer.objects.active=rigify_arm
    bpy.ops.object.mode_set(mode = 'EDIT')
    bpy.ops.armature.select_all(action='DESELECT')

    #修正只有两节拇指骨骼的模型
    if "Thumb1_L" in mmd_bones_list:
        if mmd_arm.data.bones["Thumb1_L"].parent.name !="Thumb0_L":
            rigify_arm.data.edit_bones.remove(rigify_arm.data.edit_bones["Thumb2_L"])
            rigify_arm.data.edit_bones["Thumb1_L"].name='Thumb2_L'
            rigify_arm.data.edit_bones["Thumb0_L"].name='Thumb1_L'

    if "Thumb1_R" in mmd_bones_list:
        if mmd_arm.data.bones["Thumb1_R"].parent.name !="Thumb0_R":
            rigify_arm.data.edit_bones.remove(rigify_arm.data.edit_bones["Thumb2_R"])
            rigify_arm.data.edit_bones["Thumb1_R"].name='Thumb2_R'
            rigify_arm.data.edit_bones["Thumb0_R"].name='Thumb1_R'

    rigify_bones_list=rigify_arm.data.edit_bones.keys()
    disconnect_bone_set=set(mmd_bones_list).intersection(rigify_bones_list)
    exist_bones=list(disconnect_bone_set)

    #新骨骼匹配方法

    roll_list=[]
    vector_list=[]
    length_list=[]
    disconnect_bone_set=set(exist_bones)

    for name in exist_bones:
        rigify_bone=rigify_arm.data.edit_bones[name]
        offset=np.array(rigify_bone.tail)-np.array(rigify_bone.head)
        vector_list.append(offset)
        length_list.append(rigify_bone.length)
        roll_list.append(rigify_bone.roll)

    for name in exist_bones:
        rigify_bone=rigify_arm.data.edit_bones[name]
        mmd_bone=mmd_arm2.pose.bones[name]
        rigify_bone.head=mmd_bone.head

        if rigify_bone.parent!=None and rigify_bone.use_connect:
            parent_name=rigify_bone.parent.name
            disconnect_bone_set.discard(parent_name)

    for name in disconnect_bone_set:
        rigify_bone=rigify_arm.data.edit_bones[name]
        if rigify_bone.parent!=None and rigify_bone.parent.name in exist_bones:
            parent_bone=rigify_bone.parent
            parent_index=exist_bones.index(parent_bone.name)
            index=exist_bones.index(rigify_bone.name)
            offset=vector_list[index]/length_list[parent_index]*parent_bone.length
            rigify_bone.tail=np.array(rigify_bone.head)+offset

    #修正部分骨骼

    rigify_arm.data.edit_bones["UpperBody2"].tail=mmd_arm2.pose.bones["Neck"].head
    rigify_arm.data.edit_bones["LowerBody"].head=mmd_arm2.pose.bones["LowerBody"].tail
    rigify_arm.data.edit_bones["LowerBody"].tail=mmd_arm2.pose.bones["LowerBody"].head
    if mmd_arm2.pose.bones["LowerBody"].head==mmd_arm2.pose.bones["UpperBody"].head:
        rigify_arm.data.edit_bones["LowerBody"].tail[2]-=0.01
    #rigify_arm.data.edit_bones["Head"].tail=mmd_arm2.pose.bones["Head"].tail
    rigify_arm.data.edit_bones["Neck_Middle"].head=(np.array(mmd_arm2.pose.bones["Neck"].head)+np.array(mmd_arm2.pose.bones["Head"].head))/2

    #调整缺失UpperBody2情况
    no_UpperBody2=False
    if 'UpperBody2' not in mmd_bones_list and 'UpperBody' in mmd_bones_list:
        no_UpperBody2=True
        rigify_arm.data.edit_bones['UpperBody2'].head=np.array(mmd_arm2.pose.bones["UpperBody"].head)+np.array([0.001,0.001,0.001])
        rigify_arm.data.edit_bones['UpperBody'].name='UpperBody3'
        rigify_arm.data.edit_bones['UpperBody2'].name='UpperBody'
        #rigify_arm.data.edit_bones['UpperBody2'].tail = np.array(rigify_arm.data.edit_bones['UpperBody2'].head)+np.array([0.001,0.001,0.001])

    bpy.ops.object.mode_set(mode = 'POSE')
    head_scale=mmd_arm2.pose.bones["Head"].length/rigify_arm.pose.bones["Head"].length
    rigify_arm.pose.bones["Head"].scale=[head_scale,head_scale,head_scale]
    bpy.ops.pose.armature_apply(selected=False)
    bpy.ops.object.mode_set(mode = 'EDIT')

    #匹配眼睛骨骼
    invert_eyes=False
    if 'Eye_L' in mmd_bones_list and 'Eye_R' in mmd_bones_list:
        eye_L=rigify_arm.data.edit_bones['eye.L']
        mmd_eye_L=mmd_arm2.pose.bones['Eye_L']
        eye_L.head[2]=mmd_eye_L.head[2]
        eye_L.head[0]=max(mmd_eye_L.head[0],mmd_eye_L.tail[0])
        eye_L.head[1]=min(mmd_eye_L.head[1],mmd_eye_L.tail[1])
        eye_L.tail=eye_L.head
        eye_L.tail[1]-=0.1

        eye_R=rigify_arm.data.edit_bones['eye.R']
        mmd_eye_R=mmd_arm2.pose.bones['Eye_R']
        eye_R.head[2]=mmd_eye_R.head[2]
        eye_R.head[0]=min(mmd_eye_R.head[0],mmd_eye_R.tail[0])
        eye_R.head[1]=min(mmd_eye_R.head[1],mmd_eye_R.tail[1])
        eye_R.tail=eye_R.head
        eye_R.tail[1]-=0.1

        if eye_L.head[0]<eye_R.head[0]:
            eye_R.name='1'
            eye_L.name='eye.R'
            eye_R.name='eye.L'
            invert_eyes=True

    #生成控制器
    if mmr_property.debug:
        return

    bpy.ops.object.mode_set(mode = 'OBJECT')
    bpy.context.view_layer.objects.active=rigify_arm
    bpy.ops.pose.rigify_generate()
    rig=bpy.data.objects["rig"]
    rig_bones_list=rig.data.bones.keys()

    #开始调整生成的控制器
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active=mmd_arm
    rig.select_set(True)
    mmd_arm2.select_set(True)

    #添加约束
    #add constraint

    constraints_list=[
        ("ORG-Arm_L","Arm_L",True,True),
        ("ORG-Arm_R","Arm_R",True,True),
        ("ORG-Elbow_L","Elbow_L",True,True),
        ("ORG-Elbow_R","Elbow_R",True,True),
        ("ORG-Shoulder_L","Shoulder_L",True,True),
        ("ORG-Shoulder_R","Shoulder_R",True,True),
        ("ORG-Wrist_L","Wrist_L",True,True),
        ("ORG-Wrist_R","Wrist_R",True,True),
        #("MCH-Elbow_tweak_L.001","HandTwist_L",True,False),
        #("MCH-Elbow_tweak_R.001","HandTwist_R",True,False),
        #("MCH-Arm_tweak_L.001","ArmTwist_L",True,False),
        #("MCH-Arm_tweak_R.001","ArmTwist_R",True,False),

        ("ORG-Leg_L","Leg_L",True,True),
        ("ORG-Leg_R","Leg_R",True,True),
        ("ORG-Knee_L","Knee_L",True,True),
        ("ORG-Knee_R","Knee_R",True,True),

        ("DEF-Ankle_L","Ankle_L",True,True),
        ("DEF-Ankle_R","Ankle_R",True,True),
        ("DEF-Ankle_L","LegIK_L",False,True),
        ("DEF-Ankle_R","LegIK_R",False,True),
        ("DEF-ToeTipIK_L","ToeTipIK_L",False,True),
        ("DEF-ToeTipIK_R","ToeTipIK_R",False,True),

        ("UpperBody2_fk","UpperBody2",True,True),
        ("UpperBody_fk","UpperBody",True,True),

        ("LowerBody_fk","LowerBody",True,True),
        ("torso","Center",True,True),
        ("DEF-Neck","Neck",True,True),
        ("DEF-Head","Head",True,True),
        ("root","ParentNode",True,True),

        ("ORG-Thumb0_L","Thumb0_L",True,True),
        ("ORG-Thumb0_R","Thumb0_R",True,True),
        ("ORG-Thumb1_L","Thumb1_L",True,True),
        ("ORG-Thumb1_R","Thumb1_R",True,True),
        ("ORG-Thumb2_L","Thumb2_L",True,True),
        ("ORG-Thumb2_R","Thumb2_R",True,True),

        ("ORG-IndexFinger1_L","IndexFinger1_L",True,True),
        ("ORG-IndexFinger1_R","IndexFinger1_R",True,True),
        ("ORG-IndexFinger2_L","IndexFinger2_L",True,True),
        ("ORG-IndexFinger2_R","IndexFinger2_R",True,True),
        ("ORG-IndexFinger3_L","IndexFinger3_L",True,True),
        ("ORG-IndexFinger3_R","IndexFinger3_R",True,True),
        ("ORG-MiddleFinger1_L","MiddleFinger1_L",True,True),
        ("ORG-MiddleFinger1_R","MiddleFinger1_R",True,True),
        ("ORG-MiddleFinger2_L","MiddleFinger2_L",True,True),
        ("ORG-MiddleFinger2_R","MiddleFinger2_R",True,True),
        ("ORG-MiddleFinger3_L","MiddleFinger3_L",True,True),
        ("ORG-MiddleFinger3_R","MiddleFinger3_R",True,True),
        ("ORG-RingFinger1_L","RingFinger1_L",True,True),
        ("ORG-RingFinger1_R","RingFinger1_R",True,True),
        ("ORG-RingFinger2_L","RingFinger2_L",True,True),
        ("ORG-RingFinger2_R","RingFinger2_R",True,True),
        ("ORG-RingFinger3_L","RingFinger3_L",True,True),
        ("ORG-RingFinger3_R","RingFinger3_R",True,True),
        ("ORG-LittleFinger1_L","LittleFinger1_L",True,True),
        ("ORG-LittleFinger1_R","LittleFinger1_R",True,True),
        ("ORG-LittleFinger2_L","LittleFinger2_L",True,True),
        ("ORG-LittleFinger2_R","LittleFinger2_R",True,True),
        ("ORG-LittleFinger3_L","LittleFinger3_L",True,True),
        ("ORG-LittleFinger3_R","LittleFinger3_R",True,True),
    ]

    if invert_eyes:
        constraints_list.append(("ORG-eye.L","Eye_R",True,False))
        constraints_list.append(("ORG-eye.R","Eye_L",True,False))
    else:
        constraints_list.append(("ORG-eye.L","Eye_L",True,False))
        constraints_list.append(("ORG-eye.R","Eye_R",True,False))

    add_constraint2(constraints_list)

    #眼睛约束
    '''if 'Eye_L'in mmd_bones_list and 'Eye_R' in mmd_bones_list:
        bpy.ops.object.mode_set(mode = 'EDIT')
        eyes_parent_L=rig.data.edit_bones.new(name='eyes_parent_L')
        eyes_parent_L.head=mmd_arm2.data.edit_bones['Eye_L'].head
        eyes_parent_L.tail=mmd_arm2.data.edit_bones['Eye_L'].tail
        eyes_parent_L.roll=mmd_arm2.data.edit_bones['Eye_L'].roll

        eyes_parent_R=rig.data.edit_bones.new(name='eyes_parent_R')
        eyes_parent_R.head=mmd_arm2.data.edit_bones['Eye_R'].head
        eyes_parent_R.tail=mmd_arm2.data.edit_bones['Eye_R'].tail
        eyes_parent_R.roll=mmd_arm2.data.edit_bones['Eye_R'].roll

        if invert_eyes:
            eyes_parent_L.parent=rig.data.edit_bones['ORG-eye.R']
            eyes_parent_R.parent=rig.data.edit_bones['ORG-eye.L']
        else:
            eyes_parent_L.parent=rig.data.edit_bones['ORG-eye.L']
            eyes_parent_R.parent=rig.data.edit_bones['ORG-eye.R']

        bpy.ops.object.mode_set(mode = 'POSE')
        con= mmd_arm.pose.bones['Eye_L'].constraints
        rig.data.bones['eyes_parent_L'].hide=True
        mmd_arm.data.bones['Eye_L'].hide=False
        COPY_ROTATION=con.new(type='COPY_ROTATION')
        COPY_ROTATION.target = rig
        COPY_ROTATION.subtarget = 'eyes_parent_L'
        COPY_ROTATION.name="rel_rotation"

        con= mmd_arm.pose.bones['Eye_R'].constraints
        rig.data.bones['eyes_parent_R'].hide=True
        mmd_arm.data.bones['Eye_R'].hide=False
        COPY_ROTATION=con.new(type='COPY_ROTATION')
        COPY_ROTATION.target = rig
        COPY_ROTATION.subtarget = 'eyes_parent_R'
        COPY_ROTATION.name="rel_rotation"'''

    #上半身控制器

    if mmr_property.upper_body_controller:
        bpy.ops.object.mode_set(mode = 'EDIT')
        torso_parent=rig.data.edit_bones.new(name='torso_parent')
        torso_parent.head=rig.data.edit_bones['root'].head
        torso_parent.tail=rig.data.edit_bones['root'].tail
        torso_parent.roll=rig.data.edit_bones['root'].roll
        torso_parent.length=rig.data.edit_bones['root'].length/3
        torso_parent.head[2]=torso_parent.tail[2]=mmd_arm2.data.edit_bones['Knee_L'].head[2]
        torso_parent.parent=rig.data.edit_bones['root']
        rig.data.edit_bones['MCH-torso.parent'].parent=torso_parent
        rig.data.edit_bones['MCH-Wrist_ik.parent_L'].parent=torso_parent
        rig.data.edit_bones['MCH-Wrist_ik.parent_R'].parent=torso_parent
        
        bpy.ops.object.mode_set(mode = 'POSE')
        rig.pose.bones["torso_parent"].custom_shape = bpy.data.objects["WGT-rig_root"]
        rig.pose.bones["torso_parent"].custom_shape_scale = 0.4
        rig.pose.bones['torso_parent'].mmd_bone.name_j='グルーブ'
        rig.pose.bones["Arm_parent_L"]["IK_parent"] = 0
        rig.pose.bones["Arm_parent_R"]["IK_parent"] = 0
        rig.pose.bones["torso"]["torso_parent"] = 0
        rig.data.bones["torso_parent"].layers=rig.data.bones["torso"].layers


    else:
        rig.pose.bones['MCH-torso.parent'].mmd_bone.name_j='グルーブ'



    #手腕旋转跟随上半身开关
    if mmr_property.wrist_rotation_follow:
        bpy.ops.object.mode_set(mode = 'EDIT')
        parent_bone=rig.data.edit_bones.new(name="Wrist_ik_L_parent")
        parent_bone.head=rig.data.edit_bones["Wrist_ik_L"].head
        parent_bone.tail=rig.data.edit_bones["Wrist_ik_L"].tail
        parent_bone.roll=rig.data.edit_bones["Wrist_ik_L"].roll
        parent_bone.parent=rig.data.edit_bones["MCH-Elbow_ik_L"]
        parent_bone=rig.data.edit_bones.new(name="Wrist_ik_R_parent")
        parent_bone.head=rig.data.edit_bones["Wrist_ik_R"].head
        parent_bone.tail=rig.data.edit_bones["Wrist_ik_R"].tail
        parent_bone.roll=rig.data.edit_bones["Wrist_ik_R"].roll
        parent_bone.parent=rig.data.edit_bones["MCH-Elbow_ik_R"]
        '''rig.pose.bones["ORG-Wrist_L"].constraints[0].mute = True
        rig.pose.bones["ORG-Wrist_L"].constraints[1].mute = True
        rig.pose.bones["ORG-Wrist_R"].constraints[0].mute = True
        rig.pose.bones["ORG-Wrist_R"].constraints[1].mute = True'''
        bpy.ops.object.mode_set(mode = 'POSE')

        wrist_rotation=rig.pose.bones["Wrist_ik_L"].constraints.new(type='COPY_ROTATION')
        wrist_rotation.target = rig
        wrist_rotation.subtarget = "Wrist_ik_L_parent"
        wrist_rotation.name="wrist_rotation"
        wrist_rotation.mix_mode = 'BEFORE'
        wrist_rotation.owner_space = 'LOCAL_WITH_PARENT'
        wrist_rotation.target_space = 'LOCAL_WITH_PARENT'

        wrist_rotation=rig.pose.bones["Wrist_ik_R"].constraints.new(type='COPY_ROTATION')
        wrist_rotation.target = rig
        wrist_rotation.subtarget = "Wrist_ik_R_parent"
        wrist_rotation.name="wrist_rotation"
        wrist_rotation.mix_mode = 'BEFORE'
        wrist_rotation.owner_space = 'LOCAL_WITH_PARENT'
        wrist_rotation.target_space = 'LOCAL_WITH_PARENT'

        rig.data.bones["Wrist_ik_L_parent"].hide=True
        rig.data.bones["Wrist_ik_R_parent"].hide=True


    #肩膀联动
    #IK shoulder
    rig.pose.bones["Shoulder_L"].ik_stiffness_x = 0.5
    rig.pose.bones["Shoulder_L"].ik_stiffness_y = 0.5
    rig.pose.bones["Shoulder_L"].ik_stiffness_z = 0.5
    rig.pose.bones["Shoulder_R"].ik_stiffness_x = 0.5
    rig.pose.bones["Shoulder_R"].ik_stiffness_y = 0.5
    rig.pose.bones["Shoulder_R"].ik_stiffness_z = 0.5

    rig.pose.bones["ORG-Shoulder_L"].ik_stiffness_x = 0.5
    rig.pose.bones["ORG-Shoulder_L"].ik_stiffness_y = 0.5
    rig.pose.bones["ORG-Shoulder_L"].ik_stiffness_z = 0.5
    rig.pose.bones["ORG-Shoulder_R"].ik_stiffness_x = 0.5
    rig.pose.bones["ORG-Shoulder_R"].ik_stiffness_y = 0.5
    rig.pose.bones["ORG-Shoulder_R"].ik_stiffness_z = 0.5

    if mmr_property.auto_shoulder:
        bpy.ops.object.mode_set(mode = 'EDIT')
        rig.data.edit_bones["Arm_ik_L"].parent=rig.data.edit_bones["Shoulder_L"]
        rig.pose.bones["MCH-Elbow_ik_L"].constraints["IK.001"].chain_count = 3
        rig.pose.bones["MCH-Elbow_ik_L"].constraints["IK"].chain_count = 3

        rig.data.edit_bones["Arm_ik_R"].parent=rig.data.edit_bones["Shoulder_R"]
        rig.pose.bones["MCH-Elbow_ik_R"].constraints["IK.001"].chain_count = 3
        rig.pose.bones["MCH-Elbow_ik_R"].constraints["IK"].chain_count = 3


    bpy.ops.object.mode_set(mode = 'POSE')

    
    #修正rigifyIK控制器范围限制
    rig.pose.bones["MCH-Knee_ik_L"].use_ik_limit_x = True
    rig.pose.bones["MCH-Knee_ik_R"].use_ik_limit_x = True
    rig.pose.bones["MCH-Knee_ik_L"].ik_min_x = -0.0174533
    rig.pose.bones["MCH-Knee_ik_R"].ik_min_x = -0.0174533

    #极向目标开关
    #pole target
    rig.pose.bones["MCH-Elbow_ik_L"].constraints["IK.001"].pole_angle = 3.14159
    if mmr_property.pole_target:
        rig.pose.bones["Leg_parent_L"]["pole_vector"] = 1
        rig.pose.bones["Leg_parent_R"]["pole_vector"] = 1
        rig.pose.bones["Arm_parent_L"]["pole_vector"] = 1
        rig.pose.bones["Arm_parent_R"]["pole_vector"] = 1


    #捩骨约束
    #Twist constrains
    if 'HandTwist_L' in mmd_bones_list:
        #bpy.ops.object.mode_set(mode = 'EDIT')
        #mmd_arm.data.edit_bones['HandTwist_L'].tail=mmd_arm.data.edit_bones['Wrist_L'].head
        bpy.ops.object.mode_set(mode = 'POSE')
        c1=mmd_arm.pose.bones['HandTwist_L'].constraints.new(type='COPY_ROTATION')
        c1.target=rig
        c1.subtarget='ORG-Wrist_L'
        c1.mix_mode = 'BEFORE'
        c1.target_space = 'LOCAL'
        c1.owner_space = 'LOCAL'
        c1.influence = 0.5
        c2=mmd_arm.pose.bones['HandTwist_L'].constraints.new(type='DAMPED_TRACK')
        c2.target=rig
        c2.subtarget='ORG-Wrist_L'
        mmd_arm.data.bones['HandTwist_L'].hide=False

    if 'HandTwist_R' in mmd_bones_list:
        #bpy.ops.object.mode_set(mode = 'EDIT')
        #mmd_arm.data.edit_bones['HandTwist_R'].tail=mmd_arm.data.edit_bones['Wrist_R'].head
        bpy.ops.object.mode_set(mode = 'POSE')
        c1=mmd_arm.pose.bones['HandTwist_R'].constraints.new(type='COPY_ROTATION')
        c1.target=rig
        c1.subtarget='ORG-Wrist_R'
        c1.mix_mode = 'BEFORE'
        c1.target_space = 'LOCAL'
        c1.owner_space = 'LOCAL'
        c1.influence = 0.5
        c2=mmd_arm.pose.bones['HandTwist_R'].constraints.new(type='DAMPED_TRACK')
        c2.target=rig
        c2.subtarget='ORG-Wrist_R'
        mmd_arm.data.bones['HandTwist_R'].hide=False

    if 'ArmTwist_L' in mmd_bones_list:
        #bpy.ops.object.mode_set(mode = 'EDIT')
        #mmd_arm.data.edit_bones['ArmTwist_L'].tail=mmd_arm.data.edit_bones['Elbow_L'].head
        bpy.ops.object.mode_set(mode = 'POSE')
        c1=mmd_arm.pose.bones['ArmTwist_L'].constraints.new(type='COPY_ROTATION')
        c1.target=rig
        c1.subtarget='ORG-Elbow_L'
        c1.mix_mode = 'BEFORE'
        c1.target_space = 'LOCAL'
        c1.owner_space = 'LOCAL'
        c2=mmd_arm.pose.bones['ArmTwist_L'].constraints.new(type='DAMPED_TRACK')
        c2.target=rig
        c2.subtarget='ORG-Elbow_L'
        mmd_arm.data.bones['ArmTwist_L'].hide=False

    if 'ArmTwist_R' in mmd_bones_list:
        #bpy.ops.object.mode_set(mode = 'EDIT')
        #mmd_arm.data.edit_bones['ArmTwist_R'].tail=mmd_arm.data.edit_bones['Elbow_R'].head
        bpy.ops.object.mode_set(mode = 'POSE')
        c1=mmd_arm.pose.bones['ArmTwist_R'].constraints.new(type='COPY_ROTATION')
        c1.target=rig
        c1.subtarget='ORG-Elbow_R'
        c1.mix_mode = 'BEFORE'
        c1.target_space = 'LOCAL'
        c1.owner_space = 'LOCAL'
        c2=mmd_arm.pose.bones['ArmTwist_R'].constraints.new(type='DAMPED_TRACK')
        c2.target=rig
        c2.subtarget='ORG-Elbow_R'
        mmd_arm.data.bones['ArmTwist_R'].hide=False

    #写入PMX骨骼名称数据
    #write PMX bone name
    rig_bones_list=rig.data.bones.keys()

    PMX_dict={
    'root':'全ての親','torso':'センター','hips':'下半身','UpperBody_fk':'上半身','UpperBody2_fk':'上半身2','neck':'首','head':'頭','Eyes_Rig':'両目',
    'Leg_ik_L':'左足','Ankle_ik_L':'左足ＩＫ','ToeTipIK_L':'左つま先ＩＫ','Leg_ik_R':'右足','Ankle_ik_R':'右足ＩＫ','ToeTipIK_R':'右つま先ＩＫ',
    'Shoulder_L':'左肩','Arm_fk_L':'左腕','Elbow_fk_L':'左ひじ','Wrist_fk_L':'左手首','Shoulder_R':'右肩','Arm_fk_R':'右腕','Elbow_fk_R':'右ひじ','Wrist_fk_R':'右手首',
    'Thumb0_L':'左親指０','Thumb1_L':'左親指１','Thumb2_L':'左親指２',
    'IndexFinger1_L':'左人指１','IndexFinger2_L':'左人指２','IndexFinger3_L':'左人指３',
    'MiddleFinger1_L':'左中指１','MiddleFinger2_L':'左中指２','MiddleFinger3_L':'左中指３',
    'RingFinger1_L':'左薬指１','RingFinger2_L':'左薬指２','RingFinger3_L':'左薬指３',
    'LittleFinger1_L':'左小指１','LittleFinger2_L':'左小指２','LittleFinger3_L':'左小指３',
    'Thumb0_R':'右親指０','Thumb1_R':'右親指１','Thumb2_R':'右親指２',
    'IndexFinger1_R':'右人指１','IndexFinger2_R':'右人指２','IndexFinger3_R':'右人指３',
    'MiddleFinger1_R':'右中指１','MiddleFinger2_R':'右中指２','MiddleFinger3_R':'右中指３',
    'RingFinger1_R':'右薬指１','RingFinger2_R':'右薬指２','RingFinger3_R':'右薬指３',
    'LittleFinger1_R':'右小指１','LittleFinger2_R':'右小指２','LittleFinger3_R':'右小指３'
    }

    for key,value in PMX_dict.items():
        if key in rig_bones_list:
            rig.pose.bones[key].mmd_bone.name_j=value
    
    bpy.ops.object.mode_set(mode = 'OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    #删除多余骨架
    #delete metarig armatrue
    rigify_arm.select_set(True)
    mmd_arm2.select_set(True)
    bpy.ops.object.delete(use_global=True)
    #隐藏原骨架，把新骨架设为永远在前
    #hide old armature
    rig.show_in_front = True
    mmd_arm.hide = True
    mmd_arm.parent.hide = True
    rig.name=mmd_arm.parent.name+'_Rig'
    mmd_arm.parent.parent=rig

    #缩小root控制器
    #reduce size
    rig.pose.bones["root"].custom_shape_scale = 0.4

    if 'master' in mmd_bones_dict_e:
        mmd_arm.data.bones[mmd_bones_dict_e['master']].hide=False


    #隐藏部分控制器
    #hide some controller
    rig.data.layers[1] = False
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

    #锁定移动的骨骼列表
    #lock the location of these bone
    lock_location_bone_list=[
        "Arm_ik_L","Arm_ik_R","Leg_ik_L","Leg_ik_R","hips","chest","neck","head","Shoulder_L","Shoulder_R","Thumb0_master_L","Thumb0_master_R",
        "Thumb1_master_L","Thumb1_master_R","IndexFinger1_master_L","IndexFinger1_master_R","MiddleFinger1_master_L","MiddleFinger1_master_R",
        "RingFinger1_master_L","RingFinger1_master_R","LittleFinger1_master_L","LittleFinger1_master_R"
        ]
    #隐藏的骨骼列表
    #hide these bone
    hide_bone_list=[
        "Leg_parent_L","Leg_parent_R","Arm_parent_L","Arm_parent_R","Ankle_heel_ik_L","Ankle_heel_ik_R",'master_eye.L','master_eye.R',
        'ear.L','ear.R','nose_master','teeth.T','teeth.B','tongue_master','jaw_master'
        ]
    #锁定缩放的骨骼列表
    #lock the scale of these bone
    lock_scale_bone_list=[
        "root","torso","Ankle_ik_L","Ankle_ik_R","toe.L","toe.R","Wrist_ik_L","Wrist_ik_R","Arm_ik_L","Arm_ik_R","Leg_ik_L","Leg_ik_R",
        "hips","chest","neck","head","Shoulder_L","Shoulder_R"
        ]
    for name in lock_location_bone_list:
        if name in rig.data.bones.keys():              
            rig.pose.bones[name].lock_location = [True,True,True]
    for name in lock_scale_bone_list:
        if name in rig.data.bones.keys():  
            rig.pose.bones[name].lock_scale = [True,True,True]
    for name in hide_bone_list:
        if name in rig.data.bones.keys():  
            rig.data.bones[name].hide=True

    if 'Eye_L' not in mmd_bones_list or 'Eye_R' not in mmd_bones_list:
        rig.data.bones['eyes'].hide=True
        rig.data.bones['eye.L'].hide=True
        rig.data.bones['eye.R'].hide=True

    #将IK拉伸设为0
    #set IK stretch to 0
    rig.pose.bones["Arm_parent_L"]["IK_Stretch"] = 0
    rig.pose.bones["Arm_parent_R"]["IK_Stretch"] = 0
    rig.pose.bones["Leg_parent_L"]["IK_Stretch"] = 0
    rig.pose.bones["Leg_parent_R"]["IK_Stretch"] = 0

    #替换实心控制器
    #replace controller
    bpy.ops.object.select_all(action='DESELECT')
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
        bpy.ops.object.mode_set(mode = 'OBJECT')



    #将轴心设为各自中点以方便操作
    #set transform pivot point to individual
    bpy.context.view_layer.objects.active=rig
    rig.select_set(True)
    bpy.context.scene.tool_settings.transform_pivot_point = 'INDIVIDUAL_ORIGINS'
    logging.info("完成")
    alert_error("提示","完成")
    return(True)

def RIG2(context):

    #属性准备阶段
    global mmd_arm
    global mmd_arm2
    global rig
    global mmd_bones_list
    global rig_bones_list

    area = bpy.context.area.type
    bpy.context.area.type = 'VIEW_3D'

    mmd_arm=context.view_layer.objects.active

    scene=context.scene
    mmr_property=scene.mmr_property

    my_dir = os.path.dirname(os.path.realpath(__file__))
    rigify_blend_file = os.path.join(my_dir, "MMR_Rig.blend")

    bpy.ops.object.mode_set(mode = 'OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    context.view_layer.objects.active=mmd_arm
    mmd_arm.select_set(True)
    

    #检查骨架并翻译
    if check_arm()==False:
        return{False}

    #生成字典
    unconnect_bone=['LowerBody']
    mmd_bones_list=mmd_arm.pose.bones.keys()
    preset_dict={}
    bpy.ops.object.mode_set(mode = 'EDIT')
    for bone in mmd_arm.pose.bones:
        name=bone.name
        if bone.mmr_bone_type !='None':
            preset_dict[bone.mmr_bone_type]=bone.name
        if bone.mmr_bone_type in unconnect_bone:
            mmd_arm.data.edit_bones[name].use_connect = False

    bpy.ops.object.mode_set(mode = 'OBJECT')

    #生成第二套骨骼
    mmd_arm2=mmd_arm.copy()
    context.collection.objects.link(mmd_arm2)
    mmd_arm2.data=mmd_arm.data.copy()
    context.view_layer.objects.active=mmd_arm2
    mmd_arm2.select_set(True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bpy.ops.object.mode_set(mode = 'POSE')
    bpy.ops.pose.armature_apply(selected=False)
    bpy.ops.object.mode_set(mode = 'OBJECT')


    #导入metarig骨骼
    #import metarig armature
    rigify_arm_name="MMR_Rig_relative2"
    
    with bpy.data.libraries.load(rigify_blend_file) as (data_from, data_to):
        data_to.objects = [rigify_arm_name]

    rigify_arm=data_to.objects[0]
    context.collection.objects.link(rigify_arm)
    rigify_arm.dimensions=mmd_arm2.dimensions

    bpy.ops.object.select_all(action='DESELECT')
    context.view_layer.objects.active=rigify_arm
    rigify_arm.select_set(True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bpy.ops.object.mode_set(mode = 'EDIT')
    bpy.ops.armature.select_all(action='DESELECT')

    if "Thumb0_L" not in preset_dict:
        rigify_arm.data.edit_bones.remove(rigify_arm.data.edit_bones["Thumb2_L"])
        rigify_arm.data.edit_bones["Thumb1_L"].name='Thumb2_L'
        rigify_arm.data.edit_bones["Thumb0_L"].name='Thumb1_L'

    if "Thumb0_R" not in preset_dict:
        rigify_arm.data.edit_bones.remove(rigify_arm.data.edit_bones["Thumb2_R"])
        rigify_arm.data.edit_bones["Thumb1_R"].name='Thumb2_R'
        rigify_arm.data.edit_bones["Thumb0_R"].name='Thumb1_R'

    rigify_bones_list=rigify_arm.data.edit_bones.keys()
    remain_bone=set(rigify_bones_list)


    #新骨骼匹配方法

    for bone in mmd_arm2.pose.bones:
        bone_type2=bone.mmr_bone_type
        if bone_type2!="None" and bone_type2 in rigify_bones_list:
            rigify_bone=rigify_arm.data.edit_bones[bone_type2]
            if bone.mmr_bone_invert:
                rigify_bone.tail=bone.head
            else:
                rigify_bone.tail=bone.tail

    for bone in mmd_arm2.pose.bones:
        bone_type2=bone.mmr_bone_type
        if bone_type2!="None" and bone_type2 in rigify_bones_list:
            rigify_bone=rigify_arm.data.edit_bones[bone_type2]
            remain_bone.discard(bone_type2)
            if bone.mmr_bone_invert:
                rigify_bone.head=bone.tail
            else:
                rigify_bone.head=bone.head

    #修正部分骨骼

    rigify_arm.data.edit_bones["UpperBody2"].tail=rigify_arm.data.edit_bones["Neck"].head
    if rigify_arm.data.edit_bones["LowerBody"].tail==rigify_arm.data.edit_bones["UpperBody"].head:
        rigify_arm.data.edit_bones["LowerBody"].tail[2]-=0.01

    rigify_arm.data.edit_bones["Head"].tail=rigify_arm.data.edit_bones["Head"].head
    rigify_arm.data.edit_bones["Head"].tail[2]+=rigify_arm.data.edit_bones["Neck"].length*3
    if rigify_arm.data.edit_bones["Neck"].tail==rigify_arm.data.edit_bones["Head"].head:
        rigify_arm.data.edit_bones["Neck"].tail[2]-=0.01

    rigify_arm.data.edit_bones["LegIK_L"].head=(np.array(rigify_arm.data.edit_bones["Ankle_L"].head)+np.array(rigify_arm.data.edit_bones["Ankle_L"].head))/2
    rigify_arm.data.edit_bones["LegIK_L"].head[2]=rigify_arm.data.edit_bones["Ankle_L"].tail[2]
    rigify_arm.data.edit_bones["LegIK_L"].tail=rigify_arm.data.edit_bones["LegIK_L"].head
    rigify_arm.data.edit_bones["LegIK_L"].tail[0]+=rigify_arm.data.edit_bones["Ankle_L"].length/10
    rigify_arm.data.edit_bones["LegIK_L"].head[0]-=rigify_arm.data.edit_bones["Ankle_L"].length/10

    rigify_arm.data.edit_bones["LegIK_R"].head=(np.array(rigify_arm.data.edit_bones["Ankle_R"].head)+np.array(rigify_arm.data.edit_bones["Ankle_R"].head))/2
    rigify_arm.data.edit_bones["LegIK_R"].head[2]=rigify_arm.data.edit_bones["Ankle_R"].tail[2]
    rigify_arm.data.edit_bones["LegIK_R"].tail=rigify_arm.data.edit_bones["Ankle_R"].head
    rigify_arm.data.edit_bones["LegIK_R"].tail[0]+=rigify_arm.data.edit_bones["Ankle_R"].length/10
    rigify_arm.data.edit_bones["LegIK_R"].head[0]-=rigify_arm.data.edit_bones["Ankle_R"].length/10

    rigify_arm.data.edit_bones["Wrist_L"].tail=(np.array(rigify_arm.data.edit_bones["MiddleFinger1_L"].head)+np.array(rigify_arm.data.edit_bones["RingFinger1_L"].head))/2
    rigify_arm.data.edit_bones["Wrist_R"].tail=(np.array(rigify_arm.data.edit_bones["MiddleFinger1_R"].head)+np.array(rigify_arm.data.edit_bones["RingFinger1_R"].head))/2

    rigify_arm.data.edit_bones["ToeTipIK_L"].tail=rigify_arm.data.edit_bones["ToeTipIK_L"].head
    rigify_arm.data.edit_bones["ToeTipIK_L"].tail[1]+=rigify_arm.data.edit_bones["Ankle_L"].length/2

    rigify_arm.data.edit_bones["ToeTipIK_R"].tail=rigify_arm.data.edit_bones["ToeTipIK_R"].head
    rigify_arm.data.edit_bones["ToeTipIK_R"].tail[1]+=rigify_arm.data.edit_bones["Ankle_R"].length/2

    extend_bone=['Thumb2_L','IndexFinger3_L','MiddleFinger3_L','RingFinger3_L','LittleFinger3_L','Thumb2_R','IndexFinger3_R','MiddleFinger3_R','RingFinger3_R','LittleFinger3_R']
    for name in extend_bone:
        bone=rigify_arm.data.edit_bones[name]
        parent_bone=bone.parent
        bone.tail=np.array(parent_bone.tail)*2-np.array(parent_bone.head)

    #匹配眼睛骨骼
    invert_eyes=False
    if 'Eye_L' in preset_dict and 'Eye_R' in preset_dict:
        eye_L=rigify_arm.data.edit_bones['eye.L']
        mmd_eye_L=mmd_arm2.pose.bones[preset_dict['Eye_L']]
        eye_L.head[2]=mmd_eye_L.head[2]
        eye_L.head[0]=max(mmd_eye_L.head[0],mmd_eye_L.tail[0])
        eye_L.head[1]=min(mmd_eye_L.head[1],mmd_eye_L.tail[1])
        eye_L.tail=eye_L.head
        eye_L.tail[1]-=0.1

        eye_R=rigify_arm.data.edit_bones['eye.R']
        mmd_eye_R=mmd_arm2.pose.bones[preset_dict['Eye_R']]
        eye_R.head[2]=mmd_eye_R.head[2]
        eye_R.head[0]=min(mmd_eye_R.head[0],mmd_eye_R.tail[0])
        eye_R.head[1]=min(mmd_eye_R.head[1],mmd_eye_R.tail[1])
        eye_R.tail=eye_R.head
        eye_R.tail[1]-=0.1

        if eye_L.head[0]<eye_R.head[0]:
            eye_R.name='1'
            eye_L.name='eye.R'
            eye_R.name='eye.L'
            invert_eyes=True

    positive_z_bone=[
        'Shoulder_L','Arm_L','Elbow_L','Shoulder_R','Arm_R','Elbow_R',
        'IndexFinger1_L','IndexFinger2_L','IndexFinger3_L',
        'MiddleFinger1_L','MiddleFinger2_L','MiddleFinger3_L',
        'RingFinger1_L','RingFinger2_L','RingFinger3_L',
        'LittleFinger1_L','LittleFinger2_L','LittleFinger3_L',
        'IndexFinger1_R','IndexFinger2_R','IndexFinger3_R',
        'MiddleFinger1_R','MiddleFinger2_R','MiddleFinger3_R',
        'RingFinger1_R','RingFinger2_R','RingFinger3_R',
        'LittleFinger1_R','LittleFinger2_R','LittleFinger3_R',
    ]
    negative_y_bone=[
        'Wrist_L','Wrist_R',
        'Thumb0_L','Thumb1_L','Thumb2_L',
        'Thumb0_R','Thumb1_R','Thumb2_R',
    ]

    bpy.ops.armature.select_all(action='DESELECT')
    rigify_arm.data.show_axes = True
    rigify_bones_list=rigify_arm.data.edit_bones.keys()

    for name in positive_z_bone:
        if name in rigify_bones_list:
            rigify_arm.data.edit_bones[name].select=True
            rigify_arm.data.edit_bones[name].select_head=True
            rigify_arm.data.edit_bones[name].select_tail=True

    bpy.ops.armature.calculate_roll(type='GLOBAL_POS_Z')
    
    bpy.ops.armature.select_all(action='DESELECT')

    for name in negative_y_bone:
        if name in rigify_bones_list:
            rigify_arm.data.edit_bones[name].select=True
            rigify_arm.data.edit_bones[name].select_head=True
            rigify_arm.data.edit_bones[name].select_tail=True
    
    bpy.ops.armature.calculate_roll(type='GLOBAL_NEG_Y')

    #生成控制器
    if mmr_property.debug:
        bpy.context.area.type = area
        return

    bpy.ops.object.mode_set(mode = 'OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    context.view_layer.objects.active=rigify_arm
    rigify_arm.select_set(True)

    bpy.ops.pose.rigify_generate()
    rig=bpy.data.objects["rig"]
    rig_bones_list=rig.data.bones.keys()

    #开始调整生成的控制器
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active=mmd_arm
    rig.select_set(True)
    mmd_arm2.select_set(True)

    #添加约束
    #add constraint

    constraints_list=[
        ("ORG-Arm_L","Arm_L",True,True),
        ("ORG-Arm_R","Arm_R",True,True),
        ("ORG-Elbow_L","Elbow_L",True,True),
        ("ORG-Elbow_R","Elbow_R",True,True),
        ("ORG-Shoulder_L","Shoulder_L",True,True),
        ("ORG-Shoulder_R","Shoulder_R",True,True),
        ("ORG-Wrist_L","Wrist_L",True,True),
        ("ORG-Wrist_R","Wrist_R",True,True),
        #("MCH-Elbow_tweak_L.001","HandTwist_L",True,False),
        #("MCH-Elbow_tweak_R.001","HandTwist_R",True,False),
        #("MCH-Arm_tweak_L.001","ArmTwist_L",True,False),
        #("MCH-Arm_tweak_R.001","ArmTwist_R",True,False),

        ("ORG-Leg_L","Leg_L",True,True),
        ("ORG-Leg_R","Leg_R",True,True),
        ("ORG-Knee_L","Knee_L",True,True),
        ("ORG-Knee_R","Knee_R",True,True),

        ("DEF-Ankle_L","Ankle_L",True,True),
        ("DEF-Ankle_R","Ankle_R",True,True),
        ("DEF-Ankle_L","LegIK_L",False,True),
        ("DEF-Ankle_R","LegIK_R",False,True),
        ("DEF-ToeTipIK_L","ToeTipIK_L",False,True),
        ("DEF-ToeTipIK_R","ToeTipIK_R",False,True),

        ("UpperBody2_fk","UpperBody2",True,True),
        ("UpperBody_fk","UpperBody",True,True),
        ("UpperBody0_fk","UpperBody0",True,True),

        ("LowerBody_fk","LowerBody",True,True),
        ("torso","Center",True,True),
        ("DEF-Neck","Neck",True,True),
        ("DEF-Head","Head",True,True),
        ("root","ParentNode",True,True),

        ("ORG-Thumb0_L","Thumb0_L",True,True),
        ("ORG-Thumb0_R","Thumb0_R",True,True),
        ("ORG-Thumb1_L","Thumb1_L",True,True),
        ("ORG-Thumb1_R","Thumb1_R",True,True),
        ("ORG-Thumb2_L","Thumb2_L",True,True),
        ("ORG-Thumb2_R","Thumb2_R",True,True),

        ("ORG-IndexFinger1_L","IndexFinger1_L",True,True),
        ("ORG-IndexFinger1_R","IndexFinger1_R",True,True),
        ("ORG-IndexFinger2_L","IndexFinger2_L",True,True),
        ("ORG-IndexFinger2_R","IndexFinger2_R",True,True),
        ("ORG-IndexFinger3_L","IndexFinger3_L",True,True),
        ("ORG-IndexFinger3_R","IndexFinger3_R",True,True),
        ("ORG-MiddleFinger1_L","MiddleFinger1_L",True,True),
        ("ORG-MiddleFinger1_R","MiddleFinger1_R",True,True),
        ("ORG-MiddleFinger2_L","MiddleFinger2_L",True,True),
        ("ORG-MiddleFinger2_R","MiddleFinger2_R",True,True),
        ("ORG-MiddleFinger3_L","MiddleFinger3_L",True,True),
        ("ORG-MiddleFinger3_R","MiddleFinger3_R",True,True),
        ("ORG-RingFinger1_L","RingFinger1_L",True,True),
        ("ORG-RingFinger1_R","RingFinger1_R",True,True),
        ("ORG-RingFinger2_L","RingFinger2_L",True,True),
        ("ORG-RingFinger2_R","RingFinger2_R",True,True),
        ("ORG-RingFinger3_L","RingFinger3_L",True,True),
        ("ORG-RingFinger3_R","RingFinger3_R",True,True),
        ("ORG-LittleFinger1_L","LittleFinger1_L",True,True),
        ("ORG-LittleFinger1_R","LittleFinger1_R",True,True),
        ("ORG-LittleFinger2_L","LittleFinger2_L",True,True),
        ("ORG-LittleFinger2_R","LittleFinger2_R",True,True),
        ("ORG-LittleFinger3_L","LittleFinger3_L",True,True),
        ("ORG-LittleFinger3_R","LittleFinger3_R",True,True),
    ]

    if invert_eyes:
        constraints_list.append(("ORG-eye.L","Eye_R",True,False))
        constraints_list.append(("ORG-eye.R","Eye_L",True,False))
    else:
        constraints_list.append(("ORG-eye.L","Eye_L",True,False))
        constraints_list.append(("ORG-eye.R","Eye_R",True,False))

    add_constraint3(constraints_list,preset_dict)

    #上半身控制器

    if mmr_property.upper_body_controller:
        bpy.ops.object.mode_set(mode = 'EDIT')
        torso_parent=rig.data.edit_bones.new(name='torso_parent')
        torso_parent.head=rig.data.edit_bones['root'].head
        torso_parent.tail=rig.data.edit_bones['root'].tail
        torso_parent.roll=rig.data.edit_bones['root'].roll
        torso_parent.length=rig.data.edit_bones['root'].length/3
        torso_parent.head[2]=torso_parent.tail[2]=rig.data.edit_bones['Knee_fk_L'].head[2]
        torso_parent.parent=rig.data.edit_bones['root']
        rig.data.edit_bones['MCH-torso.parent'].parent=torso_parent
        rig.data.edit_bones['MCH-Wrist_ik.parent_L'].parent=torso_parent
        rig.data.edit_bones['MCH-Wrist_ik.parent_R'].parent=torso_parent
        
        bpy.ops.object.mode_set(mode = 'POSE')
        rig.pose.bones["torso_parent"].custom_shape = bpy.data.objects["WGT-rig_root"]
        rig.pose.bones["torso_parent"].custom_shape_scale = 0.4
        rig.pose.bones['torso_parent'].mmd_bone.name_j='グルーブ'
        rig.pose.bones["Arm_parent_L"]["IK_parent"] = 0
        rig.pose.bones["Arm_parent_R"]["IK_parent"] = 0
        rig.pose.bones["torso"]["torso_parent"] = 0
        rig.data.bones["torso_parent"].layers=rig.data.bones["torso"].layers


    else:
        rig.pose.bones['MCH-torso.parent'].mmd_bone.name_j='グルーブ'


    #肩膀联动
    #IK shoulder
    rig.pose.bones["Shoulder_L"].ik_stiffness_x = 0.5
    rig.pose.bones["Shoulder_L"].ik_stiffness_y = 0.5
    rig.pose.bones["Shoulder_L"].ik_stiffness_z = 0.5
    rig.pose.bones["Shoulder_R"].ik_stiffness_x = 0.5
    rig.pose.bones["Shoulder_R"].ik_stiffness_y = 0.5
    rig.pose.bones["Shoulder_R"].ik_stiffness_z = 0.5

    rig.pose.bones["ORG-Shoulder_L"].ik_stiffness_x = 0.5
    rig.pose.bones["ORG-Shoulder_L"].ik_stiffness_y = 0.5
    rig.pose.bones["ORG-Shoulder_L"].ik_stiffness_z = 0.5
    rig.pose.bones["ORG-Shoulder_R"].ik_stiffness_x = 0.5
    rig.pose.bones["ORG-Shoulder_R"].ik_stiffness_y = 0.5
    rig.pose.bones["ORG-Shoulder_R"].ik_stiffness_z = 0.5

    if mmr_property.auto_shoulder:
        bpy.ops.object.mode_set(mode = 'EDIT')
        rig.data.edit_bones["Arm_ik_L"].parent=rig.data.edit_bones["Shoulder_L"]
        rig.pose.bones["MCH-Elbow_ik_L"].constraints["IK.001"].chain_count = 3
        rig.pose.bones["MCH-Elbow_ik_L"].constraints["IK"].chain_count = 3

        rig.data.edit_bones["Arm_ik_R"].parent=rig.data.edit_bones["Shoulder_R"]
        rig.pose.bones["MCH-Elbow_ik_R"].constraints["IK.001"].chain_count = 3
        rig.pose.bones["MCH-Elbow_ik_R"].constraints["IK"].chain_count = 3


    bpy.ops.object.mode_set(mode = 'POSE')

    
    #修正rigifyIK控制器范围限制
    rig.pose.bones["MCH-Knee_ik_L"].use_ik_limit_x = True
    rig.pose.bones["MCH-Knee_ik_R"].use_ik_limit_x = True
    rig.pose.bones["MCH-Knee_ik_L"].ik_min_x = -0.0174533
    rig.pose.bones["MCH-Knee_ik_R"].ik_min_x = -0.0174533

    rig.pose.bones["MCH-Elbow_ik_L"].use_ik_limit_z = True
    rig.pose.bones["MCH-Elbow_ik_R"].use_ik_limit_z = True
    rig.pose.bones["MCH-Elbow_ik_L"].ik_max_z = 0
    rig.pose.bones["MCH-Elbow_ik_R"].ik_min_z = 0

    #极向目标开关
    #pole target
    rig.pose.bones["MCH-Elbow_ik_L"].constraints["IK.001"].pole_angle = 3.14159
    if mmr_property.pole_target:
        rig.pose.bones["Leg_parent_L"]["pole_vector"] = 1
        rig.pose.bones["Leg_parent_R"]["pole_vector"] = 1
        rig.pose.bones["Arm_parent_L"]["pole_vector"] = 1
        rig.pose.bones["Arm_parent_R"]["pole_vector"] = 1


    #捩骨约束
    #Twist constrains
    if 'HandTwist_L' in preset_dict and 'Wrist_L' in preset_dict:
        c1=mmd_arm.pose.bones[preset_dict['HandTwist_L']].constraints.new(type='COPY_ROTATION')
        c1.target=rig
        c1.subtarget='ORG-Wrist_L'
        c1.mix_mode = 'BEFORE'
        c1.target_space = 'LOCAL'
        c1.owner_space = 'LOCAL'
        c1.influence = 0.5
        c2=mmd_arm.pose.bones[preset_dict['HandTwist_L']].constraints.new(type='DAMPED_TRACK')
        c2.target=rig
        c2.subtarget='ORG-Wrist_L'
        mmd_arm.data.bones[preset_dict['HandTwist_L']].hide=False

    if 'HandTwist_R' in mmd_bones_list:
        c1=mmd_arm.pose.bones[preset_dict['HandTwist_R']].constraints.new(type='COPY_ROTATION')
        c1.target=rig
        c1.subtarget='ORG-Wrist_R'
        c1.mix_mode = 'BEFORE'
        c1.target_space = 'LOCAL'
        c1.owner_space = 'LOCAL'
        c1.influence = 0.5
        c2=mmd_arm.pose.bones[preset_dict['HandTwist_R']].constraints.new(type='DAMPED_TRACK')
        c2.target=rig
        c2.subtarget='ORG-Wrist_R'
        mmd_arm.data.bones[preset_dict['HandTwist_R']].hide=False

    if 'ArmTwist_L' in mmd_bones_list:
        c1=mmd_arm.pose.bones[preset_dict['ArmTwist_L']].constraints.new(type='COPY_ROTATION')
        c1.target=rig
        c1.subtarget='ORG-Elbow_L'
        c1.mix_mode = 'BEFORE'
        c1.target_space = 'LOCAL'
        c1.owner_space = 'LOCAL'
        c2=mmd_arm.pose.bones[preset_dict['ArmTwist_L']].constraints.new(type='DAMPED_TRACK')
        c2.target=rig
        c2.subtarget='ORG-Elbow_L'
        mmd_arm.data.bones[preset_dict['ArmTwist_L']].hide=False

    if 'ArmTwist_R' in mmd_bones_list:
        c1=mmd_arm.pose.bones[preset_dict['ArmTwist_R']].constraints.new(type='COPY_ROTATION')
        c1.target=rig
        c1.subtarget='ORG-Elbow_R'
        c1.mix_mode = 'BEFORE'
        c1.target_space = 'LOCAL'
        c1.owner_space = 'LOCAL'
        c2=mmd_arm.pose.bones[preset_dict['ArmTwist_R']].constraints.new(type='DAMPED_TRACK')
        c2.target=rig
        c2.subtarget='ORG-Elbow_R'
        mmd_arm.data.bones[preset_dict['ArmTwist_R']].hide=False

    #写入PMX骨骼名称数据
    #write PMX bone name
    rig_bones_list=rig.data.bones.keys()

    PMX_dict={
    'root':'全ての親','torso':'センター','hips':'下半身','UpperBody_fk':'上半身','UpperBody2_fk':'上半身2','neck':'首','head':'頭','Eyes_Rig':'両目',
    'Leg_ik_L':'左足','Ankle_ik_L':'左足ＩＫ','ToeTipIK_L':'左つま先ＩＫ','Leg_ik_R':'右足','Ankle_ik_R':'右足ＩＫ','ToeTipIK_R':'右つま先ＩＫ',
    'Shoulder_L':'左肩','Arm_fk_L':'左腕','Elbow_fk_L':'左ひじ','Wrist_fk_L':'左手首','Shoulder_R':'右肩','Arm_fk_R':'右腕','Elbow_fk_R':'右ひじ','Wrist_fk_R':'右手首',
    'Thumb0_L':'左親指０','Thumb1_L':'左親指１','Thumb2_L':'左親指２',
    'IndexFinger1_L':'左人指１','IndexFinger2_L':'左人指２','IndexFinger3_L':'左人指３',
    'MiddleFinger1_L':'左中指１','MiddleFinger2_L':'左中指２','MiddleFinger3_L':'左中指３',
    'RingFinger1_L':'左薬指１','RingFinger2_L':'左薬指２','RingFinger3_L':'左薬指３',
    'LittleFinger1_L':'左小指１','LittleFinger2_L':'左小指２','LittleFinger3_L':'左小指３',
    'Thumb0_R':'右親指０','Thumb1_R':'右親指１','Thumb2_R':'右親指２',
    'IndexFinger1_R':'右人指１','IndexFinger2_R':'右人指２','IndexFinger3_R':'右人指３',
    'MiddleFinger1_R':'右中指１','MiddleFinger2_R':'右中指２','MiddleFinger3_R':'右中指３',
    'RingFinger1_R':'右薬指１','RingFinger2_R':'右薬指２','RingFinger3_R':'右薬指３',
    'LittleFinger1_R':'右小指１','LittleFinger2_R':'右小指２','LittleFinger3_R':'右小指３'
    }

    for key,value in PMX_dict.items():
        if key in rig_bones_list:
            rig.pose.bones[key].mmd_bone.name_j=value
    
    bpy.ops.object.mode_set(mode = 'OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    #删除多余骨架
    #delete metarig armatrue
    rigify_arm.select_set(True)
    mmd_arm2.select_set(True)
    bpy.ops.object.delete(use_global=True)
    #隐藏原骨架，把新骨架设为永远在前
    #hide old armature
    rig.show_in_front = True
    mmd_arm.hide = True
    rig.name=mmd_arm.name+'_Rig'

    #缩小root控制器
    #reduce size
    rig.pose.bones["root"].custom_shape_scale = 0.4


    #隐藏部分控制器
    #hide some controller
    rig.data.layers[1] = False
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
    if 'Eye_L' not in preset_dict or 'Eye_R' not in preset_dict:
        rig.data.layers[0] = False

    #锁定移动的骨骼列表
    #lock the location of these bone
    lock_location_bone_list=[
        "Arm_ik_L","Arm_ik_R","Leg_ik_L","Leg_ik_R","hips","chest","neck","head","Shoulder_L","Shoulder_R","Thumb0_master_L","Thumb0_master_R",
        "Thumb1_master_L","Thumb1_master_R","IndexFinger1_master_L","IndexFinger1_master_R","MiddleFinger1_master_L","MiddleFinger1_master_R",
        "RingFinger1_master_L","RingFinger1_master_R","LittleFinger1_master_L","LittleFinger1_master_R"
        ]
    #隐藏的骨骼列表
    #hide these bone
    hide_bone_list=[
        "Leg_parent_L","Leg_parent_R","Arm_parent_L","Arm_parent_R","Ankle_heel_ik_L","Ankle_heel_ik_R",'master_eye.L','master_eye.R',
        'ear.L','ear.R','nose_master','teeth.T','teeth.B','tongue_master','jaw_master'
        ]
    #锁定缩放的骨骼列表
    #lock the scale of these bone
    lock_scale_bone_list=[
        "root","torso","Ankle_ik_L","Ankle_ik_R","toe.L","toe.R","Wrist_ik_L","Wrist_ik_R","Arm_ik_L","Arm_ik_R","Leg_ik_L","Leg_ik_R",
        "hips","chest","neck","head","Shoulder_L","Shoulder_R"
        ]
    for name in lock_location_bone_list:
        if name in rig.data.bones.keys():              
            rig.pose.bones[name].lock_location = [True,True,True]
    for name in lock_scale_bone_list:
        if name in rig.data.bones.keys():  
            rig.pose.bones[name].lock_scale = [True,True,True]
    for name in hide_bone_list:
        if name in rig.data.bones.keys():  
            rig.data.bones[name].hide=True


    #将IK拉伸设为0
    #set IK stretch to 0
    rig.pose.bones["Arm_parent_L"]["IK_Stretch"] = 0
    rig.pose.bones["Arm_parent_R"]["IK_Stretch"] = 0
    rig.pose.bones["Leg_parent_L"]["IK_Stretch"] = 0
    rig.pose.bones["Leg_parent_R"]["IK_Stretch"] = 0

    #替换实心控制器
    #replace controller
    bpy.ops.object.select_all(action='DESELECT')
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
        bpy.ops.object.mode_set(mode = 'OBJECT')



    #将轴心设为各自中点以方便操作
    #set transform pivot point to individual
    bpy.context.view_layer.objects.active=rig
    rig.select_set(True)
    bpy.context.scene.tool_settings.transform_pivot_point = 'INDIVIDUAL_ORIGINS'
    bpy.context.area.type = area
    logging.info("完成")
    alert_error("提示","完成")
    return(True)

def RIG3(context):

    #属性准备阶段
    global mmd_arm
    global mmd_arm2
    global rig
    global mmd_bones_list
    global rig_bones_list

    area = bpy.context.area.type
    bpy.context.area.type = 'VIEW_3D'

    mmd_arm=context.view_layer.objects.active

    scene=context.scene
    mmr_property=scene.mmr_property

    my_dir = os.path.dirname(os.path.realpath(__file__))
    rigify_blend_file = os.path.join(my_dir, "MMR_Rig.blend")

    bpy.ops.object.mode_set(mode = 'OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    context.view_layer.objects.active=mmd_arm
    mmd_arm.select_set(True)
    

    #检查骨架并翻译
    if check_arm()==False:
        return{False}

    #生成字典
    unconnect_bone=['LowerBody']
    mmd_bones_list=mmd_arm.pose.bones.keys()
    preset_dict={}
    bpy.ops.object.mode_set(mode = 'EDIT')
    for bone in mmd_arm.pose.bones:
        name=bone.name
        if bone.mmr_bone_type !='None':
            preset_dict[bone.mmr_bone_type]=bone.name
        if bone.mmr_bone_type in unconnect_bone:
            mmd_arm.data.edit_bones[name].use_connect = False

    bpy.ops.object.mode_set(mode = 'OBJECT')

    #生成第二套骨骼
    mmd_arm2=mmd_arm.copy()
    context.collection.objects.link(mmd_arm2)
    mmd_arm2.data=mmd_arm.data.copy()
    context.view_layer.objects.active=mmd_arm2
    mmd_arm2.select_set(True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bpy.ops.object.mode_set(mode = 'POSE')
    bpy.ops.pose.armature_apply(selected=False)
    bpy.ops.object.mode_set(mode = 'OBJECT')


    #导入metarig骨骼
    #import metarig armature
    rigify_arm_name="MMR_Rig_relative3"
    
    with bpy.data.libraries.load(rigify_blend_file) as (data_from, data_to):
        data_to.objects = [rigify_arm_name]

    rigify_arm=data_to.objects[0]
    context.collection.objects.link(rigify_arm)
    rigify_arm.dimensions=mmd_arm2.dimensions

    bpy.ops.object.select_all(action='DESELECT')
    context.view_layer.objects.active=rigify_arm
    rigify_arm.select_set(True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bpy.ops.object.mode_set(mode = 'EDIT')
    bpy.ops.armature.select_all(action='DESELECT')

    if "thumb.01.L" not in preset_dict:
        rigify_arm.data.edit_bones.remove(rigify_arm.data.edit_bones["thumb.03.L"])
        rigify_arm.data.edit_bones["thumb.02.L"].name='thumb.03.L'
        rigify_arm.data.edit_bones["thumb.01.L"].name='thumb.02.L'

    if "thumb.01.R" not in preset_dict:
        rigify_arm.data.edit_bones.remove(rigify_arm.data.edit_bones["thumb.03.R"])
        rigify_arm.data.edit_bones["thumb.02.R"].name='thumb.03.R'
        rigify_arm.data.edit_bones["thumb.01.R"].name='thumb.02.R'

    rigify_bones_list=rigify_arm.data.edit_bones.keys()
    remain_bone=set(rigify_bones_list)


    #新骨骼匹配方法

    for bone in mmd_arm2.pose.bones:
        bone_type2=bone.mmr_bone_type
        if bone_type2!="None" and bone_type2 in rigify_bones_list:
            rigify_bone=rigify_arm.data.edit_bones[bone_type2]
            if bone.mmr_bone_invert:
                rigify_bone.tail=bone.head
            else:
                rigify_bone.tail=bone.tail

    for bone in mmd_arm2.pose.bones:
        bone_type2=bone.mmr_bone_type
        if bone_type2!="None" and bone_type2 in rigify_bones_list:
            rigify_bone=rigify_arm.data.edit_bones[bone_type2]
            remain_bone.discard(bone_type2)
            if bone.mmr_bone_invert:
                rigify_bone.head=bone.tail
            else:
                rigify_bone.head=bone.head

    #修正部分骨骼

    rigify_arm.data.edit_bones["spine.003"].tail=rigify_arm.data.edit_bones["spine.004"].head
    if rigify_arm.data.edit_bones["spine"].tail==rigify_arm.data.edit_bones["spine.002"].head:
        rigify_arm.data.edit_bones["spine"].tail[2]-=0.01

    rigify_arm.data.edit_bones["spine.006"].tail=rigify_arm.data.edit_bones["spine.006"].head
    rigify_arm.data.edit_bones["spine.006"].tail[2]+=rigify_arm.data.edit_bones["spine.004"].length*3
    if rigify_arm.data.edit_bones["spine.004"].tail==rigify_arm.data.edit_bones["spine.006"].head:
        rigify_arm.data.edit_bones["spine.004"].tail[2]-=0.01

    rigify_arm.data.edit_bones["heel.02.L"].head=(np.array(rigify_arm.data.edit_bones["foot.L"].head)+np.array(rigify_arm.data.edit_bones["foot.L"].head))/2
    rigify_arm.data.edit_bones["heel.02.L"].head[2]=rigify_arm.data.edit_bones["foot.L"].tail[2]
    rigify_arm.data.edit_bones["heel.02.L"].tail=rigify_arm.data.edit_bones["foot.L"].head
    rigify_arm.data.edit_bones["heel.02.L"].tail[0]+=rigify_arm.data.edit_bones["foot.L"].length/10
    rigify_arm.data.edit_bones["heel.02.L"].head[0]-=rigify_arm.data.edit_bones["foot.L"].length/10

    rigify_arm.data.edit_bones["heel.02.R"].head=(np.array(rigify_arm.data.edit_bones["foot.R"].head)+np.array(rigify_arm.data.edit_bones["foot.R"].head))/2
    rigify_arm.data.edit_bones["heel.02.R"].head[2]=rigify_arm.data.edit_bones["foot.R"].tail[2]
    rigify_arm.data.edit_bones["heel.02.R"].tail=rigify_arm.data.edit_bones["foot.R"].head
    rigify_arm.data.edit_bones["heel.02.R"].tail[0]+=rigify_arm.data.edit_bones["foot.R"].length/10
    rigify_arm.data.edit_bones["heel.02.R"].head[0]-=rigify_arm.data.edit_bones["foot.R"].length/10

    rigify_arm.data.edit_bones["hand.L"].tail=(np.array(rigify_arm.data.edit_bones["f_middle.01.L"].head)+np.array(rigify_arm.data.edit_bones["f_ring.01.L"].head))/2
    rigify_arm.data.edit_bones["hand.R"].tail=(np.array(rigify_arm.data.edit_bones["f_middle.01.R"].head)+np.array(rigify_arm.data.edit_bones["f_ring.01.R"].head))/2

    rigify_arm.data.edit_bones["toe.L"].tail=rigify_arm.data.edit_bones["toe.L"].head
    rigify_arm.data.edit_bones["toe.L"].tail[1]+=rigify_arm.data.edit_bones["foot.L"].length/2

    rigify_arm.data.edit_bones["toe.R"].tail=rigify_arm.data.edit_bones["toe.R"].head
    rigify_arm.data.edit_bones["toe.R"].tail[1]+=rigify_arm.data.edit_bones["foot.L"].length/2

    extend_bone=['thumb.03.L','f_index.03.L','f_middle.03.L','f_ring.03.L','f_pinky.03.L','thumb.03.R','f_index.03.R','f_middle.03.R','f_ring.03.R','f_pinky.03.R',]
    for name in extend_bone:
        bone=rigify_arm.data.edit_bones[name]
        parent_bone=bone.parent
        bone.tail=np.array(parent_bone.tail)*2-np.array(parent_bone.head)

    #匹配眼睛骨骼
    invert_eyes=False
    if 'eye.L' in preset_dict and 'eye.R' in preset_dict:
        eye_L=rigify_arm.data.edit_bones['eye.L']
        mmd_eye_L=mmd_arm2.pose.bones[preset_dict['eye.L']]
        eye_L.head[2]=mmd_eye_L.head[2]
        eye_L.head[0]=max(mmd_eye_L.head[0],mmd_eye_L.tail[0])
        eye_L.head[1]=min(mmd_eye_L.head[1],mmd_eye_L.tail[1])
        eye_L.tail=eye_L.head
        eye_L.tail[1]-=0.1

        eye_R=rigify_arm.data.edit_bones['eye.R']
        mmd_eye_R=mmd_arm2.pose.bones[preset_dict['eye.R']]
        eye_R.head[2]=mmd_eye_R.head[2]
        eye_R.head[0]=min(mmd_eye_R.head[0],mmd_eye_R.tail[0])
        eye_R.head[1]=min(mmd_eye_R.head[1],mmd_eye_R.tail[1])
        eye_R.tail=eye_R.head
        eye_R.tail[1]-=0.1

        if eye_L.head[0]<eye_R.head[0]:
            eye_R.name='1'
            eye_L.name='eye.R'
            eye_R.name='eye.L'
            invert_eyes=True

    positive_z_bone=[
        'shoulder.L','upper_arm.L','forearm.L','shoulder.R','upper_arm.R','forearm.R',
        'f_index.01.L','f_index.02.L','f_index.03.L',
        'f_middle.01.L','f_middle.02.L','f_middle.03.L',
        'f_ring.01.L','f_ring.02.L','f_ring.03.L',
        'f_pinky.01.L','f_pinky.02.L','f_pinky.03.L',
        'f_index.01.R','f_index.02.R','f_index.03.R',
        'f_middle.01.R','f_middle.02.R','f_middle.03.R',
        'f_ring.01.R','f_ring.02.R','f_ring.03.R',
        'f_pinky.01.R','f_pinky.02.R','f_pinky.03.R',
    ]
    negative_y_bone=[
        'hand.L','hand.R',
        'thumb.01.L','thumb.02.L','thumb.03.L',
        'thumb.01.R','thumb.02.R','thumb.03.R',
    ]

    bpy.ops.armature.select_all(action='DESELECT')
    rigify_arm.data.show_axes = True

    for name in positive_z_bone:
        rigify_arm.data.edit_bones[name].select=True
        rigify_arm.data.edit_bones[name].select_head=True
        rigify_arm.data.edit_bones[name].select_tail=True

    bpy.ops.armature.calculate_roll(type='GLOBAL_POS_Z')
    
    bpy.ops.armature.select_all(action='DESELECT')

    for name in negative_y_bone:
        rigify_arm.data.edit_bones[name].select=True
        rigify_arm.data.edit_bones[name].select_head=True
        rigify_arm.data.edit_bones[name].select_tail=True
    
    bpy.ops.armature.calculate_roll(type='GLOBAL_NEG_Y')

    #生成控制器
    if mmr_property.debug:
        bpy.context.area.type = area
        return

    bpy.ops.object.mode_set(mode = 'OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    context.view_layer.objects.active=rigify_arm
    rigify_arm.select_set(True)

    bpy.ops.pose.rigify_generate()
    rig=bpy.data.objects["rig"]
    rig_bones_list=rig.data.bones.keys()

    #开始调整生成的控制器
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active=mmd_arm
    rig.select_set(True)
    mmd_arm2.select_set(True)

    #添加约束
    #add constraint

    constraints_list=[
        ("ORG-upper_arm.L","upper_arm.L",True,True),
        ("ORG-upper_arm.R","upper_arm.R",True,True),
        ("ORG-forearm.L","forearm.L",True,True),
        ("ORG-forearm.R","forearm.R",True,True),
        ("ORG-shoulder.L","shoulder.L",True,True),
        ("ORG-shoulder.R","shoulder.R",True,True),
        ("ORG-hand.L","hand.L",True,True),
        ("ORG-hand.R","hand.R",True,True),
        #("MCH-Elbow_tweak_L.001","HandTwist_L",True,False),
        #("MCH-Elbow_tweak_R.001","HandTwist_R",True,False),
        #("MCH-Arm_tweak_L.001","ArmTwist_L",True,False),
        #("MCH-Arm_tweak_R.001","ArmTwist_R",True,False),

        ("ORG-thigh.L","thigh.L",True,True),
        ("ORG-thigh.R","thigh.R",True,True),
        ("ORG-shin.L","shin.L",True,True),
        ("ORG-shin.R","shin.R",True,True),

        ("DEF-foot.L","foot.L",True,True),
        ("DEF-foot.R","foot.R",True,True),
        ("DEF-foot.L","LegIK_L",False,True),
        ("DEF-foot.R","LegIK_R",False,True),
        ("DEF-toe.L","toe.L",False,True),
        ("DEF-toe.R","toe.R",False,True),

        ("spine_fk.003","spine.003",True,True),
        ("spine_fk.002","spine.002",True,True),
        ("spine_fk.001","spine.001",True,True),

        ("spine_fk","spine",True,True),
        ("torso","Center",True,True),
        ("DEF-spine.004","spine.004",True,True),
        ("DEF-spine.006","spine.006",True,True),
        ("root","ParentNode",True,True),

        ("ORG-thumb.01.L","thumb.01.L",True,True),
        ("ORG-thumb.01.R","thumb.01.R",True,True),
        ("ORG-thumb.02.L","thumb.02.L",True,True),
        ("ORG-thumb.02.R","thumb.02.R",True,True),
        ("ORG-thumb.03.L","thumb.03.L",True,True),
        ("ORG-thumb.03.R","thumb.03.R",True,True),

        ("ORG-f_index.01.L","f_index.01.L",True,True),
        ("ORG-f_index.01.R","f_index.01.R",True,True),
        ("ORG-f_index.02.L","f_index.02.L",True,True),
        ("ORG-f_index.02.R","f_index.02.R",True,True),
        ("ORG-f_index.03.L","f_index.03.L",True,True),
        ("ORG-f_index.03.R","f_index.03.R",True,True),

        ("ORG-f_middle.01.L","f_middle.01.L",True,True),
        ("ORG-f_middle.01.R","f_middle.01.R",True,True),
        ("ORG-f_middle.02.L","f_middle.02.L",True,True),
        ("ORG-f_middle.02.R","f_middle.02.R",True,True),
        ("ORG-f_middle.03.L","f_middle.03.L",True,True),
        ("ORG-f_middle.03.R","f_middle.03.R",True,True),

        ("ORG-f_ring.01.L","f_ring.01.L",True,True),
        ("ORG-f_ring.01.R","f_ring.01.R",True,True),
        ("ORG-f_ring.02.L","f_ring.02.L",True,True),
        ("ORG-f_ring.02.R","f_ring.02.R",True,True),
        ("ORG-f_ring.03.L","f_ring.03.L",True,True),
        ("ORG-f_ring.03.R","f_ring.03.R",True,True),

        ("ORG-f_pinky.01.L","f_pinky.01.L",True,True),
        ("ORG-f_pinky.01.R","f_pinky.01.R",True,True),
        ("ORG-f_pinky.01.L","f_pinky.01.L",True,True),
        ("ORG-f_pinky.01.R","f_pinky.01.R",True,True),
        ("ORG-f_pinky.01.L","f_pinky.01.L",True,True),
        ("ORG-f_pinky.01.R","f_pinky.01.R",True,True),
    ]

    if invert_eyes:
        constraints_list.append(("ORG-eye.L","eye.R",True,False))
        constraints_list.append(("ORG-eye.R","eye.L",True,False))
    else:
        constraints_list.append(("ORG-eye.L","eye.L",True,False))
        constraints_list.append(("ORG-eye.R","eye.R",True,False))

    add_constraint3(constraints_list,preset_dict)

    #上半身控制器

    if mmr_property.upper_body_controller:
        bpy.ops.object.mode_set(mode = 'EDIT')
        torso_parent=rig.data.edit_bones.new(name='torso_parent')
        torso_parent.head=rig.data.edit_bones['root'].head
        torso_parent.tail=rig.data.edit_bones['root'].tail
        torso_parent.roll=rig.data.edit_bones['root'].roll
        torso_parent.length=rig.data.edit_bones['root'].length/3
        torso_parent.head[2]=torso_parent.tail[2]=rig.data.edit_bones['shin_fk.L'].head[2]
        torso_parent.parent=rig.data.edit_bones['root']
        rig.data.edit_bones['MCH-torso.parent'].parent=torso_parent
        rig.data.edit_bones['MCH-hand_ik.parent.L'].parent=torso_parent
        rig.data.edit_bones['MCH-hand_ik.parent.R'].parent=torso_parent
        
        bpy.ops.object.mode_set(mode = 'POSE')
        rig.pose.bones["torso_parent"].custom_shape = bpy.data.objects["WGT-rig_root"]
        rig.pose.bones["torso_parent"].custom_shape_scale = 0.4
        rig.pose.bones['torso_parent'].mmd_bone.name_j='グルーブ'
        rig.pose.bones["upper_arm_parent.L"]["IK_parent"] = 0
        rig.pose.bones["upper_arm_parent.R"]["IK_parent"] = 0
        rig.pose.bones["torso"]["torso_parent"] = 0
        rig.data.bones["torso_parent"].layers=rig.data.bones["torso"].layers


    else:
        rig.pose.bones['MCH-torso.parent'].mmd_bone.name_j='グルーブ'


    #肩膀联动
    #IK shoulder
    rig.pose.bones["shoulder.L"].ik_stiffness_x = 0.7
    rig.pose.bones["shoulder.L"].ik_stiffness_y = 0.7
    rig.pose.bones["shoulder.L"].ik_stiffness_z = 0.7
    rig.pose.bones["shoulder.R"].ik_stiffness_x = 0.7
    rig.pose.bones["shoulder.R"].ik_stiffness_y = 0.7
    rig.pose.bones["shoulder.R"].ik_stiffness_z = 0.7

    rig.pose.bones["ORG-shoulder.L"].ik_stiffness_x = 0.7
    rig.pose.bones["ORG-shoulder.L"].ik_stiffness_y = 0.7
    rig.pose.bones["ORG-shoulder.L"].ik_stiffness_z = 0.7
    rig.pose.bones["ORG-shoulder.R"].ik_stiffness_x = 0.7
    rig.pose.bones["ORG-shoulder.R"].ik_stiffness_y = 0.7
    rig.pose.bones["ORG-shoulder.R"].ik_stiffness_z = 0.7

    if mmr_property.auto_shoulder:
        bpy.ops.object.mode_set(mode = 'EDIT')
        rig.data.edit_bones["hand_ik.L"].parent=rig.data.edit_bones["shoulder.L"]
        rig.pose.bones["MCH-forearm_tweak.L"].constraints["IK.001"].chain_count = 3
        rig.pose.bones["MCH-forearm_tweak.L"].constraints["IK"].chain_count = 3

        rig.data.edit_bones["hand_ik.R"].parent=rig.data.edit_bones["shoulder.L"]
        rig.pose.bones["MCH-forearm_tweak.R"].constraints["IK.001"].chain_count = 3
        rig.pose.bones["MCH-forearm_tweak.R"].constraints["IK"].chain_count = 3


    bpy.ops.object.mode_set(mode = 'POSE')

    
    #修正rigifyIK控制器范围限制
    rig.pose.bones["MCH-shin_ik.L"].use_ik_limit_x = True
    rig.pose.bones["MCH-shin_ik.R"].use_ik_limit_x = True
    rig.pose.bones["MCH-shin_ik.L"].ik_min_x = -0.0174533
    rig.pose.bones["MCH-shin_ik.R"].ik_min_x = -0.0174533

    rig.pose.bones["MCH-forearm_ik.L"].use_ik_limit_z = True
    rig.pose.bones["MCH-forearm_ik.R"].use_ik_limit_z = True
    rig.pose.bones["MCH-forearm_ik.L"].ik_max_z = 0
    rig.pose.bones["MCH-forearm_ik.R"].ik_min_z = 0

    #极向目标开关
    #pole target
    rig.pose.bones["MCH-forearm_ik.L"].constraints["IK.001"].pole_angle = 3.14159
    if mmr_property.pole_target:
        rig.pose.bones["thigh_parent.L"]["pole_vector"] = 1
        rig.pose.bones["thigh_parent.R"]["pole_vector"] = 1
        rig.pose.bones["upper_arm_parent.L"]["pole_vector"] = 1
        rig.pose.bones["upper_arm_parent.R"]["pole_vector"] = 1

    #将IK拉伸设为0
    #set IK stretch to 0
    rig.pose.bones["upper_arm_parent.L"]["IK_Stretch"] = 0
    rig.pose.bones["upper_arm_parent.R"]["IK_Stretch"] = 0
    rig.pose.bones["thigh_parent.L"]["IK_Stretch"] = 0
    rig.pose.bones["thigh_parent.R"]["IK_Stretch"] = 0

    #捩骨约束
    #Twist constrains
    if 'HandTwist_L' in preset_dict and 'Wrist_L' in preset_dict:
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

    if 'HandTwist_R' in mmd_bones_list:
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

    if 'ArmTwist_L' in mmd_bones_list:
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

    if 'ArmTwist_R' in mmd_bones_list:
        c1=mmd_arm.pose.bones[preset_dict['ArmTwist_R']].constraints.new(type='COPY_ROTATION')
        c1.target=rig
        c1.subtarget='ORG-forearm.R'
        c1.mix_mode = 'BEFORE'
        c1.target_space = 'LOCAL'
        c1.owner_space = 'LOCAL'
        c2=mmd_arm.pose.bones[preset_dict['ArmTwist_R']].constraints.new(type='DAMPED_TRACK')
        c2.target=rig
        c2.subtarget='ORG-forearm.R'
        mmd_arm.data.bones[preset_dict['ArmTwist_R']].hide=False

    #写入PMX骨骼名称数据
    #write PMX bone name
    rig_bones_list=rig.data.bones.keys()

    PMX_dict={
    'root':'全ての親','torso':'センター','hips':'下半身','UpperBody_fk':'上半身','UpperBody2_fk':'上半身2','neck':'首','head':'頭','Eyes_Rig':'両目',
    'Leg_ik_L':'左足','Ankle_ik_L':'左足ＩＫ','ToeTipIK_L':'左つま先ＩＫ','Leg_ik_R':'右足','Ankle_ik_R':'右足ＩＫ','ToeTipIK_R':'右つま先ＩＫ',
    'Shoulder_L':'左肩','Arm_fk_L':'左腕','Elbow_fk_L':'左ひじ','Wrist_fk_L':'左手首','Shoulder_R':'右肩','Arm_fk_R':'右腕','Elbow_fk_R':'右ひじ','Wrist_fk_R':'右手首',
    'Thumb0_L':'左親指０','Thumb1_L':'左親指１','Thumb2_L':'左親指２',
    'IndexFinger1_L':'左人指１','IndexFinger2_L':'左人指２','IndexFinger3_L':'左人指３',
    'MiddleFinger1_L':'左中指１','MiddleFinger2_L':'左中指２','MiddleFinger3_L':'左中指３',
    'RingFinger1_L':'左薬指１','RingFinger2_L':'左薬指２','RingFinger3_L':'左薬指３',
    'LittleFinger1_L':'左小指１','LittleFinger2_L':'左小指２','LittleFinger3_L':'左小指３',
    'Thumb0_R':'右親指０','Thumb1_R':'右親指１','Thumb2_R':'右親指２',
    'IndexFinger1_R':'右人指１','IndexFinger2_R':'右人指２','IndexFinger3_R':'右人指３',
    'MiddleFinger1_R':'右中指１','MiddleFinger2_R':'右中指２','MiddleFinger3_R':'右中指３',
    'RingFinger1_R':'右薬指１','RingFinger2_R':'右薬指２','RingFinger3_R':'右薬指３',
    'LittleFinger1_R':'右小指１','LittleFinger2_R':'右小指２','LittleFinger3_R':'右小指３'
    }

    for key,value in PMX_dict.items():
        if key in rig_bones_list:
            rig.pose.bones[key].mmd_bone.name_j=value
    
    bpy.ops.object.mode_set(mode = 'OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    #删除多余骨架
    #delete metarig armatrue
    rigify_arm.select_set(True)
    mmd_arm2.select_set(True)
    bpy.ops.object.delete(use_global=True)
    #隐藏原骨架，把新骨架设为永远在前
    #hide old armature
    rig.show_in_front = True
    mmd_arm.hide = True
    rig.name=mmd_arm.name+'_Rig'

    #缩小root控制器
    #reduce size
    rig.pose.bones["root"].custom_shape_scale = 0.4


    #隐藏部分控制器
    #hide some controller
    rig.data.layers[1] = False
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
    if 'Eye_L' not in preset_dict or 'Eye_R' not in preset_dict:
        rig.data.layers[0] = False

    #锁定移动的骨骼列表
    #lock the location of these bone
    lock_location_bone_list=[
        "upper_arm_ik.L","upper_arm_ik.R","thigh_ik.L","thigh_ik.R","hips","chest","neck","head","shoulder.L","shoulder.R","thumb.01_master.L","thumb.01_master.R",
        "thumb.02_master.L","thumb.02_master.R","f_index.01_master.L","f_index.01_master.R","f_middle.01_master.L","f_middle.01_master.R",
        "f_ring.01_master.L","f_ring.01_master.R","f_pinky.01_master.L","f_pinky.01_master.R"
        ]
    #隐藏的骨骼列表
    #hide these bone
    hide_bone_list=[
        'upper_arm_parent.L','upper_arm_parent.R','thigh_parent.L','thigh_parent.R',"foot_heel_ik.L","foot_heel_ik.R",'master_eye.L','master_eye.R',
        'ear.L','ear.R','nose_master','teeth.T','teeth.B','tongue_master','jaw_master'
        ]
    #锁定缩放的骨骼列表
    #lock the scale of these bone
    lock_scale_bone_list=[
        "root","torso","foot_ik.L","foot_ik.R","toe.L","toe.R","hand_ik.L","hand_ik.R","upper_arm_ik.L","upper_arm_ik.R","thigh_ik.L","thigh_ik.R",
        "hips","chest","neck","head","shoulder.L","shoulder.R"
        ]
    for name in lock_location_bone_list:
        if name in rig.data.bones.keys():              
            rig.pose.bones[name].lock_location = [True,True,True]
    for name in lock_scale_bone_list:
        if name in rig.data.bones.keys():  
            rig.pose.bones[name].lock_scale = [True,True,True]
    for name in hide_bone_list:
        if name in rig.data.bones.keys():  
            rig.data.bones[name].hide=True

    #替换实心控制器
    #replace controller
    bpy.ops.object.select_all(action='DESELECT')
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
        bpy.ops.object.mode_set(mode = 'OBJECT')



    #将轴心设为各自中点以方便操作
    #set transform pivot point to individual
    bpy.context.view_layer.objects.active=rig
    rig.select_set(True)
    bpy.context.scene.tool_settings.transform_pivot_point = 'INDIVIDUAL_ORIGINS'
    bpy.context.area.type = area
    logging.info("完成")
    alert_error("提示","完成")
    return(True)


def set_min_ik_loop(arm,min_ik_loop=10):
    if check_arm(arm)==False:
        return
    for bone in arm.pose.bones:
        for c in bone.constraints:
            if c.type=='IK':
                if c.iterations < min_ik_loop:
                    c.iterations=min_ik_loop
    return(True)

class OT_Generate_Rig(Operator):
    bl_idname = "mmr.generate_rig" # python 提示
    bl_label = "Interface"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self,context):
        RIG(context)
        return{"FINISHED"}

class OT_Set_Min_IK_Loop(Operator):
    bl_idname = "mmr.set_min_ik_loop" # python 提示
    bl_label = "Interface"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self,context):
        scene=context.scene
        mmr_property=scene.mmr_property
        set_min_ik_loop(context.view_layer.objects.active,mmr_property.min_ik_loop)
        return{"FINISHED"}

Class_list=[OT_Generate_Rig,OT_Set_Min_IK_Loop]