import bpy
from pathlib import Path

try:
    import coldtype.text as ct
except ImportError:
    pass


def find_ctxyz(context):
    ob = context.active_object
    if ob is not None and ob.select_get():
        if ob.ctxyz.parent:
            pob = bpy.data.objects[ob.ctxyz.parent]
            return pob.ctxyz, pob
        else:
            return ob.ctxyz, ob
    else:
        return context.scene.ctxyz, None


def find_ctxyz_all_selected(context):
    selected = []
    for o in context.scene.objects:
        if o.ctxyz.editable(o) and o.select_get():
            selected.append(o)
    return selected


def find_ctxyz_editables(context):
    editables = []
    for o in context.scene.objects:
        if o.ctxyz.editable(o):
            editables.append(o)
    return editables


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

        return {"FINISHED"}


class Coldtype_OT_ShowFont(bpy.types.Operator):
    """Show the selected font in your OS file system browser"""

    bl_label = "Coldtype Show Font"
    bl_idname = "ctxyz.show_font"
    
    def execute(self, context):
        ctxyz, _ = find_ctxyz(context)
        import os
        os.system(f"open {str(Path(ctxyz.font_path).parent)}")
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


classes = [
    Coldtype_OT_LoadVarAxesDefaults,
    Coldtype_OT_LoadNextFont,
    Coldtype_OT_LoadPrevFont,
    Coldtype_OT_ShowFont,
]