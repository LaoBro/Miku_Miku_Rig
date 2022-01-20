import bpy
import bpy_extras
import os
from bpy.types import Operator

def alert_error(title,message):
    def draw(self,context):
        self.layout.label(text=str(message))
    bpy.context.window_manager.popup_menu(draw,title=title,icon='ERROR')

def retarget_mixmao(OT,context):

    scene=context.scene
    mmr_property=scene.mmr_property
    rigify_arm=context.view_layer.objects.active
    mixamo_path=OT.filepath
    lock_location=mmr_property.lock_location
    fade_in_out=mmr_property.fade_in_out
    action_scale=mmr_property.action_scale
    auto_action_scale=mmr_property.auto_action_scale
    IKFK_arm=mmr_property.IKFK_arm
    IKFK_leg=mmr_property.IKFK_leg
    debug=mmr_property.debug

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
        context.collection.objects.link(obj)
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
    if IKFK_arm=='IK':
        retarget_arm.pose.bones["Arm_parent_L"]["IK_FK"]=0
        retarget_arm.pose.bones["Arm_parent_R"]["IK_FK"]=0
    elif IKFK_arm=='FK':
        retarget_arm.pose.bones["Arm_parent_L"]["IK_FK"]=1
        retarget_arm.pose.bones["Arm_parent_R"]["IK_FK"]=1
    if IKFK_arm !="None":
        retarget_arm.pose.bones["Arm_parent_L"].keyframe_insert(data_path='["IK_FK"]', frame=mixamo_action.frame_range[0])
        retarget_arm.pose.bones["Arm_parent_R"].keyframe_insert(data_path='["IK_FK"]', frame=mixamo_action.frame_range[0])

    if IKFK_leg=='IK':
        retarget_arm.pose.bones["Leg_parent_L"]["IK_FK"]=0
        retarget_arm.pose.bones["Leg_parent_R"]["IK_FK"]=0
    elif IKFK_leg=='FK':
        retarget_arm.pose.bones["Leg_parent_L"]["IK_FK"]=1
        retarget_arm.pose.bones["Leg_parent_R"]["IK_FK"]=1
    if IKFK_leg !='None':
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
    #插入IK硬度关键帧
    retarget_arm.pose.bones["Shoulder_L"].ik_stiffness_x = 0.99
    retarget_arm.pose.bones["Shoulder_L"].ik_stiffness_y = 0.99
    retarget_arm.pose.bones["Shoulder_L"].ik_stiffness_z = 0.99

    retarget_arm.pose.bones["Shoulder_R"].ik_stiffness_x = 0.99
    retarget_arm.pose.bones["Shoulder_R"].ik_stiffness_y = 0.99
    retarget_arm.pose.bones["Shoulder_R"].ik_stiffness_z = 0.99

    retarget_arm.pose.bones["Shoulder_L"].keyframe_insert(data_path='ik_stiffness_x', frame=mixamo_action.frame_range[0])
    retarget_arm.pose.bones["Shoulder_L"].keyframe_insert(data_path='ik_stiffness_y', frame=mixamo_action.frame_range[0])
    retarget_arm.pose.bones["Shoulder_L"].keyframe_insert(data_path='ik_stiffness_z', frame=mixamo_action.frame_range[0])

    retarget_arm.pose.bones["Shoulder_R"].keyframe_insert(data_path='ik_stiffness_x', frame=mixamo_action.frame_range[0])
    retarget_arm.pose.bones["Shoulder_R"].keyframe_insert(data_path='ik_stiffness_y', frame=mixamo_action.frame_range[0])
    retarget_arm.pose.bones["Shoulder_R"].keyframe_insert(data_path='ik_stiffness_z', frame=mixamo_action.frame_range[0])
    
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
    if debug==False:
        bpy.data.objects.remove(mixamo_arm)
        bpy.data.objects.remove(mixamo_arm2)
        bpy.data.objects.remove(retarget_arm)
    bpy.context.view_layer.objects.active=rigify_arm
    rigify_arm.select=True
    alert_error("提示","导入完成")
    return(True)
    
