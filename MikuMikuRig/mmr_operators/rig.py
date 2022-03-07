import bpy
import os
import logging
import mathutils
from bpy.types import Operator
from . import preset
from . import extra

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

def add_constraint3(constraint_List,preset_dict):
    global match_bone_nunber
    match_bone_nunber=0
    rig_bones_list=rig.data.bones.keys()

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
            match_bone_nunber+=1
            index_list.append(i)
            mmd_arm.data.bones[From].hide=False

    bpy.ops.object.mode_set(mode = 'EDIT')

    for i in index_list:
        From = preset_dict[constraint_List[i][1]]
        From1=constraint_List[i][1]
        To = constraint_List[i][0]
        parent_name=From1 + '_parent'
        parent_bone=rig.data.edit_bones.new(name=parent_name)
        parent_bone.matrix=mmd_arm.pose.bones[From].matrix
        parent_bone.tail=mmd_arm.pose.bones[From].tail
        parent_bone.parent=rig.data.edit_bones[To]
        parent_bone.layers=rig.data.edit_bones[To].layers

    bpy.ops.object.mode_set(mode = 'POSE')

    for i in index_list:
        From = preset_dict[constraint_List[i][1]]
        From1=constraint_List[i][1]
        To = constraint_List[i][0]
        rotation=constraint_List[i][2]
        location=constraint_List[i][3]
        con= mmd_arm.pose.bones[From].constraints
        for c in con:
            c.mute=True
        parent_name=From1 + '_parent'
        rig.data.bones[parent_name].hide=True
        if location:
            if rotation:
                COPY_TRANSFORMS=con.new(type='COPY_TRANSFORMS')
                COPY_TRANSFORMS.target = rig
                COPY_TRANSFORMS.subtarget = parent_name
                COPY_TRANSFORMS.name="rel_transforms"
                COPY_TRANSFORMS.mix_mode = 'REPLACE'
                COPY_TRANSFORMS.owner_space = 'WORLD'
                COPY_TRANSFORMS.target_space = 'WORLD'
            else:
                COPY_LOCATION=mmd_arm.pose.bones[From].constraints.new(type='COPY_LOCATION')
                COPY_LOCATION.target = rig
                COPY_LOCATION.subtarget = parent_name
                COPY_LOCATION.name="rel_location"
        else:
            if rotation:
                COPY_TRANSFORMS=con.new(type='COPY_ROTATION')
                COPY_TRANSFORMS.target = rig
                COPY_TRANSFORMS.subtarget = parent_name
                COPY_TRANSFORMS.name="rel_rotation"

