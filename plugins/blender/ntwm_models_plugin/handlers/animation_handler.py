# io_anim_ntwm/handlers/animation_handler.py
import bpy
import mathutils

class AnimationHandler:
    def __init__(self):
        self.actions = {}
    
    def create_shape_keys_from_morphs(self, obj, morph_frames, mesh_index):
        """Create shape keys from morph frames (ANB format)"""
        if not morph_frames:
            return
        
        mesh = obj.data
        
        # Create basis shape key
        if not mesh.shape_keys:
            basis = obj.shape_key_add(name="Basis")
        
        # Create shape keys for each morph frame
        for frame_idx, morph_frame in enumerate(morph_frames):
            if mesh_index < len(morph_frame.frame_meshes):
                frame_mesh = morph_frame.frame_meshes[mesh_index]
                
                shape_key = obj.shape_key_add(name=f"Morph_{frame_idx}")
                
                # Read positions from bytearray
                pos_data = frame_mesh.positions
                for vert_idx, vert in enumerate(mesh.vertices):
                    offset = vert_idx * 12  # 3 floats * 4 bytes
                    if offset + 12 <= len(pos_data):
                        import struct
                        x = struct.unpack('<f', pos_data[offset:offset+4])[0]
                        y = struct.unpack('<f', pos_data[offset+4:offset+8])[0]
                        z = struct.unpack('<f', pos_data[offset+8:offset+12])[0]
                        shape_key.data[vert_idx].co = (x, y, z)
    
    def create_armature_from_bones(self, bones, name="Armature"):
        """Create armature from bone data (FXM format)"""
        # Create armature
        arm_data = bpy.data.armatures.new(name)
        arm_obj = bpy.data.objects.new(name, arm_data)
        
        bpy.context.collection.objects.link(arm_obj)
        
        # Enter edit mode
        bpy.context.view_layer.objects.active = arm_obj
        bpy.ops.object.mode_set(mode='EDIT')
        
        bone_map = {}
        
        # Create bones
        for idx, bone_data in enumerate(bones):
            bone = arm_data.edit_bones.new(bone_data.name)
            bone.head = (0, 0, 0)
            bone.tail = (0, 1, 0)
            
            # Set parent
            if bone_data.parent_index >= 0 and bone_data.parent_index < len(bones):
                parent_name = bones[bone_data.parent_index].name
                if parent_name in arm_data.edit_bones:
                    bone.parent = arm_data.edit_bones[parent_name]
            
            # Store matrix
            bone_map[bone_data.name] = {
                'bone': bone,
                'matrix': bone_data.matrix,
                'index': idx
            }
        
        bpy.ops.object.mode_set(mode='OBJECT')
        
        return arm_obj, bone_map
    
    def create_animation_from_motion(self, arm_obj, bone_map, motion_data, name="Animation"):
        """Create animation from motion data (FXM .mot format)"""
        if not motion_data or not motion_data.bone_motions:
            return None
        
        # Create action
        action = bpy.data.actions.new(name)
        arm_obj.animation_data_create()
        arm_obj.animation_data.action = action
        
        # Process each bone motion
        for bone_motion in motion_data.bone_motions:
            if bone_motion.bone_name not in bone_map:
                continue
            
            bone_info = bone_map[bone_motion.bone_name]
            bone = bone_info['bone']
            
            # Process rotation keys
            for key in bone_motion.rotation_keys:
                frame = int(key.time * 30)  # Assume 30 FPS
                quat = mathutils.Quaternion((key.motion.w, key.motion.x, key.motion.y, key.motion.z))
                
                bone_key = f"pose.bones[\"{bone.name}\"].rotation_quaternion"
                arm_obj.keyframe_insert(bone_key, frame=frame)
            
            # Process position keys
            for key in bone_motion.position_keys:
                frame = int(key.time * 30)
                loc = (key.motion.x, key.motion.y, key.motion.z)
                
                bone_key = f"pose.bones[\"{bone.name}\"].location"
                arm_obj.keyframe_insert(bone_key, frame=frame)
        
        return action
    
    def export_shape_keys_to_morphs(self, obj):
        """Export shape keys to morph frames"""
        morph_frames = []
        
        if not obj.data.shape_keys or not obj.data.shape_keys.key_blocks:
            return morph_frames
        
        # Skip basis key
        for idx, shape_key in enumerate(obj.data.shape_keys.key_blocks[1:], 1):
            frame_mesh = type('FrameMesh', (), {})()
            frame_mesh.positions = bytearray()
            frame_mesh.normals = bytearray()
            
            import struct
            for vert in obj.data.vertices:
                co = shape_key.data[vert.index].co
                frame_mesh.positions += struct.pack("<fff", co.x, co.y, co.z)
                frame_mesh.normals += struct.pack("<fff", vert.normal.x, vert.normal.y, vert.normal.z)
            
            morph_frames.append(frame_mesh)
        
        return morph_frames
    
    def export_bones_to_fxm(self, arm_obj):
        """Export armature bones to FXM format"""
        bones = []
        
        if not arm_obj or arm_obj.type != 'ARMATURE':
            return bones
        
        # Create bone data
        for idx, bone in enumerate(arm_obj.data.bones):
            bone_data = type('Bone', (), {})()
            bone_data.name = bone.name
            bone_data.parent_index = -1
            
            # Find parent index
            if bone.parent:
                for p_idx, p_bone in enumerate(arm_obj.data.bones):
                    if p_bone.name == bone.parent.name:
                        bone_data.parent_index = p_idx
                        break
            
            # Get matrix
            if arm_obj.pose and bone.name in arm_obj.pose.bones:
                pose_bone = arm_obj.pose.bones[bone.name]
                bone_data.matrix = tuple(pose_bone.matrix)
            else:
                bone_data.matrix = (1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1)
            
            bones.append(bone_data)
        
        return bones