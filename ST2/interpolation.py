import bpy

from ST2 import search, typesetter


class ST2_OT_InterpolateStrings(bpy.types.Operator):
    """Interpolate multiple strings"""

    bl_label = "ST2 Interpolate Strings"
    bl_idname = "st2.interpolate_strings"
    bl_options = {"REGISTER","UNDO"}
    
    def execute(self, context):
        data = context.scene.st2
        editables = search.find_st2_editables(context)
        a = editables[0]
        b = editables[1]
        collection = a.users_collection[0]

        font = a.st2.font()
        fvars = font.variations()

        from coldtype.timing.easing import ease
        from coldtype.interpolation import norm

        created = []

        context.window_manager.progress_begin(0, 1)

        coll, parent = None, None
        if data.interpolator_style == "PARENT":
            parent = True
        elif data.interpolator_style == "COLLECTION":
            coll = f"ST2:Interpolations"

        if parent:
            parent = typesetter.cb.BpyObj.Empty(f"ST2:InterpolationAnchor", collection="Global")

        for x in range(0, data.interpolator_count):
            xi = x + 1
            p = xi / (data.interpolator_count + 1)
            e, _ = ease(data.interpolator_easing, p)

            context.window_manager.progress_update(e)

            t = typesetter.T(data, None, context.scene, collection=coll)
            c = t.create_live_text_obj(t.two_dimensional())
            c = c.obj

            created.append(c)
            
            c.location = a.location.lerp(b.location, e)

            c.data = a.data.copy()
            c.animation_data_clear()

            for ax in range(0, 3):
                c.rotation_euler[ax] = norm(e, a.rotation_euler[ax], b.rotation_euler[ax])

                c.scale[ax] = norm(e, a.scale[ax], b.scale[ax])
            
            c.data.extrude = norm(e, a.data.extrude, b.data.extrude)

            for k in a.st2.__annotations__.keys():
                v = getattr(a.st2, k)
                setattr(c.st2, k, v)
            
            c.st2.frozen = True
            for idx, (k, v) in enumerate(fvars.items()):
                prop = f"fvar_axis{idx+1}"
                setattr(c.st2, prop, norm(e, getattr(a.st2, prop), getattr(b.st2, prop)))
            c.st2.frozen = False

            c.st2.interpolated = True

            t = typesetter.T(c.st2, c, context.scene)
            t.update_live_text_obj(t.two_dimensional())

            if parent:
                c.parent = parent.obj

        context.window_manager.progress_end()

        bpy.ops.object.select_all(action='DESELECT')
        for obj in created:
            obj.select_set(True)

        return {"FINISHED"}


class ST2InterpolationPanel(bpy.types.Panel):
    bl_label = "Interpolation"
    bl_idname = "ST2_PT_21_INTERPOLATIONPANEL"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "ST2"

    @classmethod
    def poll(cls, context):
        editables = search.find_st2_editables(context)
        if len(editables) == 2:
            if editables[0].st2.text == editables[1].st2.text:
                return True
    
    def draw(self, context):
        editables = search.find_st2_editables(context)

        if len(editables) == 2:
            row = self.layout.row()
            row.prop(context.scene.st2, "interpolator_count", text="")
            row.prop(context.scene.st2, "interpolator_easing", text="")
            row.prop(context.scene.st2, "interpolator_style", text=None, expand=True)

            row = self.layout.row()
            row.operator("st2.interpolate_strings", text="Interpolate")


classes = [
    ST2_OT_InterpolateStrings,
]

panels = [
    ST2InterpolationPanel,
]