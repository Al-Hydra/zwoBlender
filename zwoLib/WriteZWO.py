from .utils.PyBinaryReader.binary_reader import *
from .zwo.zwo import *

def write_zwo(zwo: zwoFile, path):
    br = BinaryReader(encoding= "cp932", endianness= Endian.BIG)
    br.write_struct(zwo)
    with open(path, "wb") as f:
        f.write(br.buffer())
