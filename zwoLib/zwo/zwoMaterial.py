from ..utils.PyBinaryReader.binary_reader import *
from .zwoEntity import zwoEntity
from .zwoTypes import zwoTypes


class zwoMaterial(BrStruct):
    def __init__(self) -> None:
        self.Type = zwoTypes.Material
        self.Name = ""
        self.Flag = 0
        self.vector1 = (0, 0, 0)
        self.vector2 = (0, 0, 0)
        self.vector3 = (0, 0, 0)
        self.unk1 = 0
        self.unk2 = 0
        self.unk3 = 0
        self.unk4 = 0
        self.unk5 = 0
        self.vector4 = (0, 0, 0)
        self.unkint1 = 0
        self.unkint2 = 0
        self.ScaleUV = (1,1)
        self.MoveUV = (0, 0)
        self.RotateUV = (0, 0)
        self.ScaleUV2 = (1, 1)
        self.unkint3 = 0
        self.TextureName = ""
        self.TextureName2 = ""
        self.unk15 = 0
        self.unk16 = 0
        self.UnkString = ""
        self.unk17 = 0
        self.unk18 = 0
        


    def __br_read__(self, br: BinaryReader, *args) -> None:
        self.FileSize = br.read_uint32()
        self.Flag = br.read_uint8()
        if (self.Flag - 2) < 2:
            nameLength = br.read_uint32()
            if nameLength > 0:
                self.Name = br.read_bytes(nameLength).decode('cp1252')
            else:
                self.Name = ""

            self.vector1 = br.read_float(3)
            self.vector2 = br.read_float(3)
            self.vector3 = br.read_float(3)

            self.unk1 = br.read_float()
            self.unk2 = br.read_float()
            self.unk3 = br.read_float()
            self.unk4 = br.read_float()
            self.unk5 = br.read_float()

            self.vector4 = br.read_float(3)

            self.unkint1 = br.read_uint32()
            self.unkint2 = br.read_uint32()

            self.ScaleUV = br.read_float(2)

            self.MoveUV = br.read_float(2)

            self.RotateUV = br.read_float(3)
            
            self.ScaleUV2 = br.read_float(2)

            self.unkint3 = br.read_uint32()

            self.TextureName = br.read_str(br.read_uint32())
            self.TextureName2 = br.read_str(br.read_uint32())

            if self.Flag == 0x03:
                self.unk15 = br.read_uint32()
                self.unk16 = br.read_uint32()

                if (self.unk16 & 1) == 1:
                    self.UnkString = br.read_str(br.read_uint32())

                if (self.unk16 & 2) == 2:
                    self.unk17 = br.read_float()
                    self.unk18 = br.read_uint32()
    
    def __br_write__(self, br: BinaryReader):

        mat_buf = BinaryReader(bytearray(), Endian.BIG)
        mat_buf.write_uint8(self.Flag)
        mat_buf.write_uint32(len(self.Name))
        mat_buf.write_str(self.Name)
        mat_buf.write_float(self.vector1)
        mat_buf.write_float(self.vector2)
        mat_buf.write_float(self.vector3)
        mat_buf.write_float(self.unk1)
        mat_buf.write_float(self.unk2)
        mat_buf.write_float(self.unk3)
        mat_buf.write_float(self.unk4)
        mat_buf.write_float(self.unk5)
        mat_buf.write_float(self.vector4)
        mat_buf.write_uint32(self.unkint1)
        mat_buf.write_uint32(self.unkint2)

        mat_buf.write_float(self.ScaleUV)
        mat_buf.write_float(self.MoveUV)
        mat_buf.write_float(self.RotateUV)
        mat_buf.write_float(self.ScaleUV2)

        mat_buf.write_uint32(self.unkint3)

        mat_buf.write_uint32(len(self.TextureName))
        mat_buf.write_str(self.TextureName)
        mat_buf.write_uint32(len(self.TextureName2))
        mat_buf.write_str(self.TextureName2)

        if self.Flag == 0x03:
            mat_buf.write_uint32(self.unk15)
            mat_buf.write_uint32(self.unk16)

            if (self.unk16 & 1) == 1:
                mat_buf.write_uint32(len(self.UnkString))
                mat_buf.write_str(self.UnkString)

            if (self.unk16 & 2) == 2:
                mat_buf.write_float(self.unk17)
                mat_buf.write_uint32(self.unk18)

        size = mat_buf.size() + 4
        br.write_uint32(size)
        br.write_bytes(bytes(mat_buf.buffer()))
        