# io_anim_ntwm/handlers/animation_handler.py
import bpy
import mathutils
import struct

class AnimationHandler:
    def __init__(self):
        self.actions = {}
    
    def create_shape_keys_from_morphs(self, obj, morph_frames, mesh_index):
        """Create shape keys from morph frames (ANB format)"""
        if not morph_frames:
            return
        
        mesh = obj.data
        
        if not mesh.shape_keys:
            basis = obj.shape_key_add(name="Basis")
        
        for frame_idx, morph_frame in enumerate(morph_frames):
            if mesh_index < len(morph_frame.frame_meshes):
                frame_mesh = morph_frame.frame_meshes[mesh_index]
                shape_key = obj.shape_key_add(name=f"Morph_{frame_idx}")
                
                for vert_idx, vert in enumerate(mesh.vertices):
                    shape_key.data[vert_idx].co = frame_mesh.positions[vert_idx].to_tuple()
    
    def create_morph_animation(self, obj, morph_count, fps=0.01):
        """
        Create animation timeline for morph shape keys.
        Each morph gets keyframed on consecutive frames.
        """
        if not obj.data.shape_keys or not obj.data.shape_keys.key_blocks:
            return None
        
        shape_keys = obj.data.shape_keys.key_blocks
        
        action = bpy.data.actions.new(name=f"{obj.name}_MorphAnim")
        
        if not obj.animation_data:
            obj.animation_data_create()
        
        obj.animation_data.action = action
        
        for i, key in enumerate(shape_keys):
            key.value = 0.0
            key.keyframe_insert(data_path="value", frame=1)
        

        for i in range(1, len(shape_keys)):
            morph_key = shape_keys[i]
            
            # Previous frame: morph OFF
            prev_frame = (i - 1) * fps
            morph_key.value = 0.0
            morph_key.keyframe_insert(data_path="value", frame=prev_frame)
            
            # Current frame: morph ON
            curr_frame = i * fps
            morph_key.value = 1.0
            morph_key.keyframe_insert(data_path="value", frame=curr_frame)
            
            # Next frame (if exists): morph OFF again
            next_frame = (i + 1) * fps
            morph_key.value = 0.0
            morph_key.keyframe_insert(data_path="value", frame=next_frame)
        
        # Set timeline range
        scene = bpy.context.scene
        scene.frame_start = 1
        scene.frame_end = len(shape_keys) * fps
        
        return action
    
    def create_morph_animation_loop(self, obj, morph_count, fps=60/30):
        if not obj.data.shape_keys or not obj.data.shape_keys.key_blocks:
            return None
        
        shape_keys = obj.data.shape_keys.key_blocks
        
        # Create new action
        action = bpy.data.actions.new(name=f"{obj.name}_MorphLoop")
        
        if not obj.animation_data:
            obj.animation_data_create()
        
        obj.animation_data.action = action
        
        # Keyframe each morph on consecutive frames
        for i, key in enumerate(shape_keys):
            # Reset all keys
            for j, k in enumerate(shape_keys):
                k.value = 0.0
                k.keyframe_insert(data_path="value", frame=1)
        
        # Set each morph active on its frame
        for i in range(1, len(shape_keys)):
            morph_key = shape_keys[i]
            
            # Previous frame: morph OFF
            prev_frame = (i - 1) * fps
            morph_key.value = 0.0
            morph_key.keyframe_insert(data_path="value", frame=prev_frame)
            
            # Current frame: morph ON
            curr_frame = i * fps
            morph_key.value = 1.0
            morph_key.keyframe_insert(data_path="value", frame=curr_frame)
            
            # Next frame (if exists): morph OFF again
            next_frame = (i + 1) * fps
            morph_key.value = 0.0
            morph_key.keyframe_insert(data_path="value", frame=next_frame)
        
        # Set timeline to loop
        scene = bpy.context.scene
        scene.frame_start = 1
        scene.frame_end = len(shape_keys)
        
        # Enable cycling
        if action.fcurves:
            for fcurve in action.fcurves:
                for modifier in fcurve.modifiers:
                    if modifier.type == 'CYCLES':
                        break
                else:
                    modifier = fcurve.modifiers.new('CYCLES')
                    modifier.mode_before = 'REPEAT'
                    modifier.mode_after = 'REPEAT'
        
        return action
    
    def create_armature_from_bones(self, bones, name="Armature"):
        """Create armature from bone data (FXM format)"""
        arm_data = bpy.data.armatures.new(name)
        arm_obj = bpy.data.objects.new(name, arm_data)
        
        bpy.context.collection.objects.link(arm_obj)
        bpy.context.view_layer.objects.active = arm_obj
        bpy.ops.object.mode_set(mode='EDIT')
        
        bone_map = {}
        
        for idx, bone_data in enumerate(bones):
            bone = arm_data.edit_bones.new(bone_data.name)
            bone.head = (0, 0, 0)
            bone.tail = (0, 1, 0)
            
            if bone_data.parent_index >= 0 and bone_data.parent_index < len(bones):
                parent_name = bones[bone_data.parent_index].name
                if parent_name in arm_data.edit_bones:
                    bone.parent = arm_data.edit_bones[parent_name]
            
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
        
        action = bpy.data.actions.new(name)
        
        if not arm_obj.animation_data:
            arm_obj.animation_data_create()
        
        arm_obj.animation_data.action = action
        
        for bone_motion in motion_data.bone_motions:
            if bone_motion.bone_name not in bone_map:
                continue
            
            bone_info = bone_map[bone_motion.bone_name]
            bone = bone_info['bone']
            
            # Process rotation keys
            for key in bone_motion.rotation_keys:
                frame = int(key.time * 30)  # Assume 30 FPS
                quat = mathutils.Quaternion((key.motion.w, key.motion.x, key.motion.y, key.motion.z))
                
                bone_key = f'pose.bones["{bone.name}"].rotation_quaternion'
                arm_obj.keyframe_insert(bone_key, frame=frame)
            
            # Process position keys
            for key in bone_motion.position_keys:
                frame = int(key.time * 30)
                loc = (key.motion.x, key.motion.y, key.motion.z)
                
                bone_key = f'pose.bones["{bone.name}"].location'
                arm_obj.keyframe_insert(bone_key, frame=frame)
        
        # Set timeline range
        scene = bpy.context.scene
        if action.frame_range[1] > scene.frame_end:
            scene.frame_end = int(action.frame_range[1])
        
        return action
    
    def export_bones_to_fxm(self, arm_obj):
        """Export armature bones to FXM format"""
        bones = []
        if not arm_obj or arm_obj.type != 'ARMATURE':
            return bones
        
        for idx, bone in enumerate(arm_obj.data.bones):
            bone_data = type('Bone', (), {})()
            bone_data.name = bone.name
            bone_data.parent_index = -1
            
            if bone.parent:
                for p_idx, p_bone in enumerate(arm_obj.data.bones):
                    if p_bone.name == bone.parent.name:
                        bone_data.parent_index = p_idx
                        break
            
            if arm_obj.pose and bone.name in arm_obj.pose.bones:
                pose_bone = arm_obj.pose.bones[bone.name]
                bone_data.matrix = tuple(pose_bone.matrix)
            else:
                bone_data.matrix = (1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1)
            
            bones.append(bone_data)
        
        return bones