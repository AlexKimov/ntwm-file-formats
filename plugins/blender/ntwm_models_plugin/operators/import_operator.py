# io_anim_ntwm/operators/import_operator.py
import bpy
import os
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator
from ..parsers.anb_parser import ANBModel
from ..parsers.fxm_parser import FXMModel, MOTAnimation
from ..handlers.texture_handler import TextureHandler
from ..handlers.material_handler import MaterialHandler
from ..handlers.animation_handler import AnimationHandler
import bmesh
import struct

class ImportNTWMOperator(Operator, ImportHelper):
    bl_idname = "import_mesh.ntwm"
    bl_label = "Import Nosferatu ANB/FXM"
    bl_options = {'PRESET', 'UNDO'}
    
    filename_ext = ".anb"
    filter_glob: StringProperty(
        default="*.anb;*.fxm;",
        options={'HIDDEN'},
        maxlen=255,
    )
    
    import_morphs: BoolProperty(
        name="Import Morph Frames",
        description="Import morph target frames as shape keys",
        default=True,
    )
    
    import_animation: BoolProperty(
        name="Import Animation",
        description="Import .mot animation file if available",
        default=True,
    )
    
    import_textures: BoolProperty(
        name="Import Textures",
        description="Load and apply textures",
        default=True,
    )
    
    texture_directory: StringProperty(
        name="Texture Directory",
        description="Directory to search for textures",
        default="",
        subtype='DIR_PATH',
    )
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
        
    def execute(self, context):
        filepath = self.filepath
        file_ext = os.path.splitext(filepath)[1].lower()
        
        texture_handler = TextureHandler()
        material_handler = MaterialHandler()
        animation_handler = AnimationHandler()
        
        if self.texture_directory:
            texture_handler.set_texture_directory(self.texture_directory)
        
        # Create collection for this import
        collection = bpy.data.collections.new("NTWM_Import")
        context.scene.collection.children.link(collection)
        
        try:
            if file_ext == '.anb':
                self.import_anb(filepath, collection, texture_handler, 
                              material_handler, animation_handler, context)
            elif file_ext == '.fxm':
                self.import_fxm(filepath, collection, texture_handler,
                              material_handler, animation_handler, context)
            else:
                self.report({'ERROR'}, f"Unsupported file format: {file_ext}")
                return {'CANCELLED'}
            
            self.report({'INFO'}, "Import completed successfully")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Import failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'CANCELLED'}
    
    def import_anb(self, filepath, collection, texture_handler, 
                   material_handler, animation_handler, context):
        """Import ANB format"""
        model = ANBModel()
        model.read(filepath)
        
        mesh_index = 0
        for mesh_data in model.meshes:
            # Create Blender mesh
            bm = bmesh.new()
            
            # Create vertices
            vert_map = {}
            for i, (pos, norm) in enumerate(mesh_data.vertices):
                vert = bm.verts.new(pos.to_tuple())
                vert_map[i] = vert
            
            bm.verts.ensure_lookup_table()
            
            # Create faces
            for face_idx, face in enumerate(mesh_data.faces):
                indices = face.to_tuple()
                try:
                    face_verts = [vert_map[i] for i in indices]
                    bm.faces.new(face_verts)
                except:
                    pass  # Skip invalid faces
            
            # Create mesh object
            mesh = bpy.data.meshes.new(f"ANB_Mesh_{mesh_index}")
            bm.to_mesh(mesh)
            bm.free()
            
            # Add UV layer
            if mesh_data.uv_coords and mesh_data.uv_indices:
                mesh.uv_layers.new(name="UVMap")
                uv_layer = mesh.uv_layers.active.data
                
                for poly_idx, poly in enumerate(mesh.polygons):
                    if poly_idx < len(mesh_data.uv_indices):
                        uv_idx_face = mesh_data.uv_indices[poly_idx]
                        for loop_idx, loop in enumerate(poly.loop_indices):
                            if loop_idx < 3:
                                uv_coord_idx = uv_idx_face.to_tuple()[loop_idx]
                                if uv_coord_idx < len(mesh_data.uv_coords):
                                    uv = mesh_data.uv_coords[uv_coord_idx]
                                    uv_layer[loop].uv = uv.to_tuple()
            
            mesh.update()
            
            # Create object
            obj = bpy.data.objects.new(f"ANB_Mesh_{mesh_index}", mesh)
            collection.objects.link(obj)
            
            # Apply material
            if self.import_textures and mesh_data.texture_name:
                mat = texture_handler.create_material_with_texture(
                    mesh_data.texture_name, 
                    mesh_data.texture_name
                )
                material_handler.apply_material_to_object(obj, mat)
            
            # Import morph frames as shape keys
            if self.import_morphs and model.morph_frames:
                animation_handler.create_shape_keys_from_morphs(
                    obj, model.morph_frames, mesh_index
                )
            
            mesh_index += 1
    
    def import_fxm(self, filepath, collection, texture_handler,
                   material_handler, animation_handler, context):
        """Import FXM format"""
        model = FXMModel()
        model.read(filepath)
        
        # Create armature if bones exist
        arm_obj = None
        bone_map = {}
        
        if model.bones:
            arm_obj, bone_map = animation_handler.create_armature_from_bones(
                model.bones, "NTWM_Armature"
            )
            collection.objects.link(arm_obj)
        
        # Import animation if available
        if self.import_animation and arm_obj:
            # Look for .mot file in same directory
            mot_path = os.path.splitext(filepath)[0] + ".mot"
            if os.path.exists(mot_path):
                motion = MOTAnimation()
                motion.read(mot_path)
                animation_handler.create_animation_from_motion(
                    arm_obj, bone_map, motion, "NTWM_Animation"
                )
        
        mesh_index = 0
        for mesh_data in model.meshes:
            # Create Blender mesh
            bm = bmesh.new()
            
            # Create vertices
            vert_map = {}
            for i, vertex in enumerate(mesh_data.vertices):
                vert = bm.verts.new(vertex.coordinates.to_tuple())
                vert_map[i] = vert
            
            bm.verts.ensure_lookup_table()
            
            # Create faces
            for face in mesh_data.face_indexes:
                indices = face.to_tuple()
                try:
                    face_verts = [vert_map[i] for i in indices]
                    bm.faces.new(face_verts)
                except:
                    pass
            
            # Create mesh object
            mesh = bpy.data.meshes.new(f"FXM_Mesh_{mesh_index}")
            bm.to_mesh(mesh)
            bm.free()
            
            # Add UV layer
            if mesh_data.vertices and mesh_data.vertices[0].uv:
                mesh.uv_layers.new(name="UVMap")
                uv_layer = mesh.uv_layers.active.data
                
                for poly_idx, poly in enumerate(mesh.polygons):
                    if poly_idx < len(mesh_data.face_indexes):
                        face = mesh_data.face_indexes[poly_idx]
                        for loop_idx, loop in enumerate(poly.loop_indices):
                            if loop_idx < 3:
                                vert_idx = face.to_tuple()[loop_idx]
                                if vert_idx < len(mesh_data.vertices):
                                    uv = mesh_data.vertices[vert_idx].uv
                                    uv_layer[loop].uv = uv.to_tuple()
            
            mesh.update()
            
            # Create object
            obj = bpy.data.objects.new(f"FXM_Mesh_{mesh_index}", mesh)
            collection.objects.link(obj)
            
            # Apply material
            if self.import_textures and mesh_data.texture_name:
                mat = texture_handler.create_material_with_texture(
                    mesh_data.texture_name,
                    mesh_data.texture_name
                )
                material_handler.apply_material_to_object(obj, mat)
            
            # Parent to armature
            if arm_obj:
                modifier = obj.modifiers.new(name="Armature", type='ARMATURE')
                modifier.object = arm_obj
                obj.parent = arm_obj
            
            mesh_index += 1