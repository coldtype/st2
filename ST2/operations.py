import bpy
from pathlib import Path
from bpy_extras.io_utils import ImportHelper
from ST2 import search, typesetter

try:
    import coldtype.text as ct
except ImportError:
    pass


class ST2_OT_ShowFont(bpy.types.Operator):
    """Show the selected font in your OS file system browser"""

    bl_label = "ST2 Show Font"
    bl_idname = "st2.show_font"
    
    def execute(self, context):
        st2, _ = search.find_st2(context)
        import os
        os.system(f"open {str(Path(st2.font_path).parent)}")
        return {"FINISHED"}


def cycle_font(context, inc):
    data, obj = search.find_st2(context)
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


class ST2_OT_LoadNextFont(bpy.types.Operator):
    """Load next font in directory"""

    bl_label = "ST2 Load Next Font"
    bl_idname = "st2.load_next_font"
    bl_options = {"REGISTER","UNDO"}
    
    def execute(self, context):
        cycle_font(context, +1)
        return {"FINISHED"}


class ST2_OT_LoadPrevFont(bpy.types.Operator):
    """Load previous font in directory"""

    bl_label = "ST2 Load Previous Font"
    bl_idname = "st2.load_prev_font"
    bl_options = {"REGISTER","UNDO"}
    
    def execute(self, context):
        cycle_font(context, -1)
        return {"FINISHED"}


class ST2_OT_ClearFont(bpy.types.Operator):
    bl_label = "ST2 Clear Font"
    bl_idname = "st2.clear_font"
    bl_options = {"REGISTER","UNDO"}
    
    def execute(self, context):
        ts = context.scene.st2
        ts.font_path = ""

        # TODO reset stuff?
        return {"FINISHED"}


class ST2_OT_RefreshSettings(bpy.types.Operator):
    """Refresh/resync all live text to specified settings"""

    bl_label = "ST2 Refresh Settings"
    bl_idname = "st2.refresh_settings"
    
    def execute(self, context):
        from coldtype.text.reader import FontCache

        if typesetter.MESH_CACHE_COLLECTION in bpy.data.collections:
            mcc = bpy.data.collections[typesetter.MESH_CACHE_COLLECTION]
            for o in mcc.objects:
                bpy.data.objects.remove(o, do_unlink=True)

        editables = search.find_st2_editables(context)
        for e in editables:
            for k in [kp:=e.st2.font_path, str(kp)]:
                if k in FontCache:
                    del FontCache[k]
            
            typesetter.set_type(e.st2, e, context=context)
        return {"FINISHED"}


def delete_parent_recursively(ko):
    for o in bpy.data.objects:
        if o.parent == ko:
            bpy.data.objects.remove(o, do_unlink=True)
    
    bpy.data.objects.remove(ko, do_unlink=True)


class ST2_OT_DeleteParentedText(bpy.types.Operator):
    bl_label = "ST2 Delete Parented Text"
    bl_idname = "st2.delete_parented_text"
    bl_options = {"REGISTER","UNDO"}
    
    def execute(self, context):
        ko = search.active_key_object(context)
        delete_parent_recursively(ko)
        return {"FINISHED"}


class ST2_OT_InsertNewlineSymbol(bpy.types.Operator):
    """Insert a ¶ symbol to mark a newline in the single-line text editor"""

    bl_label = "Insert Newline Symbol"
    bl_idname = "st2.insert_newline_symbol"
    bl_options = {"REGISTER","UNDO"}
    
    def execute(self, context):
        ko = search.active_key_object(context)
        ko.st2.text = ko.st2.text + "¶"
        return {"FINISHED"}


class WM_OT_ST2ChooseFont(bpy.types.Operator, ImportHelper):
    """Open file dialog to pick a font"""
    
    bl_idname = "wm.st2_choose_font"
    bl_label = "Choose font file"
    bl_options = {"REGISTER","UNDO"}
    
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
        data, _ = search.find_st2(context)
        
        font = ct.Font.Cacheable(path)
        data.font_path = str(font.path)
        return {'FINISHED'}


