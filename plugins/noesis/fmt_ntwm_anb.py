from inc_noesis import *


def registerNoesisTypes():
    handle = noesis.register( "Nosferatu The Wrath of Malachi (2003) model", ".anb")

    noesis.setHandlerTypeCheck(handle, ntwmModelCheckType)
    noesis.setHandlerLoadModel(handle, ntwmModelLoadModel)
    noesis.setHandlerWriteModel(handle, ntwmModelWriteModel)
    
    return 1 
   
   
class Vector3UI16:
    def read(self, reader):
        self.x = reader.readShort()
        self.y = reader.readShort()
        self.z = reader.readShort()
        
    def getStorage(self):
        return (self.x, self.y, self.z)    
   
    def toBytes(self):
        result = bytearray()
        result += self.x.to_bytes(2, byteorder='little')
        result += self.y.to_bytes(2, byteorder='little')
        result += self.z.to_bytes(2, byteorder='little')
        
        return result 
        
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
        
    def toBytes(self):
        result = bytearray()
        result += bytearray(struct.pack("f", self.x))
        result += bytearray(struct.pack("f", self.y))
        return result           
        
    
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
            uvCoordinates = Vector2F() 
            uvCoordinates.read(reader)
            
            self.uvCoordinates.append(uvCoordinates)
            
        for uvIndex in range(self.faceCount):
            uvIndexes = Vector3UI16() 
            uvIndexes.read(reader)
            
            self.uvIndexes.append(uvIndexes)
 
 
class NTWMFrameMesh: 
    def __init__(self): 
        self.positions = bytearray()    
        self.normals = bytearray()
        
class NTWMMorphFrame:
    def __init__(self):
        self.frameMeshes = []      
        
            
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
            frameMesh = NTWMFrameMesh()
            for vertexIndex in range(mesh.vertexCount):
                coordinates = Vector3F()
                coordinates.read(reader)
                normal = Vector3F()
                normal.read(reader)  

                frameMesh.positions += coordinates.toBytes()
                frameMesh.normals += normal.toBytes()                
            
            morphFrame.frameMeshes.append(frameMesh)
               
        return morphFrame 
            
    def readMorphFrames(self, reader):   
        for frameIndex in range(self.morphFrameCount - 1):         
            self.morphFrames.append(self.readFrame(reader))  
            
    def read(self):
        self.readHeader(self.reader)         
        self.readModelData(self.reader)       
        self.readMorphFrames(self.reader)       
    
    
def ntwmModelCheckType(data):     
            
    return 1     
    
    
# ToDo: texture coordinates
def ntwmModelLoadModel(data, mdlList): 
    ntwmModel = NTWMCharacterModel(NoeBitStream(data)) 
    ntwmModel.read()
    
    ctx = rapi.rpgCreateContext()

    materials = []
    textures = [] 
    textureName = ""
            
    textureName = "F:/Games/Nosferatu - The Wrath of Malachi/Version/Data/corpse.jpg"        
    texture = rapi.loadExternalTex(textureName)

    if texture == None:
        texture = NoeTexture(textureName, 0, 0, bytearray())

    textures.append(texture)            
    material = NoeMaterial(textureName, textureName)
    material.setFlags(noesis.NMATFLAG_TWOSIDED, 1)
    materials.append(material)     
          
    noesis.logPopup()
    
    index = 0     
    for mesh in ntwmModel.meshes:
        rapi.rpgSetMaterial(textureName)   
        rapi.rpgSetName("mesh " + str(index))
        
        # for i in range(len(mesh.facesIndexes)):               
            # rapi.immBegin(noesis.RPGEO_TRIANGLE)
            
            # for idx in range(3):
                # uvIndex = mesh.uvIndexes[i].getStorage()[idx] 
                # rapi.immUV2(mesh.uvCoordinates[uvIndex].getStorage())  
                # vertexIndex = mesh.facesIndexes[i].getStorage()[idx]                                 
                # rapi.immVertex3(mesh.vertexCoordinates[vertexIndex].getStorage())                   
                
            # rapi.immEnd()       
       
        positions = bytearray() 
        for vertex in mesh.vertexCoordinates:
            positions += vertex.toBytes()
            
        uvs = bytearray() 
        for uvIndexes in mesh.uvIndexes:
            uvs += uvIndexes.toBytes()        
        for uvIndexes in mesh.uvIndexes:        
            for i in uvIndexes.getStorage():
                uvs += mesh.uvCoordinates[i].toBytes()   
            
        triangles = bytearray() 
        for triangle in mesh.facesIndexes:
            triangles += triangle.toBytes()        
                  
        rapi.rpgBindPositionBuffer(positions, noesis.RPGEODATA_FLOAT, 12)      
        #rapi.rpgBindUV1Buffer(uvs, noesis.RPGEODATA_FLOAT, 8) 
        
        for frame in ntwmModel.morphFrames:
            frameMesh = frame.frameMeshes[index]
            rapi.rpgFeedMorphTargetPositions(frameMesh.positions, noesis.RPGEODATA_FLOAT, 12)
            rapi.rpgFeedMorphTargetNormals(frameMesh.normals, noesis.RPGEODATA_FLOAT, 12)
            rapi.rpgCommitMorphFrame(len(frameMesh.positions) // 12)
            
        rapi.rpgCommitMorphFrameSet()
        
        rapi.rpgCommitTriangles(triangles, noesis.RPGEODATA_USHORT, len(mesh.facesIndexes)*3, noesis.RPGEO_TRIANGLE, 1)
        rapi.rpgClearBufferBinds()
        
        index += 1
        
    rapi.rpgOptimize()
    
    mdl = rapi.rpgConstructModelSlim()
    
    mdl.setModelMaterials(NoeModelMaterials(textures, materials)) 
    
    mdlList.append(mdl)
    
    return 1 
 

def ntwmModelWriteModel(mdl, bs): 
    # writing header
    bs.writeInt(len(mdl.meshes[0].morphList)) # number of frames
    bs.writeInt(len(mdl.meshes)) # number of meshes
    
    # meshes
    for mesh in mdl.meshes:        
        bs.writeInt(len(mesh.positions))
        bs.writeInt(len(mesh.uvs))
        bs.writeInt(len(mesh.indices)//3)        

        for i in range(len(mesh.positions)):
            bs.writeBytes(mesh.positions[i].toBytes())               
            bs.writeBytes(mesh.normals[i].toBytes())            
        for idx in mesh.indices:
            bs.writeShort(idx)
        for vcmp in mesh.uvs:
            bs.writeBytes(vcmp.toBytes()[0:8])
        for idx in mesh.indices:
            bs.writeShort(idx)
            
    # morphs 
    for frameIndex in range(len(mdl.meshes[0].morphList)):  
        for mesh in mdl.meshes:       
            mf = mesh.morphList[frameIndex]
            for i in range(len(mf.positions)):      
                bs.writeBytes(mf.positions[i].toBytes())                  
                bs.writeBytes(mf.normals[i].toBytes())
    
   
    return 1