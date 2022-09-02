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
from pathlib import Path


if "bpy" in locals():
    for module in modules:
        importlib.reload(module)
else:
    import bpy
    from Coldtype import importer, operations, properties, typesetter, search, exporting

#from Coldtype import importer

modules = [importer, properties, operations, typesetter, search, exporting]


if importer.C is not None:
    from fontTools.ttLib.ttFont import TTFont, registerCustomTableClass
    registerCustomTableClass("MESH", "Coldtype.meshtable", "table__M_E_S_H")


def _update_type(props, context):
#    data, active = find_ctxyz(context)
#    if props != data:

    for obj in context.scene.objects:
        if obj.ctxyz == props and obj.ctxyz.frozen != True:
            typesetter.set_type(obj.ctxyz, obj, scene=context.scene)
            return obj
    
    # if data.updatable and not data.baked:
    #     set_type(data, active, scene=context.scene)
    #return data, active

def update_type(props, context):
    _update_type(props, context)

def update_type_and_copy(prop, props, context):
    active = _update_type(props, context)
    if active:
        for obj in context.scene.objects:
            if obj.ctxyz.editable(obj) and obj != active and obj != context.active_object:
                setattr(obj.ctxyz, prop, getattr(active.ctxyz, prop))

def is_rendering():
    try:
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D' and space.shading.type == "RENDERED":
                        return True
    except:
        pass
    return False

def update_type_frame_change(scene, depsgraph):
    rendered_view = is_rendering()
    playing = bpy.context.screen.is_animation_playing if bpy.context.screen else False
    lu = scene.ctxyz.live_updating

    if lu == "NOPREVIEW":
        return
    elif lu == "NONRENDERSTATIC" and (rendered_view or playing):
        return
    elif lu == "NONRENDERANIMATE" and rendered_view:
        return
    elif lu == "RENDERSTATIC" and rendered_view and playing:
        return

    for obj in scene.objects:
        data = obj.ctxyz
        if data.updatable and not data.baked and obj.hide_render == False and data.has_keyframes(obj):
            typesetter.set_type(data, obj, scene=scene)


ColdtypePropertiesGroup = properties.build_properties(
    update_type, update_type_and_copy)


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

        #row = layout.row()

    #if mesh:
    #    row = layout.row()

    row.prop(data, "use_horizontal_font_metrics", text="", icon="EVENT_X")
    row.prop(data, "use_vertical_font_metrics", text="", icon="EVENT_Y")

    if not mesh:
        row = layout.row()
        row.prop(data, "combine_glyphs", text="", icon="META_DATA")
        row.prop(data, "remove_overlap", text="", icon="OVERLAY")
        
        #row.separator()
        #row.label(text="Outline")

        #row = layout.row()
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


def font_advanced(layout, data, font, obj):
    fvars = font.variations()
    if len(fvars) > 0:
        row = layout.row()
        icon = 'TRIA_DOWN' if data.font_variations_open else 'TRIA_RIGHT'
        row.prop(data, 'font_variations_open', icon=icon, icon_only=True)
        row.label(text='Font Variations')

        if data.font_variations_open:
            row.operator("ctxyz.load_var_axes_defaults", icon="EMPTY_AXIS", text="")
            #box = layout.box()
        
            for idx, (k, v) in enumerate(fvars.items()):
                layout.row().prop(data, f"fvar_axis{idx+1}", text=k)
        
            if obj.ctxyz.has_keyframes(obj):
                #layout.row().label(text="Variation Offsets")

                for idx, (k, v) in enumerate(fvars.items()):
                    layout.row().prop(data, f"fvar_axis{idx+1}_offset", text=f"{k} offset")
            
            layout.separator()
    
    row = layout.row()
    icon = 'TRIA_DOWN' if data.font_features_open else 'TRIA_RIGHT'
    row.prop(data, 'font_features_open', icon=icon, icon_only=True)
    row.label(text='Font Features')

    if data.font_features_open:
        box = layout.box()

        fi = 0
        row = None

        def show_fea(fea):
            nonlocal fi, row
            if fi%4 == 0 or row is None:
                row = box.row()
            
            row.prop(data, f"fea_{fea}")
            fi += 1
        
        for fea in font.font.featuresGPOS:
            if not hasattr(data, f"fea_{fea}"):
                #print("!", fea)
                pass
            else:
                show_fea(fea)

        for fea in font.font.featuresGSUB:
            if not fea.startswith("cv") and not fea.startswith("ss"):
                if not hasattr(data, f"fea_{fea}"):
                    #print(fea)
                    pass
                else:
                    show_fea(fea)
        
        if len(font.font.stylisticSetNames) > 0:
            for x in range(1, 21):
                tag = "ss{:02d}".format(x)
                ss_name = font.font.stylisticSetNames.get(tag)
                if ss_name:
                    row = box.row()
                    row.prop(data, "fea_ss{:02d}".format(x), text=f"{tag}: {ss_name}")
        
    # box = layout.box()
    # row = box.row()
    # row.prop(data, "individual_glyphs")
    # row = box.row()
    # row.prop(data, "stagger_y")
    # row.prop(data, "stagger_z")


