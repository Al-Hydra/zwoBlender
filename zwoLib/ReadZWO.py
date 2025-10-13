from .utils.PyBinaryReader.binary_reader import *
from enum import Enum
from .zwo.zwo import *

def read_zwo(filepath):
    with open(filepath, 'rb') as f:
        filebytes = f.read()
    
    br = BinaryReader(filebytes, Endian.BIG, encoding='cp1252')

    zwo: zwoFile = br.read_struct(zwoFile)
    return zwo
