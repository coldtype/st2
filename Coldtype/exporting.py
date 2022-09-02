import bpy

try:
    import coldtype.text as ct
    import coldtype.blender as cb
except ImportError:
    ct, cb = None, None


from Coldtype import typesetter
from Coldtype import search


def bake_frames(context, framewise=True, frames=None, glyphwise=False, shapewise=False, layerwise=False, progress_fn=None):
    obj = context.active_object
    obj.ctxyz.frozen = True
    sc = context.scene
    current = sc.frame_current

    anchor = cb.BpyObj.Empty(f"{obj.name}_BakedFrames_Anchor", collection="Global")
    
    anchor.obj.scale = obj.scale
    anchor.obj.location = obj.location
    anchor.obj.rotation_euler = obj.rotation_euler
    
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
            , glyphwise=glyphwise
            , shapewise=shapewise
            , layerwise=layerwise)
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


class Coldtype_OT_ExportShapes(bpy.types.Operator):
    """Export word broken down into individual shapes"""

    bl_label = "Coldtype Export Shapes"
    bl_idname = "ctxyz.export_shapes"
    bl_options = {"REGISTER","UNDO"}
    
    def execute(self, context):
        bake_frames(context, framewise=False, glyphwise=True, shapewise=True, frames=[context.scene.frame_current])
        return {"FINISHED"}


class Coldtype_OT_ExportLayers(bpy.types.Operator):
    """Export word broken down by individual glyph layers"""

    bl_label = "Coldtype Export Layers"
    bl_idname = "ctxyz.export_layers"
    bl_options = {"REGISTER","UNDO"}
    
    def execute(self, context):
        bake_frames(context, framewise=False, glyphwise=True, shapewise=True, layerwise=True, frames=[context.scene.frame_current])
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


class ColdtypeExportPanel(bpy.types.Panel):
    bl_label = "Text Export"
    bl_idname = "COLDTYPE_PT_4_EXPORTPANEL"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Coldtype"

    @classmethod
    def poll(cls, context):
        return bool(search.active_key_object(context))
        # obj = bpy.context.active_object
        # return (
        #     cb is not None
        #     and obj
        #     and obj.select_get()
        #     and obj.ctxyz.updatable
        #     and not obj.ctxyz.parent
        #     and not obj.ctxyz.baked)
    
    def draw(self, context):
        layout = self.layout
        ko = search.active_key_object(context)
        data = ko.ctxyz

        row = layout.row()

        row.label(text="Options")
        row.prop(data, "export_geometric_origins", icon="TRANSFORM_ORIGINS", icon_only=True)
        row.prop(data, "export_meshes", icon="OUTLINER_OB_MESH", icon_only=True)

        if data.export_meshes:
            row = layout.row()
            col = row.column()
            col.prop(data, "export_apply_transforms", icon="DRIVER_TRANSFORM", text="Apply Transforms")
            col = row.column()
            col.prop(data, "export_rigidbody_active", icon="RIGID_BODY", text="Add Rigid Body")

        font = ct.Font.Cacheable(data.font_path)

        layout.row().separator()
        layout.row().operator("ctxyz.export_slug", text="Export Slug")
        layout.row().operator("ctxyz.export_glyphs", text="Export Glyphs")
        layout.row().operator("ctxyz.export_shapes", text="Export Shapes")

        if font._colr:
            row.operator("ctxyz.export_layers", text="Layers")
    
        if ko.ctxyz.has_keyframes(ko):
            row = layout.row()
            row.label(text="Export Animated")
            row.operator("ctxyz.bake_frames", text="Timed")
            row.operator("ctxyz.bake_frames_no_timing", text="Untimed")
            row.prop(data, "export_every_x_frame", text="")


class ColdtypeBakedPanel(bpy.types.Panel):
    bl_label = "Baked"
    bl_idname = "COLDTYPE_PT_4_BAKEDPANEL"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Coldtype"

    @classmethod
    def poll(cls, context):
        ko = search.active_key_object(context, disallow_baked=False)
        if ko and ko.ctxyz.baked:
            return True
    
    def draw(self, context):
        ko = search.active_key_object(context, disallow_baked=False)

        self.layout.row().label(text=f"Baked: “{ko.ctxyz.text}”")
        self.layout.row().operator("ctxyz.delete_bake", text="Delete Bake")


classes = [
    Coldtype_OT_ExportSlug,
    Coldtype_OT_ExportGlyphs,
    Coldtype_OT_ExportShapes,
    Coldtype_OT_ExportLayers,
    Coldtype_OT_BakeFrames,
    Coldtype_OT_BakeFramesNoTiming,
    Coldtype_OT_DeleteBake,
]

panels = [
    ColdtypeExportPanel,
    ColdtypeBakedPanel,
]