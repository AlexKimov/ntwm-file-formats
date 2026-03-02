bl_info = {
    "name": "FXA Importer (Nosperatu)",
    "author": "Custom",
    "version": (1, 0, 1),
    "blender": (3, 0, 0),
    "location": "File > Import > FXA File (.fxa)",
    "description": "Import FXA hierarchy files from Nosperatu: Wrath of Malachii",
    "category": "Import-Export",
}

import bpy
import importlib
from bpy.props import StringProperty
from bpy.types import Operator, AddonPreferences

# Module references (for reloading)
_modules = []

def reload_modules():
    """Reload all addon modules - useful for development"""
    global _modules
    
    # Reload each submodule
    for mod_name in ['fxa_utils', 'fxa_parser', 'fxa_nodes']:
        if mod_name in locals() or mod_name in globals():
            try:
                locals()[mod_name] = importlib.reload(locals()[mod_name])
            except KeyError:
                pass
    
    # Also reload via sys.modules
    import sys
    pkg_name = __package__
    
    for name, mod in list(sys.modules.items()):
        if mod and name.startswith(pkg_name + '.') and not name.endswith('__'):
            try:
                sys.modules[name] = importlib.reload(mod)
                print(f"[FXA] Reloaded: {name}")
            except Exception as e:
                print(f"[FXA] Error reloading {name}: {e}")

class ImportFXA_OT(Operator):
    bl_idname = "import_mesh.fxa_nosperatu"
    bl_label = "Import FXA File (Nosperatu)"
    bl_description = "Import FXA hierarchy files from Nosperatu: Wrath of Malachii"
    bl_options = {'REGISTER', 'UNDO'}
    
    filepath: StringProperty(subtype='FILE_PATH')
    filter_glob: StringProperty(default="*.fxa", options={'HIDDEN'})
    
    def execute(self, context):
        try:
            # Always get fresh module references
            # from . import fxa_parser
            # from . import fxa_nodes
            
            # parser = fxa_parser.FXAParser()
            # nodes_data = parser.parse_file(self.filepath)
            
            # creator = fxa_nodes.FXANodeCreator(context)
            # created_count = creator.create_objects_from_nodes(nodes_data)
            
            # self.report({'INFO'}, f"Successfully imported {created_count} FXA nodes")
            return {'FINISHED'}
        except Exception as e:
            # self.report({'ERROR'}, f"Error importing FXA: {str(e)}")
            # import traceback
            # traceback.print_exc()
            return {'CANCELLED'}


# ======================== RELOAD OPERATORS ========================

class ReloadFXAModules_OT(Operator):
    """Reload FXA addon modules (Development Only)"""
    bl_idname = "addon_reload.fxa_nosperatu"
    bl_label = "Reload FXA Modules"
    bl_description = "Reload all FXA addon modules without restart"
    
    def execute(self, context):
        reload_modules()
        self.report({'INFO'}, "FXA modules reloaded successfully")
        return {'FINISHED'}


class MENU_ReloadFXA_PT(bpy.types.Panel):
    """Panel for FXA development tools"""
    bl_idname = "FXA_MT_reload_panel"
    bl_label = "FXA Developer Tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'FXA'
    
    def draw(self, context):
        layout = self.layout
        col = layout.column()
        
        col.label(text="Development Tools:")
        col.operator(
            ReloadFXAModules_OT.bl_idname, 
            text="Reload All Modules", 
            icon='FILE_REFRESH'
        )
        col.separator()
        
        # Debug info
        from . import fxa_parser
        from . import fxa_nodes
        
        col.label(text=f"Parser loaded: {fxa_parser.__file__}")
        col.label(text=f"NodeCreator loaded: {fxa_nodes.__file__}")


# ======================== REGISTRATION ========================

classes = [
    ImportFXA_OT,
    ReloadFXAModules_OT,
    MENU_ReloadFXA_PT,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    
    # Store initial module references
    global _modules
    from . import fxa_utils
    from . import fxa_parser
    from . import fxa_nodes
    _modules = [fxa_utils, fxa_parser, fxa_nodes]
    
    print("[FXA] Addon registered successfully")

def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    print("[FXA] Addon unregistered")


def menu_func_import(self, context):
    self.layout.operator(ImportFXA_OT.bl_idname, text="FXA File (.fxa)")


# ==================== DEVELOPMENT HELPER =======================

if __name__ == "__main__":
    register()