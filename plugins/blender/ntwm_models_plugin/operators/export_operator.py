# io_anim_ntwm/operators/export_operator.py
import bpy
from pathlib import Path
import struct
import bmesh
from bpy_extras.io_utils import ExportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator

from ..parsers.anb_parser import ANBModel, NTWMMesh, NTWMMorphFrame, NTWMFrameMesh
from ..parsers.fxm_parser import FXMModel
from ..handlers.texture_handler import TextureHandler
from ..handlers.animation_handler import AnimationHandler
from ..utils.data_structures import Vector3F, Vector2F, Vector3UI16

from .. import consts as const


class ExportNTWMOperator(Operator, ExportHelper):
    bl_idname = "export_mesh.ntwm"
    bl_label = "Export Nosferatu ANB/FXM"
    bl_options = {'PRESET', 'UNDO'}
    
    filename_ext = ".anb"
    filter_glob: StringProperty(
        default="*.anb;*.fxm",
        options={'HIDDEN'},
        maxlen=255,
    )
    
    export_format: EnumProperty(
        name="Format",
        description="Choose export format",
        items=(
            ('ANB', "ANB", "Nosferatu The Wrath of Malachi ANB format with morph frames"),
            ('FXM', "FXM", "Nosferatu The Wrath of Malachi FXM format with bones"),
        ),
        default='ANB',
    )
    
    triangulate: BoolProperty(
        name="Triangulate",
        description="Triangulate all faces before export",
        default=False,
    )
    
    def execute(self, context):
        filepath = Path(self.filepath)
        file_ext = filepath.suffix.lower()
        
        if file_ext == '.anb' or self.export_format == 'ANB':
            self.export_anb(filepath, context)
        elif file_ext == '.fxm' or self.export_format == 'FXM':
            self.export_fxm(filepath, context)
        else:
            self.report({'ERROR'}, f"Unsupported file format: {file_ext}")
            return {'CANCELLED'}
        
        self.report({'INFO'}, f"Export completed: {filepath.name}")
        return {'FINISHED'}
    
    def export_anb(self, filepath, context):    
        context = bpy.context
        scene = context.scene

        initial_frame = scene.frame_current
        
        try:
            scene.frame_set(0)
            scene.frame_start = 0
            
            model = ANBModel()
            objects = [obj for obj in context.selected_objects if obj.type == 'MESH']

            if not objects:
                print("No mesh objects selected.")

            model.mesh_count = len(objects)

            for obj in objects:
                mesh_data = NTWMMesh()
                bm = bmesh.new()
             
                bm.from_mesh(obj.data)
                bm.verts.ensure_lookup_table()

                if triangulate:
                    bmesh.ops.triangulate(bm, faces=bm.faces[:])

                final_vertices = []
                final_indices = []
                vertex_map = {} #

                
                uv_layer = obj.data.uv_layers.active
                uv_map = {} 
                unique_uvs = []
                uv_lookup = {} 

                if uv_layer:
                    for poly in obj.data.polygons:
                        for loop_idx in poly.loop_indices:
                            uv = uv_layer.data[loop_idx].uv
                            uv_key = (uv.x, uv.y)
                            if uv_key not in uv_lookup:
                                uv_lookup[uv_key] = len(unique_uvs)
                                unique_uvs.append(Vector2F(uv.x, uv.y))
                            uv_map[loop_idx] = uv_lookup[uv_key]
                    
                    mesh_data.uv_coords = unique_uvs
                    mesh_data.uv_count = len(unique_uvs)

                for face in bm.faces:
                    face_indices = []
                    for i, vert in enumerate(face.verts):
                        uv_idx = -1
                        if uv_layer:
                            loop_idx = face.loops[i].index
                            uv_idx = uv_map.get(loop_idx, -1)
                        
                        vert_key = (vert.index, uv_idx) 
                        
                        if vert_key not in vertex_map:
                            new_idx = len(final_vertices)
                            vertex_map[vert_key] = new_idx
                            
                            pos = const.BLENDER_DX_MATRIX @ vert.co
                            norm = const.BLENDER_DX_NORMAL_MATRIX @ vert.normal
                            norm.normalize()
                            
                            final_vertices.append((Vector3F(pos.x, pos.y, pos.z), Vector3F(norm.x, norm.y, norm.z)))
                        
                        face_indices.append(vertex_map[vert_key])
                    
                    if len(face_indices) == 3:
                        final_indices.append(Vector3UI16(face_indices[0], face_indices[1], face_indices[2]))

                mesh_data.vertices = final_vertices # Assign list of tuples/objects
                mesh_data.vertex_count = len(final_vertices)
                mesh_data.faces = final_indices
                mesh_data.face_count = len(final_indices)
               
                if uv_layer:
                    for face in bm.faces:
                        face_uv_indices = []
                        for i, vert in enumerate(face.verts):
                            loop_idx = face.loops[i].index
                            uv_idx = uv_map.get(loop_idx, 0)

                            vert_key = (vert.index, uv_idx)
                            new_vert_idx = vertex_map[vert_key]
                            
                            face_uv_indices.append(uv_idx) 
                        
                        if len(face_uv_indices) == 3:
                             mesh_data.uv_indices.append(Vector3UI16(face_uv_indices[0], face_uv_indices[1], face_uv_indices[2]))

                bm.free()
                model.meshes.append(mesh_data)
                
            all_keyframes = set()

            for obj in objects:
                if obj.data.animation_data and obj.data.animation_data.action:
                    for fcurve in obj.data.animation_data.action.fcurves:
                        for keyframe in fcurve.keyframe_points:
                            all_keyframes.add(int(keyframe.co.x))
            
            model.morph_frame_count = len(all_keyframes) - 1            
            sorted_keyframes = sorted(all_keyframes[1:])
            
            if sorted_keyframes:
                depsgraph = context.evaluated_depsgraph_get()
                
                for frame_num in sorted_keyframes:
                    morph_frame = NTWMMorphFrame()
                    scene.frame_set(frame_num)
                    
                    for obj_idx, obj in enumerate(objects):
                        frame_mesh = NTWMFrameMesh()
                        
                        eval_obj = obj.evaluated_get(depsgraph)
                        eval_mesh = eval_obj.to_mesh(preserve_all_data_layers=True, depsgraph=depsgraph)

                        for vert in eval_mesh.vertices:
                            pos = const.BLENDER_DX_MATRIX @ vert.co
                            frame_mesh.positions.append(Vector3F(pos.x, pos.y, pos.z))
                            
                            norm = const.BLENDER_DX_NORMAL_MATRIX @ vert.normal
                            norm.normalize()
                            frame_mesh.normals.append(Vector3F(norm.x, norm.y, norm.z))
                        
                        eval_obj.to_mesh_clear()
                        morph_frame.frame_meshes.append(frame_mesh)
                    
                    model.morph_frames.append(morph_frame)

            model.write(str(filepath))
            
        except Exception as e:
            print(f"Export failed: {e}")
            raise
        finally:
            scene.frame_set(initial_frame)       
    
    def export_fxm(self, filepath, context):
        model = FXMModel()
        
        objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
        if not objects:
            objects = [obj for obj in bpy.data.objects if obj.type == 'MESH']
        
        if not objects:
            self.report({'ERROR'}, "No mesh objects to export")
            return {'CANCELLED'}
        
        arm_obj = None
        for obj in context.selected_objects:
            if obj.type == 'ARMATURE':
                arm_obj = obj
                break
        
        if not arm_obj:
            for obj in objects:
                if obj.parent and obj.parent.type == 'ARMATURE':
                    arm_obj = obj.parent
                    break
        
        animation_handler = AnimationHandler()
        
        if arm_obj:
            model.type = FXMModel.FXM_KEYPOSE
            model.bones = animation_handler.export_bones_to_fxm(arm_obj)
            model.name = arm_obj.name
        else:
            model.type = FXMModel.FXM
        
        for obj in objects:
            mesh_data = type('Mesh', (), {})()
            mesh_data.vertices = []
            mesh_data.face_indexes = []
            mesh_data.texture_name = ""
            
            bm = bmesh.new()
            bm.from_mesh(obj.data)
            bm.verts.ensure_lookup_table()
            
            if self.triangulate:
                bmesh.ops.triangulate(bm, faces=bm.faces[:])
            
            if self.export_textures and obj.data.materials:
                mat = obj.data.materials[0]
                texture_handler = TextureHandler()
                mesh_data.texture_name = texture_handler.export_texture_reference(mat.name)
            
            for vert in bm.verts:
                vertex = type('Vertex', (), {})()
                vertex.coordinates = Vector3F(vert.co.x, vert.co.y, vert.co.z)
                vertex.normal = Vector3F(vert.normal.x, vert.normal.y, vert.normal.z)
                
                vertex.uv = Vector2F()
                if obj.data.uv_layers.active:
                    uv_layer = obj.data.uv_layers.active.data
                    for poly in obj.data.polygons:
                        for loop_idx in poly.loop_indices:
                            vert_idx = poly.vertices[loop_idx]
                            if vert_idx == vert.index:
                                uv = uv_layer[loop_idx].uv
                                vertex.uv = Vector2F(uv.x, uv.y)
                                break
                        if vertex.uv.x != 0 or vertex.uv.y != 0:
                            break
                
                mesh_data.vertices.append(vertex)
            
            for face in bm.faces:
                if len(face.verts) == 3:
                    indices = Vector3UI16(
                        face.verts[0].index,
                        face.verts[1].index,
                        face.verts[2].index
                    )
                    mesh_data.face_indexes.append(indices)
            
            mesh_data.vertex_count = len(mesh_data.vertices)
            mesh_data.face_count = len(mesh_data.face_indexes)
            
            bm.free()
            model.meshes.append(mesh_data)
        
        model.mesh_count = len(model.meshes)
        model.write(str(filepath))