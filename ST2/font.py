import bpy

try:
    import coldtype.text as ct
except ImportError:
    ct = None

from ST2 import search


class ST2_OT_LoadVarAxesDefaults(bpy.types.Operator):
    """Set variable font axes to their font-specified default values"""

    bl_label = "ST2 Load Var Axes Defaults"
    bl_idname = "st2.load_var_axes_defaults"
    bl_options = {"REGISTER","UNDO"}
    
    def execute(self, context):
        for o in search.find_st2_all_selected(context):
            font = o.st2.font()
            for idx, (axis, v) in enumerate(font.variations().items()):
                diff = abs(v["maxValue"]-v["minValue"])
                v = (v["defaultValue"]-v["minValue"])/diff
                setattr(o.st2, f"fvar_axis{idx+1}", v)

        return {"FINISHED"}


class ST2Text3DSettingsPanel(bpy.types.Panel):
    bl_label = "3D Settings"
    bl_idname = "ST2_PT_30_TEXT3DPANEL"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "ST2"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        ko = search.active_key_object(context)
        if ko and ko.data:
            return True
    
    def draw(self, context):
        ko = search.active_key_object(context)
        layout = self.layout

        row = layout.row()
        row.prop(ko, "rotation_euler", text="Rotation")
        row = layout.row()
        row.prop(ko.data, "extrude", text="Extrude")
        row.prop(ko.data, "bevel_depth", text="Bevel")
        row = layout.row()
        row.prop(ko.data, "fill_mode", text="Fill Mode")
        


class ST2FontVariationsPanel(bpy.types.Panel):
    bl_label = "Font Variations"
    bl_idname = "ST2_PT_31_FONTVARSPANEL"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "ST2"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        ko = search.active_key_object(context)
        if ko:
            font = ko.st2.font()
            if font.variations():
                return True
        return False
    
    def draw(self, context):
        ko = search.active_key_object(context)
        
        layout = self.layout
        data = ko.st2
        font = data.font()
        fvars = font.variations()
    
        for idx, (k, v) in enumerate(fvars.items()):
            prop = f"fvar_axis{idx+1}"
            
            norm_v = getattr(data, prop)
            diff = abs(v["maxValue"]-v["minValue"])
            unnorm_v = v["minValue"] + (diff * norm_v)

            row = layout.row()
            split = row.split(factor=0.85)
            col = split.column()
            col.prop(data, prop, text=k)
            #col = row.column()
            #col.alignment = "RIGHT"
            #col.width = 50
            col = split.column()
            col.alignment = "RIGHT"
            col.label(text="{:d}".format(round(unnorm_v)))

            if k == "wdth":
                row = layout.row()
                row.label(text="Fit Width")
                row.prop(data, "fit", text="")
                row.prop(data, "fit_enable", text="Enable")
    
        if ko.st2.has_keyframes(ko):
            #layout.row().label(text="Variation Offsets")

            for idx, (k, v) in enumerate(fvars.items()):
                layout.row().prop(data, f"fvar_axis{idx+1}_offset", text=f"{k} offset")
        
        row = layout.row()
        row.operator("st2.load_var_axes_defaults", icon="EMPTY_AXIS", text="Set to Defaults")


class ST2FontStylisticSetsPanel(bpy.types.Panel):
    bl_label = "Font Stylistic Sets"
    bl_idname = "ST2_PT_32_FONTSTYLESPANEL"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "ST2"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        ko = search.active_key_object(context)
        if ko:
            font = ko.st2.font()
            styles = [fea for fea in font.font.featuresGSUB if fea.startswith("ss")]

            if len(styles) > 0:
                return True
        return False
    
    def draw(self, context):
        ko = search.active_key_object(context)
        
        layout = self.layout
        data = ko.st2
        font = data.font()

        fi = 0
        row = None

        styles = [fea for fea in sorted(font.font.featuresGSUB) if fea.startswith("ss")]

        for style in styles:
            if fi%2 == 0 or row is None:
                row = layout.row()
            
            ss_name = font.font.stylisticSetNames.get(style)
            if not ss_name:
                ss_name = "Stylistic Set " + str(int(style[2:]))

            row.prop(data, f"fea_{style}", text=f"{style}: {ss_name}")
            
            fi += 1


class ST2FontFeaturesPanel(bpy.types.Panel):
    bl_label = "Font Features"
    bl_idname = "ST2_PT_33_FONTFEATURESPANEL"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "ST2"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return bool(search.active_key_object(context))
    
    def draw(self, context):
        ko = search.active_key_object(context)
        
        layout = self.layout
        data = ko.st2
        font = data.font()

        fi = 0
        row = None

        def show_fea(fea):
            nonlocal fi, row
            if fi%4 == 0 or row is None:
                row = layout.row()
            
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
        
        row = layout.row()
        row.prop(data, "kerning_pairs", text="KP (dict)")
        row.prop(data, "kerning_pairs_enabled", text="")


classes = [
    ST2_OT_LoadVarAxesDefaults,
]

panels = [
    ST2Text3DSettingsPanel,
    ST2FontVariationsPanel,
    ST2FontStylisticSetsPanel,
    ST2FontFeaturesPanel,
]