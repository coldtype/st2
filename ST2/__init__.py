bl_info = {
    "name": "ST2",
    "author": "Rob Stenson",
    "version": (0, 19),
    "blender": (3, 0, 0),
    "location": "View3D > Toolshelf",
    "description": "Well-shaped 3D typography",
    "warning": "",
    "wiki_url": "",
    "category": "Coldtype",
}

import importlib

if "bpy" in locals():
    for module in modules:
        importlib.reload(module)
else:
    import bpy
    from ST2 import importer, operations, properties, typesetter, search, exporting, font, util, interpolation

modules = [importer, properties, operations, typesetter, search, exporting, font, util, interpolation]


if importer.C is not None:
    from fontTools.ttLib.ttFont import TTFont, registerCustomTableClass
    registerCustomTableClass("MESH", "ST2.meshtable", "table__M_E_S_H")


class ST2DefaultPanel(bpy.types.Panel):
    bl_label = "Defaults"
    bl_idname = "ST2_PT_1_DEFAULTPANEL"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "ST2"

    @classmethod
    def poll(cls, context):
        if not importer.C:
            return False
        else:
            ko = search.active_key_object(context, disallow_baked=False)
            return not bool(ko)
    
    def draw(self, context):
        util.ensure_frame_changer(frame_changers, properties.update_type_frame_change)

        layout = self.layout
        data = context.scene.st2
        font = data.font(none_ok=True)
        
        if font is None:
            if util.on_mac():
                layout.row().label(text="Two ways to choose a font:")

            row = layout.row()
            row.operator("wm.st2_choose_font", text="", icon="FONTPREVIEW")
            row.label(text="Browse for a font file")

            if util.on_mac():
                row = layout.row()
                row.operator("st2.search_font", text="", icon="VIEWZOOM")
                row.label(text="Search for an installed font")
        
        else:
            row = layout.row()
            row.operator("wm.st2_choose_font", text="", icon="FONTPREVIEW")
            if util.on_mac():
                row.operator("st2.search_font", text="", icon="VIEWZOOM")
            
            row.label(text=f"{font.names()[0]}")

            if not data.enable_font_search:
                row.operator("st2.load_prev_font", text="", icon="TRIA_LEFT")
                row.operator("st2.load_next_font", text="", icon="TRIA_RIGHT")

            row.operator("st2.clear_font", text="", icon="X")

            row = layout.row()
            row.label(text="Defaults")

            row.prop(data, "align_x", text="X", expand=True)
            row.prop(data, "align_y", text="Y", expand=True)

            row.prop(data, "default_upright", icon="ORIENTATION_VIEW", icon_only=True)
            row.prop(data, "default_extrude")

            row.prop(data, "newline_character", icon="TRACKING_BACKWARDS", text="")

            layout.row().operator("st2.settype_with_scene_defaults", text="Add New Text Object", icon="SORTALPHA")


class ST2MainPanel(bpy.types.Panel):
    bl_label = "Text"
    bl_idname = "ST2_PT_20_MAINPANEL"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "ST2"

    @classmethod
    def poll(cls, context):
        ko = search.active_key_object(context)
        return ko and not ko.st2.baked
    
    def draw(self, context):
        ko = search.active_key_object(context)
        st2 = ko.st2
        
        row = self.layout.row()
        col = row.column()
        col.enabled = st2.text_mode == "UI"
        col.prop(st2, "text", text="")

        row = self.layout.row()
        row.prop(st2, "text_mode", text="", expand=True)

        row.prop(st2, "text_indexed", icon="PRESET_NEW", text="Keyframing")
        row.prop(st2, "auto_rename", icon="INDIRECT_ONLY_ON", text="Auto Rename")
        #row.operator("st2.insert_newline_symbol", icon="TRACKING_BACKWARDS", text="")
        row.prop(st2, "newline_character", icon="TRACKING_BACKWARDS", text="")
        row.prop(st2, "script_enabled", text="", icon="PLUGIN")
        
        if st2.text_mode == "FILE":
            row = self.layout.row()
            row.prop(st2, "text_file", text="File")
            #row.operator("st2.refresh_settings", text="", icon="FILE_REFRESH")
        elif st2.text_mode == "BLOCK":
            row = self.layout.row()
            row.prop(st2, "text_block", text="Block")
        
        row.operator("st2.refresh_settings", text="", icon="FILE_REFRESH")
        
        if st2.text_indexed:
            self.layout.row().prop(st2, "text_index")
        
        if st2.text_mode == "SEQUENCE":
            self.layout.row().prop(st2, "text_sequence_channel")
        
        if not ko.data:
            self.layout.row().operator("st2.delete_parented_text", text="Delete All")


