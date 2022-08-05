bl_info = {
    "name": "Coldtype",
    "author": "Rob Stenson",
    "version": (0, 3),
    "blender": (3, 0, 0),
    "location": "View3D > Toolshelf",
    "description": "Well-shaped 3D typography",
    "warning": "",
    "wiki_url": "",
    "category": "Coldtype",
}

# TODO
# - justification of words? (ala the line-crunching example)

import importlib
from pathlib import Path

# apparently if you require this twice, it'll work the second time (??)
try:
    from ufo2ft.featureCompiler import FeatureCompiler
except ImportError:
    print("-- failed FeatureCompiler --")
    pass

if "bpy" in locals():
    # bpy.ops.scripts.reload() was called
    importlib.reload(importer)
    importlib.reload(properties)
    importlib.reload(typesetter)
else:
    import bpy
    from bpy_extras.io_utils import ImportHelper
    from Coldtype import importer
    from Coldtype import properties

importer.require_coldtype(globals())

if globals().get("coldtype_found") == True:
    from Coldtype import typesetter


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

def find_ctxyz_editables(context):
    editables = []
    for o in context.scene.objects:
        if o.ctxyz.editable(o):
            editables.append(o)
    return editables

def find_ctxyz_all_selected(context):
    selected = []
    for o in context.scene.objects:
        if o.ctxyz.editable(o) and o.select_get():
            selected.append(o)
    return selected

def find_ctxyz(context):
    ob = context.active_object
    if ob is not None and ob.select_get():
        return ob.ctxyz, ob
    else:
        return context.scene.ctxyz, None


ColdtypePropertiesGroup = properties.build_properties(
    update_type, update_type_and_copy)


def editor_for_exported_text(layout, data):
    layout.row().label(text=f"Baked frame: “{data.text}”")
    layout.row().operator("ctxyz.delete_bake", text="Delete Baked Frames")

def individual_font(layout, data, font_index):
    row = layout.row()
    op = row.operator("wm.ctxyz_choose_font", text="", icon="FONTPREVIEW")
    op.font_index = font_index

    if font_index > 0:
        font_path = getattr(data, f"font_path_alt{font_index}")
    else:
        font_path = data.font_path

    font = ct.Font.Cacheable(font_path)

    #layout.row().prop(data, "font_path", text="")
    
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
            #layout.row().prop(data, "ufo_path", text="", icon="UNDERLINE")

def font_basics(layout, data, font, obj):
    individual_font(layout, data, 0)

    if font:
        for x in range(1, 4):
            fp = getattr(data, f"font_path_alt{x}")
            if fp:
                individual_font(layout, data, x)
        
        if obj and False:
            row = layout.row()
            row.operator("ctxyz.add_font", text="Add Font")
            row.prop(data, "font_path_index", text="")

    row = layout.row()
    row.label(text="Position")

    row.prop(data, "align_x", text="X", expand=True)
    row.prop(data, "align_y", text="Y", expand=True)

    #row = layout.row()

    row.prop(data, "use_horizontal_font_metrics", text="", icon="EVENT_X")
    row.prop(data, "use_vertical_font_metrics", text="", icon="EVENT_Y")

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

def export_options(layout, data, obj):
    row = layout.row()
    #row.label(text="Live Rendering")
    #row.prop(data, "live_rendered_updates", icon="ONIONSKIN_ON", icon_only=True)
    #row.prop(data, "live_rendered_animation", icon="PLAY", icon_only=True)
    #row.prop(data, "live_updating")

    row = layout.row()
    icon = 'TRIA_DOWN' if data.export_open else 'TRIA_RIGHT'
    row.prop(data, 'export_open', icon=icon, icon_only=True)
    row.label(text='Export')

    if data.export_open:
        box = layout.box()

        row = box.row()
        row.label(text="Options")
        row.prop(data, "export_meshes", icon="OUTLINER_OB_MESH", icon_only=True)
        row.prop(data, "export_geometric_origins", icon="TRANSFORM_ORIGINS", icon_only=True)
        row.prop(data, "export_apply_transforms", icon="DRIVER_TRANSFORM", icon_only=True)

        row = box.row()
        row.label(text="Export Static")
        row.operator("ctxyz.export_slug", text="Slug")
        row.operator("ctxyz.export_glyphs", text="Glyphs")
    
        if obj.ctxyz.has_keyframes(obj):
            row = box.row()
            row.label(text="Export Animated")
            row.operator("ctxyz.bake_frames", text="Timed")
            row.operator("ctxyz.bake_frames_no_timing", text="Untimed")
            row.prop(data, "export_every_x_frame", text="")


