from mathutils import Matrix

BLENDER_DX_MATRIX = Matrix((
    ( 1.0,  0.0,  0.0,  0.0),  
    ( 0.0,  0.0,  1.0,  0.0),  
    ( 0.0,  1.0,  0.0,  0.0), 
    ( 0.0,  0.0,  0.0,  1.0)  
))

BLENDER_DX_NORMAL_MATRIX = BLENDER_DX_MATRIX.to_3x3()