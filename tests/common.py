from coldtype import *
from coldtype.blender import *
import pytest

nickel = Font.Find("Nickel", "tests/fonts")

def vec(a, b, c):
    import mathutils
    return mathutils.Vector([a, b, c])

def new_text(text):
    tag = f"ST2:{text}"
    
    bpy.ops.st2.settype_with_scene_defaults()
    to = BpyObj.Find(tag)
    return to


def common(bw:BpyWorld):
    BpyObj.Find("Cube").delete()
    bw.cycles(32, False, Rect(1080, 1080))
    bw.timeline(Timeline(30))
    bw.scene.frame_set(0)

    bpy.context.preferences.inputs.use_emulate_numpad = True
    bpy.context.preferences.view.show_tooltips_python = True

    import addon_utils
    addon_utils.disable("ST2")
    addon_utils.enable("ST2")
    bpy.ops.st2.import_dependencies()

    st2 = bw.scene.st2
    st2.font_path = str(nickel.path)

    for _ in range(0, 2):
        for obj in bpy.data.objects:
            if obj.name.startswith("ST2:"):
                bpy.data.objects.remove(obj, do_unlink=True)
    
    bpy.ops.st2.settype_with_scene_defaults()
    
    to = BpyObj.Find(bpy.context.object)
    
    assert to.obj is not None
    assert to.obj.location == vec(0,0,0)

    return to