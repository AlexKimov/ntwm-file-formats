import struct
from io import BytesIO

class Vector3F:
    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x = x
        self.y = y
        self.z = z
    
    def read(self, reader):
        self.x = reader.read_float()
        self.y = reader.read_float()
        self.z = reader.read_float()
    
    def to_bytes(self):
        return struct.pack("<fff", self.x, self.y, self.z)
    
    def to_tuple(self):
        return (self.x, self.y, self.z)
    
    @classmethod
    def from_bytes(cls, data):
        x, y, z = struct.unpack("<fff", data[:12])
        return cls(x, y, z)


class Vector4F:
    def __init__(self, x=0.0, y=0.0, z=0.0, w=0.0):
        self.x = x
        self.y = y
        self.z = z
        self.w = w
    
    def read(self, reader):
        self.x = reader.read_float()
        self.y = reader.read_float()
        self.z = reader.read_float()
        self.w = reader.read_float()
    
    def to_bytes(self):
        return struct.pack("<ffff", self.x, self.y, self.z, self.w)
    
    def to_tuple(self):
        return (self.x, self.y, self.z, self.w)


class Vector3UI16:
    def __init__(self, x=0, y=0, z=0):
        self.x = x
        self.y = y
        self.z = z
    
    def read(self, reader):
        self.x = reader.read_ushort()
        self.y = reader.read_ushort()
        self.z = reader.read_ushort()
    
    def to_bytes(self):
        return struct.pack("<HHH", self.x, self.y, self.z)
    
    def to_tuple(self):
        return (self.x, self.y, self.z)


class Vector2F:
    def __init__(self, x=0.0, y=0.0):
        self.x = x
        self.y = y
    
    def read(self, reader):
        self.x = reader.read_float()
        self.y = reader.read_float()
    
    def to_bytes(self):
        return struct.pack("<ff", self.x, self.y)
    
    def to_tuple(self):
        return (self.x, self.y)


class BinaryReader:
    def __init__(self, data):
        self.stream = BytesIO(data)
        self.size = len(data)
    
    def read_uint(self):
        return struct.unpack("<I", self.stream.read(4))[0]
    
    def read_int(self):
        return struct.unpack("<i", self.stream.read(4))[0]
    
    def read_short(self):
        return struct.unpack("<h", self.stream.read(2))[0]
    
    def read_ushort(self):
        return struct.unpack("<H", self.stream.read(2))[0]
    
    def read_float(self):
        return struct.unpack("<f", self.stream.read(4))[0]
    
    def read_ubyte(self):
        return struct.unpack("<B", self.stream.read(1))[0]
    
    def read_bytes(self, size):
        return self.stream.read(size)
    
    def seek(self, offset, whence=0):
        self.stream.seek(offset, whence)
    
    def tell(self):
        return self.stream.tell()
    
    def remaining(self):
        return self.size - self.tell()


class BinaryWriter:
    def __init__(self):
        self.stream = BytesIO()
    
    def write_uint(self, value):
        self.stream.write(struct.pack("<I", value))
    
    def write_int(self, value):
        self.stream.write(struct.pack("<i", value))
    
    def write_short(self, value):
        self.stream.write(struct.pack("<h", value))
    
    def write_ushort(self, value):
        self.stream.write(struct.pack("<H", value))
    
    def write_float(self, value):
        self.stream.write(struct.pack("<f", value))
    
    def write_bytes(self, data):
        self.stream.write(data)
    
    def get_data(self):
        return self.stream.getvalue()