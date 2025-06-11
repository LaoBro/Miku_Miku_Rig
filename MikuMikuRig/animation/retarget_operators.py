# pyright: reportInvalidTypeForm=false
import bpy_extras
from bpy.types import Operator
from bpy.props import FloatProperty, IntProperty ,BoolProperty, StringProperty
from . import retarget_core

class OT_Import_Mixamo(Operator, bpy_extras.io_utils.ImportHelper):
    bl_idname = "mmr.import_mixamo" 
    bl_label = "Import Mixamo/BVH Action"
    bl_description = "Import an FBX or BVH animation file and retarget it to the selected rig"
    bl_options = {'REGISTER', 'UNDO'}
    filter_glob: StringProperty(
        default='*.fbx;*.bvh;', 
        options={'HIDDEN'} 
    )

    first_frame_as_rest_pose: BoolProperty(
        name="First Frame As Rest Pose",
        description="First Frame As Rest Pose",
        default=False
    )
    
    def execute(self,context):
        retarget_core.retarget_mixmao(self,context)
        return{"FINISHED"}

class OT_Import_Vmd(Operator, bpy_extras.io_utils.ImportHelper):
    bl_idname = "mmr.import_vmd" 
    bl_label = "Import VMD Action"
    bl_description = "Import a VMD animation file and retarget it to the selected rig"
    bl_options = {'REGISTER', 'UNDO'}
    filter_glob: StringProperty(
    default='*.vmd;', 
    options={'HIDDEN'} 
    )
    
    def execute(self,context):
        retarget_core.load_vmd(self,context)
        return{"FINISHED"}

class OT_Export_Vmd(Operator, bpy_extras.io_utils.ExportHelper):
    bl_idname = "mmr.export_vmd" 
    bl_label = "Export VMD Action"
    bl_description = "Export the current animation of the selected rig to a VMD file"
    bl_options = {'REGISTER', 'UNDO'}

    filename_ext = ".vmd"

    filter_glob: StringProperty(
    default='*.vmd;', 
    options={'HIDDEN'} ,
    maxlen=255
    )

    scale: FloatProperty(
        name="Action scale",
        description="Action scale",
        default=1,
        min=0
    )

    use_pose_mode: BoolProperty(
        name="Use pose mod",
        description="Use Pose Mod",
        default=False
    )
    
    set_action_range: BoolProperty(
        name="Set action range",
        description="Use Frame Range",
        default=False
    )
    start_frame: IntProperty(
        name="Start frame",
        description="Action start frame",
        default=1
    )
    end_frame: IntProperty(
        name="End frame",
        description="Action end frame",
        default=1
    )
    only_contain_keyframe: BoolProperty(
        name="Only Contain Keyframe",
        description="Only Contain Keyframe",
        default=False
    )

    def execute(self,context):
        retarget_core.export_vmd(self,context)
        return{"FINISHED"}

CLASS_LIST = [
    OT_Import_Mixamo,
    OT_Import_Vmd,
    OT_Export_Vmd
]