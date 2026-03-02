# io_anim_ntwm/parsers/fxm_parser.py
from ..utils.data_structures import Vector3F, Vector4F, Vector2F, Vector3UI16, BinaryReader, BinaryWriter
import struct

class NTWMMeshVertex:
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
        self.vertices = []
        self.face_indexes = []
        self.texture_name = ""
        self.vertex_count = 0
        self.face_count = 0
    
    def read(self, reader, has_texture_data=True):
        if has_texture_data:
            length = reader.read_uint()
            self.texture_name = reader.read_bytes(length).decode("ascii", errors="ignore")
            reader.seek(24, 1)  # NOESEEK_REL equivalent
        
        self.face_count = reader.read_uint()
        self.vertex_count = reader.read_uint()
        
        for _ in range(self.face_count):
            face_indexes = Vector3UI16()
            face_indexes.read(reader)
            self.face_indexes.append(face_indexes)
        
        for _ in range(self.vertex_count):
            vertex = NTWMMeshVertex()
            vertex.read(reader)
            self.vertices.append(vertex)


class NTWMBone:
    def __init__(self):
        self.name = ""
        self.parent_index = 0
        self.matrix = None  # 4x3 matrix
    
    def read(self, reader):
        reader.seek(8, 1)  # Skip header
        length = reader.read_uint()
        self.name = reader.read_bytes(length).decode("ascii", errors="ignore")
        self.parent_index = reader.read_int()
        
        # Read 4x4 matrix and convert to 4x3
        matrix_data = reader.read_bytes(64)
        self.matrix = struct.unpack("<16f", matrix_data)


class NTWMVertexWeights:
    def __init__(self):
        self.count = 0
        self.weights = []
        self.bone_indexes = []


class FXMModel:
    FXM = 1002
    FXM_KEYPOSE = 1001
    
    def __init__(self):
        self.meshes = []
        self.bones = []
        self.weights = []
        self.type = self.FXM
        self.mesh_count = 0
        self.name = ""
        self.texture_path = ""
        self.motion_filename = ""
    
    def read(self, filepath):
        with open(filepath, 'rb') as f:
            data = f.read()
        reader = BinaryReader(data)
        
        # Read header
        reader.seek(4, 1)
        if reader.read_uint() == 1:
            self.type = self.FXM_KEYPOSE
        
        if self.type == self.FXM:
            reader.seek(36, 1)
            self.mesh_count = reader.read_uint()
            
            # Read meshes
            for _ in range(self.mesh_count):
                mesh = NTWMMesh()
                mesh.read(reader)
                self.meshes.append(mesh)
        else:
            # KeyPose format - read bones first
            self.read_bones(reader)
            
            reader.seek(36, 1)
            length = reader.read_uint()
            self.name = reader.read_bytes(length).decode("ascii", errors="ignore")
            reader.seek(24, 1)
            
            self.mesh_count = 1
            mesh = NTWMMesh()
            mesh.read(reader, has_texture_data=False)
            self.meshes.append(mesh)
            
            if self.bones:
                self.read_vertex_weights(reader)
    
    def read_bones(self, reader):
        count = reader.read_uint()
        for _ in range(count):
            bone = NTWMBone()
            bone.read(reader)
            self.bones.append(bone)
    
    def read_vertex_weights(self, reader):
        for _ in range(len(self.meshes[0].vertices)):
            pos = Vector3F()
            pos.read(reader)
            
            weight_count = reader.read_ubyte()
            reader.seek(3, 1)  # Skip padding
            
            vertex_weights = NTWMVertexWeights()
            vertex_weights.count = weight_count
            
            if weight_count > 0:
                count = weight_count - 1 if weight_count > 0 else 1
                weights_data = reader.read_bytes(16)
                vertex_weights.weights = list(struct.unpack("<4f", weights_data)[:count])
                
                bone_data = reader.read_bytes(4)
                vertex_weights.bone_indexes = list(struct.unpack("<4B", bone_data)[:count])
            
            self.weights.append(vertex_weights)
            
            normal = Vector3F()
            normal.read(reader)
            
            uv = Vector2F()
            uv.read(reader)
    
    def write(self, filepath):
        writer = BinaryWriter()
        
        # Write header
        writer.write_uint(0)  # Version
        writer.write_uint(1 if self.type == self.FXM_KEYPOSE else 0)
        
        if self.type == self.FXM:
            writer.write_bytes(bytearray(36))  # Padding
            writer.write_uint(self.mesh_count)
            
            for mesh in self.meshes:
                # Write texture name
                texture_bytes = mesh.texture_name.encode("ascii")
                writer.write_uint(len(texture_bytes))
                writer.write_bytes(texture_bytes)
                writer.write_bytes(bytearray(24))  # Padding
                
                writer.write_uint(mesh.face_count)
                writer.write_uint(mesh.vertex_count)
                
                for face in mesh.face_indexes:
                    writer.write_bytes(face.to_bytes())
                
                for vertex in mesh.vertices:
                    writer.write_bytes(vertex.coordinates.to_bytes())
                    writer.write_bytes(vertex.normal.to_bytes())
                    writer.write_bytes(vertex.uv.to_bytes())
        else:
            # Write bones
            writer.write_uint(len(self.bones))
            for bone in self.bones:
                writer.write_bytes(bytearray(8))  # Padding
                writer.write_uint(len(bone.name))
                writer.write_bytes(bone.name.encode("ascii"))
                writer.write_int(bone.parent_index)
                writer.write_bytes(struct.pack("<16f", *bone.matrix))
            
            writer.write_bytes(bytearray(36))  # Padding
            writer.write_uint(len(self.name))
            writer.write_bytes(self.name.encode("ascii"))
            writer.write_bytes(bytearray(24))  # Padding
            
            writer.write_uint(1)  # mesh_count
            
            mesh = self.meshes[0]
            writer.write_uint(mesh.face_count)
            writer.write_uint(mesh.vertex_count)
            
            for face in mesh.face_indexes:
                writer.write_bytes(face.to_bytes())
            
            for i, vertex in enumerate(mesh.vertices):
                writer.write_bytes(vertex.coordinates.to_bytes())
                
                weights = self.weights[i] if i < len(self.weights) else NTWMVertexWeights()
                writer.write_ubyte(weights.count)
                writer.write_bytes(bytearray(3))  # Padding
                
                if weights.count > 0:
                    weights_padded = weights.weights + [0.0] * (4 - len(weights.weights))
                    writer.write_bytes(struct.pack("<4f", *weights_padded))
                    
                    bones_padded = weights.bone_indexes + [0] * (4 - len(weights.bone_indexes))
                    writer.write_bytes(struct.pack("<4B", *bones_padded))
                else:
                    writer.write_bytes(bytearray(20))
                
                writer.write_bytes(vertex.normal.to_bytes())
                writer.write_bytes(vertex.uv.to_bytes())
        
        with open(filepath, 'wb') as f:
            f.write(writer.get_data())


