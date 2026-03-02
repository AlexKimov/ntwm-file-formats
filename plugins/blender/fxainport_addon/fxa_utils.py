import struct
import mathutils

# Version tracking for reload detection
_MODULE_VERSION = "1.0.1"

# Type names mapping based on getName() function in FXA.txt
NODE_TYPE_NAMES = {
    0x0: "Spawn",
    0x2: "Sound",
    0x3: "Model",
    0x4: "Light",
    0x5: "Link",
    0xC: "InventoryIcon",   # 0x12 = 18 decimal
    0x11: "Model_Particle",  # 17 decimal
    0x12: "Particle",        # 18 decimal (duplicate key above - fix below)
    0x15: "Spawn_Node",      # 21 decimal  
    0x1F: "Matrix_Trigger",  # 31 decimal
    0x1C: "Matrix_Animation",
    0x20: "AI",              # 32 decimal -> But 0x20 = 32
    0x13: "Trigger",         # Based on case 31 -> actually 0x1F
}

# Fix: Map both decimal values correctly
NODE_TYPE_NAMES_FULL = {
    0: "Spawn",
    2: "Sound",
    3: "Model",
    4: "Light",
    5: "Link",
    9: "Unknown_Type9",
    10: "Unknown_Type10",
    11: "Unknown_Type11",
    12: "InventoryIcon",
    13: "Unknown_Type13",
    15: "Unknown_Type15",
    16: "Unknown_Type16",
    17: "Model_Particle",
    18: "Particle",
    19: "Unknown_Type19",
    20: "Unknown_Type20",
    21: "Spawn_Node",
    24: "Unknown_Type24",
    25: "Unknown_Type25",
    26: "Unknown_Type26",
    27: "Unknown_Type27",
    29: "Unknown_Type29",
    30: "Unknown_Type30",
    32: "AI",
    33: "Unknown_Type33",
    34: "Unknown_Type34",
    35: "Unknown_Type35",
    36: "Unknown_Type36",
    38: "Unknown_Type38",
    0x1C: "Matrix_Animation",  # 28
    0x1F: "Matrix_Trigger",    # 31
}

TYPE_COLORS = {
    0: (1.0, 0.0, 0.0, 1.0),     # Spawn - Red
    2: (1.0, 0.5, 0.0, 1.0),     # Sound - Orange
    3: (0.0, 1.0, 0.0, 1.0),     # Model - Green
    4: (0.0, 0.0, 1.0, 1.0),     # Light - Blue
    5: (1.0, 1.0, 0.0, 1.0),     # Link - Yellow
    12: (1.0, 0.0, 1.0, 1.0),    # InventoryIcon - Magenta
    17: (1.0, 0.5, 0.5, 1.0),    # Model_Particle - Pink
    18: (0.5, 1.0, 0.5, 1.0),    # Particle - Light Green
    21: (0.5, 0.5, 1.0, 1.0),    # Spawn_Node - Light Blue
    31: (1.0, 1.0, 1.0, 1.0),    # Matrix_Trigger - White
    28: (0.0, 1.0, 1.0, 1.0),    # Matrix_Animation - Cyan
    32: (0.8, 0.2, 0.8, 1.0),    # AI - Purple
}


def read_uint(f):
    """Read an unsigned 32-bit integer"""
    return struct.unpack('<I', f.read(4))[0]


def read_int(f):
    """Read a signed 32-bit integer"""
    return struct.unpack('<i', f.read(4))[0]


def read_float(f):
    """Read a 32-bit float"""
    return struct.unpack('<f', f.read(4))[0]


def read_vector3f(f):
    """Read VECTOR_3F (x, y, z)"""
    return {
        'x': read_float(f),
        'y': read_float(f),
        'z': read_float(f)
    }


def read_vector4f(f):
    """Read VECTOR_4F (x, y, z, w)"""
    return {
        'x': read_float(f),
        'y': read_float(f),
        'z': read_float(f),
        'w': read_float(f)
    }


def read_string(f, length):
    """Read a null-terminated or fixed-length string"""
    if length <= 0:
        return ""
    raw = f.read(length)
    return raw.decode('utf-8', errors='ignore').rstrip('\x00')


def skip_bytes(f, count):
    """Safely skip n bytes"""
    pos = f.tell()
    f.seek(pos + count)


def skip_uints(f, count):
    """Skip n uint32 values"""
    skip_bytes(f, count * 4)


def skip_floats(f, count):
    """Skip n float values"""
    skip_bytes(f, count * 4)


def skip_ints(f, count):
    """Skip n signed int values"""
    skip_bytes(f, count * 4)


def get_node_type_name(node_type):
    """Get display name for node type"""
    return NODE_TYPE_NAMES_FULL.get(node_type, f"Type_{node_type}")


def get_node_type_color(node_type):
    """Get color for node type"""
    return TYPE_COLORS.get(node_type, (0.5, 0.5, 0.5, 1.0))


def check_if_exist_anywhere():
    """Placeholder for checkIfExistAnywhere() - actual implementation unknown"""
    return True


def calculate_world_position(node, node_map):
    """
    Calculate world position considering parent hierarchy transformation.
    Applies parent rotation/scale before adding local position.
    """
    local_pos = mathutils.Vector([
        node['coordinates']['x'],
        node['coordinates']['y'],
        node['coordinates']['z']
    ])
    
    world_pos = local_pos.copy()
    current_index = node['parentIndex']
    
    # Traverse up the hierarchy tree
    while current_index != 0xFFFFFFFF and current_index in node_map:
        parent = node_map[current_index]
        
        parent_pos = mathutils.Vector([
            parent['coordinates']['x'],
            parent['coordinates']['y'],
            parent['coordinates']['z']
        ])
        
        parent_quat = mathutils.Quaternion([
            parent['orientation']['w'],
            parent['orientation']['x'],
            parent['orientation']['y'],
            parent['orientation']['z']
        ])
        
        parent_scale = mathutils.Vector([
            parent['scale']['x'],
            parent['scale']['y'],
            parent['scale']['z']
        ])
        
        # Transform: pos = parent_rotation * (local_pos * scale) + parent_pos
        world_pos = parent_quat @ (world_pos * parent_scale) + parent_pos
        
        current_index = parent['parentIndex']
    
    return world_pos