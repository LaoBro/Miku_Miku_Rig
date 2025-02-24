import bpy
import bpy_extras
import os
from bpy.types import Operator
from . import preset
from mathutils import Matrix,Vector,Quaternion,Euler

def alert_error(title,message):
    def draw(self,context):
        self.layout.label(text=str(message))
    bpy.context.window_manager.popup_menu(draw,title=title,icon='ERROR')

def retarget_mixmao(OT,context):

    scene=context.scene
    mmr_property=scene.mmr_property
    rigify_arm=context.view_layer.objects.active
    #把路径转成小写
    mixamo_path=OT.filepath.lower ()
    lock_location=mmr_property.lock_location
    fade_in_out=mmr_property.fade_in_out
    action_scale=mmr_property.action_scale
    auto_action_scale=mmr_property.auto_action_scale
    IKFK_arm=mmr_property.IKFK_arm
    IKFK_leg=mmr_property.IKFK_leg
    debug=mmr_property.debug

    if rigify_arm.type!='ARMATURE':
        alert_error('警告','所选物体不是骨骼')
        return(False)
    if mixamo_path==None:
        return(False)

    #获得文件路径
    #get file path
    #my_dir = os.path.dirname(os.path.realpath(__file__))
    #retarget_blend_file = os.path.join(my_dir, "mixamo_retarget_arm_ik.blend")
    fname,fename=os.path.split(mixamo_path)
    action_name=str(os.path.splitext(fename)[0])

    #导入FBX或BVH文件
    #import mixamo file
    bpy.ops.object.mode_set(mode = 'OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    if mixamo_path.endswith(".fbx"):
        bpy.ops.import_scene.fbx(filepath=mixamo_path,directory =fname)
    elif mixamo_path.endswith(".bvh"):
        bpy.ops.import_anim.bvh(filepath=mixamo_path, rotate_mode='QUATERNION')
    else:
        alert_error('警告','文件格式错误')
        return(False)
    for obj in bpy.data.objects:
        if obj.select==True:
            if obj.type=='ARMATURE':
                mixamo_arm=obj
            else:
                bpy.data.objects.remove(obj,do_unlink=True)
    mixamo_action=mixamo_arm.animation_data.action
    rigify_action=mixamo_action.copy()
    frame_range=mixamo_action.frame_range
    rigify_action.name=action_name

    old_frame=context.scene.frame_current
    context.scene.frame_current=int(frame_range[0])
    
    #写入MMR预设
    fbx_preset=preset.preset_dict_dict['retarget'][mmr_property.retarget_preset_name]
    preset.set_bone_type(mixamo_arm.pose,fbx_preset)
    #生成字典
    from_dict={}
    to_dict={}
    #from_to_dict={}
    type_from_to_list=[]
    match_bone_number=0
    for bone in mixamo_arm.pose.bones:
        if bone.mmr_bone.bone_type !='None':
            from_dict[bone.mmr_bone.bone_type]=bone.name
    for bone in rigify_arm.pose.bones:
        if bone.mmr_bone.bone_type !='None':
            to_dict[bone.mmr_bone.bone_type]=bone.name
    for bone_type,from_name in from_dict.items():
        if bone_type in to_dict:
            to_name=to_dict[bone_type]
            type_from_to_list.append((bone_type,from_name,to_name))
            match_bone_number+=1

    #检测关键骨骼是否存在
    from_necessary_bone_type_list=['thigh.L','thigh.R','upper_arm.L','upper_arm.R','forearm.L','forearm.R']
    to_necessary_bone_type_list=['spine','thigh.L','thigh.R','upper_arm.L','upper_arm.R','forearm.L','forearm.R']
    for bone_type in from_necessary_bone_type_list:
        if bone_type not in from_dict:
            alert_error('警告','导入骨骼缺失关键骨骼类型'+str(bone_type))
            return(False)
    for bone_type in to_necessary_bone_type_list:
        if bone_type not in to_dict:
            alert_error('警告','所选骨骼缺失关键骨骼类型'+str(bone_type))
            return(False)

    #计算物体矩阵
    #物体矩阵a
    mat_wa4=mixamo_arm.matrix_world
    mat_wa=mat_wa4.to_3x3()

    q_wa=mat_wa.to_quaternion()
    q_wai=q_wa.inverted()
    #物体矩阵b
    mat_wb=rigify_arm.matrix_world.to_3x3()

    q_wb=mat_wb.to_quaternion()
    q_wbi=q_wb.inverted()

    #自动动作缩放
    #auto action scale
    action_scale_finel=1
    if auto_action_scale:
        head_a=mixamo_arm.pose.bones[from_dict['thigh.L']].bone.head_local
        head_a= q_wa @ head_a
        head_a+=mixamo_arm.location
        head_b=rigify_arm.pose.bones[to_dict['thigh.L']].bone.head_local
        head_b= q_wb @ head_b
        action_scale_finel=abs(head_b[2]/head_a[2])
    else:
        action_scale_finel=action_scale
        

    #调整世界矩阵缩放
    #mat_s=Matrix([(action_scale_finel,0,0),(0,action_scale_finel,0),(0,0,action_scale_finel)])
    #mat_wa=mat_s @ mat_wa
    print('scale='+str(action_scale_finel))

    q_wab=q_wai @ q_wb
    q_wba=q_wbi @ q_wa

    pose_bones_a=mixamo_arm.pose.bones
    pose_bones_b=rigify_arm.pose.bones

    #生成手臂角度差
    if OT.first_frame_as_rest_pose:
        v_a_arm=pose_bones_a[from_dict['upper_arm.L']].head-pose_bones_a[from_dict['forearm.L']].head
    else:
        v_a_arm=pose_bones_a[from_dict['upper_arm.L']].bone.head_local-pose_bones_a[from_dict['forearm.L']].bone.head_local
    v_b_arm=pose_bones_b[to_dict['upper_arm.L']].bone.head_local-pose_bones_b[to_dict['forearm.L']].bone.head_local
    v_a_arm=mat_wa @ v_a_arm
    v_b_arm=mat_wb @ v_b_arm
    v_a_arm=v_a_arm.xz
    v_b_arm=v_b_arm.xz

    #肩膀大臂分别旋转一半
    angle_arm=v_a_arm.angle_signed(v_b_arm)
    q_arm_l=Quaternion((0,1,0),-angle_arm)
    q_arm_r=Quaternion((0,1,0),angle_arm)

    #计算手臂旋转四元数
    q_warb_l=q_wai @ q_arm_l @ q_wb
    q_warb_r=q_wai @ q_arm_r @ q_wb
    q_wbra_l=q_wbi @ q_arm_r @ q_wa
    q_wbra_r=q_wbi @ q_arm_l @ q_wa

    rotate_wab_l_set={
        'upper_arm.L','forearm.L',
        'thumb.01.L','thumb.02.L','thumb.03.L',
        'f_index.01.L','f_index.02.L','f_index.03.L',
        'f_middle.01.L','f_middle.02.L','f_middle.03.L',
        'f_ring.01.L','f_ring.02.L','f_ring.03.L',
        'f_pinky.01.L','f_pinky.02.L','f_pinky.03.L',
    }
    rotate_wab_r_set={
        'upper_arm.R','forearm.R',
        'thumb.01.R','thumb.02.R','thumb.03.R',
        'f_index.01.R','f_index.02.R','f_index.03.R',
        'f_middle.01.R','f_middle.02.R','f_middle.03.R',
        'f_ring.01.R','f_ring.02.R','f_ring.03.R',
        'f_pinky.01.R','f_pinky.02.R','f_pinky.03.R',
    }
    rotate_wba_l_set={
        'forearm.L',
        'thumb.01.L','thumb.02.L','thumb.03.L',
        'f_index.01.L','f_index.02.L','f_index.03.L',
        'f_middle.01.L','f_middle.02.L','f_middle.03.L',
        'f_ring.01.L','f_ring.02.L','f_ring.03.L',
        'f_pinky.01.L','f_pinky.02.L','f_pinky.03.L',
        }
    rotate_wba_r_set={
        'forearm.R',
        'thumb.01.R','thumb.02.R','thumb.03.R',
        'f_index.01.R','f_index.02.R','f_index.03.R',
        'f_middle.01.R','f_middle.02.R','f_middle.03.R',
        'f_ring.01.R','f_ring.02.R','f_ring.03.R',
        'f_pinky.01.R','f_pinky.02.R','f_pinky.03.R',
    }
    translation_set={'spine'}

    fcurves_b=rigify_action.fcurves

    #清除曲线函数
    def remove_fcurves(obj):
        path=obj.path_from_id('location')
        for i in range(3):
            fcurve=fcurves_b.find(path,index=i)
            if fcurve:
                fcurves_b.remove(fcurve)
        path=obj.path_from_id('rotation_quaternion')
        for i in range(4):
            fcurve=fcurves_b.find(path,index=i)
            if fcurve:
                fcurves_b.remove(fcurve)
        path=obj.path_from_id('rotation_euler')
        for i in range(3):
            fcurve=fcurves_b.find(path,index=i)
            if fcurve:
                fcurves_b.remove(fcurve)
        path=obj.path_from_id('scale')
        for i in range(3):
            fcurve=fcurves_b.find(path,index=i)
            if fcurve:
                fcurves_b.remove(fcurve)

    #FBX限定重定向函数
    #暂时忽略缩放
    def retarget_fcurves(q_l,q_r,obj_from,obj_to,translation=False,translation_offset=None):

        #删除缩放曲线
        path=obj_from.path_from_id('scale')
        for i in range(3):
            fc=fcurves_b.find(path,index=i)
            if fc:
                fcurves_b.remove(fc)

        #修改旋转模式为四元数
        rotation_mode=obj_from.rotation_mode
        obj_to.rotation_mode='QUATERNION'

        #欧拉角曲线改完四元数曲线函数
        def efc_to_qfc(obj):
            path_e=obj.path_from_id('rotation_euler')
            path_q=obj.path_from_id('rotation_quaternion')
            fcurve=None
            for i in range(3):
                fcurve=fcurves_b.find(path_e,index=i)
                fcurve.data_path=path_q
            kps=fcurve.keyframe_points
            kps_len=len(kps)
            qfc4=fcurves_b.new(path_q,index=3,action_group=fcurve.group.name)
            kps=qfc4.keyframe_points
            kps.add(kps_len)


        #曲线转矩阵函数
        def get_co_lists(obj_from,obj_to,attr_name):

            co_lists=[]
            path_from=obj_from.path_from_id(attr_name)
            path_to=obj_to.path_from_id(attr_name)
            dimension=len(getattr(obj,attr_name))
            #把关键帧数据提取为矩阵
            for i in range(dimension):
                fcurve=fcurves_b.find(path_from,index=i)
                #找不到曲线则返回None
                if not fcurve:
                    return None
                #修改路径
                fcurve.data_path=path_to
                kps=fcurve.keyframe_points
                co_list=[None]*2*len(kps)
                kps.foreach_get('co',co_list)
                co_lists.append(co_list)
            return co_lists
        #矩阵转曲线函数
        def set_co_lists(obj,attr_name,co_lists):
            path=obj.path_from_id(attr_name)
            dimension=len(getattr(obj,attr_name))
            for i in range(dimension):
                co_list=co_lists[i]
                fcurve=fcurves_b.find(path,index=i)
                kps=fcurve.keyframe_points
                kps.foreach_set('co',co_list)
                fcurve.update()

        #重定向平移曲线
        if translation:
            l_co_lists=get_co_lists(obj_from,obj_to,'location')
            if l_co_lists:
                frame_count=len(l_co_lists[0])
                for i in range(1,frame_count,2):
                    #从列表中获得平移向量
                    old_location=Vector((l_co_lists[0][i],l_co_lists[1][i],l_co_lists[2][i]))
                    if translation_offset is not None:
                        old_location+=translation_offset
                    new_location=q_l @ old_location 
                    new_location*=action_scale_finel

                    #修改列表
                    l_co_lists[0][i]=new_location[0]
                    l_co_lists[1][i]=new_location[1]
                    l_co_lists[2][i]=new_location[2]

                #修改曲线
                set_co_lists(obj_to,'location',l_co_lists)

        #重定向旋转曲线
        #四元数旋转的情况
        if rotation_mode=='QUATERNION':
            #获得四元数关键帧列表
            q_co_lists=get_co_lists(obj_from,obj_to,'rotation_quaternion')
            #有四元数曲线的情况
            if q_co_lists:
                frame_count=len(q_co_lists[0])
                for i in range(1,frame_count,2):
                    #从列表中获得变换四元数
                    old_quaternion=Quaternion((q_co_lists[0][i],q_co_lists[1][i],q_co_lists[2][i],q_co_lists[3][i]))
                    new_quaternion = q_l @ old_quaternion @ q_r

                    #修改列表
                    q_co_lists[0][i]=new_quaternion[0]
                    q_co_lists[1][i]=new_quaternion[1]
                    q_co_lists[2][i]=new_quaternion[2]
                    q_co_lists[3][i]=new_quaternion[3]
                
                #修改曲线
                set_co_lists(obj_to,'rotation_quaternion',q_co_lists)

        #欧拉角旋转的情况
        else:
            #获得欧拉角关键帧列表
            e_co_lists=get_co_lists(obj_from,obj_to,'rotation_euler')
            efc_to_qfc(obj_to)
            #有欧拉角曲线的情况
            if e_co_lists:
                frame_count=len(e_co_lists[0])
                #添加第四条曲线
                e_co_lists.append([None]*frame_count)
                for i in range(1,frame_count,2):
                    #从列表获得变换欧拉角
                    old_euler=Euler((e_co_lists[0][i],e_co_lists[1][i],e_co_lists[2][i]),rotation_mode)
                    #获得当前是第几帧
                    co0=e_co_lists[0][i-1]
                    old_quaternion=old_euler.to_quaternion()
                    new_quaternion=q_l @ old_quaternion @ q_r

                    #修改列表
                    e_co_lists[0][i]=new_quaternion[0]
                    e_co_lists[1][i]=new_quaternion[1]
                    e_co_lists[2][i]=new_quaternion[2]
                    e_co_lists[3][i]=new_quaternion[3]
                    e_co_lists[3][i-1]=co0

                set_co_lists(obj_to,'rotation_quaternion',e_co_lists)


    #开始遍历列表
    for bone_type , from_name , to_name in type_from_to_list:

        posebone_a=pose_bones_a[from_name]
        posebone_b=pose_bones_b[to_name]

        bone_a=posebone_a.bone
        bone_b=posebone_b.bone

        mat_a=bone_a.matrix_local
        mat_b=bone_b.matrix_local
        mat_ap=posebone_a.matrix

        #计算骨骼四元数
        q_a=mat_a.to_quaternion()
        q_ai=q_a.inverted()
        q_b=mat_b.to_quaternion()
        q_bi=q_b.inverted()
        q_ap=mat_ap.to_quaternion()
        q_api=q_ap.inverted()

        #计算右乘四元数
        q_r:Quaternion

        if OT.first_frame_as_rest_pose:
            q_r=q_api
        else:
            q_r=q_ai

        if bone_type in rotate_wab_l_set:
            q_r @= q_warb_l
        elif bone_type in rotate_wab_r_set:
            q_r @= q_warb_r
        else:
            q_r @= q_wab

        q_r @= q_b

        #计算左乘四元数
        q_l:Quaternion

        q_l=q_bi

        if bone_type in rotate_wba_l_set:
            q_l @= q_wbra_l
        elif bone_type in rotate_wba_r_set:
            q_l @= q_wbra_r
        else:
            q_l @= q_wba

        q_l @= q_a

        #mat_R=mat_R.to_4x4()
        #mat_L=mat_L.to_4x4()

        translation=False
        if bone_type in translation_set:
            translation=True

        retarget_fcurves(q_l,q_r,posebone_a,posebone_b,translation)

    if 'spine' not in from_dict and 'spine' in to_dict:
        print('Action have no spine')

        x_finel,y_finel,z_finel=mat_wa4.to_translation()*action_scale_finel

        mat_wat=Matrix([
            (1,0,0,-x_finel),
            (0,1,0,-y_finel),
            (0,0,1,-z_finel),
            (0,0,0,1)
        ])

        spine_name=to_dict['spine']
        spine_posebone=pose_bones_b[spine_name]
        spine_bone=spine_posebone.bone
        spine_mat=spine_bone.matrix_local.to_3x3()

        q_spine=spine_mat.to_quaternion()

        #mat_R=mat_wab @ spine_mat
        #mat_R=mat_R.to_4x4()

        q_r=q_wab @ q_spine

        '''mat_L=spine_mat.inverted() @ mat_wbi
        mat_L=mat_L.to_4x4()
        mat_L=mat_L @ mat_wat'''

        q_l = q_spine.inverted() @ q_wbi

        retarget_fcurves(q_l,q_r,mixamo_arm,spine_posebone,True,-mixamo_arm.location)
    else:
        remove_fcurves(rigify_arm)

    #锁定骨骼位置
    if lock_location:
        path=pose_bones_b[to_dict['spine']].path_from_id('location')
        curve_lx=fcurves_b.find(path,index=0)
        curve_ly=fcurves_b.find(path,index=1)
        if curve_lx and curve_ly:
            for keyframe in curve_lx.keyframe_points and curve_ly.keyframe_points:
                keyframe.co[1]=0

    #曲线操作

    def insert_keyframe(path,frame,value):
        fcurve=fcurves_b.find(path)
        if fcurve == None:
            fcurve=fcurves_b.new(path)
        fcurve.keyframe_points.insert(frame,value,options={'FAST'})

    #插入IKFK关键帧
    #insert IKFK keyframe
    insert_keyframe('pose.bones["upper_arm_parent.L"]["IK_FK"]',frame_range[0],1)
    insert_keyframe('pose.bones["upper_arm_parent.R"]["IK_FK"]',frame_range[0],1)

    insert_keyframe('pose.bones["thigh_parent.L"]["IK_FK"]',frame_range[0],1)
    insert_keyframe('pose.bones["thigh_parent.R"]["IK_FK"]',frame_range[0],1)

    insert_keyframe('pose.bones["torso"]["neck_follow"]',frame_range[0],1)
    insert_keyframe('pose.bones["torso"]["head_follow"]',frame_range[0],1)
    #插入手腕旋转约束关键帧
    #insert wrist rotation constrain keyframe
    insert_keyframe('pose.bones["hand_ik.L"].constraints["wrist_rotation"].influence',frame_range[0],0)
    insert_keyframe('pose.bones["hand_ik.R"].constraints["wrist_rotation"].influence',frame_range[0],0)
    insert_keyframe('pose.bones["shoulder.L"].constraints["MMR_auto_shoulder"].influence',frame_range[0],0)
    insert_keyframe('pose.bones["shoulder.R"].constraints["MMR_auto_shoulder"].influence',frame_range[0],0)
    #清空部分位置关键帧
    #clear certain keyframe

    bpy.ops.object.mode_set(mode = 'OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active=rigify_arm

    if mmr_property.import_as_NLA_strip:
        target_track=rigify_arm.animation_data.nla_tracks.new()
        target_track.name='mixamo_track'
        target_strip=target_track.strips.new(action_name,bpy.context.scene.frame_current,rigify_action)
        target_strip.blend_type = 'REPLACE'
        #target_strip.use_auto_blend = True
        target_strip.extrapolation = 'NOTHING'
        target_strip.blend_in = fade_in_out
        target_strip.blend_out = fade_in_out
        target_strip.frame_start+=old_frame-1
        target_strip.frame_end+=old_frame-1

        #更改原动作混合模式为合并
        rigify_arm.animation_data.action_blend_type = 'COMBINE'
    else:
        rigify_arm.animation_data.action=rigify_action

    if debug==False:
        bpy.data.objects.remove(mixamo_arm,do_unlink=True)
        bpy.data.actions.remove(mixamo_action,do_unlink=True)
        context.scene.frame_current=old_frame


    rigify_arm.select_set(True)
    alert_error("提示","导入完成,匹配骨骼数:"+str(match_bone_number))
    return(True)
    
def load_vmd(OT,context):

    scene=context.scene
    mmr_property=scene.mmr_property
    rigify_arm=context.view_layer.objects.active
    vmd_path=OT.filepath
    fade_in_out=mmr_property.fade_in_out
    action_scale=mmr_property.action_scale
    debug=mmr_property.debug

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
    rigify_arm2.animation_data.action=None
    for track in rigify_arm2.animation_data.nla_tracks:
        rigify_arm2.animation_data.nla_tracks.remove(track)
    bpy.context.view_layer.objects.active=rigify_arm2
    rigify_arm2.select_set(True)
    print(vmd_path)
    old_frame_end=bpy.context.scene.frame_end
    old_frame=context.scene.frame_current

    #指定mmd骨骼名称
    #生成字典
    mmd_dict={
    'root':'全ての親','Center':'センター','Groove':'グルーブ','LowerBody':'下半身','spine.001':'上半身','spine.003':'上半身2','spine.004':'首','spine.006':'頭',
    'thigh.L':'左足','shin.L':'左ひざ','foot.L':'左足首','toe.L':'左足先EX','LegIK_L':'左足ＩＫ',
    'thigh.R':'右足','shin.R':'右ひざ','foot.R':'右足首','toe.R':'右足先EX','LegIK_R':'右足ＩＫ',
    'shoulder.L':'左肩','upper_arm.L':'左腕','forearm.L':'左ひじ','hand.L':'左手首',
    'shoulder.R':'右肩','upper_arm.R':'右腕','forearm.R':'右ひじ','hand.R':'右手首',
    'thumb.01.L':'左親指０','thumb.02.L':'左親指１','thumb.03.L':'左親指２',
    'f_index.01.L':'左人指１','f_index.02.L':'左人指２','f_index.03.L':'左人指３',
    'f_middle.01.L':'左中指１','f_middle.02.L':'左中指２','f_middle.03.L':'左中指３',
    'f_ring.01.L':'左薬指１','f_ring.02.L':'左薬指２','f_ring.03.L':'左薬指３',
    'f_pinky.01.L':'左小指１','f_pinky.02.L':'左小指２','f_pinky.03.L':'左小指３',
    'thumb.01.R':'右親指０','thumb.02.R':'右親指１','thumb.03.R':'右親指２',
    'f_index.01.R':'右人指１','f_index.02.R':'右人指２','f_index.03.R':'右人指３',
    'f_middle.01.R':'右中指１','f_middle.02.R':'右中指２','f_middle.03.R':'右中指３',
    'f_ring.01.R':'右薬指１','f_ring.02.R':'右薬指２','f_ring.03.R':'右薬指３',
    'f_pinky.01.R':'右小指１','f_pinky.02.R':'右小指２','f_pinky.03.R':'右小指３'
    }
    rigify_dict={}
    for bone in rigify_arm2.pose.bones:
        bone1=rigify_arm.pose.bones[bone.name]
        bone_type=bone.mmr_bone.bone_type
        if bone_type != 'None':
            rigify_dict[bone.mmr_bone.bone_type]=bone.name
            if bone_type in mmd_dict:
                bone.mmd_bone.name_j=mmd_dict[bone_type]
                bone1.rotation_mode = 'QUATERNION'

    #自动缩放
    action_scale_finel=1
    if mmr_property.auto_action_scale:
        head_b=rigify_arm2.pose.bones[rigify_dict['thigh.L']].bone.head_local
        action_scale_finel=head_b[2]/10.2857
    else:
        action_scale_finel=action_scale
    print('Action scale='+str(action_scale_finel))

    #矫正手臂角度
    bone_a=rigify_arm2.pose.bones[rigify_dict['upper_arm.L']]
    bone_b=rigify_arm2.pose.bones[rigify_dict['forearm.L']]
    v_rigify_arm=bone_b.bone.head_local-bone_a.bone.head_local
    v_rigify_arm=v_rigify_arm.xz
    v_mmd_arm=(2.1216, -1.6906)

    angle_arm=v_rigify_arm.angle_signed(v_mmd_arm)
    mat_a=bone_a.bone.matrix_local.to_3x3()
    mat_2=Matrix.Rotation(angle_arm,3,(0,1,0))
    mat_3=mat_a.inverted() @ mat_2 @ mat_a
    bone_a.rotation_mode='QUATERNION'
    bone_a.rotation_quaternion=mat_3.to_quaternion()

    bone_a=rigify_arm2.pose.bones[rigify_dict['upper_arm.R']]
    mat_a=bone_a.bone.matrix_local.to_3x3()
    mat_2=Matrix.Rotation(-angle_arm,3,(0,1,0))
    mat_3=mat_a.inverted() @ mat_2 @ mat_a
    bone_a.rotation_mode='QUATERNION'
    bone_a.rotation_quaternion=mat_3.to_quaternion()
    
    bpy.ops.mmd_tools.import_vmd(files= [{"name": vmd_path}],scale=action_scale_finel,use_pose_mode=True, margin=0)
    
    vmd_action = rigify_arm2.animation_data.action

    fcurves=vmd_action.fcurves
    frame_range=vmd_action.frame_range

    #复制曲线
    def copy_fcurve(FK_type):
        FK_name=rigify_dict[FK_type]
        IK_name=FK_name.replace('_fk.','_ik.')
        if IK_name in rigify_arm2.pose.bones.keys():
            FK_bone=rigify_arm2.pose.bones[FK_name]
            IK_bone=rigify_arm2.pose.bones[IK_name]
            IK_bone1=rigify_arm.pose.bones[IK_name]
            IK_bone1.rotation_mode = 'QUATERNION'

            fcurve_data_list=[('rotation_quaternion',4),('location',3)]
            keyframe_data_list=['co','interpolation','handle_left','handle_left_type','handle_right','handle_right_type']
            for attr_name,attr_len in fcurve_data_list:
                for index in range(attr_len):

                    path1=FK_bone.path_from_id(attr_name)
                    path2=IK_bone.path_from_id(attr_name)

                    fcurve1=fcurves.find(path1,index=index)
                    
                    if (fcurve1 != None):
                        fcurve2=fcurves.new(path2,index=index)

                        keyframe_points1=fcurve1.keyframe_points
                        keyframe_points2=fcurve2.keyframe_points

                        keyframe_len=len(keyframe_points1)
                        keyframe_points2.add(keyframe_len)

                        for i,keyframe1 in enumerate(keyframe_points1):
                            keyframe2=keyframe_points2[i]

                            for keyframe_data in keyframe_data_list:
                                attr=getattr(keyframe1,keyframe_data)
                                setattr(keyframe2,keyframe_data,attr)

    
    copy_fcurve('thigh.L')
    copy_fcurve('thigh.R')

    #清空部分位置关键帧
    #clear certain keyframe
    for bone in rigify_arm2.pose.bones:
        if bone.bone.hide==False:
            if bone.lock_location[0] == True:
                bone_path=bone.path_from_id('location')
                location_fcurves=[fcurves.find(bone_path,index=0),fcurves.find(bone_path,index=1),fcurves.find(bone_path,index=2)]
                for fcurve in location_fcurves:
                    if fcurve :
                        fcurves.remove(fcurve)
    

    #导入mmd骨骼
    old_scene=context.scene
    new_scene=bpy.data.scenes.new('MMR_scene')
    context.window.scene=new_scene

    mmd_arm_name="mmd_leg"
    my_dir = os.path.dirname(os.path.realpath(__file__))
    mmd_leg_blend_file = os.path.join(my_dir, "MMD_leg.blend")
    with bpy.data.libraries.load(mmd_leg_blend_file) as (data_from, data_to):
        data_to.objects = [mmd_arm_name]

    mmd_arm=data_to.objects[0]
    context.collection.objects.link(mmd_arm)
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active=mmd_arm
    mmd_arm.select_set(True)

    #匹配骨骼轴向
    bpy.ops.object.mode_set(mode = 'EDIT')

    def match_bone(from_type,to_name_list):
        mat_rigify=rigify_arm.data.bones[rigify_dict[from_type]].matrix_local.copy()
        for to_name in to_name_list:
            to_bone=mmd_arm.data.edit_bones[to_name]
            mat_mmd=to_bone.matrix
            mat_rigify[0][3]=mat_mmd[0][3]
            mat_rigify[1][3]=mat_mmd[1][3]
            mat_rigify[2][3]=mat_mmd[2][3]
            to_bone.matrix=mat_rigify

    match_bone('LegIK_L',['foot.L.parent','foot.L'])
    match_bone('LegIK_R',['foot.R.parent','foot.R'])
    match_bone('shoulder.L',['shoulder.L','肩.L'])
    match_bone('shoulder.R',['shoulder.R','肩.R'])
    match_bone('upper_arm.L',['upper_arm.L','腕.L'])
    match_bone('upper_arm.R',['upper_arm.R','腕.R'])
    match_bone('forearm.L',['forearm.L','ひじ.L'])
    match_bone('forearm.R',['forearm.R','ひじ.R'])
    match_bone('hand.L',['hand.L','手首.L'])
    match_bone('hand.R',['hand.R','手首.R'])
    match_bone('spine',['腰','spine'])

    mmd_arm.data.edit_bones["全ての親"].matrix=rigify_arm.data.bones[rigify_dict['Root']].matrix_local

    bpy.ops.object.mode_set(mode = 'POSE')
    bpy.ops.mmd_tools.import_vmd(files=[{"name": vmd_path}],scale=1, margin=0)
    bpy.ops.pose.select_all(action='DESELECT')
    bake_name_list=['foot.L','foot.R','shoulder.L','shoulder.R','upper_arm.L','upper_arm.R','forearm.L','forearm.R','hand.L','hand.R','spine']
    for name in bake_name_list:
        mmd_arm.data.bones[name].select=True

    mmd_arm.animation_data_create()
    vmd_action2=mmd_arm.animation_data.action
    fcurves2=vmd_action2.fcurves
    frame_range=vmd_action2.frame_range

    bpy.ops.nla.bake(frame_start=int(frame_range[0]), frame_end=int(frame_range[1]), visual_keying=True, clear_constraints=True, use_current_action=True, bake_types={'POSE'})
    context.window.scene=old_scene
    
    #检测IKFK动作
    #IKFK_leg=1-mmd_arm.pose.bones["ひざ.L"].constraints["IK"].mute
    IKFK_leg=True
    shin_bone=mmd_arm.pose.bones['ひざ.L']
    leg_IK_bone=mmd_arm.pose.bones['足ＩＫ.L']
    shin_path=shin_bone.path_from_id('rotation_quaternion')
    leg_IK_path=leg_IK_bone.path_from_id('location')
    fcurve_shin=fcurves2.find(shin_path,index=0)
    fcurve_leg_IK=fcurves2.find(leg_IK_path,index=0)
    if fcurve_shin :
        if fcurve_leg_IK:
            IKFK_leg=len(fcurve_leg_IK.keyframe_points)>len(fcurve_shin.keyframe_points)
        else:
            IKFK_leg=False
    else:
        IKFK_leg=True

    def insert_keyframe(path,frame,value):
        fcurve=fcurves.find(path)
        if fcurve == None:
            fcurve=fcurves.new(path)
        fcurve.keyframe_points.insert(frame,value,options={'FAST'})

    #插入IKFK关键帧
    #insert IKFK keyframe
    insert_keyframe('pose.bones["upper_arm_parent.L"]["IK_FK"]',frame_range[0],1)
    insert_keyframe('pose.bones["upper_arm_parent.R"]["IK_FK"]',frame_range[0],1)
    if IKFK_leg:
        insert_keyframe('pose.bones["thigh_parent.L"]["IK_FK"]',frame_range[0],0)
        insert_keyframe('pose.bones["thigh_parent.R"]["IK_FK"]',frame_range[0],0)
    else:
        insert_keyframe('pose.bones["thigh_parent.L"]["IK_FK"]',frame_range[0],1)
        insert_keyframe('pose.bones["thigh_parent.R"]["IK_FK"]',frame_range[0],1)

    #插入脖子跟随关键帧
    insert_keyframe('pose.bones["torso"]["neck_follow"]',frame_range[0],1)
    insert_keyframe('pose.bones["torso"]["head_follow"]',frame_range[0],1)

    #插入脚掌约束关键帧
    #insert leg constrain keyframe
    insert_keyframe('pose.bones["DEF-Ankle_L"].constraints[0]',frame_range[0],0)
    insert_keyframe('pose.bones["DEF-Ankle_R"].constraints[0]',frame_range[0],0)

    #插入肩膀联动关键帧
    insert_keyframe('pose.bones["shoulder.L"].constraints["MMR_auto_shoulder"].influence',frame_range[0],0)
    insert_keyframe('pose.bones["shoulder.R"].constraints["MMR_auto_shoulder"].influence',frame_range[0],0)

    #转移曲线
    def copy_fcurve(bone_type,key_names,bake_name,translation=False):

        if bone_type in rigify_dict:
            #获得控制器骨骼和烘焙骨骼
            rigify_bone=rigify_arm2.pose.bones[rigify_dict[bone_type]]
            bake_bone=mmd_arm.pose.bones[bake_name]
            rigify_bone.rotation_mode = 'QUATERNION'

            keyframe_data_list=['co','interpolation','handle_left','handle_left_type','handle_right','handle_right_type']

            keyframe_set=set()
            bezier_L_dict={}
            bezier_R_dict={}

            def get_fcurve(obj,fcurves,id,index):
                path=obj.path_from_id(id)
                fcurve=fcurves.find(path,index=index)
                return fcurve

            def new_fcurve(obj,fcurves,id,index):
                path=obj.path_from_id(id)
                fcurve=fcurves.find(path,index=index)
                if fcurve:
                    group=fcurve.group
                    fcurves.remove(fcurve)
                    fcurve=fcurves.new(path,index=index)
                    fcurve.group=group
                else:
                    fcurve=fcurves.new(path,index=index)
                return fcurve

            for key_name in key_names:
                key_bone=mmd_arm.pose.bones[key_name]
                fcurve=get_fcurve(key_bone,fcurves2,'location',0)
                if fcurve==None:
                    continue
                kps=fcurve.keyframe_points
                kp0=kps[0]
                x0=int(kp0.co[0])
                keyframe_set.add(x0)
                for i in range(len(kps)-1):
                    kp0=kps[i]
                    kp1=kps[i+1]
                    x0=int(kp0.co[0])
                    x1=int(kp1.co[0])
                    keyframe_set.add(x1)
                    if kp0.interpolation=='BEZIER':
                        d = (kp1.co - kp0.co)
                        #防止除零
                        if d[1]!=0:
                            bezier=[None,None]
                            if x0 not in bezier_R_dict:
                                bezier_R=kp0.handle_right-kp0.co
                                bezier_R[0]/=d[0]
                                bezier_R[1]/=d[1]
                                #bezier_R[0]=max(min(bezier_R[0],1),-1)
                                #bezier_R[1]=max(min(bezier_R[1],1),-1)
                                bezier_R_dict[x0]=bezier_R

                            if x1 not in bezier_L_dict:
                                bezier_L=kp1.handle_left-kp0.co
                                bezier_L[0]/=d[0]
                                bezier_L[1]/=d[1]
                                #bezier_L[0]=max(min(bezier_L[0],1),-1)
                                #bezier_L[1]=max(min(bezier_L[1],1),-1)
                                bezier_L_dict[x1]=bezier_L


            for index in range(4):

                bake_fcurve=get_fcurve(bake_bone,fcurves2,'rotation_quaternion',index)
                rigify_fcurve=new_fcurve(rigify_bone,fcurves,'rotation_quaternion',index)

                bake_kps=bake_fcurve.keyframe_points
                rigify_kps=rigify_fcurve.keyframe_points

                keyframe_len=len(keyframe_set)
                rigify_kps.add(keyframe_len)

                for i,co0 in enumerate(keyframe_set):
                    #co0需要减一
                    keyframe1=bake_kps[co0-1]
                    keyframe2=rigify_kps[i]
                    keyframe2.co=keyframe1.co
                
                rigify_fcurve.update()

                for i in range(keyframe_len-1):
                    kp0=rigify_kps[i]
                    kp1=rigify_kps[i+1]
                    x0=int(kp0.co[0])
                    x1=int(kp1.co[0])
                    d = (kp1.co - kp0.co)
                    if x0 in bezier_R_dict:
                        kp0.interpolation='BEZIER'
                        kp0.handle_right_type = 'FREE'
                        bezier=bezier_R_dict[x0]
                        kp0.handle_right = kp0.co + d*bezier
                    else:
                        kp0.interpolation = 'LINEAR'
                    if x1 in bezier_L_dict:
                        kp1.handle_left_type = 'FREE'
                        bezier=bezier_L_dict[x1]
                        kp1.handle_left = kp0.co + d*bezier
                
                rigify_fcurve.update()

                if translation:
                    for index in range(3):

                        bake_fcurve=get_fcurve(bake_bone,fcurves2,'location',index)
                        rigify_fcurve=new_fcurve(rigify_bone,fcurves,'location',index)

                        bake_kps=bake_fcurve.keyframe_points
                        rigify_kps=rigify_fcurve.keyframe_points

                        keyframe_len=len(keyframe_set)
                        rigify_kps.add(keyframe_len)

                        for i,co0 in enumerate(keyframe_set):
                            #co0需要减一
                            keyframe1=bake_kps[co0-1]
                            keyframe2=rigify_kps[i]
                            keyframe2.co[0]=keyframe1.co[0]
                            keyframe2.co[1]=keyframe1.co[1]*action_scale
                        
                        rigify_fcurve.update()

                        for i in range(keyframe_len-1):
                            kp0=rigify_kps[i]
                            kp1=rigify_kps[i+1]
                            x0=int(kp0.co[0])
                            x1=int(kp1.co[0])
                            d = (kp1.co - kp0.co)
                            if x0 in bezier_R_dict:
                                kp0.interpolation='BEZIER'
                                kp0.handle_right_type = 'FREE'
                                bezier=bezier_R_dict[x0]
                                kp0.handle_right = kp0.co + d*bezier
                            else:
                                kp0.interpolation = 'LINEAR'
                            if x1 in bezier_L_dict:
                                kp1.handle_left_type = 'FREE'
                                bezier=bezier_L_dict[x1]
                                kp1.handle_left = kp0.co + d*bezier
                        
                        rigify_fcurve.update()



    copy_fcurve('LegIK_L',['足ＩＫ.L','つま先ＩＫ.L','足首.L','足IK親.L'],'foot.L',True)
    copy_fcurve('LegIK_R',['足ＩＫ.R','つま先ＩＫ.R','足首.R','足IK親.R'],'foot.R',True)
    copy_fcurve('shoulder.L',['肩.L','肩P.L'],'shoulder.L')
    copy_fcurve('shoulder.R',['肩.R','肩P.R'],'shoulder.R')
    copy_fcurve('upper_arm.L',['腕.L','肩P.L'],'upper_arm.L')
    copy_fcurve('upper_arm.R',['腕.L','肩P.R'],'upper_arm.R')
    copy_fcurve('spine',['グルーブ','腰'],'spine',True)

    if 'ArmTwist_L' not in rigify_dict and 'forearm.L' in rigify_dict:
        copy_fcurve('forearm.L',['腕捩.L','ひじ.L'],'forearm.L')
    if 'ArmTwist_R' not in rigify_dict and 'forearm.R' in rigify_dict:
        copy_fcurve('forearm.R',['腕捩.R','ひじ.R'],'forearm.R')
    if 'HandTwist_L' not in rigify_dict and 'hand.L' in rigify_dict:
        copy_fcurve('hand.L',['手捩.L','手首.L'],'hand.L')
    if 'HandTwist_R' not in rigify_dict and 'hand.R' in rigify_dict:
        copy_fcurve('hand.R',['手捩.R','手首.R'],'hand.R')
    
    if mmr_property.import_as_NLA_strip:
        target_track=rigify_arm.animation_data.nla_tracks.new()
        target_track.name='vmd_track'
        target_strip=target_track.strips.new(action_name,bpy.context.scene.frame_current,vmd_action)
        target_strip.blend_type = 'REPLACE'
        target_strip.use_auto_blend = False
        target_strip.extrapolation = 'NOTHING'
        target_strip.blend_in = fade_in_out
        target_strip.blend_out = fade_in_out
        target_strip.frame_start+=old_frame
        target_strip.frame_end+=old_frame

        #更改原动作混合模式为合并
        rigify_arm.animation_data.action_blend_type = 'COMBINE'
    else:
        rigify_arm.animation_data.action=vmd_action

    if debug==False:
        bpy.data.objects.remove(rigify_arm2,do_unlink=True)
        bpy.data.objects.remove(mmd_arm,do_unlink=True)
        bpy.data.scenes.remove(new_scene,do_unlink=True)
    bpy.context.view_layer.objects.active=rigify_arm
    rigify_arm.select_set(True)
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

    mmd_rigify_dict={
    '全ての親':['root'],'センター':['spine','Center'],'下半身':['spine_fk','hips'],'上半身':['spine_fk.001','spine_fk.002','chest'],'上半身2':['spine_fk.003','chest'],
    '首':['neck'],'頭':['head'],'両目':[],'左目':[],'右目':[],
    '左足':['thigh_fk.L','thigh_ik.L'],'左足ＩＫ':['thigh_fk.L','shin_fk.L','foot_ik.L'],'左つま先ＩＫ':['foot_fk.L','foot_ik.L'],'左足首':['foot_fk.L','foot_ik.L'],
    '右足':['thigh_fk.R','thigh_ik.R'],'右足ＩＫ':['thigh_fk.R','shin_fk.R','foot_ik.R'],'右つま先ＩＫ':['foot_fk.L','foot_ik.R'],'右足首':['foot_fk.L','foot_ik.R'],
    '左肩':['shoulder.L'],'左腕':['upper_arm_fk.L','upper_arm_ik.L','hand_ik.R'],'左ひじ':['forearm_fk.L','upper_arm_ik.L','hand_ik.L'],'左手首':['hand_fk.L','hand_ik.L'],
    '右肩':['shoulder.L'],'右腕':['upper_arm_fk.R','upper_arm_ik.R','hand_ik.R'],'右ひじ':['forearm_fk.R','upper_arm_ik.R','hand_ik.R'],'右手首':['hand_fk.R','hand_ik.R'],
    '左親指０':['thumb.01_master.L','thumb.01.L'],'左親指１':['thumb.01_master.L','thumb.02.L'],'左親指２':['thumb.01_master.L','thumb.03.L'],
    '左人指１':['f_index.01_master.L','f_index.01.L'],'左人指２':['f_index.01_master.L','f_index.02.L'],'左人指３':['f_index.01_master.L','f_index.03.L'],
    '左中指１':['f_middle.01_master.L','f_middle.01.L'],'左中指２':['f_middle.01_master.L','f_middle.02.L'],'左中指３':['f_middle.01_master.L','f_middle.03.L'],
    '左薬指１':['f_ring.01_master.L','f_ring.01.L'],'左薬指２':['f_ring.01_master.L','f_ring.02.L'],'左薬指３':['f_ring.01_master.L','f_ring.03.L'],
    '左小指１':['f_pinky.01_master.L','f_pinky.01.L'],'左小指２':['f_pinky.01_master.L','f_pinky.02.L'],'左小指３':['f_pinky.01_master.L','f_pinky.03.L'],
    '右親指０':['thumb.01_master.R','thumb.01.R'],'右親指１':['thumb.01_master.R','thumb.02.R'],'右親指２':['thumb.01_master.R','thumb.03.R'],
    '右人指１':['f_index.01_master.R','f_index.01.R'],'右人指２':['f_index.01_master.R','f_index.02.R'],'右人指３':['f_index.01_master.R','f_index.03.R'],
    '右中指１':['f_middle.01_master.L','f_middle.01.R'],'右中指２':['f_middle.01_master.L','f_middle.02.R'],'右中指３':['f_middle.01_master.L','f_middle.03.R'],
    '右薬指１':['f_ring.01_master.R','f_ring.01.R'],'右薬指２':['f_ring.01_master.R','f_ring.02.R'],'右薬指３':['f_ring.01_master.R','f_ring.03.R'],
    '右小指１':['f_pinky.01_master.R','f_pinky.01.R'],'右小指２':['f_pinky.01_master.R','f_pinky.02.R'],'右小指３':['f_pinky.01_master.R','f_pinky.03.R'],
    }



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
    mmd_arm2.select_set(True)
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

    mmd_blender_dict={}

    for bone in mmd_arm2.pose.bones:
        name_j=bone.mmd_bone.name_j
        if name_j in mmd_rigify_dict:
            bone.bone.select=True
            mmd_blender_dict[name_j]=bone.name
        else:
            bone.bone.select=False

    bpy.ops.nla.bake(frame_start=int(start_frame1), frame_end=int(end_frame1), only_selected=True, visual_keying=True,clear_constraints=True, bake_types={'POSE'})
    bpy.ops.object.mode_set(mode = 'OBJECT')

    mmd_action=mmd_arm2.animation_data.action
    fcurves1=rigify_action.fcurves
    fcurves2=mmd_action.fcurves

    '''def combine_twist_fcurve(elbow_bone,twist_bone):
        keyframe_dice={}
        elbow_path=elbow_bone.path_from_id('rotation_quaternion')
        twist_path=twist_bone.path_from_id('rotation_quaternion')
        
        fcurve=fcurves1.find(elbow_path,index=0)
        elbow_w=fcurve.keyframe_points
        fcurve=fcurves1.find(elbow_path,index=1)
        elbow_x=fcurve.keyframe_points
        fcurve=fcurves1.find(elbow_path,index=2)
        elbow_y=fcurve.keyframe_points
        fcurve=fcurves1.find(elbow_path,index=3)
        elbow_z=fcurve.keyframe_points

        fcurve=fcurves2.find(elbow_path,index=0)
        twist_w=fcurve.keyframe_points
        fcurve=fcurves2.find(elbow_path,index=1)
        twist_x=fcurve.keyframe_points
        fcurve=fcurves2.find(elbow_path,index=2)
        twist_y=fcurve.keyframe_points
        fcurve=fcurves2.find(elbow_path,index=3)
        twist_z=fcurve.keyframe_points

        for i in range(1,len(elbow_w)-1):'''


    def clean_fcurve(blender_name,keyframe_bone_list):

        mmd_bone=mmd_arm2.pose.bones[blender_name]

        keyframe_data_list=['co','interpolation','handle_left','handle_left_type','handle_right','handle_right_type']

        keyframe_set=set()
        bezier_L_dict={}
        bezier_R_dict={}
        def gather_data(bone_name,attr_name):
            bone=rigify_arm.pose.bones[bone_name]
            path=bone.path_from_id(attr_name)
            fcurve=fcurves1.find(path,index=0)
            if fcurve:
                keyframe_points=fcurve.keyframe_points
                #先录入第一个关键帧的数据
                kp0=keyframe_points[0]
                x0=int(kp0.co[0])
                keyframe_set.add(x0)
                #反向计算mmd控制柄
                for i in range(len(keyframe_points)-1):
                    kp0=keyframe_points[i]
                    kp1=keyframe_points[i+1]
                    x0=int(kp0.co[0])
                    x1=int(kp1.co[0])
                    keyframe_set.add(x1)
                    if kp0.interpolation=='BEZIER':
                        d = (kp1.co - kp0.co)
                        #防止除零
                        if d[1]!=0:
                            if x0 not in bezier_R_dict:
                                bezier_R=kp0.handle_right-kp0.co
                                bezier_R[0]/=d[0]
                                bezier_R[1]/=d[1]
                                bezier_R_dict[x0]=bezier_R

                            if x1 not in bezier_L_dict:
                                bezier_L=kp1.handle_left-kp0.co
                                bezier_L[0]/=d[0]
                                bezier_L[1]/=d[1]
                                bezier_L_dict[x1]=bezier_L

        for name in keyframe_bone_list:
            gather_data(name,'location')
            gather_data(name,'rotation_quaternion')

        #清除烘焙的缩放曲线
        path=mmd_bone.path_from_id('scale')
        for index in range(3):

            fcurve=fcurves2.find(path,index=index)
            if fcurve:
                fcurves2.remove(fcurve)

        
        keyframe_points_set=set()
        path=mmd_bone.path_from_id('rotation_quaternion')
        for index in range(4):

            fcurve=fcurves2.find(path,index=index)
            if fcurve:
                keyframe_points=fcurve.keyframe_points
                keyframe_points_set.add(keyframe_points)

        path=mmd_bone.path_from_id('location')
        for index in range(3):

            fcurve=fcurves2.find(path,index=index)
            if fcurve:
                keyframe_points=fcurve.keyframe_points
                keyframe_points_set.add(keyframe_points)

        for keyframe_points in keyframe_points_set:
            i=0
            keyframe_points_len=len(keyframe_points)
            while i<keyframe_points_len:
                keyframe=keyframe_points[i]
                if int(keyframe.co[0]) not in keyframe_set:
                    keyframe_points.remove(keyframe,fast=True)
                    keyframe_points_len-=1
                else:
                    i+=1

            fcurve.update()

            for i in range(keyframe_points_len-1):
                kp0=keyframe_points[i]
                kp1=keyframe_points[i+1]
                x0=int(kp0.co[0])
                x1=int(kp1.co[0])
                d = (kp1.co - kp0.co)
                if x0 in bezier_R_dict:
                    kp0.handle_right_type = 'FREE'
                    kp0.interpolation = 'BEZIER'
                    bezier=bezier_R_dict[x0]
                    kp0.handle_right = kp0.co + bezier*d
                else:
                    kp0.interpolation = 'LINEAR'
                if x1 in bezier_L_dict:
                    kp1.handle_left_type = 'FREE'
                    bezier=bezier_L_dict[x1]
                    kp1.handle_left = kp0.co + bezier*d


    if OT.only_contain_keyframe:
        for name_j,blender_name in mmd_blender_dict.items():
            print(name_j)
            keyframe_bone_list=mmd_rigify_dict[name_j]
            clean_fcurve(blender_name,keyframe_bone_list)

    bpy.ops.mmd_tools.export_vmd(filepath=vmd_path,scale=scale, use_pose_mode=use_pose_mode,use_frame_range=False)
    bpy.data.objects.remove(mmd_arm2,do_unlink=True)

    return(True)

class OT_Import_Mixamo(Operator, bpy_extras.io_utils.ImportHelper):
    bl_idname = "mmr.import_mixamo" 
    bl_label = "Import mixamo action"
    filter_glob: bpy.props.StringProperty( 
    default='*.fbx;*.bvh;', 
    options={'HIDDEN'} 
    )

    first_frame_as_rest_pose: bpy.props.BoolProperty(
        name="First Frame As Rest Pose",
        description="First Frame As Rest Pose",
        default=False
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
    only_contain_keyframe: bpy.props.BoolProperty(
        name="Only Contain Keyframe",
        description="Only Contain Keyframe",
        default=False
    )

    def execute(self,context):
        export_vmd(self,context)
        return{"FINISHED"}

Class_list=[OT_Import_Mixamo,OT_Import_Vmd,OT_Export_Vmd]