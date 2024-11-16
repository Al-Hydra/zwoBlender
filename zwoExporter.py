import bpy
from .zwoLib.zwo import *
from .zwoLib.zwoMesh import *
from .zwoLib.zwoTypes import *
from .zwoLib.zwoEntity import *
from .zwoLib.zwoEntity3D import *
from .zwoLib.zwoMaterial import *
from .zwoLib.zwoSkeleton import *
import sys
from mathutils import Matrix, Vector
import bmesh
from .zwoLib.PyBinaryReader.binary_reader import *
from bpy_extras.io_utils import ExportHelper
from bpy.types import Operator, MeshLoopTriangle
from bpy.props import CollectionProperty, StringProperty
from zlib import crc32

from .zwoLib.ReadZWO import read_zwo
from .zwoLib.WriteZWO import write_zwo





class ZWO_IMPORTER_OT_EXPORT(Operator, ExportHelper):
    bl_idname = 'export_scene.zwo'
    bl_label = 'Export .zwo'
    filename_ext = '.zwo'

    directory: StringProperty(subtype='DIR_PATH', options={'HIDDEN', 'SKIP_SAVE'}) # type: ignore
    filepath: StringProperty(subtype='FILE_PATH') # type: ignore
    
    def update_collection(self, context):
        if self.filepath:
            self.filepath = self.filepath.split('.')[0] + '_' + self.collection_name + '.zwo'
    
    collection_name: StringProperty(name='Collection', update= update_collection)
    
    overwrite: bpy.props.BoolProperty(name='Overwrite Existing zwo', default=False)
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
    
    def draw(self, context):
        layout = self.layout
        layout.prop_search(self, 'collection_name', bpy.data, 'collections')
        layout.prop(self, 'overwrite')

    def execute(self, context):
        
        if self.overwrite:
            og_zwo = read_zwo(self.filepath)
        else:
            og_zwo = zwoFile()
        
        self.collection = bpy.data.collections[self.collection_name]
        
        blender_meshes = [obj for obj in self.collection.objects if obj.type == 'MESH']
        blender_armatures = [obj for obj in self.collection.objects if obj.type == 'ARMATURE']
        
        zwo_meshes = []
        zwo_materials = {}
        zwo_skeletons = []
        
        for entity in og_zwo.Entities:
            if entity.Type == zwoTypes.Material:
                zwo_materials.append(entity)
            elif entity.Type == zwoTypes.Mesh:
                zwo_meshes.append(entity)
            elif entity.Type == zwoTypes.Skeleton:
                zwo_skeletons.append(entity)
        
        
        for obj in blender_meshes:
            zwomesh = self.make_mesh(obj, zwo_materials)
            zwo_meshes.append(zwomesh)
            
        for obj in blender_armatures:
            zwo_skeleton = self.make_skeleton(obj)
            zwo_skeletons.append(zwo_skeleton)
        
        og_zwo.Entities = zwo_meshes + list(zwo_materials.values()) + zwo_skeletons
                
        write_zwo(og_zwo, self.filepath)


        return {'FINISHED'}


    def make_mesh(self, obj, materials_list):
        
        #we'll check if the mesh has an armature modifier if it does, we'll use the armature data and consider it a skinned mesh
        armature_data = None
        for mod in obj.modifiers:
            if mod.type == 'ARMATURE':
                armature_data = mod.object
                break
        

        mesh_obj = obj
        
        blender_mesh = mesh_obj.data
        #triangulate the mesh
        blender_mesh.calc_loop_triangles()

        mesh_vertices = blender_mesh.vertices
        mesh_loops = blender_mesh.loops
        
        vertex_groups = mesh_obj.vertex_groups

        if len(blender_mesh.color_attributes) > 0:
            color_layer = blender_mesh.color_attributes[0].data

        uv_layer = blender_mesh.uv_layers[0].data

        mdl_vertices = {}
        tris = []
        
        vbuffer = VertexBuffer()


        if armature_data:
            blender_bones = [b.name for b in armature_data.data.bones]
        else:
            blender_bones = []
        
        #get mesh materials
        #blender_materials = [m for m in blender_mesh.materials]
        for mat in blender_mesh.materials:
            if mat.name not in materials_list.keys():
                materials_list[mat.name] = self.make_material(mat)
                
        mdl_vertex_index = 0

        for triangle in blender_mesh.loop_triangles:
            triangle: MeshLoopTriangle
            zwo_tri = Face()
            
            zwo_tri.MaterialIndex = triangle.material_index

            triverts = []
            
            for loop_index in triangle.loops:
                loop = mesh_loops[loop_index]
                blender_vertex = mesh_vertices[loop.vertex_index]                

                zwo_vertex = Vertex()

                
                zwo_vertex.Position = list(blender_vertex.co)
                zwo_vertex.Normal = list(loop.normal)

                # Color
                zwo_vertex.Colors = [[0, 255, 255, 255]]
                
                if uv_layer:
                    zwo_vertex.UVs = [[uv_layer[loop_index].uv[0], 1 - uv_layer[loop_index].uv[1]]]
                
                if armature_data:
                
                    # Bone weights
                    b_weights = [(vertex_groups[g.group].name, g.weight) for g in sorted(
                        blender_vertex.groups, key=lambda g: 1 - g.weight) if vertex_groups[g.group].name in blender_bones]
                    if len(b_weights) > 4:
                        b_weights = b_weights[:4]
                    elif len(b_weights) < 4:
                        # Add zeroed elements to b_weights so it's 4 elements long
                        b_weights += [(0, 0.0)] * (4 - len(b_weights))

                    weight_sum = sum(weight for (_, weight) in b_weights)
                    if weight_sum > 0.0:
                        for i, bw in enumerate(b_weights):
                            if bw[0] in blender_bones:
                                zwo_vertex.BoneIndices.append(blender_bones.index(bw[0]))
                            else:
                                zwo_vertex.BoneIndices.append(0)
                            
                            zwo_vertex.BoneWeights.append(bw[1] / weight_sum)

                    else:
                        zwo_vertex.BoneIndices = [0] * 4
                        zwo_vertex.BoneWeights = [0] * 3 + [1]
                
                
                #to avoid creating unnecessary duplicate vertices
                #we'll create a hash of the vertex and check if it already exists
                vertex_hash = crc32(bytes(str(zwo_vertex.Position) + str(zwo_vertex.Normal) + str(zwo_vertex.Colors) + str(zwo_vertex.UVs), 'utf-8'))
                
                #check if the vertex already exists
                if vertex_hash in mdl_vertices:
                    #if it does, we'll just use the existing vertex
                    triverts.append(mdl_vertices[vertex_hash][0])
                else:
                    #if it doesn't, we'll add it to the list of vertices
                    mdl_vertices[vertex_hash] = [mdl_vertex_index, zwo_vertex]
                    triverts.append(mdl_vertex_index)
                    mdl_vertex_index += 1
            
            zwo_tri.Indices = triverts
            tris.append(zwo_tri)
        
        
        #sort verts by their indices        
        vbuffer.Vertices = [v[1] for v in sorted(mdl_vertices.values(), key=lambda x: x[0])]
        
        
        sample_vertex = vbuffer.Vertices[0]
        
        if sample_vertex.Normal != (0,0,0):        
            vbuffer.VertexFlags = 0x1
        
        if len(sample_vertex.Colors) >= 1:
            vbuffer.VertexFlags += 0x2
        
        if len(sample_vertex.Colors) >= 2:
            vbuffer.VertexFlags += 0x4
        
        if len(sample_vertex.UVs) >= 1:
            vbuffer.VertexFlags += 0x8
        
        if len(sample_vertex.UVs) >= 2:
            vbuffer.VertexFlags += 0x10
        
        if len(sample_vertex.UVs) >= 3:
            vbuffer.VertexFlags += 0x20
        
        if len(sample_vertex.UVs) >= 4:
            vbuffer.VertexFlags += 0x40

        
        #we'll assume that we have 4 weights per vertex
        if armature_data:
            vbuffer.VertexFlags += 0x80 + 0x100 + 0x200 + 0x400
        
        
        fbuffer = FaceBuffer()
        fbuffer.TrianglesType = 1
        fbuffer.IndexType = 0
        
        fbuffer.Faces = tris
        
        zwo_mesh: zwoMesh = zwoMesh()
        zwo_mesh.Entity = zwoEntity()
        zwo_mesh.Entity.Name = obj.name
        zwo_mesh.Entity.Type = 5
        if armature_data:
            zwo_mesh.Entity.HeaderType = 5
        else:
            zwo_mesh.Entity.HeaderType = 6
        
        zwo_mesh.Entity3D = zwoEntity3D()
        zwo_mesh.Entity3D.Name = obj.name
        
        zwo_mesh.Entity3D.MaterialCount = len(blender_mesh.materials)
        zwo_mesh.Entity3D.Materials = [mat.name for mat in blender_mesh.materials]
        zwo_mesh.Entity3D.flags1 = 0x1
        if armature_data:
            zwo_mesh.Entity3D.MeshType = 6
        else:
            zwo_mesh.Entity3D.MeshType = 2

        zwo_geometry = zwoGeometry()
        zwo_geometry.TransformerCount = 1
        zwo_geometry.unk = 1000
        
        #save and reset the object's matrix
        world_matrix = obj.matrix_world.copy()
        obj.matrix_world = Matrix()
        local_matrix = obj.matrix_local.copy()
        
        #restore the object's matrix
        obj.matrix_world = world_matrix
        
        local_transformer = zwoTransformer()
        local_transformer.Position = list(local_matrix.translation)
        local_transformer.Rotation = list(local_matrix.to_quaternion())
        local_transformer.Scale = list(local_matrix.to_scale())
        local_transformer.Matrix = [list(row) for row in local_matrix]
        
        zwo_geometry.LocalTransformer = local_transformer
        
    
        world_transformer = zwoTransformer()
        world_transformer.Position = list(world_matrix.translation)
        world_transformer.Rotation = list(world_matrix.to_quaternion())
        world_transformer.Scale = list(world_matrix.to_scale())
        world_transformer.Matrix = [list(row) for row in world_matrix]     
        
        zwo_geometry.WorldTransformer = world_transformer
                
        zwo_geometry.OrientedBoundingBox = self.calculate_obb(obj)
        
        zwo_mesh.Geometry = zwo_geometry
        
        
        zwo_mesh.VertexBuffers = [vbuffer] # a mesh can have multiple vertex buffers
        zwo_mesh.FaceBuffer = fbuffer
        
        return zwo_mesh
    
    
    def make_material(self, blender_material, old_material= None):
        
        if old_material:
            new_material = old_material
        else:
            new_material = zwoMaterial()
            new_material.vector4 = (0.5,0.5,0.5)
            new_material.ScaleUV = (1,1,1)
        
        new_material.Name = blender_material.name
        new_material.Flag = 3
        
        #find the first texture in the blender material
        tex = None
        for node in blender_material.node_tree.nodes:
            if node.type == 'TEX_IMAGE':
                tex = node
                break
        
        if tex:
            if tex.image:
                new_material.TextureName = tex.image.name
            
                #make sure that the name has no format extension
                if '.' in new_material.TextureName:
                    new_material.TextureName = new_material.TextureName.split('.')[0]
                
        return new_material
        
    
    def make_skeleton(self, blender_armature):
        zwo_skeleton = zwoSkeleton()
        zwo_skeleton.Entity = zwoEntity()   
        zwo_skeleton.Entity.Name = blender_armature.name
        zwo_skeleton.Entity.Type = 6
        zwo_skeleton.Entity.HeaderType = 5
        zwo_skeleton.Entity3D = zwoEntity3D()
        
        zwo_skeleton.BonesCount = len(blender_armature.data.bones)
        
        bone_indices = {bone.name: i for i, bone in enumerate(blender_armature.data.bones)}
        
        for bone in blender_armature.data.bones:
            zwo_bone = Bone()
            zwo_bone.Name = bone.name
            zwo_bone.Matrix = [list(row) for row in bone.matrix_local]
            zwo_bone.ChildCount = len(bone.children)
            zwo_bone.ChildIndices = [bone_indices[child.name] for child in bone.children]
            
            zwo_skeleton.Bones.append(zwo_bone)
        
        return zwo_skeleton

    
    def calculate_obb(self, obj):
        zwo_obb = zwoOBB()
        # Apply object's world matrix to bounding box corners
        corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
        
        # Calculate center as the average of all corners
        zwo_obb.Center = list(sum(corners, Vector()) / 8)
        
        # Calculate axes based on corner pairs
        zwo_obb.Axis1 = list((corners[1] - corners[0]) / 2)
        zwo_obb.Axis2 = list((corners[3] - corners[0]) / 2)
        zwo_obb.Axis3 = list((corners[4] - corners[0]) / 2)
        
        return zwo_obb

def menu_func_export(self, context):
    self.layout.operator(ZWO_IMPORTER_OT_EXPORT.bl_idname, text='ZWO Model Exporter')