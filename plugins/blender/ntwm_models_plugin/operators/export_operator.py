# io_anim_ntwm/operators/export_operator.py
import bpy
import os
import bmesh
import struct
from bpy_extras.io_utils import ExportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator
from ..parsers.anb_parser import ANBModel, NTWMMesh, NTWMMorphFrame, NTWMFrameMesh
from ..parsers.fxm_parser import FXMModel, MOTAnimation
from ..handlers.texture_handler import TextureHandler
from ..handlers.animation_handler import AnimationHandler
from ..utils.data_structures import Vector3F, Vector2F, Vector3UI16

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
            ('ANB', "ANB", "Nosferatu ANB format with morph frames"),
            ('FXM', "FXM", "Nosferatu FXM format with bones"),
        ),
        default='ANB',
    )
    
    export_morphs: BoolProperty(
        name="Export Morph Frames",
        description="Export shape keys as morph frames",
        default=True,
    )
    
    export_textures: BoolProperty(
        name="Export Texture References",
        description="Include texture references in export",
        default=True,
    )
    
    triangulate: BoolProperty(
        name="Triangulate",
        description="Triangulate all faces before export",
        default=True,
    )
    
    def execute(self, context):
        filepath = self.filepath
        file_ext = os.path.splitext(filepath)[1].lower()
        
        # Determine format from extension or selection
        if file_ext == '.anb' or self.export_format == 'ANB':
            self.export_anb(filepath, context)
        elif file_ext == '.fxm' or self.export_format == 'FXM':
            self.export_fxm(filepath, context)
        else:
            self.report({'ERROR'}, f"Unsupported file format: {file_ext}")
            return {'CANCELLED'}
        
        self.report({'INFO'}, "Export completed successfully")
        return {'FINISHED'}
    
    def export_anb(self, filepath, context):
        """Export to ANB format"""
        model = ANBModel()
        
        # Get selected objects or all mesh objects
        objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
        if not objects:
            objects = [obj for obj in bpy.data.objects if obj.type == 'MESH']
        
        if not objects:
            self.report({'ERROR'}, "No mesh objects to export")
            return {'CANCELLED'}
        
        model.mesh_count = len(objects)
        model.morph_frame_count = 1  # Base frame + morph frames
        
        # Check for shape keys
        max_shape_keys = 0
        for obj in objects:
            if obj.data.shape_keys and obj.data.shape_keys.key_blocks:
                shape_key_count = len(obj.data.shape_keys.key_blocks) - 1  # Exclude basis
                max_shape_keys = max(max_shape_keys, shape_key_count)
        
        if self.export_morphs and max_shape_keys > 0:
            model.morph_frame_count = max_shape_keys + 1
        
        # Process each mesh
        for obj in objects:
            mesh_data = NTWMMesh()
            bm = bmesh.new()
            bm.from_mesh(obj.data)
            bm.verts.ensure_lookup_table()
            
            # Triangulate if needed
            if self.triangulate:
                bmesh.ops.triangulate(bm, faces=bm.faces[:])
            
            mesh_data.vertex_count = len(bm.verts)
            mesh_data.face_count = len(bm.faces)
            
            # Export texture name
            if self.export_textures and obj.data.materials:
                mat = obj.data.materials[0]
                mesh_data.texture_name = mat.name
            
            # Export vertices
            for vert in bm.verts:
                pos = Vector3F(vert.co.x, vert.co.y, vert.co.z)
                norm = Vector3F(vert.normal.x, vert.normal.y, vert.normal.z)
                mesh_data.vertices.append((pos, norm))
            
            # Export faces
            for face in bm.faces:
                if len(face.verts) == 3:
                    indices = Vector3UI16(
                        face.verts[0].index,
                        face.verts[1].index,
                        face.verts[2].index
                    )
                    mesh_data.faces.append(indices)
            
            # Export UVs
            if obj.data.uv_layers.active:
                uv_layer = obj.data.uv_layers.active.data
                uv_dict = {}
                uv_list = []
                
                for poly in obj.data.polygons:
                    for loop_idx in poly.loop_indices:
                        uv = uv_layer[loop_idx].uv
                        uv_key = (uv.x, uv.y)
                        if uv_key not in uv_dict:
                            uv_dict[uv_key] = len(uv_list)
                            uv_list.append(Vector2F(uv.x, uv.y))
                
                mesh_data.uv_coords = uv_list
                mesh_data.uv_count = len(uv_list)
                
                # Create UV indices per face
                for poly in obj.data.polygons:
                    face_uv_indices = []
                    for loop_idx in poly.loop_indices:
                        uv = uv_layer[loop_idx].uv
                        uv_key = (uv.x, uv.y)
                        face_uv_indices.append(uv_dict[uv_key])
                    
                    if len(face_uv_indices) == 3:
                        mesh_data.uv_indices.append(Vector3UI16(
                            face_uv_indices[0],
                            face_uv_indices[1],
                            face_uv_indices[2]
                        ))
            
            bm.free()
            model.meshes.append(mesh_data)
        
        # Export morph frames (shape keys)
        if self.export_morphs and max_shape_keys > 0:
            for shape_key_idx in range(1, max_shape_keys + 1):
                morph_frame = NTWMMorphFrame()
                
                for obj_idx, obj in enumerate(objects):
                    frame_mesh = NTWMFrameMesh()
                    
                    if obj.data.shape_keys and shape_key_idx < len(obj.data.shape_keys.key_blocks):
                        shape_key = obj.data.shape_keys.key_blocks[shape_key_idx]
                        
                        for vert in obj.data.vertices:
                            co = shape_key.data[vert.index].co
                            pos = Vector3F(co.x, co.y, co.z)
                            frame_mesh.positions += pos.to_bytes()
                            
                            norm = Vector3F(vert.normal.x, vert.normal.y, vert.normal.z)
                            frame_mesh.normals += norm.to_bytes()
                    else:
                        # Use base mesh data
                        for vert in obj.data.vertices:
                            pos = Vector3F(vert.co.x, vert.co.y, vert.co.z)
                            frame_mesh.positions += pos.to_bytes()
                            norm = Vector3F(vert.normal.x, vert.normal.y, vert.normal.z)
                            frame_mesh.normals += norm.to_bytes()
                    
                    morph_frame.frame_meshes.append(frame_mesh)
                
                model.morph_frames.append(morph_frame)
        
        # Write to file
        model.write(filepath)
    
    def export_fxm(self, filepath, context):
        """Export to FXM format"""
        model = FXMModel()
        
        # Get selected objects
        objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
        if not objects:
            objects = [obj for obj in bpy.data.objects if obj.type == 'MESH']
        
        if not objects:
            self.report({'ERROR'}, "No mesh objects to export")
            return {'CANCELLED'}
        
        # Check for armature
        arm_obj = None
        for obj in context.selected_objects:
            if obj.type == 'ARMATURE':
                arm_obj = obj
                break
        
        if not arm_obj:
            # Try to find parent armature
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
        
        # Process meshes
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
            
            # Export texture name
            if self.export_textures and obj.data.materials:
                mat = obj.data.materials[0]
                texture_handler = TextureHandler()
                mesh_data.texture_name = texture_handler.export_texture_reference(mat.name)
            
            # Export vertices
            for vert in bm.verts:
                vertex = type('Vertex', (), {})()
                vertex.coordinates = Vector3F(vert.co.x, vert.co.y, vert.co.z)
                vertex.normal = Vector3F(vert.normal.x, vert.normal.y, vert.normal.z)
                
                # Get UV
                vertex.uv = Vector2F()
                if obj.data.uv_layers.active:
                    uv_layer = obj.data.uv_layers.active.data
                    # Get UV from first loop of first polygon using this vertex
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
            
            # Export faces
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
        
        # Write to file
        model.write(filepath)