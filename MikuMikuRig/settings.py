# pyright: reportInvalidTypeForm=false
import bpy
from bpy.props import BoolProperty, IntProperty, FloatProperty, EnumProperty, PointerProperty

class MMRProperty(bpy.types.PropertyGroup):
    bent_IK_bone: BoolProperty(default=False, description="弯曲IK骨骼")
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

def register():
    bpy.utils.register_class(MMRProperty)
    bpy.types.Scene.mmr_property = PointerProperty(type=MMRProperty)

def unregister():
    del bpy.types.Scene.mmr_property
    bpy.utils.unregister_class(MMRProperty)