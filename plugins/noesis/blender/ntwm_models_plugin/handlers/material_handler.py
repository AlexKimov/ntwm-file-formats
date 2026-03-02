# io_anim_ntwm/handlers/material_handler.py
import bpy

class MaterialHandler:
    def __init__(self):
        self.materials = {}
    
    def create_material(self, name, texture_name=None, two_sided=True):
        if name in bpy.data.materials:
            return bpy.data.materials[name]
        
        mat = bpy.data.materials.new(name=name)
        mat.use_nodes = True
        mat.blend_method = 'CLIP'
        if two_sided:
            mat.backface_culling = False
        
        self.materials[name] = mat
        return mat
    
    def apply_material_to_object(self, obj, material):
        if obj.data.materials:
            obj.data.materials[0] = material
        else:
            obj.data.materials.append(material)