from .PyBinaryReader.binary_reader.binary_reader import BinaryReader, Endian

from .brDDS import BrDDS, BrDDS_Header, BrDDS_PixelFormat, BrDDS_DX10_Header


class DDS:
    def init_data(self, dds: BrDDS):
        self.magic = 'DDS '
        self.header = BrDDS_Header()
        self.header.init_data(dds.header)
        self.mipmaps = dds.mipmaps
        self.texture_data = dds.texture_data


class DDS_Header:
    def init_data(self, dds1: BrDDS_Header):
        self.size = dds1.size
        self.flags = dds1.flags
        self.height = dds1.height
        self.width = dds1.width
        self.pitchOrLinearSize = dds1.pitchOrLinearSize
        self.depth = dds1.depth
        self.mipmap_count = dds1.mipmap_count
        self.reserved = dds1.reserved
        self.pixel_format = dds1.pixel_format
        self.caps1 = dds1.caps1
        self.caps2 = dds1.caps2
        self.caps3 = dds1.caps3
        self.caps4 = dds1.caps4
        self.reserved2 = dds1.reserved2


class DDS_PixelFormat:
    def init_data(self, dds2: BrDDS_PixelFormat):
        self.size = dds2.size
        self.flags = dds2.flags
        self.fourCC = dds2.four_cc
        self.rgbBitCount = dds2.rgbBitCount
        self.bitmaks = dds2.bitmasks


class DDS_DX10_Header:
    def init_data(self, dds3: BrDDS_DX10_Header):
        self.dxgi_format = dds3.dxgi_format
        self.resource_dimension = dds3.resource_dimension
        self.misc_flag = dds3.misc_flag
        self.array_size = dds3.array_size
        self.misc_flags2 = dds3.misc_flags2


def read_dds_path(path):
    with open(path, 'rb') as f:
        file = f.read()

    with BinaryReader(file, Endian.LITTLE) as br:
        dds: BrDDS = br.read_struct(BrDDS)
    return dds

def read_dds(file):
    with BinaryReader(file, Endian.LITTLE) as br:
        dds: BrDDS = br.read_struct(BrDDS)
    return dds
