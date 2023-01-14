import bpy

from ST2 import typesetter

try:
    import coldtype.text as ct
except ImportError:
    ct = None


def _update_type(props, context):
#    data, active = find_st2(context)
#    if props != data:

    for obj in context.scene.objects:
        if obj.st2 == props and obj.st2.frozen != True:
            typesetter.set_type(obj.st2, obj, scene=context.scene)
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
            if obj.st2.editable(obj) and obj != active and obj != context.active_object:
                setattr(obj.st2, prop, getattr(active.st2, prop))

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
    lu = scene.st2.live_updating

    if lu == "NOPREVIEW":
        return
    elif lu == "NONRENDERSTATIC" and (rendered_view or playing):
        return
    elif lu == "NONRENDERANIMATE" and rendered_view:
        return
    elif lu == "RENDERSTATIC" and rendered_view and playing:
        return

    for obj in scene.objects:
        data = obj.st2
        if data.updatable and not data.baked and obj.hide_render == False and data.has_keyframes(obj):
            typesetter.set_type(data, obj, scene=scene)


def feaprop(prop, default=False):
    prop_key = f"fea_{prop}"
    return bpy.props.BoolProperty(name=prop, default=default, update=lambda p, c: update_type_and_copy(prop_key, p, c))

def axisprop(num, default=0):
    prop = f"fvar_axis{num}"
    return bpy.props.FloatProperty(name=f"Axis {num}", default=default, min=0, max=1, update=lambda p, c: update_type_and_copy(prop, p, c))

def axisprop_offset(num, default=0):
    prop = f"fvar_axis{num}_offset"
    return bpy.props.FloatProperty(name=f"Axis {num} Offset", default=default, min=-20, max=20, update=update_type)


