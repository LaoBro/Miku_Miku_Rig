import bpy
import bmesh
from bpy.types import Operator

def alert_error(title,message):
    def draw(self,context):
        self.layout.label(text=str(message))
    bpy.context.window_manager.popup_menu(draw,title=title,icon='ERROR')

def convert_rigid_body_to_cloth(context):

    scene=context.scene
    mmr_property=scene.mmr_property

    select_obj=bpy.context.selected_objects
    mmd_mesh_object=None
    mmd_arm=None
    mmd_parent=None
    select_rigid_body=[]
    select_mesh=[]
    
    for obj in select_obj:
        if obj.type=="MESH":
            for m in obj.modifiers:
                if m.type=='ARMATURE':
                    select_mesh.append(obj)
                    break
            if hasattr(obj,'mmd_rigid'):
                if obj.mmd_rigid.name != ''and obj.mmd_rigid.type != '0':
                    select_rigid_body.append(obj)

    if len(select_rigid_body)==0:
                    alert_error("提示","所选物体中没有MMD刚体")
                    return(False)

    if mmr_property.auto_select_rigid_body:
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active=select_rigid_body[0]
        bpy.ops.mmd_tools.rigid_body_select(properties={'collision_group_number'})
        rigid_bodys=[]
        for obj in bpy.context.selected_objects:
            if hasattr(obj,'mmd_rigid'):
                if obj.mmd_rigid.name != ''and obj.mmd_rigid.type != '0':
                    rigid_bodys.append(obj)
    else:
        rigid_bodys=select_rigid_body

    mmd_parent=select_rigid_body[0].parent.parent

    if mmr_property.auto_select_mesh:
        for obj in mmd_parent.children:
            if obj.type=="ARMATURE":
                mmd_arm=obj
                mmd_mesh_object=mmd_arm.children[0]
        if mmd_mesh_object == None:
            alert_error("提示","所选刚体没有对应网格模型")
            return(False)

    elif len(select_mesh)==0:
        alert_error("提示","所选物体中没有MMD网格模型")
        return(False)
    else:
        mmd_mesh_object=select_mesh[0]
            
    mmd_arm=mmd_mesh_object.parent

    rigid_bodys_count=len(rigid_bodys)
    joints=[]
    side_joints=[]
    edge_index=[]
    verts=[]
    edges=[]
    bones_list=[]

    mean_radius=0

    for r in rigid_bodys:
        if r.mmd_rigid.shape == 'BOX':
            radius=min(r.mmd_rigid.size[0],min(r.mmd_rigid.size[1],r.mmd_rigid.size[2]))
        else :
            radius=r.mmd_rigid.size[0]
        mean_radius+=radius

        bone=mmd_arm.pose.bones[r.mmd_rigid.bone]
        verts.append(r.location)
        bones_list.append(bone)

    mean_radius/=rigid_bodys_count

    for obj in bpy.context.view_layer.objects:
        if hasattr(obj,'rigid_body_constraint'):
            if obj.rigid_body_constraint!=None:
                if obj.rigid_body_constraint.object1 in rigid_bodys and obj.rigid_body_constraint.object2 in rigid_bodys:
                    joints.append(obj)
                    index1=rigid_bodys.index(obj.rigid_body_constraint.object1)
                    index2=rigid_bodys.index(obj.rigid_body_constraint.object2)
                    edge_index.append([index1,index2])
                    edges.append([index1,index2])
                elif obj.rigid_body_constraint.object1 in rigid_bodys or obj.rigid_body_constraint.object2 in rigid_bodys:
                    side_joints.append(obj)
    

    mesh=bpy.data.meshes.new('mmd_cloth')
    mesh.from_pydata(verts,edges,[])
    mesh.validate()
    cloth_obj=bpy.data.objects.new('mmd_cloth',mesh)
    bpy.context.collection.objects.link(cloth_obj)

    #写入钉固顶点组
    #add pin vertex groups
    pin_vertex_group=cloth_obj.vertex_groups.new(name='mmd_cloth_pin')
    skin_vertex_groups_index=[pin_vertex_group.index]
    for obj in side_joints:
        if obj.rigid_body_constraint.object1 in rigid_bodys:
            side_rigid_body=obj.rigid_body_constraint.object1
            pin_rigid_body=obj.rigid_body_constraint.object2
        else:
            side_rigid_body=obj.rigid_body_constraint.object2
            pin_rigid_body=obj.rigid_body_constraint.object1
        
        index1=rigid_bodys.index(side_rigid_body)
        pin_index=[index1]

        pin_bone_name=pin_rigid_body.mmd_rigid.bone
        skin_vertex_group=cloth_obj.vertex_groups.get(pin_bone_name)

        if skin_vertex_group==None:
            skin_vertex_group=cloth_obj.vertex_groups.new(name=pin_bone_name)

        skin_vertex_group.add(pin_index,1,'REPLACE')
        pin_vertex_group.add(pin_index,1,'REPLACE')

        skin_vertex_groups_index.append(skin_vertex_group.index)

    cloth_obj.parent=mmd_parent
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active=cloth_obj
    bpy.ops.object.mode_set(mode = 'OBJECT')

    #填充面
    #remove ngon
    bm=bmesh.new()
    bm.from_mesh(mesh)
    #bmesh.ops.edgenet_fill(bm, edges=bm.edges, mat_nr=0, use_smooth=True, sides=4)
    bmesh.ops.holes_fill(bm, edges=bm.edges, sides=4)

    #删除大于四边的面
    #remove ngon
    '''for f in bm.faces:
        if len(f.verts)>4:
            bm.faces.remove(f)'''
    #删除多余边
    #remove extra edge
    for e in bm.edges:
        true_edge=False
        for i in edge_index:
            if e.verts[0].index in i and e.verts[1].index in i:
                true_edge=True
                break
        if true_edge==False:
            bm.edges.remove(e)
    bm.faces.ensure_lookup_table()

    #尝试标记出头发,飘带
    #try mark hair or ribbon vertex

    '''bm.to_mesh(mesh)
    bpy.ops.object.mode_set(mode = 'EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.mesh.select_mode(type='EDGE')
    bpy.ops.mesh.select_non_manifold(extend=False, use_wire=True, use_boundary=False, use_multi_face=False, use_non_contiguous=False, use_verts=False)
    bpy.ops.mesh.select_linked(delimit=set())
    bpy.ops.object.mode_set(mode = 'OBJECT')
    bm.clear()
    bm.from_mesh(mesh)'''

    ribbon_verts=[v for v in bm.verts if v.is_wire]
    if mmr_property.extend_ribbon:
        boundary_verts=set(ribbon_verts)
        boundary_verts2=[]
        while len(boundary_verts) != 0:
            boundary_verts2.clear()
            for v in boundary_verts:
                for e in v.link_edges:
                    for v2 in e.verts:
                        if v2 not in ribbon_verts:
                            ribbon_verts.append(v2)
                            boundary_verts2.append(v2)
            boundary_verts=set(boundary_verts2)
            boundary_verts2.clear()

    all_ribbon=True
    for f in bm.faces:
        ribbon_face=False
        for v in f.verts:
            if v in ribbon_verts:
                ribbon_face=True
        if ribbon_face==False:
            all_ribbon=False

    #标记出特殊边和点
    #These are special edge and vertex

    up_edges=[]
    down_edges=[]
    side_edges=[]
    up_verts=[]
    down_verts=[]
    side_verts=[]

    #标出头部，尾部，飘带顶点
    #try mark head,tail,ribbon vertex
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    for i in range(len(bm.verts)):
        v=bm.verts[i]
        bone=bones_list[i]
        if bone.bone.use_connect==False and v.is_boundary:
            up_verts.append(v)
        elif bone.parent not in bones_list:
            up_verts.append(v)
        elif len(bone.children)==0:
            down_verts.append(v)
        elif bone.children[0] not in bones_list:
            down_verts.append(v)
        if v in ribbon_verts and mmr_property.cloth_convert_mod=='Auto' or mmr_property.cloth_convert_mod=='Bone Constrain':
            v.co=bone.tail

    #标出头部，尾部，飘带边
    #try mark head,tail,ribbon edge
    for i in range(len(bm.edges)):
        e=bm.edges[i]
        vert1=e.verts[0]
        vert2=e.verts[1]
        if e.is_boundary:
            if vert1 in  up_verts and vert2 in up_verts:
                up_edges.append(e)
            elif vert1 in down_verts and vert2 in down_verts:
                down_edges.append(e)
            else:
                side_edges.append(e)
                if e.verts[0] not in side_verts:
                    side_verts.append(e.verts[0])
                if e.verts[1] not in side_verts:
                    side_verts.append(e.verts[1])

    #延长头部顶点 
    #extend root vertex
    new_up_verts=[None for i in range(len(bm.verts))]
    new_down_verts=[None for i in range(len(bm.verts))]
    for v in up_verts:
        new_location=bones_list[v.index].head
        if mmr_property.cloth_convert_mod=='Auto' and v not in ribbon_verts or mmr_property.cloth_convert_mod=='Surface Deform':
            for e in v.link_edges:
                if e not in up_edges:
                    if e.verts[0]==v:
                        new_location=v.co*2-e.verts[1].co
                    else:
                        new_location=v.co*2-e.verts[0].co
                break
        new_vert=bm.verts.new(new_location,v)
        new_edge=bm.edges.new([v,new_vert])

        deform_layer = bm.verts.layers.deform.active
        if deform_layer != None:
            deform_vert = v[deform_layer]
            for i in skin_vertex_groups_index:
                if i in deform_vert:
                    deform_vert[i]=0

        new_up_verts[v.index]=new_vert
        if v in side_verts:
            side_verts.append(new_vert)
            side_edges.append(new_edge)

    #延长尾部顶点
    #extend tail vertex
    for v in down_verts:
        if v not in up_verts:
            new_location=[0,0,0]
            for e in v.link_edges:
                if e not in down_edges:
                    if e.verts[0]==v:
                        new_location=v.co*2-e.verts[1].co
                    else:
                        new_location=v.co*2-e.verts[0].co
                break
            new_vert=bm.verts.new(new_location,v)
            new_edge=bm.edges.new([v,new_vert])
            new_down_verts[v.index]=new_vert
            if v in side_verts:
                side_verts.append(new_vert)
                side_edges.append(new_edge)

    for e in up_edges:
        vert1=e.verts[0]
        vert2=e.verts[1]
        vert3=new_up_verts[vert2.index]
        vert4=new_up_verts[vert1.index]
        if vert3 != None and vert4 != None:
            bm.faces.new([vert1,vert2,vert3,vert4])


    for e in down_edges:
        vert1=e.verts[0]
        vert2=e.verts[1]
        vert3=new_down_verts[vert2.index]
        vert4=new_down_verts[vert1.index]
        if vert3 != None and vert4 != None:
            bm.faces.new([vert1,vert2,vert3,vert4])
        
    #延长侧边顶点
    #extend side vertex
    bm.verts.index_update( ) 
    bm.faces.ensure_lookup_table()
    new_side_verts=[None for i in range(len(bm.verts))]
    for v in side_verts:
        for e in v.link_edges:
            if e not in side_edges:
                if e.verts[0]==v:
                    new_location=v.co*2-e.verts[1].co
                else:
                    new_location=v.co*2-e.verts[0].co
                break
        new_vert=bm.verts.new(new_location,v)
        new_side_verts[v.index]=new_vert

    for e in side_edges:
        vert1=e.verts[0]
        vert2=e.verts[1]
        vert3=new_side_verts[vert2.index]
        vert4=new_side_verts[vert1.index]
        if vert3 != None and vert4 != None:
            bm.faces.new([vert1,vert2,vert3,vert4])

    bm.verts.ensure_lookup_table()
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces)
    bm.normal_update()

    #挤出飘带顶点
    #extrude ribbon edge
    new_extrude_verts=[None for i in range(len(bm.verts))]
    for v in bm.verts[:]:
        if v.is_wire:
            new_location=[v.co[0],v.co[1]+0.01,v.co[2]]
            new_vert=bm.verts.new(new_location,v)
            new_extrude_verts[v.index]=new_vert
        else:
            v.co[0]-=v.normal[0]*mean_radius
            v.co[1]-=v.normal[1]*mean_radius
            v.co[2]-=v.normal[2]*mean_radius

    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    for e in bm.edges[:]:
        if e.is_wire:
            vert1=e.verts[0]
            vert2=e.verts[1]
            vert3=new_extrude_verts[vert2.index]
            vert4=new_extrude_verts[vert1.index]
            if vert3 != None and vert4 != None:
                bm.faces.new([vert1,vert2,vert3,vert4])

    #删除孤立顶点
    #remove single vertex
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()

    '''for v in bm.verts[:]:
        if len(v.link_edges)==0:
            bm.verts.remove(v)

    bm.verts.ensure_lookup_table()'''
    bm.to_mesh(mesh)

    bpy.ops.object.mode_set(mode = 'EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode = 'OBJECT')

    for obj in joints:
        bpy.data.objects.remove(obj)
    for obj in side_joints:
        bpy.data.objects.remove(obj)

    deform_vertex_group=mmd_mesh_object.vertex_groups.new(name='mmd_cloth_deform')

    cloth_obj.display_type = 'WIRE'

    mod=cloth_obj.modifiers.new('mmd_cloth_subsurface','SUBSURF')
    mod.levels = mmr_property.subdivide
    mod.render_levels = mmr_property.subdivide
    mod.boundary_smooth = 'PRESERVE_CORNERS'
    mod.show_only_control_edges = False


    mod=cloth_obj.modifiers.new('mmd_cloth_skin','ARMATURE')
    mod.object = mmd_arm
    mod.vertex_group = "mmd_cloth_pin"

    mod=cloth_obj.modifiers.new('mmd_cloth','CLOTH')
    mod.settings.vertex_group_mass = "mmd_cloth_pin"
    mod.settings.compression_stiffness = 0
    mod.settings.compression_damping = 0
    mod.settings.shear_stiffness = 0
    mod.settings.shear_damping = 0



    mod=cloth_obj.modifiers.new('mmd_cloth_smooth','CORRECTIVE_SMOOTH')
    mod.smooth_type = 'LENGTH_WEIGHTED'
    mod.rest_source = 'BIND'
    bpy.ops.object.correctivesmooth_bind(modifier="mmd_cloth_smooth")
    if mmr_property.subdivide==0:
        mod.show_viewport = False

    bpy.context.view_layer.objects.active=mmd_mesh_object

    #写入形变权重或骨骼约束
    #Add weight or constrain
    #准备阶段
    # preparation
    unnecessary_vertex_groups: type.List[bpy.types.VertexGroup] = []
    mmd_mesh: bpy.types.Mesh = mmd_mesh_object.data
    mmd_bm: bmesh.types.BMesh = bmesh.new()
    mmd_bm.from_mesh(mmd_mesh)

    mmd_bm.verts.layers.deform.verify()
    deform_layer = mmd_bm.verts.layers.deform.active

    for i in range(rigid_bodys_count):
        v=bm.verts[i]
        obj=rigid_bodys[i]
        bone=bones_list[i]
        name=bone.name
        if v in ribbon_verts and mmr_property.cloth_convert_mod=='Auto' or mmr_property.cloth_convert_mod=='Bone Constrain' :
            line_vertex_group=cloth_obj.vertex_groups.new(name=name)
            line_vertex_group.add([i],1,'REPLACE')
            for c in bone.constraints:
                bone.constraints.remove(c)
            con=bone.constraints.new(type='STRETCH_TO')
            con.target = cloth_obj
            con.subtarget = name
            con.rest_length = bone.length
        else:
            from_vertex_group = mmd_mesh_object.vertex_groups[name]
            from_index = from_vertex_group.index
            unnecessary_vertex_groups.append(from_vertex_group)

            vert: bmesh.types.BMVert
            for vert in mmd_bm.verts:
                deform_vert: bmesh.types.BMDeformVert = vert[deform_layer]
                if from_index not in deform_vert:
                    continue

                to_index = deform_vertex_group.index
                deform_vert[to_index] = deform_vert.get(to_index, 0.0) + deform_vert[from_index]
    
        bpy.data.objects.remove(obj)

    mmd_bm.to_mesh(mmd_mesh)
    mmd_bm.free()
    for vertex_group in unnecessary_vertex_groups:
        mmd_mesh_object.vertex_groups.remove(vertex_group)

    if all_ribbon == False and mmr_property.cloth_convert_mod!='Bone Constrain':
        bpy.context.view_layer.objects.active=mmd_mesh_object
        mod=mmd_mesh_object.modifiers.new('mmd_cloth_deform','SURFACE_DEFORM')
        mod.target = cloth_obj
        mod.vertex_group = deform_vertex_group.name
        bpy.ops.object.surfacedeform_bind(modifier=mod.name)

    bm.free()

class OT_Convert_Rigid_Body_To_Cloth(Operator):
    bl_idname = "mmr.convert_rigid_body_to_cloth" # python 提示
    bl_label = "Interface"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self,context):
        convert_rigid_body_to_cloth(context)
        return{"FINISHED"}

class OT_Rigid_Body_mass_Multiply(Operator):
    bl_idname = "mmr.rigid_body_mass_multiply" # python 提示
    bl_label = "Interface"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self,context):
        scene=context.scene
        mmr_property=scene.mmr_property
        for obj in bpy.data.objects:
            if hasattr(obj,'mmd_rigid'):
                if obj.mmd_rigid.name != ''and obj.mmd_rigid.type != '0':
                    obj.rigid_body.mass*=mmr_property.mass_multiply_rate
                    obj.rigid_body.mass*=mmr_property.mass_multiply_rate
                    obj.rigid_body.mass*=mmr_property.mass_multiply_rate
        return{"FINISHED"}

Class_list=[OT_Convert_Rigid_Body_To_Cloth,OT_Rigid_Body_mass_Multiply]