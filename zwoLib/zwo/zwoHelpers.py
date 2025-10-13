from ..utils.PyBinaryReader.binary_reader import *

def zwoVector(br: BinaryReader):
    return br.read_float(3)

def zwoQuaternion(br: BinaryReader):
    return br.read_float(4)

def zwoMatrix(br: BinaryReader):
    return [br.read_float(4), br.read_float(4), br.read_float(4), br.read_float(4)]   

#zwoOBB is the mesh's oriented bounding box, it's used for collision detection
class zwoOBB(BrStruct):
    def __init__(self):
        self.Center = [0, 0, 0]
        self.Axis1 = [0, 0, 0]
        self.Axis2 = [0, 0, 0]
        self.Axis3 = [0, 0, 0]
    def __br_read__(self, br: BinaryReader):
        self.Center = br.read_float(3)
        self.Axis1 = br.read_float(3)
        self.Axis2 = br.read_float(3)
        self.Axis3 = br.read_float(3)

    def __br_write__(self, br: BinaryReader):
        br.write_float(self.Center)
        br.write_float(self.Axis1)
        br.write_float(self.Axis2)
        br.write_float(self.Axis3)

#zwoTransform is mostly used for rigid objects it defines the position, scale and rotation of an object
#it's also used for some animations
#using the position, scale and rotation is the same as using the matrix, so it doesn't really matter which one you use
class zwoTransformer(BrStruct):
    def __init__(self):
        self.Position = (0, 0, 0)
        self.Scale = (0, 0, 0)
        self.Rotation = (0, 0, 0, 0)
        self.Matrix = None

    def __br_read__(self, br: BinaryReader):
        self.Position = zwoVector(br)
        self.Scale = zwoVector(br)
        self.Rotation = zwoQuaternion(br)
        self.Matrix = zwoMatrix(br)

    def __br_write__(self, br: BinaryReader):
        br.write_float(self.Position)
        br.write_float(self.Scale)
        br.write_float(self.Rotation)
        
        for m in self.Matrix:
            br.write_float(m)
