from ..base import MMRPanelBase
from .. import bl_info # 从父级 __init__.py 导入 bl_info

class ExtraPanel(MMRPanelBase):
    bl_idname = "MMR_PT_Extra"
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

class AboutPanel(MMRPanelBase):
    bl_idname = "MMR_PT_About"
    bl_label = "About"  # 菜单名字
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        layout.label(text="MikuMikuRig")
        # 直接使用导入的 bl_info
        layout.label(text="版本号:" + str(bl_info["version"]))
        layout.label(text="作者:小威廉伯爵")
        layout.prop(context.scene.mmr_property, 'debug', text="Debug")

CLASS_LIST = [ExtraPanel, AboutPanel]