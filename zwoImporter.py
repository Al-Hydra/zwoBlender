import bpy, bmesh
import os
from time import time, perf_counter
from bpy.props import CollectionProperty, StringProperty
from mathutils import Vector, Quaternion, Matrix, Euler
from bpy_extras.io_utils import ImportHelper
from math import radians, tan
from .zwoLib.ReadZWO import read_zwo
from .zwoLib.zwo import *
from .zwoLib.texDict import *
from .zwoLib.zwoSkeletalAnimation import Entry


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
                dic: dicFile = read_tex_dictionary(self.filepath)
                for texture in dic.Textures:
                    tex_data = dic2dds(texture)
                    tex = bpy.data.images.new(texture.Name, texture.Width, texture.Height)
                    tex.pack(data=bytes(tex_data), data_len= len(tex_data))
                    tex.source = "FILE"
            else:
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
        elif chunk.Type == zwoTypes.Mesh:
            Models.append(chunk)
        elif chunk.Type == zwoTypes.Material:
            Materials.append(chunk)
        elif chunk.Type == zwoTypes.SkeletalAnimation:
            Animations.append(chunk)

    BoneDict = {}
    ReverseBoneDict = {}


    def RigidModel(Model):
        mesh = bpy.data.meshes.new(Model.Entity.Name)
        obj = bpy.data.objects.new(Model.Entity.Name, mesh)
        


        #assign materials
        for material in Model.Entity3D.Materials:
            if bpy.data.materials.get(material):
                obj.data.materials.append(bpy.data.materials[material])

        bm = bmesh.new()
        
        vertex_buffer = Model.VertexBuffers[0]
        for v in vertex_buffer.Vertices:
            bv = bm.verts.new(v.Position)
            bv.normal = v.Normal

        bm.verts.ensure_lookup_table()
        bm.verts.index_update()

        for f in Model.FaceBuffer.Faces:
            try:
                face = bm.faces.new([bm.verts[i] for i in f.Indices])
                face.smooth = True
                bm.faces.ensure_lookup_table()
                bm.faces.index_update()
                face.material_index = f.MaterialIndex
            except:
                pass
        bm.to_mesh(mesh)
        bm.free()
        
        for i in range(vertex_buffer.UVPerVertex):
            uv_layer = mesh.uv_layers.new(name = f"UVMap_{i}")
            for poly in mesh.polygons:
                for loop_index in poly.loop_indices:
                    uv = vertex_buffer.Vertices[mesh.loops[loop_index].vertex_index].UVs[i]
                    mesh.uv_layers[0].data[loop_index].uv = (uv[0], 1 - uv[1])
        
        #obj.matrix_world = Matrix(Model.Geometry.Transformer2.Matrix) @ Matrix(Model.Geometry.Transformer1.Matrix)
        obj.data.transform(Matrix(Model.Geometry.LocalTransformer.Matrix))
        obj.matrix_world = Matrix(Model.Geometry.WorldTransformer.Matrix)
        
        return obj
        
        


    def DeformableModel(Model):
        mesh = bpy.data.meshes.new(Model.Entity.Name)
        obj = bpy.data.objects.new(Model.Entity.Name, mesh)
        obj.parent = armature
        obj.modifiers.new("Armature", 'ARMATURE').object = armature
        #obj.matrix_world = Matrix(Model.Geometry.Transformer1.Matrix)
        

        #assign materials
        for material in Model.Entity3D.Materials:
            if bpy.data.materials.get(material):
                obj.data.materials.append(bpy.data.materials[material])
        
        for bone in armature.data.bones:
            obj.vertex_groups.new(name = bone.name)

        bm = bmesh.new()
        
        #weight layer
        w_layer = bm.verts.layers.deform.new("weights")
        
        
        vertex_buffer = Model.VertexBuffers[0]
        for v in vertex_buffer.Vertices:
            bv = bm.verts.new(v.Position)
            bv.normal = v.Normal
            
            for i in range(vertex_buffer.WeightPerVertex):
                bv[w_layer][v.BoneIndices[i]] = v.BoneWeights[i]

        bm.verts.ensure_lookup_table()
        bm.verts.index_update()

        for f in Model.FaceBuffer.Faces:
            try:
                face = bm.faces.new([bm.verts[i] for i in f.Indices])
                face.smooth = True
                bm.faces.ensure_lookup_table()
                bm.faces.index_update()
                face.material_index = f.MaterialIndex
            except:
                pass
        bm.to_mesh(mesh)
        bm.free()
        
        #mesh.transform(Matrix(Model.Geometry.Transformer2.Matrix))
        
        for i in range(vertex_buffer.UVPerVertex):
            uv_layer = mesh.uv_layers.new(name = f"UVMap_{i}")
            for poly in mesh.polygons:
                for loop_index in poly.loop_indices:
                    uv = vertex_buffer.Vertices[mesh.loops[loop_index].vertex_index].UVs[i]
                    mesh.uv_layers[0].data[loop_index].uv = (uv[0], 1 - uv[1])
        
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
                b.matrix = Matrix(bone.Matrix)
                b.parent = parent

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
        material.use_nodes = True

        bsdf = material.node_tree.nodes["Principled BSDF"]

        texture = material.node_tree.nodes.new("ShaderNodeTexImage")
        
        if load_from_folder:
            path = os.path.join(texturesPath, mat.TextureName + ".bmp")
            #check if texture exists
            if os.path.exists(path):
            #if bpy.data.images.get(mat.TextureName):
                texture.image = bpy.data.images.get(mat.TextureName)
            else:
                path = os.path.join(texturesPath, mat.TextureName + ".tga")
            
            if os.path.exists(path):
                texture.image = bpy.data.images.load(path)
        else:
            texture.image = bpy.data.images.get(mat.TextureName)

        material.node_tree.links.new(bsdf.inputs['Base Color'], texture.outputs['Color'])


    for Model in Models:
        if Model.Entity3D.MeshType == 6:
            obj = DeformableModel(Model)
            zwoCollection.objects.link(obj)
        elif Model.Entity3D.MeshType == 2:
            obj = RigidModel(Model)
            zwoCollection.objects.link(obj)

    '''if Animations:
        if Skeleton:
            AnimSkeleton = Skeleton
        else:
            obj = bpy.context.object
            if obj.type == "ARMATURE":
                AnimSkeleton = obj
        
        if AnimSkeleton:
            #let's test the first animation
            anim: zwoSkeletalAnimation = Animations[0]

            #create an action
            action = bpy.data.actions.new(name = anim.Entity.Name)
            curves = anim.Curves
            #set fps to 30
            bpy.context.scene.render.fps = 30

            #adjust the timeline
            bpy.context.scene.frame_start = 0
            bpy.context.scene.frame_end = anim.FrameCount

            
            for bone, entry in zip(AnimSkeleton.pose.bones, anim.Entries):
                print(bone.name)
                print(entry.EntryTypeFlag, entry.CurveStartIndex, entry.CurvesPerFrame)

                #bone info
                b = obj.data.bones[bone.name]

                if b.parent:
                    matrix = b.parent.matrix_local @ b.matrix_local
                else:
                    matrix = b.matrix_local
                
                loc, rot, scale = matrix.decompose()

                trans = loc
                bone_rot = rot.inverted()


                entry: Entry
                entryType = entry.EntryTypeFlag
                if entryType == 0:
                    continue
                elif entryType == 1:
                    curveIndex = entry.CurveStartIndex
                    rotation = curves[curveIndex]
                    rotation = (rotation[3], rotation[0], rotation[1], rotation[2])
                    
                    anim_rot = Quaternion(rotation)

                    bone_rot.rotate(anim_rot)


                    bone.rotation_quaternion = rot
                    bone.keyframe_insert(data_path = "rotation_quaternion", frame = 0)
                    curveIndex += 1

                    #loc = Vector(curves[curveIndex][x] * 0.01 for x in range(3))
                    
                    bone.location = loc
                    bone.keyframe_insert(data_path = "location", frame = 0)
                    curveIndex += 1

                    bone.scale = Vector(curves[curveIndex][x] for x in range(3))
                    bone.keyframe_insert(data_path = "scale", frame = 0)
                    curveIndex += 1
                
                elif entryType == 3:
                    curveIndex = entry.CurveStartIndex

                    rotation = curves[curveIndex]
                    rotation = (rotation[3], rotation[0], rotation[2], rotation[1])
                    bone.rotation_quaternion = Quaternion(rotation)
                    bone.keyframe_insert(data_path = "rotation_quaternion", frame = 0)
                    curveIndex += 1

                    #location

                    bone_loc = Vector(curves[curveIndex][x] * 0.01 for x in range(3))
                    #bind_loc = trans * 0.01
                    #bone_loc.rotate(bone_rot)
                    #bind_loc.rotate(bone_rot)

                    bone.location = bone_loc
                    bone.keyframe_insert(data_path = "location", frame = 0)
                    curveIndex += 1



                    bone.scale = Vector(curves[curveIndex][x] for x in range(3))
                    bone.keyframe_insert(data_path = "scale", frame = 0)
                    curveIndex += 1

                    for i in range(anim.FrameCount - 1):
                        rotation = curves[curveIndex]
                        rotation = (rotation[3], rotation[0], rotation[1], rotation[2])
                        bone.rotation_quaternion = rot
                        #bone.matrix = Quaternion(rotation).to_matrix().to_4x4() @ matrix
                        bone.keyframe_insert(data_path = "rotation_quaternion", frame = i + 1)
                        curveIndex += 1
                    
                elif entryType == 7:

                    curveIndex = entry.CurveStartIndex
                    rotation = curves[curveIndex]
                    rotation = (rotation[3], rotation[0], rotation[2], rotation[1])
                    rotation = Quaternion(rotation)
                    bone.rotation_quaternion = rotation
                    bone.keyframe_insert(data_path = "rotation_quaternion", frame = 0)
                    curveIndex += 1

                    bone.location = Vector(curves[curveIndex][x] * 0.01 for x in range(3))
                    bone.keyframe_insert(data_path = "location", frame = 0)
                    curveIndex += 1

                    bone.scale = Vector(curves[curveIndex][x] for x in range(3))
                    bone.keyframe_insert(data_path = "scale", frame = 0)
                    curveIndex += 1

                    for i in range(anim.FrameCount - 1):
                        rotation = curves[curveIndex]
                        rotation = (rotation[3], rotation[0], rotation[1], rotation[2])
                        rotation = Quaternion(rotation).conjugated()
                        bone.rotation_quaternion = rot
                        bone.keyframe_insert(data_path = "rotation_quaternion", frame = i + 1)
                        curveIndex += 1

                        location = Vector(curves[curveIndex][x] * 0.01 for x in range(3))
                        location = (location[0], location[1], location[2])
                        bone.location = loc 
                        bone.keyframe_insert(data_path = "location", frame = i + 1)
                        curveIndex += 1

'''


def menu_func_import(self, context):
    self.layout.operator(ZWO_IMPORTER_OT_IMPORT.bl_idname,
                        text='.zwo model Importer')