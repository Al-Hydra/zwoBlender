from ..utils.PyBinaryReader.binary_reader import *
from .zwoHelpers import zwoTransformer

class zwoEntity3D(BrStruct):
    def __init__(self):
        self.MaterialCount = 0
        self.Materials = []
        self.flags1 = 0
        self.flags2 = 0
        self.unk1 = 0
        self.value1 = 0
        self.value2 = 0
        self.Param1 = None
        self.Param2 = None
        self.unk2 = 0
        self.MeshType = 0
        self.WorldTransformer = None
        self.unk5 = 0
    def __br_read__(self, br: BinaryReader):
        self.MaterialCount = br.read_uint32()
        self.Materials = [br.read_str(br.read_uint32()) for i in range(self.MaterialCount)]

        self.flags1 = br.read_uint32()
        self.flags2 = br.read_uint32()
        self.unk = br.read_uint32()
        

        self.HasGeometry = (self.flags1 & 0x1) != 0
        self.HasInstance = (self.flags1 & 0x2) != 0
        self.HasParentSibling = (self.flags1 & 0x4) != 0
        self.readExtra = (self.flags1 & 0x8) != 0
        self.HasAnimFrame = (self.flags1 & 0x20) != 0
        self.HasExtraInt = (self.flags1 & 0x40) != 0
        self.DisableSomething = (self.flags2 & 0x10000) != 0
        self.EnableSomething = (self.flags2 & 0x20000) != 0
        Flag88 = (self.flags1 >> 3) & 1
        Flag8C = (self.flags1 >> 4) & 1


        if self.HasParentSibling:
            self.Param1 = br.read_str(br.read_uint32())
            self.Param2 = br.read_str(br.read_uint32())

        self.EntityType = br.read_uint32()

        if self.HasExtraInt:
            self.extra = br.read_uint32()

        if self.HasGeometry:
            self.MeshType = br.read_uint32()

        if self.HasInstance:
            self.InstancedObjectName = br.read_str(br.read_uint32())
            self.WorldTransformer = br.read_struct(zwoTransformer)

    
    def __br_write__(self, br: BinaryReader):
        br.write_uint32(self.MaterialCount)
        for m in self.Materials:
            br.write_uint32(len(m))
            br.write_str(m)
        
        br.write_uint32(self.flags1)
        br.write_uint32(self.flags2)
        br.write_uint32(self.unk1)
        
        if (self.flags2 & 0x10000) != 0:
            br.write_uint32(self.value1)
        
        if (self.flags2 & 0x20000) != 0:
            br.write_uint32(self.value2)
        
        if (self.flags1 & 4) != 0:
            br.write_uint32(len(self.Param1))
            br.write_str(self.Param1)
            br.write_uint32(len(self.Param2))
            br.write_str(self.Param2)
        
        br.write_uint32(self.unk2)
        
        if (self.flags1 & 0x40) != 0:
            br.write_uint32(self.unk2)
        
        if (self.flags1 & 1) != 0:
            br.write_uint32(self.MeshType)
            
        if (self.flags1 & 2) != 0:
            br.write_uint32(len(self.Param1))
            br.write_str(self.Param1)
            br.write_struct(self.Transformer1)
            
        if (self.flags1 & 0x20) != 0:
            br.write_uint32(self.unk5)
            



