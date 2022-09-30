import bpy, platform


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


classes = []
panels = []