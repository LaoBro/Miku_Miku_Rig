bl_info = {
    "name": "MikuMikuRig", #插件名字
    "author": "William", #作者名字
    "version": (0, 3, 8,1), #插件版本
    "blender": (2, 92, 0), #blender版本
    "location": "3DView > Tools", #插件所在位置
    "description": "自动为MMD模型生成rigify控制器", #描述
    #"warning": "不稳定", #警告
    "support": 'OFFICIAL', #支持??
    "category": "Rigging", #分类
}
import bpy
import bpy_extras
from . import MMR_Core
def MMR_property():
    scene=bpy.types.Scene
    scene.limit_mod=bpy.props.BoolProperty(default=True,description="限制模式")
    scene.wrist_follow=bpy.props.BoolProperty(default=True,description="手腕跟随上半身")
    scene.wrist_rotation_follow=bpy.props.BoolProperty(default=True,description="手腕旋转跟随手臂")
    scene.auto_fix_axial=bpy.props.BoolProperty(default=False,description="自动修正骨骼轴向")
    scene.auto_rest_pose=bpy.props.BoolProperty(default=False,description="自动导入初始姿势")
    scene.relative_mod=bpy.props.BoolProperty(default=True,description="相对模式")
    scene.auto_shoulder=bpy.props.BoolProperty(default=False,description="肩膀联动")
    scene.auto_upperbody=bpy.props.BoolProperty(default=False,description="上半身联动")
    scene.auto_lowerbody=bpy.props.BoolProperty(default=False,description="下半身联动")
    scene.solid_rig=bpy.props.BoolProperty(default=False,description="实心控制器")
    scene.pole_target=bpy.props.BoolProperty(default=False,description="极向目标")
    scene.min_ik_loop=bpy.props.IntProperty(default=10,description="最小IK迭代次数",min=1)
    scene.lock_location=bpy.props.BoolProperty(default=False,description="锁定位置")
    scene.fade_in_out=bpy.props.IntProperty(default=20,description="淡入淡出长度",min=0)
    scene.action_scale=bpy.props.FloatProperty(default=1,description="动作缩放",min=0)
    scene.auto_action_scale=bpy.props.BoolProperty(default=True,description="自动动作缩放")
    scene.ik_fk_hand=bpy.props.IntProperty(default=3,description="手部IKFK",min=1,max=3)
    scene.ik_fk_leg=bpy.props.IntProperty(default=3,description="腿部IKFK",min=1,max=3)
    scene.subdivide=bpy.props.IntProperty(default=0,description="细分级别",min=0,max=5)
    scene.cloth_convert_mod=bpy.props.IntProperty(default=1,description="布料转换模式",min=1,max=3)

class Mmr_Panel_Base(object):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "MMR"
    bl_context = "objectmode"
    #bl_options = {'DEFAULT_CLOSED'} # HIDE_HEADER 为隐藏菜单

class PT_MikuMikuRig_1(Mmr_Panel_Base,bpy.types.Panel):
    bl_idname="mmr.mmr_panel_1"
    bl_label = "一键生成控制器" #菜单名字

    def draw(self, context):
        prefs = context.preferences
        view= prefs.view
        scene=context.scene
        layout = self.layout
        layout.label(text="选中MMD骨骼后点击按钮")
        layout.operator("mmr.generate_rig",text="生成控制器",icon="CUBE")
        layout.operator("mmr.fix_axial",text="修正骨骼轴向",icon="CUBE")
        #layout.prop(scene,'relative_mod',text="相对模式（无视轴向）")
        #layout.prop(scene,'auto_fix_axial',text="创建控制器前修正轴向")
        #layout.prop(scene,'limit_mod',text="限制模式(锁定某些骨骼)")
        layout.prop(scene,'wrist_follow',text="手腕跟随上半身")
        layout.prop(scene,'wrist_rotation_follow',text="手腕旋转跟随手臂")
        layout.prop(scene,'auto_shoulder',text="肩膀联动")
        #layout.prop(scene,'auto_upperbody',text="上半身联动")
        #layout.prop(scene,'auto_lowerbody',text="下半身联动")
        layout.prop(scene,'solid_rig',text="实心控制器")
        layout.prop(scene,'pole_target',text="使用极向目标")

class PT_MikuMikuRig_2(Mmr_Panel_Base,bpy.types.Panel):
    bl_idname="mmr.mmr_panel_2"
    bl_label = "修复MMD骨骼错位" #菜单名字

    def draw(self, context):
        prefs = context.preferences
        view= prefs.view
        scene=context.scene
        layout = self.layout
        layout.prop(scene,'min_ik_loop',text="最低IK迭代次数")
        layout.operator("mmr.set_min_ik_loop",text="设置最低IK迭代次数",icon="CUBE")

