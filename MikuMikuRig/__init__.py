# pyright: reportInvalidTypeForm=false
bl_info = {
    "name": "MikuMikuRig",  # 插件名字
    "author": "William",  # 作者名字
    "version": (0, 5, 7, 0),  # 插件版本
    "blender": (4, 0, 0),  # 建议更新到较新的Blender版本，例如4.0
    "location": "3DView > Tools",  # 插件所在位置
    "description": "快速为各种人形模型生成rigify控制器,一键套mixamo动作",  # 描述
    "support": 'COMMUNITY',  # 支持等级（社区支持）
    "category": "Rigging",  # 分类
}

import bpy
from . import translation
from . import mmr_operators
from bpy.props import BoolProperty, IntProperty, FloatProperty, EnumProperty, PointerProperty


class MMRProperty(bpy.types.PropertyGroup):
    upper_body_controller: BoolProperty(default=True, description="上半身控制器")
    wrist_rotation_follow: BoolProperty(default=False, description="手腕旋转跟随手臂")
    bent_IK_bone: BoolProperty(default=False, description="弯曲IK骨骼")
    auto_shoulder: BoolProperty(default=False, description="肩膀联动")
    solid_rig: BoolProperty(default=False, description="实心控制器")
    pole_target: BoolProperty(default=False, description="极向目标")
    min_ik_loop: IntProperty(default=10, description="最小IK迭代次数", min=1)
    lock_location: BoolProperty(default=False, description="锁定动画位置")
    fade_in_out: IntProperty(default=0, description="淡入淡出长度", min=0)
    action_scale: FloatProperty(default=1, description="动作缩放", min=0)
    auto_action_scale: BoolProperty(default=True, description="自动动作缩放")
    subdivide: IntProperty(default=0, description="细分级别", min=0, max=5)
    auto_select_mesh: BoolProperty(default=True, description="自动选择模型")
    auto_select_rigid_body: BoolProperty(default=True, description="自动选择刚体")
    extend_ribbon: BoolProperty(default=True, description="延展飘带区域")
    debug: BoolProperty(default=False, description="debug")
    rig_preset_name: EnumProperty(
        items=mmr_operators.preset.get_rig_preset_item,
        description=('Choose the preset you want to use'),
    )
    retarget_preset_name: EnumProperty(
        items=mmr_operators.preset.get_retarget_preset_item,
        description=('Choose the preset you want to use'),
    )

    IK_FK_ITEMS = [
        ('None', 'None', ''),
        ('IK', 'IK', ''),
        ('FK', "FK", ''),
    ]

    IKFK_arm: EnumProperty(
        items=IK_FK_ITEMS,
        description=('retarget mod'),
        default='FK',
    )
    IKFK_leg: EnumProperty(
        items=IK_FK_ITEMS,
        description=('retarget mod'),
        default='IK',
    )
    cloth_convert_mod: EnumProperty(
        items=[
            ('Auto', 'Auto', ''),
            ('Bone Constrain', 'Bone Constrain', ''),
            ('Surface Deform', 'Surface Deform', '')
        ],
        description=('retarget mod'),
        default = 'Auto',
    )
    quick_assign_index: IntProperty(default=1,description="快速指定序号",min=1)
    quick_assign_mod: BoolProperty(default=False,description="快速指定模式")
    extra_options1: BoolProperty(default=False,description="高级选项")
    extra_options2: BoolProperty(default=False,description="高级选项")
    mass_multiply_rate: FloatProperty(default=12.5,description="刚体质量倍率",min=0)
    import_as_NLA_strip: BoolProperty(
        name='Import as NLA strip',
        description="Import as NLA strip",
        default=True
    )