def layout_editor(layout, data, obj, context):
    if not globals().get("coldtype_found"):
        return importer.editor_needs_coldtype(layout)

    if data.baked:
        return editor_for_exported_text(layout, data)

    if data.updatable and obj:
        editables = find_ctxyz_editables(context)

        if len(editables) == 2:
            row = layout.row()
            row.operator("ctxyz.interpolate_strings", text="Interpolate")
            row.prop(context.scene.ctxyz, "interpolator_count", text="")
            row.prop(context.scene.ctxyz, "interpolator_easing", text="")
            layout.row().separator()
    
    row = layout.row()
    row.prop(data, "text")

    font = None
    if data.font_path:
        try:
            font = ct.Font.Cacheable(data.font_path)
        except ct.FontNotFoundException:
            font = None

    font_basics(layout, data, font, obj)

    if font:
        if data.updatable and obj:
            font_advanced(layout, data, font, obj)
            dimensional_advanced(layout, data, obj)
            export_options(layout, data, obj)
        else:
            # TODO dimensional defaults, but need new props
            pass
    
    if font and not data.updatable:
        layout.row().separator()
        layout.row().operator("ctxyz.settype_with_scene_defaults", text="Build Text", icon="SORTALPHA")
    
    layout.row().separator()
    row = layout.row()
    row.label(text="Global Render Settings")
    row = layout.row()
    row.prop(context.scene.ctxyz, "live_updating", text="")


def active_obj_has_ctxyz():
    ob = bpy.context.active_object
    return ob and ob.select_get() and ob.ctxyz.updatable


class ColdtypeMainPanel(bpy.types.Panel):
    bl_label = "Coldtype"
    bl_idname = "COLDTYPE_PT_MAINPANEL"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Coldtype"
    
    def draw(self, context):
        if len(bpy.app.handlers.frame_change_post) == 0:
            frame_changers.append(update_type_frame_change)

        obj = bpy.context.active_object
        if obj and obj.select_get() and obj.ctxyz.updatable:
            layout_editor(self.layout, obj.ctxyz, obj, context)
        else:
            layout_editor(self.layout, context.scene.ctxyz, None, context)


class WM_OT_ColdtypeChooseFont(bpy.types.Operator, ImportHelper):
    """Open file dialog to pick a font"""
    bl_idname = "wm.ctxyz_choose_font"
    bl_label = "Choose font file"

    font_index: bpy.props.IntProperty(default=0)

    #filepath = bpy.props.StringProperty(subtype='DIR_PATH')
    
    filter_glob: bpy.props.StringProperty(
        default='*.ttf;*.otf;*.ufo;*.designspace',
        options={'HIDDEN'})

    def invoke(self, context, event):
        #self.filepath = str(Path("~/Library/Fonts/asdf").expanduser())
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        path = Path(self.filepath)
        data, _ = find_ctxyz(context)
        
        font = ct.Font.Cacheable(path)
        if self.font_index == 0:
            data.font_path = str(font.path)
        else:
            setattr(data, f"font_path_alt{self.font_index}", str(font.path))
        return {'FINISHED'}


class Coldtype_OT_ClearFont(bpy.types.Operator):
    bl_label = "Coldtype Clear Font"
    bl_idname = "ctxyz.clear_font"
    bl_options = {"REGISTER","UNDO"}
    
    def execute(self, context):
        ts = context.scene.ctxyz
        ts.font_path = ""

        # TODO reset stuff?
        return {"FINISHED"}


class Coldtype_OT_SetTypeWithSceneDefaults(bpy.types.Operator):
    """Build text with current settings"""

    bl_label = "Coldtype SetType Scene"
    bl_idname = "ctxyz.settype_with_scene_defaults"
    bl_options = {"REGISTER","UNDO"}
    
    def execute(self, context):
        ts = context.scene.ctxyz
        txtObj = typesetter.set_type(ts)[0]
        
        for k in ts.__annotations__.keys():
            v = getattr(ts, k)
            setattr(txtObj.obj.ctxyz, k, v)
        
        txtObj.obj.ctxyz.updatable = True
        txtObj.obj.ctxyz.frozen = False
        txtObj.obj.select_set(True)
        
        return {"FINISHED"}


