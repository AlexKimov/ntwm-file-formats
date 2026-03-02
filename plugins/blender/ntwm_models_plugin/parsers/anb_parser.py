# io_anim_ntwm/parsers/anb_parser.py
from ..utils.data_structures import Vector3F, Vector2F, Vector3UI16, BinaryReader, BinaryWriter

class NTWMMesh:
    def __init__(self):
        self.vertex_count = 0
        self.uv_count = 0
        self.face_count = 0
        self.vertices = []  # List of (position, normal)
        self.faces = []  # List of Vector3UI16
        self.uv_coords = []  # List of Vector2F
        self.uv_indices = []  # List of Vector3UI16
        self.texture_name = ""
    
    def read(self, reader):
        self.vertex_count = reader.read_uint()
        self.uv_count = reader.read_uint()
        self.face_count = reader.read_uint()
        
        # Read vertices (position + normal)
        for _ in range(self.vertex_count):
            pos = Vector3F()
            pos.read(reader)
            norm = Vector3F()
            norm.read(reader)
            self.vertices.append((pos, norm))
        
        # Read face indices
        for _ in range(self.face_count):
            face = Vector3UI16()
            face.read(reader)
            self.faces.append(face)
        
        # Read UV coordinates
        for _ in range(self.uv_count):
            uv = Vector2F()
            uv.read(reader)
            self.uv_coords.append(uv)
        
        # Read UV indices per face
        for _ in range(self.face_count):
            uv_idx = Vector3UI16()
            uv_idx.read(reader)
            self.uv_indices.append(uv_idx)
    
    def write(self, writer):
        writer.write_uint(self.vertex_count)
        writer.write_uint(self.uv_count)
        writer.write_uint(self.face_count)
        
        for pos, norm in self.vertices:
            writer.write_bytes(pos.to_bytes())
            writer.write_bytes(norm.to_bytes())
        
        for face in self.faces:
            writer.write_bytes(face.to_bytes())
        
        for uv in self.uv_coords:
            writer.write_bytes(uv.to_bytes())
        
        for uv_idx in self.uv_indices:
            writer.write_bytes(uv_idx.to_bytes())


class NTWMFrameMesh:
    def __init__(self):
        self.positions = bytearray()
        self.normals = bytearray()
    
    def read(self, reader, vertex_count):
        for _ in range(vertex_count):
            pos = Vector3F()
            pos.read(reader)
            self.positions += pos.to_bytes()
            
            norm = Vector3F()
            norm.read(reader)
            self.normals += norm.to_bytes()
    
    def write(self, writer):
        writer.write_bytes(self.positions)
        writer.write_bytes(self.normals)


class NTWMMorphFrame:
    def __init__(self):
        self.frame_meshes = []  # List of NTWMFrameMesh


class ANBModel:
    def __init__(self):
        self.morph_frame_count = 0
        self.mesh_count = 0
        self.meshes = []
        self.morph_frames = []
        self.texture_path = ""
    
    def read(self, filepath):
        with open(filepath, 'rb') as f:
            data = f.read()
        reader = BinaryReader(data)
        
        self.morph_frame_count = reader.read_uint()
        self.mesh_count = reader.read_uint()
        
        # Read mesh data
        for _ in range(self.mesh_count):
            mesh = NTWMMesh()
            mesh.read(reader)
            self.meshes.append(mesh)
        
        # Read morph frames (morph_frame_count - 1)
        for _ in range(self.morph_frame_count - 1):
            morph_frame = NTWMMorphFrame()
            for mesh in self.meshes:
                frame_mesh = NTWMFrameMesh()
                frame_mesh.read(reader, mesh.vertex_count)
                morph_frame.frame_meshes.append(frame_mesh)
            self.morph_frames.append(morph_frame)
    
    def write(self, filepath):
        writer = BinaryWriter()
        
        writer.write_uint(self.morph_frame_count)
        writer.write_uint(self.mesh_count)
        
        for mesh in self.meshes:
            mesh.write(writer)
        
        for morph_frame in self.morph_frames:
            for frame_mesh in morph_frame.frame_meshes:
                frame_mesh.write(writer)
        
        with open(filepath, 'wb') as f:
            f.write(writer.get_data())