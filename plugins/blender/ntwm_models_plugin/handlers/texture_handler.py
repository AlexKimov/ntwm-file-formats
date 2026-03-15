import bpy
import os
from pathlib import Path

class TextureHandler:
    def __init__(self):
        pass
    
    def load_texture(self, filepath):
        try:
            img = bpy.data.images.load(filepath, check_existing=True)
            return img
        except Exception as e:
            print(f"Failed to load texture {filepath}: {e}")
            
            img = bpy.data.images.new("ntwm_tex", 32, 32)
            self.textures[filepath] = img
            
            return img
    
    def create_texture_for_material(self, \
        mat, texture_path, \
        transparency_color = (1.0, 1.0, 1.0, 1.0), \
        threshold = .5, \
        add_transparency = False):          
        try:    
            img = self.load_texture(texture_path)
            
            if img:                
                nodes = mat.node_tree.nodes
                links = mat.node_tree.links
            
                tex_node = nodes.new("ShaderNodeTexImage")
                tex_node.image = img
                tex_node.location = (-400, 100)
                
                principled = nodes.new("ShaderNodeBsdfPrincipled")
                links.new(tex_node.outputs["Color"], principled.inputs["Base Color"])
                principled.location = (-900, 400)                
                
                output = nodes.new("ShaderNodeOutputMaterial")
                links.new(principled.outputs["BSDF"], output.inputs["Surface"])
                output.location = (-1000, 600)
                
                if add_transparency:
                    key_color = nodes.new("ShaderNodeRGB")
                    key_color.outputs[0].default_value = transparency_color
                    key_color.location = (-200, 400)

                    tolerance_node = nodes.new("ShaderNodeValue")
                    tolerance_node.outputs[0].default_value = threshold
                    tolerance_node.location = (-400, 400)
                    
                    diff_node = nodes.new("ShaderNodeMixRGB")
                    diff_node.blend_type = 'DIFFERENCE'
                    diff_node.inputs["Fac"].default_value = 1.0 
                    diff_node.location = (0, 400)
                    links.new(tex_node.outputs["Color"], diff_node.inputs[1])
                    links.new(key_color.outputs[0], diff_node.inputs[2])

                    separate_rgb = nodes.new("ShaderNodeSeparateRGB")
                    links.new(diff_node.outputs["Color"], separate_rgb.inputs["Image"])
                    separate_rgb.location = (100, 600)
                    
                    add_node = nodes.new("ShaderNodeMath")
                    add_node.operation = 'ADD'
                    add_node.location = (-100, 600)
                    links.new(separate_rgb.outputs["R"], add_node.inputs[0])
                    links.new(separate_rgb.outputs["G"], add_node.inputs[1])

                    add_final = nodes.new("ShaderNodeMath")
                    add_final.operation = 'ADD'
                    links.new(add_node.outputs["Value"], add_final.inputs[0])
                    links.new(separate_rgb.outputs["B"], add_final.inputs[1])
                    add_final.location = (-300, 600)

                    compare_node = nodes.new("ShaderNodeMath")
                    compare_node.operation = 'LESS_THAN'
                    links.new(add_final.outputs["Value"], compare_node.inputs[0])
                    links.new(tolerance_node.outputs[0], compare_node.inputs[1])
                    compare_node.location = (-500, 600)

                    invert_node = nodes.new("ShaderNodeInvert")
                    links.new(compare_node.outputs["Value"], invert_node.inputs[1])
                    invert_node.location = (-700, 600)    
                    
                    links.new(invert_node.outputs["Color"], principled.inputs["Alpha"])  # маска → альфа                
                
        except Exception as e:
            print({'ERROR'}, f"Texure create failed: {str(e)}")
            import traceback
            traceback.print_exc()