class ST2ScriptPanel(bpy.types.Panel):
    bl_label = "Script"
    bl_idname = "ST2_PT_211_SCRIPTPANEL"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "ST2"

    @classmethod
    def poll(cls, context):
        ko = search.active_key_object(context)
        return ko and not ko.st2.baked and ko.st2.script_enabled
    
    def draw(self, context):
        ko = search.active_key_object(context)
        data = ko.st2
        
        row = self.layout.row()
        row.prop(data, "script_mode", text="", expand=True)
        if data.script_mode == "FILE":
            row.prop(data, "script_file", text="")
        elif data.script_mode == "BLOCK":
            row.prop(data, "script_block", text="")
        
        #row.prop(data, "script_enabled", text="", icon="PLUGIN")

        row = self.layout.row()
        row.prop(data, "script_kwargs", text="Kwargs")

        row.operator("st2.refresh_settings", text="", icon="FILE_REFRESH")

        if False:
            if context.scene.st2.script_watch:
                row.operator("st2.cancel_watch_source", text="", icon="CANCEL")
            else:
                row.operator("st2.watch_source", text="", icon="MONKEY")


class ST2FontPanel(bpy.types.Panel):
    bl_label = "Font"
    bl_idname = "ST2_PT_22_FONTPANEL"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "ST2"

    @classmethod
    def poll(cls, context):
        ko = search.active_key_object(context)
        return ko and not ko.st2.baked
    
    def draw(self, context):
        ko = search.active_key_object(context)
        data = ko.st2
        font = data.font()

        mesh = None
        try:
            mesh = font.font.ttFont["MESH"]
        except KeyError:
            pass
    
        row = self.layout.row()
        
        row.operator("wm.st2_choose_font", text="", icon="FONTPREVIEW")
        if util.on_mac():
            row.operator("st2.search_font", text="", icon="VIEWZOOM")
        
        row.label(text=f"{font.names()[0]}")
        
        row.operator("st2.refresh_settings", text="", icon="FILE_REFRESH")
        if not data.enable_font_search:
            row.operator("st2.load_prev_font", text="", icon="TRIA_LEFT")
            row.operator("st2.load_next_font", text="", icon="TRIA_RIGHT")
        #row.operator("st2.show_font", text="", icon="FILEBROWSER")
        
        row = self.layout.row()
        row.label(text="Position")

        row.prop(data, "align_x", text="X", expand=True)
        row.prop(data, "align_y", text="Y", expand=True)

        row.prop(data, "use_horizontal_font_metrics", text="", icon="EVENT_X")
        row.prop(data, "use_vertical_font_metrics", text="", icon="EVENT_Y")

        if mesh:
            if data.use_mesh:
                self.layout.row().operator("st2.convert_mesh_to_flat", text="Convert Mesh to Outlines")
            else:
                self.layout.row().operator("st2.convert_flat_to_mesh", text="Convert Outlines to Mesh")

        row = self.layout.row()
        row.enabled = not mesh or (mesh and not data.use_mesh)
        row.prop(data, "combine_glyphs", text="", icon="META_DATA")
        row.prop(data, "remove_overlap", text="", icon="OVERLAY")

        row.prop(data, "outline", text="", icon="OUTLINER_DATA_VOLUME")
        row.prop(data, "outline_weight", text="Weight")
        row.prop(data, "outline_outer", text="", icon="SELECT_DIFFERENCE")
        row.prop(data, "outline_miter_limit")

        row = self.layout.row()
        row.prop(data, "scale")
        row.prop(data, "tracking")
        row.prop(data, "leading")

        # row = self.layout.row()
        # row.label(text="Blocks")
        # row.prop(data, "block", text="", icon="MESH_CUBE")
        # row.prop(data, "block_inset_x", text="X")
        # row.prop(data, "block_inset_y", text="Y")
        # row.prop(data, "block_horizontal_metrics", text="", icon="EVENT_X")
        # row.prop(data, "block_vertical_metrics", text="", icon="EVENT_Y")
        
        row = self.layout.row()
        row.label(text="Case")
        row.prop(data, "case", text="LX", expand=True)
        row.label(text="Line Align")
        row.prop(data, "align_lines_x", text="LX", expand=True)


