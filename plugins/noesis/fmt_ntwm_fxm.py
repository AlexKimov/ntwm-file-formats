from inc_noesis import *
import os.path
import os
import noewin
import noewinext

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

class Vector4F:
    def read(self, reader):
        self.x = reader.readFloat()
        self.y = reader.readFloat()
        self.z = reader.readFloat() 
        self.w = reader.readFloat()
        
    def getStorage(self):
        return (self.x, self.y, self.z, self.w)  
        

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
        self.textureName = ""
        
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
        self.parentIndex = reader.readInt()           
        self.matrix = NoeMat44.fromBytes(reader.readBytes(64)).toMat43() 


class NTWMVertexWeights:
    def __init__(self):
        self.count = 0
        self.weights = None
        self.boneIndexes = None
        
            
class NTWMCharacterModel: 
    def __init__(self, reader):
        self.reader = reader
        self.meshes = []
        self.bones = []
        self.weights = []
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
        for i in range(len(self.meshes[0].vertexes)):
            pos = Vector3F()
            pos.read(reader)
            weightCount = reader.readUByte()
            reader.seek(3, NOESEEK_REL)
        
            vertexWeights = NTWMVertexWeights()
            vertexWeights.count = weightCount
            
            count = weightCount - 1 if weightCount > 0 else 1
            vertexWeights.weights = noeUnpack('4f', reader.readBytes(16))[:count]
            vertexWeights.boneIndexes = noeUnpack('4b', reader.readBytes(4))[:count]

            self.weights.append(vertexWeights)
                  
            normal = Vector3F()
            normal.read(reader)
            uv = Vector2F()
            uv.read(reader) 
            
                  
    def readModelData(self, reader):
        if self.type == FXM: 
            self.readMeshes(reader)
        else:
            self.readBones(reader)

            if not self.bones:
                reader.seek(36, NOESEEK_REL)
            else:
                reader.seek(48, NOESEEK_REL)
            length = reader.readUInt()
            self.name = reader.readBytes(length).decode("ascii")             
            reader.seek(24, NOESEEK_REL)
            
            self.meshCount = 1
            self.readMeshes(reader, False)

            if self.bones:            
                self.readVertexWeights(reader)     
        
    def read(self):
        self.readHeader(self.reader)         
        self.readModelData(self.reader)             
   
   
class NTWMMotionKey:
    def __init__(self):
        time = 0
        motion = None
        
   
class NTWMBoneMotion:
    def __init__(self):
        self.rotationKeys = []
        self.positionKeys = []
        self.scaleKeys = []
        
    def read(self, reader):
        time = reader.readFloat()
        length = reader.readUInt()
        self.boneName = reader.readBytes(length).decode("ascii")

        keyCount = reader.readUInt() 
        for i in range(keyCount): 
            keyTime = reader.readFloat()          
            rotation = Vector4F()
            rotation.read(reader)
            
            key = NTWMMotionKey()
            key.time = keyTime
            key.motion = rotation
            
            self.rotationKeys.append(key)

        keyCount = reader.readUInt()         
        for i in range(keyCount):
            keyTime = reader.readFloat()           
            position = Vector3F()
            position.read(reader)
            
            key = NTWMMotionKey()
            key.time = keyTime
            key.motion = position
            
            self.positionKeys.append(key)
            
        keyCount = reader.readUInt()         
        for i in range(keyCount): 
            keyTime = reader.readFloat()             
            scale = Vector3F()
            scale.read(reader)  
            
            key = NTWMMotionKey()
            key.time = keyTime
            key.motion = scale
            
            self.scaleKeys.append(key)
            
        reader.seek(4, NOESEEK_REL)    
            
            
class NTWMMotions: 
    def __init__(self):
        self.boneMotions = []
        self.filename = ""
    
    def readMotions(self, reader):    
        count = reader.readUInt()
        for i in range(count):
            boneMotion = NTWMBoneMotion()
            boneMotion.read(reader)
        
            self.boneMotions.append(boneMotion)          
    
    def readHeader(self, reader):
        reader.seek(28, NOESEEK_REL)
    
    def read(self, filename):
        try:
            with open(filename, "rb") as filereader:
                self.reader = NoeBitStream(filereader.read()) 
                self.filename = filename
                self.readHeader(self.reader)
                self.readMotions(self.reader)
            return True    
        except:    
            return False    
            

