import bpy

try:
    import coldtype.text as ct
except ImportError:
    ct = None


def find_st2(context):
    ob = context.active_object
    if ob is not None and ob.select_get():
        if ob.st2.parent:
            pob = bpy.data.objects[ob.st2.parent]
            return pob.st2, pob
        else:
            return ob.st2, ob
    else:
        return context.scene.st2, None


def find_st2_all_selected(context):
    selected = []
    for o in context.scene.objects:
        if o.st2.editable(o) and o.select_get():
            selected.append(o)
    return selected


def find_st2_editables(context):
    editables = []
    for o in context.scene.objects:
        if o.st2.editable(o):
            editables.append(o)
    return editables


def active_key_object(context, disallow_baked=True):
    if not ct:
        return None
    
    obj = context.active_object
    if obj and obj.select_get():
        if obj.st2.parent:
            return bpy.data.objects[obj.st2.parent]
        elif obj.st2.updatable:
            if not disallow_baked:
                return obj
            elif not obj.st2.baked:
                return obj


def active_baked_object(context, prefer_parent=False):
    if not ct:
        return None
    
    obj = context.active_object
    if obj and obj.select_get() and obj.st2.baked:
        if obj.parent and prefer_parent:
            return obj.parent
        else:
            return obj


classes = []
panels = []