from enum import Enum

class zwoTypes(Enum):
    Camera = 0x02
    Material = 0x03
    EOF = 0x04
    Mesh = 0x05
    Skeleton = 0x06
    SkeletalAnimation = 0x07
    CameraAnimation = 0x09
    Node = 0x0A
    Light = 0x0D
    Animation = 0x0E
    LightAmbientBox = 0x0F
    OmniLight = 0x10