class NTWMMotionKey:
    def __init__(self):
        self.time = 0
        self.motion = None


class NTWMBoneMotion:
    def __init__(self):
        self.bone_name = ""
        self.rotation_keys = []
        self.position_keys = []
        self.scale_keys = []
    
    def read(self, reader):
        time = reader.read_float()
        length = reader.read_uint()
        self.bone_name = reader.read_bytes(length).decode("ascii", errors="ignore")
        
        # Rotation keys
        key_count = reader.read_uint()
        for _ in range(key_count):
            key_time = reader.read_float()
            rotation = Vector4F()
            rotation.read(reader)
            key = NTWMMotionKey()
            key.time = key_time
            key.motion = rotation
            self.rotation_keys.append(key)
        
        # Position keys
        key_count = reader.read_uint()
        for _ in range(key_count):
            key_time = reader.read_float()
            position = Vector3F()
            position.read(reader)
            key = NTWMMotionKey()
            key.time = key_time
            key.motion = position
            self.position_keys.append(key)
        
        # Scale keys
        key_count = reader.read_uint()
        for _ in range(key_count):
            key_time = reader.read_float()
            scale = Vector3F()
            scale.read(reader)
            key = NTWMMotionKey()
            key.time = key_time
            key.motion = scale
            self.scale_keys.append(key)
        
        reader.seek(4, 1)  # Padding


class MOTAnimation:
    def __init__(self):
        self.bone_motions = []
        self.filename = ""
    
    def read(self, filepath):
        with open(filepath, 'rb') as f:
            data = f.read()
        reader = BinaryReader(data)
        
        reader.seek(28, 1)  # Header
        
        count = reader.read_uint()
        for _ in range(count):
            bone_motion = NTWMBoneMotion()
            bone_motion.read(reader)
            self.bone_motions.append(bone_motion)
        
        self.filename = filepath