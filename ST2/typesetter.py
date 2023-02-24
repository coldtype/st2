import bpy, tempfile, math, inspect, time
from mathutils import Vector
from pathlib import Path

from ST2 import util


MESH_CACHE_COLLECTION = "ST2.MeshCache"


def read_mesh_glyphs_into_cache(font, p, mesh_table):
    if MESH_CACHE_COLLECTION not in bpy.data.collections:
        coll = bpy.data.collections.new(MESH_CACHE_COLLECTION)
        bpy.context.scene.collection.children.link(coll)
    
    mcc = bpy.data.collections[MESH_CACHE_COLLECTION]
    mcc.hide_select = True
    mcc.hide_viewport = True
    mcc.hide_render = True
    
    font_name = font.path.stem

    for x in p:
        key = f"{font_name}.{x.glyphName}"
        
        if key not in bpy.data.objects:
            mg = mesh_table.strikes[1000].glyphs[x.glyphName]

            with tempfile.NamedTemporaryFile("wb", suffix=".glb", delete=False) as glbf:
                glbf.write(mg.meshData)
            
            bpy.ops.import_scene.gltf(filepath=glbf.name)
            Path(glbf.name).unlink()
            
            obj = bpy.context.object
            obj.name = key
            obj.st2.meshOffsetX = mg.originOffsetX
            obj.st2.meshOffsetY = mg.originOffsetY

            mcc.objects.link(obj)

            for c in obj.users_collection:
                if c != mcc:
                    c.objects.unlink(obj)    
            #print(">>> imported mesh:", x.glyphName)


def build_mesh(empty, p, data):
    font = data.font()
    current = {}

    for o in bpy.data.objects:
        if o.parent == empty:
            idx = int(o.name.split(".")[-1])
            current[idx] = o

    for idx, x in enumerate(p):
        key = f"{font.path.stem}.{x.glyphName}"
        prototype = bpy.data.objects[key]
        existing = current.get(idx, None)
        
        if existing:
            mesh_glyph = existing
        else:
            mesh_glyph = prototype.copy()
        
        mesh_glyph.data = prototype.data.copy()
        mesh_glyph.name = f"{empty.name}.glyph.{idx}"
        mesh_glyph.parent = empty
        mesh_glyph.st2.parent = empty.name

        mesh_glyph.scale = (0.3*data.scale, 0.3*data.scale, 0.3*data.scale)

        amb = x.ambit(tx=0, ty=0)
        # 0.003 is b/c of the 3pt fontSize hardcoded above
        mesh_glyph.location = (
            amb.x + prototype.st2.meshOffsetX*0.003*data.scale,
            0, #mesh_glyph.location.y,
            prototype.st2.meshOffsetY*0.003*data.scale)

        if existing is None:
            empty.users_collection[0].objects.link(mesh_glyph)
    
    for idx, o in current.items():
        if idx >= len(p):
            bpy.data.objects.remove(current[idx], do_unlink=True)


