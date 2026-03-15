import struct
import bpy 

def vector3f_list_to_bytes(vector_list):
    count = len(vector_list)
    if count == 0:
        return b''
    
    floats = [val for v in vector_list for val in v.to_tuple()]
    return struct.pack(f'<{count * 3}f', *floats)
    
def apply_smoothing_to_collection(collection):
    for obj in collection.objects:
        if obj.type != 'MESH':
            continue
            
        mesh = obj.data
        for poly in mesh.polygons:
            poly.use_smooth = True    
            
def focus_view_on_collection(collection, transform_axes: False):     
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for region in area.regions:
                if region.type == 'WINDOW':
                    with bpy.context.temp_override(area=area, region=region):                 
                        bpy.ops.view3d.view_all()
                        pass                        
                    break
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    space.clip_end = 40000
                
            if 'break' in locals():
                break    
            