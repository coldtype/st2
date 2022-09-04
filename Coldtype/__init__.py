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
    from Coldtype import importer, operations, properties, typesetter, search, exporting, font

modules = [importer, properties, operations, typesetter, search, exporting, font]


if importer.C is not None:
    from fontTools.ttLib.ttFont import TTFont, registerCustomTableClass
    registerCustomTableClass("MESH", "Coldtype.meshtable", "table__M_E_S_H")


def individual_font(layout, data):
    row = layout.row()
    op = row.operator("wm.ctxyz_choose_font", text="", icon="FONTPREVIEW")
    font_path = data.font_path

    if not font_path:
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
    if data.updatable and obj:
        editables = search.find_ctxyz_editables(context)

        if len(editables) == 2:
            row = layout.row()
            row.operator("ctxyz.interpolate_strings", text="Interpolate")
            row.prop(context.scene.ctxyz, "interpolator_count", text="")
            row.prop(context.scene.ctxyz, "interpolator_easing", text="")
            layout.row().separator()
    
    layout.row().prop(data, "text")
    #layout.row().prop(data, "text_file")

    font = None
    if data.font_path:
        try:
            font = importer.ct.Font.Cacheable(data.font_path)
        except importer.ct.FontNotFoundException:
            font = None

    mesh = font_basics(layout, data, font, obj)


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
        if len(bpy.app.handlers.frame_change_post) == 0:
            frame_changers.append(properties.update_type_frame_change)

        layout = self.layout
        data = context.scene.ctxyz

        individual_font(layout, data)

        row = layout.row()
        row.label(text="Defaults")

        row.prop(data, "align_x", text="X", expand=True)
        row.prop(data, "align_y", text="Y", expand=True)

        row.prop(data, "default_upright", icon="ORIENTATION_VIEW", icon_only=True)
        row.prop(data, "default_extrude")

        layout.row().operator("ctxyz.settype_with_scene_defaults", text="Add New Text", icon="SORTALPHA")


class ColdtypeMainPanel(bpy.types.Panel):
    bl_label = "Selected Text"
    bl_idname = "COLDTYPE_PT_2_MAINPANEL"
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

def clear_frame_changers():
    for funcs in [
        bpy.app.handlers.frame_change_pre,
        bpy.app.handlers.frame_change_post
        ]:
        remove = []
        for handler in funcs:
            if handler.__name__ == properties.update_type_frame_change.__name__:
                remove.append(handler)

        for func in remove:
            try:
                funcs.remove(func)
            except ValueError:
                pass


def register():
    print("---COLDTYPE---", bl_info["version"])

    for c in all_classes:
        bpy.utils.register_class(c)
    
    for p in all_panels:
        bpy.utils.register_class(p)

    bpy.types.Scene.ctxyz = bpy.props.PointerProperty(type=properties.ColdtypePropertiesGroup, name="Coldtype", description="Default Coldtype properties")
    bpy.types.Object.ctxyz = bpy.props.PointerProperty(type=properties.ColdtypePropertiesGroup, name="Coldtype", description="Coldtype properties")

    clear_frame_changers()
    frame_changers.append(properties.update_type_frame_change)


def unregister():
    for p in reversed(all_panels):
        bpy.utils.unregister_class(p)

    for c in reversed(all_classes):
        bpy.utils.unregister_class(c)

    clear_frame_changers()

if __name__ == "__main__":
    register()
