from .PyBinaryReader.binary_reader import *
from .brDDS import *
from .dds import *
from .bmp import *
from .png import *
from .tga import *
import zlib
import PIL

def BMPtoPNG(bmp: BMP):
    png: PNG = PNG()
    png.Signature = b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A'
    png.Chunks = []
    
    # Header
    HeaderChunk = PNG_Chunk()
    HeaderChunk.Length = 13
    HeaderChunk.Type = 'IHDR'

    pngHeader = HeaderChunk.Data = IHDR()
    pngHeader.Width = bmp.DIBHeader.Width
    pngHeader.Height = bmp.DIBHeader.Height
    pngHeader.BitDepth = 8
            
    pngHeader.ColorType = 2
    #set to zlib compression
    pngHeader.CompressionMethod = 0
    pngHeader.FilterMethod = 0
    pngHeader.InterlaceMethod = 0

    png.Chunks.append(HeaderChunk)

    DataChunk = PNG_Chunk()
    DataChunk.Length = 0
    DataChunk.Type = 'IDAT'

    pngData = DataChunk.Data = IDAT()
    pngData.ImageData = zlib.compress(bytes(bmp.PixelData), level=0)
    png.Chunks.append(DataChunk)

    #End
    EndChunk = PNG_Chunk()
    EndChunk.Length = 0
    EndChunk.Type = 'IEND'
    pngEnd = EndChunk.Data = IEND()

    png.Chunks.append(EndChunk)
    
    return png


def DDStoPNG(DDS: DDS):
    png = PNG()
    png.Signature = b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A'
    png.Chunks = []
    
    # Header
    HeaderChunk = PNG_Chunk()
    HeaderChunk.Length = 13
    HeaderChunk.Type = 'IHDR'

    pngHeader = HeaderChunk.Data = IHDR()
    pngHeader.Width = DDS.header.width
    pngHeader.Height = DDS.header.height
    pngHeader.BitDepth = 8

    pixels = bytearray()
    for i in range(0, len(DDS.texture_data), 4):
        pixels.append(DDS.texture_data[i+2])
        pixels.append(DDS.texture_data[i+1])
        pixels.append(DDS.texture_data[i])
        pixels.append(DDS.texture_data[i+3])
            

    pngHeader.ColorType = 6
    pngHeader.CompressionMethod = 0
    pngHeader.FilterMethod = 0
    pngHeader.InterlaceMethod = 0

    png.Chunks.append(HeaderChunk)

    #Data
    DataChunk = PNG_Chunk()
    DataChunk.Length = 0
    DataChunk.Type = 'IDAT'

    pngData = DataChunk.Data = IDAT()
    pngData.ImageData = bytes(pixels)
    png.Chunks.append(DataChunk)

    #End
    EndChunk = PNG_Chunk()
    EndChunk.Length = 0
    EndChunk.Type = 'IEND'
    pngEnd = EndChunk.Data = IEND()

    png.Chunks.append(EndChunk)
    
    return png


if __name__ == "__main__":
    '''path = r"D:\SteamLibrary\steamapps\common\Obscure\data\_common\textures\a_door.bmp"

    with open(path, "rb") as f:
        data = f.read()
    
    with BinaryReader(data, Endian.LITTLE, "cp932") as br:
        bmp = br.read_struct(BMP)

    png = BMPtoPNG(bmpBGRtoRGB(bmp))
    
    with BinaryReader(bytearray(), Endian.BIG, "cp932") as bw:
        bw.write_struct(png)
        pngData = bw.buffer()
    
    with open(path.replace(".bmp", ".png"), "wb") as f:
        f.write(pngData)'''
    

    '''path = r"D:\Games\Obscure 2\adatapack\characters\boy2\boy2_pc\b2_hair.dds"

    with open(path, "rb") as f:
        data = f.read()
    
    with BinaryReader(data, Endian.LITTLE, "cp932") as br:
        dds = br.read_struct(BrDDS)

    png = DDStoPNG(dds)
    
    with BinaryReader(bytearray(), Endian.BIG, "cp932") as bw:
        bw.write_struct(png)
        pngData = bw.buffer()
    
    with open(path.replace(".dds", ".png"), "wb") as f:
        f.write(pngData)'''
    
    