from .PyBinaryReader.binary_reader import *
from enum import Enum
from zlib import crc32
class PNG(BrStruct):
    def __init__(self):
        self.Signature = b'\x89PNG\r\n\x1a\n'
        self.Chunks = []

    def __br_read__(self, br: BinaryReader, *args):
        self.Signature = br.read_bytes(8)
        while not br.eof():
            self.Chunks.append(br.read_struct(PNG_Chunk))

    def __br_write__(self, br: BinaryReader, *args):
        br.write_bytes(self.Signature)
        for chunk in self.Chunks:
            br.write_struct(chunk)


class PNG_Chunk(BrStruct):
    def __init__(self):
        self.Length = 0
        self.Type = 0
        self.Data = None
        self.CRC = 0

    def __br_read__(self, br: BinaryReader, *args):
        self.Length = br.read_uint32()
        self.Type = br.read_str(4)

        #read the correct struct based on the type
        self.Data = br.read_struct(globals()[self.Type], None, self.Length)

        self.CRC = br.read_uint32()

    def __br_write__(self, br: BinaryReader, *args):

        #write the chunk data first to get its size
        datbr = BinaryReader(bytearray(), Endian.BIG)
        datbr.write_str(self.Type)
        datbr.write_struct(self.Data)

        br.write_uint32(datbr.size() - 4)

        br.extend(datbr.buffer())
        br.seek(datbr.size(), 1)

        br.write_uint32(crc32(datbr.buffer()))


class IHDR(PNG_Chunk):
    def __init__(self):
        self.Width = 0
        self.Height = 0
        self.BitDepth = 0
        self.ColorType = 0
        self.CompressionMethod = 0
        self.FilterMethod = 0
        self.InterlaceMethod = 0

    def __br_read__(self, br: BinaryReader, *args):
        self.Width = br.read_uint32()
        self.Height = br.read_uint32()
        self.BitDepth = br.read_uint8()
        self.ColorType = br.read_uint8()
        self.CompressionMethod = br.read_uint8()
        self.FilterMethod = br.read_uint8()
        self.InterlaceMethod = br.read_uint8()

    def __br_write__(self, br: BinaryReader, *args):
        br.write_uint32(self.Width)
        br.write_uint32(self.Height)
        br.write_uint8(self.BitDepth)
        br.write_uint8(self.ColorType)
        br.write_uint8(self.CompressionMethod)
        br.write_uint8(self.FilterMethod)
        br.write_uint8(self.InterlaceMethod)


class PLTE(PNG_Chunk):
    def __init__(self):
        self.Palette = []

    def __br_read__(self, br: BinaryReader, *args):
        pass

    def __br_write__(self, br: BinaryReader, *args):
        pass


class IDAT(PNG_Chunk):
    def __init__(self):
        self.ImageData = None

    def __br_read__(self, br: BinaryReader, length: int):
        self.ImageData = br.read_bytes(length)

    
    def __br_write__(self, br: BinaryReader, *args):
        br.write_bytes(self.ImageData)
        if len(self.ImageData) % 8 != 0:
            br.align(8)


class IEND(PNG_Chunk):
    def __init__(self):
        pass

    def __br_read__(self, br: BinaryReader, length: int):
        pass

    def __br_write__(self, br: BinaryReader, *args):
        pass

class cHRM(PNG_Chunk):
    def __init__(self):
        self.WhitePointX = 0
        self.WhitePointY = 0
        self.RedX = 0
        self.RedY = 0
        self.GreenX = 0
        self.GreenY = 0
        self.BlueX = 0
        self.BlueY = 0

    def __br_read__(self, br: BinaryReader, *args):
        self.WhitePointX = br.read_uint32()
        self.WhitePointY = br.read_uint32()
        self.RedX = br.read_uint32()
        self.RedY = br.read_uint32()
        self.GreenX = br.read_uint32()
        self.GreenY = br.read_uint32()
        self.BlueX = br.read_uint32()
        self.BlueY = br.read_uint32()

    def __br_write__(self, br: BinaryReader, *args):
        br.write_uint32(self.WhitePointX)
        br.write_uint32(self.WhitePointY)
        br.write_uint32(self.RedX)
        br.write_uint32(self.RedY)
        br.write_uint32(self.GreenX)
        br.write_uint32(self.GreenY)
        br.write_uint32(self.BlueX)
        br.write_uint32(self.BlueY)


