from .PyBinaryReader.binary_reader import *
from .dds import DDS, DDS_Header, DDS_PixelFormat
from .brDDS import BrDDS
from enum import Enum
import sys
import os

def read_tex_dictionary(file_path: str):
    #check file extension
    ext = file_path.split(".")[-1]
    if ext == "dic":
        with open(file_path, 'rb') as f:
            br = BinaryReader(f.read(), Endian.BIG, "cp932")
            dic = br.read_struct(dicFile)
            return dic
        
    elif ext == "dip":
        with open(file_path, 'rb') as f:
            br = BinaryReader(f.read(), Endian.LITTLE, "cp932")
            dip = br.read_struct(dipFile)
            return dip
        
    else:
        print("Unknown type")
        return None

    

class dicFile(BrStruct):
    def __init__(self):
        self.TexturesCount = 0
        self.Textures = []
    
    def __br_read__(self, br: BinaryReader):
        self.TexturesCount = br.read_uint32()
        print(self.TexturesCount)
        if self.TexturesCount > 1000000:
            print("Invalid dic file")
            br.set_endian(Endian.LITTLE)
            br.seek(0)
            self.TexturesCount = br.read_uint32()
            print(self.TexturesCount)

        self.Textures = br.read_struct(dicTexture, self.TexturesCount)

    def __br_write__(self, br: BinaryReader):
        br.write_uint32(self.TexturesCount)
        br.write_struct(self.Textures)


class dicTexture(BrStruct):
    def __init__(self):
        self.Name = ""
        self.Width = 0
        self.Height = 0
        self.Format = 0
        self.AlphaFlag = 0
        self.OneBitAlphaFlag = 0
        self.MipmapsCount = 0
        self.Mipmaps = []
        self.Data = None
    
    def __br_read__(self, br: BinaryReader):
        br.seek(4, 1)
        self.Name = br.read_str(br.read_uint32())

        self.MipmapsCount = br.read_uint32()
        self.AlphaFlag = br.read_uint32()
        self.OneBitAlphaFlag = br.read_uint32()
        self.Width = br.read_uint32()
        self.Height = br.read_uint32()
        self.Format = TextureFormats(br.read_uint32())
        for i in range(self.MipmapsCount):
            mipmapSize = br.read_uint32()
            self.Mipmaps.append(br.read_bytes(mipmapSize))
        
        self.Data = self.Mipmaps[0]
    
    def __br_write__(self, br: BinaryReader):
        br.write_uint32(0)
        br.write_uint32(len(self.Name))
        br.write_str(self.Name)
        br.write_uint32(self.MipmapsCount)
        br.write_uint32(self.AlphaFlag)
        br.write_uint32(self.OneBitAlphaFlag)
        br.write_uint32(self.Width)
        br.write_uint32(self.Height)
        br.write_uint32(self.Format.value)
        for mipmap in self.Mipmaps:
            br.write_uint32(len(mipmap))
            br.write_bytes(mipmap)


class dipFile(BrStruct):
    def __init__(self):
        self.TexturesCount = 0
        self.Textures = []
    
    def __br_read__(self, br: BinaryReader):
        br.seek(4, 1)
        self.TexturesCount = br.read_uint32()

        self.Textures = br.read_struct(dicTexture, self.TexturesCount)

    def __br_write__(self, br: BinaryReader):
        br.write_uint32(0)
        br.write_uint32(self.TexturesCount)
        br.write_struct(self.Textures)

        
class TextureFormats(Enum):
    R8G8B8A8 = 0x15
    R5G6B5 = 0x17
    R5G5B5A1 = 0x19


BitMasks = {
    TextureFormats.R8G8B8A8: [0x00ff0000, 0x0000ff00, 0x000000ff, 0xff000000],
    TextureFormats.R5G6B5: [0x0000f800, 0x000007e0, 0x0000001f, 0x00000000],
    TextureFormats.R5G5B5A1: [0x00007c00, 0x000003e0, 0x0000001f, 0x00008000]
}


BitCount = {
    TextureFormats.R8G8B8A8: 32,
    TextureFormats.R5G6B5: 16,
    TextureFormats.R5G5B5A1: 16
}


