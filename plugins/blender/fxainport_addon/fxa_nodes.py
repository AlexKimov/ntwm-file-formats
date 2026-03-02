import bpy
import mathutils

from .fxa_utils import (
    get_node_type_name, get_node_type_color,
    calculate_world_position
)

# Module version for reload tracking
__module_version__ = "1.0.1"


class FXANodeCreator:
    """Creates Blender objects from parsed FXA nodes"""
    
    def __init__(self, context):
        self.context = context
        self.sphere_count = 0
        self.collection = None
    
    def create_objects_from_nodes(self, nodes_data):
        """Create spheres for all nodes and return count"""
        # Build node map for hierarchy
        node_map = {node['index']: node for node in nodes_data}
        
        # Calculate world positions
        for node in nodes_data:
            node['world_position'] = calculate_world_position(node, node_map)
        
        # Create collection
        self.collection = bpy.data.collections.new("FXA_Nodes")
        scene_collection = self.context.scene.collection
        scene_collection.children.link(self.collection)
        
        # Create objects
        for node in nodes_data:
            self._create_sphere_object(node)
            
            # Progress report
            idx = nodes_data.index(node)
            if (idx + 1) % 50 == 0:
                print(f"[FXA Nodes] Created {idx + 1}/{len(nodes_data)} objects...")
        
        # Select created objects
        for obj in self.collection.objects:
            obj.select_set(True)
        
        if self.collection.objects:
            self.context.view_layer.objects.active = self.collection.objects[0]
        
        print(f"[FXA Nodes] Successfully created {len(nodes_data)} sphere objects")
        return len(nodes_data)
    
    def _create_sphere_object(self, node):
        """Create a sphere object for this node"""
        type_name = get_node_type_name(node['type'])
        display_name = f"{type_name}_{node['NodeName']}"
        obj_name = f"FXA_{display_name}_{self.sphere_count}"
        
        # Create mesh geometry
        bpy.ops.mesh.primitive_uv_sphere_add(
            radius=0.5,
            segments=16,
            ring_count=8,
            location=(
                node['world_position'].x,
                node['world_position'].y,
                node['world_position'].z
            ),
            collection=self.collection
        )
        
        obj = self.context.active_object
        obj.name = obj_name
        obj.display_type = 'WIRE'
        
        # Set custom properties (readable by other tools/scripts)
        self._set_custom_properties(obj, node)
        
        # Assign colored material
        self._assign_material(obj, node)
        
        self.sphere_count += 1
    
    def _set_custom_properties(self, obj, node):
        """Set all readable properties as Blender custom properties"""
        props = {
            "fxa_version": getattr(self, 'parser_version', 1),
            "fxa_type": node['type'],
            "fxa_type_name": get_node_type_name(node['type']),
            "fxa_index": node['index'],
            "fxa_parentIndex": node['parentIndex'],
            "fxa_local_x": node['coordinates']['x'],
            "fxa_local_y": node['coordinates']['y'],
            "fxa_local_z": node['coordinates']['z'],
            "fxa_world_x": node['world_position'].x,
            "fxa_world_y": node['world_position'].y,
            "fxa_world_z": node['world_position'].z,
            "fxa_scale_x": node['scale']['x'],
            "fxa_scale_y": node['scale']['y'],
            "fxa_scale_z": node['scale']['z'],
            "fxa_orient_w": node['orientation']['w'],
            "fxa_orient_x": node['orientation']['x'],
            "fxa_orient_y": node['orientation']['y'],
            "fxa_orient_z": node['orientation']['z'],
            "fxa_node_name": node['NodeName'],
            "fxa_raw_index": node['raw_index'],
        }
        
        for key, value in props.items():
            obj[key] = value
    
    def _assign_material(self, obj, node):
        """Assign color-coded material based on node type"""
        color = get_node_type_color(node['type'])
        mat_name = f"FXA_{get_node_type_name(node['type'])}"
        
        # Try to reuse existing material or create new
        mat = bpy.data.materials.get(mat_name)
        if mat is None:
            mat = bpy.data.materials.new(name=mat_name)
        
        mat.diffuse_color = color
        obj.active_material = mat