class T():
    def __init__(self
        , st2
        , obj
        , scene
        , collection="Global"
        ):
        self.st2 = st2
        self.scene = scene
        self.obj = obj
        self.collection = collection

        self.font = self.st2.font()
        self.text = self.st2.build_text()
        
        self.base_name = "ST2::File" if self.st2.text_mode != "UI" else "ST2:" + self.text[:20].replace("\n", "")
    
    def base_vectors(self):
        if not self.obj or not self.obj.st2.has_keyframes(self.obj):
            p = self.build_single_style()
        else:
            p = self.build_multi_style()

        self.align(p)
        
        # not good if we want to do stagger line-wise, need to preserve this info
        p.collapse()
        return p
    
    def two_dimensional(self, glyphwise=False, shapewise=False):
        p = self.base_vectors()

        if self.st2.script_enabled:
            p = self.apply_script(p)
        if self.st2.combine_glyphs and not glyphwise:
            p = p.pen()
        if self.st2.remove_overlap:
            p.remove_overlap()
        if self.st2.outline:
            p = self.apply_outline(p, shapewise)
        
        #if self.st2.block:
        #    p = self.add_blocks(p)
        
        return p
    
    def base_style_kwargs(self):
        kp = None
        if self.st2.kerning_pairs and self.st2.kerning_pairs_enabled:
            try:
                kp = eval(self.st2.kerning_pairs)
            except Exception as e:
                print(">>>", e)
                pass

        return dict(font=self.font
            , fontSize=3*self.st2.scale
            , tu=self.st2.tracking
            , kp=kp
            , fit=self.st2.fit if self.st2.fit_enable else None
            , **self.st2.features(self.font))
    
    def build_single_style(self):
        from ST2.importer import ct

        return ct.StSt(self.text
            , **self.base_style_kwargs()
            , **self.st2.variations(self.font)
            , multiline=True
            , leading=self.st2.leading
            , strip=False)

    def build_multi_style(self):
        from ST2.importer import ct

        def styler(x):
            _vars = {}
            for idx, (k, _) in enumerate(self.st2.visible_variation_axes(self.font).items()):
                dp = f"fvar_axis{idx+1}"
                fvar_offset = getattr(self.st2, f"{dp}_offset")
                found = False
                var_val = getattr(self.st2, dp)
                
                try:
                    for fcu in self.obj.animation_data.action.fcurves:
                        #print(fcu.data_path, dp)
                        if fcu.data_path.split(".")[-1] == dp:
                            found = True
                            _vars[k] = fcu.evaluate((self.scene.frame_current - x.i*fvar_offset)%(self.scene.frame_end+1 - self.scene.frame_start))
                except AttributeError as e:
                    print(x.e, var_val, var_val%1)
                    _vars[k] = (var_val + (fvar_offset * x.e))%1.001
                    found = True
                
                if not found:
                    _vars[k] = var_val

            return ct.Style(**self.base_style_kwargs(), **_vars)

        p = ct.Glyphwise(self.text, styler, multiline=True)
        if self.st2.leading:
            p.lead(self.st2.leading)
        return p
    
    def align(self, p):
        txty = dict(tx=not self.st2.use_horizontal_font_metrics, ty=not self.st2.use_vertical_font_metrics)
        
        amb = p.ambit(**txty)

        p.xalign(rect=amb, x=self.st2.align_lines_x, tx=not self.st2.use_horizontal_font_metrics)

        ax, ay, aw, ah = p.ambit(**txty)

        p.t(-ax, -ay)

        if self.st2.align_x == "CX":
            p.t(-aw/2, 0)
        elif self.st2.align_x == "E":
            p.t(-aw, 0)
        
        if self.st2.align_y == "CY":
            p.t(0, -ah/2)
        elif self.st2.align_y == "N":
            p.t(0, -ah)

    def apply_script(self, p):
        from runpy import run_path
        from tempfile import NamedTemporaryFile

        res = None
        if self.st2.script_mode == "FILE" and self.st2.script_file:
            try:
                res = run_path(self.st2.script_file)
            except Exception as e:
                print("Could not run script", e)
        elif self.st2.script_mode == "BLOCK":
            try:
                script_text = bpy.data.texts[self.st2.script_block].as_string()
                if script_text:
                    tmp_path = None
                    with NamedTemporaryFile("w", suffix=".py", delete=False) as tf:
                        tf.write(script_text)
                        tmp_path = Path(tf.name)
                    try:
                        res = run_path(tmp_path)
                    except Exception as e:
                        print("Could not run block", e)
                    finally:
                        tmp_path.unlink()
            except KeyError:
                print("No block with that name")
        
        if res:
            if "modify" in res:
                fn = res["modify"]
                arg_count = len(inspect.signature(fn).parameters)
                
                args = [self.st2]
                if arg_count > 1:
                    try:
                        args.append(eval(f"dict({self.st2.script_kwargs})"))
                    except Exception as e:
                        print(e)
                        print("failed to parse kwargs")
                        args.append({})

                if arg_count > 2:
                    args.append(p)
                
                #if arg_count > 3:
                #    args.append(txtObj)
                
                return fn(*args)
                #if output is not None:
                #    txtObj.draw(output, set_origin=False, fill=False)
            else:
                print(">>> SCRIPT ERROR: no `modify` function found")

    def add_blocks(self, p):
        from ST2.importer import C

        def block(_p):
            return (C.P(_p.ambit(
                        tx=not self.st2.block_horizontal_metrics,
                        ty=not self.st2.block_vertical_metrics)
                    .inset(self.st2.block_inset_x, self.st2.block_inset_y))
                #.skew(0.5, 0)
                #.translate(0.2, 0)
                .difference(_p.copy()))

        if self.st2.combine_glyphs:
            p = block(p)
        
        p.mapv(block)
        return p

    def apply_outline(self, p, shapewise):
        if shapewise:
            p.mapv(lambda _p: _p.explode())
            p.collapse()

        ow = self.st2.outline_weight/100
        if self.st2.outline_outer or ow < 0:
            p_inner = p.copy()
        
        p.outline(self.st2.outline_weight/100, miterLimit=self.st2.outline_miter_limit)
        
        if ow < 0:
            p_inner.difference(p)
            p = p_inner
        elif self.st2.outline_outer:
            p.difference(p_inner)
        
        return p
    
    def create_live_text(self, p):
        if p.depth() == 0 or True:
            return self.create_live_single(p)
        else:
            return self.create_live_parented(p)
        
    def swap_metadata(self, other, selected):
        other.obj.location = self.obj.location
        other.obj.rotation_euler = self.obj.rotation_euler

        self.st2.copy_to(other.obj.st2)

        was_name = self.obj.name
        util.delete_parent_recursively(self.obj)
        other.obj.name = was_name
        self.obj = other.obj

        if selected:
            other.obj.select_set(True)
            bpy.context.view_layer.objects.active = other.obj

        return other
    
    def create_live_single(self, p):
        from ST2.importer import cb

        to = cb.BpyObj.Curve("ST2:Text", self.collection)
        to.extrude(0)

        if self.obj: # converting
            data = self.obj.data
            if self.obj.type == "EMPTY":
                data = util.get_children(self.obj)[0].data

            to.obj.data = data.copy()
            to.obj.animation_data_clear()
            self.st2.copy_to(to.obj.st2)
        
        to.draw(p, set_origin=False, fill=True)
        return to
    
    def add_parented_glyph(self, idx, p, parent, data):
        from ST2.importer import cb

        name = "ST2:Glyphs:" + "::" + str(idx)
        to = cb.BpyObj.Curve(name, self.collection)
        if data: # converting
            to.obj.data = data.copy()
            to.obj.animation_data_clear() # necessary?
        to.obj.parent = parent
        #self.st2.copy_to(to.obj.st2) # necessary?
        to.draw(p, set_origin=False, fill=False)
        return to.obj
    
    def create_live_parented(self, p, empty=None):
        from ST2.importer import cb

        if empty is None:
            empty = cb.BpyObj.Empty("ST2:temporary_empty", "Global")

        def glyph_obj(i, gp):
            self.add_parented_glyph(i, gp, empty.obj, self.obj.data.copy() if self.obj else None)
        
        p.mapv(glyph_obj)
        return empty
    
    def update_live_text_obj(self, p):
        from ST2.importer import cb

        selected = self.obj.select_get()

        if p.depth() == 0 or True:
            if self.obj.type == "EMPTY":
                return self.swap_metadata(self.create_live_single(p), selected)

            to = cb.BpyObj()
            to.obj = self.obj

            if self.st2.auto_rename:
                to.obj.name = self.base_name

            to.draw(p, set_origin=False, fill=False)
        else:
            if self.obj.type == "CURVE":
                return self.swap_metadata(self.create_live_parented(p), selected)

            children = util.get_children(self.obj)
            children_reused = []

            def glyph_obj(i, gp):
                try:
                    c = children[i]
                    cb.BpyObj.Find(c).draw(gp, set_origin=False, fill=False)
                    children_reused.append(i)
                    #leftover.pop(0)
                except IndexError:
                    c = self.add_parented_glyph(i, gp, self.obj, children[1].data)
            
            p.map(glyph_obj)

            for i, c in enumerate(children):
                if i not in children_reused:
                    bpy.data.objects.remove(c, do_unlink=True)
    
    def convert_live_to_baked(self, p, framewise, glyphwise, shapewise, parent):
        from ST2.importer import cb
        output = []

        def export(glyph=None, idx=None):
            txtObj = (cb.BpyObj.Curve(f"{self.obj.name}Frozen", self.collection))
            txtObj.obj.data = self.obj.data.copy()
            txtObj.obj.animation_data_clear()
            txtObj.obj.scale = self.obj.scale
            txtObj.obj.location = self.obj.location
            txtObj.obj.rotation_euler = self.obj.rotation_euler

            if glyph and idx is not None:
                if self.st2.export_stagger_y:
                    txtObj.locate_relative(y=idx*self.st2.export_stagger_y)
                if self.st2.export_stagger_z:
                    txtObj.locate_relative(z=idx*self.st2.export_stagger_z)

            if glyph:
                txtObj.draw(glyph, set_origin=False, fill=False)
                # TODO option to set typographic origins
            else:
                txtObj.draw(p, set_origin=False, fill=False)

            frame = self.scene.frame_current

            txtObj.obj.st2.baked = True
            txtObj.obj.st2.baked_from = self.obj.name
            txtObj.obj.st2.bake_frame = frame

            txtObj.obj.st2._baked_frame = self.obj

            if framewise:
                def hide(hidden):
                    txtObj.obj.scale = Vector((0, 0, 0)) if hidden else self.obj.scale
                    txtObj.obj.keyframe_insert(data_path="scale")
                
                self.scene.frame_set(frame-1)
                hide(True)
                self.scene.frame_set(frame)
                hide(False)
                self.scene.frame_set(frame+self.st2.export_every_x_frame-1)
                hide(False)
                self.scene.frame_set(frame+self.st2.export_every_x_frame)
                hide(True)
                self.scene.frame_set(frame)
            
            txtObj.obj.select_set(True)
            if self.st2.export_meshes:
                bpy.ops.object.convert(target="MESH")
                if self.st2.export_apply_transforms:
                    bpy.ops.object.transform_apply(location=0, rotation=1, scale=1, properties=0)
                if self.st2.export_rigidbody_active:
                    bpy.ops.rigidbody.object_add()
                    txtObj.obj.rigid_body.type = "ACTIVE"
                    #bpy.ops.object.transform_apply(location=0, rotation=1, scale=1, properties=0)
                    pass
            if self.st2.export_geometric_origins:
                bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY')
            txtObj.obj.select_set(False)
            
            if parent:
                txtObj.obj.parent = parent
                #txtObj.obj.st2.parent = parent.name
            
            txtObj.obj.st2.updatable = True
            txtObj.obj.visible_camera = self.obj.visible_camera

            if glyph and idx is not None:
                if self.st2.export_rotate_y:
                    txtObj.rotate(y=math.degrees(self.st2.export_rotate_y))

            return txtObj
        
        if glyphwise:
            if shapewise:
                if not self.st2.outline:
                    p.mapv(lambda _p: _p.explode())
                    p.collapse()
            #if layerwise:
            #    p.mapv(lambda _p: _p.explode())
            
            for idx, glyph in enumerate(p):
                output.append(export(glyph, idx=idx))
        else:
            output.append(export())
        
        return output


classes = []
panels = []