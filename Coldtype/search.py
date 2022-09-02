import bpy

try:
    import coldtype.text as ct
except ImportError:
    ct = None


def find_ctxyz(context):
    ob = context.active_object
    if ob is not None and ob.select_get():
        if ob.ctxyz.parent:
            pob = bpy.data.objects[ob.ctxyz.parent]
            return pob.ctxyz, pob
        else:
            return ob.ctxyz, ob
    else:
        return context.scene.ctxyz, None


def find_ctxyz_all_selected(context):
    selected = []
    for o in context.scene.objects:
        if o.ctxyz.editable(o) and o.select_get():
            selected.append(o)
    return selected


def find_ctxyz_editables(context):
    editables = []
    for o in context.scene.objects:
        if o.ctxyz.editable(o):
            editables.append(o)
    return editables


def active_key_object(context, disallow_baked=True):
    if not ct:
        return None
    
    obj = context.active_object
    if obj and obj.select_get():
        if obj.ctxyz.parent:
            return bpy.data.objects[obj.ctxyz.parent]
        elif obj.ctxyz.updatable:
            if not disallow_baked:
                return obj
            elif not obj.ctxyz.baked:
                return obj


classes = []
panels = []