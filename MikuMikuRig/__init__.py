bl_info = {
    "name": "MikuMikuRig", #插件名字
    "author": "William", #作者名字
    "version": (0, 3, 8,6), #插件版本
    "blender": (2, 80, 0), #需要的*最低* blender 版本
    "location": "3DView > Tools", #插件所在位置
    "description": "自动为MMD模型生成rigify控制器", #描述
    #"warning": "不稳定", #警告
    "support": 'COMMUNITY', #支持等级（社区支持）
    "category": "Rigging", #分类
}
import bpy
import bpy_extras
from bpy.types import Operator
from . import MMR_Core
from . import translation

class MMR_property(bpy.types.PropertyGroup):
    upper_body_controller:bpy.props.BoolProperty(default=True,description="上半身控制器")
    wrist_rotation_follow:bpy.props.BoolProperty(default=False,description="手腕旋转跟随手臂")
    auto_shoulder:bpy.props.BoolProperty(default=False,description="肩膀联动")
    solid_rig:bpy.props.BoolProperty(default=False,description="实心控制器")
    pole_target:bpy.props.BoolProperty(default=False,description="极向目标")
    min_ik_loop:bpy.props.IntProperty(default=10,description="最小IK迭代次数",min=1)
    lock_location:bpy.props.BoolProperty(default=False,description="锁定动画位置")
    fade_in_out:bpy.props.IntProperty(default=0,description="淡入淡出长度",min=0)
    action_scale:bpy.props.FloatProperty(default=1,description="动作缩放",min=0)
    auto_action_scale:bpy.props.BoolProperty(default=True,description="自动动作缩放")
    ik_fk_hand:bpy.props.IntProperty(default=3,description="手部IKFK",min=1,max=3)
    ik_fk_leg:bpy.props.IntProperty(default=3,description="腿部IKFK",min=1,max=3)
    subdivide:bpy.props.IntProperty(default=0,description="细分级别",min=0,max=5)
    cloth_convert_mod:bpy.props.IntProperty(default=1,description="布料转换模式",min=1,max=3)
    auto_select_mesh:bpy.props.BoolProperty(default=True,description="自动选择模型")
    auto_select_rigid_body:bpy.props.BoolProperty(default=True,description="自动选择刚体")
    extend_ribbon:bpy.props.BoolProperty(default=True,description="延展飘带区域")
    debug:bpy.props.BoolProperty(default=False,description="debug")