class ST2SelectionPanel(bpy.types.Panel):
    bl_label = "Selection"
    bl_idname = "ST2_PT_997_SELECTIONPANEL"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "ST2"
    #bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return importer.C is not None
    
    def draw(self, context):
        editables = search.find_st2_editables(context)
        bakes = search.find_st2_bakes(context)

        if editables:
            row = self.layout.row()
            row.operator("st2.select_editables", text="Select All Editables")

        if bakes:
            row = self.layout.row()
            row.operator("st2.select_bakes", text="Select All Baked Anchors")
        
        #if not bakes and not 
        
        # row.prop(context.scene.st2, "live_updating", text="Frame Updating")

        # self.layout.row().label(text="New Objects")
        # self.layout.row().prop(context.scene.st2, "interpolator_style", text="Interpolate")
        # self.layout.row().prop(context.scene.st2, "export_style", text="Export")


class ST2GlobalPanel(bpy.types.Panel):
    bl_label = "Render Settings"
    bl_idname = "ST2_PT_998_GLOBALPANEL"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "ST2"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return importer.C is not None
    
    def draw(self, context):
        row = self.layout.row()
        row.prop(context.scene.st2, "live_updating", text="Frame Updating")

        self.layout.row().label(text="New Objects")
        self.layout.row().prop(context.scene.st2, "interpolator_style", text="Interpolate")
        self.layout.row().prop(context.scene.st2, "export_style", text="Export")


class ST2AboutPanel(bpy.types.Panel):
    bl_label = "About"
    bl_idname = "ST2_PT_999_ABOUTPANEL"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "ST2"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        if importer.coldtype_status == -2:
            importer.do_import()
            #print("hello")
        return True
    
    def draw(self, context):
        row = self.layout.row()
        version = bl_info.get("version")
        row.label(text=f"ST2 v{version[0]}.{version[1]}")
        # TODO buttons for help?


classes = [
    #ST2PropertiesGroup,
]

panels = [
    ST2DefaultPanel,
    ST2MainPanel,
    ST2ScriptPanel,
    ST2FontPanel,
    ST2SelectionPanel,
    ST2GlobalPanel,
    ST2AboutPanel,
]

all_classes = [*classes]
all_panels = [*panels]

for module in modules:
    for c in module.classes:
        all_classes.append(c)
    for p in module.panels:
        all_panels.append(p)

all_panels = sorted(all_panels, key=lambda p: p.bl_idname)

frame_changers = bpy.app.handlers.frame_change_post


def register():
    print("---ST2---", bl_info["version"])

    for c in all_classes:
        bpy.utils.register_class(c)
    
    for p in all_panels:
        bpy.utils.register_class(p)

    bpy.types.Scene.st2 = bpy.props.PointerProperty(type=properties.ST2PropertiesGroup, name="ST2", description="Default ST2 properties")
    bpy.types.Object.st2 = bpy.props.PointerProperty(type=properties.ST2PropertiesGroup, name="ST2", description="ST2 properties")

    util.clear_frame_changers(properties.update_type_and_copy)
    util.ensure_frame_changer(frame_changers, properties.update_type_frame_change)


def unregister():
    for p in reversed(all_panels):
        bpy.utils.unregister_class(p)

    for c in reversed(all_classes):
        bpy.utils.unregister_class(c)

    util.clear_frame_changers(properties.update_type_frame_change)

if __name__ == "__main__":
    register()
