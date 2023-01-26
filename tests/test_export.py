from .common import * #INLINE

@b3d_runnable()
def test_export(bw:BpyWorld):
    def setup():
        to1 = common(bw)
        return to1

    to1 = setup()
    to1.obj.st2.text = "Hello¶World"
    to1.select(set_active=True)

    bpy.ops.st2.export_glyphs()

    anchor = bpy.context.object
    assert "\n" not in anchor.name, "no newline"
    assert anchor.name == "ST2:HelloWorld_BakedFrames_Anchor"

    ao = BpyObj(anchor)
    bakes = ao.find_children()
    assert len(bakes) == 10

    assert anchor.location == vec(0,0,0)

    bpy.ops.st2.delete_bake()

    assert bpy.context.object.name == "ST2:HelloWorld"

    bpy.ops.st2.export_slug()

    anchor = bpy.context.object
    assert "\n" not in anchor.name, "no newline"
    assert anchor.name == "ST2:HelloWorld_BakedFrames_Anchor"

    ao = BpyObj(anchor)
    bakes = ao.find_children()
    assert len(bakes) == 1, "count"