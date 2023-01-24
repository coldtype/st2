import bpy

from ST2 import typesetter
from ST2 import search


def bake_frames(context, framewise=True, frames=None, glyphwise=False, shapewise=False, layerwise=False, progress_fn=None):
    from ST2.importer import cb

    obj = context.active_object
    data = obj.st2
    data.frozen = True

    sc = context.scene
    current = sc.frame_current

    if not frames:
        frames = range(sc.frame_start, sc.frame_end+1)

    duration = len(frames)

    if data.export_style == "TOP":
        parent, coll = None, None
    elif data.export_style == "PARENT":
        parent, coll = True, None
    elif data.export_style == "COLLECTION":
        parent, coll = None, True

    if parent:
        anchor = cb.BpyObj.Empty(f"{obj.name}_BakedFrames_Anchor", collection="Global")

        data.copy_to(anchor.obj.st2)
        
        anchor.obj.st2.baked = True
        anchor.obj.st2.baked_from = obj.name
        anchor.obj.st2.bake_frame = -1
        anchor.obj.st2.updatable = True
        parent = anchor
    
    if coll:
        coll = f"ST2:Export_{obj.name}"

    results = []

    for frame in frames:
        if progress_fn:
            progress_fn(frame/duration)
        
        if frame%data.export_every_x_frame != 0:
            print("skipping", frame)
            continue
        
        sc.frame_set(frame)
        print("> baking:", frame)

        t = typesetter.T(data, obj, context.scene, coll)
        p = t.two_dimensional(glyphwise, framewise)
        
        results.append(t.convert_live_to_baked(p, framewise, glyphwise, shapewise, parent.obj if parent else None))
        
        #bpy.context.view_layer.update()
    
    sc.frame_set(current)

    obj.st2.frozen = False
    obj.hide_render = True
    obj.hide_set(True)

    if parent:
        bpy.context.view_layer.objects.active = None
        bpy.context.view_layer.objects.active = parent.obj
        bpy.ops.object.select_all(action='DESELECT')
        parent.obj.select_set(True)
    elif coll:
        pass
    else:
        bpy.context.view_layer.objects.active = None
        bpy.ops.object.select_all(action='DESELECT')
        for res in results:
            for bp in res:
                bp.obj.select_set(True)
        bpy.context.view_layer.objects.active = bp.obj

    sc.frame_set(0)


class ST2_OT_ExportSlug(bpy.types.Operator):
    """Export slug as single shape"""

    bl_label = "ST2 Export Slug"
    bl_idname = "st2.export_slug"
    bl_options = {"REGISTER","UNDO"}
    
    def execute(self, context):
        bake_frames(context, framewise=False, glyphwise=False, frames=[context.scene.frame_current])
        return {"FINISHED"}


class ST2_OT_ExportGlyphs(bpy.types.Operator):
    """Export glyphs as individual shapes"""

    bl_label = "ST2 Export Glyphs"
    bl_idname = "st2.export_glyphs"
    bl_options = {"REGISTER","UNDO"}
    
    def execute(self, context):
        bake_frames(context, framewise=False, glyphwise=True, frames=[context.scene.frame_current])
        return {"FINISHED"}


class ST2_OT_ExportShapes(bpy.types.Operator):
    """Export text broken down into individual shapes"""

    bl_label = "ST2 Export Shapes"
    bl_idname = "st2.export_shapes"
    bl_options = {"REGISTER","UNDO"}
    
    def execute(self, context):
        bake_frames(context, framewise=False, glyphwise=True, shapewise=True, frames=[context.scene.frame_current])
        return {"FINISHED"}


class ST2_OT_ExportLayers(bpy.types.Operator):
    """Export text broken down by individual glyph layers"""

    bl_label = "ST2 Export Layers"
    bl_idname = "st2.export_layers"
    bl_options = {"REGISTER","UNDO"}
    
    def execute(self, context):
        bake_frames(context, framewise=False, glyphwise=True, shapewise=True, layerwise=True, frames=[context.scene.frame_current])
        return {"FINISHED"}


class ST2_OT_BakeFrames(bpy.types.Operator):
    """Bake animation as individual curves, shown/hidden per-frame"""

    bl_label = "ST2 Bake Frames"
    bl_idname = "st2.bake_frames"
    bl_options = {"REGISTER","UNDO"}
    
    def execute(self, context):
        context.window_manager.progress_begin(0, 1)
        bake_frames(context, framewise=True, progress_fn=lambda x: 
            context.window_manager.progress_update(x))
        context.window_manager.progress_end()
        return {"FINISHED"}


class ST2_OT_BakeFramesNoTiming(bpy.types.Operator):
    """Bake animation as individual curves, shown all at once"""

    bl_label = "ST2 Bake Frames with No Timing"
    bl_idname = "st2.bake_frames_no_timing"
    bl_options = {"REGISTER","UNDO"}
    
    def execute(self, context):
        context.window_manager.progress_begin(0, 1)
        bake_frames(context, framewise=False, progress_fn=lambda x: 
            context.window_manager.progress_update(x))
        context.window_manager.progress_end()
        
        return {"FINISHED"}


