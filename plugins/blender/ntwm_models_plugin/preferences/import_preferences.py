import bpy


class ImportPreferences(bpy.types.AddonPreferences):
    bl_idname = 'ntwm_models_plugin'

    ntwm_game_dat_dir: bpy.props.StringProperty(
        name="",
        subtype="DIR_PATH",
    )
    
    def draw(self, context):
        layout = self.layout

        split = layout.split(factor=0.3, align=True)
        split.label(text="Game data directory")
        split.prop(self, "ntwm_game_dat_dir")