class Mmr_Panel_Base(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "MMR"
    bl_context = "objectmode"
    #bl_options = {'DEFAULT_CLOSED'} # HIDE_HEADER 为隐藏菜单

class PT_MikuMikuRig_1(Mmr_Panel_Base):
    bl_idname="mmr.mmr_panel_1"
    bl_label = "Auto MMD rig" #菜单名字

    def draw(self, context):
        prefs = context.preferences
        view= prefs.view
        scene=context.scene
        mmr_property=scene.mmr_property
        layout = self.layout
        layout.label(text="Select MMD armature then press the button")
        layout.operator("mmr.generate_rig",text="Generate MMD rig",icon="CUBE")
        layout.prop(mmr_property,'upper_body_controller',text="Upper body controller")
        layout.prop(mmr_property,'wrist_rotation_follow',text="Wrist rotation follow arm")
        layout.prop(mmr_property,'auto_shoulder',text="Shoulder IK")
        layout.prop(mmr_property,'solid_rig',text="Replace the controller")
        layout.prop(mmr_property,'pole_target',text="Use pole target")
        layout.prop(mmr_property,'debug',text="Debug")

class PT_MikuMikuRig_2(Mmr_Panel_Base):
    bl_idname="mmr.mmr_panel_2"
    bl_label = "Fixed MMD bone dislocation" #菜单名字

    def draw(self, context):
        prefs = context.preferences
        view= prefs.view
        scene=context.scene
        mmr_property=scene.mmr_property
        layout = self.layout
        layout.prop(mmr_property,'min_ik_loop',text="Min IK loop")
        layout.operator("mmr.set_min_ik_loop",text="Set min IK loop",icon="CUBE")
        layout.operator("mmr.fix_axial",text="Fix axial",icon="CUBE")

class PT_MikuMikuRig_3(Mmr_Panel_Base):
    bl_idname="mmr.mmr_panel_3"
    bl_label = "Auto animation import" #菜单名字

    def draw(self, context):
        prefs = context.preferences
        view= prefs.view
        scene=context.scene
        mmr_property=scene.mmr_property
        layout = self.layout
        layout.label(text="Select rigify controller then press the button")
        layout.prop(mmr_property,'fade_in_out',text="Fade in out")
        layout.prop(mmr_property,'action_scale',text="Animation scale")
        layout.prop(mmr_property,'auto_action_scale',text="Auto mixamo animation scale")
        layout.prop(mmr_property,'lock_location',text="Lock mixamo animation location")
        row=layout.row()
        row.prop(mmr_property,'ik_fk_hand',text="Arm IK-FK")
        row.prop(mmr_property,'ik_fk_leg',text="Leg IK-FK")
        layout.label(text="1=Undefined 2=IK 3=FK")
        layout.operator("mmr.import_mixamo",text="Import mixamo animation as NLA",icon="CUBE")
        layout.operator("mmr.import_vmd",text="Import VMD animation as NLA",icon="CUBE")
        layout.operator("mmr.export_vmd",text="Bake and export VMD animation",icon="CUBE")

class PT_MikuMikuRig_4(Mmr_Panel_Base):
    bl_idname="mmr.mmr_panel_4"
    bl_label = "Auto cloth(experimental)" #菜单名字

    def draw(self, context):
        prefs = context.preferences
        view= prefs.view
        scene=context.scene
        mmr_property=scene.mmr_property
        layout = self.layout
        layout.label(text="Select mesh and rigidbody then press the button")
        layout.prop(mmr_property,'subdivide',text="Subdivide level")
        layout.prop(mmr_property,'cloth_convert_mod',text="Cloth convert mod")
        layout.label(text="1=Auto 2=Bone constrain 3=Surface deform")
        layout.prop(mmr_property,'auto_select_mesh',text="Auto select mesh")
        layout.prop(mmr_property,'auto_select_rigid_body',text="Auto select rigid body")
        layout.prop(mmr_property,'extend_ribbon',text="Extend ribbon area")
        layout.operator("mmr.convert_rigid_body_to_cloth",text="Convert rigid body to cloth",icon="CUBE")
        layout.label(text="This featur is developed in cooperation with")
        layout.label(text="UuuNyaa")

class OT_Generate_Rig(Operator):
    bl_idname = "mmr.generate_rig" # python 提示
    bl_label = "Interface"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self,context):
        scene=context.scene
        mmr_property=scene.mmr_property
        MMR_Class=MMR_Core.MMR(context)
        MMR_Class.RIG()
        del MMR_Class
        return{"FINISHED"}

class OT_Load_Pose(Operator):
    bl_idname = "mmr.load_pose" # python 提示
    bl_label = "Interface"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self,context):
        scene=context.scene
        mmr_property=scene.mmr_property
        MMR_Class=MMR_Core.MMR(context)
        MMR_Class.load_pose()
        del MMR_Class
        return{"FINISHED"}

class OT_Fix_Axial(Operator):
    bl_idname = "mmr.fix_axial" # python 提示
    bl_label = "Interface"
    bl_options = {'REGISTER', 'UNDO'}
    def execute(self,context):
        scene=context.scene
        mmr_property=scene.mmr_property
        MMR_Class=MMR_Core.MMR(context)
        if MMR_Class.check_arm():
            bpy.ops.object.mode_set(mode = 'EDIT')
            MMR_Class.fix_axial()
            bpy.ops.object.mode_set(mode = 'OBJECT')
            del MMR_Class
        else:
            del MMR_Class
            return {"CANCELLED"}
        return{"FINISHED"}

