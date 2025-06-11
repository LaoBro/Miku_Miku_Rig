from ..base import MMRPanelBase

class AutoClothPanel(MMRPanelBase):
    bl_idname = "MMR_PT_Auto_Cloth"
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

CLASS_LIST = [
    AutoClothPanel
]