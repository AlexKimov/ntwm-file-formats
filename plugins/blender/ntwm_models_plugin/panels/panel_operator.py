import bpy

from bpy.types import Panel, Operator, PropertyGroup
from bpy.props import StringProperty, FloatVectorProperty, FloatProperty, BoolProperty 

from ..handlers.texture_handler import TextureHandler
from ..handlers.material_handler import MaterialHandler


class CustomToolProperties(bpy.types.PropertyGroup):
    bl_idname = __name__

    texturesPath: bpy.props.StringProperty(
        name="Textures directory",
        subtype="DIR_PATH",
    )
    
    def draw(self, context):
        layout = self.layout
        layout.label(text="Path to unpacked textures (from Textures.res)")
        layout.prop(self, "texturesPath")


class IMPORT_OT_ntwm_textures(Operator):
    bl_idname = "import.ntwm_textures"
    bl_label = "Import"
    bl_options = {'REGISTER'}

    filepath: StringProperty(
        name="File Path",
        description="Filepath used for importing the file",
        maxlen=1024,
        subtype='FILE_PATH',
    )

    filter_glob: StringProperty(
        default="*.jpg;*.jpeg;*.png;*.tga;*.bmp",
        options={'HIDDEN'},
    )

    def execute(self, context):
        if self.filepath:
            self.report({'INFO'}, f"Selected texture file: {self.filepath}")
            
            context = bpy.context
            objects = [obj for obj in context.selected_objects if obj.type == 'MESH']

            props = context.scene.custom_tool_props 
            
            if not objects:
                print("No mesh objects selected.")   
            else:             
                texture_handler = TextureHandler()
                material_handler = MaterialHandler() 
              
                mat = material_handler.create_material(self.filepath)                
                if mat is not None:
                    texture_handler.create_texture_for_material(mat, self.filepath, props.transparency_color, props.threshold, props.add_transparency)                  
                    for obj in objects:
                        material_handler.apply_material_to_object(obj, mat)               

        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class VIEW3D_PT_TextureImportOperator(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "NTWM"        
    bl_label = "Textures"    

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        layout.prop(scene.custom_tool_props, "add_transparency", text="Add transparency")    
        layout.prop(scene.custom_tool_props, "threshold", text="Color threshold")    
        layout.prop(scene.custom_tool_props, "transparency_color", text="Transparency Color")    
        
        layout.separator(factor=2.0)
        
        layout.operator(IMPORT_OT_ntwm_textures.bl_idname,
                        text="Apply texture",
                        icon='FILE_FOLDER')