class HTWMDLoadDialogWindow:
    def __init__(self):
        self.options = {"TextureFilename": "", "MotionFilename": ""}
        self.isCanceled = True
        self.animationListBox = None
        self.texturePathEditBox = None
        self.motionFileNameEditBox = None   
        
    def buttonGetMotionFileNameOnClick(self, noeWnd, controlId, wParam, lParam):
        dialog = noewinext.NoeUserDialog("Open Motion file", ".mot", \
            "Motion files (*.mot)|*.mot", "")
        motionFileName = dialog.getOpenFileName()
        
        if motionFileName is not None:
            self.motionFileNameEditBox.setText(motionFileName)
        
        return True        
        
    def buttonGetTexturePathOnClick(self, noeWnd, controlId, wParam, lParam):
        dialog = noewinext.NoeUserDialog("Choose texture")
        filename = dialog.getOpenFileName()
        
        if filename is not None:
            self.texturePathEditBox.setText(filename)
        
        return True
        
    def buttonLoadOnClick(self, noeWnd, controlId, wParam, lParam):    
        self.options["TextureFilename"] = self.texturePathEditBox.getText()
        self.options["MotionFilename"] = self.motionFileNameEditBox.getText()
        
        self.isCanceled = False
        self.noeWnd.closeWindow()   

        return True

    def buttonCancelOnClick(self, noeWnd, controlId, wParam, lParam):
        self.isCanceled = True
        self.noeWnd.closeWindow()

        return True

    def create(self):
        self.noeWnd = noewin.NoeUserWindow("Load Ghost Recon character model", "openModelWindowClass", 430, 200)
        noeWindowRect = noewin.getNoesisWindowRect()

        if noeWindowRect:
            windowMargin = 100
            self.noeWnd.x = noeWindowRect[0] + windowMargin
            self.noeWnd.y = noeWindowRect[1] + windowMargin

        if self.noeWnd.createWindow():
            self.noeWnd.setFont("Arial", 14)

            self.noeWnd.createStatic("Texture filename", 5, 5, 140, 20)
            # 
            index = self.noeWnd.createEditBox(5, 24, 330, 40, "", None, True)
            self.texturePathEditBox = self.noeWnd.getControlByIndex(index)
            
            self.noeWnd.createButton("Open", 340, 24, 80, 21, self.buttonGetTexturePathOnClick)

            self.noeWnd.createStatic("Motion filename", 5, 70, 140, 20)
            # 
            index = self.noeWnd.createEditBox(5, 90, 330, 40, "", None, True)
            self.motionFileNameEditBox = self.noeWnd.getControlByIndex(index)            
            self.noeWnd.createButton("Open", 340, 90, 80, 21, self.buttonGetMotionFileNameOnClick)
            
            self.noeWnd.createButton("Load", 5, 140, 80, 30, self.buttonLoadOnClick)
            self.noeWnd.createButton("Cancel", 95, 140, 80, 30, self.buttonCancelOnClick)

            self.noeWnd.doModal()
            
      
             
def ntwmModelCheckType(data):     
            
    return 1     
    

def ntwmModelLoadModel(data, mdlList): 
    dialogWindow = HTWMDLoadDialogWindow()
    dialogWindow.create()
  
    if dialogWindow.isCanceled:
        return 1
     
    textureName = dialogWindow.options["TextureFilename"]
    motionFilename = dialogWindow.options["MotionFilename"]      
    
    ntwmModel = NTWMCharacterModel(NoeBitStream(data)) 
    ntwmModel.read()
    
    ctx = rapi.rpgCreateContext()
      
    materials = []
    textures = [] 
       
    currentPath = noesis.getSelectedDirectory()
    for mesh in ntwmModel.meshes:
        if not textureName:    
            if ntwmModel.type == FXM:
                for extension in [".jpg", ".tga"]:           
                    filename = "{}/{}{}".format(currentPath, mesh.textureName, extension)
                    if os.path.exists(filename):
                        textureName = mesh.textureName + extension
                        break
            else:
                textureName = mesh.textureName        
               
        texture = rapi.loadExternalTex(textureName)

        if texture == None:
            texture = NoeTexture(textureName, 0, 0, bytearray())

        textures.append(texture)            
        material = NoeMaterial(mesh.textureName, textureName)
        material.setFlags(noesis.NMATFLAG_TWOSIDED, 1)
        materials.append(material)      
    
    # render model  
    for mesh in ntwmModel.meshes: 
        rapi.rpgSetMaterial(mesh.textureName)  
            
        for faceIndex in mesh.faceIndexes:
            rapi.immBegin(noesis.RPGEO_TRIANGLE) 
            for index in faceIndex.getStorage():
                rapi.immUV2(mesh.vertexes[index].uv.getStorage())    
                
                if ntwmModel.bones:
                    rapi.immBoneIndex(ntwmModel.weights[index].boneIndexes)
                    rapi.immBoneWeight(ntwmModel.weights[index].weights) 
                    
                rapi.immVertex3(mesh.vertexes[index].coordinates.getStorage())
            
            rapi.immEnd() 
                   
    mdl = rapi.rpgConstructModelSlim()
    
    # show skeleton
    bones = []
    index = 0
    boneNames = []
   
    for bone in ntwmModel.bones:
        if index >= 0:
            boneNames.append(bone.name) 
    
            if bone.parentIndex >= 0:
                boneMat = bone.matrix.inverse()
            else:         
                boneMat = bone.matrix 
        
            boneName = bone.name
            boneParentName = ntwmModel.bones[bone.parentIndex].name
            if bone.parentIndex < 0:
                boneParentName = ""
            
            bones.append(NoeBone(index, boneName, boneMat, boneParentName, bone.parentIndex))

        index += 1

    # load animation 
    ntwmMotions = NTWMMotions()
    if motionFilename and ntwmMotions.read(motionFilename):     
        index = 0   
        kfBones = []

        for boneMotion in ntwmMotions.boneMotions:
            if boneMotion.boneName in boneNames:
                keyFramedBone = NoeKeyFramedBone(index)
                rkeys = []
                for rotKey in boneMotion.rotationKeys:
                    rkeys.append(NoeKeyFramedValue(rotKey.time, NoeQuat(rotKey.motion.getStorage()).toMat43(1).toQuat()))
                
                pkeys = []
                for posKey in boneMotion.positionKeys:
                    pkeys.append(NoeKeyFramedValue(posKey.time, NoeVec3(posKey.motion.getStorage())))
                
                keyFramedBone.setRotation(rkeys)          
                keyFramedBone.setTranslation(pkeys)
            
                kfBones.append(keyFramedBone) 
        
                index += 1
                
        anims = []      
        anim = NoeKeyFramedAnim(ntwmMotions.filename, bones, kfBones) 
        anims.append(anim)

        if anims:
            mdl.setAnims(anims)  
   
    mdl.setBones(bones)   
        
    # set materials
    if materials:    
        mdl.setModelMaterials(NoeModelMaterials(textures, materials)) 
        
    mdlList.append(mdl)
    
    #rapi.setPreviewOption("setAngOfs", "0 -90 0")
    
    return 1