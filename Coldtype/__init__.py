bl_info = {
    "name": "Coldtype",
    "author": "Rob Stenson",
    "version": (0, 4),
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
    from Coldtype import importer, operations, properties, typesetter, search, exporting, font, util, interpolation

modules = [importer, properties, operations, typesetter, search, exporting, font, util, interpolation]


if importer.C is not None:
    from fontTools.ttLib.ttFont import TTFont, registerCustomTableClass
    registerCustomTableClass("MESH", "Coldtype.meshtable", "table__M_E_S_H")


def individual_font(layout, data):
    row = layout.row()
    op = row.operator("wm.ctxyz_choose_font", text="", icon="FONTPREVIEW")
    font_path = data.font_path

    if not font_path:
        for x in ["< Choose a font to get started"]:
            row.label(text=x)
        return

    font = importer.ct.Font.Cacheable(font_path)
    mesh = None
    try:
        mesh = font.font.ttFont["MESH"]
    except KeyError:
        pass
    
    if font:
        row.label(text=f"“{font.path.stem}”")
    else:
        row.label(text="No font selected")

    if font:
        if not data.updatable:
            row.operator("ctxyz.clear_font", text="", icon="X")
        else:
            row.operator("ctxyz.refresh_settings", text="", icon="FILE_REFRESH")
            row.operator("ctxyz.load_prev_font", text="", icon="TRIA_LEFT")
            row.operator("ctxyz.load_next_font", text="", icon="TRIA_RIGHT")
            row.operator("ctxyz.show_font", text="", icon="FILEBROWSER")
        
    return mesh


def font_basics(layout, data, font, obj):
    mesh = individual_font(layout, data)

    if mesh:
        row = layout.row()
        row.label(text=">>> MESH font")
    
    if True:
        row = layout.row()
        row.label(text="Position")

        row.prop(data, "align_x", text="X", expand=True)
        row.prop(data, "align_y", text="Y", expand=True)

    row.prop(data, "use_horizontal_font_metrics", text="", icon="EVENT_X")
    row.prop(data, "use_vertical_font_metrics", text="", icon="EVENT_Y")

    if not mesh:
        row = layout.row()
        row.prop(data, "combine_glyphs", text="", icon="META_DATA")
        row.prop(data, "remove_overlap", text="", icon="OVERLAY")

        row.prop(data, "outline", text="", icon="OUTLINER_DATA_VOLUME")
        row.prop(data, "outline_weight", text="Weight")
        row.prop(data, "outline_outer", text="", icon="SELECT_DIFFERENCE")
        row.prop(data, "outline_miter_limit")

    row = layout.row()
    row.prop(data, "tracking")
    row.prop(data, "leading")
    
    row = layout.row()
    row.label(text="Case")
    row.prop(data, "case", text="LX", expand=True)
    row.label(text="Line Align")
    row.prop(data, "align_lines_x", text="LX", expand=True)

    return mesh


def layout_editor(layout, data, obj, context):
    row = layout.row()
    col = row.column()
    col.enabled = data.text_mode == "UI"
    col.prop(data, "text", text="")

    row = layout.row()
    row.prop(data, "text_mode", text="", expand=True)
    
    #row = layout.grid_flow(columns=4)
    #col = row.column()
    #col.enabled = False
    #col.prop(data, "text_file_enable", icon="FILE_TEXT", text="")
    #row.prop(data, "text_block_enable", icon="TEXT", text="")

    row.prop(data, "text_indexed", icon="PRESET_NEW", text="Keyframing")
    row.prop(data, "auto_rename", icon="INDIRECT_ONLY_ON", text="Rename")
    
    if data.text_mode == "FILE":
        row = layout.row()
        row.prop(data, "text_file", text="File")
        row.operator("ctxyz.refresh_settings", text="", icon="FILE_REFRESH")
    elif data.text_mode == "BLOCK":
        row = layout.row()
        row.prop(data, "text_block", text="Block")
        row.operator("ctxyz.refresh_settings", text="", icon="FILE_REFRESH")
    
    if data.text_indexed:
        layout.row().prop(data, "text_index")


class ColdtypeDefaultPanel(bpy.types.Panel):
    bl_label = "Defaults"
    bl_idname = "COLDTYPE_PT_1_DEFAULTPANEL"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Coldtype"

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
        data = context.scene.ctxyz

        individual_font(layout, data)

        if data.font_path:
            row = layout.row()
            row.label(text="Defaults")

            row.prop(data, "align_x", text="X", expand=True)
            row.prop(data, "align_y", text="Y", expand=True)

            row.prop(data, "default_upright", icon="ORIENTATION_VIEW", icon_only=True)
            row.prop(data, "default_extrude")

            layout.row().operator("ctxyz.settype_with_scene_defaults", text="Add New Text", icon="SORTALPHA")


class ColdtypeMainPanel(bpy.types.Panel):
    bl_label = "Text"
    bl_idname = "COLDTYPE_PT_20_MAINPANEL"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Coldtype"

    @classmethod
    def poll(cls, context):
        ko = search.active_key_object(context)
        return ko and not ko.ctxyz.baked
    
    def draw(self, context):
        ko = search.active_key_object(context)
        layout_editor(self.layout, ko.ctxyz, ko, context)


class ColdtypeFontPanel(bpy.types.Panel):
    bl_label = "Font"
    bl_idname = "COLDTYPE_PT_22_FONTPANEL"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Coldtype"

    @classmethod
    def poll(cls, context):
        ko = search.active_key_object(context)
        return ko and not ko.ctxyz.baked
    
    def draw(self, context):
        ko = search.active_key_object(context)
        
        data = ko.ctxyz
        font = importer.ct.Font.Cacheable(data.font_path)
        #print(">>>", font)
        mesh = font_basics(self.layout, data, font, ko)


class ColdtypeGlobalPanel(bpy.types.Panel):
    bl_label = "Render Settings"
    bl_idname = "COLDTYPE_PT_999_GLOBALPANEL"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Coldtype"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return importer.C is not None
    
    def draw(self, context):
        row = self.layout.row()
        row.prop(context.scene.ctxyz, "live_updating", text="")


classes = [
    #ColdtypePropertiesGroup,
]

panels = [
    ColdtypeDefaultPanel,
    ColdtypeMainPanel,
    ColdtypeFontPanel,
    ColdtypeGlobalPanel,
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
    print("---COLDTYPE---", bl_info["version"])

    for c in all_classes:
        bpy.utils.register_class(c)
    
    for p in all_panels:
        bpy.utils.register_class(p)

    bpy.types.Scene.ctxyz = bpy.props.PointerProperty(type=properties.ColdtypePropertiesGroup, name="Coldtype", description="Default Coldtype properties")
    bpy.types.Object.ctxyz = bpy.props.PointerProperty(type=properties.ColdtypePropertiesGroup, name="Coldtype", description="Coldtype properties")

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