class ST2_OT_BakeSelectAll(bpy.types.Operator):
    bl_label = "ST2 Bake Select All"
    bl_idname = "st2.bake_select_all"
    #bl_options = {"REGISTER","UNDO"}
    
    def execute(self, context):
        ko = search.active_baked_object(context, prefer_parent=True)
        
        for o in context.scene.objects:
            if o.parent and o.parent == ko:
                o.select_set(True)
        
        ko.select_set(True)
        return {"FINISHED"}


def delete_at_frame(context, o:bpy.types.Object, frame:int):
    context.scene.frame_set(frame)
    bpy.ops.object.select_all(action='DESELECT')
    o.select_set(True)
    bpy.ops.object.delete()


class ST2_OT_DeleteBake(bpy.types.Operator):
    bl_label = "ST2 Delete Bake"
    bl_idname = "st2.delete_bake"
    bl_options = {"REGISTER","UNDO"}
    
    def execute(self, context):
        ko = search.active_baked_object(context, prefer_parent=True)
        baked_from = context.scene.objects[ko.st2.baked_from]

        bpy.context.view_layer.objects.active = None
        current = context.scene.frame_current

        for o in context.scene.objects:
            if o.parent and o.parent == ko:
                delete_at_frame(context, o, o.st2.bake_frame)

        delete_at_frame(context, ko, current)

        baked_from.hide_set(False)
        baked_from.hide_render = False

        bpy.context.view_layer.objects.active = None
        bpy.context.view_layer.objects.active = baked_from
        bpy.ops.object.select_all(action='DESELECT')
        baked_from.select_set(True)
        
        return {"FINISHED"}


class ST2ExportPanel(bpy.types.Panel):
    bl_label = "Export"
    bl_idname = "ST2_PT_4_EXPORTPANEL"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "ST2"

    @classmethod
    def poll(cls, context):
        ko = search.active_key_object(context)
        if ko and ko.data and not ko.st2.has_keyframes(ko):
            return True
    
    def draw(self, context):
        layout = self.layout
        ko = search.active_key_object(context)
        data = ko.st2

        row = layout.row()

        row.label(text="Options")
        row.prop(data, "export_geometric_origins", icon="TRANSFORM_ORIGINS", icon_only=True)
        row.prop(data, "export_meshes", icon="OUTLINER_OB_MESH", icon_only=True)

        #row = layout.row()
        col = row.column()
        col.enabled = data.export_meshes
        col.prop(data, "export_apply_transforms", icon="DRIVER_TRANSFORM", icon_only=True)
        col = row.column()
        col.enabled = data.export_meshes
        col.prop(data, "export_rigidbody_active", icon="RIGID_BODY", icon_only=True)

        # row = layout.row()
        # row.label(text="New Objects")
        # row.prop(data, "export_style", text="", expand=True)

        row = layout.row(align=True)
        row.label(text="Stagger")
        row.prop(data, "export_stagger_y", text="Y")
        row.prop(data, "export_stagger_z", text="Z")

        row = layout.row(align=True)
        row.label(text="Rotate")
        row.prop(data, "export_rotate_x", text="X")
        row.prop(data, "export_rotate_y", text="Y")
        row.prop(data, "export_rotate_z", text="Z")

        font = data.font()
    
        layout.row().operator("st2.export_slug", text="Export Slug")
        layout.row().operator("st2.export_glyphs", text="Export Glyphs")
        layout.row().operator("st2.export_shapes", text="Export Shapes")

        if font._colr:
            row.operator("st2.export_layers", text="Layers")


class ST2BakeAnimationPanel(bpy.types.Panel):
    bl_label = "Bake Animation"
    bl_idname = "ST2_PT_5_BAKEPANEL"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "ST2"

    @classmethod
    def poll(cls, context):
        ko = search.active_key_object(context)
        if ko and ko.st2.has_keyframes(ko):
            return True
        else:
            return False
    
    def draw(self, context):
        layout = self.layout
        ko = search.active_key_object(context)
        data = ko.st2

        row = layout.row()

        row.label(text="Options")
        #row.prop(data, "export_geometric_origins", icon="TRANSFORM_ORIGINS", icon_only=True)

        row.prop(data, "export_every_x_frame", text="Frame Interval")
        row.prop(data, "export_meshes", icon="OUTLINER_OB_MESH", icon_only=True)

        layout.row().operator("st2.bake_frames", text="Bake Timed")
        layout.row().operator("st2.bake_frames_no_timing", text="Export Untimed")
        


class ST2BakedPanel(bpy.types.Panel):
    bl_label = "Baked"
    bl_idname = "ST2_PT_6_BAKEDPANEL"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "ST2"

    @classmethod
    def poll(cls, context):
        return bool(search.active_baked_object(context))
    
    def draw(self, context):
        ko = search.active_baked_object(context, prefer_parent=True)

        self.layout.row().label(text=f"Baked: “{ko.st2.text}”")
        self.layout.row().operator("st2.bake_select_all", text="Select All")
        self.layout.row().operator("st2.delete_bake", text="Delete Bake")


classes = [
    ST2_OT_ExportSlug,
    ST2_OT_ExportGlyphs,
    ST2_OT_ExportShapes,
    ST2_OT_ExportLayers,
    ST2_OT_BakeFrames,
    ST2_OT_BakeFramesNoTiming,
    ST2_OT_BakeSelectAll,
    ST2_OT_DeleteBake,
]

panels = [
    ST2ExportPanel,
    ST2BakeAnimationPanel,
    ST2BakedPanel,
]