def dimensional_advanced(layout, data, obj):
    row = layout.row()
    icon = 'TRIA_DOWN' if data.dimensional_open else 'TRIA_RIGHT'
    row.prop(data, 'dimensional_open', icon=icon, icon_only=True)
    row.label(text='3D Settings')

    if data.dimensional_open:
        box = layout.box()
        if obj:
            row = box.row()
            row.prop(obj, "rotation_euler", text="Rotation")
            row = box.row()
            row.prop(obj.data, "extrude", text="Extrude")
            row.prop(obj.data, "bevel_depth", text="Bevel")
            row = box.row()
            row.prop(obj.data, "fill_mode", text="Fill Mode")


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

    if font:
        if data.updatable and obj:
            font_advanced(layout, data, font, obj)
            if not mesh:
                dimensional_advanced(layout, data, obj)
            #export_options(layout, data, obj)
        else:
            # TODO dimensional defaults, but need new props
            pass
    
    if font and not data.updatable:
        layout.row().separator()
        #layout.row().prop(data, "individual_glyphs")
        layout.row().operator("ctxyz.settype_with_scene_defaults", text="Build Text", icon="SORTALPHA")


def active_obj_has_ctxyz():
    ob = bpy.context.active_object
    return ob and ob.select_get() and ob.ctxyz.updatable


class ColdtypeDefaultPanel(bpy.types.Panel):
    bl_label = "Defaults"
    bl_idname = "COLDTYPE_PT_1_DEFAULTPANEL"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Coldtype"

    @classmethod
    def poll(cls, context):
        obj = bpy.context.active_object
        return importer.C is not None and not (obj and obj.select_get())
    
    def draw(self, context):
        if len(bpy.app.handlers.frame_change_post) == 0:
            frame_changers.append(update_type_frame_change)

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
        obj = bpy.context.active_object
        return importer.C is not None and obj and obj.select_get() and not obj.ctxyz.baked
    
    def draw(self, context):
        obj = bpy.context.active_object
        if obj and obj.select_get() and obj.ctxyz.parent:
            pobj = bpy.data.objects[obj.ctxyz.parent]
            layout_editor(self.layout, pobj.ctxyz, pobj, context)
        elif obj and obj.select_get() and obj.ctxyz.updatable:
            layout_editor(self.layout, obj.ctxyz, obj, context)
        #else:
            #layout_editor(self.layout, context.scene.ctxyz, None, context)


class ColdtypeGlobalPanel(bpy.types.Panel):
    bl_label = "Render Settings"
    bl_idname = "COLDTYPE_PT_9_GLOBALPANEL"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Coldtype"

    @classmethod
    def poll(cls, context):
        return importer.C is not None
    
    def draw(self, context):
        row = self.layout.row()
        row.prop(context.scene.ctxyz, "live_updating", text="")


classes = [
    ColdtypePropertiesGroup,
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
            if handler.__name__ == update_type_frame_change.__name__:
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

    bpy.types.Scene.ctxyz = bpy.props.PointerProperty(type=ColdtypePropertiesGroup, name="Coldtype", description="Default Coldtype properties")
    bpy.types.Object.ctxyz = bpy.props.PointerProperty(type=ColdtypePropertiesGroup, name="Coldtype", description="Coldtype properties")

    clear_frame_changers()
    frame_changers.append(update_type_frame_change)


def unregister():
    for p in reversed(all_panels):
        bpy.utils.unregister_class(p)

    for c in reversed(all_classes):
        bpy.utils.unregister_class(c)

    clear_frame_changers()

if __name__ == "__main__":
    register()
