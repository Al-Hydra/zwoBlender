from .PyBinaryReader.binary_reader import *
from enum import Enum
from PIL import Image


class TGA(BrStruct):
    def __init__(self):
        self.IdLength = 0
        self.ColorMapType = 0
        self.DataTypeCode = 0
        self.ColorMapOrigin = 0
        self.ColorMapLength = 0
        self.ColorMapDepth = 0
        self.x_Origin = 0
        self.y_Origin = 0
        self.Width = 0
        self.Height = 0
        self.BitsPerPixel = 0
        self.ImageDescriptor = 0
        self.ImageID = ""
        self.ImageData = b""

    def __br_read__(self, br: BinaryReader):
        self.IdLength = br.read_uint8()
        self.ColorMapType = br.read_uint8()
        self.DataTypeCode = br.read_uint8()
        self.ColorMapOrigin = br.read_uint16()
        self.ColorMapLength = br.read_uint16()
        self.ColorMapDepth = br.read_uint8()
        self.x_Origin = br.read_uint16()
        self.y_Origin = br.read_uint16()
        self.Width = br.read_uint16()
        self.Height = br.read_uint16()
        self.BitsPerPixel = br.read_uint8()
        self.ImageDescriptor = br.read_uint8()
        self.ImageID = br.read_str(self.IdLength)
        self.ImageData = br.read_bytes(self.Width * self.Height * self.BitsPerPixel // 8)
    

    def __br_write__(self, br: BinaryReader):
        br.write_uint8(self.IdLength)
        br.write_uint8(self.ColorMapType)
        br.write_uint8(self.DataTypeCode)
        br.write_uint16(self.ColorMapOrigin)
        br.write_uint16(self.ColorMapLength)
        br.write_uint8(self.ColorMapDepth)
        br.write_uint16(self.x_Origin)
        br.write_uint16(self.y_Origin)
        br.write_uint16(self.Width)
        br.write_uint16(self.Height)
        br.write_uint8(self.BitsPerPixel)
        br.write_uint8(self.ImageDescriptor)
        br.write_str(self.ImageID)
        br.write_bytes(self.ImageData)



class DataTypes(Enum):
    NO_IMAGE_DATA = 0
    UNCOMPRESSED_COLOR_MAPPED = 1
    UNCOMPRESSED_TRUE_COLOR = 2
    UNCOMPRESSED_BLACK_AND_WHITE = 3
    RUN_LENGTH_ENCODED_COLOR_MAPPED = 9
    RUN_LENGTH_ENCODED_TRUE_COLOR = 10
    RUN_LENGTH_ENCODED_BLACK_AND_WHITE = 11


def BGRA_to_RGBA(data: bytes) -> bytes:
    new_data = bytearray(data)
    for i in range(0, len(new_data), 4):
        b = new_data[i]
        g = new_data[i + 1]
        r = new_data[i + 2]
        a = new_data[i + 3]
        new_data[i] = r
        new_data[i + 1] = g
        new_data[i + 2] = b
        new_data[i + 3] = a

    
    return bytes(new_data)


if __name__ == "__main__":
    path = r"D:\SteamLibrary\steamapps\common\Obscure\data\_common\textures\b1bonus3.tga"
    with open(path, "rb") as f:
        filebytes = f.read()
    
    br = BinaryReader(filebytes, Endian.LITTLE, "cp932")
    tga = br.read_struct(TGA)
    print(tga.Width)

    img = Image.frombytes("RGBA", (tga.Height, tga.Width), BGRA_to_RGBA(tga.ImageData)).show()

