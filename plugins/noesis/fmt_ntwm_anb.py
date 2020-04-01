from inc_noesis import *


def registerNoesisTypes():
    handle = noesis.register( "Nosferatu The Wrath of Malachi (2003) model", ".anb")

    noesis.setHandlerTypeCheck(handle, ntwmModelCheckType)
    noesis.setHandlerLoadModel(handle, ntwmModelLoadModel)
        
    return 1 
   
   
class Vector3UI16:
    def read(self, reader):
        self.x = reader.readShort()
        self.y = reader.readShort()
        self.z = reader.readShort()
        
    def getStorage(self):
        return (self.x, self.y, self.z)    
   
   
class Vector3F:
    def read(self, reader):
        self.x = reader.readFloat()
        self.y = reader.readFloat()
        self.z = reader.readFloat() 
        
    def getStorage(self):
        return (self.x, self.y, self.z) 

    def toBytes(self):
        result = bytearray()
        result += bytearray(struct.pack("f", self.x))
        result += bytearray(struct.pack("f", self.y))
        result += bytearray(struct.pack("f", self.z))
        return result        


class Vector2F:
    def read(self, reader):
        self.x = reader.readFloat()
        self.y = reader.readFloat()
 
    def getStorage(self):
        return (self.x, self.y) 
        
    
class NTWMMesh:
    def __init__(self):
        self.vertexCoordinates = []
        self.facesIndexes = []
        self.uvIndexes = []
        self.uvCoordinates = []
        
    def read(self, reader):  
        self.vertexCount = reader.readUInt()
        self.uvCount = reader.readUInt()
        self.faceCount = reader.readUInt()
        
        for vertexIndex in range(self.vertexCount):
            coordinates = Vector3F()
            coordinates.read(reader)
            normal = Vector3F()
            normal.read(reader)  

            self.vertexCoordinates.append(coordinates)            
            
        for faceIndex in range(self.faceCount):
            faceIndexes = Vector3UI16() 
            faceIndexes.read(reader)
            
            self.facesIndexes.append(faceIndexes)
            
        for uvCoordIndex in range(self.uvCount):
            coordinates = Vector2F() 
            coordinates.read(reader)
            
            self.uvCoordinates.append(coordinates)
            
        for uvIndex in range(self.faceCount):
            uvIndexes = Vector3UI16() 
            uvIndexes.read(reader)
            
            self.uvIndexes.append(uvIndexes)
 
 
class NTWMMorphFrame:
    def __init__(self):
        self.positions = bytearray()    
        self.normals = bytearray()
        self.vertexCount = 0        
        
            
class NTWMCharacterModel: 
    def __init__(self, reader):
        self.reader = reader
        self.textures = []
        self.materials = []
        self.meshes = []
        self.morphFrames= []
        
    def readHeader(self, reader):
        self.morphFrameCount = reader.readUInt()
        self.meshCount = reader.readUInt()
        
    def readModelData(self, reader):
        for i in range(self.meshCount):
            mesh = NTWMMesh()
            mesh.read(reader)
            
            self.meshes.append(mesh)
            
    def readFrame(self, reader):
        morphFrame = NTWMMorphFrame()
        for mesh in self.meshes:
            for vertexIndex in range(mesh.vertexCount):
                coordinates = Vector3F()
                coordinates.read(reader)
                normal = Vector3F()
                normal.read(reader)  

                morphFrame.positions += coordinates.toBytes()
                morphFrame.normals += normal.toBytes()                
 
            morphFrame.vertexCount += mesh.vertexCount
               
        return morphFrame 
            
    def readMorphFrames(self, reader):   
        for frameIndex in range(self.morphFrameCount - 1):         
            self.morphFrames.append(self.readFrame(reader))  
            
    def read(self):
        #noesis.logPopup()
        self.readHeader(self.reader)         
        self.readModelData(self.reader)       
        self.readMorphFrames(self.reader)       
    
    
def ntwmModelCheckType(data):     
            
    return 1     
    

def ntwmModelLoadModel(data, mdlList): 
    ntwmModel = NTWMCharacterModel(NoeBitStream(data)) 
    ntwmModel.read()
    
    ctx = rapi.rpgCreateContext()
      
    for mesh in ntwmModel.meshes:
        for faceIndex in mesh.facesIndexes:
            rapi.immBegin(noesis.RPGEO_TRIANGLE) 
            
            for index in faceIndex.getStorage():
                rapi.immVertex3(mesh.vertexCoordinates[index].getStorage())
            
            rapi.immEnd()          

    # for frame in ntwmModel.morphFrames:
       # rapi.rpgFeedMorphTargetPositions(frame.positions, noesis.RPGEODATA_FLOAT, 12)
       # rapi.rpgFeedMorphTargetNormals(frame.normals, noesis.RPGEODATA_FLOAT, 12)
       # rapi.rpgCommitMorphFrame(len(frame.positions) // 12)
    
    # rapi.rpgCommitMorphFrameSet()       
    
    mdl = rapi.rpgConstructModelSlim()
    mdlList.append(mdl)
    
    return 1 