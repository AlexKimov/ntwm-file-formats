import bpy
from .. import consts as const
from mathutils import Matrix, Quaternion, Vector
import struct

class AnimationHandler:
    def __init__(self):
        self.actions = {}
    
    def create_vertex_morph_animation(self, obj, morph_frames, mesh_index, fps_scale=1, fps=24):
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        
        if obj.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        mesh = obj.data
        if not mesh or not mesh.vertices:
            return None

        num_verts = len(mesh.vertices)
        num_frames = len(morph_frames) - 1

        action = bpy.data.actions.new(name=f"{obj.name}_vertex_morph")
        if not mesh.animation_data:
            mesh.animation_data_create()
        mesh.animation_data.action = action

        fcurves = {}
        for v_idx in range(num_verts):
            for i, coord in enumerate('xyz'):
                data_path = f'vertices[{v_idx}].co'
                fcurve = action.fcurves.new(data_path=data_path, index=i)
                fcurves[(v_idx, coord)] = fcurve

        kf_data = {(v_idx, coord): {'frames': [], 'values': []} 
                  for v_idx in range(num_verts) for coord in 'xyz'}

        for frame_idx, morph_frame in enumerate(morph_frames):
            frame = int(frame_idx * fps_scale)

            frame_mesh = morph_frame.frame_meshes[mesh_index]

            for v_idx, pos in enumerate(frame_mesh.positions):
                pos_tuple = pos.to_tuple() if hasattr(pos, 'to_tuple') else tuple(pos)
                for i, coord in enumerate('xyz'):
                    kf_data[(v_idx, coord)]['frames'].append(frame)
                    kf_data[(v_idx, coord)]['values'].append(pos_tuple[i])

        for (v_idx, coord), data in kf_data.items():
            fcurve = fcurves[(v_idx, coord)]
            num_kfs = len(data['frames'])

            if num_kfs == 0:
                continue

            fcurve.keyframe_points.add(num_kfs)
            flat_coords = [val for pair in zip(data['frames'], data['values']) for val in pair]
            
            fcurve.keyframe_points.foreach_set("co", flat_coords)
            fcurve.keyframe_points.foreach_set("interpolation", [1] * num_kfs)

        scene = bpy.context.scene
        scene.frame_start = 0
        scene.frame_end = int(num_frames * fps_scale)
        scene.render.fps = fps

        bpy.context.view_layer.update()

    def create_armature_from_bones(self, bones, name="Armature", transform_axes = False):
        arm_data = bpy.data.armatures.new(name)
        arm_obj = bpy.data.objects.new(name, arm_data)
        
        arm_obj.data.display_type = 'STICK'
        arm_obj.show_in_front = True
    
        bpy.context.collection.objects.link(arm_obj)
        bpy.context.view_layer.objects.active = arm_obj
        bpy.ops.object.mode_set(mode='EDIT')

        
        for idx, bone_data in enumerate(bones):
            bone = arm_data.edit_bones.new(bone_data.name)          
            matrix_data = bone_data.matrix
        
            mat = Matrix((
                (matrix_data[0],  matrix_data[4],  matrix_data[8],  matrix_data[12]),
                (matrix_data[1],  matrix_data[5],  matrix_data[9],  matrix_data[13]),
                (matrix_data[2],  matrix_data[6],  matrix_data[10], matrix_data[14]),
                (matrix_data[3], matrix_data[7], matrix_data[11], matrix_data[15])
            ))
            mat.invert()                        
            if transform_axes:
                mat = const.BLENDER_DX_MATRIX @ mat 
                
            bone.head = (0, 0, 0)
            bone.tail = (0, 0.01, 0)
            bone.matrix = mat 
            
            
            
            if bone_data.parent_index >= 0:
                parent_name = bones[bone_data.parent_index].name
                if parent_name in arm_data.edit_bones:
                    bone.parent = arm_data.edit_bones[parent_name]
                    # bone.head = bone.parent.tail              
                    bone.use_connect = True 
                  
            
            
        bpy.ops.object.mode_set(mode='OBJECT')
        return arm_obj
    
    def create_animation_from_motion(self, arm_obj, motion_data, name="Animation"):
        frame_time = 1 / 30
        """
        Create an animation action on the given armature object from motion data.
        
        Parameters:
            arm_obj     – Blender armature object
            motion_data – MOTAnimation instance containing bone motions
            name        – name for the new action
        
        Returns:
            The created action, or None if no motion data.
        """
        if not motion_data or not motion_data.bone_motions:
            return None

        # Ensure armature has animation data and assign a new action
        if not arm_obj.animation_data:
            arm_obj.animation_data_create()
        action = bpy.data.actions.new(name)
        arm_obj.animation_data.action = action

        # Get frames per second from scene settings
        fps = bpy.context.scene.render.fps

        for bone_motion in motion_data.bone_motions:
            bone_name = bone_motion.bone_name

            # Make sure the bone exists in the armature
            if bone_name not in arm_obj.pose.bones:
                print(f"Warning: Bone '{bone_name}' not found in armature, skipping.")
                continue

            pose_bone = arm_obj.pose.bones[bone_name]

            # Ensure rotation mode is quaternion (required for rotation_quaternion fcurves)
            if pose_bone.rotation_mode != 'QUATERNION':
                pose_bone.rotation_mode = 'QUATERNION'

            # ------------------ Rotation keys ------------------
            rot_keys = bone_motion.rotation_keys
            if rot_keys:
                frames = [(int(k.time/frame_time) + 1) for k in rot_keys]
                quats = []
                for k in rot_keys:
                    quat = Quaternion((k.motion.w, k.motion.x, k.motion.y, k.motion.z))
                    mat = quat.to_matrix().transposed()                    
                    quats.append(mat.to_quaternion())

                # Extract components for fcurves
                comps = [
                    [q.w for q in quats],
                    [q.x for q in quats],
                    [q.y for q in quats],
                    [q.z for q in quats],
                ]

                data_path = f'pose.bones["{bone_name}"].rotation_quaternion'
                fcurves = [action.fcurves.new(data_path, index=i) for i in range(4)]

                for i, fc in enumerate(fcurves):
                    fc.keyframe_points.add(len(rot_keys))
                    coords = [val for pair in zip(frames, comps[i]) for val in pair]
                    fc.keyframe_points.foreach_set("co", coords)
                    fc.update()

            # ------------------ Position keys ------------------
            pos_keys = bone_motion.position_keys
            if pos_keys:
                frames = [int(k.time * fps) for k in pos_keys]
                # Position components: x, y, z
                comps = [
                    [k.motion.x for k in pos_keys],
                    [k.motion.y for k in pos_keys],
                    [k.motion.z for k in pos_keys]
                ]

                data_path = f'pose.bones["{bone_name}"].location'
                fcurves = [action.fcurves.new(data_path, index=i) for i in range(3)]

                for i, fc in enumerate(fcurves):
                    fc.keyframe_points.add(len(pos_keys))
                    coords = [val for pair in zip(frames, comps[i]) for val in pair]
                    fc.keyframe_points.foreach_set("co", coords)
                    fc.update()

            # ------------------ Scale keys ------------------
            scale_keys = bone_motion.scale_keys
            if scale_keys:
                frames = [int(k.time * fps) for k in scale_keys]
                comps = [
                    [k.motion.x for k in scale_keys],
                    [k.motion.y for k in scale_keys],
                    [k.motion.z for k in scale_keys]
                ]

                data_path = f'pose.bones["{bone_name}"].scale'
                fcurves = [action.fcurves.new(data_path, index=i) for i in range(3)]

                for i, fc in enumerate(fcurves):
                    fc.keyframe_points.add(len(scale_keys))
                    coords = [val for pair in zip(frames, comps[i]) for val in pair]
                    fc.keyframe_points.foreach_set("co", coords)
                    fc.update()

        
        # Extend scene's frame range to cover the animation
        # if action.frame_range[1] > bpy.context.scene.frame_end:
            # bpy.context.scene.frame_end = action.frame_range[1] - 2

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