class Coldtype_OT_SetTypeWithObject(bpy.types.Operator):
    bl_label = "Coldtype SetType Object"
    bl_idname = "ctxyz.settype_with_object"
    bl_options = {"REGISTER","UNDO"}
    
    def execute(self, context):
        obj = context.active_object
        typesetter.set_type(obj.ctxyz)
        return {"FINISHED"}


def bake_frames(context, framewise=True, frames=None, glyphwise=False, progress_fn=None):
    obj = context.active_object
    obj.ctxyz.frozen = True
    sc = context.scene
    current = sc.frame_current

    anchor = cb.BpyObj.Empty(f"{obj.name}_BakedFrames_Anchor", collection="Global")
    
    for k in obj.ctxyz.__annotations__.keys():
        v = getattr(obj.ctxyz, k)
        setattr(anchor.obj.ctxyz, k, v)
    
    anchor.obj.ctxyz.baked = True
    anchor.obj.ctxyz.baked_from = obj.name
    anchor.obj.ctxyz.bake_frame = -1
    anchor.obj.ctxyz.updatable = True

    if not frames:
        frames = range(sc.frame_start, sc.frame_end+1)

    duration = len(frames)

    for frame in frames:
        if progress_fn:
            progress_fn(frame/duration)
        
        if frame%obj.ctxyz.export_every_x_frame != 0:
            print("skipping", frame)
            continue
        
        sc.frame_set(frame)
        print("> baking:", frame)
        typesetter.set_type(obj.ctxyz, obj
            , baking=True
            , parent=anchor.obj
            , context=context
            , scene=context.scene
            , framewise=framewise
            , glyphwise=glyphwise)
        #bpy.context.view_layer.update()
    
    sc.frame_set(current)

    obj.ctxyz.frozen = False
    obj.hide_render = True
    obj.hide_set(True)

    print(">>>>>>> BAKED")

    bpy.context.view_layer.objects.active = None
    bpy.context.view_layer.objects.active = anchor.obj
    bpy.ops.object.select_all(action='DESELECT')
    #print("deselecting all")
    anchor.obj.select_set(True)
    return anchor


class Coldtype_OT_RefreshSettings(bpy.types.Operator):
    """Refresh/resync all live text to specified settings"""

    bl_label = "Coldtype Refresh Settings"
    bl_idname = "ctxyz.refresh_settings"
    
    def execute(self, context):
        editables = find_ctxyz_editables(context)
        for e in editables:
            typesetter.set_type(e.ctxyz, e, context=context)
        return {"FINISHED"}


class Coldtype_OT_LoadVarAxesDefaults(bpy.types.Operator):
    """Set variable font axes to their font-specified default values"""

    bl_label = "Coldtype Load Var Axes Defaults"
    bl_idname = "ctxyz.load_var_axes_defaults"
    
    def execute(self, context):
        for o in find_ctxyz_all_selected(context):
            font = ct.Font.Cacheable(o.ctxyz.font_path)
            for idx, (axis, v) in enumerate(font.variations().items()):
                diff = abs(v["maxValue"]-v["minValue"])
                v = (v["defaultValue"]-v["minValue"])/diff
                setattr(o.ctxyz, f"fvar_axis{idx+1}", v)
                print(">", axis, v)

        return {"FINISHED"}


def cycle_font(context, inc):
    data, obj = find_ctxyz(context)
    font_path = Path(data.font_path)
    fonts = []
    for file in sorted(font_path.parent.iterdir(), key=lambda x: x.name):
        if file.suffix in [".otf", ".ttf", ".ufo"]:
            fonts.append(file)
    
    fidx = fonts.index(font_path)
    try:
        adj_font = fonts[fidx+inc]
    except IndexError:
        if inc > 0:
            adj_font = fonts[0]
        else:
            adj_font = fonts[len(fonts)-1]
    
    data.font_path = str(adj_font)


class Coldtype_OT_LoadNextFont(bpy.types.Operator):
    """Load next font in directory"""

    bl_label = "Coldtype Load Next Font"
    bl_idname = "ctxyz.load_next_font"
    
    def execute(self, context):
        cycle_font(context, +1)
        return {"FINISHED"}