class ST2PropertiesGroup(bpy.types.PropertyGroup):
    text: bpy.props.StringProperty(name="Text", default="Text",
        update=lambda p, c: update_type_and_copy("text", p, c))
    
    text_mode: bpy.props.EnumProperty(name="Text Mode",
        description="Where to source the text",
        items=[
            ("UI", "UI", "As typed above", "SMALL_CAPS", 0),
            ("BLOCK", "Block", "From a text-block in Blender", "TEXT", 1),
            ("FILE", "Text file", "From an external text file", "FILE_TEXT", 2),
        ],
        default="UI",
        update=lambda p, c: update_type_and_copy("text_mode", p, c))
    
    text_file: bpy.props.StringProperty(name="Text File", default="", subtype="FILE_PATH", update=lambda p, c: update_type_and_copy("text_file", p, c))
    
    text_block: bpy.props.StringProperty(name="Text Block", default="", update=lambda p, c: update_type_and_copy("text_block", p, c))
    
    text_indexed: bpy.props.BoolProperty(name="Text Indexed", default=False, update=lambda p, c: update_type_and_copy("text_indexed", p, c))
    
    text_index: bpy.props.IntProperty(name="Text Index", default=1, min=1, update=lambda p, c: update_type_and_copy("text_index", p, c))

    script_mode: bpy.props.EnumProperty(name="Script Mode",
        description="Where to source the script",
        items=[
            ("BLOCK", "Block", "From a text-block in Blender", "TEXT", 0),
            ("FILE", "Text file", "From an external text file", "FILE_TEXT", 1),
        ],
        default="FILE",
        update=lambda p, c: update_type_and_copy("script_mode", p, c))

    script_file: bpy.props.StringProperty(name="Script File", default="", subtype="FILE_PATH", update=lambda p, c: update_type_and_copy("script_file", p, c))

    script_block: bpy.props.StringProperty(name="Script Block", default="", update=lambda p, c: update_type_and_copy("script_block", p, c))

    script_enabled: bpy.props.BoolProperty(name="Script Enabled", default=False, update=lambda p, c: update_type_and_copy("script_enabled", p, c))

    script_watch: bpy.props.BoolProperty(name="Script Watch", default=False)

    script_kwargs: bpy.props.StringProperty(name="Script Args", default="", update=lambda p, c: update_type_and_copy("script_kwargs", p, c))
    
    font_path: bpy.props.StringProperty(name="Font", default="", update=lambda p, c: update_type_and_copy("font_path", p, c))

    enable_font_search: bpy.props.BoolProperty(name="Enable Font Search", default=False, update=lambda p, c: update_type_and_copy("enable_font_search", p, c))

    default_upright: bpy.props.BoolProperty(name="Default to Upright", default=False)

    default_extrude: bpy.props.FloatProperty(name="Default Extrude Depth", default=0.1)

    #stagger: bpy.props.StringProperty(name="Stagger", default="")
    #bounce: bpy.props.StringProperty(name="Bounce", default="")
    
    # internal
    
    frozen: bpy.props.BoolProperty(name="Frozen", default=True)
    updatable: bpy.props.BoolProperty(name="Updatable", default=False)
    baked: bpy.props.BoolProperty(name="Baked", default=False)
    baked_from: bpy.props.StringProperty(name="Baked From", default="")
    bake_frame: bpy.props.IntProperty(name="Bake Frame", default=-1)

    parent: bpy.props.StringProperty(name="Parent", default="")

    auto_rename: bpy.props.BoolProperty(name="Auto Rename", default=True)

    # mesh-state

    meshOffsetX: bpy.props.IntProperty(name="Mesh Offset X", default=0)
    meshOffsetY: bpy.props.IntProperty(name="Mesh Offset Y", default=0)

    use_mesh: bpy.props.BoolProperty(name="Use Mesh", default=True)
    
    # ui-state
    
    font_variations_open: bpy.props.BoolProperty(name="Font Variations", default=True)
    font_features_open: bpy.props.BoolProperty(name="Font Features", default=False)
    dimensional_open: bpy.props.BoolProperty(name="3D Settings", default=True)
    export_open: bpy.props.BoolProperty(name="Export Settings", default=True)

    # animating

    live_rendered_animation: bpy.props.BoolProperty(name="Live Rendered Animation", default=False)
    live_rendered_updates: bpy.props.BoolProperty(name="Live Rendered Updates", default=False)

    live_updating: bpy.props.EnumProperty(name="Live Updating",
        description="How/when should live updating happen",
        items=[
            ("NOPREVIEW", "No live updating", "Must export to view animation"),
            ("NONRENDERSTATIC", "Non-rendered static", "No playback support"),
            ("NONRENDERANIMATE", "Non-rendered animation", "Playback support only in non-render view"),
            ("RENDERSTATIC", "Rendered static", "Step frames to view animation"),
            ("RENDERANIMATE", "Rendered animation", "Full playback support in rendered view"),
        ],
        default="NONRENDERANIMATE")

    # exporting

    export_meshes: bpy.props.BoolProperty(name="Export as Meshes", default=True)
    export_geometric_origins: bpy.props.BoolProperty(name="Export with Geometric Origins", default=True)
    export_apply_transforms: bpy.props.BoolProperty(name="Export with Applied Transforms", default=True)
    export_rigidbody_active: bpy.props.BoolProperty(name="Export with Active Rigid Body", default=False)
    export_every_x_frame: bpy.props.IntProperty(name="Export Every X Frame", default=1, min=1, max=50)

    export_stagger_y: bpy.props.FloatProperty(name="Export Stagger Y", default=0)
    export_stagger_z: bpy.props.FloatProperty(name="Export Stagger Z", default=0)

    export_rotate_x: bpy.props.FloatProperty(name="Export Rotate X", default=0, unit="ROTATION")
    export_rotate_y: bpy.props.FloatProperty(name="Export Rotate Y", default=0, unit="ROTATION")
    export_rotate_z: bpy.props.FloatProperty(name="Export Rotate Z", default=0, unit="ROTATION")

    # interpolating

    interpolator_easing: bpy.props.StringProperty(name="Interpolator Easing", default="linear")

    interpolator_count: bpy.props.IntProperty(name="Interpolator Count", default=1, min=1, max=50)

    interpolated: bpy.props.BoolProperty(name="Interpolated", default=False)

    interpolator_style: bpy.props.EnumProperty(name="Interpolator Style", items=[
        ("TOP", "Top-level", "Create new interpolated object(s) at top-level", "MESH_CUBE", 0),
        ("PARENT", "Empty Parent", "Create new interpolated object(s) that are parented to an empty at the origin", "EMPTY_AXIS", 1),
        ("COLLECTION", "Collection", "Create new interpolated object(s) that are added to a collection", "COLLECTION_NEW", 2),
    ], default="TOP", update=lambda p, c: update_type_and_copy("interpolator_style", p, c))

    export_style: bpy.props.EnumProperty(name="Export Style", items=[
        ("TOP", "Top-level", "Export object(s) at top-level", "MESH_CUBE", 0),
        ("PARENT", "Empty Parent", "Export object(s) parented to an empty at the origin", "EMPTY_AXIS", 1),
        ("COLLECTION", "Collection", "Export object(s) into a collection", "COLLECTION_NEW", 2),
    ], default="PARENT", update=lambda p, c: update_type_and_copy("export_style", p, c))
    
    # font state

    fit: bpy.props.FloatProperty(name="Fit Width", default=2, min=0.1, max=100, update=lambda p, c: update_type_and_copy("fit", p, c))

    fit_enable: bpy.props.BoolProperty(name="Fit Enable", default=False, update=lambda p, c: update_type_and_copy("fit_enable", p, c))

    outline: bpy.props.BoolProperty(name="Outline", default=0, update=update_type)
    
    outline_weight: bpy.props.FloatProperty(name="Outline Weight", default=1, min=-20, max=100, update=update_type)

    outline_outer: bpy.props.BoolProperty(name="Outline Outer", default=0, update=update_type)

    outline_miter_limit: bpy.props.FloatProperty(name="Outline Miter Limit", default=0.5, update=update_type)

    remove_overlap: bpy.props.BoolProperty(name="Remove Overlap", default=1, update=update_type)

    combine_glyphs: bpy.props.BoolProperty(name="Combine Glyphs", default=1, update=update_type)

    block: bpy.props.BoolProperty(name="Set on Blocks", default=0, update=update_type)
    block_inset_x: bpy.props.FloatProperty(name="Block Inset X", default=0, update=update_type)
    block_inset_y: bpy.props.FloatProperty(name="Block Inset Y", default=-0.05, update=update_type)
    block_horizontal_metrics: bpy.props.BoolProperty(name="Blocks Use Horizontal Font Metrics", default=True, update=update_type)
    block_vertical_metrics: bpy.props.BoolProperty(name="Blocks Use Vertical Font Metrics", default=True, update=update_type)

    tracking: bpy.props.IntProperty(name="Tracking", default=0, min=-1000, max=1000, update=lambda p, c: update_type_and_copy("tracking", p, c))
    
    leading: bpy.props.FloatProperty(name="Leading", default=0.5, min=-10, max=10, update=lambda p, c: update_type_and_copy("leading", p, c))

    align_lines_x: bpy.props.EnumProperty(name="Align Lines X", items=[
        ("W", "", "", "ALIGN_LEFT", 0),
        ("CX", "", "", "ALIGN_CENTER", 1),
        ("E", "", "", "ALIGN_RIGHT", 2),
    ], default="CX", update=lambda p, c: update_type_and_copy("align_lines_x", p, c))

    align_x: bpy.props.EnumProperty(name="Align X", items=[
        ("W", "", "", "ANCHOR_LEFT", 0),
        ("CX", "", "", "ANCHOR_CENTER", 1),
        ("E", "", "", "ANCHOR_RIGHT", 2),
    ], default="CX", update=update_type)

    align_y: bpy.props.EnumProperty(name="Align Y", items=[
        ("N", "", "", "ANCHOR_TOP", 0),
        ("CY", "", "", "ANCHOR_CENTER", 1),
        ("S", "", "", "ANCHOR_BOTTOM", 2),
    ], default="CY", update=update_type)

    use_horizontal_font_metrics: bpy.props.BoolProperty(name="Use Horizontal Font Metrics", default=True, update=update_type)

    use_vertical_font_metrics: bpy.props.BoolProperty(name="Use Vertical Font Metrics", default=True, update=update_type)

    case: bpy.props.EnumProperty(name="Case", items=[
        ("TYPED", "", "", "RADIOBUT_OFF", 0),
        ("UPPER", "", "", "TRIA_UP", 1),
        ("LOWER", "", "", "TRIA_DOWN", 2),
    ], default="TYPED", update=update_type)

    individual_glyphs: bpy.props.BoolProperty(name="Individual Glyphs", default=False)
    
    fvar_axis1: axisprop(1, 0)
    fvar_axis2: axisprop(2, 0)
    fvar_axis3: axisprop(3, 0)
    fvar_axis4: axisprop(4, 0)
    fvar_axis5: axisprop(5, 0)
    fvar_axis6: axisprop(6, 0)
    fvar_axis7: axisprop(7, 0)
    fvar_axis8: axisprop(8, 0)
    fvar_axis9: axisprop(9, 0)

    fvar_axis1_offset: axisprop_offset(1, 0)
    fvar_axis2_offset: axisprop_offset(2, 0)
    fvar_axis3_offset: axisprop_offset(3, 0)
    fvar_axis4_offset: axisprop_offset(4, 0)
    fvar_axis5_offset: axisprop_offset(5, 0)
    fvar_axis6_offset: axisprop_offset(6, 0)
    fvar_axis7_offset: axisprop_offset(7, 0)
    fvar_axis8_offset: axisprop_offset(8, 0)
    fvar_axis9_offset: axisprop_offset(9, 0)

    kerning_pairs: bpy.props.StringProperty(name="Kerning Pairs", default="", update=lambda p, c: update_type_and_copy("kerning_pairs", p, c), description="Provide a Python dictionary literal to control kerning of pairs, where the keys are two glyph names separated by slashes, and the values are integers specified in font-size upem values")

    kerning_pairs_enabled: bpy.props.BoolProperty(name="Kerning Pairs Enabled", default=True, update=lambda p, c: update_type_and_copy("kerning_pairs_enabled", p, c))
    
    fea_kern: feaprop("kern", True)
    fea_liga: feaprop("liga", True)

    # TODO are these default states configurable by the font?
    # could look at it in FontGoggles
    fea_mark: feaprop("mark", False)
    fea_ccmp: feaprop("ccmp", False)
    fea_tnum: feaprop("tnum", False)
    fea_pnum: feaprop("pnum", False)
    fea_frac: feaprop("frac", False)
    fea_subs: feaprop("subs", False)
    fea_dnom: feaprop("dnom", False)
    fea_sups: feaprop("sups", False)
    fea_sinf: feaprop("sinf", False)
    fea_case: feaprop("case", False)
    fea_numr: feaprop("numr", False)
    fea_ordn: feaprop("ordn", False)
    fea_aalt: feaprop("aalt", False)
    fea_salt: feaprop("salt", False)
    fea_calt: feaprop("calt", False)
    fea_locl: feaprop("locl", False)
    
    fea_ss01: feaprop("ss01")
    fea_ss02: feaprop("ss02")
    fea_ss03: feaprop("ss03")
    fea_ss04: feaprop("ss04")
    fea_ss05: feaprop("ss05")
    fea_ss06: feaprop("ss06")
    fea_ss07: feaprop("ss07")
    fea_ss08: feaprop("ss08")
    fea_ss09: feaprop("ss09")
    fea_ss10: feaprop("ss10")
    fea_ss11: feaprop("ss11")
    fea_ss12: feaprop("ss12")
    fea_ss13: feaprop("ss13")
    fea_ss14: feaprop("ss14")
    fea_ss15: feaprop("ss15")
    fea_ss16: feaprop("ss16")
    fea_ss17: feaprop("ss17")
    fea_ss18: feaprop("ss18")
    fea_ss19: feaprop("ss19")
    fea_ss20: feaprop("ss20")

    def has_keyframes(self, obj):
        if obj.animation_data is not None and obj.animation_data.action is not None:
            has_coldtype_keyframes = False
            for fcu in obj.animation_data.action.fcurves:
                if fcu.data_path.startswith("st2."):
                    has_coldtype_keyframes = True
            return has_coldtype_keyframes
        return False
    
    def editable(self, obj):
        return obj.select_get() and obj.st2.updatable and not obj.st2.baked
    
    def get_parent(self, obj):
        pass

    def font(self, none_ok=False):
        font = None
        if self.font_path:
            try:
                font = ct.Font.Cacheable(self.font_path)
            except Exception as e:
                print(">>>", e)
        
        if font:
            return font
        else:
            if none_ok:
                return None
            else:
                return ct.Font.RecursiveMono()




classes = [ST2PropertiesGroup]
panels = []