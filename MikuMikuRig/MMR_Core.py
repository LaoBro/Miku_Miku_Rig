import bpy
import os
import logging
import math
import bmesh
import copy
def alert_error(title,message):
    def draw(self,context):
        self.layout.label(text=str(message))
    bpy.context.window_manager.popup_menu(draw,title=title,icon='ERROR')
class MMR():

    context=None
    mmr_property=None

    zero_roll_list=["Head","Neck_Middle","Neck","LowerBody","UpperBody","UpperBody2","spine.001","UpperBody3","Leg_L","Leg_R","Knee_L","Knee_R","Ankle_L","Ankle_R","toe.L","toe.R"]

    def __init__(self,context):
        #获得场景变量
        #get scene variable
        self.context=context
        scene=context.scene
        self.mmr_property=scene.mmr_property


    def quad(self,rad):
        degree=rad*180/math.pi
        degree= degree % 360
        if degree <= 90:
            Quadrant = 1
        else:
            if degree <= 180:
                Quadrant = 2
            else:
                if degree <= 270:
                    Quadrant = 3
                else:
                    if degree <= 360:
                        Quadrant = 4

        return Quadrant

    def check_arm(self):
        global mmd_arm
        global mmd_bones_list

        mmd_arm=bpy.context.object
        have_rigify=False
        for addon in bpy.context.preferences.addons:
            if addon.module=="rigify":
                have_rigify=True
        if mmd_arm==None:
            logging.info("未选择骨骼！")
            alert_error("提示","未选择骨骼！")
            return(False)
        if have_rigify==False:
            logging.info("检测到未开启rigify，已自动开启")
            alert_error("提示","检测到未开启rigify，已自动开启")
            bpy.ops.preferences.addon_enable(module="rigify")
        if "_arm" not in mmd_arm.name:
            logging.info("所选对象不是MMD骨骼！")
            alert_error("提示","所选对象不是MMD骨骼！")
            return(False)
        elif mmd_arm.parent==None:
            logging.info("所选对象不是MMD骨骼！")
            alert_error("提示","所选对象不是MMD骨骼！")
            return(False) 
        elif mmd_arm.name.replace("_arm","") != mmd_arm.parent.name:
            logging.info("所选对象不是MMD骨骼！")
            alert_error("提示","所选对象不是MMD骨骼！")
            return(False) 
        bpy.ops.mmd_tools.translate_mmd_model(dictionary='INTERNAL', types={'BONE'}, modes={'MMD', 'BLENDER'})
        mmd_bones_list=mmd_arm.data.bones.keys()
        if "UpperBodyB" in mmd_bones_list:
            mmd_arm.data.bones["UpperBodyB"].name="UpperBody2"
            mmd_bones_list=mmd_arm.data.bones.keys()
        return (True)

    #Outdated methods
    def fix_axial_simple(self):

        global mmd_arm
        global mmd_bones_list
        fix_bone_list=[
            "Thumb0_L","Thumb1_L","Thumb2_L","Thumb0_R","Thumb1_R","Thumb2_R","IndexFinger1_L","IndexFinger1_R","IndexFinger2_L","IndexFinger2_R","IndexFinger3_L","IndexFinger3_R",
            "MiddleFinger1_L","MiddleFinger1_R","MiddleFinger2_L","MiddleFinger2_R","MiddleFinger3_L","MiddleFinger3_R","RingFinger1_L","RingFinger1_R","RingFinger2_L","RingFinger2_R","RingFinger3_L","RingFinger3_R",
            "LittleFinger1_L","LittleFinger1_R","LittleFinger2_L","LittleFinger2_R","LittleFinger3_L","LittleFinger3_R","Shoulder_L","Shoulder_R","Arm_L","Arm_R","Elbow_L","Elbow_R","Wrist_L","Wrist_R"
        ]
        p_operate_bones=[
            "IndexFinger1_L","IndexFinger2_L","IndexFinger3_L",
            "MiddleFinger1_L","MiddleFinger2_L","MiddleFinger3_L","RingFinger1_L","RingFinger2_L","RingFinger3_L",
            "LittleFinger1_L","LittleFinger2_L","LittleFinger3_L","LittleFinger3_R"]
        n_operate_bones=[
            "IndexFinger1_R","IndexFinger2_R","IndexFinger3_R",
            "MiddleFinger1_R","MiddleFinger2_R","MiddleFinger3_R","RingFinger1_R","RingFinger2_R","RingFinger3_R",
            "LittleFinger1_R","LittleFinger2_R","LittleFinger3_R"]
        bpy.ops.armature.select_all(action='DESELECT')
        for name in fix_bone_list:
            if name in mmd_bones_list:
                mmd_arm.data.edit_bones[name].select=True
        bpy.ops.armature.calculate_roll(type='GLOBAL_NEG_Y')
        for name in p_operate_bones:
            if name in mmd_bones_list:
                mmd_arm.data.edit_bones[name].roll+=math.pi/2
        for name in n_operate_bones:
            if name in mmd_bones_list:
                mmd_arm.data.edit_bones[name].roll-=math.pi/2
                
        alert_error("提示","轴向修正完成")

    #Outdated methods
    def fix_axial(self):
        global mmd_arm
        L_first_quadrant_list=[
            "IndexFinger1_L","IndexFinger2_L","IndexFinger3_L",
            "MiddleFinger1_L","MiddleFinger2_L","MiddleFinger3_L","RingFinger1_L","RingFinger2_L","RingFinger3_L",
            "LittleFinger1_L","LittleFinger2_L","LittleFinger3_L","Shoulder_L","Arm_L","Elbow_L"
            ]
        L_second_quadrant_bones_list=["Thumb0_L","Thumb1_L","Thumb2_L","Wrist_L"]
        R_first_quadrant_bones_list=[
            "IndexFinger1_R","IndexFinger2_R","IndexFinger3_R",
            "MiddleFinger1_R","MiddleFinger2_R","MiddleFinger3_R","RingFinger1_R","RingFinger2_R","RingFinger3_R",
            "LittleFinger1_R","LittleFinger2_R","LittleFinger3_R","Shoulder_R","Arm_R","Elbow_R"
            ]
        R_second_quadrant_bones_list=["Thumb0_R","Thumb1_R","Thumb2_R","Wrist_R"]

        for name in self.zero_roll_list:
            if name in mmd_bones_list:
                bone=mmd_arm.data.edit_bones[name]
                bone.roll=0

        for name in L_first_quadrant_list:
            if name in mmd_bones_list:
                bone=mmd_arm.data.edit_bones[name]
                roll=bone.roll
                old_quadrant=self.quad(roll)
                if old_quadrant==4:
                    roll+=math.pi/2
                elif old_quadrant==3:
                    roll+=math.pi
                elif old_quadrant==2:
                    roll-=math.pi/2
                bone.roll=roll
        for name in L_second_quadrant_bones_list:
            if name in mmd_bones_list:
                bone=mmd_arm.data.edit_bones[name]
                roll=bone.roll
                old_quadrant=self.quad(roll)
                if old_quadrant==4:
                    roll+=math.pi
                elif old_quadrant==3:
                    roll-=math.pi/2
                elif old_quadrant==1:
                    roll+=math.pi/2
                bone.roll=roll
        for name in R_first_quadrant_bones_list:
            if name in mmd_bones_list:
                bone=mmd_arm.data.edit_bones[name]
                roll=bone.roll
                old_quadrant=self.quad(roll)
                if old_quadrant==3:
                    roll+=math.pi/2
                elif old_quadrant==2:
                    roll+=math.pi
                elif old_quadrant==1:
                    roll-=math.pi/2
                bone.roll=roll
        for name in R_second_quadrant_bones_list:
            if name in mmd_bones_list:
                bone=mmd_arm.data.edit_bones[name]
                roll=bone.roll
                old_quadrant=self.quad(roll)
                if old_quadrant==1:
                    roll+=math.pi
                elif old_quadrant==4:
                    roll-=math.pi/2
                elif old_quadrant==2:
                    roll+=math.pi/2
                bone.roll=roll

        for name in L_first_quadrant_list+L_second_quadrant_bones_list:
            if name in mmd_bones_list:
                R_name=name.replace("_L","_R")
                if R_name in mmd_bones_list:
                    mmd_arm.data.edit_bones[R_name].roll=-mmd_arm.data.edit_bones[name].roll
        alert_error("提示","轴向修正完成")

    #load Stance Pose
    def load_pose(self):
        my_dir = os.path.dirname(os.path.realpath(__file__))
        vpd_file = os.path.join(my_dir, "MMR_Rig_pose.vpd")
        print(my_dir)
        print(vpd_file)
        bpy.ops.mmd_tools.import_vpd(filepath=vpd_file, files=[{"name":"MMR_Rig_pose.vpd", "name":"MMR_Rig_pose.vpd"}], directory=my_dir)

    def add_constraint_execute(self):

        length=len(constraints_from)
        bpy.ops.object.mode_set(mode = 'EDIT')
        for i in range(length):
            From = constraints_from[i]
            To = constraints_to[i]
            parent_name=From + '_parent'
            parent_bone=rig.data.edit_bones.new(name=parent_name)
            parent_bone.head=mmd_arm2.data.edit_bones[From].head
            parent_bone.tail=mmd_arm2.data.edit_bones[From].tail
            parent_bone.roll=mmd_arm2.data.edit_bones[From].roll
            parent_bone.parent=rig.data.edit_bones[To]

        bpy.ops.object.mode_set(mode = 'POSE')
        for i in range(length):
            From = constraints_from[i]
            To = constraints_to[i]
            con= mmd_arm.pose.bones[From].constraints
            for c in con:
                c.mute=True
            parent_name=From + '_parent'
            rig.data.bones[parent_name].hide=True
            COPY_TRANSFORMS=con.new(type='COPY_TRANSFORMS')
            COPY_TRANSFORMS.target = rig
            COPY_TRANSFORMS.subtarget = parent_name
            COPY_TRANSFORMS.name="rel_transforms"
            COPY_TRANSFORMS.mix_mode = 'REPLACE'
            COPY_TRANSFORMS.owner_space = 'WORLD'
            COPY_TRANSFORMS.target_space = 'WORLD'



    def add_constraint(self,To,From,rotation=True):

        if From in mmd_bones_list:
            if rotation:
                constraints_from.append(From)
                constraints_to.append(To)
            else:
                COPY_LOCATION=mmd_arm.pose.bones[From].constraints.new(type='COPY_LOCATION')
                COPY_LOCATION.target = rig
                COPY_LOCATION.subtarget = To
                COPY_LOCATION.name="rel_location"

    def RIG(self):


        global mmd_arm
        global mmd_arm2
        global mmd_bones_list
        global rig
        global constraints_from
        global constraints_to

        my_dir = os.path.dirname(os.path.realpath(__file__))
        rigify_blend_file = os.path.join(my_dir, "MMR_Rig.blend")

        if self.check_arm()==False:
            return{False}



        self.load_pose()

        bpy.ops.object.mode_set(mode = 'OBJECT')
        mmd_arm2=mmd_arm.copy()
        self.context.collection.objects.link(mmd_arm2)
        mmd_arm2.data=mmd_arm.data.copy()
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active=mmd_arm2
        bpy.ops.object.mode_set(mode = 'POSE')
        bpy.ops.pose.armature_apply(selected=False)
        bpy.ops.object.mode_set(mode = 'OBJECT')

        rigify_arm_name="MMR_Rig_relative"

        #导入metarig骨骼
        #import metarig armature
        rigify_arm=None
        with bpy.data.libraries.load(rigify_blend_file) as (data_from, data_to):
            data_to.objects = [name for name in data_from.objects if rigify_arm_name == name]
        for obj in data_to.objects:
            self.context.collection.objects.link(obj)
            rigify_arm=obj

        rigify_bones_list=rigify_arm.data.bones.keys()
        exist_bones=list(set(mmd_bones_list).intersection(rigify_bones_list))

        #隐藏多余骨骼
        #hide useless bone
        for bone in mmd_arm.data.bones:
            if bone.name not in rigify_bones_list:
                bone.hide=True
            

        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active=rigify_arm
        bpy.ops.object.mode_set(mode = 'EDIT')
        bpy.ops.armature.select_all(action='DESELECT')

        #修正只有两节拇指骨骼的模型
        if "Thumb1_L" in exist_bones:
            if mmd_arm.data.bones["Thumb1_L"].parent.name !="Thumb0_L":
                rigify_arm.data.edit_bones["Thumb2_L"].select=True
                bpy.ops.armature.delete()
                rigify_arm.data.edit_bones["Thumb1_L"].name='Thumb2_L'
                rigify_arm.data.edit_bones["Thumb0_L"].name='Thumb1_L'

        if "Thumb1_R" in exist_bones:
            if mmd_arm.data.bones["Thumb1_R"].parent.name !="Thumb0_R":
                rigify_arm.data.edit_bones["Thumb2_R"].select=True
                bpy.ops.armature.delete()
                rigify_arm.data.edit_bones["Thumb1_R"].name='Thumb2_R'
                rigify_arm.data.edit_bones["Thumb0_R"].name='Thumb1_R'

        rigify_bones_list=rigify_arm.data.edit_bones.keys()

        #调整约束以匹配骨骼
        bpy.ops.object.mode_set(mode = 'POSE')
        for name in rigify_bones_list:
            bone=rigify_arm.pose.bones[name]
            parent_bone=None
            parent_bone=bone.parent
            if parent_bone!=None:
                parent_bone.constraints['location'].target=mmd_arm2
                parent_bone.constraints['location'].subtarget=bone.parent.name
                parent_bone.constraints['stretch'].target=mmd_arm2
                parent_bone.constraints['stretch'].subtarget=name
                parent_bone.constraints["stretch"].rest_length = parent_bone.length
            if name not in exist_bones:
                bone.constraints['location'].mute=True
                bone.constraints['stretch'].mute=True

        '''vector_list=[]
        scale_list=[]
        for bone in rigify_arm.data.edit_bones:
            vector=[bone.tail[0]-bone.head[0],bone.tail[1]-bone.head[1],bone.tail[2]-bone.head[2]]
            scale=1
            if bone.parent!=None:
                scale=bone.length/bone.parent.length
            vector_list.append(vector)
            scale_list.append(scale)

        for i in range(len(rigify_arm.data.edit_bones)):
            bone=rigify_arm.data.edit_bones[i]
            name=bone.name
            parent_bone=bone.parent
            mmd_bone=mmd_arm2.pose.bone[name]
            if name in exist_bones:
                bone.head=mmd_bone.head
                if len(bone.children)==0:
                    vector=vector_list[i]
                    bone.tail=[bone.head[0]+vector[0],bone.head[1]+vector[1],bone.head[2]+vector[2]]
                    if parent_bone!=None:
                        bone.length=parent_bone.length*scale_list[i]'''



        #spine.001，Neck_Middle是多余骨骼
        rigify_arm.pose.bones['spine.001'].constraints["location"].mute=True
        rigify_arm.pose.bones['spine.001'].constraints["stretch"].mute=True


        rigify_arm.pose.bones['Neck_Middle'].constraints["location"].mute=True
        rigify_arm.pose.bones['Neck_Middle'].constraints["stretch"].mute=True

        rigify_arm.pose.bones['Neck'].constraints['stretch'].subtarget='Head'

        rigify_arm.pose.bones['LowerBody'].constraints["stretch"].subtarget='UpperBody'
        rigify_arm.pose.bones["LowerBody"].constraints["location"].head_tail = 1

        rigify_arm.pose.bones['UpperBody2'].constraints["stretch"].subtarget='UpperBody2'
        rigify_arm.pose.bones["UpperBody2"].constraints["stretch"].head_tail = 1

        rigify_arm.pose.bones['Ankle_L'].constraints["stretch"].subtarget='ToeTipIK_L'

        rigify_arm.pose.bones['Ankle_R'].constraints["stretch"].subtarget='ToeTipIK_R'
        
        rigify_arm.pose.bones['Head'].constraints['location'].target=mmd_arm
        rigify_arm.pose.bones['Head'].constraints['location'].subtarget='Head'
        scale=mmd_arm.data.bones['Head'].length/rigify_arm.data.bones['Head'].length
        rigify_arm.pose.bones['Head'].scale=[scale,scale,scale]
        rigify_arm.pose.bones['Head'].constraints['stretch'].target=mmd_arm
        rigify_arm.pose.bones['Head'].constraints['stretch'].subtarget='Head'
        rigify_arm.pose.bones['Head'].constraints["stretch"].head_tail = 1
        #rigify_arm.pose.bones['Head'].constraints["stretch"].rest_length = rigify_arm.data.bones['Head'].length

        rigify_arm.pose.bones['Wrist_L'].constraints["stretch"].mute=True
        rigify_arm.pose.bones['Wrist_R'].constraints["stretch"].mute=True

        rigify_arm.pose.bones['ToeTipIK_L'].constraints["stretch"].mute=True
        rigify_arm.pose.bones['ToeTipIK_R'].constraints["stretch"].mute=True

        #调整缺失UpperBody2情况
        if 'UpperBody2' not in exist_bones and 'UpperBody' in exist_bones:
            rigify_arm.pose.bones['UpperBody'].scale[0] = 0.0001
            rigify_arm.pose.bones['UpperBody'].scale[1] = 0.0001
            rigify_arm.pose.bones['UpperBody'].scale[2] = 0.0001
            rigify_arm.pose.bones['UpperBody'].constraints['location'].mute=True
            rigify_arm.pose.bones['UpperBody'].constraints['stretch'].mute=True
            rigify_arm.pose.bones['UpperBody2'].constraints['location'].subtarget='UpperBody'
            rigify_arm.pose.bones['UpperBody2'].constraints['stretch'].subtarget='UpperBody'
            rigify_arm.pose.bones['UpperBody2'].constraints['location'].mute=False
            rigify_arm.pose.bones['UpperBody2'].constraints['stretch'].mute=False

        #匹配眼睛骨骼
        rigify_arm.pose.bones['eye.L'].constraints['location'].mute=False
        rigify_arm.pose.bones['eye.L'].constraints['stretch'].mute=False
        rigify_arm.pose.bones['eye.L'].constraints['location'].target=mmd_arm
        rigify_arm.pose.bones['eye.L'].constraints['location'].subtarget='Eye_L'
        rigify_arm.pose.bones['eye.L'].constraints['location'].head_tail = 1
        #rigify_arm.pose.bones['eye.L'].constraints['stretch'].target=mmd_arm
        #rigify_arm.pose.bones['eye.L'].constraints['stretch'].subtarget='Eye_L'
        #rigify_arm.pose.bones['eye.L'].constraints["stretch"].head_tail = 1

        rigify_arm.pose.bones['eye.R'].constraints['location'].mute=False
        rigify_arm.pose.bones['eye.R'].constraints['stretch'].mute=False
        rigify_arm.pose.bones['eye.R'].constraints['location'].target=mmd_arm
        rigify_arm.pose.bones['eye.R'].constraints['location'].subtarget='Eye_R'
        rigify_arm.pose.bones['eye.R'].constraints['location'].head_tail = 1
        #rigify_arm.pose.bones['eye.R'].constraints['stretch'].target=mmd_arm
        #rigify_arm.pose.bones['eye.R'].constraints['stretch'].subtarget='Eye_R'
        #rigify_arm.pose.bones['eye.R'].constraints["stretch"].head_tail = 1

        bpy.ops.pose.armature_apply(selected=False)
        bpy.ops.pose.select_all(action='SELECT')
        bpy.ops.pose.constraints_clear()

        bpy.ops.object.mode_set(mode = 'OBJECT')
        mmd_arm2.select=True
        bpy.ops.object.mode_set(mode = 'EDIT')

        #修正末端骨骼长度
        rigify_arm.data.edit_bones["Thumb2_L"].length=rigify_arm.data.edit_bones["Thumb1_L"].length
        rigify_arm.data.edit_bones["Thumb2_R"].length=rigify_arm.data.edit_bones["Thumb1_R"].length
        rigify_arm.data.edit_bones["IndexFinger3_L"].length=rigify_arm.data.edit_bones["IndexFinger2_L"].length
        rigify_arm.data.edit_bones["IndexFinger3_R"].length=rigify_arm.data.edit_bones["IndexFinger2_R"].length
        rigify_arm.data.edit_bones["MiddleFinger3_L"].length=rigify_arm.data.edit_bones["MiddleFinger2_L"].length
        rigify_arm.data.edit_bones["MiddleFinger3_R"].length=rigify_arm.data.edit_bones["MiddleFinger2_R"].length
        rigify_arm.data.edit_bones["RingFinger3_L"].length=rigify_arm.data.edit_bones["RingFinger2_L"].length
        rigify_arm.data.edit_bones["RingFinger3_R"].length=rigify_arm.data.edit_bones["RingFinger2_R"].length
        rigify_arm.data.edit_bones["LittleFinger3_L"].length=rigify_arm.data.edit_bones["LittleFinger2_L"].length
        rigify_arm.data.edit_bones["LittleFinger3_R"].length=rigify_arm.data.edit_bones["LittleFinger2_R"].length
        rigify_arm.data.edit_bones["ToeTipIK_L"].length=rigify_arm.data.edit_bones["Ankle_L"].length/2
        rigify_arm.data.edit_bones["ToeTipIK_R"].length=rigify_arm.data.edit_bones["Ankle_R"].length/2
        rigify_arm.data.edit_bones["Wrist_L"].length=rigify_arm.data.edit_bones["Elbow_L"].length/4
        rigify_arm.data.edit_bones["Wrist_R"].length=rigify_arm.data.edit_bones["Elbow_R"].length/4





        #生成控制器
        bpy.ops.object.mode_set(mode = 'OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active=rigify_arm
        bpy.ops.pose.rigify_generate()
        rig=bpy.data.objects["rig"]
        rig_bones_list=rig.data.bones.keys()

        #开始调整生成的控制器
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active=rig
        rig.select=True

        bpy.ops.object.mode_set(mode = 'OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active=mmd_arm
        rig.select=True
        mmd_arm2.select=True
        bpy.ops.object.mode_set(mode = 'POSE')

        #添加约束
        #add constraint

        constraints_from=[]
        constraints_to=[]

        self.add_constraint("ORG-Arm_L","Arm_L",True)
        self.add_constraint("ORG-Arm_R","Arm_R",True)
        self.add_constraint("ORG-Elbow_L","Elbow_L",True)
        self.add_constraint("ORG-Elbow_R","Elbow_R",True)
        self.add_constraint("ORG-Shoulder_L","Shoulder_L",True)
        self.add_constraint("ORG-Shoulder_R","Shoulder_R",True)
        self.add_constraint("ORG-Wrist_L","Wrist_L",True)
        self.add_constraint("ORG-Wrist_R","Wrist_R",True)

        
        self.add_constraint("ORG-Leg_L","Leg_L",True)
        self.add_constraint("ORG-Leg_R","Leg_R",True)
        self.add_constraint("ORG-Knee_L","Knee_L",True)
        self.add_constraint("ORG-Knee_R","Knee_R",True)

        self.add_constraint("DEF-Ankle_L","Ankle_L",True)
        self.add_constraint("DEF-Ankle_R","Ankle_R",True)
        self.add_constraint("DEF-Ankle_L","LegIK_L",False)
        self.add_constraint("DEF-Ankle_R","LegIK_R",False)
        self.add_constraint("DEF-ToeTipIK_L","ToeTipIK_L",False)
        self.add_constraint("DEF-ToeTipIK_R","ToeTipIK_R",False)

        #修正缺少UpperBody2的骨骼
        #fix the armature that lack upperbody2
        if 'UpperBody2' not in exist_bones and 'UpperBody' in exist_bones:
            self.add_constraint("UpperBody2_fk","UpperBody",True)
        else:
            self.add_constraint("UpperBody2_fk","UpperBody2",True)
            self.add_constraint("UpperBody_fk","UpperBody",True)
        self.add_constraint("LowerBody_fk","LowerBody",True)
        self.add_constraint("torso","Center",True)
        self.add_constraint("DEF-Neck","Neck",True)
        self.add_constraint("DEF-Head","Head",True)
        self.add_constraint("root","ParentNode",True)

        #self.add_constraint("ORG-eye.L","Eye_L",True)
        #self.add_constraint("ORG-eye.R","Eye_R",True)


        self.add_constraint("ORG-Thumb0_L","Thumb0_L",True)
        self.add_constraint("ORG-Thumb0_R","Thumb0_R",True)
        self.add_constraint("ORG-Thumb1_L","Thumb1_L",True)
        self.add_constraint("ORG-Thumb1_R","Thumb1_R",True)
        self.add_constraint("ORG-Thumb2_L","Thumb2_L",True)
        self.add_constraint("ORG-Thumb2_R","Thumb2_R",True)

        self.add_constraint("ORG-IndexFinger1_L","IndexFinger1_L",True)
        self.add_constraint("ORG-IndexFinger1_R","IndexFinger1_R",True)
        self.add_constraint("ORG-IndexFinger2_L","IndexFinger2_L",True)
        self.add_constraint("ORG-IndexFinger2_R","IndexFinger2_R",True)
        self.add_constraint("ORG-IndexFinger3_L","IndexFinger3_L",True)
        self.add_constraint("ORG-IndexFinger3_R","IndexFinger3_R",True)
        self.add_constraint("ORG-MiddleFinger1_L","MiddleFinger1_L",True)
        self.add_constraint("ORG-MiddleFinger1_R","MiddleFinger1_R",True)
        self.add_constraint("ORG-MiddleFinger2_L","MiddleFinger2_L",True)
        self.add_constraint("ORG-MiddleFinger2_R","MiddleFinger2_R",True)
        self.add_constraint("ORG-MiddleFinger3_L","MiddleFinger3_L",True)
        self.add_constraint("ORG-MiddleFinger3_R","MiddleFinger3_R",True)
        self.add_constraint("ORG-RingFinger1_L","RingFinger1_L",True)
        self.add_constraint("ORG-RingFinger1_R","RingFinger1_R",True)
        self.add_constraint("ORG-RingFinger2_L","RingFinger2_L",True)
        self.add_constraint("ORG-RingFinger2_R","RingFinger2_R",True)
        self.add_constraint("ORG-RingFinger3_L","RingFinger3_L",True)
        self.add_constraint("ORG-RingFinger3_R","RingFinger3_R",True)
        self.add_constraint("ORG-LittleFinger1_L","LittleFinger1_L",True)
        self.add_constraint("ORG-LittleFinger1_R","LittleFinger1_R",True)
        self.add_constraint("ORG-LittleFinger2_L","LittleFinger2_L",True)
        self.add_constraint("ORG-LittleFinger2_R","LittleFinger2_R",True)
        self.add_constraint("ORG-LittleFinger3_L","LittleFinger3_L",True)
        self.add_constraint("ORG-LittleFinger3_R","LittleFinger3_R",True)

        self.add_constraint_execute()

        #眼睛约束
        bpy.ops.object.mode_set(mode = 'EDIT')
        eyes_parent_L=rig.data.edit_bones.new(name='eyes_parent_L')
        eyes_parent_L.head=mmd_arm2.data.edit_bones['Eye_L'].head
        eyes_parent_L.tail=mmd_arm2.data.edit_bones['Eye_L'].tail
        eyes_parent_L.roll=mmd_arm2.data.edit_bones['Eye_L'].roll
        eyes_parent_L.parent=rig.data.edit_bones['ORG-eye.L']

        eyes_parent_R=rig.data.edit_bones.new(name='eyes_parent_R')
        eyes_parent_R.head=mmd_arm2.data.edit_bones['Eye_R'].head
        eyes_parent_R.tail=mmd_arm2.data.edit_bones['Eye_R'].tail
        eyes_parent_R.roll=mmd_arm2.data.edit_bones['Eye_R'].roll
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
        COPY_ROTATION.name="rel_rotation"

        #手腕旋转跟随上半身开关
        if self.mmr_property.wrist_rotation_follow:
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
        if self.mmr_property.auto_shoulder:
            bpy.ops.object.mode_set(mode = 'EDIT')
            rig.pose.bones["Shoulder_L"].ik_stiffness_x = 0.5
            rig.pose.bones["Shoulder_L"].ik_stiffness_y = 0.5
            rig.pose.bones["Shoulder_L"].ik_stiffness_z = 0.5
            rig.data.edit_bones["Arm_ik_L"].parent=rig.data.edit_bones["Shoulder_L"]
            rig.pose.bones["MCH-Elbow_ik_L"].constraints["IK.001"].chain_count = 3
            rig.pose.bones["MCH-Elbow_ik_L"].constraints["IK"].chain_count = 3
            rig.pose.bones["Shoulder_R"].ik_stiffness_x = 0.5
            rig.pose.bones["Shoulder_R"].ik_stiffness_y = 0.5
            rig.pose.bones["Shoulder_R"].ik_stiffness_z = 0.5
            rig.data.edit_bones["Arm_ik_R"].parent=rig.data.edit_bones["Shoulder_R"]
            rig.pose.bones["MCH-Elbow_ik_R"].constraints["IK.001"].chain_count = 3
            rig.pose.bones["MCH-Elbow_ik_R"].constraints["IK"].chain_count = 3


        bpy.ops.object.mode_set(mode = 'POSE')

        #手腕跟随上半身开关
        if self.mmr_property.wrist_follow:
            rig.pose.bones["Arm_parent_L"]["IK_parent"] = 4
            rig.pose.bones["Arm_parent_R"]["IK_parent"] = 4
       
        #肩膀联动复制缩放
        #shoulder scale
        '''if self.mmr_property.auto_shoulder:
            COPY_SCALE=rig.pose.bones["Shoulder_L"].constraints.new(type='COPY_SCALE')
            COPY_SCALE.target = rig
            COPY_SCALE.subtarget = "root"
            COPY_SCALE.name="shoulder_scale"
            COPY_SCALE.use_make_uniform = True

            COPY_SCALE=rig.pose.bones["Shoulder_R"].constraints.new(type='COPY_SCALE')
            COPY_SCALE.target = rig
            COPY_SCALE.subtarget = "root"
            COPY_SCALE.name="shoulder_scale"
            COPY_SCALE.use_make_uniform = True'''

       
        #修正rigifyIK控制器范围限制
        rig.pose.bones["MCH-Knee_ik_L"].use_ik_limit_x = True
        rig.pose.bones["MCH-Knee_ik_R"].use_ik_limit_x = True
        rig.pose.bones["MCH-Knee_ik_L"].ik_min_x = -0.0174533
        rig.pose.bones["MCH-Knee_ik_R"].ik_min_x = -0.0174533

        #极向目标开关
        #pole target
        rig.pose.bones["MCH-Elbow_ik_L"].constraints["IK.001"].pole_angle = 3.14159
        if self.mmr_property.pole_target:
            rig.pose.bones["Leg_parent_L"]["pole_vector"] = 1
            rig.pose.bones["Leg_parent_R"]["pole_vector"] = 1
            rig.pose.bones["Arm_parent_L"]["pole_vector"] = 1
            rig.pose.bones["Arm_parent_R"]["pole_vector"] = 1


        #捩骨约束
        #Twist constrains
        if 'HandTwist_L' in mmd_bones_list:
            c1=mmd_arm.pose.bones['HandTwist_L'].constraints.new(type='COPY_ROTATION')
            c1.target=rig
            c1.subtarget='ORG-Wrist_L'
            c1.mix_mode = 'BEFORE'
            c1.target_space = 'LOCAL'
            c1.owner_space = 'LOCAL'
            c2=mmd_arm.pose.bones['HandTwist_L'].constraints.new(type='DAMPED_TRACK')
            c2.target=rig
            c2.subtarget='ORG-Wrist_L'
            mmd_arm.data.bones['HandTwist_L'].hide=False
        else:
            mmd_arm.data.bones["Wrist_L"].bbone_segments = 2
            mmd_arm.data.bones["Elbow_L"].bbone_segments = 2
            mmd_arm.pose.bones["Wrist_L"].bbone_easein = -1
            mmd_arm.pose.bones["Elbow_L"].bbone_easein = -1
            mmd_arm.pose.bones["Elbow_L"].bbone_easeout = -1

        if 'HandTwist_R' in mmd_bones_list:
            c1=mmd_arm.pose.bones['HandTwist_R'].constraints.new(type='COPY_ROTATION')
            c1.target=rig
            c1.subtarget='ORG-Wrist_R'
            c1.mix_mode = 'BEFORE'
            c1.target_space = 'LOCAL'
            c1.owner_space = 'LOCAL'
            c2=mmd_arm.pose.bones['HandTwist_R'].constraints.new(type='DAMPED_TRACK')
            c2.target=rig
            c2.subtarget='ORG-Wrist_R'
            mmd_arm.data.bones['HandTwist_R'].hide=False
        else:
            mmd_arm.data.bones["Wrist_R"].bbone_segments = 2
            mmd_arm.data.bones["Elbow_R"].bbone_segments = 2
            mmd_arm.pose.bones["Wrist_R"].bbone_easein = -1
            mmd_arm.pose.bones["Elbow_R"].bbone_easein = -1
            mmd_arm.pose.bones["Elbow_R"].bbone_easeout = -1

        if 'ArmTwist_L' in mmd_bones_list:
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
        
        #眼睛控制器
        #eyes controller
        '''if 'Eyes' in mmd_bones_list and 'Eye_L'in mmd_bones_list and 'Eye_R' in mmd_bones_list:
            bpy.ops.object.mode_set(mode = 'EDIT')
            head_L=mmd_arm2.data.edit_bones["Eye_L"].head
            head_R=mmd_arm2.data.edit_bones["Eye_R"].head
            center=[(head_L[0]+head_R[0])/2,(head_L[1]+head_R[1])/2,(head_L[2]+head_R[2])/2]
            eye_distance=abs(head_L[0]-head_R[0])

            eyes_parent=rig.data.edit_bones.new(name="eyes_parent")
            eyes_parent.head=eyes_parent.tail=center
            eyes_parent.tail[1]-=eye_distance
            eyes_parent.parent=rig.data.edit_bones['head']

            eyes_parent2=rig.data.edit_bones.new(name="eyes_parent2")
            eyes_parent2.head=mmd_arm2.data.edit_bones["Eyes"].head
            eyes_parent2.tail=mmd_arm2.data.edit_bones["Eyes"].tail
            eyes_parent2.roll=mmd_arm2.data.edit_bones["Eyes"].roll
            eyes_parent2.parent=eyes_parent

            eyes_parent_L=rig.data.edit_bones.new(name="eyes_parent_L")
            eyes_parent_L.head=eyes_parent_L.tail=head_L
            eyes_parent_L.tail[1]-=eye_distance
            eyes_parent_L.parent=rig.data.edit_bones['head']

            eyes_parent2_L=rig.data.edit_bones.new(name="eyes_parent2_L")
            eyes_parent2_L.head=head_L
            eyes_parent2_L.tail=mmd_arm2.data.edit_bones["Eye_L"].tail
            eyes_parent2_L.roll=mmd_arm2.data.edit_bones["Eye_L"].roll
            eyes_parent2_L.parent=eyes_parent_L

            eyes_parent_R=rig.data.edit_bones.new(name="eyes_parent_R")
            eyes_parent_R.head=eyes_parent_R.tail=head_R
            eyes_parent_R.tail[1]-=eye_distance
            eyes_parent_R.parent=rig.data.edit_bones['head']

            eyes_parent2_R=rig.data.edit_bones.new(name="eyes_parent2_R")
            eyes_parent2_R.head=head_R
            eyes_parent2_R.tail=mmd_arm2.data.edit_bones["Eye_R"].tail
            eyes_parent2_R.roll=mmd_arm2.data.edit_bones["Eye_R"].roll
            eyes_parent2_R.parent=eyes_parent_R

            eyes_controller_C=rig.data.edit_bones.new(name="eyes_controller_C")
            eyes_controller_C.head=eyes_controller_C.tail=[center[0],center[1]-eye_distance*2,center[2]]
            eyes_controller_C.tail[2]+=eye_distance
            eyes_controller_C.parent=rig.data.edit_bones['head']

            eyes_controller_L=rig.data.edit_bones.new(name="eyes_controller_L")
            eyes_controller_L.head=eyes_controller_L.tail=[head_L[0],head_L[1]-eye_distance*2,head_L[2]]
            eyes_controller_L.tail[2]+=eye_distance
            eyes_controller_L.parent=eyes_controller_C

            eyes_controller_R=rig.data.edit_bones.new(name="eyes_controller_R")
            eyes_controller_R.head=eyes_controller_R.tail=[head_R[0],head_R[1]-eye_distance*2,head_R[2]]
            eyes_controller_R.tail[2]+=eye_distance
            eyes_controller_R.parent=eyes_controller_C

            bpy.ops.object.mode_set(mode = 'POSE')
            rig.pose.bones['Eyes_Rig'].custom_shape = bpy.data.objects["WGT-rig_Arm_ik_L"]
            rig.pose.bones["Eyes_Rig"].lock_location[0] = True
            rig.pose.bones["Eyes_Rig"].lock_location[1] = True
            rig.pose.bones["Eyes_Rig"].lock_location[2] = True

            c=mmd_arm.pose.bones['Eyes'].constraints.new(type='COPY_ROTATION')
            c.target=rig
            c.subtarget='eyes_parent2'
            c.mix_mode = 'BEFORE'
            c.target_space = 'LOCAL'
            c.owner_space = 'LOCAL'
            mmd_arm.data.bones['Eyes'].hide=False

            c=mmd_arm.pose.bones['Eye_L'].constraints.new(type='COPY_ROTATION')
            c.target=rig
            c.subtarget='eyes_parent2_L'
            c=rig.pose.bones['eyes_parent_L'].constraints.new(type='DAMPED_TRACK')
            c.target=rig
            c.subtarget='eyes_controller_L'
            mmd_arm.data.bones['Eye_L'].hide=False
            rig.data.bones['eyes_parent_L'].hide=True
            rig.data.bones['eyes_parent2_L'].hide=True

            c=mmd_arm.pose.bones['Eye_R'].constraints.new(type='COPY_ROTATION')
            c.target=rig
            c.subtarget='eyes_parent2_R'
            c=rig.pose.bones['eyes_parent_R'].constraints.new(type='DAMPED_TRACK')
            c.target=rig
            c.subtarget='eyes_controller_R'
            mmd_arm.data.bones['Eye_R'].hide=False
            rig.data.bones['eyes_parent_R'].hide=True
            rig.data.bones['eyes_parent2_R'].hide=True'''

        #脚掌IK
        #ToeTipIK
        bpy.ops.object.mode_set(mode = 'EDIT')
        '''if 'LegTipEX_L' in mmd_bones_list:
            LegTipEX_L=rig.data.edit_bones.new(name="LegTipEX_L")
            LegTipEX_L.head=mmd_arm2.data.edit_bones["LegTipEX_L"].head
            LegTipEX_L.tail=mmd_arm2.data.edit_bones["LegTipEX_L"].tail
            LegTipEX_L.roll=mmd_arm2.data.edit_bones["LegTipEX_L"].roll
            #LegTipEX_L.roll=-90
            LegTipEX_L.parent=rig.data.edit_bones['ToeTipIK_L']

        if 'LegTipEX_R' in mmd_bones_list:
            LegTipEX_R=rig.data.edit_bones.new(name="LegTipEX_R")
            LegTipEX_R.head=mmd_arm2.data.edit_bones["LegTipEX_R"].head
            LegTipEX_R.tail=mmd_arm2.data.edit_bones["LegTipEX_R"].tail
            LegTipEX_R.roll=mmd_arm2.data.edit_bones["LegTipEX_R"].roll
            #LegTipEX_R.roll=0
            LegTipEX_R.parent=rig.data.edit_bones['ToeTipIK_R']

        head=rig.data.edit_bones['Ankle_ik_L'].head
        tail=rig.data.edit_bones['Ankle_ik_L'].tail
        roll=rig.data.edit_bones['Ankle_ik_L'].roll
        Foot_IK_cs_L=rig.data.edit_bones.new(name="Foot_IK_cs_L")
        Foot_IK_cs_L.head=head
        Foot_IK_cs_L.tail=tail
        Foot_IK_cs_L.roll=roll
        Foot_IK_cs_L.parent=rig.data.edit_bones['Ankle_ik_L']

        rig.data.edit_bones['Ankle_ik_L'].tail=rig.data.edit_bones["ORG-Ankle_L"].tail

        Foot_IK_Tip_L=rig.data.edit_bones.new(name="Foot_IK_Tip_L")
        Foot_IK_Tip_L.head=Foot_IK_Tip_L.tail=rig.data.edit_bones['Ankle_ik_L'].tail
        Foot_IK_Tip_L.tail[2]+=1
        Foot_IK_Tip_L.length=rig.data.edit_bones['ToeTipIK_L'].length

        Foot_IK_Parent_L=rig.data.edit_bones.new(name="Foot_IK_Parent_L")
        Foot_IK_Parent_L.head=Foot_IK_Parent_L.tail=head
        Foot_IK_Parent_L.tail[2]+=1
        Foot_IK_Parent_L.parent=rig.data.edit_bones['Ankle_ik_L']
        Foot_IK_Parent_L.use_inherit_rotation = False

        Foot_IK_Tip_L.parent=Foot_IK_Parent_L



        head=rig.data.edit_bones['Ankle_ik_R'].head
        tail=rig.data.edit_bones['Ankle_ik_R'].tail
        roll=rig.data.edit_bones['Ankle_ik_R'].roll
        Foot_IK_cs_R=rig.data.edit_bones.new(name="Foot_IK_cs_R")
        Foot_IK_cs_R.head=head
        Foot_IK_cs_R.tail=tail
        Foot_IK_cs_R.roll=roll
        Foot_IK_cs_R.parent=rig.data.edit_bones['Ankle_ik_R']

        rig.data.edit_bones['Ankle_ik_R'].tail=rig.data.edit_bones["ORG-Ankle_R"].tail

        Foot_IK_Tip_R=rig.data.edit_bones.new(name="Foot_IK_Tip_R")
        Foot_IK_Tip_R.head=Foot_IK_Tip_R.tail=rig.data.edit_bones['Ankle_ik_R'].tail
        Foot_IK_Tip_R.tail[2]+=1
        Foot_IK_Tip_R.length=rig.data.edit_bones['ToeTipIK_R'].length

        Foot_IK_Parent_R=rig.data.edit_bones.new(name="Foot_IK_Parent_R")
        Foot_IK_Parent_R.head=Foot_IK_Parent_R.tail=head
        Foot_IK_Parent_R.tail[2]+=1
        Foot_IK_Parent_R.parent=rig.data.edit_bones['Ankle_ik_R']
        Foot_IK_Parent_R.use_inherit_rotation = False

        Foot_IK_Tip_R.parent=Foot_IK_Parent_R

        bpy.ops.object.mode_set(mode = 'POSE')

        if 'LegTipEX_L' in mmd_bones_list:
            mmd_arm.data.bones['LegTipEX_L'].hide=False
            rig.data.bones['LegTipEX_L'].hide=True
            c=mmd_arm.pose.bones['LegTipEX_L'].constraints.new(type='COPY_ROTATION')
            c.target=rig
            c.subtarget='LegTipEX_L'

        if 'LegTipEX_R' in mmd_bones_list:
            mmd_arm.data.bones['LegTipEX_R'].hide=False
            rig.data.bones['LegTipEX_R'].hide=True
            c=mmd_arm.pose.bones['LegTipEX_R'].constraints.new(type='COPY_ROTATION')
            c.target=rig
            c.subtarget='LegTipEX_R'

        c=rig.pose.bones['Ankle_ik_L'].constraints.new(type='IK')
        c.target=rig
        c.subtarget='Foot_IK_Tip_L'
        c.chain_count = 1
        rig.pose.bones["Ankle_ik_L"].custom_shape_transform = rig.pose.bones["Foot_IK_cs_L"]
        rig.data.bones["Foot_IK_cs_L"].hide=True
        rig.pose.bones["Foot_IK_Tip_L"].custom_shape = bpy.data.objects["WGT-rig_ToeTipIK_L"]



        c=rig.pose.bones['Ankle_ik_R'].constraints.new(type='IK')
        c.target=rig
        c.subtarget='Foot_IK_Tip_R'
        c.chain_count = 1
        rig.pose.bones["Ankle_ik_R"].custom_shape_transform = rig.pose.bones["Foot_IK_cs_R"]
        rig.data.bones["Foot_IK_cs_R"].hide=True
        rig.pose.bones["Foot_IK_Tip_R"].custom_shape = bpy.data.objects["WGT-rig_ToeTipIK_R"]'''



        #写入PMX骨骼名称数据
        #write PMX bone name
        rig_bones_list=rig.data.bones.keys()
        PMX_list=['root','全ての親','MCH-torso.parent','グルーブ','torso','センター','hips','下半身','UpperBody_fk','上半身','UpperBody2_fk','上半身2','neck','首','head','頭','Eyes_Rig','両目',
        'Leg_ik_L','左足','Ankle_ik_L','左足ＩＫ','ToeTipIK_L','左つま先ＩＫ','Leg_ik_R','右足','Ankle_ik_R','右足ＩＫ','ToeTipIK_R','右つま先ＩＫ',
        'Shoulder_L','左肩','Arm_fk_L','左腕','Elbow_fk_L','左ひじ','Wrist_fk_L','左手首','Shoulder_R','右肩','Arm_fk_R','右腕','Elbow_fk_R','右ひじ','Wrist_fk_R','右手首',
        'Thumb0_L','左親指０','Thumb1_L','左親指１','Thumb2_L','左親指２',
        'IndexFinger1_L','左人指１','IndexFinger2_L','左人指２','IndexFinger3_L','左人指３',
        'MiddleFinger1_L','左中指１','MiddleFinger2_L','左中指２','MiddleFinger3_L','左中指３',
        'RingFinger1_L','左薬指１','RingFinger2_L','左薬指２','RingFinger3_L','左薬指３',
        'LittleFinger1_L','左小指１','LittleFinger2_L','左小指２','LittleFinger3_L','左小指３',
        'Thumb0_R','右親指０','Thumb1_R','右親指１','Thumb2_R','右親指２',
        'IndexFinger1_R','右人指１','IndexFinger2_R','右人指２','IndexFinger3_R','右人指３',
        'MiddleFinger1_R','右中指１','MiddleFinger2_R','右中指２','MiddleFinger3_R','右中指３',
        'RingFinger1_R','右薬指１','RingFinger2_R','右薬指２','RingFinger3_R','右薬指３',
        'LittleFinger1_R','右小指１','LittleFinger2_R','右小指２','LittleFinger3_R','右小指３']
        for i in range(int(len(PMX_list)/2)):
            if PMX_list[2*i] in rig_bones_list:
                rig.pose.bones[PMX_list[2*i]].mmd_bone.name_j=PMX_list[2*i+1]
        
        bpy.ops.object.mode_set(mode = 'OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        #删除多余骨架
        #delete metarig armatrue
        rigify_arm.select=True
        mmd_arm2.select=True
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
            'ear.L','ear.R','nose_master','teeth.T','teeth.B','tongue_master','jaw_master']
        #锁定缩放的骨骼列表
        #lock the scale of these bone
        lock_scale_bone_list=[
            "root","torso","Ankle_ik_L","Ankle_ik_R","toe.L","toe.R","Wrist_ik_L","Wrist_ik_R","Arm_ik_L","Arm_ik_R","Leg_ik_L","Leg_ik_R",
            "hips","chest","neck","head","Shoulder_L","Shoulder_R"]
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
        if self.mmr_property.solid_rig:
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
        rig.select=True
        bpy.context.scene.tool_settings.transform_pivot_point = 'INDIVIDUAL_ORIGINS'
        logging.info("完成")
        alert_error("提示","完成")
        return(True)

    #设置最小ik迭代
    def set_min_ik_loop(self,min_ik_loop=10):
        if self.check_arm()==False:
            return
        for bone in mmd_arm.pose.bones:
            for c in bone.constraints:
                if c.type=='IK':
                    if c.iterations < min_ik_loop:
                        c.iterations=min_ik_loop
        return(True)
    
    #重定向mixamo动画
    def retarget_mixmao(self,mixamo_path,rigify_arm,lock_location=True,fade_in_out=0,action_scale=1,auto_action_scale=False,ik_fk_hand=3,ik_fk_leg=3):

        if rigify_arm.type!='ARMATURE':
            return(False)
        if mixamo_path==None:
            return(False)

        #获得文件路径
        #get file path
        my_dir = os.path.dirname(os.path.realpath(__file__))
        retarget_blend_file = os.path.join(my_dir, "mixamo_retarget_arm_ik.blend")
        fname,fename=os.path.split(mixamo_path)
        action_name=str(os.path.splitext(fename)[0])

        #导入mixamo FBX文件
        #import mixamo file
        bpy.ops.object.mode_set(mode = 'OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.import_scene.fbx(filepath=mixamo_path,directory =fname)
        for obj in bpy.data.objects:
            if obj.select==True:
                if obj.type=='ARMATURE':
                    mixamo_arm=obj
                else:
                    bpy.data.objects.remove(obj)
        mixamo_action=mixamo_arm.animation_data.action
        #自动动作缩放
        #auto action scale
        if auto_action_scale:
            action_scale_auto=rigify_arm.pose.bones['Leg_ik_L'].head[2]/10.896
            action_scale2=action_scale_auto
        else:
            action_scale2=action_scale
        #导入重定向骨骼文件
        #import armature for retarget
        with bpy.data.libraries.load(retarget_blend_file) as (data_from,data_to):
            data_to.objects = [name for name in data_from.objects]
        for obj in data_to.objects:
                self.context.collection.objects.link(obj)
        mixamo_arm2=bpy.data.objects['mixamo_arm']
        retarget_arm=bpy.data.objects['retarget_arm']
        bpy.ops.object.select_all(action='DESELECT')
        retarget_arm.select=True
        mixamo_arm2.scale[0] *= action_scale2
        mixamo_arm2.scale[1] *= action_scale2
        mixamo_arm2.scale[2] *= action_scale2
        retarget_arm.scale[0] *= action_scale2
        retarget_arm.scale[1] *= action_scale2
        retarget_arm.scale[2] *= action_scale2
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        
        #锁定位置开关
        #lock animation location
        if lock_location:
            mixamo_arm2.pose.bones["mixamorig:Hips2"].constraints["复制位置"].use_x = False
            mixamo_arm2.pose.bones["mixamorig:Hips2"].constraints["复制位置"].use_y = False

        mixamo_arm2.animation_data.action=mixamo_action
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active=retarget_arm
        retarget_arm.select=True
        bpy.ops.object.mode_set(mode = 'POSE')
        bpy.ops.pose.select_all(action='SELECT')
        bpy.ops.nla.bake(frame_start=mixamo_action.frame_range[0], frame_end=mixamo_action.frame_range[1], only_selected=True, visual_keying=True, bake_types={'POSE'})

        #插入IKFK关键帧
        #insert IKFK keyframe
        if ik_fk_hand==2:
            retarget_arm.pose.bones["Arm_parent_L"]["IK_FK"]=0
            retarget_arm.pose.bones["Arm_parent_R"]["IK_FK"]=0
        elif ik_fk_hand==3:
            retarget_arm.pose.bones["Arm_parent_L"]["IK_FK"]=1
            retarget_arm.pose.bones["Arm_parent_R"]["IK_FK"]=1
        if ik_fk_hand !=1:
            retarget_arm.pose.bones["Arm_parent_L"].keyframe_insert(data_path='["IK_FK"]', frame=mixamo_action.frame_range[0])
            retarget_arm.pose.bones["Arm_parent_R"].keyframe_insert(data_path='["IK_FK"]', frame=mixamo_action.frame_range[0])

        if ik_fk_leg==2:
            retarget_arm.pose.bones["Leg_parent_L"]["IK_FK"]=0
            retarget_arm.pose.bones["Leg_parent_R"]["IK_FK"]=0
        elif ik_fk_leg==3:
            retarget_arm.pose.bones["Leg_parent_L"]["IK_FK"]=1
            retarget_arm.pose.bones["Leg_parent_R"]["IK_FK"]=1
        if ik_fk_leg !=1:
            retarget_arm.pose.bones["Leg_parent_L"].keyframe_insert(data_path='["IK_FK"]', frame=mixamo_action.frame_range[0])
            retarget_arm.pose.bones["Leg_parent_R"].keyframe_insert(data_path='["IK_FK"]', frame=mixamo_action.frame_range[0])

        retarget_arm.pose.bones["head"]["neck_follow"]=1
        retarget_arm.pose.bones["head"]["head_follow"]=1
        retarget_arm.pose.bones["head"].keyframe_insert(data_path='["neck_follow"]', frame=mixamo_action.frame_range[0])
        retarget_arm.pose.bones["head"].keyframe_insert(data_path='["head_follow"]', frame=mixamo_action.frame_range[0])
        #插入手腕旋转约束关键帧
        #insert wrist rotation constrain keyframe
        retarget_arm.pose.bones["Wrist_ik_L"].constraints["wrist_rotation"].keyframe_insert(data_path='influence', frame=mixamo_action.frame_range[0])
        retarget_arm.pose.bones["Wrist_ik_R"].constraints["wrist_rotation"].keyframe_insert(data_path='influence', frame=mixamo_action.frame_range[0])
        
        #清空部分位置关键帧
        #clear certain keyframe
        for bone in retarget_arm.pose.bones:
            if bone.bone.hide==False:
                if bone.lock_location[0] == True:
                    bone.location[0]=0
                    bone.location[1]=0
                    bone.location[2]=0
                    for i in range(int(mixamo_action.frame_range[0]),int(mixamo_action.frame_range[1])+1):
                        bone.keyframe_delete(data_path='location',frame=i)


        bpy.ops.object.mode_set(mode = 'OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active=rigify_arm
        rigify_arm.select=True

        retarget_action=retarget_arm.animation_data.action
        retarget_action.name=action_name
        target_track=rigify_arm.animation_data.nla_tracks.new()
        target_track.name='mixamo_track'
        target_strip=target_track.strips.new(action_name,bpy.context.scene.frame_current,retarget_action)
        target_strip.blend_type = 'REPLACE'
        #target_strip.use_auto_blend = True
        target_strip.extrapolation = 'NOTHING'
        target_strip.blend_in = fade_in_out
        target_strip.blend_out = fade_in_out

        #更改原动作混合模式为合并
        rigify_arm.animation_data.action_blend_type = 'COMBINE'

        bpy.ops.object.select_all(action='DESELECT')
        bpy.data.objects.remove(mixamo_arm)
        bpy.data.objects.remove(mixamo_arm2)
        bpy.data.objects.remove(retarget_arm)
        bpy.context.view_layer.objects.active=rigify_arm
        rigify_arm.select=True
        alert_error("提示","导入完成")
        return(True)
        

    def load_vmd(self,vmd_path,rigify_arm,fade_in_out,action_scale=1):
        if rigify_arm.type!='ARMATURE':
            return(False)
        if vmd_path==None:
            return(False)


        fname,fename=os.path.split(vmd_path)
        action_name=str(os.path.splitext(fename)[0])
        bpy.ops.object.mode_set(mode = 'OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        #复制骨骼
        #duplicate armature
        rigify_arm2=rigify_arm.copy()
        self.context.collection.objects.link(rigify_arm2)
        for track in rigify_arm2.animation_data.nla_tracks:
            rigify_arm2.animation_data.nla_tracks.remove(track)
        bpy.context.view_layer.objects.active=rigify_arm2
        rigify_arm2.select=True
        print(vmd_path)
        old_frame_end=bpy.context.scene.frame_end
        bpy.ops.mmd_tools.import_vmd(filepath=vmd_path,scale=action_scale, margin=0)
        bpy.context.scene.frame_end=old_frame_end
        
        vmd_action=rigify_arm2.animation_data.action
        vmd_action.name=action_name

        #插入IKFK关键帧
        #insert IKFK keyframe
        rigify_arm2.pose.bones["Arm_parent_L"]["IK_FK"]=1
        rigify_arm2.pose.bones["Arm_parent_R"]["IK_FK"]=1
        rigify_arm2.pose.bones["Leg_parent_L"]["IK_FK"]=0
        rigify_arm2.pose.bones["Leg_parent_R"]["IK_FK"]=0
        rigify_arm2.pose.bones["head"]["neck_follow"]=1
        rigify_arm2.pose.bones["head"]["head_follow"]=1
        

        rigify_arm2.pose.bones["Arm_parent_L"].keyframe_insert(data_path='["IK_FK"]', frame=vmd_action.frame_range[0])
        rigify_arm2.pose.bones["Arm_parent_R"].keyframe_insert(data_path='["IK_FK"]', frame=vmd_action.frame_range[0])
        rigify_arm2.pose.bones["Leg_parent_L"].keyframe_insert(data_path='["IK_FK"]', frame=vmd_action.frame_range[0])
        rigify_arm2.pose.bones["Leg_parent_R"].keyframe_insert(data_path='["IK_FK"]', frame=vmd_action.frame_range[0])
        rigify_arm2.pose.bones["head"].keyframe_insert(data_path='["neck_follow"]', frame=vmd_action.frame_range[0])
        rigify_arm2.pose.bones["head"].keyframe_insert(data_path='["head_follow"]', frame=vmd_action.frame_range[0])

        #插入脚掌约束关键帧
        #insert leg constrain keyframe
        rigify_arm2.pose.bones["DEF-Ankle_L"].constraints[0].influence=0
        rigify_arm2.pose.bones["DEF-Ankle_R"].constraints[0].influence=0
        rigify_arm2.pose.bones["DEF-Ankle_L"].constraints[0].keyframe_insert(data_path='influence', frame=vmd_action.frame_range[0])
        rigify_arm2.pose.bones["DEF-Ankle_R"].constraints[0].keyframe_insert(data_path='influence', frame=vmd_action.frame_range[0])

        #清空部分位置关键帧
        #clear certain keyframe
        for bone in rigify_arm2.pose.bones:
            if bone.bone.hide==False:
                if bone.lock_location[0] == True:
                    bone.location[0]=0
                    bone.location[1]=0
                    bone.location[2]=0
                    for i in range(int(vmd_action.frame_range[0]),int(vmd_action.frame_range[1])+1):
                        bone.keyframe_delete(data_path='location',frame=i)

        #修复脚掌
        rigify_arm.data.bones["Ankle_L_parent"].inherit_scale = 'NONE'
        rigify_arm.data.bones["Ankle_R_parent"].inherit_scale = 'NONE'
        
        target_track=rigify_arm.animation_data.nla_tracks.new()
        target_track.name='vmd_track'
        target_strip=target_track.strips.new(action_name,bpy.context.scene.frame_current,vmd_action)
        target_strip.blend_type = 'REPLACE'
        target_strip.use_auto_blend = False
        target_strip.extrapolation = 'NOTHING'
        target_strip.blend_in = fade_in_out
        target_strip.blend_out = fade_in_out

        #更改原动作混合模式为合并
        rigify_arm.animation_data.action_blend_type = 'COMBINE'
        bpy.data.objects.remove(rigify_arm2)
        bpy.context.view_layer.objects.active=rigify_arm
        rigify_arm.select=True
        alert_error("提示","导入完成")

        return(True)

    def convert_rigid_body_to_cloth(self,subdivide,cloth_convert_mod):
        select_obj=bpy.context.selected_objects
        mmd_mesh=None
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
                    if obj.mmd_rigid.name!='':
                        select_rigid_body.append(obj)

        if len(select_rigid_body)==0:
                        alert_error("提示","所选物体中没有MMD刚体")
                        return(False)

        if self.mmr_property.auto_select_rigid_body:
            bpy.ops.object.select_all(action='DESELECT')
            bpy.context.view_layer.objects.active=select_rigid_body[0]
            bpy.ops.mmd_tools.rigid_body_select(properties={'collision_group_number'})
            rigid_bodys=bpy.context.selected_objects
        else:
            rigid_bodys=select_rigid_body

        mmd_parent=mmd_mesh=select_rigid_body[0].parent.parent

        if self.mmr_property.auto_select_mesh:
            for obj in mmd_parent.children:
                if obj.type=="ARMATURE":
                    mmd_arm=obj
                    mmd_mesh=mmd_arm.children[0]
            if mmd_mesh == None:
                alert_error("提示","所选刚体没有对应网格模型")
                return(False)
  
        elif len(select_mesh)==0:
            alert_error("提示","所选物体中没有MMD网格模型")
            return(False)
        else:
            mmd_mesh=select_mesh[0]
                
        mmd_arm=mmd_mesh.parent

        rigid_bodys_count=len(rigid_bodys)
        joints=[]
        side_joints=[]
        edge_index=[]
        verts=[]
        edges=[]
        bones_list=[]

        mean_radius=0

        for r in rigid_bodys:
            if r.mmd_rigid.shape == 'BOX':
                radius=min(r.mmd_rigid.size[0],min(r.mmd_rigid.size[1],r.mmd_rigid.size[2]))
            else :
                radius=r.mmd_rigid.size[0]
            mean_radius+=radius

            bone=mmd_arm.pose.bones[r.mmd_rigid.bone]
            verts.append(r.location)
            bones_list.append(bone)

        mean_radius/=rigid_bodys_count

        for obj in bpy.context.view_layer.objects:
            if hasattr(obj,'rigid_body_constraint'):
                if obj.rigid_body_constraint!=None:
                    if obj.rigid_body_constraint.object1 in rigid_bodys and obj.rigid_body_constraint.object2 in rigid_bodys:
                        joints.append(obj)
                        index1=rigid_bodys.index(obj.rigid_body_constraint.object1)
                        index2=rigid_bodys.index(obj.rigid_body_constraint.object2)
                        edge_index.append([index1,index2])
                        edges.append([index1,index2])
                    elif obj.rigid_body_constraint.object1 in rigid_bodys or obj.rigid_body_constraint.object2 in rigid_bodys:
                        side_joints.append(obj)
        

        mesh=bpy.data.meshes.new('mmd_cloth')
        mesh.from_pydata(verts,edges,[])
        mesh.validate()
        cloth_obj=bpy.data.objects.new('mmd_cloth',mesh)
        bpy.context.collection.objects.link(cloth_obj)
        cloth_obj.parent=mmd_parent
        bpy.ops.object.select_all(action='DESELECT')



        bpy.context.view_layer.objects.active=cloth_obj
        bpy.ops.object.mode_set(mode = 'EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.edge_face_add()
        bpy.ops.object.mode_set(mode = 'OBJECT')

        #删除大于四边的面
        #remove ngon
        bm=bmesh.new()
        bm.from_mesh(mesh)
        for f in bm.faces:
            if len(f.verts)>4:
                bm.faces.remove(f)
        #删除多余边
        #remove extra edge
        for e in bm.edges:
            true_edge=False
            for i in edge_index:
                if e.verts[0].index in i and e.verts[1].index in i:
                    true_edge=True
                    break
            if true_edge==False:
                bm.edges.remove(e)
        #尝试标记出头发,飘带
        #try mark hair or ribbon vertex
        bm.to_mesh(mesh)
        bpy.ops.object.mode_set(mode = 'EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.mesh.select_mode(type='EDGE')
        bpy.ops.mesh.select_non_manifold(extend=False, use_wire=True, use_boundary=False, use_multi_face=False, use_non_contiguous=False, use_verts=False)
        bpy.ops.mesh.select_linked(delimit=set())
        bpy.ops.object.mode_set(mode = 'OBJECT')
        bm.clear()
        bm.from_mesh(mesh)

        #标记出特殊边和点
        #These are special edge and vertex
        hair_verts=[]
        up_edges=[]
        down_edges=[]
        side_edges=[]
        up_verts=[]
        down_verts=[]
        wire_verts=[]
        side_verts=[]

        #标出头部，尾部，飘带顶点
        #try mark head,tail,ribbon vertex
        bm.verts.ensure_lookup_table()
        for i in range(len(bm.verts)):
            v=bm.verts[i]
            bone=bones_list[i]
            if bone.bone.use_connect==False:
                up_verts.append(v)
            elif len(bone.children)==0:
                down_verts.append(v)
            elif bone.children[0] not in bones_list:
                down_verts.append(v)
            if v.is_wire:
                wire_verts.append(v)
            if v.select :
                hair_verts.append(v)
                if cloth_convert_mod==1:
                    v.co=bone.tail
            if cloth_convert_mod==2:
                v.co=bone.tail

            
        bm.edges.ensure_lookup_table()
        for i in range(len(bm.edges)):
            e=bm.edges[i]
            vert1=e.verts[0]
            vert2=e.verts[1]
            if e.is_boundary:
                if vert1 in  up_verts and vert2 in up_verts:
                    up_edges.append(e)
                elif vert1 in down_verts and vert2 in down_verts:
                    down_edges.append(e)
                else:
                    side_edges.append(e)
                    if e.verts[0] not in side_verts:
                        side_verts.append(e.verts[0])
                    if e.verts[1] not in side_verts:
                        side_verts.append(e.verts[1])

        #延长头部顶点 
        #extend root vertex
        new_up_verts=[None for i in range(len(bm.verts))]
        new_down_verts=[None for i in range(len(bm.verts))]
        for i in range(len(up_verts)):
            v=up_verts[i]
            new_location=bones_list[v.index].head
            if cloth_convert_mod==1 and v not in hair_verts or cloth_convert_mod==3:
                for e in v.link_edges:
                    if e not in up_edges:
                        if e.verts[0]==v:
                            new_location=v.co*2-e.verts[1].co
                        else:
                            new_location=v.co*2-e.verts[0].co
                    break
            new_vert=bm.verts.new(new_location)
            new_edge=bm.edges.new([v,new_vert])
            new_up_verts[v.index]=new_vert
            if v in side_verts:
                side_verts.append(new_vert)
                side_edges.append(new_edge)
            bm.edges.ensure_lookup_table()

        #延长尾部顶点
        #extend tail vertex
        for i in range(len(down_verts)):
            v=down_verts[i]
            if v not in up_verts:
                new_location=[0,0,0]
                for e in v.link_edges:
                    if e not in down_edges:
                        if e.verts[0]==v:
                            new_location=v.co*2-e.verts[1].co
                        else:
                            new_location=v.co*2-e.verts[0].co
                    break
                new_vert=bm.verts.new(new_location)
                new_edge=bm.edges.new([v,new_vert])
                new_down_verts[v.index]=new_vert
                if v in side_verts:
                    side_verts.append(new_vert)
                    side_edges.append(new_edge)
                bm.edges.ensure_lookup_table()

        for i in range(len(up_edges)):
            e=up_edges[i]
            vert1=e.verts[0]
            vert2=e.verts[1]
            vert3=new_up_verts[vert2.index]
            vert4=new_up_verts[vert1.index]
            if vert3 != None and vert4 != None:
                bm.faces.new([vert1,vert2,vert3,vert4])
            bm.edges.ensure_lookup_table()

        for i in range(len(down_edges)):
            e=down_edges[i]
            vert1=e.verts[0]
            vert2=e.verts[1]
            vert3=new_down_verts[vert2.index]
            vert4=new_down_verts[vert1.index]
            if vert3 != None and vert4 != None:
                bm.faces.new([vert1,vert2,vert3,vert4])
            bm.edges.ensure_lookup_table()
            
        bm.verts.index_update( ) 
        bm.faces.ensure_lookup_table()
        new_side_verts=[None for i in range(len(bm.verts))]
        for i in range(len(side_verts)):
            v=side_verts[i]
            for e in v.link_edges:
                if e not in side_edges:
                    if e.verts[0]==v:
                        new_location=v.co*2-e.verts[1].co
                    else:
                        new_location=v.co*2-e.verts[0].co
                    break
            new_vert=bm.verts.new(new_location)
            new_side_verts[v.index]=new_vert
            bm.edges.ensure_lookup_table()

        for i in range(len(side_edges)):
            e=side_edges[i]
            vert1=e.verts[0]
            vert2=e.verts[1]
            vert3=new_side_verts[vert2.index]
            vert4=new_side_verts[vert1.index]
            if vert3 != None and vert4 != None:
                bm.faces.new([vert1,vert2,vert3,vert4])
            bm.edges.ensure_lookup_table()

        bm.verts.ensure_lookup_table()
        bm.to_mesh(mesh)

        bpy.ops.object.mode_set(mode = 'EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.normals_make_consistent(inside=False)
        bpy.ops.object.mode_set(mode = 'OBJECT')

        pin_vertex_group=cloth_obj.vertex_groups.new(name='mmd_cloth_pin')
        for obj in joints:
            bpy.data.objects.remove(obj)
        for obj in side_joints:
            if obj.rigid_body_constraint.object1 in rigid_bodys:
                side_rigid_body=obj.rigid_body_constraint.object1
                pin_rigid_body=obj.rigid_body_constraint.object2
            else:
                side_rigid_body=obj.rigid_body_constraint.object2
                pin_rigid_body=obj.rigid_body_constraint.object1
            
            index1=rigid_bodys.index(side_rigid_body)
            vert2=new_up_verts[index1]
            if vert2 !=None:
                index3=vert2.index
                vert3=new_side_verts[index3]
                if vert3 == None:
                    pin_index=[index3]
                else:
                    pin_index=[index3,vert3.index]
            else:
                pin_index=[index1]

            pin_bone_name=pin_rigid_body.mmd_rigid.bone

            skin_vertex_group=cloth_obj.vertex_groups.get(pin_bone_name)
            if skin_vertex_group==None:
                skin_vertex_group=cloth_obj.vertex_groups.new(name=pin_bone_name)
            skin_vertex_group.add(pin_index,1,'REPLACE')
            pin_vertex_group.add(pin_index,1,'REPLACE')
            bpy.data.objects.remove(obj)

        deform_vertex_group=mmd_mesh.vertex_groups.new(name='mmd_cloth_deform')

        cloth_obj.display_type = 'WIRE'

        mod=cloth_obj.modifiers.new('mmd_cloth_subsurface','SUBSURF')
        mod.levels = subdivide
        mod.render_levels = subdivide
        mod.boundary_smooth = 'PRESERVE_CORNERS'
        mod.show_only_control_edges = False


        mod=cloth_obj.modifiers.new('mmd_cloth_skin','ARMATURE')
        mod.object = mmd_arm
        mod.vertex_group = "mmd_cloth_pin"

        mod=cloth_obj.modifiers.new('mmd_cloth','CLOTH')
        mod.settings.vertex_group_mass = "mmd_cloth_pin"

        mod=cloth_obj.modifiers.new('mmd_cloth_smooth','CORRECTIVE_SMOOTH')
        mod.smooth_type = 'LENGTH_WEIGHTED'
        mod.rest_source = 'BIND'
        bpy.ops.object.correctivesmooth_bind(modifier="mmd_cloth_smooth")
        if subdivide==0:
            mod.show_viewport = False

        bpy.context.view_layer.objects.active=mmd_mesh

        for i in range(rigid_bodys_count):
            v=bm.verts[i]
            obj=rigid_bodys[i]
            bone=bones_list[i]
            name=bone.name
            if v in hair_verts and cloth_convert_mod==1 or cloth_convert_mod==2 :
                line_vertex_group=cloth_obj.vertex_groups.new(name=name)
                line_vertex_group.add([i],1,'REPLACE')
                for c in bone.constraints:
                    bone.constraints.remove(c)
                con=bone.constraints.new(type='STRETCH_TO')
                con.target = cloth_obj
                con.subtarget = name
                con.rest_length = bone.length
            else:
                mod=mmd_mesh.modifiers.new('combin_weight','VERTEX_WEIGHT_MIX')
                mod.vertex_group_a = deform_vertex_group.name
                mod.vertex_group_b = name
                mod.mix_set = 'OR'
                mod.mix_mode = 'ADD'
                mod.normalize = False
                bpy.ops.object.modifier_move_to_index(modifier="combin_weight", index=0)
                bpy.ops.object.modifier_apply(modifier="combin_weight")
                mmd_mesh.vertex_groups.remove(mmd_mesh.vertex_groups[name])
            bpy.data.objects.remove(obj)

        #挤出孤立边
        bpy.context.view_layer.objects.active=cloth_obj
        bpy.ops.object.mode_set(mode = 'EDIT')
        bpy.ops.mesh.select_non_manifold(extend=False, use_wire=True, use_boundary=False, use_multi_face=False, use_non_contiguous=False, use_verts=False)
        bpy.ops.mesh.extrude_edges_move(TRANSFORM_OT_translate={"value":(0, 0.01, 0)})
        bpy.ops.mesh.select_linked(delimit=set())
        bpy.ops.mesh.select_all(action='INVERT')
        bpy.ops.transform.shrink_fatten(value=mean_radius, use_even_offset=False, mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)

        bpy.ops.object.mode_set(mode = 'OBJECT')

        if len(mesh.polygons.items())!=0 and cloth_convert_mod!=2:
            bpy.context.view_layer.objects.active=mmd_mesh
            mod=mmd_mesh.modifiers.new('mmd_cloth_deform','SURFACE_DEFORM')
            mod.target = cloth_obj
            mod.vertex_group = deform_vertex_group.name
            bpy.ops.object.surfacedeform_bind(modifier=mod.name)

        bm.free()
