import bpy

class MaterialHandler:
    def __init__(self):
        self.materials = {}
    
    def create_material(self, name):
        try:
            if name in bpy.data.materials:
                mat = bpy.data.materials[name]
                if mat.node_tree:
                    mat.node_tree.nodes.clear()                
            else:
                mat = bpy.data.materials.new(name=name)

            mat.use_nodes = True
            mat.node_tree.nodes.clear()
            mat.blend_method = 'CLIP'        
            mat.use_backface_culling = True            
        except Exception as e:       
            print({'ERROR'}, f"Material create failed: {str(e)}")
            import traceback
            traceback.print_exc() 
            
            return None            
        return mat        
    
    def apply_material_to_object(self, obj, material):
        if obj.data.materials:
            obj.data.materials[0] = material
        else:
            obj.data.materials.append(material)
         