import bpy, platform, re


def _os(): return platform.system()
def on_windows(): return _os() == "Windows"
def on_mac(): return _os() == "Darwin"
def on_linux(): return _os() == "Linux"


def clear_frame_changers(fn):
    for funcs in [
        bpy.app.handlers.frame_change_pre,
        bpy.app.handlers.frame_change_post
        ]:
        remove = []
        for handler in funcs:
            if handler.__name__ == fn.__name__:
                remove.append(handler)

        for func in remove:
            try:
                funcs.remove(func)
            except ValueError:
                pass


def ensure_frame_changer(frame_changers, fn, src=None):
    found = False
    for fc in frame_changers:
        if fc.__name__ == fn.__name__:
            found = True
    
    if not found:
        frame_changers.append(fn)


def get_children(ko):
    children = []
    for o in bpy.data.objects:
        if o.parent == ko:
            children.append(o)
    return sorted(children, key=lambda c: c.name)


def delete_parent_recursively(ko):
    for c in get_children(ko):
        bpy.data.objects.remove(c, do_unlink=True)
    
    bpy.data.objects.remove(ko, do_unlink=True)


# ensure_channelbag & get_fcurves are taken/modified from
# https://blenderartists.org/t/how-to-access-fcurves-in-blender-5-0/1623022/6

def ensure_channelbag(data_block):
    """
    Returns the channelbag of f-curves for a given ID, or `None` if the ID doesn't
    have an animation data, an action, or a slot.
    """

    if data_block.animation_data is None: return None

    anim_data = data_block.animation_data
    if anim_data.action is None: return None

    action = anim_data.action
    if action.is_empty: return None

    if anim_data.action_slot is None: return None

    try:
        from bpy_extras.anim_utils import action_ensure_channelbag_for_slot
        return action_ensure_channelbag_for_slot(action, anim_data.action_slot)
    except ImportError:
        #print("could not import action_ensure_channelbag_for_slot")
        pass


def get_fcurves(obj, matching:re.Pattern=None):
    if not obj.animation_data or not obj.animation_data.action: return None

    fcurves_out = []

    if hasattr(obj.animation_data.action, 'fcurves'):
        fcurves = obj.animation_data.action.fcurves
    else:
        channelbag = ensure_channelbag(obj)
        if channelbag is None: return None
        fcurves = channelbag.fcurves

    for fcurve in fcurves:
        if matching is None:
            fcurves_out.append(fcurve)
        else:
            if re.match(matching, fcurve.data_path):
                fcurves_out.append(fcurve)

    return fcurves_out


classes = []
panels = []