# io_anim_ntwm/handlers/texture_handler.py
import bpy
import os
from pathlib import Path

class TextureHandler:
    def __init__(self):
        self.textures = {}
        self.texture_directory = ""
    
    def set_texture_directory(self, directory):
        self.texture_directory = directory
    
    def find_texture(self, texture_name):
        """Find texture file in common locations"""
        if not texture_name:
            return None
        
        # Check if already loaded
        if texture_name in self.textures:
            return self.textures[texture_name]
        
        # Common extensions to try
        extensions = ["", ".jpg", ".jpeg", ".tga", ".png", ".dds", ".bmp"]
        
        # Try current directory
        current_dir = bpy.path.abspath("//")
        for ext in extensions:
            filepath = os.path.join(current_dir, texture_name + ext)
            if os.path.exists(filepath):
                return self.load_texture(filepath, texture_name + ext)
        
        # Try texture directory
        if self.texture_directory:
            for ext in extensions:
                filepath = os.path.join(self.texture_directory, texture_name + ext)
                if os.path.exists(filepath):
                    return self.load_texture(filepath, texture_name + ext)
        
        # Try game data directories
        game_dirs = [
            "F:/Games/Nosferatu - The Wrath of Malachi/Version/Data/",
            "C:/Games/Nosferatu/Data/",
        ]
        
        for game_dir in game_dirs:
            if os.path.exists(game_dir):
                for ext in extensions:
                    filepath = os.path.join(game_dir, texture_name + ext)
                    if os.path.exists(filepath):
                        return self.load_texture(filepath, texture_name + ext)
        
        return None
    
    def load_texture(self, filepath, name):
        """Load texture into Blender"""
        if filepath in self.textures:
            return self.textures[filepath]
        
        try:
            # Check if image already exists
            for img in bpy.data.images:
                if img.filepath == filepath:
                    self.textures[filepath] = img
                    return img
            
            # Load new image
            img = bpy.data.images.load(filepath, check_existing=True)
            self.textures[filepath] = img
            return img
        except Exception as e:
            print(f"Failed to load texture {filepath}: {e}")
            # Create placeholder
            img = bpy.data.images.new(name, 32, 32)
            self.textures[filepath] = img
            return img
    
    def create_material_with_texture(self, name, texture_path):
        """Create a material with texture"""
        # Check if material exists
        if name in bpy.data.materials:
            return bpy.data.materials[name]
        
        mat = bpy.data.materials.new(name=name)
        mat.use_nodes = True
        
        if texture_path:
            img = self.find_texture(texture_path)
            if img:
                nodes = mat.node_tree.nodes
                links = mat.node_tree.links
                
                # Get principled BSDF
                bsdf = nodes.get("Principled BSDF")
                if bsdf:
                    # Create texture node
                    tex_node = nodes.new("ShaderNodeTexImage")
                    tex_node.image = img
                    tex_node.location = (-300, 0)
                    
                    # Link to base color
                    links.new(tex_node.outputs["Color"], bsdf.inputs["Base Color"])
        
        return mat
    
    def export_texture_reference(self, texture_name):
        """Get texture name for export"""
        if not texture_name:
            return ""
        
        # Remove extension for storage
        base = os.path.basename(texture_name)
        for ext in [".jpg", ".jpeg", ".tga", ".png", ".dds", ".bmp"]:
            if base.lower().endswith(ext):
                return base[:-len(ext)]
        
        return base