import bpy

from Coldtype import search, typesetter


class Coldtype_OT_InterpolateStrings(bpy.types.Operator):
    """Interpolate multiple strings"""

    bl_label = "Coldtype Interpolate Strings"
    bl_idname = "ctxyz.interpolate_strings"
    bl_options = {"REGISTER","UNDO"}
    
    def execute(self, context):
        data = context.scene.ctxyz
        editables = search.find_ctxyz_editables(context)
        a = editables[0]
        b = editables[1]
        collection = a.users_collection[0]

        font = typesetter.ct.Font.Cacheable(a.ctxyz.font_path)
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

            collection = None #if data.interpolator_count == 1 else f""
            #f"{a.name}_{b.name}_Interpolations"

            # Todo make collection or parent optional

            c = typesetter.set_type(data, collection=collection)[0]
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

            c.ctxyz.interpolated = True

            typesetter.set_type(c.ctxyz, c, context=context)

        context.window_manager.progress_end()

        bpy.ops.object.select_all(action='DESELECT')
        for obj in created:
            obj.select_set(True)

        return {"FINISHED"}


class ColdtypeInterpolationPanel(bpy.types.Panel):
    bl_label = "Interpolation"
    bl_idname = "COLDTYPE_PT_21_INTERPOLATIONPANEL"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Coldtype"

    @classmethod
    def poll(cls, context):
        editables = search.find_ctxyz_editables(context)
        if len(editables) == 2:
            if editables[0].ctxyz.text == editables[1].ctxyz.text:
                return True
    
    def draw(self, context):
        editables = search.find_ctxyz_editables(context)

        if len(editables) == 2:
            row = self.layout.row()
            row.operator("ctxyz.interpolate_strings", text="Interpolate")
            row.prop(context.scene.ctxyz, "interpolator_count", text="")
            row.prop(context.scene.ctxyz, "interpolator_easing", text="")


classes = [
    Coldtype_OT_InterpolateStrings,
]

panels = [
    ColdtypeInterpolationPanel,
]