class gAMA(PNG_Chunk):
    def __init__(self):
        self.Gamma = 0

    def __br_read__(self, br: BinaryReader, *args):
        self.Gamma = br.read_uint32()

    def __br_write__(self, br: BinaryReader, *args):
        br.write_uint32(self.Gamma)


class iCCP(PNG_Chunk):
    def __init__(self):
        self.ProfileName = None
        self.CompressionMethod = 0
        self.CompressedProfile = None

    def __br_read__(self, br: BinaryReader, *args):
        self.ProfileName = br.read_str()
        self.CompressionMethod = br.read_uint8()
        self.CompressedProfile = br.read_bytes()

    def __br_write__(self, br: BinaryReader, *args):
        br.write_str(self.ProfileName)
        br.write_uint8(self.CompressionMethod)
        br.write_bytes(self.CompressedProfile)


class sBIT(PNG_Chunk):
    def __init__(self):
        self.ColorType = 0
        self.GreyscaleBits = 0
        self.RedBits = 0
        self.GreenBits = 0
        self.BlueBits = 0
        self.AlphaBits = 0

    def __br_read__(self, br: BinaryReader, *args):
        self.ColorType = br.read_uint8()
        self.GreyscaleBits = br.read_uint8()
        self.RedBits = br.read_uint8()
        self.GreenBits = br.read_uint8()
        self.BlueBits = br.read_uint8()
        self.AlphaBits = br.read_uint8()

    def __br_write__(self, br: BinaryReader, *args):
        br.write_uint8(self.ColorType)
        br.write_uint8(self.GreyscaleBits)
        br.write_uint8(self.RedBits)
        br.write_uint8(self.GreenBits)
        br.write_uint8(self.BlueBits)
        br.write_uint8(self.AlphaBits)


class sRGB(PNG_Chunk):
    def __init__(self):
        self.RenderingIntent = 0

    def __br_read__(self, br: BinaryReader, *args):
        self.RenderingIntent = br.read_uint8()

    def __br_write__(self, br: BinaryReader, *args):
        br.write_uint8(self.RenderingIntent)


class bKGD(PNG_Chunk):
    def __init__(self):
        self.ColorType = 0
        self.Greyscale = 0
        self.Red = 0
        self.Green = 0
        self.Blue = 0

    def __br_read__(self, br: BinaryReader, *args):
        self.ColorType = br.read_uint8()
        self.Greyscale = br.read_uint16()
        self.Red = br.read_uint16()
        self.Green = br.read_uint16()
        self.Blue = br.read_uint16()

    def __br_write__(self, br: BinaryReader, *args):
        br.write_uint8(self.ColorType)
        br.write_uint16(self.Greyscale)
        br.write_uint16(self.Red)
        br.write_uint16(self.Green)
        br.write_uint16(self.Blue)


class hIST(PNG_Chunk):
    def __init__(self):
        self.Histogram = []

    def __br_read__(self, br: BinaryReader, *args):
        pass

    def __br_write__(self, br: BinaryReader, *args):
        pass


class tRNS(PNG_Chunk):
    def __init__(self):
        self.ColorType = 0
        self.Greyscale = 0
        self.Red = 0
        self.Green = 0
        self.Blue = 0

    def __br_read__(self, br: BinaryReader, *args):
        self.ColorType = br.read_uint8()
        self.Greyscale = br.read_uint16()
        self.Red = br.read_uint16()
        self.Green = br.read_uint16()
        self.Blue = br.read_uint16()

    def __br_write__(self, br: BinaryReader, *args):
        br.write_uint8(self.ColorType)
        br.write_uint16(self.Greyscale)
        br.write_uint16(self.Red)
        br.write_uint16(self.Green)
        br.write_uint16(self.Blue)


