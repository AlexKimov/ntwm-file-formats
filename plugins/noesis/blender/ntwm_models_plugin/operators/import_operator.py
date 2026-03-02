import bpy
from pathlib import Path
import struct
import bmesh
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty, IntProperty, FloatProperty
from bpy.types import Operator

from ..parsers.anb_parser import ANBModel
from ..parsers.fxm_parser import FXMModel, MOTAnimation
from ..handlers.texture_handler import TextureHandler
from ..handlers.material_handler import MaterialHandler
from ..handlers.animation_handler import AnimationHandler

def focus_view_on_collection(collection):  
    bpy.ops.object.select_all(action='DESELECT')
    if collection.objects:
        for obj in collection.objects:
            obj.select_set(True)     

    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for region in area.regions:
                if region.type == 'WINDOW':
                    with bpy.context.temp_override(area=area, region=region):
                        bpy.ops.view3d.view_selected()    
                    break
            if 'break' in locals():
                break
            
    
class ImportNTWMOperator(Operator, ImportHelper):
    bl_idname = "import_mesh.ntwm"
    bl_label = "Import Nosferatu ANB/FXM"
    bl_options = {'PRESET', 'UNDO'}
    
    filename_ext = ".anb"
    filter_glob: StringProperty(
        default="*.anb;*.fxm;*.mot",
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
    
    create_morph_timeline: BoolProperty(
        name="Create Morph Timeline",
        description="Auto-create animation timeline for morph frames (ANB only)",
        default=True,
    )
    
    morph_animation_type: EnumProperty(
        name="Morph Animation Type",
        description="How to animate morph frames",
        items=(
            ('SEQUENTIAL', "Sequential", "Each morph displays for 1 second"),
            ('LOOP', "Frame-by-Frame", "Each morph displays for 1 frame (looping)"),
        ),
        default='LOOP',
    )
    
    morph_fps: IntProperty(
        name="Morph FPS",
        description="Frames per morph (for Sequential mode)",
        default=10,
        min=1,
        max=120,
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
    
    mesh_shading: EnumProperty(
        name="Mesh Shading",
        description="Apply smoothing to imported mesh faces",
        items=(
            ('SMOOTH', "Smooth", "Apply smooth shading to all faces"),
            ('FLAT', "Flat", "Keep flat shading (hard edges)"),
            ('AUTO', "Auto Detect", "Use existing face normals (default)"),
        ),
        default='SMOOTH',
    )
    
    auto_smooth_angle: FloatProperty(
        name="Auto Smooth Angle",
        description="Angle threshold for auto smooth (degrees)",
        default=30.0,
        min=0.0,
        max=90.0,
        step=1.0,
        precision=1,
    )
    
    def execute(self, context):
        filepath = Path(self.filepath)
        file_ext = filepath.suffix.lower()
        
        texture_handler = TextureHandler()
        material_handler = MaterialHandler()
        animation_handler = AnimationHandler()
        
        if self.texture_directory:
            texture_handler.set_texture_directory(self.texture_directory)
        
        texture_handler.file_directory = str(filepath.parent)
        
        # Create collection named after filename (without extension)
        collection_name = filepath.stem
        collection = bpy.data.collections.new(collection_name)
        context.scene.collection.children.link(collection)
        
        try:
            imported_count = 0
            
            if file_ext == '.anb':
                imported_count = self.import_anb(filepath, collection, texture_handler, 
                              material_handler, animation_handler, context)
            elif file_ext == '.fxm':
                imported_count = self.import_fxm(filepath, collection, texture_handler,
                              material_handler, animation_handler, context)
            else:
                self.report({'ERROR'}, f"Unsupported file format: {file_ext}")
                return {'CANCELLED'}
                    
            # Focus view on imported collection
            if imported_count > 0:
                focus_view_on_collection(collection)
                # Apply smoothing to all imported meshes
                self.apply_smoothing_to_collection(collection, context)
                self.report({'INFO'}, f"Imported {imported_count} objects: {filepath.name}")
            else:
                self.report({'WARNING'}, f"No objects imported from {filepath.name}")
                
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Import failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'CANCELLED'}
    
    def apply_smoothing_to_collection(self, collection, context):
        """Apply mesh smoothing to all objects in a collection"""
        if self.mesh_shading not in ['SMOOTH', 'AUTO']:
            return
        
        smoothed_count = 0
        
        for obj in collection.objects:
            if obj.type != 'MESH':
                continue
                
            mesh = obj.data
            
            # Set all polygons to smooth
            if self.mesh_shading == 'SMOOTH':
                for poly in mesh.polygons:
                    poly.use_smooth = True
                 
            
    def import_anb(self, filepath, collection, texture_handler, 
                   material_handler, animation_handler, context):
        model = ANBModel()
        model.read(str(filepath))
        
        mesh_index = 0
        for mesh_data in model.meshes:
            bm = bmesh.new()
            
            vert_map = {}
            for i, (pos, norm) in enumerate(mesh_data.vertices):
                vert = bm.verts.new(pos.to_tuple())
                vert_map[i] = vert
            
            bm.verts.ensure_lookup_table()
            
            for face_idx, face in enumerate(mesh_data.faces):
                indices = face.to_tuple()
                try:
                    face_verts = [vert_map[i] for i in indices]
                    bm.faces.new(face_verts)
                except:
                    pass
            
            mesh = bpy.data.meshes.new(f"Mesh_{mesh_index}")
            bm.to_mesh(mesh)
            bm.free()
            
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
            
            obj = bpy.data.objects.new(f"{collection.name}_Mesh_{mesh_index}", mesh)
            collection.objects.link(obj)
            
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
                
                # Create animation timeline
                if self.create_morph_timeline and obj.data.shape_keys:
                    if self.morph_animation_type == 'SEQUENTIAL':
                        animation_handler.create_morph_animation(
                            obj, len(model.morph_frames), self.morph_fps
                        )
                    else:  # LOOP
                        animation_handler.create_morph_animation_loop(
                            obj, len(model.morph_frames), fps=self.morph_fps
                        )
            
            mesh_index += 1
        
        return mesh_index
    
    
    def import_fxm(self, filepath, collection, texture_handler,
                   material_handler, animation_handler, context):
        model = FXMModel()
        model.read(str(filepath))
        
        arm_obj = None
        bone_map = {}
        imported_objects = []
        
        if model.bones:
            arm_obj, bone_map = animation_handler.create_armature_from_bones(
                model.bones, f"{collection.name}_Armature"
            )
            collection.objects.link(arm_obj)
            imported_objects.append(arm_obj)
        
        # Import animation if available
        if self.import_animation and arm_obj:
            mot_path = filepath.with_suffix('.mot')
            if mot_path.exists():
                motion = MOTAnimation()
                motion.read(str(mot_path))
                animation_handler.create_animation_from_motion(
                    arm_obj, bone_map, motion, f"{collection.name}_Anim"
                )
        
        mesh_index = 0
        for mesh_data in model.meshes:
            bm = bmesh.new()
            
            vert_map = {}
            for i, vertex in enumerate(mesh_data.vertices):
                vert = bm.verts.new(vertex.coordinates.to_tuple())
                vert_map[i] = vert
            
            bm.verts.ensure_lookup_table()
            
            for face in mesh_data.face_indexes:
                indices = face.to_tuple()
                try:
                    face_verts = [vert_map[i] for i in indices]
                    bm.faces.new(face_verts)
                except:
                    pass
            
            mesh = bpy.data.meshes.new(f"{collection.name}_Mesh_{mesh_index}")
            bm.to_mesh(mesh)
            bm.free()
            
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
            
            obj = bpy.data.objects.new(f"{collection.name}_Mesh_{mesh_index}", mesh)
            collection.objects.link(obj)
            imported_objects.append(obj)
            
            for poly in mesh.polygons:
                poly.use_smooth = True             
            
            if self.import_textures and mesh_data.texture_name:
                mat = texture_handler.create_material_with_texture(
                    mesh_data.texture_name,
                    mesh_data.texture_name
                )
                material_handler.apply_material_to_object(obj, mat)
            
            if arm_obj:
                modifier = obj.modifiers.new(name="Armature", type='ARMATURE')
                modifier.object = arm_obj
                obj.parent = arm_obj
            
            mesh_index += 1
        
        # Select all imported objects
        bpy.ops.object.select_all(action='DESELECT')
        for obj in imported_objects:
            obj.select_set(True)
            if obj.type == 'ARMATURE':
                context.view_layer.objects.active = obj
        
        # Set timeline to start
        context.scene.frame_set(1)
        
        return mesh_index