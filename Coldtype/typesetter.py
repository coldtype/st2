import bpy, tempfile
from mathutils import Vector

try:
    import coldtype.text as ct
    import coldtype.blender as cb
    import coldtype as C
except ImportError:
    pass

MESH_CACHE_COLLECTION = "Coldtype.MeshCache"

def set_type(ts, object=None, parent=None, baking=False, context=None, scene=None, framewise=True, glyphwise=False, object_name=None, collection=None):
    # if ufo, don't cache?

    font = ct.Font.Cacheable(ts.font_path)
    try:
        mesh = font.font.ttFont["MESH"]
    except KeyError:
        mesh = None

    collection = collection or "Global"

    text = "\n".join(ts.text.split("¶"))
    if ts.case == "TYPED":
        pass
    elif ts.case == "UPPER":
        text = text.upper()
    elif ts.case == "LOWER":
        text = text.lower()
    
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

    if mesh:
        p.mapv(lambda g: g.record(C.P(g.ambit(th=1, tv=1))))
    
    p.collapse()

    if mesh:
        if MESH_CACHE_COLLECTION not in bpy.data.collections:
            coll = bpy.data.collections.new(MESH_CACHE_COLLECTION)
            bpy.context.scene.collection.children.link(coll)
        
        mcc = bpy.data.collections[MESH_CACHE_COLLECTION]
        #mcc.hide_select = True
        #mcc.hide_viewport = True
        #mcc.hide_render = True
        font_name = font.path.stem

        for x in p:
            key = f"{font_name}.{x.glyphName}"
            
            if key not in bpy.data.objects:
                mg = mesh.strikes[1000].glyphs[x.glyphName]

                with tempfile.NamedTemporaryFile("wb", suffix=".glb") as glbf:
                    glbf.write(mg.meshData)
                    bpy.ops.import_scene.gltf(
                        filepath=glbf.name,
                        #filter_glob="*.glb;*.gltf",
                        #files=[],
                        #loglevel=0,
                        #import_pack_images=True,
                        #merge_vertices=False,
                        #import_shading='NORMALS',
                        #bone_heuristic='TEMPERANCE',
                        #guess_original_bind_pose=True
                        )
                    
                    obj = bpy.context.object
                    obj.name = key
                    obj.ctxyz.meshOffsetX = mg.originOffsetX
                    obj.ctxyz.meshOffsetY = mg.originOffsetY

                    mcc.objects.link(obj)
                    for c in obj.users_collection:
                        if c != mcc:
                            c.objects.unlink(obj)
                        
                    print(">>> imported mesh:", x.glyphName)
        
        def build_mesh(empty):
            print(">", empty, p)

            current = {}
            for o in bpy.data.objects:
                if o.parent == empty:
                    idx = int(o.name.split(".")[-1])
                    current[idx] = o

            for idx, x in enumerate(p):
                key = f"{font_name}.{x.glyphName}"
                prototype = bpy.data.objects[key]
                existing = current.get(idx, None)
                
                if existing:
                    mesh_glyph = existing
                else:
                    mesh_glyph = prototype.copy()
                
                mesh_glyph.data = prototype.data.copy()
                mesh_glyph.name = f"{empty.name}.glyph.{idx}"
                mesh_glyph.parent = empty

                mesh_glyph.scale = (0.3, 0.3, 0.3)

                amb = x.ambit(th=0, tv=0)
                mesh_glyph.location = (
                    amb.x + prototype.ctxyz.meshOffsetX*0.003,
                    0,
                    prototype.ctxyz.meshOffsetY*0.003
                    )

                print(">", x.ambit().x)

                if existing is None:
                    empty.users_collection[0].objects.link(mesh_glyph)
            
            for idx, o in current.items():
                if idx >= len(p):
                    bpy.data.objects.remove(current[idx], do_unlink=True)
    
    # need to check baking glyphwise?

    if not mesh:
        if ts.combine_glyphs and not glyphwise:
            p = p.pen()

        if ts.remove_overlap:
            p.remove_overlap()
        
        if ts.outline:
            ow = ts.outline_weight/100
            if ts.outline_outer or ow < 0:
                p_inner = p.copy()
            
            p.outline(ts.outline_weight/100, miterLimit=ts.outline_miter_limit)
            
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
            if mesh:
                build_mesh(object)
            else:
                txtObj.obj = object
                txtObj.draw(p, set_origin=False, fill=False)
            
            output.append(txtObj)
    else:
        # initial creation of live text

        if mesh:
            txtObj = (cb.BpyObj.Empty(object_name or "Coldtype", collection))
            #txtObj = (cb.BpyObj.Cube(object_name or "Coldtype", collection))
            build_mesh(txtObj.obj)
        else:
            txtObj = (cb.BpyObj.Curve(object_name or "Coldtype", collection))
            txtObj.draw(p, set_origin=False, fill=True)
            txtObj.extrude(0)
            #txtObj.rotate(x=90)
        output.append(txtObj)
    
    return output