class Coldtype_OT_LoadPrevFont(bpy.types.Operator):
    """Load previous font in directory"""

    bl_label = "Coldtype Load Previous Font"
    bl_idname = "ctxyz.load_prev_font"
    
    def execute(self, context):
        cycle_font(context, -1)
        return {"FINISHED"}


class Coldtype_OT_AddFont(bpy.types.Operator):
    """Add font for keyframing fonts"""

    bl_label = "Coldtype Add Font"
    bl_idname = "ctxyz.add_font"
    
    def execute(self, context):
        for o in find_ctxyz_all_selected(context):
            font_idx = 0
            for x in range(1, 4):
                if getattr(o.ctxyz, f"font_path_alt{x}"):
                    font_idx = x
            
            if font_idx < 3:
                setattr(o.ctxyz, f"font_path_alt{font_idx+1}", o.ctxyz.font_path)
        return {"FINISHED"}


class Coldtype_OT_ExportSlug(bpy.types.Operator):
    """Export slug as single shape"""

    bl_label = "Coldtype Export Slug"
    bl_idname = "ctxyz.export_slug"
    bl_options = {"REGISTER","UNDO"}
    
    def execute(self, context):
        bake_frames(context, framewise=False, glyphwise=False, frames=[context.scene.frame_current])
        return {"FINISHED"}

class Coldtype_OT_ExportGlyphs(bpy.types.Operator):
    """Export glyphs as individual shapes"""

    bl_label = "Coldtype Export Glyphs"
    bl_idname = "ctxyz.export_glyphs"
    bl_options = {"REGISTER","UNDO"}
    
    def execute(self, context):
        bake_frames(context, framewise=False, glyphwise=True, frames=[context.scene.frame_current])
        return {"FINISHED"}


class Coldtype_OT_InterpolateStrings(bpy.types.Operator):
    """Interpolate multiple strings"""

    bl_label = "Coldtype Interpolate Strings"
    bl_idname = "ctxyz.interpolate_strings"
    bl_options = {"REGISTER","UNDO"}
    
    def execute(self, context):
        data = context.scene.ctxyz
        editables = find_ctxyz_editables(context)
        a = editables[0]
        b = editables[1]
        collection = a.users_collection[0]

        font = ct.Font.Cacheable(a.ctxyz.font_path)
        fvars = font.variations()

        from coldtype.time.easing import ease
        from coldtype.interpolation import norm

        created = []

        context.window_manager.progress_begin(0, 1)

        for x in range(0, data.interpolator_count):
            xi = x + 1
            p = xi / (data.interpolator_count + 1)
            e, _ = ease(data.interpolator_easing, p)

            context.window_manager.progress_update(e)

            c = typesetter.set_type(data, object_name=f"{a.name}_{b.name}_Interpolated", collection=f"{a.name}_{b.name}_Interpolations")[0]
            c = c.obj

            created.append(c)
            
            c.location = a.location.lerp(b.location, e)

            c.data = a.data.copy()
            c.animation_data_clear()

            for ax in range(0, 3):
                c.rotation_euler[ax] = norm(e, a.rotation_euler[ax], b.rotation_euler[ax])

                c.scale[ax] = norm(e, a.scale[ax], b.scale[ax])
            
            c.data.extrude = norm(e, a.data.extrude, b.data.extrude)

            for k in a.ctxyz.__annotations__.keys():
                v = getattr(a.ctxyz, k)
                setattr(c.ctxyz, k, v)
            
            c.ctxyz.frozen = True
            for idx, (k, v) in enumerate(fvars.items()):
                prop = f"fvar_axis{idx+1}"
                setattr(c.ctxyz, prop, norm(e, getattr(a.ctxyz, prop), getattr(b.ctxyz, prop)))
            c.ctxyz.frozen = False

            typesetter.set_type(c.ctxyz, c, context=context)

        context.window_manager.progress_end()

        bpy.ops.object.select_all(action='DESELECT')
        for obj in created:
            obj.select_set(True)

        return {"FINISHED"}


class Coldtype_OT_BakeFrames(bpy.types.Operator):
    """Bake animation as individual curves, shown/hidden per-frame"""

    bl_label = "Coldtype Bake Frames"
    bl_idname = "ctxyz.bake_frames"
    bl_options = {"REGISTER","UNDO"}
    
    def execute(self, context):
        context.window_manager.progress_begin(0, 1)
        bake_frames(context, framewise=True, progress_fn=lambda x: 
            context.window_manager.progress_update(x))
        context.window_manager.progress_end()
        return {"FINISHED"}