class OT_Set_Min_IK_Loop(Operator):
    bl_idname = "mmr.set_min_ik_loop" # python 提示
    bl_label = "Interface"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self,context):
        scene=context.scene
        mmr_property=scene.mmr_property
        MMR_Class=MMR_Core.MMR(context)
        MMR_Class.set_min_ik_loop(mmr_property.min_ik_loop)
        del MMR_Class
        return{"FINISHED"}

class OT_Import_Mixamo(Operator, bpy_extras.io_utils.ImportHelper):
    bl_idname = "mmr.import_mixamo" 
    bl_label = "Import mixamo action"
    filter_glob: bpy.props.StringProperty( 
    default='*.fbx;', 
    options={'HIDDEN'} 
    )
    def execute(self,context):
        scene=context.scene
        mmr_property=scene.mmr_property
        MMR_Class=MMR_Core.MMR(context)
        MMR_Class.retarget_mixmao(self.filepath,context.view_layer.objects.active,mmr_property.lock_location,mmr_property.fade_in_out,mmr_property.action_scale,mmr_property.auto_action_scale,mmr_property.ik_fk_hand,mmr_property.ik_fk_leg)
        del MMR_Class
        return{"FINISHED"}

class OT_Import_Vmd(Operator, bpy_extras.io_utils.ImportHelper):
    bl_idname = "mmr.import_vmd" 
    bl_label = "Import vmd action"
    filter_glob: bpy.props.StringProperty( 
    default='*.vmd;', 
    options={'HIDDEN'} 
    )
    def execute(self,context):
        scene=context.scene
        mmr_property=scene.mmr_property
        MMR_Class=MMR_Core.MMR(context)
        MMR_Class.load_vmd(self.filepath,context.view_layer.objects.active,mmr_property.fade_in_out,mmr_property.action_scale)
        del MMR_Class
        return{"FINISHED"}

class OT_Convert_Rigid_Body_To_Cloth(Operator):
    bl_idname = "mmr.convert_rigid_body_to_cloth" # python 提示
    bl_label = "Interface"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self,context):
        scene=context.scene
        mmr_property=scene.mmr_property
        MMR_Class=MMR_Core.MMR(context)
        MMR_Class.convert_rigid_body_to_cloth(mmr_property.subdivide,mmr_property.cloth_convert_mod)
        del MMR_Class
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
        scene=context.scene
        mmr_property=scene.mmr_property
        MMR_Class=MMR_Core.MMR(context)
        MMR_Class.export_vmd(self.filepath,context.view_layer.objects.active,self.scale,self.use_pose_mode,self.set_action_range,self.start_frame,self.end_frame)
        del MMR_Class
        return{"FINISHED"}


def alert_error(title,message):
    def draw(self,context):
        self.layout.label(text=str(message))
    bpy.context.window_manager.popup_menu(draw,title=title,icon='ERROR')

class_list=[OT_Generate_Rig,PT_MikuMikuRig_1,PT_MikuMikuRig_2,PT_MikuMikuRig_3,PT_MikuMikuRig_4,OT_Fix_Axial,OT_Load_Pose,OT_Set_Min_IK_Loop,OT_Import_Mixamo,OT_Import_Vmd,OT_Convert_Rigid_Body_To_Cloth,OT_Export_Vmd]
def register(): #启用插件时候执行
    bpy.utils.register_class(MMR_property)
    bpy.types.Scene.mmr_property = bpy.props.PointerProperty(type=MMR_property)
    for Class in class_list:
        bpy.utils.register_class(Class)
        
    translation.register_module()

    print('zc')

def unregister(): #关闭插件时候执行
    for Class in class_list:
        bpy.utils.unregister_class(Class)
    bpy.utils.unregister_class(MMR_property)

    translation.unregister_module()

    print('zx')





if __name__ == "__main__":
    register()