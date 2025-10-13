from .PyBinaryReader.binary_reader import *
#from PIL import Image
class BMP(BrStruct):
    def __init__(self):
        self.Signature = "BM"
        self.Header = bmpHeader()
        self.DIBHeader = bmpDIBHeader()
        self.PixelData = b""


    def __br_read__(self, br: BinaryReader):
        self.Header = br.read_struct(bmpHeader)
        self.DIBHeader = br.read_struct(bmpDIBHeader)
        DIB: bmpDIBHeader = self.DIBHeader
        if DIB.ImageSize == 0:
            DIB.ImageSize = DIB.Width * DIB.Height * DIB.BitsPerPixel // 8
        self.PixelData = bytearray(br.read_bytes(self.DIBHeader.ImageSize))
    

    def __br_write__(self, br: BinaryReader):
        br.write_struct(self.Header)
        br.write_struct(self.DIBHeader)
        br.write_bytes(self.PixelData)


class bmpHeader(BrStruct):
    def __init__(self):
        self.FileSize = 0
        self.Reserved1 = 0
        self.Reserved2 = 0
        self.OffsetToPixelData = 0


    def __br_read__(self, br: BinaryReader):
        self.Signature = br.read_str(2)
        self.FileSize = br.read_uint32()
        self.Reserved1 = br.read_uint16()
        self.Reserved2 = br.read_uint16()
        self.OffsetToPixelData = br.read_uint32()


    def __br_write__(self, br: BinaryReader):
        br.write_str(self.Signature)
        br.write_uint32(self.FileSize)
        br.write_uint16(self.Reserved1)
        br.write_uint16(self.Reserved2)
        br.write_uint32(self.OffsetToPixelData)


class bmpDIBHeader(BrStruct):
    def __init__(self):
        self.Size = 0
        self.Width = 0
        self.Height = 0
        self.ColorPlanes = 0
        self.BitsPerPixel = 0
        self.Compression = 0
        self.ImageSize = 0
        self.HorizontalResolution = 0
        self.VerticalResolution = 0
        self.ColorsInColorTable = 0
        self.ImportantColors = 0


    def __br_read__(self, br: BinaryReader):
        self.Size = br.read_uint32()
        self.Width = br.read_uint32()
        self.Height = br.read_uint32()
        self.ColorPlanes = br.read_uint16()
        self.BitsPerPixel = br.read_uint16()
        self.Compression = br.read_uint32()
        self.ImageSize = br.read_uint32()
        self.HorizontalResolution = br.read_uint32()
        self.VerticalResolution = br.read_uint32()
        self.ColorsInColorTable = br.read_uint32()
        self.ImportantColors = br.read_uint32()


    def __br_write__(self, br: BinaryReader):
        br.write_uint32(self.Size)
        br.write_uint32(self.Width)
        br.write_uint32(self.Height)
        br.write_uint16(self.ColorPlanes)
        br.write_uint16(self.BitsPerPixel)
        br.write_uint32(self.Compression)
        br.write_uint32(self.ImageSize)
        br.write_uint32(self.HorizontalResolution)
        br.write_uint32(self.VerticalResolution)
        br.write_uint32(self.ColorsInColorTable)
        br.write_uint32(self.ImportantColors)


class bmpColorTable(BrStruct):
    def __init__(self):
        self.Colors = []


    def __br_read__(self, br: BinaryReader):
        for i in range(0, 256):
            self.Colors.append(br.read_uint8(4))


    def __br_write__(self, br: BinaryReader):
        for i in range(0, 256):
            br.write_uint8(self.Colors[i])


def bmpBGRtoRGB(bmp: BMP):
    pixels = bmp.PixelData

    #construct RGB pixels and flip vertically
    newPixels = bytearray()
    for y in range(bmp.DIBHeader.Height - 1, -1, -1):
        for x in range(0, bmp.DIBHeader.Width):
            newPixels.append(pixels[y * bmp.DIBHeader.Width * 3 + x * 3 + 2])
            newPixels.append(pixels[y * bmp.DIBHeader.Width * 3 + x * 3 + 1])
            newPixels.append(pixels[y * bmp.DIBHeader.Width * 3 + x * 3 + 0])
    
    bmp.PixelData = newPixels

    return bmp


if __name__ == "__main__":
    path = r"D:\SteamLibrary\steamapps\common\Obscure\data\_common\textures\a_door.bmp"

    with open(path, "rb") as f:
        br = BinaryReader(f.read(), Endian.LITTLE, "cp932")
        
    bmp: BMP() = br.read_struct(BMP)

    '''bmp = bmpBGRtoRGB(bmp)

    #BGR
    img = Image.frombytes("RGB", (bmp.DIBHeader.Width, bmp.DIBHeader.Height), bmp.PixelData)
    #img = img.transpose(method=Image.FLIP_LEFT_RIGHT)
    img.show()'''


    '''with BinaryReader(Endian.LITTLE) as bw:
        bw.write_struct(bmp)
        with open(path.replace(".bmp", "1.bmp"), "wb") as f:
            f.write(bw.buffer())'''
