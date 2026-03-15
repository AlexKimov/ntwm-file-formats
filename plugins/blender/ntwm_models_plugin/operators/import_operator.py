import bpy
from pathlib import Path
import struct
import bmesh
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty, IntProperty, FloatProperty
from bpy.types import Operator

from ..parsers.anb_parser import ANBModel
from ..parsers.fxm_parser import FXMModel, MOTAnimation
from ..handlers.animation_handler import AnimationHandler
from ..utils import helpers as Helper

from .. import consts as const
from mathutils import Matrix

from collections import defaultdict


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
    
    transform_axes: BoolProperty(
        name="Transform axes",
        description="Apply transformation from Directx to Blender coordinate systems",
        default=True,
    )
    
    import_animation: BoolProperty(
        name="Import morphs",
        description="Import animation file if available",
        default=True,
    )
    
    focus_view: BoolProperty(
        name="Focus view on model",
        description="Focus view on model after it loaded",
        default=True,
    )    
    
    fps: FloatProperty(
        name="Keyframes scale",
        description="Scale keyframes along timeline",
        default=1,
        min=0.01,
        max=10,
    )
    
    fps: IntProperty(
        name="Scene fps",
        description="Set scene fps",
        default=24,
        min=1,
        max=100,
    ) 
    
    def execute(self, context):
        filepath = Path(self.filepath)
        file_ext = filepath.suffix.lower()
        
        animation_handler = AnimationHandler()
 
        collection_name = filepath.stem
        collection = bpy.data.collections.new(collection_name)
        context.scene.collection.children.link(collection)
        
        try:
            imported_count = 0
            
            if file_ext == '.anb':
                imported_count = self.import_anb(filepath, collection, animation_handler)
            elif file_ext == '.fxm':
                imported_count = self.import_fxm(filepath, collection, animation_handler)
                    
            if imported_count > 0:
                Helper.apply_smoothing_to_collection(collection)
                if self.focus_view:
                    Helper.focus_view_on_collection(collection, self.transform_axes)
                self.report({'INFO'}, f"Imported {imported_count} objects: {filepath.name}")
            else:
                self.report({'WARNING'}, f"No objects imported from {filepath.name}")
                                             
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Import failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'CANCELLED'}
              
            
    def import_anb(self, filepath, collection, animation_handler):
        model = ANBModel()
        model.read(str(filepath))
        
        mesh_index = 0
        for mesh_data in model.meshes:
            bm = bmesh.new()
            
            vert_map = [0] * mesh_data.vertex_count
            for i, (pos, norm) in enumerate(mesh_data.vertices):
                vert_map[i] = bm.verts.new(pos.to_tuple())
            
            bm.verts.ensure_lookup_table()
            
            for face_idx, face in enumerate(mesh_data.faces):
                face_verts = [vert_map[i] for i in face.to_tuple()]
                try:
                    bm.faces.new(face_verts)
                except:
                    pass                
            
            mesh = bpy.data.meshes.new(f"Mesh: {mesh_index}")
            bm.to_mesh(mesh)
            bm.free()
            
            if mesh_data.uv_coords and mesh_data.uv_indices:
                mesh.uv_layers.new(name="UVMap")
                uv_layer = mesh.uv_layers.active.data

                uv_data = [0.0] * (len(mesh.loops) * 2)  

                for poly_idx, poly in enumerate(mesh.polygons):
                    uv_idx_face = mesh_data.uv_indices[poly_idx].to_tuple() 
                    for loop_idx, loop_id in enumerate(poly.loop_indices):
                        uv_coord_idx = uv_idx_face[loop_idx]
                        u, v = mesh_data.uv_coords[uv_coord_idx].to_tuple()
                        base_idx = loop_id * 2
                        uv_data[base_idx] = u
                        uv_data[base_idx + 1] = 1.0 - v 

                uv_layer.foreach_set('uv', uv_data)
            mesh.update()
            
            obj = bpy.data.objects.new(f"Mesh: {mesh_index}", mesh)
            collection.objects.link(obj)
            
            if self.transform_axes:
                obj.matrix_world = const.BLENDER_DX_MATRIX @ obj.matrix_world

            if self.import_animation and model.morph_frames:
                animation_handler.create_vertex_morph_animation(
                    obj, model.morph_frames, mesh_index, fps = self.fps, \
                    fps_scale = self.fps
                )
                                
            mesh_index += 1
             
        return mesh_index
    
    
    def import_fxm(self, filepath, collection, animation_handler):
        model = FXMModel()
        model.read(str(filepath))
        
        arm_obj = None

        if model.bones:
            arm_obj = animation_handler.create_armature_from_bones(
                model.bones, f"{collection.name}_Armature", self.transform_axes
            )
            collection.objects.link(arm_obj)
        
        # Import animation if available
        if self.import_animation and arm_obj:
            mot_path = "F:/Games/Nosferatu - Wrath of Malachi2/Version/Data/L06_N_Gethit0.mot"
            if mot_path:
                motion = MOTAnimation()
                motion.read(str(mot_path))
                animation_handler.create_animation_from_motion(
                    arm_obj, motion, f"{collection.name}_Anim"
                )
                
        bone_names = [bone.name for bone in model.bones]
        
        mesh_index = 0
        for mesh_data in model.meshes:
            name = f"Mesh: {mesh_data.name}"
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
                     
            mesh = bpy.data.meshes.new(name)
            bm.to_mesh(mesh)
            bm.free()
 
            mesh.update()
        
            obj = bpy.data.objects.new(name, mesh)
            collection.objects.link(obj)   

            group_lookup = {}
            for name in bone_names:
                if name not in obj.vertex_groups:
                    vg = obj.vertex_groups.new(name=name)
                else:
                    vg = obj.vertex_groups[name]
                group_lookup[name] = vg
               
            batch = defaultdict(list)
            
            vertex_idx = 0
            for v in mesh_data.weightedVertexes:  
                for w, bone_idx in zip(v.weights, v.boneIndexes):
                    if bone_idx >= len(bone_names):
                        print(f"Warning: bone index {bone_idx} out of range at vertex {vertex_idx}")
                        continue
                    group_name = bone_names[bone_idx]
                    batch[(group_name, w)].append(vertex_idx)
                vertex_idx += 1                    
            
            for (group_name, weight), vertices in batch.items():
                vg = group_lookup[group_name]
                vg.add(vertices, weight, 'REPLACE')               
            
            if self.transform_axes:
                obj.matrix_world = const.BLENDER_DX_MATRIX @ obj.matrix_world
                      
            if arm_obj:
                modifier = obj.modifiers.new(name="Armature", type='ARMATURE')
                modifier.object = arm_obj
                obj.parent = arm_obj
            
            mesh_index += 1         
        
        return mesh_index