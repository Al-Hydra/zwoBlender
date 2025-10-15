from ..utils.PyBinaryReader.binary_reader import *
from .zwoEntity import zwoEntity
from .zwoEntity3D import zwoEntity3D
from .zwoTypes import zwoTypes
from .zwoHelpers import zwoVector, zwoQuaternion
import numpy as np


class zwoSkeletalAnimation(BrStruct):
    def __init__(self) -> None:
        self.Type = zwoTypes.SkeletalAnimation

    def __br_read__(self, br: BinaryReader, *args) -> None:
        
        self.Entity = br.read_struct(zwoEntity)
        self.Entity2 = br.read_struct(zwoEntity)

        self.Flags = br.read_uint32()
        flag1 = self.Flags >> 1 & 1
        flag2 = self.Flags >> 2 & 1

        self.EntryCount = br.read_uint32()
        self.FrameCount = br.read_uint32()
        self.FrameCountMultiplied = br.read_uint32()
        self.FrameRate = br.read_uint32()
        
        # set endian to little
        br.set_endian(Endian.LITTLE)
        
        if flag1 == 0:
            #self.Entries = np.frombuffer(br.read_bytes(self.EntryCount * 12), dtype=[('EntryTypeFlag', '<u4'), ('CurveStartIndex', '<u4'), ('CurvesPerFrame', '<u4')])
            #self.Entries = [Entry.from_dict(e) for e in self.Entries]
            self.Entries = [br.read_struct(Entry) for i in range(self.EntryCount)]
        else:
            br.read_bytes(14 * 4)
        
        br.set_endian(Endian.BIG)
        
        self.CurveCount = br.read_uint32()
        self.Curves = np.frombuffer(br.read_bytes(self.CurveCount * 16), dtype="<f").reshape(self.CurveCount, 4)
        
        #process curves
        curveIndex = 0
        
        for entry in self.Entries:
            entryType = entry.EntryTypeFlag
            curvesPerFrame = entry.CurvesPerFrame
            curveStartIndex = entry.CurveStartIndex

            if entryType & 1: # 1 frame pos, rot, scale
                entry.rotationCurves[0] = self.Curves[curveIndex]
                entry.positionCurves[0] = self.Curves[curveIndex + 1][:3]
                entry.scaleCurves[0] = self.Curves[curveIndex + 2][:3]
                curveIndex += 3
            
            if entryType == 3: # keyframed rot
                entry.rotationCurves.update({i: self.Curves[curveIndex + i - 1] for i in range(1, self.FrameCount)})
                curveIndex += self.FrameCount - 1
            
            if entryType == 5: # keyframed pos
                entry.positionCurves.update({i: self.Curves[curveIndex + i - 1][:3] for i in range(1, self.FrameCount)})
                curveIndex += self.FrameCount - 1
            if entryType == 7: # keyframed pos and rot
                
                #alternate between rot and pos
                for i in range(1, self.FrameCount):
                    entry.rotationCurves[i] = self.Curves[curveIndex]
                    entry.positionCurves[i] = self.Curves[curveIndex + 1][:3]
                    curveIndex += 2

        if self.Flags & 1:
            self.Transformer1Curve = (zwoVector(br), zwoVector(br), zwoQuaternion(br))

        if self.Flags & 4:
            self.Transformer2Curve = (zwoVector(br), zwoVector(br), zwoQuaternion(br))

class Entry(BrStruct):
    def __init__(self) -> None:
        self.EntryTypeFlag = 0
        self.CurveStartIndex = 0
        self.CurvesPerFrame = 0
        self.rotationCurves = {}
        self.positionCurves = {}
        self.scaleCurves = {}
        
    def __br_read__(self, br: BinaryReader, *args) -> None:
        
        self.EntryTypeFlag = br.read_uint32()
        self.CurveStartIndex = br.read_uint32()
        self.CurvesPerFrame = br.read_uint32()
        