class MMRPanelBase(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "MMR"
    # bl_context = "objectmode" # bl_context 已弃用，通常可移除
    # bl_options = {'DEFAULT_CLOSED'} # HIDE_HEADER 为隐藏菜单

"""已弃用
class MikuMikuRigPanel1(MMRPanelBase):
    bl_idname = "MMR_PT_panel_1"
    bl_label = "Auto MMD rig"  # 菜单名字

    def draw(self, context):
        scene = context.scene
        mmr_property = scene.mmr_property
        layout = self.layout
        layout.label(text="Select MMD armature then press the button")
        layout.operator("mmr.generate_rig", text="Generate MMD rig")
        layout.prop(mmr_property, 'bent_IK_bone', text="Bent IK bone")
        layout.prop(mmr_property, 'wrist_rotation_follow', text="Wrist rotation follow arm")
        layout.prop(mmr_property, 'auto_shoulder', text="Shoulder IK")
        layout.prop(mmr_property, 'solid_rig', text="Replace the controller")
        layout.prop(mmr_property, 'pole_target', text="Use pole target")
"""

class MikuMikuRigPanel2(MMRPanelBase):
    bl_idname = "MMR_PT_panel_2"
    bl_label = "Extra"  # 菜单名字

    def draw(self, context):
        scene = context.scene
        mmr_property = scene.mmr_property
        layout = self.layout
        layout.prop(mmr_property, 'min_ik_loop', text="Min IK loop")
        layout.operator("mmr.set_min_ik_loop", text="Set min IK loop")
        layout.prop(mmr_property, 'mass_multiply_rate', text="Multiply Rate")
        layout.operator("mmr.rigid_body_mass_multiply", text="Rigid Body Mass Multiply")
        layout.operator("mmr.hide_skirt", text="Hide Skirt By Rigid Body")
        layout.operator("mmr.decorate_mmd_arm", text="Decorate MMD Arm")


"""已弃用
class MikuMikuRigPanel3(MMRPanelBase):
    bl_idname = "MMR_PT_panel_3"
    bl_label = "Auto animation import"  # 菜单名

    def draw(self, context):
        scene = context.scene
        mmr_property = scene.mmr_property
        layout = self.layout
        layout.label(text="Select rigify controller then press the button")
        layout.prop(mmr_property, 'fade_in_out', text="Fade in out")
        layout.prop(mmr_property, 'action_scale', text="Animation scale")
        layout.prop(mmr_property, 'auto_action_scale', text="Auto mixamo animation scale", toggle=True)
        layout.prop(mmr_property, 'lock_location', text="Lock mixamo animation location", toggle=True)
        row = layout.row()
        row.label(text='Arm:', translate=False)
        row.prop(mmr_property, 'IKFK_arm', expand=True)
        row = layout.row()
        row.label(text='Leg:', translate=False)
        row.prop(mmr_property, 'IKFK_leg', expand=True)
        layout.operator("mmr.import_mixamo", text="Import mixamo animation as NLA")
        layout.operator("mmr.import_vmd", text="Import VMD animation as NLA")
        layout.operator("mmr.export_vmd", text="Bake and export VMD animation")
"""

class MikuMikuRigPanel4(MMRPanelBase):
    bl_idname = "MMR_PT_panel_4"
    bl_label = "Auto cloth(experimental)"  # 菜单名字

    def draw(self, context):
        scene = context.scene
        mmr_property = scene.mmr_property
        layout = self.layout
        layout.label(text="Select mesh and rigidbody then press the button")
        layout.operator("mmr.convert_rigid_body_to_cloth", text="Convert rigid body to cloth")
        layout.prop(mmr_property, 'subdivide', text="Subdivide level")
        layout.label(text='Convert Mod:')
        layout.prop(mmr_property, 'cloth_convert_mod', expand=True)  # props_enum 已弃用
        layout.label(text='Options:')
        layout.prop(mmr_property, 'auto_select_mesh', text="Auto select mesh", toggle=True)
        layout.prop(mmr_property, 'auto_select_rigid_body', text="Auto select rigid body", toggle=True)
        layout.prop(mmr_property, 'extend_ribbon', text="Extend ribbon area", toggle=True)
        layout.label(text="This featur is developed in cooperation with")
        layout.label(text="UuuNyaa")


class MikuMikuRigPanel5(MMRPanelBase):
    bl_idname = "MMR_PT_panel_5"
    bl_label = "About"  # 菜单名字
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        # scene = context.scene # 未使用
        # mmr_property = scene.mmr_property # 未使用
        layout = self.layout
        layout.label(text="MikuMikuRig")
        layout.label(text="版本号:" + str(bl_info["version"]))
        layout.label(text="作者:小威廉伯爵")
        layout.prop(context.scene.mmr_property, 'debug', text="Debug")


def alert_error(title, message):
    def draw(self, context):
        self.layout.label(text=str(message))
    bpy.context.window_manager.popup_menu(draw, title=title, icon='ERROR')


# 按注册顺序列出所有类
classes_to_register = (
    MikuMikuRigPanel2,
    MikuMikuRigPanel4,
    MikuMikuRigPanel5,
)

# 需要调用其 register/unregister 方法的模块列表
modules_to_register = (
    mmr_operators,
)


def register():  # 启用插件时候执行
    # 注册 PropertyGroup
    bpy.utils.register_class(MMRProperty)
    # 将其分配给 Scene 类型
    bpy.types.Scene.mmr_property = PointerProperty(type=MMRProperty)

    # 注册此文件中的其他类 (例如 Panels)
    # 从 classes_to_register 中排除 MMR_property，因为它已经注册
    for cls in classes_to_register:
        # MMRProperty 已在前面注册，这里处理其他类
        if cls is not MMRProperty:
            bpy.utils.register_class(cls)

    # 调用其他模块的 register 函数
    for module in modules_to_register:
        if hasattr(module, "register"):
            module.register()

    translation.register_module()
    print(f"Registered: {bl_info['name']} version {bl_info['version']}")


def unregister():  # 关闭插件时候执行
    translation.unregister_module()

    # 以相反的顺序调用其他模块的 unregister 函数
    for module in reversed(modules_to_register):
        if hasattr(module, "unregister"):
            module.unregister()

    # 以相反的顺序反注册此文件中的类
    for cls in reversed(classes_to_register):
        # MMRProperty 单独处理
        if cls is not MMRProperty:
            bpy.utils.unregister_class(cls)

    # 删除 Scene 属性并反注册 PropertyGroup
    del bpy.types.Scene.mmr_property
    bpy.utils.unregister_class(MMRProperty)
    print(f"Unregistered: {bl_info['name']}")
