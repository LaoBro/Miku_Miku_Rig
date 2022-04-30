bl_info = {
    "name": "MikuMikuRig", #插件名字
    "author": "William", #作者名字
    "version": (0, 5, 6, 0), #插件版本
    "blender": (2, 90, 0), #需要的*最低* blender 版本
    "location": "3DView > Tools", #插件所在位置
    "description": "快速为各种人形模型生成rigify控制器,一键套mixamo动作", #描述
    "support": 'COMMUNITY', #支持等级（社区支持）
    "category": "Rigging", #分类
    #"warning": "暂不支持Blender3.0及以上版本",
}
import bpy
import bpy_extras
from bpy.types import Operator
from . import translation
from . import mmr_operators
from bpy.props import BoolProperty
from bpy.props import IntProperty
from bpy.props import FloatProperty
from bpy.props import EnumProperty

def get_preset_item(self,context):
    preset_items=[]
    for name in mmr_operators.preset.preset_name_list:
        preset_items.append((name,name,''))
    return(preset_items)

class MMR_property(bpy.types.PropertyGroup):
    upper_body_controller:BoolProperty(default=True,description="上半身控制器")
    wrist_rotation_follow:BoolProperty(default=False,description="手腕旋转跟随手臂")
    bent_IK_bone:BoolProperty(default=False,description="弯曲IK骨骼")
    auto_shoulder:BoolProperty(default=False,description="肩膀联动")
    solid_rig:BoolProperty(default=False,description="实心控制器")
    pole_target:BoolProperty(default=False,description="极向目标")
    min_ik_loop:IntProperty(default=10,description="最小IK迭代次数",min=1)
    lock_location:BoolProperty(default=False,description="锁定动画位置")
    fade_in_out:IntProperty(default=0,description="淡入淡出长度",min=0)
    action_scale:FloatProperty(default=1,description="动作缩放",min=0)
    auto_action_scale:BoolProperty(default=True,description="自动动作缩放")
    subdivide:IntProperty(default=0,description="细分级别",min=0,max=5)
    auto_select_mesh:BoolProperty(default=True,description="自动选择模型")
    auto_select_rigid_body:BoolProperty(default=True,description="自动选择刚体")
    extend_ribbon:BoolProperty(default=True,description="延展飘带区域")
    debug:BoolProperty(default=False,description="debug")
    rig_preset_name:EnumProperty(
        items=mmr_operators.preset.get_rig_preset_item,
        description=('Choose the preset you want to use'),
    )
    retarget_preset_name:EnumProperty(
        items=mmr_operators.preset.get_retarget_preset_item,
        description=('Choose the preset you want to use'),
    )
    IKFK_list=[
            ('None','None',''),
            ('IK','IK',''),
            ('FK',"FK",''),
        ]
    IKFK_arm:EnumProperty(
        items=IKFK_list,
        description=('retarget mod'),
        default = 'FK',
    )
    IKFK_leg:EnumProperty(
        items=IKFK_list,
        description=('retarget mod'),
        default = 'IK',
    )
    cloth_convert_mod:EnumProperty(
        items=[
            ('Auto','Auto',''),
            ('Bone Constrain','Bone Constrain',''),
            ('Surface Deform','Surface Deform','')
        ],
        description=('retarget mod'),
        default = 'Auto',
    )
    quick_assign_index:IntProperty(default=1,description="快速指定序号",min=1)
    quick_assign_mod:BoolProperty(default=False,description="快速指定模式")
    extra_options1:bpy.props.BoolProperty(default=False,description="高级选项")
    extra_options2:bpy.props.BoolProperty(default=False,description="高级选项")
    mass_multiply_rate:FloatProperty(default=12.5,description="刚体质量倍率",min=0)
    import_as_NLA_strip: bpy.props.BoolProperty(
        name='Import as NLA strip',
        description="Import as NLA strip",
        default=True
    )

