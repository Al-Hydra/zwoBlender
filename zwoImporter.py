import bpy, bmesh
import os
from time import time, perf_counter
from bpy.props import CollectionProperty, StringProperty
from mathutils import Vector, Quaternion, Matrix, Euler
from bpy_extras.io_utils import ImportHelper
from math import radians, tan
from .zwoLib.ReadZWO import read_zwo
from .zwoLib.zwo.zwo import *
from .zwoLib.utils.texDict import *
from .zwoLib.zwo.zwoSkeletalAnimation import Entry
import numpy as np

class ZWO_IMPORTER_OT_IMPORT(bpy.types.Operator, ImportHelper):
    bl_label = "Import ZWO"
    bl_idname = "import_scene.zwo"


    files: CollectionProperty(type=bpy.types.OperatorFileListElement, options={'HIDDEN', 'SKIP_SAVE'}) # type: ignore
    directory: StringProperty(subtype='DIR_PATH', options={'HIDDEN', 'SKIP_SAVE'}) # type: ignore
    filepath: StringProperty(subtype='FILE_PATH') # type: ignore
    textures_path: StringProperty(name= "Textures Path",subtype='FILE_PATH') # type: ignore


    def execute(self, context):

        start_time = perf_counter()

        for file in self.files:
            
            self.filepath = os.path.join(self.directory, file.name)
            import_zwo(self.filepath, self.textures_path)
        
        elapsed_s = "{:.2f}s".format(perf_counter() - start_time)
        self.report({'INFO'}, "ZWO file imported in " + elapsed_s)

        return {'FINISHED'}
    

class ZWO_IMPORTER_OT_DROP(bpy.types.Operator):
    bl_label = "Import ZWO"
    bl_idname = "import_scene.drop_zwo"


    files: CollectionProperty(type=bpy.types.OperatorFileListElement, options={'HIDDEN', 'SKIP_SAVE'}) # type: ignore
    directory: StringProperty(subtype='DIR_PATH', options={'HIDDEN', 'SKIP_SAVE'}) # type: ignore
    filepath: StringProperty(subtype='FILE_PATH') # type: ignore
    textures_path: StringProperty(subtype='FILE_PATH') # type: ignore


    def execute(self, context):

        start_time = perf_counter()

        for file in self.files:
            
            self.filepath = os.path.join(self.directory, file.name)
            
            #check if it's a texture dict or a model
            if self.filepath.endswith(".dic") or self.filepath.endswith(".dip"):
                import_texture_dic(self.filepath)
            
            elif self.filepath.endswith(".zwo"):
                #search for a .dip or .dic with the same name in the same folder
                base_name = os.path.splitext(file.name)[0]
                dip_path = os.path.join(self.directory, base_name + ".dip")
                dic_path = os.path.join(self.directory, base_name + ".dic")
                
                if os.path.exists(dip_path):
                    self.textures_path = dip_path
                    import_texture_dic(self.textures_path)
                elif os.path.exists(dic_path):
                    self.textures_path = dic_path
                    import_texture_dic(self.textures_path)

                import_zwo(self.filepath, self.textures_path)
        
        elapsed_s = "{:.2f}s".format(perf_counter() - start_time)
        self.report({'INFO'}, "Files imported in " + elapsed_s)

        return {'FINISHED'}
    
    

class ZWO_FH_IMPORT(bpy.types.FileHandler):
    bl_idname = "ZWO_FH_import"
    bl_label = "File handler for ZWO files"
    bl_import_operator = "import_scene.drop_zwo"
    bl_file_extensions = ".zwo"

    @classmethod
    def poll_drop(cls, context):
        return (context.area and context.area.type == 'VIEW_3D')
    
    def draw():
        pass


class DIC_FH_IMPORT(bpy.types.FileHandler):
    bl_idname = "DIC_FH_import"
    bl_label = "File handler for DIC files"
    bl_import_operator = "import_scene.drop_zwo"
    bl_file_extensions = ".dic"

    @classmethod
    def poll_drop(cls, context):
        return (context.area and context.area.type == 'VIEW_3D')
    
    def draw():
        pass