class Coldtype_OT_BakeFramesNoTiming(bpy.types.Operator):
    """Bake animation as individual curves, shown all at once"""

    bl_label = "Coldtype Bake Frames with No Timing"
    bl_idname = "ctxyz.bake_frames_no_timing"
    bl_options = {"REGISTER","UNDO"}
    
    def execute(self, context):
        context.window_manager.progress_begin(0, 1)
        bake_frames(context, framewise=False, progress_fn=lambda x: 
            context.window_manager.progress_update(x))
        context.window_manager.progress_end()
        
        return {"FINISHED"}


class Coldtype_OT_DeleteBake(bpy.types.Operator):
    bl_label = "Coldtype Delete Bake"
    bl_idname = "ctxyz.delete_bake"
    bl_options = {"REGISTER","UNDO"}
    
    def execute(self, context):
        obj = context.active_object
        ts = obj.ctxyz
        ts_baked_from = ts.baked_from
        if ts.baked and ts.baked_from:
            baked_from = context.scene.objects[ts.baked_from]
            current = context.scene.frame_current

            for obj in context.scene.objects:
                # TODO delete only the actual composition in question
                if obj.ctxyz.bake_frame > -1 and obj.ctxyz.baked_from == ts_baked_from:
                    bpy.ops.object.select_all(action='DESELECT')
                    context.scene.frame_set(obj.ctxyz.bake_frame)
                    obj.select_set(True)
                    bpy.ops.object.delete()
            
            for obj in context.scene.objects:
                if obj.ctxyz.bake_frame == -1 and obj.ctxyz.baked:
                    bpy.ops.object.select_all(action='DESELECT')
                    obj.select_set(True)
                    bpy.ops.object.delete()
            
            baked_from.hide_set(False)
            baked_from.hide_render = False

            bpy.context.view_layer.objects.active = None
            bpy.context.view_layer.objects.active = baked_from
            bpy.ops.object.select_all(action='DESELECT')
            baked_from.select_set(True)
            
            #context.scene.frame_set(current)
            # make original visible

        return {"FINISHED"}


class Coldtype_OT_InstallColdtype(bpy.types.Operator):
    """In order to work properly, Coldtype needs to download and install the Coldtype python package. You can install that package by clicking this button."""

    bl_label = "Coldtype Install Coldtype"
    bl_idname = "ctxyz.install_coldtype"
    
    def execute(self, context):
        importer.install_coldtype(context, globals())
        from Coldtype import typesetter
        globals()["ctxyz_typesetter"] = typesetter
        return {"FINISHED"}


classes = [
    ColdtypePropertiesGroup,
    Coldtype_OT_SetTypeWithSceneDefaults,
    Coldtype_OT_SetTypeWithObject,
    Coldtype_OT_RefreshSettings,
    Coldtype_OT_LoadVarAxesDefaults,
    Coldtype_OT_AddFont,
    Coldtype_OT_ClearFont,
    Coldtype_OT_ExportSlug,
    Coldtype_OT_ExportGlyphs,
    Coldtype_OT_BakeFrames,
    Coldtype_OT_BakeFramesNoTiming,
    Coldtype_OT_InterpolateStrings,
    Coldtype_OT_DeleteBake,
    Coldtype_OT_InstallColdtype,
    Coldtype_OT_LoadNextFont,
    Coldtype_OT_LoadPrevFont,
    ColdtypeMainPanel,
    WM_OT_ColdtypeChooseFont,
]

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

    for cl in classes:
        bpy.utils.register_class(cl)

    bpy.types.Scene.ctxyz = bpy.props.PointerProperty(type=ColdtypePropertiesGroup, name="Coldtype", description="Default Coldtype properties")
    bpy.types.Object.ctxyz = bpy.props.PointerProperty(type=ColdtypePropertiesGroup, name="Coldtype", description="Coldtype properties")

    clear_frame_changers()
    frame_changers.append(update_type_frame_change)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    clear_frame_changers()

if __name__ == "__main__":
    register()

#register()

#bpy.ops.ctxyz.settype_with_scene_defaults()