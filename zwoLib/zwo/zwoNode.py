from ..utils.PyBinaryReader.binary_reader import *
from .zwoHelpers import zwoVector
from .zwoTypes import zwoTypes
class zwoNode(BrStruct):
    def __init__(self):
        self.Type = zwoTypes.Node
    
    def __br_read__(self, br: BinaryReader):
        self.NodeIndex = br.read_uint32()
        self.unk1 = br.read_uint32()

        self.Vector1 = zwoVector(br)
        self.Vector2 = zwoVector(br)
        self.Vector3 = zwoVector(br)
        self.Vector4 = zwoVector(br)

        self.ChildNodeCount = br.read_uint32()
        if self.ChildNodeCount > 0:
            self.ChildNodeIndex = br.read_uint32()
            if self.ChildNodeIndex > 0:
                self.ChildNode = br.read_struct(zwoNode)

            self.NodeFlag = br.read_uint32()
            if self.NodeFlag > 0:
                self.ChildNode = br.read_struct(zwoNode)
            

