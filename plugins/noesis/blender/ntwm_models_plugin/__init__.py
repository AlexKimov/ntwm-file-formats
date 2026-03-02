bl_info = {
    "name": "Nosferatu ANB/FXM Model Format",
    "version": (1, 0, 0),
    "blender": (3, 0, 0),
    "location": "File > Import-Export",
    "description": "Import/Export Nosferatu: The Wrath of Malachi .anb/.fxm model files",
    "category": "Import-Export",
}

import bpy
import sys

if "bpy" in locals():
    dotted = __name__ + "."
    for name in tuple(sys.modules):
        if name.startswith(dotted):
            del sys.modules[name]
    
    print(f"Reloaded submodules: {__name__}")

# Import fresh copies of all modules
from .operators.import_operator import ImportNTWMOperator
from .operators.export_operator import ExportNTWMOperator

classes = (
    ImportNTWMOperator,
    ExportNTWMOperator,
)

def menu_func_import(self, context):
    self.layout.operator(ImportNTWMOperator.bl_idname, text="Nosferatu ANB/FXM (.anb, .fxm)")

def menu_func_export(self, context):
    self.layout.operator(ExportNTWMOperator.bl_idname, text="Nosferatu ANB/FXM (.anb, .fxm)")

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)
    print(f"Registered: {__name__}")

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    print(f"Unregistered: {__name__}")

if __name__ == "__main__":
    register()