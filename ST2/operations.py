import bpy
from pathlib import Path
from bpy_extras.io_utils import ImportHelper

from ST2 import search, typesetter

def item_cb(self, context):
    from ST2.importer import ct
    all_fonts = [f for f in ct.Font.LibraryList(".*") if not f.startswith(".")]
    all_fonts = sorted(all_fonts, key=lambda x: x)
    return [(str(f), str(f), "") for i, f in enumerate(all_fonts)]


class ST2_OT_SearchFont(bpy.types.Operator):
    """Search for a font in the system library"""
    bl_label = "ST2 Search Font"
    bl_idname = "st2.search_font"
    bl_property = "available_fonts"

    available_fonts: bpy.props.EnumProperty(items=item_cb)

    def execute(self, context):
        from ST2.importer import ct

        font_name = self.available_fonts
        font = ct.Font.LibraryFind(font_name)

        st2, _ = search.find_st2(context)
        st2.enable_font_search = True
        st2.font_path = str(font.path)
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        wm.invoke_search_popup(self)
        return {'FINISHED'}


# class ST2_OT_SearchFont(bpy.types.Operator):
#     """Search for a font in the system library"""

#     bl_label = "ST2 Search Font"
#     bl_idname = "st2.search_font"
#     #bl_property = "my_enum"

#     #my_enum: bpy.props.EnumProperty(items = items, name='New Name', default=None)

#     def execute(self, context):
#         def draw(self, context):
#             self.layout.label(text="Hello World")

#         bpy.context.window_manager.popup_menu(draw, title="Greeting", icon='INFO')
#         return {'FINISHED'}
    
#     # @classmethod
#     # def poll(cls, context):
#     #     return context.scene.material  # This prevents executing the operator if we didn't select a material

#     # def execute(self, context):
#     #     material = context.scene.material
#     #     material.name = self.my_enum
#     #     return {'FINISHED'}

#     # def invoke(self, context, event):
#     #     wm = context.window_manager
#     #     wm.invoke_search_popup(self)
#     #     return {'FINISHED'}


class ST2_OT_ShowFont(bpy.types.Operator):
    """Show the selected font in your OS file system browser"""

    bl_label = "ST2 Show Font"
    bl_idname = "st2.show_font"
    
    def execute(self, context):
        st2, _ = search.find_st2(context)
        import os
        font = st2.font()
        folder = font.path.parent
        print(">>>>>>>>>>>", folder)
        os.system(f"open '{str(folder)}'")
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
        ts.enable_font_search = False
        ts.font_path = ""

        # TODO reset stuff?
        return {"FINISHED"}


class ST2_OT_RefreshSettings(bpy.types.Operator):
    """Refresh/resync all live text to specified settings"""

    bl_label = "ST2 Refresh Settings"
    bl_idname = "st2.refresh_settings"
    
    def execute(self, context):
        from coldtype.text.font import FontCache

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
        from ST2.importer import ct

        path = Path(self.filepath)
        ob = search.active_key_object(context)
        if not ob:
            ob = context.scene
        
        font = ct.Font.Cacheable(path)
        ob.st2.font_path = str(font.path)
        ob.st2.enable_font_search = False
        
        return {'FINISHED'}


class ST2_OT_SetTypeWithSceneDefaults(bpy.types.Operator):
    """Build text with current settings"""

    bl_label = "ST2 SetType Scene"
    bl_idname = "st2.settype_with_scene_defaults"
    bl_options = {"REGISTER","UNDO"}
    
    def execute(self, context):
        data = context.scene.st2
        font = data.font()

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


class ST2_OT_WatchSource(bpy.types.Operator):
    bl_label = "Start Watching Source"
    bl_idname = "st2.watch_source"
    
    def execute(self, context):
        context.scene.st2.script_watch = True
        bpy.ops.wm.st2_source_watcher()
        return {"FINISHED"}


class ST2_OT_CancelWatchSource(bpy.types.Operator):
    bl_label = "Stop Watching Source"
    bl_idname = "st2.cancel_watch_source"
    
    def execute(self, context):
        context.scene.st2.script_watch = False
        return {"FINISHED"}


class ST2SourceWatcher(bpy.types.Operator):
    bl_idname = "wm.st2_source_watcher"
    bl_label = "ST2 Source Watcher"

    _timer = None
    _force = False

    _sources = {}

    def modal(self, context, event):
        st2 = context.scene.st2

        def cancel(force=False):
            print("CANCELLING")
            self._force = force
            self.cancel(context)
            return {"FINISHED"}
        
        if not st2.script_watch:
            return cancel(force=True)

        if event.type == 'ESC':
            return cancel(force=True)

        if event.type == 'TIMER':
            for obj in search.find_st2_editables(context):
                data = obj.st2
                if data.script_file and data.script_enabled:
                    if data.script_file not in self._sources:
                        stat = Path(data.script_file).stat()
                        self._sources[data.script_file] = stat.st_mtime
            
            for src, last_mtime in self._sources.items():
                stat = Path(src).stat()
                if stat.st_mtime > last_mtime:
                    self._sources[src] = stat.st_mtime
                    print("save detected:", src)
                    bpy.ops.st2.refresh_settings()

        return {'PASS_THROUGH'}

    def execute(self, context):
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.25, window=context.window)
        wm.modal_handler_add(self)

        return {'RUNNING_MODAL'}

    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)
        self._force = False
        print('timer removed')


classes = [
    ST2SourceWatcher,
    ST2_OT_WatchSource,
    ST2_OT_CancelWatchSource,
    ST2_OT_LoadNextFont,
    ST2_OT_LoadPrevFont,
    ST2_OT_SearchFont,
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