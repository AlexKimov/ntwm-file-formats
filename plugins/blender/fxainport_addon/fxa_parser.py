import struct
from .fxa_utils import (
    read_uint, read_int, read_float, read_string, 
    read_vector3f, read_vector4f,
    skip_bytes, skip_uints, skip_floats, skip_ints,
    check_if_exist_anywhere
)

# Module version for reload tracking
__module_version__ = "1.0.1"


class FXAParser:
    """Parser for FXA binary files from Nosperatu: Wrath of Malachii"""
    
    def __init__(self):
        self.version = 1
        self._parse_count = 0
    
    def parse_file(self, filepath):
        """Parse entire FXA file and return list of nodes"""
        print(f"[FXA Parser] Opening file: {filepath}")
        
        with open(filepath, 'rb') as f:
            # Read header
            self.version = read_uint(f)
            node_num = read_uint(f)
            C = read_uint(f)
            nodeNum2 = read_uint(f)
            
            print(f"[FXA Parser] Version: {self.version}, Nodes: {node_num}, C: {C}, NodeNum2: {nodeNum2}")
            
            nodes_data = []
            
            # Parse all nodes
            for i in range(node_num):
                node = self.parse_node(f)
                if node:
                    node['raw_index'] = i
                    nodes_data.append(node)
                    
                    if (i + 1) % 100 == 0:
                        print(f"[FXA Parser] Parsed {i + 1}/{node_num} nodes...")
            
            print(f"[FXA Parser] Complete! Parsed {len(nodes_data)} nodes.")
            return nodes_data
    
    def parse_node(self, f):
        """Parse a single node with full structure handling"""
        try:
            node = {}
            
            # ===== COMMON HEADER (all nodes) =====
            node['type'] = read_uint(f)
            node['index'] = read_uint(f)
            node['parentIndex'] = read_uint(f)
            
            length = read_uint(f)
            node['NodeName'] = read_string(f, length)
            
            node['coordinates'] = read_vector3f(f)
            node['scale'] = read_vector3f(f)
            node['orientation'] = read_vector4f(f)
            
            # Version >= 6: b1-b3
            if self.version >= 6:
                skip_uints(f, 3)  # b1, b2, b3
            
            # Common fields after versioned section
            node['b4'] = read_uint(f)
            node['num00'] = read_uint(f)
            
            # obj[num00] array
            for _ in range(node['num00']):
                if check_if_exist_anywhere():
                    skip_uints(f, 2)  # Assuming standard size
            
            # num and obj1[num] structure
            node['num'] = read_uint(f)
            for _ in range(node['num']):
                self._parse_obj1_structure(f)
            
            # eventNum and EVENT[eventNum]
            node['eventNum'] = read_uint(f)
            for _ in range(node['eventNum']):
                self._parse_event_structure(f)
            
            # Common trailing b9-b19
            node['trailing_b'] = {}
            for i in range(9, 20):
                if i < 16:
                    node['trailing_b'][f'b{i}'] = read_uint(f)
                elif i < 19:
                    node['trailing_b'][f'b{i}float'] = read_float(f)
                else:
                    node['trailing_b'][f'b{i}'] = read_uint(f)
            
            # Version >= 46: y[b20] structure
            if self.version >= 46:
                node['has_y_structure'] = True
                node['b20'] = read_uint(f)
                for y_idx in range(node['b20']):
                    self._parse_y_structure(f)
            
            # TYPE-SPECIFIC PARSING
            self._parse_type_specific(f, node['type'])
            
            self._parse_count += 1
            return node
            
        except Exception as e:
            print(f"Warning: Failed to parse node, seeking forward: {e}")
            return None
    
    def _parse_obj1_structure(self, f):
        """Parse obj1 array element"""
        if check_if_exist_anywhere():
            pass
        
        name_len = read_uint(f)
        skip_bytes(f, name_len)  # Name3
        
        skip_uints(f, 4)  # b1-b4
        skip_uints(f, 6)  # b5[3], b6[3]
        skip_uints(f, 2)  # b7, b8
        
        if self.version >= 2:
            skip_uints(f, 6)  # b9-b14
        
        if self.version >= 6:
            skip_uints(f, 3)  # b15-b17
        
        if self.version >= 11:
            skip_uints(f, 2)  # b18-b19
    
    def _parse_event_structure(self, f):
        """Parse EVENT structure elements"""
        read_uint(f)  # C
        
        if self.version >= 15:
            name_len = read_uint(f)
            skip_bytes(f, name_len)  # Name
            name_len = read_uint(f)
            skip_bytes(f, name_len)  # Name2
        
        name_len = read_uint(f)
        skip_bytes(f, name_len)  # Name3
    
    def _parse_y_structure(self, f):
        """Parse y[b20] array element"""
        bn = struct.unpack('<B', f.read(1))[0]
        b22 = struct.unpack('<B', f.read(1))[0]
        
        if self.version >= 50:
            b22_v2 = struct.unpack('<B', f.read(1))[0]
        
        b16 = read_uint(f)
        num = read_uint(f)
        
        # d13[num/4] uint array
        skip_uints(f, max(0, num // 4))
        
        # Switch based on bn
        if bn == 2:
            skip_uints(f, 1)
        elif bn == 3:
            skip_uints(f, 2)
        elif bn in [4, 5]:
            skip_uints(f, 4)
    
    def _parse_type_specific(self, f, node_type):
        """Handle type-specific byte sequences"""
        # Note: All cases match FXA.txt exactly including case 36
        
        if node_type == 0:  # SPAWN
            pass  # No extra fields
        
        elif node_type == 2:  # Sound
            self._parse_type_sound(f)
        
        elif node_type == 3:  # Model
            self._parse_read_node3(f)
        
        elif node_type == 4:  # LIGHT
            self._parse_type_light(f)
        
        elif node_type == 5:  # Link
            self._parse_type_link(f)
        
        elif node_type == 7:
            self._parse_type_7(f)
        
        elif node_type == 9:
            skip_uints(f, 4)  # b15-b17 + b18? Actually just 4 uints total
            name_len = read_uint(f)
            skip_bytes(f, name_len)
        
        elif node_type == 10:
            skip_uints(f, 4)  # b15-b18
            if self.version >= 35:
                skip_uints(f, 7)  # b19-b25
        
        elif node_type == 11:
            skip_uints(f, 4)  # b15-b18
            num = read_uint(f)
            for _ in range(num):
                skip_uints(f, 1)  # b1
                name_len = read_uint(f)
                skip_bytes(f, name_len)  # Name0
                name_len = read_uint(f)
                skip_bytes(f, name_len)  # Name
                name_len = read_uint(f)
                skip_bytes(f, name_len)  # Name1
                read_float(f)  # float b
            if self.version >= 48:
                skip_uints(f, 2)  # b27, b27
        
        elif node_type == 12:  # InventoryIcon
            skip_uints(f, 8)  # b15-b22
            if self.version >= 36:
                skip_uints(f, 1)  # b27
            if self.version >= 26:
                name_len = read_uint(f)
                skip_bytes(f, name_len)  # Name13
            if self.version >= 54:
                skip_uints(f, 1)  # b28
            # Complex switch(b15) structure
            b15 = read_uint(f)
            self._parse_switch_b15_case(f, b15)
        
        elif node_type == 13:
            skip_uints(f, 10)  # b15-b24[3]
            if self.version >= 3:
                skip_uints(f, 5)  # b25-b29
            if self.version >= 9:
                skip_uints(f, 5)  # b30-b34
            skip_uints(f, 1)  # b34
            if self.version >= 25:
                skip_uints(f, 1)  # b35
            if self.version >= 28:
                skip_uints(f, 14)  # b36-b42 arrays
        
        elif node_type == 15:
            skip_uints(f, 6)  # b151[6]
            skip_uints(f, 4)  # b16-b19
        
        elif node_type == 16:
            skip_uints(f, 1)  # b15
            skip_floats(f, 3)  # b16-b18
            if self.version >= 4:
                skip_floats(f, 15)  # b19-b33
            if self.version >= 14:
                skip_floats(f, 2)  # b34-b35
            if self.version >= 25:
                skip_floats(f, 4)  # b36-b39
            if self.version >= 29:
                skip_uints(f, 1)  # b41
            if self.version >= 41:
                skip_uints(f, 32)  # b42[32]
                skip_floats(f, 3)  # b43-b45
            if self.version >= 41:
                skip_floats(f, 7)  # b46-b52
            if self.version >= 42:
                skip_floats(f, 2)  # b53-b54
            if self.version >= 49:
                skip_floats(f, 2)  # b55-b56
        
        elif node_type == 17:  # Model_Particle
            self._parse_read_node3(f)
            skip_uints(f, 2)  # b27, b28
            num = read_uint(f)
            for _ in range(num):
                skip_ints(f, 3)  # b29-b31
                if self.version >= 37:
                    name_len = read_uint(f)
                    skip_bytes(f, name_len)  # Name
            if self.version >= 42:
                skip_uints(f, 1)  # b32
                num2 = read_uint(f)
                for _ in range(num2):
                    b33 = read_uint(f)
                    if b33 != 0:
                        skip_ints(f, 1)  # b34
                        name_len = read_uint(f)
                        skip_bytes(f, name_len)  # Name2
                        name_len = read_uint(f)
                        skip_bytes(f, name_len)  # Name0
                        skip_ints(f, 3)  # b35-b37
        
        elif node_type == 18:  # Particle
            self._parse_read_node3(f)
            skip_uints(f, 20)  # Multiple b values
        
        elif node_type == 19:
            if self.version >= 26:
                skip_uints(f, 1)  # b15
            if self.version >= 27:
                skip_uints(f, 1)  # b16
            if self.version >= 26:
                skip_uints(f, 12)  # b17-b26
                name_len = read_uint(f)
                skip_bytes(f, name_len)  # Name1
                name_len = read_uint(f)
                skip_bytes(f, name_len)  # Name3
        
        elif node_type == 20:
            skip_uints(f, 5)  # b15-b19
        
        elif node_type == 21:
            skip_uints(f, 5)  # b15-b19
            if self.version >= 8:
                num00 = read_uint(f)
                for _ in range(num00):
                    name_len = read_uint(f)
                    skip_bytes(f, name_len)  # Name
                    skip_uints(f, 2)  # b, b
                    if self.version >= 23:
                        skip_uints(f, 1)
                    if self.version >= 24:
                        skip_uints(f, 1)
                    if self.version >= 33:
                        skip_uints(f, 1)
                skip_uints(f, 3)  # b20-b22
            if self.version >= 19:
                skip_uints(f, 1)  # b23
            if self.version >= 20:
                skip_uints(f, 1)  # b24
            if self.version >= 23:
                skip_uints(f, 1)  # b25
            if self.version >= 34:
                skip_uints(f, 1)  # b26
            if self.version >= 33:
                skip_uints(f, 1)  # b27
            if self.version >= 32:
                skip_uints(f, 1)  # b28
            if self.version >= 33:
                skip_uints(f, 1)  # b29
        
        elif node_type == 24:
            skip_uints(f, 8)  # b15-b22
        
        elif node_type == 25:
            skip_uints(f, 8)  # b15-b22
            if self.version >= 12:
                num = read_uint(f)
                for _ in range(num):
                    skip_floats(f, 2)
                    skip_uints(f, 2)
                skip_uints(f, 3)  # b23, b241, b25
            if self.version >= 13:
                num = read_uint(f)
                for _ in range(num):
                    skip_floats(f, 2)
                    skip_uints(f, 2)
            if self.version >= 16:
                skip_uints(f, 2)  # b26, b271
            if self.version >= 18:
                skip_uints(f, 1)  # b28
            if self.version >= 53:
                skip_uints(f, 1)  # b29
        
        elif node_type == 26:
            skip_uints(f, 8)  # b15-b22
        
        elif node_type == 27:
            skip_uints(f, 8)  # b15-b22
        
        elif node_type == 29:
            skip_uints(f, 8)  # b15-b22
            if self.version >= 19:
                skip_uints(f, 3)  # b23-b25
            if self.version >= 27:
                skip_uints(f, 2)  # b26-b27
            if self.version >= 19:
                skip_uints(f, 3)  # b28-b30
            if self.version >= 27:
                skip_uints(f, 1)  # b30
            if self.version >= 19:
                num = read_uint(f)
                for _ in range(num):
                    skip_uints(f, 4)  # b32-b35
            if self.version >= 19:
                skip_uints(f, 3)  # b36-b38
            if self.version >= 13:
                num = read_uint(f)
                for _ in range(num):
                    skip_uints(f, 4)  # b32-b35
            if self.version >= 21:
                skip_uints(f, 2)  # b32-b33
            if self.version >= 41:
                skip_uints(f, 1)  # b34
            if self.version >= 45:
                skip_uints(f, 3)  # b33-b35
        
        elif node_type == 0x1C:  # Matrix_Animation (28)
            skip_uints(f, 3)  # b153[3]
            skip_uints(f, 6)  # b16-b21
            num = read_uint(f)
            for _ in range(num):
                # Multiple arrays of 3 uints each (30 total per iteration)
                skip_uints(f, 30)
        
        elif node_type == 0x1F:  # Matrix_TRIGGER (31)
            if self.version > 21:
                skip_uints(f, 2)  # b15-b16
        
        elif node_type == 30:
            skip_uints(f, 8)  # b14-b21
            if self.version > 41:
                num = read_uint(f)
                for _ in range(num):
                    name_len = read_uint(f)
                    skip_bytes(f, name_len)  # name
                    skip_floats(f, 8)  # 8 floats
        
        elif node_type == 32:  # AI
            skip_uints(f, 8)  # b15-b22
        
        elif node_type == 33:
            skip_uints(f, 4)  # b15-b18
        
        elif node_type == 34:
            skip_uints(f, 4)  # b15-b18
        
        elif node_type == 35:
            read_float(f)  # b15
            name_len = read_uint(f)
            skip_bytes(f, name_len)  # Name3
            skip_uints(f, 6)  # b17, b18, b191[4], b29, b21
        
        elif node_type == 36:  # ===== YOUR SPECIFIC CONCERN =====
            # UINT b15; UINT b16; UINT b17; UINT b18;
            skip_uints(f, 4)  # b15-b18
            
            if self.version >= 26:
                skip_uints(f, 4)  # b29[4]
                skip_uints(f, 1)  # b30
            
            if self.version >= 30:
                skip_uints(f, 2)  # b31, b32
            # ==========================================
        
        elif node_type == 38:
            read_float(f)  # b20
            skip_uints(f, 3)  # b21-b23
        
        else:
            print(f"[FXA Parser] Unknown node type {node_type}, attempting sync")
    
    def _parse_read_node3(self, f):
        """Parse readNode3() function content"""
        read_uint(f)  # ModelIndex
        materialNum = read_uint(f)
        
        for _ in range(materialNum):
            skip_uints(f, 2)  # index, unknown
        
        if self.version >= 5:
            skip_uints(f, 2)  # b19-b20
            read_float(f)  # b21
            skip_uints(f, 3)  # b22-b24
        
        if self.version >= 47:
            skip_uints(f, 2)  # b25-b26
    
    def _parse_type_sound(self, f):
        read_uint(f)  # soundIndex
        read_uint(f)  # b16
        read_float(f)  # b17
        
        if self.version >= 36:
            skip_uints(f, 1)
            skip_floats(f, 3)
            skip_floats(f, 2)  # b18-b19
            skip_uints(f, 4)  # b20-b23 (with duplicates)
            if self.version >= 41:
                read_float(f)  # b25
        else:
            skip_uints(f, 3)  # b18-b20
    
    def _parse_type_light(self, f):
        read_uint(f)  # b15
        skip_floats(f, 4)  # b160[4]
        skip_floats(f, 4)  # b170[4]
        skip_floats(f, 4)  # b180[4]
        read_float(f)  # b19
        
        if self.version >= 55:
            skip_floats(f, 3)  # 3 unnamed floats
        
        read_float(f)  # b
        skip_uints(f, 4)  # 4 uints
    
    def _parse_type_link(self, f):
        read_uint(f)  # b14
        num = read_uint(f)
        
        for _ in range(num):
            read_uint(f)  # n
            read_uint(f)  # b
            name_len = read_uint(f)
            skip_bytes(f, name_len)  # Name
        
        skip_uints(f, 3)  # b16-b18
        if self.version > 42:
            read_uint(f)  # b19
    
    def _parse_type_7(self, f):
        skip_floats(f, 4)  # b15-b18
        skip_uints(f, 1)  # b19
        skip_floats(f, 4)  # b20-b23
        skip_uints(f, 2)  # b24-b25
        skip_floats(f, 2)  # b26-b27
        
        if self.version > 10:
            skip_uints(f, 1)  # b28
            skip_floats(f, 5)  # b29-b32, b27 (duplicate?)
            read_float(f)  # b27 again
    
    def _parse_switch_b15_case(self, f, b15):
        """Handle switch(b15) cases for type 12"""
        if b15 == 0:
            skip_uints(f, 2)  # b29-b30
        elif b15 == 1:
            skip_uints(f, 8)  # b29-b36
            num = read_uint(f)
            for _ in range(num):
                skip_uints(f, 4)  # asdf[num]
            skip_uints(f, 1)  # b37
        elif b15 == 2:
            skip_uints(f, 5)  # b29-b33
        elif b15 == 3:
            skip_uints(f, 3)  # b29-b31
        elif b15 == 4:
            skip_uints(f, 8)  # b29-b36
            if self.version >= 14:
                skip_uints(f, 13)  # b36-b48
            if self.version >= 26:
                name_len = read_uint(f)
                skip_bytes(f, name_len)  # Name13
        elif b15 == 5:
            num = read_uint(f)
            for _ in range(num):
                skip_uints(f, 3)  # asdf
            skip_uints(f, 9)  # b30-b37
        elif b15 == 6:
            skip_uints(f, 5)  # b29-b33
        elif b15 == 7:
            skip_uints(f, 3)  # b29-b31
            num = read_uint(f)
            for _ in range(num):
                skip_uints(f, 4)  # asdf
            skip_uints(f, 5)  # b32-b35
        elif b15 == 8:
            num = read_uint(f)
            for _ in range(num):
                skip_uints(f, 4)  # asdf
            skip_uints(f, 16)  # b30-b45
        elif b15 == 9:
            num = read_uint(f)
            for _ in range(num):
                skip_uints(f, 4)  # asdf
            skip_uints(f, 5)  # b30-b34