class Mmr_Panel_Base(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "MMR"
    bl_context = "objectmode"
    #bl_options = {'DEFAULT_CLOSED'} # HIDE_HEADER 为隐藏菜单

class MikuMikuRig_1(Mmr_Panel_Base):
    bl_idname="MMR_PT_panel_1"
    bl_label = "Auto MMD rig" #菜单名字

    def draw(self, context):
        prefs = context.preferences
        view= prefs.view
        scene=context.scene
        mmr_property=scene.mmr_property
        layout = self.layout
        layout.label(text="Select MMD armature then press the button")
        layout.operator("mmr.generate_rig",text="Generate MMD rig")
        layout.prop(mmr_property,'bent_IK_bone',text="Bent IK bone")
        layout.prop(mmr_property,'wrist_rotation_follow',text="Wrist rotation follow arm")
        layout.prop(mmr_property,'auto_shoulder',text="Shoulder IK")
        layout.prop(mmr_property,'solid_rig',text="Replace the controller")
        layout.prop(mmr_property,'pole_target',text="Use pole target")

class MikuMikuRig_2(Mmr_Panel_Base):
    bl_idname="MMR_PT_panel_2"
    bl_label = "Extra" #菜单名字

    def draw(self, context):
        prefs = context.preferences
        view= prefs.view
        scene=context.scene
        mmr_property=scene.mmr_property
        layout = self.layout
        layout.prop(mmr_property,'min_ik_loop',text="Min IK loop")
        layout.operator("mmr.set_min_ik_loop",text="Set min IK loop")
        layout.prop(mmr_property,'mass_multiply_rate',text="Multiply Rate")
        layout.operator("mmr.rigid_body_mass_multiply",text="Rigid Body Mass Multiply")
        layout.operator("mmr.hide_skirt",text="Hide Skirt By Rigid Body")
        layout.operator("mmr.decorate_mmd_arm",text="Decorate MMD Arm")

class MikuMikuRig_3(Mmr_Panel_Base):
    bl_idname="MMR_PT_panel_3"
    bl_label = "Auto animation import" #菜单名

    def draw(self, context):
        scene=context.scene
        mmr_property=scene.mmr_property
        layout = self.layout
        layout.label(text="Select rigify controller then press the button")
        layout.prop(mmr_property,'fade_in_out',text="Fade in out")
        layout.prop(mmr_property,'action_scale',text="Animation scale")
        layout.prop(mmr_property,'auto_action_scale',text="Auto mixamo animation scale",toggle=True)
        layout.prop(mmr_property,'lock_location',text="Lock mixamo animation location",toggle=True)
        row=layout.row()
        row.label(text='Arm:',translate =False)
        row.prop(mmr_property, 'IKFK_arm',expand=True)
        row=layout.row()
        row.label(text='Leg:',translate =False)
        row.prop(mmr_property, 'IKFK_leg',expand=True)
        layout.operator("mmr.import_mixamo",text="Import mixamo animation as NLA")
        layout.operator("mmr.import_vmd",text="Import VMD animation as NLA")
        layout.operator("mmr.export_vmd",text="Bake and export VMD animation")

class MikuMikuRig_4(Mmr_Panel_Base):
    bl_idname="MMR_PT_panel_4"
    bl_label = "Auto cloth(experimental)" #菜单名字

    def draw(self, context):
        scene=context.scene
        mmr_property=scene.mmr_property
        layout = self.layout
        layout.label(text="Select mesh and rigidbody then press the button")
        layout.operator("mmr.convert_rigid_body_to_cloth",text="Convert rigid body to cloth")
        layout.prop(mmr_property,'subdivide',text="Subdivide level")
        layout.label(text='Convert Mod:')
        layout.props_enum(mmr_property,'cloth_convert_mod')
        layout.label(text='Options:')
        layout.prop(mmr_property,'auto_select_mesh',text="Auto select mesh",toggle=True)
        layout.prop(mmr_property,'auto_select_rigid_body',text="Auto select rigid body",toggle=True)
        layout.prop(mmr_property,'extend_ribbon',text="Extend ribbon area",toggle=True)
        layout.label(text="This featur is developed in cooperation with")
        layout.label(text="UuuNyaa")

class MikuMikuRig_5(Mmr_Panel_Base):
    bl_idname="MMR_PT_panel_5"
    bl_label = "About" #菜单名字
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        scene=context.scene
        mmr_property=scene.mmr_property
        layout = self.layout
        layout.label(text="MikuMikuRig")
        layout.label(text="版本号:"+str(bl_info["version"]))
        layout.label(text="作者:小威廉伯爵")
        layout.prop(mmr_property,'debug',text="Debug")

def alert_error(title,message):
    def draw(self,context):
        self.layout.label(text=str(message))
    bpy.context.window_manager.popup_menu(draw,title=title,icon='ERROR')

class_list=[MikuMikuRig_2,MikuMikuRig_4,MikuMikuRig_5]
Model_list=[mmr_operators]
def register(): #启用插件时候执行
    bpy.utils.register_class(MMR_property)
    bpy.types.Scene.mmr_property = bpy.props.PointerProperty(type=MMR_property)

    for Model in Model_list:
        Model.register()

    for Class in class_list:
        bpy.utils.register_class(Class)

    translation.register_module()

    print('register')

def unregister(): #关闭插件时候执行
    for Model in Model_list:
        Model.unregister()

    for Class in class_list:
        bpy.utils.unregister_class(Class)

    bpy.utils.unregister_class(MMR_property)

    translation.unregister_module()

    print('unregister')
