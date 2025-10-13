from ..utils.PyBinaryReader.binary_reader import *
from .zwoHelpers import zwoMatrix
from .zwoEntity import zwoEntity
from .zwoEntity3D import zwoEntity3D
from .zwoTypes import zwoTypes


class zwoSkeleton(BrStruct):
    def __init__(self) -> None:
        self.Name = ""
        self.Type = zwoTypes.Skeleton
        self.Entity = None
        self.Entity3D = None
        self.BonesCount = 0
        self.Bones = []
        self.unk1 = 0
        self.unk2 = 0
    def __br_read__(self, br: BinaryReader, *args) -> None:
        self.Entity = br.read_struct(zwoEntity)

        self.Name = self.Entity.Name
        
        self.Entity3D = br.read_struct(zwoEntity3D)
        self.unk1 = br.read_uint32()
        self.BonesCount = br.read_uint32()
        self.unk2 = br.read_uint32()
        self.Bones = br.read_struct(Bone, self.BonesCount)
        #print(f"Read Skeleton: {self.Name} with {self.BonesCount} bones")
    
    def __br_write__(self, br: BinaryReader):
        
        skl_buf = BinaryReader(endianness=Endian.BIG, encoding='cp932')
        
        skl_buf.write_uint8(self.Entity.HeaderType)
        
        if self.Entity.HeaderType == 5:
            skl_buf.write_uint32(len(self.Entity.Name))
            skl_buf.write_str(self.Entity.Name)
            skl_buf.write_uint32(self.Entity.Type)
        
        elif self.Entity.HeaderType == 6:
            skl_buf.write_uint32(len(self.Entity.Name))
            skl_buf.write_str(self.Entity.Name)
            skl_buf.write_uint32(self.Entity.Type)
            skl_buf.write_uint32(self.Entity.unk2)
            skl_buf.write_uint32(self.Entity.unk3)
            skl_buf.write_uint32(self.Entity.unk4)
            skl_buf.write_uint32(self.Entity.unk5)
            skl_buf.write_uint32(self.Entity.unk6)
        
        skl_buf.write_struct(self.Entity3D)
        skl_buf.write_uint32(self.unk1)
        skl_buf.write_uint32(self.BonesCount)
        skl_buf.write_uint32(self.unk2)
        skl_buf.write_struct(self.Bones)
        
        skl_buf_size = skl_buf.size()
        
        br.write_uint32(skl_buf_size + 4)
        
        br.write_bytes(bytes(skl_buf.buffer()))


class Bone(BrStruct):
    def __init__(self):
        self.Name = ""
        self.ChildCount = 0
        self.ChildIndices = []
        self.Matrix = []
        self.unk1 = 0
    
    def __br_read__(self, br: BinaryReader):
        self.unk1 = br.read_uint32()
        self.Name = br.read_str(br.read_uint32())
        self.ChildCount = br.read_uint32()
        self.ChildIndices = [br.read_uint32() for i in range(self.ChildCount)]
        self.Matrix = zwoMatrix(br)

    def __br_write__(self, br: BinaryReader):
        br.write_uint32(self.unk1)
        br.write_uint32(len(self.Name))
        br.write_str(self.Name)
        br.write_uint32(self.ChildCount)
        br.write_uint32(self.ChildIndices)
        for row in self.Matrix:
            br.write_float(row)