def RIG2(context):

    #属性准备阶段
    global mmd_arm
    global rig
    global mmd_bones_list
    global rig_bones_list

    area = bpy.context.area.type
    context.area.type = 'VIEW_3D'

    mmd_arm=context.view_layer.objects.active
    extra.set_min_ik_loop(mmd_arm,10)

    scene=context.scene
    mmr_property=scene.mmr_property

    my_dir = os.path.dirname(os.path.realpath(__file__))
    rigify_blend_file = os.path.join(my_dir, "MMR_Rig.blend")

    bpy.ops.object.mode_set(mode = 'OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    context.view_layer.objects.active=mmd_arm
    mmd_arm.select_set(True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    

    #检查骨架
    if check_arm()==False:
        return{False}

    #生成字典
    unconnect_bone=['spine']
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

    #添加骨骼弯曲
    def world_rotate(posebone_a,posebone_b,vector=(0,1,0),size=-0.2618):

        v1=posebone_b.head-posebone_a.head
        v2=v1.cross(vector)
        mat1=mathutils.Matrix.Rotation(size,4,v2)
        mat2=posebone_a.matrix.inverted() @ mat1 @ posebone_a.matrix
        q=mat2.to_quaternion()
        posebone_a.rotation_mode = 'QUATERNION'
        posebone_a.rotation_quaternion = q

    rotate_list=[
        ['forearm.L','hand.L',(0,1,0),-0.2618],
        ['forearm.R','hand.R',(0,1,0),-0.2618],
    ]
    if mmr_property.bent_IK_bone:
        for order in rotate_list:
            if order[0] not in preset_dict or order[1] not in preset_dict:
                continue
            posebone_a=mmd_arm.pose.bones[preset_dict[order[0]]]
            posebone_b=mmd_arm.pose.bones[preset_dict[order[1]]]
            world_rotate(posebone_a,posebone_b,order[2],order[3])


    #导入metarig骨骼
    #import metarig armature
    rigify_arm_name="MMR_Rig_relative3"
    
    with bpy.data.libraries.load(rigify_blend_file) as (data_from, data_to):
        data_to.objects = [rigify_arm_name]

    rigify_arm=data_to.objects[0]
    context.collection.objects.link(rigify_arm)

    #检测手指弯曲
    mmd_bones=mmd_arm.pose.bones
    rigify_bone=rigify_arm.pose.bones
    bent_finger=False
    finger_name1=preset_dict['f_index.01.L']
    finger_name2=preset_dict['f_index.02.L']
    finger_name3=preset_dict['f_index.03.L']
    finger_bone1=mmd_bones[finger_name1]
    finger_bone2=mmd_bones[finger_name2]
    finger_bone3=mmd_bones[finger_name3]
    finger_v1=finger_bone2.head-finger_bone1.head
    finger_v2=finger_bone3.head-finger_bone2.head
    finger_angle=finger_v1.angle(finger_v2)
    print('finger angle='+str(finger_angle))
    bent_finger = finger_angle>0.26
    if bent_finger:
        finger_list=['f_index.01.L','f_middle.01.L','f_ring.01.L','f_pinky.01.L','f_index.01.R','f_middle.01.R','f_ring.01.R','f_pinky.01.R','thumb.01.L','thumb.01.R',]
        for name in finger_list:
            bone=rigify_bone[name]
            bone.rigify_parameters.primary_rotation_axis='automatic'
    #检测手臂弯曲
    bent_arm=False
    arm_name1=preset_dict['upper_arm.L']
    arm_name2=preset_dict['forearm.L']
    arm_name3=preset_dict['hand.L']
    arm_bone1=mmd_bones[arm_name1]
    arm_bone2=mmd_bones[arm_name2]
    arm_bone3=mmd_bones[arm_name3]
    arm_v1=arm_bone2.head-arm_bone1.head
    arm_v2=arm_bone3.head-arm_bone2.head
    arm_angle=arm_v1.angle(arm_v2)
    print('arm angle='+str(finger_angle))
    bent_arm = arm_angle>0.26
    if bent_arm:
        arm_list=['upper_arm.L','upper_arm.R']
        for name in arm_list:
            bone=rigify_bone[name]
            bone.rigify_parameters.primary_rotation_axis='automatic'

    #自动缩放
    scale=(mmd_arm.pose.bones[preset_dict['spine.006']].head[2]*mmd_arm.scale[2])/(rigify_arm.pose.bones['spine.006'].head[2]*rigify_arm.scale[2])
    rigify_arm.scale*=scale

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

    for bone in mmd_arm.pose.bones:
        bone_type=bone.mmr_bone_type
        if bone_type!="None" and bone_type in rigify_bones_list:
            rigify_bone=rigify_arm.data.edit_bones[bone_type]
            if bone.mmr_bone_invert:
                rigify_bone.tail=bone.head
            else:
                rigify_bone.tail=bone.tail

    for bone in mmd_arm.pose.bones:
        bone_type=bone.mmr_bone_type
        if bone_type!="None" and bone_type in rigify_bones_list:
            rigify_bone=rigify_arm.data.edit_bones[bone_type]
            remain_bone.discard(bone_type)
            if bone.mmr_bone_invert:
                rigify_bone.head=bone.tail
            else:
                rigify_bone.head=bone.head

    #修正部分骨骼

    rigify_arm.data.edit_bones["spine.003"].tail=rigify_arm.data.edit_bones["spine.004"].head
    if rigify_arm.data.edit_bones["spine"].tail==rigify_arm.data.edit_bones["spine.002"].head:
        rigify_arm.data.edit_bones["spine"].tail[2]-=0.01
    if rigify_arm.data.edit_bones["spine.001"].tail==rigify_arm.data.edit_bones["spine.003"].head:
        rigify_arm.data.edit_bones["spine.001"].tail[2]-=0.01

    rigify_arm.data.edit_bones["spine.006"].tail=rigify_arm.data.edit_bones["spine.006"].head
    rigify_arm.data.edit_bones["spine.006"].tail[2]+=rigify_arm.data.edit_bones["spine.004"].length*3
    if rigify_arm.data.edit_bones["spine.004"].tail==rigify_arm.data.edit_bones["spine.006"].head:
        rigify_arm.data.edit_bones["spine.004"].tail[2]-=0.01

    rigify_arm.data.edit_bones["hand.L"].tail=(rigify_arm.data.edit_bones["f_middle.01.L"].head+rigify_arm.data.edit_bones["f_ring.01.L"].head)/2
    rigify_arm.data.edit_bones["hand.R"].tail=(rigify_arm.data.edit_bones["f_middle.01.R"].head+rigify_arm.data.edit_bones["f_ring.01.R"].head)/2

    if 'ToeTipIK_L' in preset_dict and "toe.L" not in preset_dict:
        rigify_arm.data.edit_bones["toe.L"].head=mmd_arm.pose.bones[preset_dict['ToeTipIK_L']].head
    if 'ToeTipIK_R' in preset_dict and "toe.R" not in preset_dict:
        rigify_arm.data.edit_bones["toe.R"].head=mmd_arm.pose.bones[preset_dict['ToeTipIK_R']].head

    rigify_arm.data.edit_bones["toe.L"].tail=rigify_arm.data.edit_bones["toe.L"].head
    rigify_arm.data.edit_bones["toe.L"].tail[1]-=rigify_arm.data.edit_bones["foot.L"].length/2

    rigify_arm.data.edit_bones["toe.R"].tail=rigify_arm.data.edit_bones["toe.R"].head
    rigify_arm.data.edit_bones["toe.R"].tail[1]-=rigify_arm.data.edit_bones["foot.L"].length/2

    rigify_arm.data.edit_bones["heel.02.L"].head=rigify_arm.data.edit_bones["foot.L"].head
    rigify_arm.data.edit_bones["heel.02.L"].head[2]=rigify_arm.data.edit_bones["foot.L"].tail[2]
    rigify_arm.data.edit_bones["heel.02.L"].tail=rigify_arm.data.edit_bones["heel.02.L"].head
    rigify_arm.data.edit_bones["heel.02.L"].tail[0]+=rigify_arm.data.edit_bones["foot.L"].length/10
    rigify_arm.data.edit_bones["heel.02.L"].head[0]-=rigify_arm.data.edit_bones["foot.L"].length/10

    rigify_arm.data.edit_bones["heel.02.R"].head=rigify_arm.data.edit_bones["foot.R"].head
    rigify_arm.data.edit_bones["heel.02.R"].head[2]=rigify_arm.data.edit_bones["foot.R"].tail[2]
    rigify_arm.data.edit_bones["heel.02.R"].tail=rigify_arm.data.edit_bones["heel.02.R"].head
    rigify_arm.data.edit_bones["heel.02.R"].tail[0]-=rigify_arm.data.edit_bones["foot.R"].length/10
    rigify_arm.data.edit_bones["heel.02.R"].head[0]+=rigify_arm.data.edit_bones["foot.R"].length/10

    extend_bone=['thumb.03.L','f_index.03.L','f_middle.03.L','f_ring.03.L','f_pinky.03.L','thumb.03.R','f_index.03.R','f_middle.03.R','f_ring.03.R','f_pinky.03.R',]
    for name in extend_bone:
        bone=rigify_arm.data.edit_bones[name]
        parent_bone=bone.parent
        bone.tail=parent_bone.tail*2-parent_bone.head

    #匹配眼睛骨骼
    invert_eyes=False
    if 'eye.L' in preset_dict and 'eye.R' in preset_dict:
        eye_L=rigify_arm.data.edit_bones['eye.L']
        mmd_eye_L=mmd_arm.pose.bones[preset_dict['eye.L']]
        eye_L.head[2]=mmd_eye_L.head[2]
        eye_L.head[0]=max(mmd_eye_L.head[0],mmd_eye_L.tail[0])
        eye_L.head[1]=min(mmd_eye_L.head[1],mmd_eye_L.tail[1])
        eye_L.tail=eye_L.head
        eye_L.tail[1]-=0.1

        eye_R=rigify_arm.data.edit_bones['eye.R']
        mmd_eye_R=mmd_arm.pose.bones[preset_dict['eye.R']]
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

    #修正骨骼轴向
    positive_z_bone=[
        'shoulder.L','shoulder.R',
    ]
    positive_x_bone=[
        'f_index.01.L','f_index.02.L','f_index.03.L',
        'f_middle.01.L','f_middle.02.L','f_middle.03.L',
        'f_ring.01.L','f_ring.02.L','f_ring.03.L',
        'f_pinky.01.L','f_pinky.02.L','f_pinky.03.L',
    ]
    negative_x_bone=[
        'f_index.01.R','f_index.02.R','f_index.03.R',
        'f_middle.01.R','f_middle.02.R','f_middle.03.R',
        'f_ring.01.R','f_ring.02.R','f_ring.03.R',
        'f_pinky.01.R','f_pinky.02.R','f_pinky.03.R',
    ]
    negative_y_bone=[
        'hand.L','upper_arm.L','forearm.L','hand.R','upper_arm.R','forearm.R',
        'thumb.01.L','thumb.02.L','thumb.03.L',
        'thumb.01.R','thumb.02.R','thumb.03.R',
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

    for name in positive_x_bone:
        if name in rigify_bones_list:
            rigify_arm.data.edit_bones[name].select=True
            rigify_arm.data.edit_bones[name].select_head=True
            rigify_arm.data.edit_bones[name].select_tail=True

    bpy.ops.armature.calculate_roll(type='GLOBAL_POS_X')

    bpy.ops.armature.select_all(action='DESELECT')

    for name in negative_x_bone:
        if name in rigify_bones_list:
            rigify_arm.data.edit_bones[name].select=True
            rigify_arm.data.edit_bones[name].select_head=True
            rigify_arm.data.edit_bones[name].select_tail=True

    bpy.ops.armature.calculate_roll(type='GLOBAL_NEG_X')
    
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

    #删除无用骨架
    bpy.data.objects.remove(rigify_arm,do_unlink=True)


    #开始调整生成的控制器
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active=mmd_arm
    rig.select_set(True)

    #肩膀联动

    if mmr_property.auto_shoulder:
        bpy.ops.object.mode_set(mode = 'EDIT')
        auto_shulder_L=Center=rig.data.edit_bones.new(name='auto_shulder_L')
        auto_shulder_L.head=rig.data.edit_bones['shoulder.L'].head
        auto_shulder_L.tail=rig.data.edit_bones['shoulder.L'].tail
        auto_shulder_L.roll=rig.data.edit_bones['shoulder.L'].roll
        auto_shulder_L.parent=rig.data.edit_bones['upper_arm_ik.L']

        auto_shulder_R=Center=rig.data.edit_bones.new(name='auto_shulder_R')
        auto_shulder_R.head=rig.data.edit_bones['shoulder.R'].head
        auto_shulder_R.tail=rig.data.edit_bones['shoulder.R'].tail
        auto_shulder_R.roll=rig.data.edit_bones['shoulder.R'].roll
        auto_shulder_R.parent=rig.data.edit_bones['upper_arm_ik.R']

        bpy.ops.object.mode_set(mode = 'POSE')
        shoulder_L=rig.pose.bones["shoulder.L"]
        auto_shulder_L=rig.pose.bones["auto_shulder_L"]
        shoulder_L_c=shoulder_L.constraints.new('COPY_ROTATION')
        shoulder_L_c.name='MMR_auto_shoulder'
        shoulder_L_c.target=rig
        shoulder_L_c.subtarget='auto_shulder_L'
        shoulder_L_c.influence=0.5
        auto_shoulder_L_c=auto_shulder_L.constraints.new('LIMIT_ROTATION')
        auto_shoulder_L_c.name='MMR_auto_shoulder'
        auto_shoulder_L_c.use_limit_x=True
        auto_shoulder_L_c.min_x = -0.35
        auto_shoulder_L_c.max_x = 1.57
        auto_shoulder_L_c.owner_space = 'LOCAL_WITH_PARENT'
        auto_shulder_L.bone.layers=rig.data.bones["ORG-shoulder.L"].layers

        shoulder_R=rig.pose.bones["shoulder.R"]
        auto_shulder_R=rig.pose.bones["auto_shulder_R"]
        shoulder_R_c=shoulder_R.constraints.new('COPY_ROTATION')
        shoulder_R_c.name='MMR_auto_shoulder'
        shoulder_R_c.target=rig
        shoulder_R_c.subtarget='auto_shulder_R'
        shoulder_R_c.influence=0.5
        auto_shoulder_R_c=auto_shulder_R.constraints.new('LIMIT_ROTATION')
        auto_shoulder_R_c.name='MMR_auto_shoulder'
        auto_shoulder_R_c.use_limit_x=True
        auto_shoulder_R_c.min_x = -0.35
        auto_shoulder_R_c.max_x = 1.57
        auto_shoulder_R_c.owner_space = 'LOCAL_WITH_PARENT'
        auto_shulder_R.bone.layers=rig.data.bones["ORG-shoulder.R"].layers

    #上半身控制器

    if mmr_property.upper_body_controller:
        bpy.ops.object.mode_set(mode = 'EDIT')
        Center=rig.data.edit_bones.new(name='Center')
        Center.head=rig.data.edit_bones['root'].head
        Center.tail=rig.data.edit_bones['root'].tail
        Center.roll=rig.data.edit_bones['root'].roll
        Center.length=rig.data.edit_bones['root'].length/3
        Center.head[2]=Center.tail[2]=rig.data.edit_bones['shin_fk.L'].head[2]

        '''Groove=rig.data.edit_bones.new(name='Groove')
        Groove.head=rig.data.edit_bones['root'].head
        Groove.tail=rig.data.edit_bones['root'].tail
        Groove.roll=rig.data.edit_bones['root'].roll
        Groove.length=rig.data.edit_bones['root'].length/3
        if 'Groove' in preset_dict:
            Groove.head[2]=Groove.tail[2]=mmd_bones[preset_dict['Groove']].head[2]
        else:
            Groove.head[2]=Groove.tail[2]=rig.data.edit_bones['shin_fk.L'].head[2]'''

        rig.data.edit_bones['MCH-torso.parent'].parent=Center
        rig.data.edit_bones['MCH-hand_ik.parent.L'].parent=Center
        rig.data.edit_bones['MCH-hand_ik.parent.R'].parent=Center
        #Groove.parent=Center
        Center.parent=rig.data.edit_bones['root']
        
        bpy.ops.object.mode_set(mode = 'POSE')
        ''' Groove=rig.pose.bones["Groove"]
        Groove.custom_shape = bpy.data.objects["WGT-rig_root"]
        Groove.mmd_bone.name_j='グルーブ'''
        rig.pose.bones["upper_arm_parent.L"]["IK_parent"] = 0
        rig.pose.bones["upper_arm_parent.R"]["IK_parent"] = 0
        rig.pose.bones["torso"]["torso_parent"] = 0
        #Groove.bone.layers=rig.data.bones["torso"].layers
        #Groove.bone_group = rig.pose.bone_groups['Special'] 
        Center=rig.pose.bones["Center"]
        Center.mmd_bone.name_j='センター'
        Center.custom_shape = bpy.data.objects["WGT-rig_root"]
        Center.bone.layers=rig.data.bones["torso"].layers
        Center.bone_group = rig.pose.bone_groups['Special'] 
    else:
        rig.pose.bones['MCH-torso.parent'].mmd_bone.name_j='グルーブ'

    #添加约束
    #add constraint

    constraints_list=[
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
        constraints_list.append(("ORG-eye.L","eye.R",True,False))
        constraints_list.append(("ORG-eye.R","eye.L",True,False))
    else:
        constraints_list.append(("ORG-eye.L","eye.L",True,False))
        constraints_list.append(("ORG-eye.R","eye.R",True,False))

    add_constraint3(constraints_list,preset_dict)

    bpy.ops.object.mode_set(mode = 'POSE')
    
    #修正rigifyIK控制器范围限制
    rig.pose.bones["MCH-shin_ik.L"].use_ik_limit_x = True
    rig.pose.bones["MCH-shin_ik.R"].use_ik_limit_x = True
    rig.pose.bones["MCH-shin_ik.L"].ik_min_x = -0.0174533
    rig.pose.bones["MCH-shin_ik.R"].ik_min_x = -0.0174533

    '''rig.pose.bones["MCH-forearm_ik.L"].use_ik_limit_z = True
    rig.pose.bones["MCH-forearm_ik.R"].use_ik_limit_z = True
    rig.pose.bones["MCH-forearm_ik.L"].ik_max_z = 0
    rig.pose.bones["MCH-forearm_ik.R"].ik_min_z = 0'''

    #极向目标开关
    #pole target
    #rig.pose.bones["MCH-forearm_ik.L"].constraints["IK.001"].pole_angle = 3.14159
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

    #写入MMR骨骼预设
    rigify_preset=preset.preset_dict_dict['retarget']['Rigify']
    preset.set_bone_type(rig.pose,rigify_preset)
    
    bpy.ops.object.mode_set(mode = 'OBJECT')
    bpy.ops.object.select_all(action='DESELECT')

    #隐藏原骨架，把新骨架设为永远在前
    #hide old armature
    rig.show_in_front = True
    mmd_arm.hide = True
    rig.name=mmd_arm.name+'_Rig'

    #缩小root控制器
    #reduce size
    '''if bpy.app.version[0]>=3:
        rig.pose.bones["root"].custom_shape_scale = 0.4
    else:
        rig.pose.bones["root"].custom_shape_scale_xyz=(0.4,0.4,0.4)'''


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
    if 'eye.L' not in preset_dict or 'eye.R' not in preset_dict:
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
        'upper_arm_parent.L','upper_arm_parent.R','thigh_parent.L','thigh_parent.R','master_eye.L','master_eye.R',
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



    #将轴心设为各自中点以方便操作
    #set transform pivot point to individual
    bpy.context.view_layer.objects.active=rig
    rig.select_set(True)
    bpy.context.scene.tool_settings.transform_pivot_point = 'INDIVIDUAL_ORIGINS'
    bpy.context.area.type = area
    logging.info("完成"+'匹配骨骼数:'+str(match_bone_nunber))
    alert_error("提示","完成"+'匹配骨骼数:'+str(match_bone_nunber))
    return(True)

Class_list=[]