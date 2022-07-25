import bpy
from mathutils import Vector

try:
    import coldtype.text as ct
    import coldtype.blender as cb
except ImportError:
    pass

def set_type(ts, object=None, parent=None, baking=False, context=None, scene=None, framewise=True, glyphwise=False, object_name=None, collection=None):
    # if ufo, don't cache?
    font = ct.Font.Cacheable(ts.font_path)
    collection = collection or "Global"

    text = "\n".join(ts.text.split("¶"))
    
    features = {}
    for k, v in ts.__annotations__.items():
        if k.startswith("fea_"):
            features[k[4:]] = getattr(ts, k)

    variations = {}
    for idx, (k, v) in enumerate(font.variations().items()):
        variations[k] = getattr(ts, f"fvar_axis{idx+1}")

    if not object or not object.ctxyz.has_keyframes(object):
        p = (ct.StSt(text, font
            , fontSize=3
            , leading=ts.leading
            , tu=ts.tracking
            , multiline=True
            , **features
            , **variations))
    else:
        def styler(x):
            _vars = {}
            for idx, (k, v) in enumerate(font.variations().items()):
                dp = f"fvar_axis{idx+1}"
                fvar_offset = getattr(ts, f"{dp}_offset")
                found = False
                for fcu in object.animation_data.action.fcurves:
                    #print(fcu.data_path, dp)
                    if fcu.data_path.split(".")[-1] == dp:
                        found = True
                        _vars[k] = fcu.evaluate((scene.frame_current - x.i*fvar_offset)%(scene.frame_end+1 - scene.frame_start))
                
                if not found:
                    _vars[k] = getattr(ts, dp)

            return ct.Style(font, 3,
                tu=ts.tracking,
                **features,
                **_vars)

        p = ct.Glyphwise(text, styler, multiline=True)
        if ts.leading:
            p.lead(ts.leading)
    
    amb = p.ambit(
        th=not ts.use_horizontal_font_metrics,
        tv=not ts.use_vertical_font_metrics)

    p.xalign(rect=amb, x=ts.align_lines_x, th=not ts.use_horizontal_font_metrics)

    ax, ay, aw, ah = p.ambit(
        th=not ts.use_horizontal_font_metrics,
        tv=not ts.use_vertical_font_metrics)

    p.t(-ax, -ay)

    if ts.align_x == "CX":
        p.t(-aw/2, 0)
    elif ts.align_x == "E":
        p.t(-aw, 0)
    
    if ts.align_y == "CY":
        p.t(0, -ah/2)
    elif ts.align_y == "N":
        p.t(0, -ah)
    
    p.collapse()
    
    # need to check baking glyphwise?
    if ts.combine_glyphs and not glyphwise:
        p = p.pen()

    if ts.remove_overlap:
        p.remove_overlap()
    
    if ts.outline:
        ow = ts.outline_weight/100
        if ts.outline_outer or ow < 0:
            p_inner = p.copy()
        p.outline(ts.outline_weight/100)
        
        if ow < 0:
            p_inner.difference(p)
            p = p_inner
        elif ts.outline_outer:
            p.difference(p_inner)
    
    output = []
    
    if object:
        if baking:
            # converting live text to non-live text

            def export(glyph=None):
                txtObj = (cb.BpyObj.Curve(f"{object.name}Frozen", collection))
                txtObj.obj.data = object.data.copy()
                txtObj.obj.animation_data_clear()
                txtObj.obj.scale = object.scale
                txtObj.obj.location = object.location
                txtObj.obj.rotation_euler = object.rotation_euler

                if glyph:
                    txtObj.draw(glyph, set_origin=False, fill=False)
                    # TODO option to set typographic origins
                else:
                    txtObj.draw(p, set_origin=False, fill=False)

                frame = context.scene.frame_current

                txtObj.obj.ctxyz.baked = True
                txtObj.obj.ctxyz.baked_from = object.name
                txtObj.obj.ctxyz.bake_frame = frame

                if framewise:
                    def hide(hidden):
                        txtObj.obj.scale = Vector((0, 0, 0)) if hidden else object.scale
                        txtObj.obj.keyframe_insert(data_path="scale")
                    
                    context.scene.frame_set(frame-1)
                    hide(True)
                    context.scene.frame_set(frame)
                    hide(False)
                    context.scene.frame_set(frame+ts.export_every_x_frame-1)
                    hide(False)
                    context.scene.frame_set(frame+ts.export_every_x_frame)
                    hide(True)
                    context.scene.frame_set(frame)
                
                txtObj.obj.select_set(True)
                if ts.export_meshes:
                    bpy.ops.object.convert(target="MESH")
                    if ts.export_apply_transforms:
                        bpy.ops.object.transform_apply(location=0, rotation=1, scale=1, properties=0)
                if ts.export_geometric_origins:
                    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY')
                txtObj.obj.select_set(False)
                
                if parent:
                    txtObj.obj.parent = parent
                
                txtObj.obj.ctxyz.updatable = True
                txtObj.obj.visible_camera = object.visible_camera
                return txtObj
            
            if glyphwise:
                for glyph in p:
                    output.append(export(glyph))
            else:
                output.append(export())
        else:
            # interactive updating of live text

            txtObj = cb.BpyObj()
            txtObj.obj = object
            txtObj.draw(p, set_origin=False, fill=False)
            output.append(txtObj)
    else:
        # initial creation of live text

        txtObj = (cb.BpyObj.Curve(object_name or "Coldtype", collection))
        txtObj.draw(p, set_origin=False, fill=True)
        txtObj.extrude(0)
        #txtObj.rotate(x=90)
        output.append(txtObj)
    
    return output