class pHYs(PNG_Chunk):
    def __init__(self):
        self.PixelsPerUnitX = 0
        self.PixelsPerUnitY = 0
        self.Unit = 0

    def __br_read__(self, br: BinaryReader, *args):
        self.PixelsPerUnitX = br.read_uint32()
        self.PixelsPerUnitY = br.read_uint32()
        self.Unit = br.read_uint8()

    def __br_write__(self, br: BinaryReader, *args):
        br.write_uint32(self.PixelsPerUnitX)
        br.write_uint32(self.PixelsPerUnitY)
        br.write_uint8(self.Unit)


class sPLT(PNG_Chunk):
    def __init__(self):
        self.PaletteName = None
        self.SampleDepth = 0
        self.Entries = []

    def __br_read__(self, br: BinaryReader, *args):
        self.PaletteName = br.read_str()
        self.SampleDepth = br.read_uint8()
        self.Entries = []

    def __br_write__(self, br: BinaryReader, *args):
        br.write_str(self.PaletteName)
        br.write_uint8(self.SampleDepth)
        br.write_bytes(self.Entries)


class tIME(PNG_Chunk):
    def __init__(self):
        self.Year = 0
        self.Month = 0
        self.Day = 0
        self.Hour = 0
        self.Minute = 0
        self.Second = 0

    def __br_read__(self, br: BinaryReader, *args):
        self.Year = br.read_uint16()
        self.Month = br.read_uint8()
        self.Day = br.read_uint8()
        self.Hour = br.read_uint8()
        self.Minute = br.read_uint8()
        self.Second = br.read_uint8()

    def __br_write__(self, br: BinaryReader, *args):
        br.write_uint16(self.Year)
        br.write_uint8(self.Month)
        br.write_uint8(self.Day)
        br.write_uint8(self.Hour)
        br.write_uint8(self.Minute)
        br.write_uint8(self.Second)


class tEXt(PNG_Chunk):
    def __init__(self):
        self.Keyword = None
        self.Text = None

    def __br_read__(self, br: BinaryReader, *args):
        self.Keyword = br.read_str()
        self.Text = br.read_str()

    def __br_write__(self, br: BinaryReader, *args):
        br.write_str(self.Keyword)
        br.write_str(self.Text)


class zTXt(PNG_Chunk):
    def __init__(self):
        self.Keyword = None
        self.CompressionMethod = 0
        self.Text = None

    def __br_read__(self, br: BinaryReader, *args):
        self.Keyword = br.read_str()
        self.CompressionMethod = br.read_uint8()
        self.Text = br.read_str()

    def __br_write__(self, br: BinaryReader, *args):
        br.write_str(self.Keyword)
        br.write_uint8(self.CompressionMethod)
        br.write_str(self.Text)


class iTXt(PNG_Chunk):
    def __init__(self):
        self.Keyword = None
        self.CompressionFlag = 0
        self.CompressionMethod = 0
        self.LanguageTag = None
        self.TranslatedKeyword = None
        self.Text = None

    def __br_read__(self, br: BinaryReader, *args):
        self.Keyword = br.read_str()
        self.CompressionFlag = br.read_uint8()
        self.CompressionMethod = br.read_uint8()
        self.LanguageTag = br.read_str()
        self.TranslatedKeyword = br.read_str()
        self.Text = br.read_str()

    def __br_write__(self, br: BinaryReader, *args):
        br.write_str(self.Keyword)
        br.write_uint8(self.CompressionFlag)
        br.write_uint8(self.CompressionMethod)
        br.write_str(self.LanguageTag)
        br.write_str(self.TranslatedKeyword)
        br.write_str(self.Text)


if __name__ == '__main__':
    from PIL import Image
    import zlib
    path = r"C:\Users\Ali\Pictures\Screenshots\Screenshot 2023-04-30 112221.png"
    with open(path, "rb") as f:
        bytedata = f.read()
    br = BinaryReader(bytedata, Endian.BIG, "cp932")
    png = br.read_struct(PNG)

    width = png.Chunks[0].Data.Width
    height = png.Chunks[0].Data.Height
    print(width, height)

    PixelData = []

    for chunk in png.Chunks:
        if isinstance(chunk.Data, IDAT):
            PixelData.append(zlib.decompress(chunk.Data.ImageData))
    
    PixelData = b"".join(PixelData)

    img = Image.frombytes("RGBA", (width, height), PixelData)
    img.show()