def load_vmd(OT,context):

    scene=context.scene
    mmr_property=scene.mmr_property
    rigify_arm=context.view_layer.objects.active
    vmd_path=OT.filepath
    fade_in_out=mmr_property.fade_in_out
    action_scale=mmr_property.action_scale
    debug=mmr_property.debug
    IKFK_leg=mmr_property.IKFK_leg

    if rigify_arm.type!='ARMATURE':
        alert_error("警告",'所选对象不是骨骼')
        return(False)
    if vmd_path==None:
        alert_error("警告",'找不到VMD文件')
        return(False)


    fename=str(os.path.split(vmd_path))
    print('path=')
    print(fename)
    action_name=str(os.path.splitext(fename)[0])
    bpy.ops.object.mode_set(mode = 'OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    #复制骨骼
    #duplicate armature
    rigify_arm2=rigify_arm.copy()
    context.collection.objects.link(rigify_arm2)
    for track in rigify_arm2.animation_data.nla_tracks:
        rigify_arm2.animation_data.nla_tracks.remove(track)
    bpy.context.view_layer.objects.active=rigify_arm2
    rigify_arm2.select=True
    print(vmd_path)
    old_frame_end=bpy.context.scene.frame_end
    #修复FK脚
    if IKFK_leg=='FK':
        rigify_arm2.pose.bones['Leg_ik_L'].mmd_bone.name_j=''
        rigify_arm2.pose.bones['Leg_ik_R'].mmd_bone.name_j=''
        rigify_arm2.pose.bones['Leg_fk_L'].mmd_bone.name_j='左足'
        rigify_arm2.pose.bones['Leg_fk_R'].mmd_bone.name_j='右足'

    bpy.ops.mmd_tools.import_vmd(filepath=vmd_path,scale=action_scale, margin=0)
    bpy.context.scene.frame_end=old_frame_end
    
    vmd_action=rigify_arm2.animation_data.action
    vmd_action.name=action_name

    #插入IKFK关键帧
    #insert IKFK keyframe
    rigify_arm2.pose.bones["Arm_parent_L"]["IK_FK"]=1
    rigify_arm2.pose.bones["Arm_parent_R"]["IK_FK"]=1
    if IKFK_leg=='FK':
        rigify_arm2.pose.bones["Leg_parent_L"]["IK_FK"]=1
        rigify_arm2.pose.bones["Leg_parent_R"]["IK_FK"]=1
    else:
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
    if debug==False:
        bpy.data.objects.remove(rigify_arm2)
    bpy.context.view_layer.objects.active=rigify_arm
    rigify_arm.select=True
    alert_error("提示","导入完成")

    return(True)

def export_vmd(OT,context):

    rigify_arm=context.view_layer.objects.active
    vmd_path=OT.filepath
    scale=OT.scale
    use_pose_mode=OT.use_pose_mode
    set_action_range=OT.set_action_range
    start_frame=OT.start_frame
    end_frame=OT.end_frame

    PMX_list=[
    '全ての親','センター','下半身','上半身','上半身2','首','頭','両目','左目','右目',
    '左足','左足ＩＫ','左つま先ＩＫ','右足','右足ＩＫ','右つま先ＩＫ',
    '左肩','左腕','左ひじ','左手首','右肩','右腕','右ひじ','右手首',
    '左親指０','左親指１','左親指２',
    '左人指１','左人指２','左人指３',
    '左中指１','左中指２','左中指３',
    '左薬指１','左薬指２','左薬指３',
    '左小指１','左小指２','左小指３',
    '右親指０','右親指１','右親指２',
    '右人指１','右人指２','右人指３',
    '右中指１','右中指２','右中指３',
    '右薬指１','右薬指２','右薬指３',
    '右小指１','右小指２','右小指３'
    ]

    if rigify_arm.type!='ARMATURE':
        alert_error("警告",'所选对象不是骨骼')
        return(False)
    if vmd_path==None:
        alert_error("警告",'导出路径错误')
        return(False)

    bpy.ops.object.mode_set(mode = 'OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    #复制骨骼
    #duplicate armature
    mmd_arm=None
    mmd_name=rigify_arm.name.replace('_Rig','')
    '''for obj in rigify_arm.children[0].children:
        if obj.type=='ARMATURE':
            mmd_arm=obj
            break'''
    if mmd_name in bpy.data.objects.keys():
        mmd_arm=bpy.data.objects[mmd_name]
    else:
        alert_error("警告",'找不到骨骼')
        return(False)

    mmd_arm2=mmd_arm.copy()
    context.collection.objects.link(mmd_arm2)
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active=mmd_arm2
    mmd_arm2.select=True
    print(vmd_path)

    if set_action_range:
        start_frame1=start_frame
        end_frame1=end_frame
    else:
        rigify_action=rigify_arm.animation_data.action
        if rigify_action ==None:
            return(False)
        start_frame1=rigify_action.frame_range[0]
        end_frame1=rigify_action.frame_range[1]

    bpy.ops.object.mode_set(mode = 'POSE')
    bpy.ops.pose.select_all(action='SELECT')

    for bone in mmd_arm2.pose.bones:
        if bone.mmd_bone.name_j in PMX_list:
            bone.bone.select=True
        else:
            bone.bone.select=False

    bpy.ops.nla.bake(frame_start=start_frame1, frame_end=end_frame1, only_selected=True, visual_keying=True,clear_constraints=True, bake_types={'POSE'})
    bpy.ops.object.mode_set(mode = 'OBJECT')
    bpy.ops.mmd_tools.export_vmd(filepath=vmd_path,scale=scale, use_pose_mode=use_pose_mode,use_frame_range=False)
    bpy.data.objects.remove(mmd_arm2)

    return(True)

class OT_Import_Mixamo(Operator, bpy_extras.io_utils.ImportHelper):
    bl_idname = "mmr.import_mixamo" 
    bl_label = "Import mixamo action"
    filter_glob: bpy.props.StringProperty( 
    default='*.fbx;', 
    options={'HIDDEN'} 
    )
    def execute(self,context):
        retarget_mixmao(self,context)
        return{"FINISHED"}

class OT_Import_Vmd(Operator, bpy_extras.io_utils.ImportHelper):
    bl_idname = "mmr.import_vmd" 
    bl_label = "Import vmd action"
    filter_glob: bpy.props.StringProperty( 
    default='*.vmd;', 
    options={'HIDDEN'} 
    )
    def execute(self,context):
        load_vmd(self,context)
        return{"FINISHED"}

class OT_Export_Vmd(Operator, bpy_extras.io_utils.ExportHelper):
    bl_idname = "mmr.export_vmd" 
    bl_label = "Export vmd action"

    filename_ext = ".vmd"

    filter_glob: bpy.props.StringProperty( 
    default='*.vmd;', 
    options={'HIDDEN'} ,
    maxlen=255
    )

    scale: bpy.props.FloatProperty(
        name="Action scale",
        description="Action scale",
        default=1,
        min=0
    )

    use_pose_mode: bpy.props.BoolProperty(
        name="Use pose mod",
        description="Use Pose Mod",
        default=False
    )
    
    set_action_range: bpy.props.BoolProperty(
        name="Set action range",
        description="Use Frame Range",
        default=False
    )
    start_frame: bpy.props.IntProperty(
        name="Start frame",
        description="Action start frame",
        default=1
    )
    end_frame: bpy.props.IntProperty(
        name="End frame",
        description="Action end frame",
        default=1
    )

    def execute(self,context):
        export_vmd(self,context)
        return{"FINISHED"}

Class_list=[OT_Import_Mixamo,OT_Import_Vmd,OT_Export_Vmd]