class PT_MikuMikuRig_3(Mmr_Panel_Base,bpy.types.Panel):
    bl_idname="mmr.mmr_panel_3"
    bl_label = "一键导入动画" #菜单名字

    def draw(self, context):
        prefs = context.preferences
        view= prefs.view
        scene=context.scene
        layout = self.layout
        layout.label(text="选中Rigify控制器后点击按钮")
        layout.label(text="一键导入动画",icon="BLENDER")
        layout.prop(scene,'fade_in_out',text="淡入淡出")
        layout.prop(scene,'action_scale',text="动作缩放")
        layout.prop(scene,'auto_action_scale',text="自动mixamo动作缩放")
        layout.prop(scene,'lock_location',text="锁定mixamo动画位置")
        layout.label(text="使用IK还是FK重定向mixamo动画")
        layout.label(text="1=不定义 2=IK 3=FK")
        row=layout.row()
        row.prop(scene,'ik_fk_hand',text="手部")
        row.prop(scene,'ik_fk_leg',text="腿部")
        layout.operator("mmr.import_mixamo",text="导入mixamo动画为NLA片段",icon="CUBE")
        layout.operator("mmr.import_vmd",text="导入vmd动画为NLA片段",icon="CUBE")

class PT_MikuMikuRig_4(Mmr_Panel_Base,bpy.types.Panel):
    bl_idname="mmr.mmr_panel_4"
    bl_label = "一键布料(测试功能)" #菜单名字

    def draw(self, context):
        prefs = context.preferences
        view= prefs.view
        scene=context.scene
        layout = self.layout
        layout.label(text="选中一块MMD刚体和网格后点击按钮")
        layout.prop(scene,'subdivide',text="细分等级")
        layout.prop(scene,'cloth_convert_mod',text="布料转换模式")
        layout.label(text="1=自动检测 2=骨骼约束 3=表面形变")
        layout.operator("mmr.convert_rigid_body_to_cloth",text="把刚体转为布料",icon="CUBE")

class OT_Generate_Rig(bpy.types.Operator):
    bl_idname = "mmr.generate_rig" # python 提示
    bl_label = "Interface"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self,context):
        MMR_Class=MMR_Core.MMR(context)
        MMR_Class.RIG()
        return{"FINISHED"}

class OT_Load_Pose(bpy.types.Operator):
    bl_idname = "mmr.load_pose" # python 提示
    bl_label = "Interface"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self,context):
        MMR_Class=MMR_Core.MMR(context)
        MMR_Class.load_pose()
        return{"FINISHED"}

class OT_Fix_Axial(bpy.types.Operator):
    bl_idname = "mmr.fix_axial" # python 提示
    bl_label = "Interface"
    bl_options = {'REGISTER', 'UNDO'}
    def execute(self,context):
        MMR_Class=MMR_Core.MMR(context)
        if MMR_Class.check_arm():
            bpy.ops.object.mode_set(mode = 'EDIT')
            MMR_Class.fix_axial()
            bpy.ops.object.mode_set(mode = 'OBJECT')
        else:
            return {"CANCELLED"}
        return{"FINISHED"}

class OT_Set_Min_IK_Loop(bpy.types.Operator):
    bl_idname = "mmr.set_min_ik_loop" # python 提示
    bl_label = "Interface"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self,context):
        MMR_Class=MMR_Core.MMR(context)
        MMR_Class.set_min_ik_loop(context.scene.min_ik_loop)
        return{"FINISHED"}

class OT_Import_Mixamo(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):
    bl_idname = "mmr.import_mixamo" 
    bl_label = "Import mixamo action"
    filter_glob: bpy.props.StringProperty( 
    default='*.fbx;', 
    options={'HIDDEN'} 
    )
    def execute(self,context):
        scene=context.scene
        MMR_Class=MMR_Core.MMR(context)
        MMR_Class.retarget_mixmao(self.filepath,context.view_layer.objects.active,scene.lock_location,scene.fade_in_out,scene.action_scale,scene.auto_action_scale,scene.ik_fk_hand,scene.ik_fk_leg)
        return{"FINISHED"}

class OT_Import_Vmd(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):
    bl_idname = "mmr.import_vmd" 
    bl_label = "Import vmd action"
    filter_glob: bpy.props.StringProperty( 
    default='*.vmd;', 
    options={'HIDDEN'} 
    )
    def execute(self,context):
        MMR_Class=MMR_Core.MMR(context)
        MMR_Class.load_vmd(self.filepath,context.view_layer.objects.active,context.scene.fade_in_out,context.scene.action_scale)
        return{"FINISHED"}

class OT_Convert_Rigid_Body_To_Cloth(bpy.types.Operator):
    bl_idname = "mmr.convert_rigid_body_to_cloth" # python 提示
    bl_label = "Interface"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self,context):
        MMR_Class=MMR_Core.MMR(context)
        MMR_Class.convert_rigid_body_to_cloth(context.scene.subdivide,context.scene.cloth_convert_mod)
        return{"FINISHED"}


def alert_error(title,message):
    def draw(self,context):
        self.layout.label(text=str(message))
    bpy.context.window_manager.popup_menu(draw,title=title,icon='ERROR')

class_list=[OT_Generate_Rig,PT_MikuMikuRig_1,PT_MikuMikuRig_2,PT_MikuMikuRig_3,PT_MikuMikuRig_4,OT_Fix_Axial,OT_Load_Pose,OT_Set_Min_IK_Loop,OT_Import_Mixamo,OT_Import_Vmd,OT_Convert_Rigid_Body_To_Cloth]
def register(): #启用插件时候执行
    for Class in class_list:
        bpy.utils.register_class(Class)
    MMR_property()
    print('zc')

def unregister(): #关闭插件时候执行
    for Class in class_list:
        bpy.utils.unregister_class(Class)
    print('zx')





if __name__ == "__main__":
    register()