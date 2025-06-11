import bpy
import bmesh
from ..base import alert_error

def convert_rigid_body_to_cloth(context):
    """
    将选定的MMD刚体转换为布料物理对象。
    该函数会自动处理相关的网格、骨骼和约束，以创建一个可模拟的布料。
    """
    scene = context.scene
    mmr_property = scene.mmr_property

    selected_objects = bpy.context.selected_objects
    mmd_mesh_object = None
    mmd_armature = None
    mmd_parent_object = None
    # 初始化列表以存储分类后的选定对象
    selected_rigid_bodies = []
    selected_meshes = []
    # 遍历选定对象，区分网格和MMD刚体
    for obj in selected_objects:
        if obj.type == "MESH":
            for m in obj.modifiers:
                if m.type == 'ARMATURE':
                    selected_meshes.append(obj)
                    break # Found armature modifier, no need to check further for this mesh
            # Check if the object has MMD rigid body properties
            if hasattr(obj, 'mmd_rigid'):
                if obj.mmd_rigid.name != '' and obj.mmd_rigid.type != '0':
                    selected_rigid_bodies.append(obj)

    if not selected_rigid_bodies:
        alert_error("提示", "所选物体中没有有效的MMD刚体")
        return False

    # 如果启用了“自动选择刚体”选项，则自动选择连接的刚体
    if mmr_property.auto_select_rigid_body:
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = selected_rigid_bodies[0]
        bpy.ops.mmd_tools.rigid_body_select(properties={'collision_group_number'})
        # Store the actually selected rigid bodies after the operator runs
        rigid_bodies = []
        for obj in bpy.context.selected_objects:
            if hasattr(obj, 'mmd_rigid'):
                if obj.mmd_rigid.name != '' and obj.mmd_rigid.type != '0':
                    rigid_bodies.append(obj)
    else:
        rigid_bodies = selected_rigid_bodies

    # 确定MMD父对象（通常是MMD模型的根对象）
    mmd_parent_object = selected_rigid_bodies[0].parent.parent

    # 如果启用了“自动选择模型”选项，则自动选择相应的网格
    if mmr_property.auto_select_mesh:
        for obj in mmd_parent_object.children:
            if obj.type == "ARMATURE":
                mmd_armature = obj
                if mmd_armature.children:
                    mmd_mesh_object = mmd_armature.children[0]
                else:
                    mmd_mesh_object = None # Armature has no children
        if mmd_mesh_object is None:
            alert_error("提示", "所选刚体没有对应网格模型")
            return False

    elif not selected_meshes:
        alert_error("提示", "所选物体中没有MMD网格模型")
        return False
    else:
        mmd_mesh_object = selected_meshes[0]

    # 骨架是MMD网格对象的父对象
    mmd_armature = mmd_mesh_object.parent

    rigid_bodies_count = len(rigid_bodies)
    joints = [] # 连接选定范围内两个刚体的关节
    side_joints = [] # 连接一个选定刚体到外部对象的关节（钉固点）
    cloth_edge_indices = [] # 用于在新布料网格中创建边的索引
    cloth_vertices_co = [] # 新布料网格顶点的坐标
    cloth_edges = [] # 新布料网格的边，使用顶点索引
    associated_bones = [] # 与每个刚体关联的MMD骨骼

    mean_radius = 0.0 # 平均半径，用于后续的一些偏移计算

    # 计算刚体的平均半径，并将刚体位置和关联骨骼存储起来
    for r_body in rigid_bodies:
        if r_body.mmd_rigid.shape == 'BOX':
            radius = min(r_body.mmd_rigid.size[0], min(r_body.mmd_rigid.size[1], r_body.mmd_rigid.size[2]))
        else:
            radius = r_body.mmd_rigid.size[0]
        mean_radius += radius

        # 将刚体的位置存储为顶点坐标，并存储关联的骨骼
        bone = mmd_armature.pose.bones[r_body.mmd_rigid.bone]
        cloth_vertices_co.append(r_body.location)
        associated_bones.append(bone)

    if rigid_bodies_count > 0:
        mean_radius /= rigid_bodies_count
    # 识别关节并对其进行分类
    for obj in bpy.context.view_layer.objects:
        if hasattr(obj, 'rigid_body_constraint'):
            if obj.rigid_body_constraint is not None:
                if obj.rigid_body_constraint.object1 in rigid_bodies and \
                   obj.rigid_body_constraint.object2 in rigid_bodies:
                    joints.append(obj) # This joint connects two selected rigid bodies
                    index1 = rigid_bodies.index(obj.rigid_body_constraint.object1)
                    index2 = rigid_bodies.index(obj.rigid_body_constraint.object2)
                    cloth_edge_indices.append([index1, index2])
                    cloth_edges.append([index1, index2])
                elif obj.rigid_body_constraint.object1 in rigid_bodies or \
                     obj.rigid_body_constraint.object2 in rigid_bodies:
                    side_joints.append(obj) # This joint connects to something outside the selection (pin)
    # 创建新的布料网格和对象
    mesh = bpy.data.meshes.new('mmd_cloth')
    mesh.from_pydata(cloth_vertices_co, cloth_edges, [])
    mesh.validate()
    cloth_object = bpy.data.objects.new('mmd_cloth', mesh)
    bpy.context.collection.objects.link(cloth_object)
    # 将钉固顶点组写入布料对象
    #写入钉固顶点组
    #add pin vertex groups
    pin_vertex_group = cloth_object.vertex_groups.new(name='mmd_cloth_pin')
    cloth_skin_vertex_group_indices = [pin_vertex_group.index] # Store indices of skinning groups on cloth_object
    for obj in side_joints:
        if obj.rigid_body_constraint.object1 in rigid_bodies:
            side_rigid_body_obj = obj.rigid_body_constraint.object1
            pin_rigid_body_obj = obj.rigid_body_constraint.object2
        else:
            side_rigid_body_obj = obj.rigid_body_constraint.object2
            pin_rigid_body_obj = obj.rigid_body_constraint.object1

        # 布料网格中对应于 side_rigid_body_obj 的顶点索引
        index1 = rigid_bodies.index(side_rigid_body_obj)
        pin_vertex_indices = [index1]

        # 与该刚体钉固到的对象关联的骨骼名称
        pin_bone_name = pin_rigid_body_obj.mmd_rigid.bone
        skin_vertex_group = cloth_object.vertex_groups.get(pin_bone_name)

        if skin_vertex_group is None:
            skin_vertex_group = cloth_object.vertex_groups.new(name=pin_bone_name)

        # 将顶点添加到此特定骨骼的蒙皮组和通用钉固组
        skin_vertex_group.add(pin_vertex_indices, 1, 'REPLACE')
        pin_vertex_group.add(pin_vertex_indices, 1, 'REPLACE')

        cloth_skin_vertex_group_indices.append(skin_vertex_group.index)

    cloth_object.parent = mmd_parent_object
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = cloth_object
    bpy.ops.object.mode_set(mode='OBJECT')
    # 使用BMesh填充布料网格中的面
    bm = bmesh.new()
    bm.from_mesh(mesh)
    #bmesh.ops.edgenet_fill(bm, edges=bm.edges, mat_nr=0, use_smooth=True, sides=4)
    if mmr_property.cloth_convert_mod != 'Bone Constrain':
        bmesh.ops.holes_fill(bm, edges=bm.edges, sides=4)
        # 删除不属于原始刚体连接的边
        #删除多余边
        # Remove edges that were not part of the original rigid body connections
        for e in bm.edges:
            is_original_edge = False
            for orig_edge_indices in cloth_edge_indices: # Check against original edge definitions
                if e.verts[0].index in orig_edge_indices and e.verts[1].index in orig_edge_indices:
                    is_original_edge = True
                    break
            if not is_original_edge:
                bm.edges.remove(e)
        bm.faces.ensure_lookup_table() # 确保面的查找表是最新的

    #尝试标记出头发,飘带
    # Try to identify vertices that are part of ribbon-like structures (long chains of un-filled edges)
    '''bm.to_mesh(mesh)
    bpy.ops.object.mode_set(mode = 'EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.mesh.select_mode(type='EDGE')
    bpy.ops.mesh.select_non_manifold(extend=False, use_wire=True, use_boundary=False, use_multi_face=False, use_non_contiguous=False, use_verts=False)
    bpy.ops.mesh.select_linked(delimit=set())
    bpy.ops.object.mode_set(mode = 'OBJECT')
    bm.clear()
    bm.from_mesh(mesh)'''
    # 仅由线连接的顶点（最初没有面）被认为是飘带顶点
    ribbon_vertices = [v for v in bm.verts if v.is_wire]
    # 如果 extend_ribbon 为 true，则将飘带顶点的选择扩展到其相邻顶点
    if mmr_property.extend_ribbon:
        current_boundary_vertices = set(ribbon_vertices)
        next_boundary_vertices = []
        while len(current_boundary_vertices) != 0:
            next_boundary_vertices.clear()
            for v in current_boundary_vertices:
                for e in v.link_edges:
                    for v2 in e.verts:
                        if v2 not in ribbon_vertices:
                            ribbon_vertices.append(v2)
                            next_boundary_vertices.append(v2)
            current_boundary_vertices = set(next_boundary_vertices)
            next_boundary_vertices.clear()
    # 检查创建的所有面是否都是这些飘带结构的一部分
    all_faces_are_ribbon_parts = True
    for f in bm.faces:
        is_ribbon_face_part = False
        for v in f.verts:
            if v in ribbon_vertices:
                is_ribbon_face_part = True
        if not is_ribbon_face_part:
            all_faces_are_ribbon_parts = False
    # 根据骨骼层级和边界条件将顶点和边分类为顶部、底部或侧面

    top_edges = []
    bottom_edges = []
    side_edges = []
    top_vertices = []
    bottom_vertices = []
    side_vertices = []
    # 识别顶部（类似根部）、底部（类似末端）和飘带顶点
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    for i in range(len(bm.verts)):
        v = bm.verts[i]
        bone = associated_bones[i]
        # 如果顶点是边界且其骨骼未向上连接，或者其骨骼的父骨骼不在布料结构中，则将其分类为顶部顶点
        if not bone.bone.use_connect and v.is_boundary:
            top_vertices.append(v)
        elif bone.parent not in associated_bones:
            top_vertices.append(v)
        # 如果骨骼没有子骨骼或子骨骼不在布料结构中，则将其分类为底部顶点
        elif not bone.children:
            bottom_vertices.append(v)
        elif bone.children[0] not in associated_bones:
            bottom_vertices.append(v)
        
        # 如果顶点是飘带的一部分且模式为“自动”或“骨骼约束”，则将顶点与骨骼尾部对齐
        if (v in ribbon_vertices and mmr_property.cloth_convert_mod == 'Auto') or \
           (mmr_property.cloth_convert_mod == 'Bone Constrain'):
            v.co = bone.tail
    # 标记出头部、尾部、飘带的边
    #标出头部，尾部，飘带边
    #try mark head,tail,ribbon edge
    for i in range(len(bm.edges)):
        e = bm.edges[i]
        vertex1 = e.verts[0]
        vertex2 = e.verts[1]
        if e.is_boundary:
            if vertex1 in top_vertices and vertex2 in top_vertices:
                top_edges.append(e)
            elif vertex1 in bottom_vertices and vertex2 in bottom_vertices:
                bottom_edges.append(e)
            else:
                side_edges.append(e)
                if e.verts[0] not in side_vertices:
                    side_vertices.append(e.verts[0])
                if e.verts[1] not in side_vertices:
                    side_vertices.append(e.verts[1]) # 标记侧边顶点
    # 扩展顶部顶点以在布料部件的根部创建“帽子”或厚度
    new_top_vertices_map = [None for _ in range(len(bm.verts))]
    new_bottom_vertices_map = [None for _ in range(len(bm.verts))]
    for v in top_vertices:
        new_vertex_location = associated_bones[v.index].head # Default to bone head
        # 如果不是自动模式下的飘带，或者如果是表面变形模式，则向外推断
        is_surface_deform_case = (mmr_property.cloth_convert_mod == 'Auto' and v not in ribbon_vertices) or \
                                 (mmr_property.cloth_convert_mod == 'Surface Deform')

        if is_surface_deform_case:
            for e in v.link_edges:
                if e not in top_edges:
                    if e.verts[0] == v:
                        new_vertex_location = v.co * 2 - e.verts[1].co
                    else:
                        new_vertex_location = v.co * 2 - e.verts[0].co
                break
        new_vertex = bm.verts.new(new_vertex_location, v)
        bm.edges.new([v, new_vertex]) # Create edge connecting original to new
        # 如果原始顶点被钉固，则清除其蒙皮权重，以便扩展部分也被钉固
        bmesh_deform_layer = bm.verts.layers.deform.active
        if bmesh_deform_layer is not None:
            bmesh_vertex_deform_data = v[bmesh_deform_layer]
            for group_idx in cloth_skin_vertex_group_indices:
                if group_idx in bmesh_vertex_deform_data:
                    # 将原始顶点上这些特定蒙皮组的权重设置为0
                    bmesh_vertex_deform_data[group_idx] = 0

        new_top_vertices_map[v.index] = new_vertex
        if v in side_vertices:
            side_vertices.append(new_vertex)
            side_edges.append(new_edge)
    # 扩展底部顶点以在末端创建厚度
    #延长尾部顶点
    for v in bottom_vertices:
        if v not in top_vertices:
            new_vertex_location = [0, 0, 0]
            for e in v.link_edges:
                if e not in bottom_edges:
                    if e.verts[0] == v:
                        new_vertex_location = v.co * 2 - e.verts[1].co
                    else:
                        new_vertex_location = v.co * 2 - e.verts[0].co
                break
            new_vertex = bm.verts.new(new_vertex_location, v) # New vertex, template from v
            new_edge = bm.edges.new([v, new_vertex])
            new_bottom_vertices_map[v.index] = new_vertex
            if v in side_vertices:
                side_vertices.append(new_vertex)
                side_edges.append(new_edge)
    # 为扩展的顶部区域创建面
    for e in top_edges:
        vertex1 = e.verts[0]
        vertex2 = e.verts[1]
        vertex3 = new_top_vertices_map[vertex2.index]
        vertex4 = new_top_vertices_map[vertex1.index]
        if vertex3 is not None and vertex4 is not None:
            bm.faces.new([vertex1, vertex2, vertex3, vertex4])
    # 为扩展的底部区域创建面
    for e in bottom_edges:
        vertex1 = e.verts[0]
        vertex2 = e.verts[1]
        vertex3 = new_bottom_vertices_map[vertex2.index]
        vertex4 = new_bottom_vertices_map[vertex1.index]
        if vertex3 is not None and vertex4 is not None:
            bm.faces.new([vertex1, vertex2, vertex3, vertex4])
    # 扩展侧面顶点以在侧面/边界创建厚度
    bm.verts.index_update()
    bm.faces.ensure_lookup_table()
    new_side_vertices_map = {}
    for v in side_vertices:
        for e in v.link_edges:
            if e not in side_edges:
                if e.verts[0] == v:
                    new_vertex_location = v.co * 2 - e.verts[1].co
                else:
                    new_vertex_location = v.co * 2 - e.verts[0].co
                #这里改了
                new_vertex = bm.verts.new(new_vertex_location, v) # New vertex, template from v
                new_side_vertices_map[v.index] = new_vertex
                break
    # 为扩展的侧面区域创建面
    for e in side_edges:
        vertex1 = e.verts[0]
        vertex2 = e.verts[1]
        if vertex2.index in new_side_vertices_map and vertex1.index in new_side_vertices_map:
            vertex3 = new_side_vertices_map[vertex2.index]
            vertex4 = new_side_vertices_map[vertex1.index]
            bm.faces.new([vertex1, vertex2, vertex3, vertex4])

    bm.verts.ensure_lookup_table()
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.normal_update()
    # 轻微挤出飘带顶点以赋予其厚度或第二层
    new_extruded_vertices_map = [None for _ in range(len(bm.verts))]
    for v in bm.verts[:]:
        if v.is_wire:
            new_vertex_location = [v.co[0], v.co[1] + 0.01, v.co[2]]
            new_vertex = bm.verts.new(new_vertex_location, v)
            new_extruded_vertices_map[v.index] = new_vertex
        else:
            # 对于非线框（主表面）顶点，沿其法线向内轻微推动
            v.co[0] -= v.normal[0] * mean_radius
            v.co[1] -= v.normal[1] * mean_radius
            v.co[2] -= v.normal[2] * mean_radius

    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    for e in bm.edges[:]: # 遍历边的副本，因为我们可能会在循环中修改边的集合
        # 在原始飘带边和其挤出对应物之间创建面
        if e.is_wire:
            vertex1 = e.verts[0]
            vertex2 = e.verts[1]
            vertex3 = new_extruded_vertices_map[vertex2.index]
            vertex4 = new_extruded_vertices_map[vertex1.index]
            if vertex3 is not None and vertex4 is not None:
                bm.faces.new([vertex1, vertex2, vertex3, vertex4])
    # 将BMesh最终转换为Mesh
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()

    '''for v in bm.verts[:]:
        if len(v.link_edges)==0:
            bm.verts.remove(v)

    bm.verts.ensure_lookup_table()'''
    bm.to_mesh(mesh)
    # 切换到编辑模式以使法线一致
    bpy.ops.object.mode_set(mode = 'EDIT')
    bpy.ops.mesh.select_all(action = 'SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode = 'OBJECT')
    # 删除原始关节对象，因为它们现在由布料网格结构表示
    for obj in joints:
        bpy.data.objects.remove(obj)
    for obj in side_joints:
        bpy.data.objects.remove(obj)

    cloth_deform_vertex_group = mmd_mesh_object.vertex_groups.new(name='mmd_cloth_deform')

    cloth_object.display_type = 'WIRE'
    # 添加表面细分修改器
    mod = cloth_object.modifiers.new('mmd_cloth_subsurface', 'SUBSURF')
    mod.levels = mmr_property.subdivide
    mod.render_levels = mmr_property.subdivide
    mod.boundary_smooth = 'PRESERVE_CORNERS'
    mod.show_only_control_edges = False
    # 为钉固顶点添加骨架修改器
    # Armature modifier for pinned vertices
    mod = cloth_object.modifiers.new('mmd_cloth_skin', 'ARMATURE')
    mod.object = mmd_armature
    mod.vertex_group = "mmd_cloth_pin"

    # Cloth modifier for simulation
    mod = cloth_object.modifiers.new('mmd_cloth', 'CLOTH')
    mod.settings.vertex_group_mass = "mmd_cloth_pin"
    mod.settings.compression_stiffness = 0
    mod.settings.compression_damping = 0
    mod.settings.shear_stiffness = 0
    mod.settings.shear_damping = 0
    # 添加矫正平滑修改器以修复布料模拟的瑕疵
    mod = cloth_object.modifiers.new('mmd_cloth_smooth', 'CORRECTIVE_SMOOTH')
    # Corrective smooth to fix cloth simulation artifacts
    mod.smooth_type = 'LENGTH_WEIGHTED'
    mod.rest_source = 'BIND'
    bpy.ops.object.correctivesmooth_bind(modifier="mmd_cloth_smooth")
    if not mmr_property.subdivide: # Assuming 0 means off
        mod.show_viewport = False

    bpy.context.view_layer.objects.active = mmd_mesh_object
    # 根据新的布料，在原始MMD骨架/网格上添加权重或约束
    #写入形变权重或骨骼约束
    # preparation    
    unnecessary_vertex_groups: list[bpy.types.VertexGroup] = [] # type hint updated
    mmd_mesh: bpy.types.Mesh = mmd_mesh_object.data
    mmd_bm: bmesh.types.BMesh = bmesh.new()
    mmd_bm.from_mesh(mmd_mesh)

    mmd_bm.verts.layers.deform.verify()
    bmesh_deform_layer = mmd_bm.verts.layers.deform.active

    # 遍历布料对象的顶点，处理每个关联的刚体和骨骼
    for i in range(rigid_bodies_count):
        v = bm.verts[i] # This bm is from the cloth_object, not mmd_mesh_object
        rigid_body_obj = rigid_bodies[i]
        bone = associated_bones[i]
        bone_name = bone.name

        # 判断该部分应由骨骼约束驱动还是表面变形驱动
        use_bone_constraint = (v in ribbon_vertices and mmr_property.cloth_convert_mod == 'Auto') or \
                              (mmr_property.cloth_convert_mod == 'Bone Constrain')
        if use_bone_constraint:
            bone_vertex_group = cloth_object.vertex_groups.new(name=bone_name)
            bone_vertex_group.add([i], 1, 'REPLACE')
            for c in bone.constraints:
                bone.constraints.remove(c)
            con = bone.constraints.new(type='STRETCH_TO')
            con.target = cloth_object
            con.subtarget = bone_name
            con.rest_length = bone.length
        else:
            # 将MMD网格上原始骨骼组的权重转移到新的“cloth_deform”组
            source_vertex_group = mmd_mesh_object.vertex_groups[bone_name]
            source_vertex_group_index = source_vertex_group.index
            unnecessary_vertex_groups.append(source_vertex_group)

            vert: bmesh.types.BMVert
            for vert in mmd_bm.verts:
                bmesh_vertex_deform_data: bmesh.types.BMDeformVert = vert[bmesh_deform_layer]
                if source_vertex_group_index not in bmesh_vertex_deform_data:
                    continue

                target_vertex_group_index = cloth_deform_vertex_group.index
                bmesh_vertex_deform_data[target_vertex_group_index] = \
                    bmesh_vertex_deform_data.get(target_vertex_group_index, 0.0) + \
                    bmesh_vertex_deform_data[source_vertex_group_index]

        bpy.data.objects.remove(rigid_body_obj) # 删除原始MMD刚体对象

    mmd_bm.to_mesh(mmd_mesh)
    mmd_bm.free()
    # 从MMD网格中删除现在由布料/表面变形处理的原始顶点组
    for vertex_group in unnecessary_vertex_groups:
        mmd_mesh_object.vertex_groups.remove(vertex_group)

    # 如果并非所有面都是飘带的一部分，并且布料转换模式不是“骨骼约束”，则添加表面变形修改器
    if not all_faces_are_ribbon_parts and mmr_property.cloth_convert_mod != 'Bone Constrain':
        bpy.context.view_layer.objects.active = mmd_mesh_object
        mod = mmd_mesh_object.modifiers.new('mmd_cloth_deform', 'SURFACE_DEFORM')
        mod.target = cloth_object
        mod.vertex_group = cloth_deform_vertex_group.name
        bpy.ops.object.surfacedeform_bind(modifier=mod.name)

    bm.free()
    return True

