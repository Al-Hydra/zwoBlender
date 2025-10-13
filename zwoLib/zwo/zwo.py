from ..utils.PyBinaryReader.binary_reader import *
from enum import Enum
from .zwoTypes import zwoTypes
from .zwoMaterial import zwoMaterial
from .zwoMesh import zwoMesh
from .zwoCamera import zwoCamera
from .zwoSkeleton import zwoSkeleton
from .zwoSkeletalAnimation import zwoSkeletalAnimation
from .zwoAnimation import zwoAnimation
from .zwoNode import zwoNode
import cProfile

class zwoFile(BrStruct):
    def __init__(self):
        self.Entities = []
    
    def __br_read__(self, br: BinaryReader):
            while not br.eof():
                EntityType = zwoTypes(br.read_uint32())
                if EntityType == zwoTypes.EOF:
                     break
                elif EntityType == zwoTypes.Camera:
                    self.Entities.append(br.read_struct(zwoCamera))

                elif EntityType == zwoTypes.Material:
                    self.Entities.append(br.read_struct(zwoMaterial))

                elif EntityType == zwoTypes.Mesh:
                    pos = br.pos()
                    try:
                        self.Entities.append(br.read_struct(zwoMesh))
                    except:
                        print(f"Error reading mesh at {pos}")
                        br.seek(pos, 0)
                        br.read_bytes(br.peek_uint32())

                elif EntityType == zwoTypes.Skeleton:
                    self.Entities.append(br.read_struct(zwoSkeleton))

                elif EntityType == zwoTypes.SkeletalAnimation:
                    self.Entities.append(br.read_struct(zwoSkeletalAnimation))

                elif EntityType == zwoTypes.CameraAnimation:
                    #self.Entities.append(br.read_struct(zwoCameraAnimation))
                    br.read_bytes(br.peek_uint32())

                elif EntityType == zwoTypes.Node:
                    #zwoNode is a special case, it doesn't have a size field so we have to read it manually
                    self.Entities.append(br.read_struct(zwoNode))

                elif EntityType == zwoTypes.Light:
                    #self.Entities.append(br.read_struct(zwoLight))
                    br.read_bytes(br.peek_uint32())

                elif EntityType == zwoTypes.Animation:
                    self.Entities.append(br.read_struct(zwoAnimation))

                elif EntityType == zwoTypes.LightAmbientBox:
                    #self.Entities.append(br.read_struct(zwoLightAmbientBox))
                    br.read_bytes(br.peek_uint32())
                
                elif EntityType == zwoTypes.OmniLight:
                    #self.Entities.append(br.read_struct(zwoOmniLight))
                    br.read_bytes(br.peek_uint32())
    

    def __br_write__(self, br: BinaryReader):
        for entity in self.Entities:
            br.write_uint32(entity.Type.value)
            br.write_struct(entity)
        br.write_uint32(zwoTypes.EOF.value)
                

if __name__ == "__main__":
    zwoPath = r"D:\SteamLibrary\steamapps\common\Obscure2\datapack.hvp_out\characters\boy1\skins\boy1_pc.zwo"
    with open(zwoPath, 'rb') as f:
        filebytes = f.read()

    br = BinaryReader(filebytes, Endian.BIG, encoding='cp932')

    #start profiler
    pr = cProfile.Profile()
    pr.enable()

    zwo: zwoFile = br.read_struct(zwoFile)

    pr.disable()
    pr.print_stats(sort='time')
