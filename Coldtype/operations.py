import bpy
from pathlib import Path
from bpy_extras.io_utils import ImportHelper
from Coldtype import search, typesetter

try:
    import coldtype.text as ct
except ImportError:
    pass


class Coldtype_OT_ShowFont(bpy.types.Operator):
    """Show the selected font in your OS file system browser"""

    bl_label = "Coldtype Show Font"
    bl_idname = "ctxyz.show_font"
    
    def execute(self, context):
        ctxyz, _ = search.find_ctxyz(context)
        import os
        os.system(f"open {str(Path(ctxyz.font_path).parent)}")
        return {"FINISHED"}


def cycle_font(context, inc):
    data, obj = search.find_ctxyz(context)
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


class Coldtype_OT_ClearFont(bpy.types.Operator):
    bl_label = "Coldtype Clear Font"
    bl_idname = "ctxyz.clear_font"
    bl_options = {"REGISTER","UNDO"}
    
    def execute(self, context):
        ts = context.scene.ctxyz
        ts.font_path = ""

        # TODO reset stuff?
        return {"FINISHED"}


class Coldtype_OT_RefreshSettings(bpy.types.Operator):
    """Refresh/resync all live text to specified settings"""

    bl_label = "Coldtype Refresh Settings"
    bl_idname = "ctxyz.refresh_settings"
    
    def execute(self, context):
        from coldtype.text.reader import FontCache

        if typesetter.MESH_CACHE_COLLECTION in bpy.data.collections:
            mcc = bpy.data.collections[typesetter.MESH_CACHE_COLLECTION]
            for o in mcc.objects:
                bpy.data.objects.remove(o, do_unlink=True)

        editables = search.find_ctxyz_editables(context)
        for e in editables:
            for k in [kp:=e.ctxyz.font_path, str(kp)]:
                if k in FontCache:
                    del FontCache[k]
            
            typesetter.set_type(e.ctxyz, e, context=context)
        return {"FINISHED"}


class WM_OT_ColdtypeChooseFont(bpy.types.Operator, ImportHelper):
    """Open file dialog to pick a font"""
    
    bl_idname = "wm.ctxyz_choose_font"
    bl_label = "Choose font file"
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
        data, _ = search.find_ctxyz(context)
        
        font = ct.Font.Cacheable(path)
        data.font_path = str(font.path)
        return {'FINISHED'}


class Coldtype_OT_SetTypeWithSceneDefaults(bpy.types.Operator):
    """Build text with current settings"""

    bl_label = "Coldtype SetType Scene"
    bl_idname = "ctxyz.settype_with_scene_defaults"
    bl_options = {"REGISTER","UNDO"}
    
    def execute(self, context):
        data = context.scene.ctxyz
        font = ct.Font.Cacheable(data.font_path)

        for idx, (_, v) in enumerate(font.variations().items()):
            diff = abs(v["maxValue"]-v["minValue"])
            v = (v["defaultValue"]-v["minValue"])/diff
            setattr(data, f"fvar_axis{idx+1}", v)

        txtObj = typesetter.set_type(data)[0]
        
        for k in data.__annotations__.keys():
            v = getattr(data, k)
            setattr(txtObj.obj.ctxyz, k, v)
        
        if data.default_upright:
            txtObj.rotate(x=90)
        
        txtObj.extrude(data.default_extrude)

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


classes = [
    Coldtype_OT_LoadNextFont,
    Coldtype_OT_LoadPrevFont,
    Coldtype_OT_ShowFont,
    Coldtype_OT_ClearFont,
    Coldtype_OT_RefreshSettings,
    Coldtype_OT_SetTypeWithSceneDefaults,
    Coldtype_OT_SetTypeWithObject,
    WM_OT_ColdtypeChooseFont,
]

panels = [

]