def dic2dds(dic: dicTexture):
    dds = DDS()
    dds.magic = 'DDS '
    header = dds.header = DDS_Header()
    header.pixel_format = DDS_PixelFormat()
    header.size = 124
    # DDSD_CAPS | DDSD_HEIGHT | DDSD_WIDTH | DDSD_PIXELFORMAT
    header.flags = 0x1 | 0x2 | 0x4 | 0x1000

    header.width = dic.Width
    header.height = dic.Height
    header.mipMapCount = dic.MipmapsCount

    # check dic format
    header.flags |= 0x8  # DDSD_PITCH
    header.pitchOrLinearSize = dic.Width * BitCount[dic.Format]
    header.pixel_format.fourCC = None
    header.pixel_format.rgbBitCount = BitCount[dic.Format]
    header.pixel_format.bitmasks = BitMasks[dic.Format]
    header.pixel_format.flags = 0x40 # DDPF_RGB
    if dic.AlphaFlag:
        header.pixel_format.flags |= 0x01 #DDPF_ALPHAPIXELS
    
    dds.mipmaps = dic.Mipmaps

    dds.texture_data = dic.Data

    header.pixel_format.size = 32
    if header.mipMapCount > 1:
        header.flags |= 0x20000  # DDSD_MIPMAPCOUNT
    header.caps1 = 0x8 | 0x1000 | 0x400000 

    header.depth = 1
    header.reserved = [0] * 11
    header.caps2 = 0
    header.caps3 = 0
    header.caps4 = 0
    header.reserved2 = 0

    br = BinaryReader(endianness=Endian.LITTLE)
    br.write_struct(BrDDS(), dds)
    return br.buffer()


def dic2ddso(dic: dicTexture):
    dds = DDS()
    dds.magic = 'DDS '
    header = dds.header = DDS_Header()
    header.pixel_format = DDS_PixelFormat()
    header.size = 124
    # DDSD_CAPS | DDSD_HEIGHT | DDSD_WIDTH | DDSD_PIXELFORMAT
    header.flags = 0x1 | 0x2 | 0x4 | 0x1000

    header.width = dic.Width
    header.height = dic.Height
    header.mipMapCount = dic.MipmapsCount

    # check dic format
    header.flags |= 0x8  # DDSD_PITCH
    header.pitchOrLinearSize = dic.Width * BitCount[dic.Format]
    header.pixel_format.fourCC = None
    header.pixel_format.rgbBitCount = BitCount[dic.Format]
    header.pixel_format.bitmasks = BitMasks[dic.Format]
    header.pixel_format.flags = 0x40 # DDPF_RGB
    if dic.AlphaFlag:
        header.pixel_format.flags |= 0x01 #DDPF_ALPHAPIXELS
    
    if dic.OneBitAlphaFlag:
        header.pixel_format.flags |= 0x02 #DDPF_ALPHA
    
    dds.mipmaps = dic.Mipmaps

    dds.texture_data = dic.Data

    header.pixel_format.size = 32
    if header.mipMapCount > 1:
        header.flags |= 0x20000  # DDSD_MIPMAPCOUNT
        header.caps1 = 0x8 | 0x1000 | 0x400000
    else:
        header.caps1 = 0x8
    
    header.depth = 1
    header.reserved = [0] * 11
    header.caps2 = 0
    header.caps3 = 0
    header.caps4 = 0
    header.reserved2 = 0

    return dds


def rgb565_to_rgb888(data, order = "BGR"):
    pixels = []
    if order == "BGR":
        for i in range(0, len(data), 2):
            b = data[i] & 0x1f
            g = ((data[i] & 0xe0) >> 5) | ((data[i + 1] & 0x07) << 3)
            r = (data[i + 1] & 0xf8) >> 3
            pixels.append((r, g, b))
    elif order == "RGB":
        for i in range(0, len(data), 2):
            r = data[i] & 0x1f
            g = ((data[i] & 0xe0) >> 5) | ((data[i + 1] & 0x07) << 3)
            b = (data[i + 1] & 0xf8) >> 3
            pixels.append((r, g, b))
    return pixels


def dic2dds_file(dic: dicTexture, filepath):
    print("Converting", dic.Name, "to DDS")
    dds = dic2dds(dic)
    name = dic.Name
    
    #check if folder exists
    if not os.path.exists(filepath):
        os.makedirs(filepath)
    
    path = os.path.join(filepath, name + ".dds")

    with open(path, 'wb') as f:
        f.write(dds)