class DIP_FH_IMPORT(bpy.types.FileHandler):
    bl_idname = "DIP_FH_import"
    bl_label = "File handler for DIP files"
    bl_import_operator = "import_scene.drop_zwo"
    bl_file_extensions = ".dip"

    @classmethod
    def poll_drop(cls, context):
        return (context.area and context.area.type == 'VIEW_3D')
    
    def draw():
        pass

def import_texture_dic(dicPath):
    dic: dicFile = read_tex_dictionary(dicPath)
        
    for texture in dic.Textures:
        if not bpy.data.images.get(texture.Name):
            tex_data = dic2dds(texture)
            tex = bpy.data.images.new(texture.Name, texture.Width, texture.Height)
            tex.pack(data=bytes(tex_data), data_len= len(tex_data))
            tex.source = "FILE"

def import_zwo(zwoPath, texturesPath):
    zwo: zwoFile = read_zwo(zwoPath)
    
    zwoName = os.path.basename(zwoPath)
    
    zwoCollection = bpy.data.collections.new(zwoName)
    bpy.context.scene.collection.children.link(zwoCollection)

    Skeleton: zwoSkeleton = None
    Models = []
    Materials = []
    Textures = []
    Animations = []
    
    load_from_folder = False
    
    #check whether the textures path points to a directory or a file
    if os.path.isdir(texturesPath):
        load_from_folder = True

    
    for chunk in zwo.Entities:
        if chunk.Type == zwoTypes.Skeleton:
            Skeleton = chunk
        elif chunk.Type == zwoTypes.SkeletalAnimation:
            Animations.append(chunk)
        elif chunk.Type == zwoTypes.Mesh:
            Models.append(chunk)
        elif chunk.Type == zwoTypes.Material:
            Materials.append(chunk)

    BoneDict = {}
    ReverseBoneDict = {}
    
    
    def instancedModel(Model):
        # get the original model from blender
        obj = bpy.data.objects.get(Model.Entity3D.InstancedObjectName)
        if obj:
            # create a new object but use the data from the original
            new_obj = bpy.data.objects.new(Model.Entity.Name, obj.data)
            
            # transform the instance using entity3d matrix
            new_obj.matrix_world = Matrix(Model.Entity3D.WorldTransformer.Matrix)
            
            return new_obj
        else:
            print(f"Instance target {Model.Entity3D.InstancedObjectName} not found")
            return None


    def RigidModel(Model):
        mesh = bpy.data.meshes.new(Model.Entity.Name)
        obj = bpy.data.objects.new(Model.Entity.Name, mesh)

        #assign materials
        for material in Model.Entity3D.Materials:
            if bpy.data.materials.get(material):
                obj.data.materials.append(bpy.data.materials[material])

        bm = bmesh.new()
        
        vertex_buffer = Model.VertexBuffers[0].Vertices

        for v in vertex_buffer["position"]:
            bm.verts.new(v)
        
        bm.verts.ensure_lookup_table()
        
        for f in Model.FaceBuffer.Faces:
            try:
                face = bm.faces.new([bm.verts[i] for i in f['indices']])
                face.smooth = True
                bm.faces.ensure_lookup_table()
                bm.faces.index_update()
                face.material_index = f['materialIndex']
            except:
                pass
        bm.to_mesh(mesh)
        bm.free()
        
        #loops
        loops = mesh.loops
        loop_count = len(loops)
        loop_vertex_indices = np.empty(loop_count, dtype=np.int32)
        loops.foreach_get("vertex_index", loop_vertex_indices)
        
        if "normal" in vertex_buffer.dtype.names:
            normals = vertex_buffer["normal"]
            mesh.normals_split_custom_set_from_vertices(normals)
        
        if "uv0" in vertex_buffer.dtype.names:
            uv_layer = mesh.uv_layers.new(name = "UVMap_0")
            uvs = vertex_buffer["uv0"].copy()
            uvs[:,1] = 1.0 - uvs[:,1]
            loop_uvs = uvs[loop_vertex_indices]
            uv_layer.data.foreach_set("uv", loop_uvs.flatten())
            
        if "uv1" in vertex_buffer.dtype.names:
            uv_layer = mesh.uv_layers.new(name = "UVMap_1")
            uvs = vertex_buffer["uv1"].copy()
            uvs[:,1] = 1 - uvs[:,1]
            loop_uvs = uvs[loop_vertex_indices]
            uv_layer.data.foreach_set("uv", loop_uvs.flatten())
        
        if "uv2" in vertex_buffer.dtype.names:
            uv_layer = mesh.uv_layers.new(name = "UVMap_2")
            uvs = vertex_buffer["uv2"].copy()
            uvs[:,1] = 1 - uvs[:,1]
            loop_uvs = uvs[loop_vertex_indices]
            uv_layer.data.foreach_set("uv", loop_uvs.flatten())
        
        if "uv3" in vertex_buffer.dtype.names:
            uv_layer = mesh.uv_layers.new(name = "UVMap_3")
            uvs = vertex_buffer["uv3"].copy()
            uvs[:,1] = 1 - uvs[:,1]
            loop_uvs = uvs[loop_vertex_indices]
            uv_layer.data.foreach_set("uv", loop_uvs.flatten())
        
        if "color0" in vertex_buffer.dtype.names:
            color_layer = mesh.vertex_colors.new(name = "Color_0")
            colors = vertex_buffer["color0"] / 255.0
            loop_colors = colors[loop_vertex_indices]
            color_layer.data.foreach_set("color", loop_colors.flatten())
        
        if "color1" in vertex_buffer.dtype.names:
            color_layer = mesh.vertex_colors.new(name = "Color_1")
            colors = vertex_buffer["color1"] / 255.0
            loop_colors = colors[loop_vertex_indices]
            color_layer.data.foreach_set("color", loop_colors.flatten())
            
            
        obj.data.transform(Matrix(Model.Geometry.LocalTransformers[0].Matrix))
        obj.matrix_world = Matrix(Model.Geometry.WorldTransformers[0].Matrix)
        
        return obj
        
        


    def DeformableModel(Model):
        mesh = bpy.data.meshes.new(Model.Entity.Name)
        obj = bpy.data.objects.new(Model.Entity.Name, mesh)
        obj.parent = armature
        obj.modifiers.new("Armature", 'ARMATURE').object = armature
        

        #assign materials
        for material in Model.Entity3D.Materials:
            if bpy.data.materials.get(material):
                obj.data.materials.append(bpy.data.materials[material])
        
        for bone in armature.data.bones:
            obj.vertex_groups.new(name = bone.name)

        bm = bmesh.new()
        
        vertex_buffer = Model.VertexBuffers[0].Vertices
        for v in vertex_buffer["position"]:
            bm.verts.new(v)

        bm.verts.ensure_lookup_table()

        for f in Model.FaceBuffer.Faces:
            try:
                face = bm.faces.new([bm.verts[i] for i in f['indices']])
                face.smooth = True
                bm.faces.ensure_lookup_table()
                bm.faces.index_update()
                face.material_index = f['materialIndex']
            except:
                pass
        bm.to_mesh(mesh)
        bm.free()
        
        if "boneIndex0" in vertex_buffer.dtype.names:
            vertex_count = len(vertex_buffer)
            weight_slots = 4  # Max 4 bone weights per vertex

            # Make sure vertex groups exist
            max_bone_idx = 0
            for slot in range(weight_slots):
                index_field = f"boneIndex{slot}"
                if index_field in vertex_buffer.dtype.names:
                    max_bone_idx = max(max_bone_idx, vertex_buffer[index_field].max())

            for i in range(max_bone_idx + 1):
                if i >= len(obj.vertex_groups):
                    obj.vertex_groups.new(name=f"Bone_{i}")

            # Assign weights one by one
            for v_idx, vert in enumerate(vertex_buffer):
                for slot in range(weight_slots):
                    index_field = f"boneIndex{slot}"
                    weight_field = f"boneWeight{slot}"
                    if index_field in vertex_buffer.dtype.names and weight_field in vertex_buffer.dtype.names:
                        b_idx = int(vert[index_field])
                        w = float(vert[weight_field])
                        if w > 0:
                            obj.vertex_groups[b_idx].add([v_idx], w, 'REPLACE')


        #loops
        loops = mesh.loops
        loop_count = len(loops)
        loop_vertex_indices = np.empty(loop_count, dtype=np.int32)
        loops.foreach_get("vertex_index", loop_vertex_indices)
        
        if "normal" in vertex_buffer.dtype.names:
            normals = vertex_buffer["normal"]
            mesh.normals_split_custom_set_from_vertices(normals)
        
        if "uv0" in vertex_buffer.dtype.names:
            uv_layer = mesh.uv_layers.new(name = "UVMap_0")
            uvs = vertex_buffer["uv0"].copy()
            uvs[:,1] = 1.0 - uvs[:,1]
            loop_uvs = uvs[loop_vertex_indices]
            uv_layer.data.foreach_set("uv", loop_uvs.flatten())
            
        if "uv1" in vertex_buffer.dtype.names:
            uv_layer = mesh.uv_layers.new(name = "UVMap_1")
            uvs = vertex_buffer["uv1"].copy()
            uvs[:,1] = 1 - uvs[:,1]
            loop_uvs = uvs[loop_vertex_indices]
            uv_layer.data.foreach_set("uv", loop_uvs.flatten())
        
        if "uv2" in vertex_buffer.dtype.names:
            uv_layer = mesh.uv_layers.new(name = "UVMap_2")
            uvs = vertex_buffer["uv2"].copy()
            uvs[:,1] = 1 - uvs[:,1]
            loop_uvs = uvs[loop_vertex_indices]
            uv_layer.data.foreach_set("uv", loop_uvs.flatten())
        
        if "uv3" in vertex_buffer.dtype.names:
            uv_layer = mesh.uv_layers.new(name = "UVMap_3")
            uvs = vertex_buffer["uv3"].copy()
            uvs[:,1] = 1 - uvs[:,1]
            loop_uvs = uvs[loop_vertex_indices]
            uv_layer.data.foreach_set("uv", loop_uvs.flatten())
        
        if "color0" in vertex_buffer.dtype.names:
            color_layer = mesh.vertex_colors.new(name = "Color_0")
            colors = vertex_buffer["color0"] / 255.0
            loop_colors = colors[loop_vertex_indices]
            color_layer.data.foreach_set("color", loop_colors.flatten())
        
        if "color1" in vertex_buffer.dtype.names:
            color_layer = mesh.vertex_colors.new(name = "Color_1")
            colors = vertex_buffer["color1"] / 255.0
            loop_colors = colors[loop_vertex_indices]
            color_layer.data.foreach_set("color", loop_colors.flatten())
        
        
        #obj.data.transform(Matrix(Model.Geometry.LocalTransformer.Matrix))
        #obj.matrix_world = Matrix(Model.Geometry.WorldTransformer.Matrix)
        return obj


    if Skeleton:
        EntityName = Skeleton.Entity.Name
        bpy.data.armatures.new(EntityName)
        armature = bpy.data.objects.new(EntityName, bpy.data.armatures[EntityName])
        zwoCollection.objects.link(armature)
        
        bpy.context.view_layer.objects.active = armature
        bpy.ops.object.mode_set(mode='EDIT')


        def add_bone(bone, parent, index):
            boneName = bone.Name
            BoneDict[boneName] = index 
            #ReverseBoneDict[index] = boneName #This will be used later to assign vertex groups

            b = armature.data.edit_bones.new(boneName)
            b.tail += Vector((0,3,0))
            
            if parent:
                b.parent = parent
                b.matrix = Matrix(bone.Matrix)
            else:
                if bone.ChildIndices:
                    # get the first child to set the head position
                    firstChild = Skeleton.Bones[bone.ChildIndices[0]]
                    childMatrix = Matrix(firstChild.Matrix)
                    
                    translation = childMatrix.translation
                    matrix = Matrix.LocRotScale(translation, Euler((0, 0, radians(-90))), (1,1,1))

                    b.matrix = matrix
            parent = b
            

            for ChildIndex in bone.ChildIndices:
                Child = Skeleton.Bones[ChildIndex]
                add_bone(Child, parent, ChildIndex)

        for i in range(Skeleton.BonesCount):
            #recursively add bones
            parent = None
            bone = Skeleton.Bones[i]
            boneName = bone.Name
            if not BoneDict.get(boneName):
                add_bone(bone, parent, i)

        bpy.ops.object.mode_set(mode='OBJECT')
    
    #load textures
    if not load_from_folder and texturesPath:
        dic: dicFile = read_tex_dictionary(texturesPath)
        
        for texture in dic.Textures:
            tex_data = dic2dds(texture)
            tex = bpy.data.images.new(texture.Name, texture.Width, texture.Height)
            tex.pack(data=bytes(tex_data), data_len= len(tex_data))
            tex.source = "FILE"
    

    for mat in Materials:
        material = bpy.data.materials.new(mat.Name)
        material.use_backface_culling = True
        material.use_nodes = True
        nodes = material.node_tree.nodes
        links = material.node_tree.links

        # Clear default nodes
        for node in nodes:
            nodes.remove(node)

        # Create output and Diffuse BSDF
        output = nodes.new(type="ShaderNodeOutputMaterial")
        output.location = (400, 0)

        diffuse = nodes.new(type="ShaderNodeBsdfDiffuse")
        diffuse.location = (200, 0)

        links.new(diffuse.outputs['BSDF'], output.inputs['Surface'])

        # Texture node
        texture = nodes.new("ShaderNodeTexImage")
        texture.location = (0, 200)

        if load_from_folder:
            path_bmp = os.path.join(texturesPath, mat.TextureName + ".bmp")
            path_tga = os.path.join(texturesPath, mat.TextureName + ".tga")
            if os.path.exists(path_bmp):
                texture.image = bpy.data.images.load(path_bmp)
            elif os.path.exists(path_tga):
                texture.image = bpy.data.images.load(path_tga)
        else:
            texture.image = bpy.data.images.get(mat.TextureName)

        # Vertex color node
        vcol = nodes.new(type="ShaderNodeVertexColor")
        vcol.layer_name = "Color_0"  # adjust if your vertex color layer has a different name
        vcol.location = (0, -100)

        # Multiply vertex color by texture
        multiply = nodes.new(type="ShaderNodeMixRGB")
        multiply.blend_type = 'MULTIPLY'
        multiply.inputs['Fac'].default_value = 0.1
        multiply.location = (150, 100)
        links.new(texture.outputs['Color'], multiply.inputs['Color1'])
        links.new(vcol.outputs['Color'], multiply.inputs['Color2'])

        # Connect multiply result to Diffuse color
        links.new(multiply.outputs['Color'], diffuse.inputs['Color'])

        # Connect alpha from texture to Material Output (requires Transparent BSDF setup)
        # Diffuse BSDF doesn't have alpha input, so we need a Mix Shader for transparency
        transparent = nodes.new(type="ShaderNodeBsdfTransparent")
        transparent.location = (200, -200)

        alpha_mix = nodes.new(type="ShaderNodeMixShader")
        alpha_mix.location = (350, -100)

        links.new(diffuse.outputs['BSDF'], alpha_mix.inputs[2])      # Shader 2 = opaque
        links.new(transparent.outputs['BSDF'], alpha_mix.inputs[1])  # Shader 1 = transparent
        links.new(texture.outputs['Alpha'], alpha_mix.inputs['Fac']) # alpha controls mix
        links.new(alpha_mix.outputs['Shader'], output.inputs['Surface'])

        # Enable transparency
        #material.blend_method = 'BLEND'



    for Model in Models:
        # check if it's an instanced mesh
        if Model.isInstance:
            obj = instancedModel(Model)
            zwoCollection.objects.link(obj)
        if Model.Entity3D.MeshType == 6:
            obj = DeformableModel(Model)
            zwoCollection.objects.link(obj)
        elif Model.Entity3D.MeshType == 2:
            obj = RigidModel(Model)
            zwoCollection.objects.link(obj)

    if Animations:
        if Skeleton:
            AnimSkeleton = Skeleton
        else:
            obj = bpy.context.object
            if obj.type == "ARMATURE":
                AnimSkeleton = obj
        
        if AnimSkeleton:
            for anim in Animations:
            
                #create anim data
                if not AnimSkeleton.animation_data:
                    AnimSkeleton.animation_data_create()

                #create an action
                action = bpy.data.actions.new(name = anim.Entity.Name)

                AnimSkeleton.animation_data.action = action
                if bpy.app.version >= (4, 4, 0):
        
                    #check if an action slot exists for this armature
                    slot = AnimSkeleton.animation_data.action.slots.get(f"OB{AnimSkeleton.name}")

                    if not slot:
                        print(f"No action slot found for armature {AnimSkeleton.name}, creating a new one.")
                        slot = AnimSkeleton.animation_data.action.slots.new(id_type='OBJECT', name=AnimSkeleton.name)
                    
                    AnimSkeleton.animation_data.action_slot = slot
                
                fcurves = action.fcurves

                #set fps to 30
                bpy.context.scene.render.fps = 30

                #adjust the timeline
                bpy.context.scene.frame_start = 0
                bpy.context.scene.frame_end = anim.FrameCount-1

                
                for bone, entry in zip(AnimSkeleton.pose.bones, anim.Entries):
                    #bone info
                    edit_bone = obj.data.bones[bone.name]

                    if edit_bone.parent:
                        matrix = edit_bone.parent.matrix_local.inverted() @ edit_bone.matrix_local
                    else:
                        matrix = edit_bone.matrix_local


                    loc, rot, scale = matrix.decompose()
                    if not edit_bone.parent:
                        rot = Quaternion()
                    
                    target = bone


                    entry: Entry
                    entryType = entry.EntryTypeFlag
                    curveIndex = entry.CurveStartIndex
                    
                    pos_data_path = f'pose.bones["{bone.name}"].location'
                    rot_data_path = f'pose.bones["{bone.name}"].rotation_quaternion'
                    scale_data_path = f'pose.bones["{bone.name}"].scale'
                    
                    group_name = bone.name
                    
                    if entry.positionCurves:
                    
                        positions = np.array(list(entry.positionCurves.values()))
                        positions -= loc
                        
                        posFrames = np.array(list(entry.positionCurves.keys()))
                        flattened = np.stack((posFrames, positions[:,0], positions[:,1], positions[:,2]), axis=1).flatten()
                        insertFrames(fcurves, group_name, pos_data_path, len(posFrames), flattened)
                    
                    if entry.rotationCurves:
                    
                        # rotations
                        rotFrames = np.array(list(entry.rotationCurves.keys()))
                        rotations = np.array(list(entry.rotationCurves.values()))[:, [3,0,1,2]]

                        rotations = np.array([convertRotation(v, rot) for v in rotations])
                        flattened = np.stack((rotFrames, rotations[:,0], rotations[:,1], rotations[:,2], rotations[:,3]), axis=1).flatten()
                        insertFrames(fcurves, group_name, rot_data_path, len(rotFrames), flattened, valCount=4)

def convertRotation(rotation, bone_rotation):
    return bone_rotation.rotation_difference(Quaternion(rotation))


def insertFrames(fcurves, group_name, data_path, kf_count, flattened_values, valCount=3):
    if kf_count == 0:
        return

    arr = np.asarray(flattened_values, dtype=np.float32).reshape(kf_count, 1 + valCount)
    frames = arr[:, 0]

    for i in range(valCount):
        values = arr[:, i + 1]
        fc = fcurves.new(data_path=data_path, index=i, action_group=group_name)
        fc.keyframe_points.add(kf_count)

        # Build (frame, value) pairs interleaved
        co = np.empty(kf_count * 2, dtype=np.float32)
        co[0::2] = frames
        co[1::2] = values

        fc.keyframe_points.foreach_set('co', co)
        fc.update()

def menu_func_import(self, context):
    self.layout.operator(ZWO_IMPORTER_OT_IMPORT.bl_idname,
                        text='.zwo model Importer')