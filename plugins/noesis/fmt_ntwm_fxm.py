from inc_noesis import *
import os.path
import os

def registerNoesisTypes():
    handle = noesis.register( "Nosferatu The Wrath of Malachi (2003) model", ".fxm")

    noesis.setHandlerTypeCheck(handle, ntwmModelCheckType)
    noesis.setHandlerLoadModel(handle, ntwmModelLoadModel)
        
    return 1 
 

FXM_KEYPOSE = 1001
FXM = 1002
 
  
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


class Vector2F:
    def read(self, reader):
        self.x = reader.readFloat()
        self.y = reader.readFloat()
 
    def getStorage(self):
        return (self.x, self.y) 
        
 
class NTWMMeshVertex():
    def __init__(self):
        self.coordinates = Vector3F()
        self.normal = Vector3F()
        self.uv = Vector2F()
        
    def read(self, reader):
        self.coordinates.read(reader)
        self.normal.read(reader)  
        self.uv.read(reader)  
        
        
class NTWMMesh:
    def __init__(self):
        self.vertexes = []
        self.faceIndexes = []
        self.texturename = ""
        
    def read(self, reader, hasTextureData=True):
        if hasTextureData:
            length = reader.readUInt()
            self.textureName = reader.readBytes(length).decode("ascii")

            reader.seek(24, NOESEEK_REL)
        
        self.faceCount = reader.readUInt()
        self.vertexCount = reader.readUInt() 
        
        for faceIndex in range(self.faceCount):
            faceIndexes = Vector3UI16() 
            faceIndexes.read(reader)
            
            self.faceIndexes.append(faceIndexes)
            
        for vertexIndex in range(self.vertexCount):
            vertex = NTWMMeshVertex()
            vertex.read(reader)
            
            self.vertexes.append(vertex)            
 
 
class NTWMBone:
    def __init__(self):
        self.name = ""
        self.parentIndex = 0
        self.matrix = None
        
    def read(self, reader):
        reader.seek(8, NOESEEK_REL)    
        length = reader.readUInt()
        self.name = reader.readBytes(length).decode("ascii") 
        print(self.name)
        self.parentIndex = reader.readInt()           
        self.matrix = NoeMat44.fromBytes(reader.readBytes(64)).toMat43() 
        
            
class NTWMCharacterModel: 
    def __init__(self, reader):
        self.reader = reader
        self.meshes = []
        self.bones = []
        self.type = FXM
        
    def readHeader(self, reader):
        reader.seek(4, NOESEEK_REL)
        if reader.readUInt() == 1:
            self.type = FXM_KEYPOSE
            
        if self.type == FXM:    
            reader.seek(36, NOESEEK_REL) 
            self.meshCount = reader.readUInt()       
        
    def readBones(self, reader):
        count = reader.readUInt()       
        for i in range(count):
                bone = NTWMBone()
                bone.read(reader)
            
                self.bones.append(bone)                 
     
    def readMeshes(self, reader, hasTextureData=True):
        for i in range(self.meshCount):
            mesh = NTWMMesh()
            mesh.read(reader, hasTextureData)
        
            self.meshes.append(mesh)        
     
    def readVertexWeights(self, reader):
        pos = Vector3F()
        pos.read(reader)
        weightCount = reader.readUByte()
        reader.seek(3, NOESEEK_REL)
        
        weights = noeUnpack('4f', reader.readBytes(16))
        boneIndexes = noeUnpack('4b', reader.readBytes(4)) 

        reader.seek(20, NOESEEK_REL)        
     
    def readModelData(self, reader):
        if self.type == FXM: 
            self.readMeshes(reader)
        else:
            self.readBones(reader)

            reader.seek(44 + 4, NOESEEK_REL)
            length = reader.readUInt()
            self.name = reader.readBytes(length).decode("ascii")             
            reader.seek(24, NOESEEK_REL)
            
            self.meshCount = 1
            self.readMeshes(reader, False)            
            self.readVertexWeights(reader)     
        
    def read(self):
        self.readHeader(self.reader)         
        self.readModelData(self.reader)             
        
    
def ntwmModelCheckType(data):     
            
    return 1     
    

def ntwmModelLoadModel(data, mdlList): 
    ntwmModel = NTWMCharacterModel(NoeBitStream(data)) 
    ntwmModel.read()
    
    ctx = rapi.rpgCreateContext()
      
    materials = []
    textures = [] 
    
    if ntwmModel.type == FXM:
        for mesh in ntwmModel.meshes:     
            for extension in [".jpg", ".tga"]:
                filename = "{}/{}{}".format(noesis.getSelectedDirectory(), mesh.textureName, extension)
                if os.path.exists(filename):
                    textureName = mesh.textureName + extension
                    break
                
            texture = rapi.loadExternalTex(textureName)
  
            if texture == None:
                texture = NoeTexture(textureName, 0, 0, bytearray())

            textures.append(texture)            
            material = NoeMaterial(mesh.textureName, textureName)
            material.setFlags(noesis.NMATFLAG_TWOSIDED, 1)
            materials.append(material)      
      
    for mesh in ntwmModel.meshes:
        if ntwmModel.type == FXM: 
            rapi.rpgSetMaterial(mesh.textureName)  
            
        for faceIndex in mesh.faceIndexes:
            rapi.immBegin(noesis.RPGEO_TRIANGLE) 
            for index in faceIndex.getStorage():
                rapi.immUV2(mesh.vertexes[index].uv.getStorage())             
                rapi.immVertex3(mesh.vertexes[index].coordinates.getStorage())
            
            rapi.immEnd() 
                   
    mdl = rapi.rpgConstructModelSlim()
    
    # show skeleton
    bones = []
    index = 0
    
    for bone in ntwmModel.bones: 
        #if index < 6:
        if bone.parentIndex >= 0:
            boneMat = bone.matrix.inverse()
        else:         
            boneMat = bone.matrix 
        boneName = bone.name
        boneParentName = ntwmModel.bones[bone.parentIndex].name       
        bones.append(NoeBone(index, boneName, boneMat, boneParentName, bone.parentIndex))
    
        index += 1

    mdl.setBones(bones)    
    # set materials    
    mdl.setModelMaterials(NoeModelMaterials(textures, materials)) 
        
    mdlList.append(mdl)
    
    return 1