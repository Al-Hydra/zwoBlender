from ..utils.PyBinaryReader.binary_reader import *
from .zwoEntity import zwoEntity
from .zwoHelpers import zwoVector, zwoQuaternion
from .zwoTypes import zwoTypes
class zwoAnimation(BrStruct):
    def __init__(self):
        self.Type = zwoTypes.Animation
        self.Entity = None
        self.Flag1 = 0
        self.Flag2 = 0
        self.FrameCount = 0
        self.ObjectCount = 0
        self.AnimationLength = 0
        self.FrameRate = 0
        self.Unk1 = 0
        self.Positions = []
        self.Rotations = []
        self.Scales = []

    def __br_read__(self, br: BinaryReader):
        self.Entity = br.read_struct(zwoEntity) 
        self.Entity2 = br.read_struct(zwoEntity) #there's no reason to have this, but the game reads the file like this

        self.Flag1 = br.read_uint32()

        self.Flag2 = br.read_uint32()

        self.FrameCount = br.read_uint32()
        self.ObjectCount = br.read_uint32()
        self.AnimationLength = br.read_float()
        self.FrameRate = br.read_float()

        if self.Flag2 == 0 and self.FrameCount != 0:
            self.Unk1 = br.read_uint32()
        
        br.set_endian(Endian.LITTLE) #Animation data is little endian

        self.Positions = [zwoVector(br) for i in range(self.FrameCount)]
        self.Rotations = [zwoQuaternion(br) for i in range(self.FrameCount)]
        self.Scales = [zwoVector(br) for i in range(self.FrameCount)]

        br.set_endian(Endian.BIG) #Back to big endian