def dds2dic(file_path):
    #read dds
    with open(file_path, 'rb') as f:
        br = BinaryReader(f.read(), Endian.LITTLE, "cp932")
        dds = br.read_struct(BrDDS)

    dicTex = dicTexture()
    dicTex.Name = os.path.basename(file_path).split(".")[0]

    dds_header: DDS_Header = dds.header
    pixel_format: DDS_PixelFormat = dds_header.pixel_format
    
    #check for alpha flag
    if pixel_format.flags & 0x01:
        dicTex.AlphaFlag = 1
    else:
        dicTex.AlphaFlag = 0

    #check for one bit alpha flag
    if pixel_format.flags & 0x02:
        dicTex.OneBitAlphaFlag = 1
    else:
        dicTex.OneBitAlphaFlag = 0

    #check the dds format
    if pixel_format.flags & 0x40 and pixel_format.flags & 1 and pixel_format.rgbBitCount == 16:
        dicTex.Format = TextureFormats.R5G5B5A1
    elif pixel_format.flags & 0x40 and pixel_format.rgbBitCount == 32:
        dicTex.Format = TextureFormats.R8G8B8A8
    elif pixel_format.flags & 0x40 and pixel_format.rgbBitCount == 16:
        dicTex.Format = TextureFormats.R5G6B5
    
    print(f"Format: {pixel_format.rgbBitCount} {dicTex.Format}")
        
    dicTex.Width = dds_header.width
    dicTex.Height = dds_header.height
    dicTex.MipmapsCount = dds_header.mipMapCount

    #check for mipmaps
    if dds_header.mipMapCount > 1:
        dicTex.Mipmaps = dds.mipmaps
    else:
        dicTex.Mipmaps = [dds.texture_data]

    dicTex.Data = dicTex.Mipmaps[0]

    return dicTex



def dic2bmp(dic: dicTexture):
    bmp = BMP()

    bmp.Header.FileSize = 0
    bmp.Header.Reserved1 = 0
    bmp.Header.Reserved2 = 0
    bmp.Header.OffsetToPixelData = 0x36

    bmp.DIBHeader.Size = 0x28
    bmp.DIBHeader.Width = dic.Width
    bmp.DIBHeader.Height = dic.Height
    bmp.DIBHeader.Planes = 1
    bmp.DIBHeader.BitCount = BitCount[dic.Format]
    bmp.DIBHeader.Compression = 0
    bmp.DIBHeader.ImageSize = 0
    bmp.DIBHeader.XPelsPerMeter = 0
    bmp.DIBHeader.YPelsPerMeter = 0
    bmp.DIBHeader.ColorsUsed = 0
    bmp.DIBHeader.ColorsImportant = 0

    bmp.PixelData = dic.Data



def dump_tex_dict(tex_dict: dicFile, folder):

    if tex_dict:
        if not os.path.exists(folder):
            os.makedirs(folder)

        for tex in tex_dict.Textures:
            print("Converting", tex.Name, "to DDS")
            dic2dds_file(tex, folder)
        
        print(f"Textures dumped to {folder}")
        input("Press enter to exit...")
    else:
        print("Error: No textures found")
        input("Press enter to exit...")


def repack_tex_dict(folder, dict_format):
    #check for dds files inside
    
    folder_name = os.path.basename(folder)
    parent_folder = os.path.dirname(folder)
    
    dds_files = []
    dict_textures = []
    for file in os.listdir(folder):
        if file.endswith(".dds"):
            dds_files.append(file)

    if len(dds_files) > 0:
        for file in dds_files:
            print("Converting", file, "to DIC")
            dict_textures.append(dds2dic(os.path.join(path, file)))

        #create dic file
        if dict_format == "1":
            dic = dipFile()
        else:
            dic = dicFile()
        dic.TexturesCount = len(dict_textures)
        dic.Textures = dict_textures

        if dict_format == "1":
            dict_name = f"{folder_name}.dip"
            #write dip file
            with open(os.path.join(parent_folder, dict_name), 'wb') as f:
                br = BinaryReader(endianness=Endian.LITTLE)
                br.write_struct(dic)
                f.write(br.buffer())
        else:
            dict_name = f"{folder_name}.dic"
        
            #write dic file
            with open(os.path.join(parent_folder, dict_name), 'wb') as f:
                br = BinaryReader(endianness=Endian.BIG)
                br.write_struct(dic)
                f.write(br.buffer())
    
        input("Press enter to exit...")
    else:
        print("No dds files found")
        input("Press enter to exit...")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        
        path = sys.argv[1]
        if os.path.isfile(path):
            #read dic file
            dic = read_tex_dictionary(path)
            if dic:
                dump_folder = os.path.dirname(path)
                dump_folder = os.path.join(dump_folder, os.path.basename(path).split(".")[0])
                #dump dic
                dump_tex_dict(dic, dump_folder)
    
    #repack mode
    # if the input is a folder check for dds files inside and repack them
    #check if the input is a file or folder

        elif os.path.isdir(path):
            dict_format = input("For Obscure 1 textures input 1, for Obscure 2 input 2: ")
            
            try:
                repack_tex_dict(path, dict_format)
            except Exception as e:
                print(e)
                input("Press enter to exit...")
        else:
            print("Invalid path")
            input("Press enter to exit...")