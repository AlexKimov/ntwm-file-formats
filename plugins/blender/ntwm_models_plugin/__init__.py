# io_anim_ntwm/__init__.py
bl_info = {
    "name": "Nosferatu ANB/FXM Model Format",
    "version": (1, 0, 0),
    "blender": (3, 0, 0),
    "location": "File > Import-Export",
    "description": "Import/Export Nosferatu: The Wrath of Malachi .anb/.fxm model files",
    "category": "Import-Export",
}

import bpy
from . import operators

classes = (
    operators.ImportNTWMOperator,
    operators.ExportNTWMOperator,
)

def menu_func_import(self, context):
    self.layout.operator(operators.ImportNTWMOperator.bl_idname, text="Nosferatu ANB/FXM (.anb, .fxm)")

def menu_func_export(self, context):
    self.layout.operator(operators.ExportNTWMOperator.bl_idname, text="Nosferatu ANB/FXM (.anb, .fxm)")

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)

if __name__ == "__main__":
    register()