class ST2_OT_SetTypeWithSceneDefaults(bpy.types.Operator):
    """Build text with current settings"""

    bl_label = "ST2 SetType Scene"
    bl_idname = "st2.settype_with_scene_defaults"
    bl_options = {"REGISTER","UNDO"}
    
    def execute(self, context):
        data = context.scene.st2
        font = ct.Font.Cacheable(data.font_path)

        for idx, (_, v) in enumerate(font.variations().items()):
            diff = abs(v["maxValue"]-v["minValue"])
            v = (v["defaultValue"]-v["minValue"])/diff
            setattr(data, f"fvar_axis{idx+1}", v)

        txtObj = typesetter.set_type(data)[0]
        
        for k in data.__annotations__.keys():
            v = getattr(data, k)
            setattr(txtObj.obj.st2, k, v)
        
        if data.default_upright:
            txtObj.rotate(x=90)
        
        if txtObj.obj.data:
            txtObj.extrude(data.default_extrude)

        txtObj.obj.st2.updatable = True
        txtObj.obj.st2.frozen = False
        txtObj.obj.select_set(True)
        
        return {"FINISHED"}
    

class ST2_OT_ConvertMeshToFlat(bpy.types.Operator):
    """Convert a mesh-based text setting to an outline-based text-setting"""

    bl_label = "ST2 Convert Mesh to Flat"
    bl_idname = "st2.convert_mesh_to_flat"
    bl_options = {"REGISTER","UNDO"}
    
    def execute(self, context):
        ko = search.active_key_object(context)
        data = ko.st2

        txtObj = typesetter.set_type(data, override_use_mesh=False)[0]

        txtObj.obj.st2.frozen = True
        txtObj.obj.st2.use_mesh = False
        
        for k in data.__annotations__.keys():
            if k not in ["frozen", "use_mesh"]:
                v = getattr(data, k)
                setattr(txtObj.obj.st2, k, v)
        
        if data.default_upright:
            txtObj.rotate(x=90)
        
        if txtObj.obj.data:
            txtObj.extrude(data.default_extrude)

        txtObj.obj.st2.updatable = True
        txtObj.obj.st2.frozen = False

        for o in bpy.data.objects:
            if o.parent == ko:
                bpy.data.objects.remove(o, do_unlink=True)
        
        bpy.data.objects.remove(ko, do_unlink=True)

        txtObj.obj.select_set(True)
        
        return {"FINISHED"}


class ST2_OT_ConvertFlatToMesh(bpy.types.Operator):
    """Convert an outline-based text setting to a mesh-based text-setting"""

    bl_label = "ST2 Convert Flat to Mesh"
    bl_idname = "st2.convert_flat_to_mesh"
    bl_options = {"REGISTER","UNDO"}
    
    def execute(self, context):
        ko = search.active_key_object(context)
        data = ko.st2

        txtObj = typesetter.set_type(data, override_use_mesh=True)[0]

        txtObj.obj.st2.frozen = True
        txtObj.obj.st2.use_mesh = True
        
        for k in data.__annotations__.keys():
            if k not in ["frozen", "use_mesh"]:
                v = getattr(data, k)
                setattr(txtObj.obj.st2, k, v)

        txtObj.obj.st2.updatable = True
        txtObj.obj.st2.frozen = False

        bpy.data.objects.remove(ko, do_unlink=True)

        txtObj.obj.select_set(True)
        
        return {"FINISHED"}


class ST2_OT_SetTypeWithObject(bpy.types.Operator):
    bl_label = "ST2 SetType Object"
    bl_idname = "st2.settype_with_object"
    bl_options = {"REGISTER","UNDO"}
    
    def execute(self, context):
        obj = context.active_object
        typesetter.set_type(obj.st2)
        return {"FINISHED"}


classes = [
    ST2_OT_LoadNextFont,
    ST2_OT_LoadPrevFont,
    ST2_OT_ShowFont,
    ST2_OT_ClearFont,
    ST2_OT_RefreshSettings,
    ST2_OT_DeleteParentedText,
    ST2_OT_InsertNewlineSymbol,
    ST2_OT_SetTypeWithSceneDefaults,
    ST2_OT_SetTypeWithObject,
    ST2_OT_ConvertMeshToFlat,
    ST2_OT_ConvertFlatToMesh,
    WM_OT_ST2ChooseFont,
]

panels = [

]